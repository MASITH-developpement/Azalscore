/**
 * AZALSCORE - Module GUARDIAN Frontend
 * =====================================
 *
 * Client frontend pour le système de correction automatique gouvernée.
 * Capture et signale les erreurs frontend au backend GUARDIAN.
 *
 * PRINCIPES:
 * - Les erreurs ne sont jamais cachées
 * - Les données utilisateur sont pseudonymisées
 * - Toutes les erreurs sont traçables
 */

import { getApiUrl } from '@/core/api-client';
import { useErrorStore, type UIError, type ErrorSeverity } from '@/core/error-handling';

// ============================================================
// TYPES
// ============================================================

export interface GuardianErrorReport {
  error_type: string;
  error_message: string;
  stack_trace?: string;
  component?: string;
  route?: string;
  browser?: string;
  browser_version?: string;
  os?: string;
  viewport_width?: number;
  viewport_height?: number;
  user_role?: string;
  module?: string;
  action?: string;
  timestamp: string;
  correlation_id?: string;
  extra_context?: Record<string, unknown>;
}

export interface GuardianAlert {
  id: number;
  alert_uid: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  is_read: boolean;
  is_resolved: boolean;
  created_at: string;
}

export interface GuardianConfig {
  is_enabled: boolean;
  auto_correction_enabled: boolean;
  auto_correction_environments: string[];
}

// ============================================================
// CONFIGURATION
// ============================================================

let isInitialized = false;
let correlationId: string | null = null;
let currentUserRole: string | null = null;
let currentModule: string | null = null;
let reportingEnabled = true;

/**
 * Génère un ID de corrélation unique pour la session
 */
const generateCorrelationId = (): string => {
  return `fe_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Détecte les informations du navigateur
 */
const getBrowserInfo = (): { browser: string; version: string; os: string } => {
  const ua = navigator.userAgent;
  let browser = 'Unknown';
  let version = '';
  let os = 'Unknown';

  // Detect browser
  if (ua.includes('Firefox/')) {
    browser = 'Firefox';
    version = ua.split('Firefox/')[1]?.split(' ')[0] || '';
  } else if (ua.includes('Chrome/')) {
    browser = 'Chrome';
    version = ua.split('Chrome/')[1]?.split(' ')[0] || '';
  } else if (ua.includes('Safari/') && !ua.includes('Chrome')) {
    browser = 'Safari';
    version = ua.split('Version/')[1]?.split(' ')[0] || '';
  } else if (ua.includes('Edge/')) {
    browser = 'Edge';
    version = ua.split('Edge/')[1]?.split(' ')[0] || '';
  }

  // Detect OS
  if (ua.includes('Windows')) {
    os = 'Windows';
  } else if (ua.includes('Mac OS')) {
    os = 'macOS';
  } else if (ua.includes('Linux')) {
    os = 'Linux';
  } else if (ua.includes('Android')) {
    os = 'Android';
  } else if (ua.includes('iOS')) {
    os = 'iOS';
  }

  return { browser, version, os };
};

// ============================================================
// API GUARDIAN
// ============================================================

/**
 * Envoie une erreur au backend GUARDIAN
 */
const sendErrorToGuardian = async (report: GuardianErrorReport): Promise<void> => {
  if (!reportingEnabled) return;

  try {
    const token = localStorage.getItem('azals_token');
    const tenantId = localStorage.getItem('azals_tenant_id');

    if (!token || !tenantId) {
      // Pas de token ou tenant, on ne peut pas envoyer
      console.debug('GUARDIAN: No auth context, error not reported');
      return;
    }

    const response = await fetch(`${getApiUrl()}/api/guardian/errors/frontend`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': tenantId,
      },
      body: JSON.stringify(report),
    });

    if (!response.ok) {
      // Silently fail - don't create more errors
      console.debug('GUARDIAN: Failed to report error', response.status);
    }
  } catch (err) {
    // Silently fail - don't create infinite loops
    console.debug('GUARDIAN: Error reporting failed', err);
  }
};

/**
 * Récupère les alertes GUARDIAN non lues
 */
export const fetchGuardianAlerts = async (): Promise<GuardianAlert[]> => {
  try {
    const token = localStorage.getItem('azals_token');
    const tenantId = localStorage.getItem('azals_tenant_id');

    if (!token || !tenantId) return [];

    const response = await fetch(`${getApiUrl()}/api/guardian/alerts?is_resolved=false`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': tenantId,
      },
    });

    if (!response.ok) return [];

    const data = await response.json();
    return data.items || [];
  } catch {
    return [];
  }
};

/**
 * Acquitte une alerte GUARDIAN
 */
export const acknowledgeGuardianAlert = async (alertId: number): Promise<boolean> => {
  try {
    const token = localStorage.getItem('azals_token');
    const tenantId = localStorage.getItem('azals_tenant_id');

    if (!token || !tenantId) return false;

    const response = await fetch(`${getApiUrl()}/api/guardian/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Tenant-ID': tenantId,
      },
    });

    return response.ok;
  } catch {
    return false;
  }
};

// ============================================================
// ERROR CAPTURE
// ============================================================

/**
 * Capture une erreur et l'envoie à GUARDIAN
 */
