/**
 * AZALSCORE - Trial Registration Page
 * Formulaire multi-etapes d'inscription a l'essai gratuit
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Link, useSearchParams, useLocation } from 'react-router-dom';
import { useVerifyEmail } from './api';
import { COLORS } from '@core/design-tokens';
import { ProgressBar } from './components/ProgressBar';
import { StepPersonalInfo } from './components/StepPersonalInfo';
import { StepCompanyInfo } from './components/StepCompanyInfo';
import { StepPricingReminder } from './components/StepPricingReminder';
import { StepValidation } from './components/StepValidation';
import { StepEmailVerification } from './components/StepEmailVerification';
import { StepPayment } from './components/StepPayment';
import { StepSuccess } from './components/StepSuccess';
import type {
  TrialStep,
  TrialFormData,
  PersonalInfo,
  CompanyInfo,
  PricingInfo,
  TrialCompleteResponse,
} from './types';
import { initialFormData, TRIAL_STEPS } from './types';
import './trial.css';

// Logo AZALSCORE
const AzalscoreLogo: React.FC<{ size?: number }> = ({ size = 40 }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" fill="none">
    <rect width="100" height="100" rx="20" fill={COLORS.primary} />
    <path
      d="M25 70L50 25L75 70H60L50 50L40 70H25Z"
      fill="white"
      stroke="white"
      strokeWidth="2"
      strokeLinejoin="round"
    />
    <circle cx="50" cy="65" r="8" fill="white" />
  </svg>
);

export const TrialRegistration: React.FC = () => {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const verifyEmailMutation = useVerifyEmail();

  // Current step
  const [currentStep, setCurrentStep] = useState<TrialStep>('personal');

  // Form data
  const [formData, setFormData] = useState<TrialFormData>(initialFormData);

  // Registration state (after step 4)
  const [registrationId, setRegistrationId] = useState<string | null>(() => {
    // Restore from localStorage if exists
    return localStorage.getItem('trial_registration_id');
  });

  // Final result (after step 6)
  const [completeResult, setCompleteResult] = useState<TrialCompleteResponse | null>(null);

  // Email verification state
  const [verificationStatus, setVerificationStatus] = useState<'pending' | 'success' | 'error'>('pending');
  const [verificationError, setVerificationError] = useState<string | null>(null);

  // Handle email verification from URL token
  useEffect(() => {
    const token = searchParams.get('token');
    if (token && location.pathname.includes('/verify')) {
      // Verify the email token
      verifyEmailMutation.mutate(
        { token },
        {
          onSuccess: (result) => {
            setVerificationStatus('success');
            setRegistrationId(result.registration_id);
            localStorage.setItem('trial_registration_id', result.registration_id);
            // Go to payment step
            setCurrentStep('payment');
          },
          onError: (error) => {
            setVerificationStatus('error');
            setVerificationError(error.message);
          },
        }
      );
    }
  }, [searchParams, location.pathname]);

  // Save registration ID to localStorage when it changes
  useEffect(() => {
    if (registrationId) {
      localStorage.setItem('trial_registration_id', registrationId);
    }
  }, [registrationId]);

  // Navigation helpers
  const goToStep = useCallback((step: TrialStep) => {
    setCurrentStep(step);
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const goToNextStep = useCallback(() => {
    const currentIndex = TRIAL_STEPS.indexOf(currentStep);
    if (currentIndex < TRIAL_STEPS.length - 1) {
      goToStep(TRIAL_STEPS[currentIndex + 1]);
    }
  }, [currentStep, goToStep]);

  const goToPrevStep = useCallback(() => {
    const currentIndex = TRIAL_STEPS.indexOf(currentStep);
    if (currentIndex > 0) {
      goToStep(TRIAL_STEPS[currentIndex - 1]);
    }
  }, [currentStep, goToStep]);

  // Step handlers
  const handlePersonalInfoNext = (data: PersonalInfo) => {
    setFormData((prev) => ({ ...prev, personal: data }));
    goToNextStep();
  };

  const handleCompanyInfoNext = (data: CompanyInfo) => {
    setFormData((prev) => ({ ...prev, company: data }));
    goToNextStep();
  };

  const handlePricingNext = (data: PricingInfo) => {
    setFormData((prev) => ({ ...prev, pricing: data }));
    goToNextStep();
  };

  const handleValidationNext = (regId: string) => {
    setRegistrationId(regId);
    goToNextStep();
  };

  const handleEmailVerified = () => {
    goToNextStep();
  };

  const handlePaymentSuccess = (result: TrialCompleteResponse) => {
    setCompleteResult(result);
    goToStep('success');
  };

  // Render current step
  const renderStep = () => {
    // Show verification in progress
    if (verifyEmailMutation.isPending) {
      return (
        <div className="trial-verification-loading">
          <div className="trial-spinner-large"></div>
          <h2>Vérification de votre email...</h2>
          <p>Veuillez patienter</p>
        </div>
      );
    }

    // Show verification error
    if (verificationStatus === 'error' && verificationError) {
      return (
        <div className="trial-verification-error">
          <h2>Erreur de vérification</h2>
          <p>{verificationError}</p>
          <button
            className="trial-btn trial-btn-primary"
            onClick={() => {
              setVerificationStatus('pending');
              setVerificationError(null);
              setCurrentStep('personal');
              window.history.pushState({}, '', '/essai-gratuit');
            }}
          >
            Recommencer l'inscription
          </button>
        </div>
      );
    }

    switch (currentStep) {
      case 'personal':
        return (
          <StepPersonalInfo
            data={formData.personal}
            onNext={handlePersonalInfoNext}
          />
        );

      case 'company':
        return (
          <StepCompanyInfo
            data={formData.company}
            onNext={handleCompanyInfoNext}
            onBack={goToPrevStep}
          />
        );

      case 'pricing':
        return (
          <StepPricingReminder
            data={formData.pricing}
            onNext={handlePricingNext}
            onBack={goToPrevStep}
          />
        );

      case 'validation':
        return (
          <StepValidation
            data={formData.validation}
            formData={formData}
            onNext={handleValidationNext}
            onBack={goToPrevStep}
          />
        );

      case 'email':
        return (
          <StepEmailVerification
            registrationId={registrationId!}
            email={formData.personal.email}
            onNext={handleEmailVerified}
          />
        );

      case 'payment':
        return (
          <StepPayment
            registrationId={registrationId!}
            onSuccess={handlePaymentSuccess}
            onBack={goToPrevStep}
          />
        );

      case 'success':
        return completeResult ? (
          <StepSuccess result={completeResult} />
        ) : null;

      default:
        return null;
    }
  };

  return (
    <div className="trial-page">
      {/* Header */}
      <header className="trial-header">
        <div className="trial-header-content">
          <Link to="/" className="trial-logo">
            <AzalscoreLogo size={36} />
            <span className="trial-logo-text">AZALSCORE</span>
          </Link>
          <div className="trial-header-right">
            <span>Deja un compte ?</span>
            <Link to="/login" className="trial-header-login">
              Se connecter
            </Link>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="trial-main">
        <div className="trial-container">
          {/* Progress bar (hidden on success) */}
          {currentStep !== 'success' && (
            <ProgressBar currentStep={currentStep} />
          )}

          {/* Step content */}
          <div className="trial-content">
            {renderStep()}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="trial-footer">
        <div className="trial-footer-content">
          <p>
            &copy; 2026 AZALSCORE - MASITH Developpement. Tous droits reserves.
          </p>
          <div className="trial-footer-links">
            <Link to="/mentions-legales">Mentions legales</Link>
            <Link to="/confidentialite">Confidentialite</Link>
            <Link to="/cgv">CGV</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default TrialRegistration;
