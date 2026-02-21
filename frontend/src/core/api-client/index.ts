/**
 * AZALSCORE UI Engine - API Client
 * Client HTTP centralisé pour toutes les communications backend
 * PRODUCTION ONLY - Aucune logique de démo
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import { createHttpIncident, createNetworkIncident, createAuthIncident } from '@/core/guardian/incident-store';
import type { ApiResponse, ApiError, ApiRequestConfig } from '@/types';

// ============================================================
// CONFIGURATION PRODUCTION
// ============================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const API_TIMEOUT = 30000;
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

/**
 * Retourne l'URL de base de l'API
 */
export const getApiUrl = (): string => API_BASE_URL;

// ============================================================
// GESTIONNAIRE DE TOKENS
// ============================================================

class TokenManager {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private refreshPromise: Promise<string> | null = null;

  setTokens(access: string, refresh: string): void {
    this.accessToken = access;
    this.refreshToken = refresh;
    sessionStorage.setItem('azals_access_token', access);
    sessionStorage.setItem('azals_refresh_token', refresh);
  }

  getAccessToken(): string | null {
    if (!this.accessToken) {
      this.accessToken = sessionStorage.getItem('azals_access_token');
    }
    return this.accessToken;
  }

  getRefreshToken(): string | null {
    if (!this.refreshToken) {
      this.refreshToken = sessionStorage.getItem('azals_refresh_token');
    }
    return this.refreshToken;
  }

  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    sessionStorage.removeItem('azals_access_token');
    sessionStorage.removeItem('azals_refresh_token');
  }

  async refreshAccessToken(): Promise<string> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refresh = this.getRefreshToken();
    if (!refresh) {
      throw new Error('No refresh token available');
    }

    this.refreshPromise = axios
      .post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refresh })
      .then((response) => {
        const { access_token, refresh_token } = response.data;
        this.setTokens(access_token, refresh_token);
        return access_token;
      })
      .finally(() => {
        this.refreshPromise = null;
      });

    return this.refreshPromise;
  }
}

export const tokenManager = new TokenManager();

// ============================================================
// CRÉATION DU CLIENT AXIOS
// ============================================================

const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  });

  // Intercepteur requêtes - Auth gate + Ajout du token
  // RÈGLE : Aucune requête métier ne part sans token valide.
  // Les endpoints /auth/* sont exemptés (login, refresh, register).
  // Note: CSRF non nécessaire car le backend bypasse CSRF pour les requêtes Bearer token
  client.interceptors.request.use(
    (config) => {
      const token = tokenManager.getAccessToken();

      // Auth gate : bloquer les requêtes métier si pas de token
      const isPublicAuthEndpoint = (
        config.url?.includes('/auth/login') ||
        config.url?.includes('/auth/register') ||
        config.url?.includes('/auth/refresh') ||
        config.url?.includes('/auth/forgot') ||
        config.url?.includes('/auth/reset') ||
        config.url?.includes('/health')
      );
      if (!token && !isPublicAuthEndpoint && !config.headers['Skip-Auth']) {
        return Promise.reject(new Error('AUTH_NOT_READY: No token available. Business requests blocked until authenticated.'));
      }

      if (token && !config.headers['Skip-Auth']) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      delete config.headers['Skip-Auth'];

      // Ajout tenant header si disponible
      const tenantId = sessionStorage.getItem('azals_tenant_id');
      if (tenantId) {
        config.headers['X-Tenant-ID'] = tenantId;
      }

      return config;
    },
    (error) => Promise.reject(error)
  );

  // Intercepteur réponses - Gestion erreurs et refresh token + Guardian incidents
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean; _incidentCreated?: boolean };

      // Skip refresh pour les endpoints d'authentification (login, register, etc.)
      const isAuthEndpoint = originalRequest.url?.includes('/auth/login') ||
                             originalRequest.url?.includes('/auth/register') ||
                             originalRequest.url?.includes('/auth/refresh');

      // Skip incidents pour les endpoints d'incidents eux-mêmes (éviter boucle infinie)
      const isIncidentEndpoint = originalRequest.url?.includes('/incidents');

      // Skip incidents pour les requêtes silencieuses (permission checks, etc.)
      const isSilentRequest = originalRequest.headers?.['X-Silent-Error'] === 'true';

      // GUARDIAN: Créer un incident pour les erreurs significatives
      // Skip les endpoints d'auth (401 attendu quand pas de session)
      if (!isIncidentEndpoint && !isAuthEndpoint && !isSilentRequest && !originalRequest._incidentCreated) {
        originalRequest._incidentCreated = true;

        const status = error.response?.status;
        const url = originalRequest.url || 'unknown';
        const method = originalRequest.method?.toUpperCase() || 'GET';
        const responseData = error.response?.data as { error?: string; message?: string; trace_id?: string } | null;

        // Erreur réseau (pas de réponse)
        if (!error.response) {
          createNetworkIncident(
            error.message || 'Erreur de connexion réseau',
            url
          ).catch(() => {}); // Ignorer les erreurs de création d'incident
        }
        // Erreurs HTTP significatives (pas les 404 sur GET)
        else if (status && (status >= 400) && !(status === 404 && method === 'GET')) {
          // Créer incident pour 401, 403, 422, 500+
          if (status === 401 || status === 403 || status === 422 || status >= 500) {
            createHttpIncident(
              status,
              url,
              method,
              responseData,
              `Requête ${method} vers ${url}`
            ).catch(() => {}); // Ignorer les erreurs de création d'incident
          }
        }
      }

      // Token expiré - tentative de refresh (sauf pour auth endpoints)
      if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
        originalRequest._retry = true;

        try {
          const newToken = await tokenManager.refreshAccessToken();
          if (originalRequest.headers) {
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
          }
          return client(originalRequest);
        } catch (refreshError) {
          // GUARDIAN: Créer incident d'auth quand le refresh échoue
          if (!isIncidentEndpoint) {
            createAuthIncident(
              'Session expirée - Reconnexion requise',
              'Le rafraîchissement du token a échoué'
            ).catch(() => {});
          }

          tokenManager.clearTokens();
          window.dispatchEvent(new CustomEvent('azals:auth:logout'));
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
};

