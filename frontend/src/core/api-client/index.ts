/**
 * AZALSCORE UI Engine - API Client
 * Client HTTP centralisé pour toutes les communications backend
 * AUCUNE logique métier - transport uniquement
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import type { ApiResponse, ApiError, ApiRequestConfig } from '@/types';

// ============================================================
// CONFIGURATION
// ============================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
const API_TIMEOUT = 30000;
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

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
      .post(`${API_BASE_URL}/v1/auth/refresh`, { refresh_token: refresh })
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

  // Intercepteur requêtes - Ajout du token
  client.interceptors.request.use(
    (config) => {
      const token = tokenManager.getAccessToken();
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

  // Intercepteur réponses - Gestion erreurs et refresh token
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

      // Token expiré - tentative de refresh
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const newToken = await tokenManager.refreshAccessToken();
          if (originalRequest.headers) {
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
          }
          return client(originalRequest);
        } catch (refreshError) {
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

export const api = {
  async get<T>(url: string, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    const response = await executeWithRetry(
      () => apiClient.get<ApiResponse<T>>(url, {
        timeout: config?.timeout,
        headers: config?.skipAuth ? { 'Skip-Auth': 'true' } : undefined,
      }),
      config
    );
    return response.data;
  },

  async post<T>(url: string, data?: unknown, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    const response = await executeWithRetry(
      () => apiClient.post<ApiResponse<T>>(url, data, {
        timeout: config?.timeout,
        headers: config?.skipAuth ? { 'Skip-Auth': 'true' } : undefined,
      }),
      config
    );
    return response.data;
  },

  async put<T>(url: string, data?: unknown, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    const response = await executeWithRetry(
      () => apiClient.put<ApiResponse<T>>(url, data, {
        timeout: config?.timeout,
      }),
      config
    );
    return response.data;
  },

  async patch<T>(url: string, data?: unknown, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    const response = await executeWithRetry(
      () => apiClient.patch<ApiResponse<T>>(url, data, {
        timeout: config?.timeout,
      }),
      config
    );
    return response.data;
  },

  async delete<T>(url: string, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    const response = await executeWithRetry(
      () => apiClient.delete<ApiResponse<T>>(url, {
        timeout: config?.timeout,
      }),
      config
    );
    return response.data;
  },
};

// ============================================================
// UTILITAIRES ERREURS
// ============================================================

export const parseApiError = (error: unknown): ApiError[] => {
  if (axios.isAxiosError(error)) {
    const response = error.response?.data;
    if (response?.errors) {
      return response.errors;
    }
    if (response?.detail) {
      return [{ code: 'API_ERROR', message: response.detail }];
    }
    if (error.message) {
      return [{ code: 'NETWORK_ERROR', message: error.message }];
    }
  }
  return [{ code: 'UNKNOWN_ERROR', message: 'Une erreur inattendue est survenue' }];
};

export const getErrorMessage = (error: unknown): string => {
  const errors = parseApiError(error);
  return errors.map((e) => e.message).join(', ');
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
