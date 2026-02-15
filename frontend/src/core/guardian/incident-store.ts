/**
 * AZALSCORE GUARDIAN - Store d'Incidents
 * =======================================
 * Gestion centralisée des incidents avec capture d'écran
 */

import { create } from 'zustand';
import { logError } from '@core/error-handling';

// ============================================================
// TYPES
// ============================================================

export type IncidentType = 'auth' | 'api' | 'business' | 'js' | 'network' | 'validation';
export type IncidentSeverity = 'info' | 'warning' | 'error' | 'critical';

export interface GuardianAction {
  id: string;
  action_type: string;
  description: string;
  timestamp: Date;
  success: boolean;
  result: string | null;
}

export interface GuardianIncident {
  id: string;
  type: IncidentType;
  severity: IncidentSeverity;
  tenant_id: string | null;
  user_id: string | null;
  page: string;
  route: string;
  endpoint: string | null;
  method: string | null;
  http_status: number | null;
  message: string;
  details: string | null;
  stack_trace: string | null;
  timestamp: Date;
  screenshot_data: string | null;
  guardian_actions: GuardianAction[];
  is_expanded: boolean;
  is_acknowledged: boolean;
  is_sent_to_backend: boolean;
}

interface IncidentStore {
  incidents: GuardianIncident[];
  is_panel_visible: boolean;
  is_panel_collapsed: boolean;
  auto_capture_screenshot: boolean;

  // Actions
  addIncident: (incident: Omit<GuardianIncident, 'id' | 'timestamp' | 'guardian_actions' | 'is_expanded' | 'is_acknowledged' | 'is_sent_to_backend'>) => Promise<string>;
  removeIncident: (id: string) => void;
  acknowledgeIncident: (id: string) => void;
  clearIncidents: () => void;
  togglePanel: () => void;
  collapsePanel: () => void;
  expandPanel: () => void;
  showPanel: () => void;
  hidePanel: () => void;
  addGuardianAction: (incident_id: string, action: Omit<GuardianAction, 'id' | 'timestamp'>) => void;
  toggleIncidentExpanded: (id: string) => void;
  setAutoCaptureScreenshot: (enabled: boolean) => void;
  markAsSentToBackend: (id: string) => void;
}

// ============================================================
// UTILITAIRES
// ============================================================

