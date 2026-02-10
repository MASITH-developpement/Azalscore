/**
 * AZALSCORE UI Engine - Module Error Handling
 * Gestion centralisée des erreurs UI
 * Affichage et remontée - AUCUNE logique de récupération métier
 */

import { create } from 'zustand';
import type { ApiError, Result } from '@/types';

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

// ============================================================
// HTTP ERROR HANDLING - STANDARDIZED BACKEND FORMAT
// ============================================================

/**
 * Format standardise des erreurs HTTP backend AZALS
 */
export interface StandardHttpError {
  error: string;
  message: string;
  code: number;
  path?: string;
  trace_id?: string;
  details?: unknown[];
}

/**
 * Verifie si l'erreur est au format standardise AZALS
 */
export const isStandardHttpError = (error: unknown): error is StandardHttpError => {
  if (typeof error !== 'object' || error === null) return false;
  const e = error as Record<string, unknown>;
  return (
    typeof e.error === 'string' &&
    typeof e.message === 'string' &&
    typeof e.code === 'number'
  );
};

/**
 * Determine si une redirection vers la page d'erreur est necessaire
 * selon le code HTTP
 */
export const shouldRedirectToErrorPage = (statusCode: number): boolean => {
  return [401, 403, 404, 500].includes(statusCode);
};

/**
 * Redirige vers la page d'erreur appropriee
 * NE redirige PAS automatiquement pour 401 si c'est une erreur d'API
 * (le frontend gere la deconnexion)
 */
export const redirectToErrorPage = (
  statusCode: number,
  options?: {
    skipFor401?: boolean;
    inNewTab?: boolean;
  }
): void => {
  const { skipFor401 = true, inNewTab = false } = options || {};

  // Ne pas rediriger pour 401 si skipFor401 est true (comportement par defaut)
  // car le frontend gere deja la deconnexion via le refresh token
  if (statusCode === 401 && skipFor401) {
    return;
  }

  const errorPageUrl = `/errors/${statusCode}`;

  if (inNewTab) {
    window.open(errorPageUrl, '_blank');
  } else {
    window.location.href = errorPageUrl;
  }
};

/**
 * Gestionnaire d'erreur HTTP standardise
 * Parse l'erreur et affiche une notification appropriee
 */
export const handleHttpError = (
  statusCode: number,
  errorData?: StandardHttpError | unknown,
  options?: {
    showNotification?: boolean;
    redirectOnError?: boolean;
    context?: string;
  }
): void => {
  const {
    showNotification = true,
    redirectOnError = false,
    context
  } = options || {};

  // Parser l'erreur standardisee
  const standardError = isStandardHttpError(errorData)
    ? errorData
    : {
        error: 'unknown',
        message: 'Une erreur inattendue est survenue',
        code: statusCode
      };

  // Afficher une notification selon le type d'erreur
  if (showNotification) {
    switch (statusCode) {
      case 401:
        showWarning(
          'Session expiree. Veuillez vous reconnecter.',
          context
        );
        break;
      case 403:
        showError(
          'Acces refuse. Vous n\'avez pas les permissions requises.',
          context
        );
        break;
      case 404:
        showWarning(
          standardError.path
            ? `Ressource non trouvee: ${standardError.path}`
            : 'La ressource demandee n\'existe pas.',
          context
        );
        break;
      case 422:
        showWarning(
          'Donnees invalides. Veuillez verifier votre saisie.',
          context
        );
        break;
      case 500:
        showCritical(
          standardError.trace_id
            ? `Erreur serveur (ref: ${standardError.trace_id}). Contactez le support si le probleme persiste.`
            : 'Erreur serveur inattendue. Veuillez reessayer.',
          context,
          {
            label: 'Recharger',
            onClick: () => window.location.reload()
          }
        );
        break;
      default:
        showError(standardError.message, context);
    }
  }

  // Rediriger vers la page d'erreur si demande
  if (redirectOnError && shouldRedirectToErrorPage(statusCode)) {
    redirectToErrorPage(statusCode);
  }
};

/**
 * Hook pour les appels API avec gestion d'erreur standardisee
 * Usage: wrapApiCall(async () => await api.get('/endpoint'))
 */
export const wrapApiCall = async <T>(
  apiCall: () => Promise<T>,
  options?: {
    context?: string;
    showNotification?: boolean;
    redirectOn?: number[];
  }
): Promise<T | null> => {
  const { context, showNotification = true, redirectOn = [] } = options || {};

  try {
    return await apiCall();
  } catch (error: unknown) {
    // Extraire le status code et les donnees d'erreur
    let statusCode = 500;
    let errorData: unknown = null;

    if (typeof error === 'object' && error !== null) {
      const e = error as { response?: { status?: number; data?: unknown } };
      if (e.response) {
        statusCode = e.response.status || 500;
        errorData = e.response.data;
      }
    }

    handleHttpError(statusCode, errorData, {
      showNotification,
      redirectOnError: redirectOn.includes(statusCode),
      context
    });

    return null;
  }
};

// ============================================================
// LOG ERROR — REMPLACEMENT DES CATCH VIDES
// ============================================================

/**
 * Log une erreur capturee de maniere non-bloquante.
 * Remplace les catch vides/silencieux.
 * Usage: catch (error) { logError(error, 'MonComposant.action'); }
 */
export function logError(error: unknown, context: string): void {
  const message = error instanceof Error ? error.message : String(error);
  console.warn(`[AZALS] ${context}:`, message);
}

// ============================================================
// SAFE API CALL — RESULT PATTERN
// ============================================================

/**
 * Wrapper API avec Result pattern.
 * Alternative type-safe a wrapApiCall (qui retourne T | null).
 * Preserve l'information d'erreur dans le discriminant.
 */
export async function safeApiCall<T>(
  apiCall: () => Promise<T>,
  context?: string
): Promise<Result<T>> {
  try {
    const data = await apiCall();
    return { ok: true, data };
  } catch (error: unknown) {
    let statusCode = 500;
    let errorData: unknown = null;

    if (typeof error === 'object' && error !== null) {
      const e = error as { response?: { status?: number; data?: unknown } };
      if (e.response) {
        statusCode = e.response.status || 500;
        errorData = e.response.data;
      }
    }

    handleHttpError(statusCode, errorData, {
      showNotification: true,
      context,
    });

    return {
      ok: false,
      error: {
        code: `HTTP_${statusCode}`,
        message: error instanceof Error ? error.message : 'Erreur inconnue',
      },
    };
  }
}
