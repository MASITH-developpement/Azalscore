/**
 * AZALSCORE - Page de connexion
 * SÉCURITÉ: Rate limiting côté client + validation renforcée
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { z } from 'zod';
import { setTenantId } from '@core/api-client';
import { trackAuthEvent } from '@core/audit-ui';
import { useAuth } from '@core/auth';
import { useCapabilitiesStore } from '@core/capabilities';
import { Button } from '@ui/actions';
import { checkRateLimit } from '@/security';

// ============================================================
// CONSTANTES SÉCURITÉ (P0)
// ============================================================
const LOGIN_RATE_LIMIT_KEY = 'login_attempts';
const LOGIN_MAX_ATTEMPTS = 5;
const LOGIN_WINDOW_MS = 15 * 60 * 1000; // 15 minutes
const LOCKOUT_DURATION_MS = 15 * 60 * 1000; // 15 minutes

const loginSchema = z.object({
  tenant: z.string().min(1, 'Société requise'),
  email: z.string().email('Email invalide'),
  password: z.string().min(1, 'Mot de passe requis'),
});

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, isLoading, error } = useAuth();
  const loadCapabilities = useCapabilitiesStore((state) => state.loadCapabilities);

  // Initialize tenant from URL parameter
  const [tenant, setTenant] = useState(searchParams.get('tenant') || '');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // SÉCURITÉ P0: Rate limiting state
  const [isRateLimited, setIsRateLimited] = useState(false);
  const [lockoutEndTime, setLockoutEndTime] = useState<number | null>(null);
  const [remainingTime, setRemainingTime] = useState(0);

  // Vérifier le lockout au chargement
  useEffect(() => {
    const storedLockout = sessionStorage.getItem('azals_login_lockout');
    if (storedLockout) {
      const endTime = parseInt(storedLockout, 10);
      if (Date.now() < endTime) {
        setIsRateLimited(true);
        setLockoutEndTime(endTime);
      } else {
        sessionStorage.removeItem('azals_login_lockout');
      }
    }
  }, []);

  // Countdown timer pour le lockout
  useEffect(() => {
    if (!lockoutEndTime) return;

    const interval = setInterval(() => {
      const remaining = Math.max(0, lockoutEndTime - Date.now());
      setRemainingTime(Math.ceil(remaining / 1000));

      if (remaining <= 0) {
        setIsRateLimited(false);
        setLockoutEndTime(null);
        sessionStorage.removeItem('azals_login_lockout');
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [lockoutEndTime]);

  // Vérifier le rate limit avant soumission
  const checkLoginRateLimit = useCallback((): boolean => {
    const allowed = checkRateLimit(LOGIN_RATE_LIMIT_KEY, LOGIN_MAX_ATTEMPTS, LOGIN_WINDOW_MS);

    if (!allowed) {
      const endTime = Date.now() + LOCKOUT_DURATION_MS;
      setIsRateLimited(true);
      setLockoutEndTime(endTime);
      sessionStorage.setItem('azals_login_lockout', endTime.toString());
      trackAuthEvent('rate_limit_exceeded', false);
      return false;
    }

    return true;
  }, []);

  // Update tenant in sessionStorage when it changes
  useEffect(() => {
    if (tenant) {
      setTenantId(tenant);
    }
  }, [tenant]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationErrors({});

    // SÉCURITÉ P0: Vérifier rate limit
    if (isRateLimited) {
      setValidationErrors({
        general: `Trop de tentatives. Réessayez dans ${Math.ceil(remainingTime / 60)} minute(s).`
      });
      return;
    }

    if (!checkLoginRateLimit()) {
      setValidationErrors({
        general: 'Trop de tentatives de connexion. Veuillez patienter 15 minutes.'
      });
      return;
    }

    try {
      const data = loginSchema.parse({ tenant, email, password });

      // Ensure tenant is set before login
      setTenantId(data.tenant);

      const result = await login({ email: data.email, password: data.password });

      if (result.requires_2fa) {
        trackAuthEvent('login', true);
        navigate('/2fa');
      } else {
        trackAuthEvent('login', true);
        // Réinitialiser le rate limit après succès
        sessionStorage.removeItem('azals_login_lockout');
        await loadCapabilities();
        navigate('/cockpit');
      }
    } catch (err) {
      if (err instanceof z.ZodError) {
        const errors: Record<string, string> = {};
        err.errors.forEach((e) => {
          if (e.path[0]) {
            errors[e.path[0] as string] = e.message;
          }
        });
        setValidationErrors(errors);
      } else {
        trackAuthEvent('login', false);
      }
    }
  };

  return (
    <>
      <Helmet>
        <title>Connexion | Azalscore ERP</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
    <div className="azals-login">
      <h1 className="azals-login__title">Connexion</h1>

      {/* SÉCURITÉ P0: Affichage rate limit */}
      {isRateLimited && (
        <div className="azals-login__error azals-login__error--rate-limit">
          Trop de tentatives de connexion. Veuillez patienter {Math.ceil(remainingTime / 60)} minute(s) ({remainingTime}s).
        </div>
      )}

      {validationErrors.general && (
        <div className="azals-login__error">
          {validationErrors.general}
        </div>
      )}

      {error && !isRateLimited && (
        <div className="azals-login__error">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="azals-login__form">
        <div className="azals-field">
          <label htmlFor="tenant" className="azals-field__label">
            Société
          </label>
          <input
            id="tenant"
            type="text"
            value={tenant}
            onChange={(e) => setTenant(e.target.value.toLowerCase().trim())}
            className={`azals-input ${validationErrors.tenant ? 'azals-input--error' : ''}`}
            placeholder="identifiant-societe"
            autoComplete="organization"
            disabled={isLoading}
          />
          {validationErrors.tenant && (
            <span className="azals-field__error">{validationErrors.tenant}</span>
          )}
        </div>

        <div className="azals-field">
          <label htmlFor="email" className="azals-field__label">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={`azals-input ${validationErrors.email ? 'azals-input--error' : ''}`}
            placeholder="votre@email.com"
            autoComplete="email"
            disabled={isLoading}
          />
          {validationErrors.email && (
            <span className="azals-field__error">{validationErrors.email}</span>
          )}
        </div>

        <div className="azals-field">
          <label htmlFor="password" className="azals-field__label">
            Mot de passe
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={`azals-input ${validationErrors.password ? 'azals-input--error' : ''}`}
            placeholder="••••••••"
            autoComplete="current-password"
            disabled={isLoading}
          />
          {validationErrors.password && (
            <span className="azals-field__error">{validationErrors.password}</span>
          )}
        </div>

        <div className="azals-login__forgot">
          <a href="/forgot-password">Mot de passe oublié ?</a>
        </div>

        <Button
          type="submit"
          variant="primary"
          fullWidth
          isLoading={isLoading}
          disabled={isRateLimited}
        >
          {isRateLimited ? `Verrouillé (${remainingTime}s)` : 'Se connecter'}
        </Button>
      </form>
    </div>
    </>
  );
};

export default LoginPage;
