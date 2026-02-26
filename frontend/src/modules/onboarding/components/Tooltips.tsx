/**
 * AZALSCORE - Systeme de Tooltips de Formation
 * ==============================================
 * Tooltips intelligents avec aide contextuelle.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Info, Lightbulb, AlertCircle, CheckCircle, ExternalLink, X } from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

export type TooltipType = 'info' | 'tip' | 'warning' | 'success';
export type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';

interface TooltipProps {
  content: string | React.ReactNode;
  type?: TooltipType;
  position?: TooltipPosition;
  children: React.ReactNode;
  showOnHover?: boolean;
  showOnClick?: boolean;
  delay?: number;
  learnMoreUrl?: string;
  persistent?: boolean;
}

interface FeatureHighlightProps {
  title: string;
  description: string;
  isNew?: boolean;
  onDismiss?: () => void;
  children: React.ReactNode;
}

interface FieldHintProps {
  hint: string;
  example?: string;
  required?: boolean;
}

// ============================================================================
// TOOLTIP COMPONENT
// ============================================================================

export function Tooltip({
  content,
  type = 'info',
  position = 'top',
  children,
  showOnHover = true,
  showOnClick = false,
  delay = 300,
  learnMoreUrl,
  persistent = false,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const typeStyles: Record<TooltipType, { bg: string; icon: React.ReactNode; border: string }> = {
    info: {
      bg: 'bg-gray-900',
      icon: <Info className="w-4 h-4 text-blue-400" />,
      border: 'border-gray-700',
    },
    tip: {
      bg: 'bg-amber-50',
      icon: <Lightbulb className="w-4 h-4 text-amber-500" />,
      border: 'border-amber-200',
    },
    warning: {
      bg: 'bg-red-50',
      icon: <AlertCircle className="w-4 h-4 text-red-500" />,
      border: 'border-red-200',
    },
    success: {
      bg: 'bg-green-50',
      icon: <CheckCircle className="w-4 h-4 text-green-500" />,
      border: 'border-green-200',
    },
  };

  const style = typeStyles[type];
  const textColor = type === 'info' ? 'text-white' : 'text-gray-800';

  const show = () => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setCoords({
        x: rect.left + rect.width / 2,
        y: rect.top,
      });
    }
    timeoutRef.current = setTimeout(() => setIsVisible(true), delay);
  };

  const hide = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (!persistent) setIsVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const getPositionStyles = (): React.CSSProperties => {
    if (!triggerRef.current) return {};

    const rect = triggerRef.current.getBoundingClientRect();
    const padding = 8;

    switch (position) {
      case 'top':
        return {
          bottom: `${window.innerHeight - rect.top + padding}px`,
          left: `${rect.left + rect.width / 2}px`,
          transform: 'translateX(-50%)',
        };
      case 'bottom':
        return {
          top: `${rect.bottom + padding}px`,
          left: `${rect.left + rect.width / 2}px`,
          transform: 'translateX(-50%)',
        };
      case 'left':
        return {
          top: `${rect.top + rect.height / 2}px`,
          right: `${window.innerWidth - rect.left + padding}px`,
          transform: 'translateY(-50%)',
        };
      case 'right':
        return {
          top: `${rect.top + rect.height / 2}px`,
          left: `${rect.right + padding}px`,
          transform: 'translateY(-50%)',
        };
      default:
        return {};
    }
  };

  return (
    <div className="relative inline-block">
      <div
        ref={triggerRef}
        onMouseEnter={showOnHover ? show : undefined}
        onMouseLeave={showOnHover ? hide : undefined}
        onClick={showOnClick ? () => setIsVisible(!isVisible) : undefined}
      >
        {children}
      </div>

      {isVisible && (
        <div
          ref={tooltipRef}
          className={`fixed z-[9999] px-3 py-2 rounded-lg shadow-lg ${style.bg} border ${style.border} max-w-xs animate-fadeIn`}
          style={getPositionStyles()}
        >
          <div className="flex items-start gap-2">
            {style.icon}
            <div className={`text-sm ${textColor}`}>
              {content}
              {learnMoreUrl && (
                <a
                  href={learnMoreUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-blue-400 hover:text-blue-300 mt-1 text-xs"
                >
                  En savoir plus
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
            {persistent && (
              <button
                onClick={() => setIsVisible(false)}
                className="text-gray-400 hover:text-gray-200 ml-2"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>

          {/* Arrow */}
          <div
            className={`absolute w-2 h-2 ${style.bg} transform rotate-45 ${
              position === 'top' ? '-bottom-1 left-1/2 -translate-x-1/2' :
              position === 'bottom' ? '-top-1 left-1/2 -translate-x-1/2' :
              position === 'left' ? '-right-1 top-1/2 -translate-y-1/2' :
              '-left-1 top-1/2 -translate-y-1/2'
            }`}
          />
        </div>
      )}
    </div>
  );
}

