/**
 * AZALSCORE UI Engine - Module Error Handling
 * Gestion centralisée des erreurs UI
 * Affichage et remontée - AUCUNE logique de récupération métier
 */

import { create } from 'zustand';
import type { ApiError } from '@/types';

// ============================================================
// TYPES
// ============================================================

export type ErrorSeverity = 'info' | 'warning' | 'error' | 'critical';

export interface UIError {
  id: string;
  code: string;
  message: string;
  severity: ErrorSeverity;
  timestamp: Date;
  context?: string;
  dismissible: boolean;
  autoDismiss?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface ErrorStore {
  errors: UIError[];
  addError: (error: Omit<UIError, 'id' | 'timestamp'>) => string;
  removeError: (id: string) => void;
  clearErrors: () => void;
  clearBySeverity: (severity: ErrorSeverity) => void;
}

// ============================================================
// STORE ERREURS (ZUSTAND)
// ============================================================

export const useErrorStore = create<ErrorStore>((set, get) => ({
  errors: [],

  addError: (error): string => {
    const id = `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newError: UIError = {
      ...error,
      id,
      timestamp: new Date(),
    };

    set((state) => ({
      errors: [...state.errors, newError],
    }));

    // Auto-dismiss si configuré
    if (error.autoDismiss && error.autoDismiss > 0) {
      setTimeout(() => {
        get().removeError(id);
      }, error.autoDismiss);
    }

    return id;
  },

  removeError: (id): void => {
    set((state) => ({
      errors: state.errors.filter((e) => e.id !== id),
    }));
  },

  clearErrors: (): void => {
    set({ errors: [] });
  },

  clearBySeverity: (severity): void => {
    set((state) => ({
      errors: state.errors.filter((e) => e.severity !== severity),
    }));
  },
}));

// ============================================================
// HOOKS UTILITAIRES
// ============================================================

export const useErrors = () => {
  const store = useErrorStore();
  return {
    errors: store.errors,
    addError: store.addError,
    removeError: store.removeError,
    clearErrors: store.clearErrors,
  };
};

export const useErrorCount = (): number => {
  return useErrorStore((state) => state.errors.length);
};

export const useCriticalErrors = (): UIError[] => {
  return useErrorStore((state) =>
    state.errors.filter((e) => e.severity === 'critical')
  );
};

// ============================================================
// FONCTIONS UTILITAIRES
// ============================================================

/**
 * Convertit une erreur API en erreur UI
 */
export const apiErrorToUIError = (
  apiErrors: ApiError[],
  context?: string
): Omit<UIError, 'id' | 'timestamp'> => {
  const firstError = apiErrors[0];
  const severity = getSeverityFromCode(firstError?.code);

  return {
    code: firstError?.code || 'UNKNOWN',
    message: apiErrors.map((e) => e.message).join('. '),
    severity,
    context,
    dismissible: severity !== 'critical',
    autoDismiss: severity === 'info' ? 5000 : undefined,
  };
};

/**
 * Détermine la sévérité selon le code d'erreur
 */
const getSeverityFromCode = (code?: string): ErrorSeverity => {
  if (!code) return 'error';

  if (code.startsWith('AZALS-SEC-') || code.startsWith('AZALS-CRIT-')) {
    return 'critical';
  }
  if (code.startsWith('AZALS-WARN-') || code === 'VALIDATION_ERROR') {
    return 'warning';
  }
  if (code.startsWith('AZALS-INFO-')) {
    return 'info';
  }
  return 'error';
};

/**
 * Crée une erreur d'information
 */
export const showInfo = (message: string, autoDismiss = 5000): string => {
  return useErrorStore.getState().addError({
    code: 'INFO',
    message,
    severity: 'info',
    dismissible: true,
    autoDismiss,
  });
};

/**
 * Crée une erreur d'avertissement
 */
export const showWarning = (message: string, context?: string): string => {
  return useErrorStore.getState().addError({
    code: 'WARNING',
    message,
    severity: 'warning',
    context,
    dismissible: true,
    autoDismiss: 10000,
  });
};

/**
 * Crée une erreur standard
 */
export const showError = (message: string, context?: string): string => {
  return useErrorStore.getState().addError({
    code: 'ERROR',
    message,
    severity: 'error',
    context,
    dismissible: true,
  });
};

/**
 * Crée une erreur critique (non dismissible)
 */
export const showCritical = (
  message: string,
  context?: string,
  action?: UIError['action']
): string => {
  return useErrorStore.getState().addError({
    code: 'CRITICAL',
    message,
    severity: 'critical',
    context,
    dismissible: false,
    action,
  });
};

// ============================================================
// BOUNDARY ERROR HANDLER
// ============================================================

export class UIErrorBoundary {
  static handleError(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('UI Error Boundary caught:', error, errorInfo);

    useErrorStore.getState().addError({
      code: 'UI_CRASH',
      message: 'Une erreur inattendue est survenue dans l\'interface',
      severity: 'critical',
      context: error.message,
      dismissible: false,
      action: {
        label: 'Recharger',
        onClick: () => window.location.reload(),
      },
    });
  }
}

// ============================================================
// ERROR CODES AZALSCORE
// ============================================================

export const ERROR_CODES = {
  // Authentification
  AUTH_EXPIRED: 'AZALS-AUTH-001',
  AUTH_INVALID: 'AZALS-AUTH-002',
  AUTH_2FA_REQUIRED: 'AZALS-AUTH-003',

  // Capacités
  CAP_DENIED: 'AZALS-CAP-001',
  CAP_MISSING: 'AZALS-CAP-002',

  // Réseau
  NET_OFFLINE: 'AZALS-NET-001',
  NET_TIMEOUT: 'AZALS-NET-002',
  NET_SERVER: 'AZALS-NET-003',

  // Validation
  VAL_REQUIRED: 'AZALS-VAL-001',
  VAL_FORMAT: 'AZALS-VAL-002',
  VAL_RANGE: 'AZALS-VAL-003',

  // Module
  MOD_UNAVAILABLE: 'AZALS-MOD-001',
  MOD_INACTIVE: 'AZALS-MOD-002',

  // Break-Glass
  BG_DENIED: 'AZALS-BG-001',
  BG_PHRASE_MISMATCH: 'AZALS-BG-002',
  BG_AUTH_FAILED: 'AZALS-BG-003',
} as const;