const apiClient = createApiClient();

// ============================================================
// FONCTIONS DE REQUÊTES
// ============================================================

const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

const shouldRetry = (error: AxiosError, attempt: number): boolean => {
  if (attempt >= MAX_RETRIES) return false;
  if (!error.response) return true; // Erreur réseau
  const status = error.response.status;
  return status >= 500 || status === 429;
};

const executeWithRetry = async <T>(
  fn: () => Promise<T>,
  config?: ApiRequestConfig
): Promise<T> => {
  const maxRetries = config?.retries ?? MAX_RETRIES;
  let lastError: AxiosError | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as AxiosError;
      if (!shouldRetry(lastError, attempt)) {
        throw lastError;
      }
      await sleep(RETRY_DELAY * Math.pow(2, attempt));
    }
  }

  throw lastError;
};

// ============================================================
// API PUBLIQUE
// ============================================================

const buildHeaders = (config?: ApiRequestConfig): Record<string, string> | undefined => {
  const headers: Record<string, string> = {};
  if (config?.skipAuth) {
    headers['Skip-Auth'] = 'true';
  }
  if (config?.headers) {
    Object.assign(headers, config.headers);
  }
  return Object.keys(headers).length > 0 ? headers : undefined;
};

export const api = {
  async get<T>(url: string, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    const response = await executeWithRetry(
      () => apiClient.get<ApiResponse<T>>(url, {
        timeout: config?.timeout,
        headers: buildHeaders(config),
        responseType: config?.responseType,
      }),
      config
    );
    return response.data;
  },

  async post<T>(url: string, data?: unknown, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    const response = await executeWithRetry(
      () => apiClient.post<ApiResponse<T>>(url, data, {
        timeout: config?.timeout,
        headers: buildHeaders(config),
      }),
      config
    );
    return response.data;
  },

  async put<T>(url: string, data?: unknown, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    const response = await executeWithRetry(
      () => apiClient.put<ApiResponse<T>>(url, data, {
        timeout: config?.timeout,
        headers: buildHeaders(config),
      }),
      config
    );
    return response.data;
  },

  async patch<T>(url: string, data?: unknown, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    const response = await executeWithRetry(
      () => apiClient.patch<ApiResponse<T>>(url, data, {
        timeout: config?.timeout,
        headers: buildHeaders(config),
      }),
      config
    );
    return response.data;
  },

  async delete<T>(url: string, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    const response = await executeWithRetry(
      () => apiClient.delete<ApiResponse<T>>(url, {
        timeout: config?.timeout,
        headers: buildHeaders(config),
      }),
      config
    );
    return response.data;
  },
};

// ============================================================
// UTILITAIRES ERREURS
// ============================================================

/**
 * Interface pour le format d'erreur standardise AZALS
 */
interface StandardHttpError {
  error: string;
  message: string;
  code: number;
  path?: string;
  trace_id?: string;
  details?: unknown[];
}

/**
 * Verifie si la reponse est au format d'erreur standardise AZALS
 */
