/**
 * AZALSCORE - Trial Registration Page
 * Formulaire multi-etapes d'inscription a l'essai gratuit
 */

import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
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
  // Current step
  const [currentStep, setCurrentStep] = useState<TrialStep>('personal');

  // Form data
  const [formData, setFormData] = useState<TrialFormData>(initialFormData);

  // Registration state (after step 4)
  const [registrationId, setRegistrationId] = useState<string | null>(null);

  // Final result (after step 6)
  const [completeResult, setCompleteResult] = useState<TrialCompleteResponse | null>(null);

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
            onNext={goToNextStep}
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
