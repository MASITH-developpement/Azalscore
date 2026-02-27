/**
 * AZALSCORE Module - Onboarding - Tour Overlay
 * Overlay de tour guide
 */

import React, { useState, useEffect } from 'react';
import { X, ChevronRight, ChevronLeft, Check, GraduationCap } from 'lucide-react';
import type { OnboardingTour } from '../types';

// ============================================================================
// TYPES
// ============================================================================

export interface TourOverlayProps {
  tour: OnboardingTour;
  stepIndex: number;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
  onEnd: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function TourOverlay({ tour, stepIndex, onNext, onPrev, onSkip, onEnd }: TourOverlayProps) {
  const step = tour.steps[stepIndex];
  const isFirst = stepIndex === 0;
  const isLast = stepIndex === tour.steps.length - 1;

  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);

  useEffect(() => {
    if (step.target) {
      const element = document.querySelector(step.target);
      if (element) {
        const rect = element.getBoundingClientRect();
        setTargetRect(rect);
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        setTargetRect(null);
      }
    } else {
      setTargetRect(null);
    }
  }, [step.target]);

  const getTooltipPosition = () => {
    if (!targetRect || step.position === 'center') {
      return {
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
    }

    const padding = 20;
    const positions: Record<string, React.CSSProperties> = {
      top: {
        bottom: `${window.innerHeight - targetRect.top + padding}px`,
        left: `${targetRect.left + targetRect.width / 2}px`,
        transform: 'translateX(-50%)',
      },
      bottom: {
        top: `${targetRect.bottom + padding}px`,
        left: `${targetRect.left + targetRect.width / 2}px`,
        transform: 'translateX(-50%)',
      },
      left: {
        top: `${targetRect.top + targetRect.height / 2}px`,
        right: `${window.innerWidth - targetRect.left + padding}px`,
        transform: 'translateY(-50%)',
      },
      right: {
        top: `${targetRect.top + targetRect.height / 2}px`,
        left: `${targetRect.right + padding}px`,
        transform: 'translateY(-50%)',
      },
    };

    return positions[step.position || 'bottom'];
  };

  return (
    <div className="fixed inset-0 z-[9999]">
      {/* Overlay avec decoupe pour le target */}
      <div className="absolute inset-0 bg-black/60">
        {targetRect && (
          <div
            className="absolute bg-transparent shadow-[0_0_0_9999px_rgba(0,0,0,0.6)] rounded-lg ring-4 ring-blue-500 ring-offset-2"
            style={{
              top: targetRect.top - 4,
              left: targetRect.left - 4,
              width: targetRect.width + 8,
              height: targetRect.height + 8,
            }}
          />
        )}
      </div>

      {/* Tooltip */}
      <div
        className="absolute bg-white rounded-xl shadow-2xl p-6 max-w-md z-10"
        style={getTooltipPosition()}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">{tour.name}</p>
              <p className="text-sm text-gray-400">
                Etape {stepIndex + 1} / {tour.steps.length}
              </p>
            </div>
          </div>
          <button
            onClick={onSkip}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {step.title}
        </h3>
        <p className="text-gray-600 mb-6">
          {step.description}
        </p>

        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-4">
          <div
            className="bg-blue-600 h-1.5 rounded-full transition-all"
            style={{ width: `${((stepIndex + 1) / tour.steps.length) * 100}%` }}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <button
            onClick={onPrev}
            disabled={isFirst}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
              isFirst
                ? 'text-gray-300 cursor-not-allowed'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            Precedent
          </button>

          <div className="flex gap-2">
            <button
              onClick={onSkip}
              className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700"
            >
              Passer
            </button>
            <button
              onClick={isLast ? onEnd : onNext}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
            >
              {isLast ? (
                <>
                  Terminer
                  <Check className="w-4 h-4" />
                </>
              ) : (
                <>
                  Suivant
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TourOverlay;
