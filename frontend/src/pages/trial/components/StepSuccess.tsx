/**
 * AZALSCORE - Step 7: Success
 * Confirmation de creation du compte
 */

import React from 'react';
import {
  CheckCircle,
  ArrowRight,
  Calendar,
  User,
  Lock,
  Copy,
  ExternalLink,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import type { TrialCompleteResponse } from '../types';

interface StepSuccessProps {
  result: TrialCompleteResponse;
}

export const StepSuccess: React.FC<StepSuccessProps> = ({ result }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopyPassword = () => {
    navigator.clipboard.writeText(result.temporary_password);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const trialEndDate = new Date(result.trial_ends_at);
  const formattedDate = trialEndDate.toLocaleDateString('fr-FR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  return (
    <div className="trial-form trial-success">
      {/* Success icon */}
      <div className="trial-success-icon">
        <CheckCircle size={64} />
      </div>

      {/* Success message */}
      <div className="trial-success-header">
        <h2>Bienvenue chez AZALSCORE !</h2>
        <p>Votre compte a ete cree avec succes.</p>
      </div>

      {/* Account info */}
      <div className="trial-success-card">
        <h3>Vos identifiants de connexion</h3>

        <div className="trial-success-credentials">
          <div className="trial-success-credential">
            <div className="trial-success-credential-icon">
              <User size={20} />
            </div>
            <div className="trial-success-credential-content">
              <span className="trial-success-label">Email</span>
              <strong>{result.admin_email}</strong>
            </div>
          </div>

          <div className="trial-success-credential">
            <div className="trial-success-credential-icon">
              <Lock size={20} />
            </div>
            <div className="trial-success-credential-content">
              <span className="trial-success-label">Mot de passe temporaire</span>
              <div className="trial-success-password">
                <code>{result.temporary_password}</code>
                <button
                  type="button"
                  className="trial-success-copy"
                  onClick={handleCopyPassword}
                  title="Copier le mot de passe"
                >
                  {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
                </button>
              </div>
              <span className="trial-success-hint">
                Vous devrez changer ce mot de passe lors de votre premiere connexion.
              </span>
            </div>
          </div>
        </div>

        {/* Trial info */}
        <div className="trial-success-info">
          <Calendar size={20} />
          <div>
            <strong>Votre essai gratuit</strong>
            <p>
              Vous avez 30 jours pour tester toutes les fonctionnalites.
              Votre essai se termine le <strong>{formattedDate}</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* Tenant info */}
      <div className="trial-success-tenant">
        <p>
          <strong>Espace de travail :</strong> {result.tenant_name}
        </p>
      </div>

      {/* Action buttons */}
      <div className="trial-success-actions">
        <a
          href={result.login_url}
          className="trial-btn trial-btn-primary trial-btn-lg"
        >
          Acceder a mon espace
          <ArrowRight size={20} />
        </a>
      </div>

      {/* Next steps */}
      <div className="trial-success-next-steps">
        <h4>Prochaines etapes</h4>
        <ol>
          <li>Connectez-vous avec vos identifiants ci-dessus</li>
          <li>Changez votre mot de passe temporaire</li>
          <li>Explorez les donnees de demonstration pre-remplies</li>
          <li>Invitez vos collaborateurs (jusqu'a 5 utilisateurs)</li>
          <li>Configurez votre entreprise selon vos besoins</li>
        </ol>
      </div>

      {/* Support info */}
      <div className="trial-success-support">
        <p>
          Besoin d'aide ?{' '}
          <Link to="/contact">
            Contactez notre equipe support
            <ExternalLink size={14} />
          </Link>
        </p>
      </div>
    </div>
  );
};

export default StepSuccess;
