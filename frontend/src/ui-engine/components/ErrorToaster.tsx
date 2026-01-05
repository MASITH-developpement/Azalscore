/**
 * AZALSCORE UI Engine - Error Toaster
 * Affichage des erreurs et notifications
 */

import React from 'react';
import { clsx } from 'clsx';
import { X, AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react';
import { useErrorStore, type UIError, type ErrorSeverity } from '@core/error-handling';

// ============================================================
// ICON MAP
// ============================================================

const SEVERITY_ICONS: Record<ErrorSeverity, React.FC<{ size: number }>> = {
  info: Info,
  warning: AlertTriangle,
  error: AlertCircle,
  critical: AlertCircle,
};

// ============================================================
// ERROR TOAST ITEM
// ============================================================

interface ErrorToastItemProps {
  error: UIError;
  onDismiss: () => void;
}

const ErrorToastItem: React.FC<ErrorToastItemProps> = ({ error, onDismiss }) => {
  const Icon = SEVERITY_ICONS[error.severity];

  return (
    <div
      className={clsx(
        'azals-error-toast',
        `azals-error-toast--${error.severity}`
      )}
      role="alert"
    >
      <div className="azals-error-toast__icon">
        <Icon size={20} />
      </div>

      <div className="azals-error-toast__content">
        <p className="azals-error-toast__message">{error.message}</p>
        {error.context && (
          <p className="azals-error-toast__context">{error.context}</p>
        )}
      </div>

      <div className="azals-error-toast__actions">
        {error.action && (
          <button
            className="azals-error-toast__action-btn"
            onClick={error.action.onClick}
          >
            {error.action.label}
          </button>
        )}
        {error.dismissible && (
          <button
            className="azals-error-toast__close"
            onClick={onDismiss}
            aria-label="Fermer"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
};

// ============================================================
// ERROR TOASTER
// ============================================================

export const ErrorToaster: React.FC = () => {
  const { errors, removeError } = useErrorStore();

  if (errors.length === 0) return null;

  return (
    <div className="azals-error-toaster" aria-live="polite">
      {errors.map((error) => (
        <ErrorToastItem
          key={error.id}
          error={error}
          onDismiss={() => removeError(error.id)}
        />
      ))}
    </div>
  );
};

export default ErrorToaster;
