/**
 * AZALSCORE - Page mot de passe oublié
 */

import React, { useState } from 'react';
import { api } from '@core/api-client';
import { Button } from '@ui/actions';

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await api.post('/v3/auth/forgot-password', { email }, { skipAuth: true });
      setIsSubmitted(true);
    } catch {
      setError('Une erreur est survenue. Veuillez réessayer.');
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="azals-login">
        <h1 className="azals-login__title">Email envoyé</h1>
        <p className="azals-login__subtitle">
          Si un compte existe avec cette adresse email, vous recevrez un lien pour réinitialiser votre mot de passe.
        </p>
        <div className="azals-login__back">
          <a href="/login">Retour à la connexion</a>
        </div>
      </div>
    );
  }

  return (
    <div className="azals-login">
      <h1 className="azals-login__title">Mot de passe oublié</h1>
      <p className="azals-login__subtitle">Entrez votre email pour recevoir un lien de réinitialisation</p>

      {error && <div className="azals-login__error">{error}</div>}

      <form onSubmit={handleSubmit} className="azals-login__form">
        <div className="azals-field">
          <label htmlFor="email" className="azals-field__label">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="azals-input"
            placeholder="votre@email.com"
            autoComplete="email"
            disabled={isLoading}
          />
        </div>

        <Button type="submit" variant="primary" fullWidth isLoading={isLoading}>
          Envoyer le lien
        </Button>
      </form>

      <div className="azals-login__back">
        <a href="/login">Retour à la connexion</a>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