export const captureError = (
  error: Error,
  context?: {
    component?: string;
    action?: string;
    extra?: Record<string, unknown>;
  }
): void => {
  const browserInfo = getBrowserInfo();
  const route = typeof window !== 'undefined' ? window.location.pathname : undefined;

  const report: GuardianErrorReport = {
    error_type: error.name || 'Error',
    error_message: error.message,
    stack_trace: error.stack,
    component: context?.component,
    route,
    browser: browserInfo.browser,
    browser_version: browserInfo.version,
    os: browserInfo.os,
    viewport_width: typeof window !== 'undefined' ? window.innerWidth : undefined,
    viewport_height: typeof window !== 'undefined' ? window.innerHeight : undefined,
    user_role: currentUserRole || undefined,
    module: currentModule || undefined,
    action: context?.action,
    timestamp: new Date().toISOString(),
    correlation_id: correlationId || undefined,
    extra_context: context?.extra,
  };

  // Envoi asynchrone (fire and forget)
  sendErrorToGuardian(report);
};

/**
 * Capture une erreur UI et la signale
 */
export const captureUIError = (uiError: UIError): void => {
  const error = new Error(uiError.message);
  error.name = uiError.code;

  captureError(error, {
    component: uiError.context,
    extra: {
      severity: uiError.severity,
      dismissible: uiError.dismissible,
    },
  });
};

/**
 * Mappe la sévérité UI vers GUARDIAN
 */
const mapSeverityToGuardian = (severity: ErrorSeverity): string => {
  const mapping: Record<ErrorSeverity, string> = {
    info: 'INFO',
    warning: 'WARNING',
    error: 'MAJOR',
    critical: 'CRITICAL',
  };
  return mapping[severity] || 'MAJOR';
};

// ============================================================
// GLOBAL ERROR HANDLERS
// ============================================================

/**
 * Handler pour les erreurs JavaScript non gérées
 */
const handleGlobalError = (event: ErrorEvent): void => {
  captureError(event.error || new Error(event.message), {
    component: 'GlobalErrorHandler',
    extra: {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    },
  });
};

/**
 * Handler pour les rejets de promesses non gérés
 */
const handleUnhandledRejection = (event: PromiseRejectionEvent): void => {
  const error = event.reason instanceof Error
    ? event.reason
    : new Error(String(event.reason));

  captureError(error, {
    component: 'UnhandledPromiseRejection',
  });
};

// ============================================================
// INITIALIZATION
// ============================================================

/**
 * Initialise le module GUARDIAN frontend
 */
export const initGuardian = (options?: {
  userRole?: string;
  module?: string;
  enabled?: boolean;
}): void => {
  if (isInitialized) return;

  correlationId = generateCorrelationId();
  currentUserRole = options?.userRole || null;
  currentModule = options?.module || null;
  reportingEnabled = options?.enabled !== false;

  // Install global error handlers
  if (typeof window !== 'undefined') {
    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
  }

  // Subscribe to error store pour capturer toutes les erreurs UI
  useErrorStore.subscribe((state, prevState) => {
    const newErrors = state.errors.filter(
      (e) => !prevState.errors.find((pe) => pe.id === e.id)
    );

    newErrors.forEach((error) => {
      // Ne pas reporter les erreurs info (trop de bruit)
      if (error.severity !== 'info') {
        captureUIError(error);
      }
    });
  });

  isInitialized = true;
  console.debug('GUARDIAN: Frontend module initialized', { correlationId });
};

/**
 * Met à jour le contexte GUARDIAN
 */
export const updateGuardianContext = (context: {
  userRole?: string;
  module?: string;
}): void => {
  if (context.userRole !== undefined) currentUserRole = context.userRole;
  if (context.module !== undefined) currentModule = context.module;
};

/**
 * Désactive temporairement le reporting
 */
export const disableReporting = (): void => {
  reportingEnabled = false;
};

/**
 * Réactive le reporting
 */
export const enableReporting = (): void => {
  reportingEnabled = true;
};

/**
 * Récupère l'ID de corrélation courant
 */
export const getCorrelationId = (): string | null => correlationId;

// ============================================================
// REACT HOOKS
// ============================================================

import { useState, useEffect, useCallback } from 'react';

/**
 * Hook pour les alertes GUARDIAN
 */
export const useGuardianAlerts = (refreshInterval = 60000) => {
  const [alerts, setAlerts] = useState<GuardianAlert[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const data = await fetchGuardianAlerts();
    setAlerts(data);
    setLoading(false);
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, refreshInterval);
    return () => clearInterval(interval);
  }, [refresh, refreshInterval]);

  const acknowledge = useCallback(async (alertId: number) => {
    const success = await acknowledgeGuardianAlert(alertId);
    if (success) {
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    }
    return success;
  }, []);

  return { alerts, loading, refresh, acknowledge };
};

/**
 * Hook pour le compteur d'alertes non lues
 */
export const useGuardianAlertCount = () => {
  const { alerts, loading } = useGuardianAlerts();
  return { count: alerts.length, loading };
};

// ============================================================
// ERROR BOUNDARY INTEGRATION
// ============================================================

/**
 * Handler pour React Error Boundary
 */
export const guardianErrorBoundaryHandler = (
  error: Error,
  errorInfo: { componentStack: string }
): void => {
  captureError(error, {
    component: 'ReactErrorBoundary',
    extra: {
      componentStack: errorInfo.componentStack,
    },
  });
};

// ============================================================
// EXPORTS
// ============================================================

export default {
  init: initGuardian,
  captureError,
  captureUIError,
  updateContext: updateGuardianContext,
  disableReporting,
  enableReporting,
  getCorrelationId,
  fetchAlerts: fetchGuardianAlerts,
  acknowledgeAlert: acknowledgeGuardianAlert,
};