const generateId = (): string => {
  return `incident_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

const getRouteFromLocation = (): string => {
  return window.location.pathname + window.location.search;
};

const getPageTitle = (): string => {
  return document.title || window.location.pathname;
};

const getTenantId = (): string | null => {
  return sessionStorage.getItem('azals_tenant_id');
};

const getUserId = (): string | null => {
  const authData = sessionStorage.getItem('azals_user');
  if (authData) {
    try {
      const parsed = JSON.parse(authData);
      return parsed.id?.toString() || null;
    } catch (error) {
      logError(error, 'Guardian.loadIncidents');
      return null;
    }
  }
  return null;
};

/**
 * Capture l'écran actuel (avec chargement dynamique de html2canvas)
 */
export const captureScreenshot = async (): Promise<string | null> => {
  try {
    // Import dynamique de html2canvas
    const html2canvas = (await import('html2canvas')).default;

    const canvas = await html2canvas(document.body, {
      logging: false,
      useCORS: true,
      allowTaint: true,
      scale: 0.5,
      ignoreElements: (element) => {
        return element.classList?.contains('guardian-panel') ||
               (element.tagName === 'INPUT' && (element as HTMLInputElement).type === 'password');
      }
    });
    return canvas.toDataURL('image/jpeg', 0.7);
  } catch (error) {
    return null;
  }
};

/**
 * Envoie l'incident au backend
 */
const sendIncidentToBackend = async (incident: GuardianIncident): Promise<boolean> => {
  try {
    const accessToken = sessionStorage.getItem('azals_access_token');
    const tenantId = sessionStorage.getItem('azals_tenant_id');

    if (!accessToken || !tenantId) {
      return false;
    }

    const apiUrl = import.meta.env.VITE_API_URL || '';

    const response = await fetch(`${apiUrl}/v3/incidents`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
        'X-Tenant-ID': tenantId,
      },
      body: JSON.stringify({
        type: incident.type,
        severity: incident.severity,
        page: incident.page,
        route: incident.route,
        endpoint: incident.endpoint,
        method: incident.method,
        http_status: incident.http_status,
        message: incident.message,
        details: incident.details,
        stack_trace: incident.stack_trace,
        screenshot_data: incident.screenshot_data,
        frontend_timestamp: incident.timestamp.toISOString(),
      }),
    });

    return response.ok;
  } catch (error) {
    return false;
  }
};

// ============================================================
// STORE
// ============================================================

export const useIncidentStore = create<IncidentStore>((set, get) => ({
  incidents: [],
  is_panel_visible: false,
  is_panel_collapsed: false,
  auto_capture_screenshot: true,

  addIncident: async (incidentData): Promise<string> => {
    const id = generateId();

    // Capture d'écran automatique si activée
    let screenshot_data: string | null = null;
    if (get().auto_capture_screenshot && !incidentData.screenshot_data) {
      screenshot_data = await captureScreenshot();
    }

    const incident: GuardianIncident = {
      ...incidentData,
      id,
      timestamp: new Date(),
      screenshot_data: screenshot_data || incidentData.screenshot_data,
      guardian_actions: [],
      is_expanded: false,
      is_acknowledged: false,
      is_sent_to_backend: false,
    };

    set((state) => ({
      incidents: [...state.incidents, incident],
      is_panel_visible: true,
    }));

    // Tenter d'envoyer au backend
    sendIncidentToBackend(incident).then((success) => {
      if (success) {
        get().markAsSentToBackend(id);
      }
    });

    return id;
  },

  removeIncident: (id): void => {
    set((state) => ({
      incidents: state.incidents.filter((i) => i.id !== id),
      is_panel_visible: state.incidents.filter((i) => i.id !== id).length > 0 ? state.is_panel_visible : false,
    }));
  },

  acknowledgeIncident: (id): void => {
    set((state) => ({
      incidents: state.incidents.map((i) =>
        i.id === id ? { ...i, is_acknowledged: true } : i
      ),
    }));
  },

  clearIncidents: (): void => {
    set({ incidents: [], is_panel_visible: false });
  },

  togglePanel: (): void => {
    set((state) => ({ is_panel_collapsed: !state.is_panel_collapsed }));
  },

  collapsePanel: (): void => {
    set({ is_panel_collapsed: true });
  },

  expandPanel: (): void => {
    set({ is_panel_collapsed: false });
  },

  showPanel: (): void => {
    set({ is_panel_visible: true });
  },

  hidePanel: (): void => {
    set({ is_panel_visible: false });
  },

  addGuardianAction: (incident_id, action): void => {
    const guardianAction: GuardianAction = {
      ...action,
      id: `action_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      timestamp: new Date(),
    };

    set((state) => ({
      incidents: state.incidents.map((i) =>
        i.id === incident_id
          ? { ...i, guardian_actions: [...i.guardian_actions, guardianAction] }
          : i
      ),
    }));
  },

  toggleIncidentExpanded: (id): void => {
    set((state) => ({
      incidents: state.incidents.map((i) =>
        i.id === id ? { ...i, is_expanded: !i.is_expanded } : i
      ),
    }));
  },

  setAutoCaptureScreenshot: (enabled): void => {
    set({ auto_capture_screenshot: enabled });
  },

  markAsSentToBackend: (id): void => {
    set((state) => ({
      incidents: state.incidents.map((i) =>
        i.id === id ? { ...i, is_sent_to_backend: true } : i
      ),
    }));
  },
}));

// ============================================================
// GUARDIAN ACTIONS
// ============================================================

