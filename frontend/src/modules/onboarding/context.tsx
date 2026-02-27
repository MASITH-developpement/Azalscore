/**
 * AZALSCORE Module - Onboarding - Context
 * Provider et hook pour le systeme de tours guides
 */

import React, { useState, useEffect, createContext, useContext, useCallback } from 'react';
import type { OnboardingTour, UserProgress } from './types';
import { ONBOARDING_TOURS } from './constants';
import { TourOverlay } from './components/TourOverlay';

// ============================================================================
// TYPES
// ============================================================================

interface OnboardingContextType {
  isActive: boolean;
  currentTour: OnboardingTour | null;
  currentStepIndex: number;
  progress: UserProgress;
  startTour: (tourId: string) => void;
  nextStep: () => void;
  prevStep: () => void;
  endTour: () => void;
  skipTour: () => void;
  showHelp: (context: string) => void;
}

// ============================================================================
// CONTEXT
// ============================================================================

const OnboardingContext = createContext<OnboardingContextType | null>(null);

export const useOnboarding = () => {
  const context = useContext(OnboardingContext);
  if (!context) {
    throw new Error('useOnboarding must be used within OnboardingProvider');
  }
  return context;
};

// ============================================================================
// DEFAULT PROGRESS
// ============================================================================

const defaultProgress: UserProgress = {
  completedTours: [],
  completedSteps: {},
  achievements: [],
  totalProgress: 0,
  preferences: {
    showTips: true,
    showHighlights: true,
    autoStartTours: false,
    dismissedFeatures: [],
  },
};

// ============================================================================
// PROVIDER
// ============================================================================

interface OnboardingProviderProps {
  children: React.ReactNode;
}

export function OnboardingProvider({ children }: OnboardingProviderProps) {
  const [isActive, setIsActive] = useState(false);
  const [currentTour, setCurrentTour] = useState<OnboardingTour | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [progress, setProgress] = useState<UserProgress>(defaultProgress);

  // Charger la progression depuis localStorage
  useEffect(() => {
    const saved = localStorage.getItem('azalscore_onboarding_progress');
    if (saved) {
      try {
        setProgress({ ...defaultProgress, ...JSON.parse(saved) });
      } catch {
        // Ignore parse errors
      }
    }
  }, []);

  // Sauvegarder la progression
  const saveProgress = useCallback((newProgress: UserProgress) => {
    setProgress(newProgress);
    localStorage.setItem('azalscore_onboarding_progress', JSON.stringify(newProgress));
  }, []);

  const startTour = useCallback((tourId: string) => {
    const tour = ONBOARDING_TOURS.find(t => t.id === tourId);
    if (tour) {
      setCurrentTour(tour);
      setCurrentStepIndex(0);
      setIsActive(true);
      saveProgress({
        ...progress,
        currentTour: tourId,
        currentStep: 0,
      });
    }
  }, [progress, saveProgress]);

  const nextStep = useCallback(() => {
    if (!currentTour) return;

    if (currentStepIndex < currentTour.steps.length - 1) {
      const newIndex = currentStepIndex + 1;
      setCurrentStepIndex(newIndex);
      saveProgress({
        ...progress,
        currentStep: newIndex,
      });
    } else {
      // Tour termine
      const newCompleted = [...progress.completedTours, currentTour.id];
      const newProgress = Math.round((newCompleted.length / ONBOARDING_TOURS.length) * 100);
      saveProgress({
        ...progress,
        completedTours: newCompleted,
        currentTour: undefined,
        currentStep: undefined,
        totalProgress: newProgress,
      });
      setIsActive(false);
      setCurrentTour(null);
    }
  }, [currentTour, currentStepIndex, progress, saveProgress]);

  const prevStep = useCallback(() => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
    }
  }, [currentStepIndex]);

  const endTour = useCallback(() => {
    if (currentTour) {
      const newCompleted = [...progress.completedTours, currentTour.id];
      saveProgress({
        ...progress,
        completedTours: newCompleted,
        currentTour: undefined,
        currentStep: undefined,
        totalProgress: Math.round((newCompleted.length / ONBOARDING_TOURS.length) * 100),
      });
    }
    setIsActive(false);
    setCurrentTour(null);
  }, [currentTour, progress, saveProgress]);

  const skipTour = useCallback(() => {
    setIsActive(false);
    setCurrentTour(null);
    saveProgress({
      ...progress,
      currentTour: undefined,
      currentStep: undefined,
    });
  }, [progress, saveProgress]);

  const showHelp = useCallback((context: string) => {
    // Ouvrir l'aide contextuelle
    console.log('Show help for:', context);
  }, []);

  return (
    <OnboardingContext.Provider
      value={{
        isActive,
        currentTour,
        currentStepIndex,
        progress,
        startTour,
        nextStep,
        prevStep,
        endTour,
        skipTour,
        showHelp,
      }}
    >
      {children}
      {isActive && currentTour && (
        <TourOverlay
          tour={currentTour}
          stepIndex={currentStepIndex}
          onNext={nextStep}
          onPrev={prevStep}
          onSkip={skipTour}
          onEnd={endTour}
        />
      )}
    </OnboardingContext.Provider>
  );
}
