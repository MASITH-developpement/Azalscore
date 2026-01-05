/**
 * AZALSCORE UI Engine - Module Audit UI
 * Traçabilité des actions UI critiques
 * Envoi au backend UNIQUEMENT - AUCUN stockage local
 */

import { api } from '@core/api-client';
import type { UIAuditEvent } from '@/types';

// ============================================================
// TYPES
// ============================================================

type AuditEventType =
  | 'navigation'
  | 'action'
  | 'form_submit'
  | 'error'
  | 'auth'
  | 'capability_check'
  | 'break_glass';

interface AuditPayload {
  event_type: AuditEventType;
  component: string;
  action: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
  session_id: string;
}

// ============================================================
// SESSION ID (NON PERSISTANT)
// ============================================================

let sessionId: string | null = null;

const getSessionId = (): string => {
  if (!sessionId) {
    sessionId = `ses_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  return sessionId;
};

// ============================================================
// FILE D'ATTENTE (BUFFER MÉMOIRE UNIQUEMENT)
// ============================================================

const eventQueue: AuditPayload[] = [];
const MAX_QUEUE_SIZE = 50;
const FLUSH_INTERVAL = 10000; // 10 secondes
let flushTimer: ReturnType<typeof setInterval> | null = null;

const startFlushTimer = (): void => {
  if (flushTimer) return;

  flushTimer = setInterval(() => {
    flushEvents();
  }, FLUSH_INTERVAL);
};

const stopFlushTimer = (): void => {
  if (flushTimer) {
    clearInterval(flushTimer);
    flushTimer = null;
  }
};

// ============================================================
// ENVOI DES ÉVÉNEMENTS
// ============================================================

const flushEvents = async (): Promise<void> => {
  if (eventQueue.length === 0) return;

  const eventsToSend = [...eventQueue];
  eventQueue.length = 0;

  try {
    await api.post('/v1/audit/ui-events', { events: eventsToSend });
  } catch {
    // En cas d'échec, on ne réinjecte PAS dans la queue
    // Les événements sont perdus - conformité charte (pas de stockage local)
    console.warn('Failed to send UI audit events');
  }
};

// ============================================================
// API PUBLIQUE
// ============================================================

/**
 * Enregistre un événement d'audit UI
 * IMPORTANT: N'enregistre RIEN localement - envoi backend uniquement
 */
export const trackUIEvent = (event: UIAuditEvent): void => {
  const payload: AuditPayload = {
    event_type: event.event_type as AuditEventType,
    component: event.component,
    action: event.action,
    metadata: event.metadata,
    timestamp: new Date().toISOString(),
    session_id: getSessionId(),
  };

  eventQueue.push(payload);

  // Flush immédiat si queue pleine
  if (eventQueue.length >= MAX_QUEUE_SIZE) {
    flushEvents();
  }
};

/**
 * Track une navigation
 */
export const trackNavigation = (from: string, to: string): void => {
  trackUIEvent({
    event_type: 'navigation',
    component: 'router',
    action: 'navigate',
    metadata: { from, to },
  });
};

/**
 * Track une action utilisateur
 */
export const trackAction = (
  component: string,
  action: string,
  metadata?: Record<string, unknown>
): void => {
  trackUIEvent({
    event_type: 'action',
    component,
    action,
    metadata,
  });
};

/**
 * Track une soumission de formulaire
 */
export const trackFormSubmit = (
  formName: string,
  success: boolean,
  metadata?: Record<string, unknown>
): void => {
  trackUIEvent({
    event_type: 'form_submit',
    component: formName,
    action: success ? 'submit_success' : 'submit_failure',
    metadata,
  });
};

/**
 * Track une erreur UI
 */
export const trackError = (
  component: string,
  errorCode: string,
  message: string
): void => {
  trackUIEvent({
    event_type: 'error',
    component,
    action: 'error_occurred',
    metadata: { errorCode, message },
  });
};

/**
 * Track un événement d'authentification
 */
export const trackAuthEvent = (
  action: 'login' | 'logout' | '2fa_verify' | 'session_refresh',
  success: boolean
): void => {
  trackUIEvent({
    event_type: 'auth',
    component: 'auth',
    action,
    metadata: { success },
  });
};

/**
 * Track une vérification de capacité (pour audit accès)
 */
export const trackCapabilityCheck = (
  capability: string,
  granted: boolean,
  component: string
): void => {
  trackUIEvent({
    event_type: 'capability_check',
    component,
    action: 'check_capability',
    metadata: { capability, granted },
  });
};

/**
 * Track un événement break-glass
 * ATTENTION: Ne log AUCUN détail du périmètre ou des données
 */
export const trackBreakGlassEvent = (
  step: 'initiated' | 'confirmed' | 'executed' | 'cancelled'
): void => {
  trackUIEvent({
    event_type: 'break_glass',
    component: 'break_glass',
    action: step,
    // PAS DE METADATA - conformité charte
  });
};

// ============================================================
// LIFECYCLE
// ============================================================

/**
 * Initialise le système d'audit UI
 */
export const initAuditUI = (): void => {
  startFlushTimer();

  // Flush avant fermeture de page
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', () => {
      flushEvents();
    });

    window.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        flushEvents();
      }
    });
  }
};

/**
 * Arrête le système d'audit UI
 */
export const stopAuditUI = (): void => {
  stopFlushTimer();
  flushEvents();
};

/**
 * Force un flush immédiat
 */
export const forceFlush = (): Promise<void> => {
  return flushEvents();
};

// ============================================================
// HOOK REACT
// ============================================================

import { useEffect } from 'react';

/**
 * Hook pour tracker automatiquement le montage d'un composant
 */
export const useTrackComponent = (
  componentName: string,
  metadata?: Record<string, unknown>
): void => {
  useEffect(() => {
    trackUIEvent({
      event_type: 'navigation',
      component: componentName,
      action: 'mount',
      metadata,
    });

    return () => {
      trackUIEvent({
        event_type: 'navigation',
        component: componentName,
        action: 'unmount',
      });
    };
  }, [componentName]);
};