export const GuardianActions = {
  forceLogout: async (incident_id: string): Promise<boolean> => {
    const store = useIncidentStore.getState();

    store.addGuardianAction(incident_id, {
      action_type: 'FORCE_LOGOUT',
      description: 'Déconnexion forcée pour nettoyer le contexte auth',
      success: false,
      result: null,
    });

    try {
      sessionStorage.removeItem('azals_access_token');
      sessionStorage.removeItem('azals_refresh_token');
      sessionStorage.removeItem('azals_tenant_id');
      sessionStorage.removeItem('azals_user');
      window.dispatchEvent(new CustomEvent('azals:auth:logout'));

      store.addGuardianAction(incident_id, {
        action_type: 'FORCE_LOGOUT',
        description: 'Déconnexion forcée réussie',
        success: true,
        result: 'Context auth nettoyé',
      });

      setTimeout(() => {
        window.location.href = '/login';
      }, 1000);

      return true;
    } catch (error) {
      store.addGuardianAction(incident_id, {
        action_type: 'FORCE_LOGOUT',
        description: 'Échec de la déconnexion forcée',
        success: false,
        result: String(error),
      });
      return false;
    }
  },

  attemptTokenRefresh: async (incident_id: string): Promise<boolean> => {
    const store = useIncidentStore.getState();

    store.addGuardianAction(incident_id, {
      action_type: 'TOKEN_REFRESH',
      description: 'Tentative de rafraîchissement du token',
      success: false,
      result: null,
    });

    try {
      const refreshToken = sessionStorage.getItem('azals_refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const apiUrl = import.meta.env.VITE_API_URL || '';
      const response = await fetch(`${apiUrl}/v3/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await response.json();
        sessionStorage.setItem('azals_access_token', data.access_token);
        sessionStorage.setItem('azals_refresh_token', data.refresh_token);

        store.addGuardianAction(incident_id, {
          action_type: 'TOKEN_REFRESH',
          description: 'Token rafraîchi avec succès',
          success: true,
          result: 'Nouveau token obtenu',
        });

        return true;
      } else {
        throw new Error(`Refresh failed: ${response.status}`);
      }
    } catch (error) {
      store.addGuardianAction(incident_id, {
        action_type: 'TOKEN_REFRESH',
        description: 'Échec du rafraîchissement token',
        success: false,
        result: String(error),
      });
      return false;
    }
  },

  reloadPage: (incident_id: string): void => {
    const store = useIncidentStore.getState();

    store.addGuardianAction(incident_id, {
      action_type: 'PAGE_RELOAD',
      description: 'Rechargement de la page',
      success: true,
      result: 'Page rechargée',
    });

    setTimeout(() => {
      window.location.reload();
    }, 500);
  },

  goBack: (incident_id: string): void => {
    const store = useIncidentStore.getState();

    store.addGuardianAction(incident_id, {
      action_type: 'NAVIGATE_BACK',
      description: 'Retour à la page précédente',
      success: true,
      result: 'Navigation arrière',
    });

    setTimeout(() => {
      window.history.back();
    }, 500);
  },

  goToCockpit: (incident_id: string): void => {
    const store = useIncidentStore.getState();

    store.addGuardianAction(incident_id, {
      action_type: 'NAVIGATE_COCKPIT',
      description: 'Redirection vers le cockpit',
      success: true,
      result: 'Navigation vers /cockpit',
    });

    setTimeout(() => {
      window.location.href = '/cockpit';
    }, 500);
  },
};

// ============================================================
// API SIMPLIFIÉE POUR CRÉER DES INCIDENTS
// ============================================================

export const createHttpIncident = async (
  status: number,
  endpoint: string,
  method: string,
  errorData: { error?: string; message?: string; trace_id?: string } | null,
  context?: string
): Promise<string> => {
  const store = useIncidentStore.getState();

  let type: IncidentType = 'api';
  let severity: IncidentSeverity = 'error';

  if (status === 401 || status === 403) {
    type = 'auth';
    severity = status === 401 ? 'warning' : 'error';
  } else if (status === 422) {
    type = 'validation';
    severity = 'warning';
  } else if (status >= 500) {
    type = 'api';
    severity = 'critical';
  } else if (status === 404) {
    severity = 'warning';
  }

  let message = errorData?.message || `Erreur HTTP ${status}`;
  if (errorData?.trace_id) {
    message += ` (ref: ${errorData.trace_id})`;
  }

  return await store.addIncident({
    type,
    severity,
    tenant_id: getTenantId(),
    user_id: getUserId(),
    page: getPageTitle(),
    route: getRouteFromLocation(),
    endpoint,
    method,
    http_status: status,
    message,
    details: context || null,
    stack_trace: null,
    screenshot_data: null,
  });
};

export const createJsIncident = async (
  error: Error,
  componentStack?: string
): Promise<string> => {
  const store = useIncidentStore.getState();

  return await store.addIncident({
    type: 'js',
    severity: 'critical',
    tenant_id: getTenantId(),
    user_id: getUserId(),
    page: getPageTitle(),
    route: getRouteFromLocation(),
    endpoint: null,
    method: null,
    http_status: null,
    message: error.message || 'Erreur JavaScript non gérée',
    details: error.name || 'Error',
    stack_trace: componentStack || error.stack || null,
    screenshot_data: null,
  });
};

export const createAuthIncident = async (
  reason: string,
  details?: string
): Promise<string> => {
  const store = useIncidentStore.getState();

  return await store.addIncident({
    type: 'auth',
    severity: 'warning',
    tenant_id: getTenantId(),
    user_id: getUserId(),
    page: getPageTitle(),
    route: getRouteFromLocation(),
    endpoint: '/v3/auth/*',
    method: null,
    http_status: null,
    message: reason,
    details: details || null,
    stack_trace: null,
    screenshot_data: null,
  });
};

export const createNetworkIncident = async (
  message: string,
  endpoint?: string
): Promise<string> => {
  const store = useIncidentStore.getState();

  return await store.addIncident({
    type: 'network',
    severity: 'error',
    tenant_id: getTenantId(),
    user_id: getUserId(),
    page: getPageTitle(),
    route: getRouteFromLocation(),
    endpoint: endpoint || null,
    method: null,
    http_status: null,
    message,
    details: null,
    stack_trace: null,
    screenshot_data: null,
  });
};

// ============================================================
// GLOBAL ERROR HANDLERS
// ============================================================

export const initGuardianErrorHandlers = (): void => {
  window.addEventListener('error', (event) => {
    if (event.error) {
      createJsIncident(event.error);
    }
  });

  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason instanceof Error
      ? event.reason
      : new Error(String(event.reason));
    createJsIncident(error);
  });

};

// ============================================================
// HOOKS
// ============================================================

export const useIncidents = () => {
  const store = useIncidentStore();
  return {
    incidents: store.incidents,
    is_panel_visible: store.is_panel_visible,
    is_panel_collapsed: store.is_panel_collapsed,
    addIncident: store.addIncident,
    removeIncident: store.removeIncident,
    acknowledgeIncident: store.acknowledgeIncident,
    clearIncidents: store.clearIncidents,
    togglePanel: store.togglePanel,
    toggleIncidentExpanded: store.toggleIncidentExpanded,
  };
};

export const useIncidentCount = (): number => {
  return useIncidentStore((state) => state.incidents.length);
};

export const useUnacknowledgedCount = (): number => {
  return useIncidentStore((state) =>
    state.incidents.filter((i) => !i.is_acknowledged).length
  );
};

export const useCriticalIncidents = () => {
  return useIncidentStore((state) =>
    state.incidents.filter((i) => i.severity === 'critical' && !i.is_acknowledged)
  );
};