// ============================================================================
// FEATURE HIGHLIGHT
// ============================================================================

export function FeatureHighlight({
  title,
  description,
  isNew = false,
  onDismiss,
  children,
}: FeatureHighlightProps) {
  const [isVisible, setIsVisible] = useState(true);

  const handleDismiss = () => {
    setIsVisible(false);
    onDismiss?.();
  };

  if (!isVisible) return <>{children}</>;

  return (
    <div className="relative">
      {children}
      <div className="absolute -top-2 -right-2 z-10">
        <div className="relative">
          {/* Pulse effect */}
          <span className="absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75 animate-ping" />
          <span className="relative inline-flex rounded-full h-4 w-4 bg-blue-500 items-center justify-center">
            {isNew && <span className="text-[8px] text-white font-bold">N</span>}
          </span>
        </div>
      </div>

      {/* Popup */}
      <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-blue-200 p-4 z-20 animate-slideDown">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
            <Lightbulb className="w-4 h-4 text-blue-600" />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-semibold text-gray-900 text-sm">{title}</h4>
              {isNew && (
                <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full font-medium">
                  NOUVEAU
                </span>
              )}
            </div>
            <p className="text-xs text-gray-600">{description}</p>
          </div>
        </div>
        <button
          onClick={handleDismiss}
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// FIELD HINT
// ============================================================================

export function FieldHint({ hint, example, required }: FieldHintProps) {
  return (
    <div className="mt-1 text-xs text-gray-500">
      <p className="flex items-center gap-1">
        <Info className="w-3 h-3" />
        {hint}
        {required && <span className="text-red-500 ml-1">*</span>}
      </p>
      {example && (
        <p className="mt-0.5 text-gray-400 italic">
          Ex: {example}
        </p>
      )}
    </div>
  );
}

// ============================================================================
// INLINE HELP
// ============================================================================

interface InlineHelpProps {
  text: string;
  expandedText?: string;
}

export function InlineHelp({ text, expandedText }: InlineHelpProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 my-2">
      <div className="flex items-start gap-2">
        <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800">
          <p>{text}</p>
          {expandedText && (
            <>
              {isExpanded && <p className="mt-2">{expandedText}</p>}
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-blue-600 hover:text-blue-800 text-xs mt-1"
              >
                {isExpanded ? 'Voir moins' : 'En savoir plus'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// STEP INDICATOR
// ============================================================================

interface StepIndicatorProps {
  steps: string[];
  currentStep: number;
  onStepClick?: (index: number) => void;
}

export function StepIndicator({ steps, currentStep, onStepClick }: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-2 py-4">
      {steps.map((step, index) => {
        const isActive = index === currentStep;
        const isCompleted = index < currentStep;
        const isClickable = onStepClick && index < currentStep;

        return (
          <React.Fragment key={index}>
            <button
              onClick={() => isClickable && onStepClick(index)}
              disabled={!isClickable}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm transition-all ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : isCompleted
                  ? 'bg-green-100 text-green-700 hover:bg-green-200'
                  : 'bg-gray-100 text-gray-400'
              } ${isClickable ? 'cursor-pointer' : 'cursor-default'}`}
            >
              {isCompleted ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <span className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center text-xs">
                  {index + 1}
                </span>
              )}
              <span className="hidden sm:inline">{step}</span>
            </button>
            {index < steps.length - 1 && (
              <div className={`w-8 h-0.5 ${isCompleted ? 'bg-green-300' : 'bg-gray-200'}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ============================================================================
// ACHIEVEMENT BADGE
// ============================================================================

interface AchievementBadgeProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  unlocked: boolean;
  onUnlock?: () => void;
}

export function AchievementBadge({
  title,
  description,
  icon,
  unlocked,
  onUnlock,
}: AchievementBadgeProps) {
  useEffect(() => {
    if (unlocked && onUnlock) {
      onUnlock();
    }
  }, [unlocked, onUnlock]);

  return (
    <div
      className={`relative p-4 rounded-xl border-2 transition-all ${
        unlocked
          ? 'border-amber-300 bg-gradient-to-br from-amber-50 to-yellow-50'
          : 'border-gray-200 bg-gray-50 opacity-50'
      }`}
    >
      <div className="flex items-center gap-3">
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center ${
            unlocked ? 'bg-amber-100' : 'bg-gray-200'
          }`}
        >
          {icon}
        </div>
        <div>
          <h4 className="font-semibold text-gray-900">{title}</h4>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
      </div>
      {unlocked && (
        <div className="absolute -top-2 -right-2">
          <CheckCircle className="w-6 h-6 text-green-500 bg-white rounded-full" />
        </div>
      )}
    </div>
  );
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  Tooltip,
  FeatureHighlight,
  FieldHint,
  InlineHelp,
  StepIndicator,
  AchievementBadge,
};
