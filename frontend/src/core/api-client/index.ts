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
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

// ============================================================
// MOCK DATA POUR MODE DÉMO
// ============================================================

const DEMO_DATA: Record<string, unknown> = {
  // Cockpit
  '/v1/cockpit/dashboard': {
    kpis: [
      { id: 'revenue', label: 'CA du mois', value: 125430, unit: '€', trend: 12.5, status: 'green' },
      { id: 'invoices', label: 'Factures en attente', value: 23, trend: -5, status: 'orange' },
      { id: 'treasury', label: 'Trésorerie', value: 45200, unit: '€', trend: 3.2, status: 'green' },
      { id: 'overdue', label: 'Impayés', value: 8500, unit: '€', trend: 15, status: 'red' },
    ],
    alerts: [
      { id: '1', severity: 'warning', message: '3 factures arrivent à échéance cette semaine', module: 'invoicing' },
      { id: '2', severity: 'info', message: 'Nouvelle version disponible', module: 'system' },
    ],
    recent_activities: [
      { id: '1', type: 'invoice', description: 'Facture FA-2024-001 créée', timestamp: new Date().toISOString() },
      { id: '2', type: 'payment', description: 'Paiement reçu: 2500€', timestamp: new Date().toISOString() },
    ],
  },

  // Partners
  '/v1/partners': {
    items: [
      { id: '1', name: 'ACME Corp', type: 'client', email: 'contact@acme.com', phone: '+33 1 23 45 67 89', city: 'Paris', balance: 15000, status: 'active' },
      { id: '2', name: 'Tech Solutions', type: 'client', email: 'info@techsol.fr', phone: '+33 1 98 76 54 32', city: 'Lyon', balance: 8500, status: 'active' },
      { id: '3', name: 'Fournitures Pro', type: 'supplier', email: 'commercial@fournpro.com', phone: '+33 1 11 22 33 44', city: 'Marseille', balance: -2300, status: 'active' },
      { id: '4', name: 'Digital Agency', type: 'client', email: 'hello@digital.agency', phone: '+33 1 55 66 77 88', city: 'Bordeaux', balance: 0, status: 'inactive' },
      { id: '5', name: 'Import Export SA', type: 'both', email: 'trade@importexport.com', phone: '+33 1 44 55 66 77', city: 'Toulouse', balance: 12000, status: 'active' },
    ],
    total: 5,
    page: 1,
    page_size: 25,
  },

  // Invoices
  '/v1/invoicing/invoices': {
    items: [
      { id: '1', number: 'FA-2024-001', partner_name: 'ACME Corp', date: '2024-01-15', due_date: '2024-02-15', amount_ht: 5000, amount_ttc: 6000, status: 'sent', type: 'invoice' },
      { id: '2', number: 'FA-2024-002', partner_name: 'Tech Solutions', date: '2024-01-20', due_date: '2024-02-20', amount_ht: 3500, amount_ttc: 4200, status: 'paid', type: 'invoice' },
      { id: '3', number: 'FA-2024-003', partner_name: 'Digital Agency', date: '2024-01-25', due_date: '2024-02-25', amount_ht: 8000, amount_ttc: 9600, status: 'draft', type: 'invoice' },
      { id: '4', number: 'AV-2024-001', partner_name: 'ACME Corp', date: '2024-01-10', due_date: '2024-01-10', amount_ht: -500, amount_ttc: -600, status: 'paid', type: 'credit_note' },
    ],
    total: 4,
    page: 1,
    page_size: 25,
  },

  // Treasury
  '/v1/treasury/accounts': {
    items: [
      { id: '1', name: 'Compte principal', bank: 'BNP Paribas', iban: 'FR76 1234 5678 9012 3456 7890 123', balance: 45200, currency: 'EUR' },
      { id: '2', name: 'Compte épargne', bank: 'Société Générale', iban: 'FR76 9876 5432 1098 7654 3210 987', balance: 25000, currency: 'EUR' },
    ],
    total: 2,
  },
  '/v1/treasury/transactions': {
    items: [
      { id: '1', date: '2024-01-28', label: 'Virement client ACME', amount: 6000, type: 'credit', account_name: 'Compte principal', category: 'Encaissement' },
      { id: '2', date: '2024-01-27', label: 'Paiement fournisseur', amount: -2300, type: 'debit', account_name: 'Compte principal', category: 'Décaissement' },
      { id: '3', date: '2024-01-26', label: 'Salaires janvier', amount: -15000, type: 'debit', account_name: 'Compte principal', category: 'Salaires' },
      { id: '4', date: '2024-01-25', label: 'Encaissement CB', amount: 4200, type: 'credit', account_name: 'Compte principal', category: 'Encaissement' },
    ],
    total: 4,
    page: 1,
    page_size: 25,
  },

  // Accounting
  '/v1/accounting/journal': {
    items: [
      { id: '1', date: '2024-01-28', piece: 'VT-001', account: '411000', label: 'Vente ACME Corp', debit: 0, credit: 6000, journal: 'VT' },
      { id: '2', date: '2024-01-28', piece: 'VT-001', account: '512000', label: 'Vente ACME Corp', debit: 6000, credit: 0, journal: 'VT' },
      { id: '3', date: '2024-01-27', piece: 'AC-001', account: '401000', label: 'Achat fournitures', debit: 2300, credit: 0, journal: 'AC' },
      { id: '4', date: '2024-01-27', piece: 'AC-001', account: '512000', label: 'Achat fournitures', debit: 0, credit: 2300, journal: 'AC' },
    ],
    total: 4,
    page: 1,
    page_size: 25,
  },

  // Projects
  '/v1/projects': {
    items: [
      { id: '1', name: 'Refonte site web', client_name: 'ACME Corp', status: 'in_progress', start_date: '2024-01-01', end_date: '2024-03-31', budget: 15000, consumed: 8500, progress: 60 },
      { id: '2', name: 'Application mobile', client_name: 'Tech Solutions', status: 'planned', start_date: '2024-02-01', end_date: '2024-06-30', budget: 35000, consumed: 0, progress: 0 },
      { id: '3', name: 'Migration cloud', client_name: 'Digital Agency', status: 'completed', start_date: '2023-10-01', end_date: '2024-01-15', budget: 20000, consumed: 18500, progress: 100 },
    ],
    total: 3,
    page: 1,
    page_size: 25,
  },

  // Interventions
  '/v1/interventions': {
    items: [
      { id: '1', reference: 'INT-2024-001', client_name: 'ACME Corp', type: 'maintenance', status: 'scheduled', date: '2024-02-01', technician: 'Jean Dupont', duration: 2 },
      { id: '2', reference: 'INT-2024-002', client_name: 'Tech Solutions', type: 'installation', status: 'in_progress', date: '2024-01-29', technician: 'Marie Martin', duration: 4 },
      { id: '3', reference: 'INT-2024-003', client_name: 'Import Export SA', type: 'repair', status: 'completed', date: '2024-01-25', technician: 'Pierre Durand', duration: 1.5 },
    ],
    total: 3,
    page: 1,
    page_size: 25,
  },

  // Purchases
  '/v1/purchases/orders': {
    items: [
      { id: '1', number: 'PO-2024-001', supplier_name: 'Fournitures Pro', date: '2024-01-20', amount_ht: 2300, amount_ttc: 2760, status: 'received' },
      { id: '2', number: 'PO-2024-002', supplier_name: 'Tech Supplies', date: '2024-01-25', amount_ht: 5500, amount_ttc: 6600, status: 'ordered' },
    ],
    total: 2,
    page: 1,
    page_size: 25,
  },

  // Payments
  '/v1/payments': {
    items: [
      { id: '1', reference: 'PAY-001', amount: 250, currency: 'EUR', method: 'card', status: 'completed', customer_name: 'Client Web 1', created_at: '2024-01-28T10:30:00Z' },
      { id: '2', reference: 'PAY-002', amount: 89.99, currency: 'EUR', method: 'tap_to_pay', status: 'completed', customer_name: 'Client Mobile', created_at: '2024-01-28T11:15:00Z' },
      { id: '3', reference: 'PAY-003', amount: 1500, currency: 'EUR', method: 'bank_transfer', status: 'pending', customer_name: 'Entreprise XYZ', created_at: '2024-01-28T14:00:00Z' },
    ],
    total: 3,
    page: 1,
    page_size: 25,
  },
  '/v1/payments/summary': {
    total_today: 1839.99,
    transactions_today: 3,
    total_this_month: 45230,
    pending_count: 1,
    failed_count: 0,
  },

  // Admin
  '/v1/admin/users': {
    items: [
      { id: '1', email: 'admin@azalscore.local', name: 'Administrateur', roles: ['superadmin'], is_active: true, last_login: '2024-01-28T09:00:00Z', login_count: 156 },
      { id: '2', email: 'user@azalscore.local', name: 'Utilisateur Standard', roles: ['user'], is_active: true, last_login: '2024-01-27T14:30:00Z', login_count: 42 },
      { id: '3', email: 'comptable@azalscore.local', name: 'Comptable', roles: ['accountant'], is_active: true, last_login: '2024-01-28T08:15:00Z', login_count: 89 },
    ],
    total: 3,
    page: 1,
    page_size: 25,
  },
  '/v1/admin/tenants': {
    items: [
      { id: 'demo-tenant', name: 'Entreprise Démo', plan: 'professional', users_count: 3, is_active: true, created_at: '2024-01-01T00:00:00Z' },
    ],
    total: 1,
  },
  '/v1/admin/modules': {
    items: [
      { id: 'cockpit', name: 'Cockpit', is_active: true },
      { id: 'partners', name: 'Partenaires', is_active: true },
      { id: 'invoicing', name: 'Facturation', is_active: true },
      { id: 'treasury', name: 'Trésorerie', is_active: true },
      { id: 'accounting', name: 'Comptabilité', is_active: true },
      { id: 'projects', name: 'Projets', is_active: true },
      { id: 'interventions', name: 'Interventions', is_active: true },
      { id: 'purchases', name: 'Achats', is_active: true },
      { id: 'payments', name: 'Paiements', is_active: true },
    ],
  },

  // Auth
  '/v1/auth/capabilities': {
    capabilities: [], // Will be filled by getDemoCapabilities
  },
  '/v1/auth/me': null, // Will trigger error, handled by auth store
};

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
// MOCK API POUR MODE DÉMO
// ============================================================

