/**
 * AZALSCORE - Step 5: Email Verification
 * Attente de verification du lien email
 */

import React, { useEffect, useState } from 'react';
import { Mail, Clock, RefreshCw, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { useRegistrationStatus, useVerifyEmail, useResendVerificationEmail } from '../api';
import { useSearchParams } from 'react-router-dom';

interface StepEmailVerificationProps {
  registrationId: string;
  email: string;
  onNext: () => void;
}

export const StepEmailVerification: React.FC<StepEmailVerificationProps> = ({
  registrationId,
  email,
  onNext,
}) => {
  const [searchParams] = useSearchParams();
  const [verificationComplete, setVerificationComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Check for token in URL (from email link)
  const token = searchParams.get('token');

  // Poll registration status
  const { data: status } = useRegistrationStatus(registrationId);

  // Email verification mutation
  const verifyEmail = useVerifyEmail();

  // Resend email mutation
  const resendEmail = useResendVerificationEmail();
  const [resendSuccess, setResendSuccess] = useState(false);

  // If token is in URL, verify it
  useEffect(() => {
    if (token && !verificationComplete && !verifyEmail.isPending) {
      verifyEmail.mutate(
        { token },
        {
          onSuccess: () => {
            setVerificationComplete(true);
            setError(null);
          },
          onError: (err) => {
            setError(err.message);
          },
        }
      );
    }
  }, [token, verificationComplete, verifyEmail]);

  // Auto-advance when email is verified
  useEffect(() => {
    if (status?.email_verified || verificationComplete) {
      // Small delay to show success state
      const timer = setTimeout(() => {
        onNext();
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [status?.email_verified, verificationComplete, onNext]);

  const isVerifying = verifyEmail.isPending;
  const isVerified = status?.email_verified || verificationComplete;

  return (
    <div className="trial-form">
      <div className="trial-form-header">
        <h2>Verification de votre email</h2>
        <p>Nous avons envoye un lien de verification a votre adresse email.</p>
      </div>

      <div className="trial-email-verification">
        {/* Email icon */}
        <div className={`trial-email-icon ${isVerified ? 'trial-email-icon--verified' : ''}`}>
          {isVerifying ? (
            <Loader2 size={48} className="spinning" />
          ) : isVerified ? (
            <CheckCircle size={48} />
          ) : (
            <Mail size={48} />
          )}
        </div>

        {/* Status message */}
        {isVerified ? (
          <div className="trial-email-status trial-email-status--success">
            <CheckCircle size={20} />
            <span>Email verifie avec succes !</span>
          </div>
        ) : isVerifying ? (
          <div className="trial-email-status trial-email-status--pending">
            <Loader2 size={20} className="spinning" />
            <span>Verification en cours...</span>
          </div>
        ) : (
          <div className="trial-email-status trial-email-status--waiting">
            <Clock size={20} />
            <span>En attente de verification...</span>
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="trial-form-error-banner">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* Email sent to */}
        <div className="trial-email-info">
          <p>Un email a ete envoye a :</p>
          <strong>{email}</strong>
        </div>

        {/* Instructions */}
        {!isVerified && (
          <div className="trial-email-instructions">
            <h4>Instructions :</h4>
            <ol>
              <li>Ouvrez votre boite mail</li>
              <li>Recherchez un email de AZALSCORE</li>
              <li>Cliquez sur le lien de verification</li>
              <li>Revenez ici automatiquement ou rafraichissez la page</li>
            </ol>

            <div className="trial-email-tips">
              <p>
                <strong>Vous ne trouvez pas l'email ?</strong>
              </p>
              <ul>
                <li>Verifiez votre dossier spam ou courrier indesirable</li>
                <li>L'email peut prendre quelques minutes a arriver</li>
                <li>Le lien expire dans 24 heures</li>
              </ul>
            </div>
          </div>
        )}

        {/* Resend button */}
        {!isVerified && (
          <div className="trial-resend-container">
            {resendSuccess && (
              <p className="trial-resend-success">
                <CheckCircle size={16} />
                Email renvoyé avec succès !
              </p>
            )}
            {resendEmail.error && (
              <p className="trial-resend-error">
                <AlertCircle size={16} />
                {resendEmail.error.message}
              </p>
            )}
            <button
              type="button"
              className="trial-btn trial-btn-outline"
              disabled={resendEmail.isPending}
              onClick={() => {
                setResendSuccess(false);
                resendEmail.mutate(
                  { registration_id: registrationId },
                  {
                    onSuccess: () => {
                      setResendSuccess(true);
                    },
                  }
                );
              }}
            >
              {resendEmail.isPending ? (
                <Loader2 size={16} className="trial-spinner" />
              ) : (
                <RefreshCw size={16} />
              )}
              {resendEmail.isPending ? 'Envoi...' : 'Renvoyer l\'email'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default StepEmailVerification;