const isStandardHttpError = (data: unknown): data is StandardHttpError => {
  if (typeof data !== 'object' || data === null) return false;
  const d = data as Record<string, unknown>;
  return (
    typeof d.error === 'string' &&
    typeof d.message === 'string' &&
    typeof d.code === 'number'
  );
};

/**
 * Parse les erreurs API en format uniforme
 * Compatible avec le nouveau format standardise et l'ancien format
 */
export const parseApiError = (error: unknown): ApiError[] => {
  if (axios.isAxiosError(error)) {
    const response = error.response?.data;
    const statusCode = error.response?.status;

    // Nouveau format standardise AZALS
    if (isStandardHttpError(response)) {
      const errorCode = getErrorCodeFromStatus(statusCode, response.error);
      return [{
        code: errorCode,
        message: response.message,
        // Inclure trace_id pour les erreurs 500
        ...(response.trace_id && { trace_id: response.trace_id }),
        // Inclure path pour les erreurs 404
        ...(response.path && { path: response.path }),
      }];
    }

    // Format avec errors array
    if (response?.errors) {
      return response.errors;
    }

    // Format avec detail (validation errors, etc.)
    if (response?.detail) {
      if (Array.isArray(response.detail)) {
        return response.detail.map((d: { msg?: string; message?: string; loc?: string[] }) => ({
          code: 'VALIDATION_ERROR',
          message: d.msg || d.message || JSON.stringify(d),
          field: d.loc ? d.loc.join('.') : undefined,
        }));
      }
      return [{ code: 'API_ERROR', message: String(response.detail) }];
    }

    // Erreur reseau (pas de reponse du serveur)
    if (!error.response && error.message) {
      return [{ code: 'NETWORK_ERROR', message: error.message }];
    }

    // Erreur HTTP generique
    if (statusCode) {
      return [{
        code: getErrorCodeFromStatus(statusCode),
        message: getDefaultMessageForStatus(statusCode),
      }];
    }
  }

  return [{ code: 'UNKNOWN_ERROR', message: 'Une erreur inattendue est survenue' }];
};

/**
 * Retourne un code d'erreur AZALS selon le status HTTP
 */
const getErrorCodeFromStatus = (status?: number, errorType?: string): string => {
  if (errorType) {
    return `AZALS-${errorType.toUpperCase().replace(/_/g, '-')}`;
  }

  switch (status) {
    case 401: return 'AZALS-AUTH-UNAUTHORIZED';
    case 403: return 'AZALS-AUTH-FORBIDDEN';
    case 404: return 'AZALS-NOT-FOUND';
    case 422: return 'AZALS-VALIDATION-ERROR';
    case 429: return 'AZALS-RATE-LIMITED';
    case 500: return 'AZALS-INTERNAL-ERROR';
    case 502:
    case 503:
    case 504: return 'AZALS-SERVICE-UNAVAILABLE';
    default: return 'AZALS-HTTP-ERROR';
  }
};

/**
 * Retourne un message par defaut selon le status HTTP
 */
const getDefaultMessageForStatus = (status: number): string => {
  switch (status) {
    case 401: return 'Authentification requise';
    case 403: return 'Acces refuse';
    case 404: return 'Ressource non trouvee';
    case 422: return 'Donnees invalides';
    case 429: return 'Trop de requetes, veuillez patienter';
    case 500: return 'Erreur serveur inattendue';
    case 502: return 'Service temporairement indisponible';
    case 503: return 'Service en maintenance';
    case 504: return 'Delai d\'attente depasse';
    default: return `Erreur HTTP ${status}`;
  }
};

/**
 * Extrait le message d'erreur lisible
 */
export const getErrorMessage = (error: unknown): string => {
  const errors = parseApiError(error);
  return errors.map((e) => e.message).join(', ');
};

/**
 * Extrait le status code d'une erreur Axios
 */
export const getErrorStatusCode = (error: unknown): number | undefined => {
  if (axios.isAxiosError(error)) {
    return error.response?.status;
  }
  return undefined;
};

/**
 * Extrait le trace_id d'une erreur 500 (si disponible)
 */
export const getErrorTraceId = (error: unknown): string | undefined => {
  if (axios.isAxiosError(error)) {
    const response = error.response?.data;
    if (isStandardHttpError(response)) {
      return response.trace_id;
    }
  }
  return undefined;
};

// ============================================================
// CONFIGURATION TENANT
// ============================================================

export const setTenantId = (tenantId: string): void => {
  sessionStorage.setItem('azals_tenant_id', tenantId);
};

export const clearTenantId = (): void => {
  sessionStorage.removeItem('azals_tenant_id');
};

export default api;
