/**
 * AZALSCORE UI Engine - State View Components
 * LoadingState, ErrorState, EmptyState - presentational components
 * for standardized loading/error/empty UX.
 */

import React, { useState, useEffect, useRef } from 'react';
import { Loader2, AlertCircle, Inbox, RefreshCw, ArrowLeft } from 'lucide-react';

// ============================================================
// LOADING STATE
// ============================================================

export interface LoadingStateProps {
  /** Timeout in ms before showing slow-loading message (default: 5000) */
  timeoutMs?: number;
  /** Retry callback shown after timeout */
  onRetry?: () => void;
  /** Custom message */
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  timeoutMs = 5000,
  onRetry,
  message,
  className,
}) => {
  const [isSlow, setIsSlow] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    timerRef.current = setTimeout(() => setIsSlow(true), timeoutMs);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [timeoutMs]);

  return (
    <div className={`azals-state azals-state--loading ${className || ''}`} role="status" aria-live="polite">
      <Loader2 className="azals-state__spinner azals-spin" size={32} />
      <p className="azals-state__message">
        {message || (isSlow ? 'Le chargement prend plus de temps que prevu.' : 'Chargement...')}
      </p>
      {isSlow && onRetry && (
        <button className="azals-btn azals-btn--secondary azals-state__action" onClick={onRetry} type="button">
          <RefreshCw size={16} />
          Reessayer
        </button>
      )}
    </div>
  );
};

// ============================================================
// ERROR STATE
// ============================================================

export interface ErrorStateProps {
  /** Error title */
  title?: string;
  /** Error message / description */
  message?: string;
  /** Retry callback */
  onRetry?: () => void;
  /** Back callback */
  onBack?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Erreur de chargement',
  message = 'Impossible de charger les donnees. Verifiez votre connexion et reessayez.',
  onRetry,
  onBack,
  className,
}) => (
  <div className={`azals-state azals-state--error ${className || ''}`} role="alert">
    <AlertCircle className="azals-state__icon azals-state__icon--error" size={48} />
    <h3 className="azals-state__title">{title}</h3>
    <p className="azals-state__message">{message}</p>
    <div className="azals-state__actions">
      {onBack && (
        <button className="azals-btn azals-btn--ghost azals-state__action" onClick={onBack} type="button">
          <ArrowLeft size={16} />
          Retour
        </button>
      )}
      {onRetry && (
        <button className="azals-btn azals-btn--primary azals-state__action" onClick={onRetry} type="button">
          <RefreshCw size={16} />
          Reessayer
        </button>
      )}
    </div>
  </div>
);

// ============================================================
// EMPTY STATE
// ============================================================

export interface EmptyStateProps {
  /** Title for empty state */
  title?: string;
  /** Description message */
  message?: string;
  /** Optional icon override */
  icon?: React.ReactNode;
  /** Optional action button */
  action?: {
    label: string;
    onClick: () => void;
    icon?: React.ReactNode;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'Aucune donnee',
  message = 'Aucun element a afficher pour le moment.',
  icon,
  action,
  className,
}) => (
  <div className={`azals-state azals-state--empty ${className || ''}`}>
    <div className="azals-state__icon azals-state__icon--empty">
      {icon || <Inbox size={48} />}
    </div>
    <h3 className="azals-state__title">{title}</h3>
    <p className="azals-state__message">{message}</p>
    {action && (
      <button className="azals-btn azals-btn--primary azals-state__action" onClick={action.onClick} type="button">
        {action.icon}
        {action.label}
      </button>
    )}
  </div>
);
