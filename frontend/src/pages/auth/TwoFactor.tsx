/**
 * AZALSCORE - Page 2FA
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@core/auth';
import { useCapabilitiesStore } from '@core/capabilities';
import { trackAuthEvent } from '@core/audit-ui';
import { Button } from '@ui/actions';

const TwoFactorPage: React.FC = () => {
  const navigate = useNavigate();
  const { verify2FA, isLoading, error } = useAuth();
  const loadCapabilities = useCapabilitiesStore((state) => state.loadCapabilities);

  const [code, setCode] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await verify2FA(code);
      trackAuthEvent('2fa_verify', true);
      await loadCapabilities();
      navigate('/cockpit');
    } catch {
      trackAuthEvent('2fa_verify', false);
    }
  };

  return (
    <div className="azals-login">
      <h1 className="azals-login__title">Vérification 2FA</h1>
      <p className="azals-login__subtitle">
        Entrez le code de votre application d'authentification
      </p>

      {error && <div className="azals-login__error">{error}</div>}

      <form onSubmit={handleSubmit} className="azals-login__form">
        <div className="azals-field">
          <label htmlFor="code" className="azals-field__label">Code 2FA</label>
          <input
            id="code"
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
            className="azals-input azals-input--lg azals-input--center"
            placeholder="000000"
            maxLength={6}
            autoComplete="one-time-code"
            disabled={isLoading}
          />
        </div>

        <Button type="submit" variant="primary" fullWidth isLoading={isLoading} isDisabled={code.length !== 6}>
          Vérifier
        </Button>
      </form>

      <div className="azals-login__back">
        <a href="/login">Retour à la connexion</a>
      </div>
    </div>
  );
};

export default TwoFactorPage;
