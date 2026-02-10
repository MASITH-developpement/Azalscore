/**
 * AZALSCORE - Trial Progress Bar
 * Barre de progression pour le formulaire multi-etapes
 */

import React from 'react';
import { Check } from 'lucide-react';
import { TRIAL_STEPS, STEP_TITLES, type TrialStep } from '../types';

interface ProgressBarProps {
  currentStep: TrialStep;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ currentStep }) => {
  const currentIndex = TRIAL_STEPS.indexOf(currentStep);

  // Only show first 6 steps in progress bar (success is final screen)
  const displaySteps = TRIAL_STEPS.slice(0, 6);

  return (
    <div className="trial-progress">
      <div className="trial-progress-bar">
        {displaySteps.map((step, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = step === currentStep;
          const isUpcoming = index > currentIndex;

          return (
            <React.Fragment key={step}>
              {/* Step circle */}
              <div
                className={`trial-progress-step ${
                  isCompleted
                    ? 'trial-progress-step--completed'
                    : isCurrent
                    ? 'trial-progress-step--current'
                    : 'trial-progress-step--upcoming'
                }`}
              >
                {isCompleted ? (
                  <Check size={14} />
                ) : (
                  <span>{index + 1}</span>
                )}
              </div>

              {/* Connector line (except after last step) */}
              {index < displaySteps.length - 1 && (
                <div
                  className={`trial-progress-line ${
                    isCompleted ? 'trial-progress-line--completed' : ''
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Step title */}
      <div className="trial-progress-title">
        {STEP_TITLES[currentStep]}
      </div>
    </div>
  );
};

export default ProgressBar;