const findDemoData = (url: string): unknown | undefined => {
  // Exact match
  if (DEMO_DATA[url] !== undefined) {
    return DEMO_DATA[url];
  }

  // Match with query params stripped
  const baseUrl = url.split('?')[0];
  if (DEMO_DATA[baseUrl] !== undefined) {
    return DEMO_DATA[baseUrl];
  }

  // Partial match for paginated endpoints
  for (const key of Object.keys(DEMO_DATA)) {
    if (baseUrl.startsWith(key) || url.startsWith(key)) {
      return DEMO_DATA[key];
    }
  }

  return undefined;
};

const createDemoResponse = <T>(data: T): ApiResponse<T> => {
  return { data } as ApiResponse<T>;
};

// ============================================================
// API PUBLIQUE
// ============================================================

export const api = {
  async get<T>(url: string, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    // Mode démo - retourner les données mockées
    if (DEMO_MODE) {
      const mockData = findDemoData(url);
      if (mockData !== undefined && mockData !== null) {
        // Simuler un petit délai réseau
        await new Promise(resolve => setTimeout(resolve, 50));
        return createDemoResponse(mockData as T);
      }
    }

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
    // Mode démo - simuler les POST
    if (DEMO_MODE) {
      // Pour les audits, ignorer silencieusement
      if (url.includes('/audit/')) {
        await new Promise(resolve => setTimeout(resolve, 10));
        return createDemoResponse({} as T);
      }
      // Pour les autres POST, retourner un succès
      await new Promise(resolve => setTimeout(resolve, 100));
      return createDemoResponse({ success: true, id: 'demo-' + Date.now() } as T);
    }

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
    // Mode démo
    if (DEMO_MODE) {
      await new Promise(resolve => setTimeout(resolve, 100));
      return createDemoResponse({ success: true, ...data as object } as T);
    }

    const response = await executeWithRetry(
      () => apiClient.put<ApiResponse<T>>(url, data, {
        timeout: config?.timeout,
      }),
      config
    );
    return response.data;
  },

  async patch<T>(url: string, data?: unknown, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    // Mode démo
    if (DEMO_MODE) {
      await new Promise(resolve => setTimeout(resolve, 100));
      return createDemoResponse({ success: true, ...data as object } as T);
    }

    const response = await executeWithRetry(
      () => apiClient.patch<ApiResponse<T>>(url, data, {
        timeout: config?.timeout,
      }),
      config
    );
    return response.data;
  },

  async delete<T>(url: string, config?: ApiRequestConfig): Promise<ApiResponse<T>> {
    // Mode démo
    if (DEMO_MODE) {
      await new Promise(resolve => setTimeout(resolve, 100));
      return createDemoResponse({ success: true } as T);
    }

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
