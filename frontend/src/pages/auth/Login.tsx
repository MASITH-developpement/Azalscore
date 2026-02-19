/**
 * AZALSCORE - Page de connexion
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';
import { setTenantId } from '@core/api-client';
import { trackAuthEvent } from '@core/audit-ui';
import { useAuth } from '@core/auth';
import { useCapabilitiesStore } from '@core/capabilities';
import { Button } from '@ui/actions';

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

  // Update tenant in sessionStorage when it changes
  useEffect(() => {
    if (tenant) {
      setTenantId(tenant);
    }
  }, [tenant]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationErrors({});

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
    <div className="azals-login">
      <h1 className="azals-login__title">Connexion</h1>

      {error && (
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
        >
          Se connecter
        </Button>
      </form>
    </div>
  );
};

export default LoginPage;
