/**
 * AZALSCORE - Module Passerelles d'Import - API Client
 * =====================================================
 */

import { api } from '@/core/api-client';
import type {
  OdooConnectionConfig,
  ImportHistory,
  CreateConfigRequest,
  UpdateConfigRequest,
  TestConnectionRequest,
  TestConnectionResponse,
  ScheduleConfig,
  ScheduleConfigResponse,
  NextRunsResponse,
  SelectiveImportRequest,
  HistorySearchParams,
  HistorySearchResponse,
} from './types';

const BASE_URL = '/odoo';

// ============================================================
// CONFIGURATION CRUD
// ============================================================

export const configApi = {
  list: async (activeOnly = false): Promise<OdooConnectionConfig[]> => {
    const url = activeOnly ? `${BASE_URL}/config?active_only=true` : `${BASE_URL}/config`;
    const response = await api.get<OdooConnectionConfig[]>(url);
    return response as unknown as OdooConnectionConfig[];
  },

  get: async (id: string): Promise<OdooConnectionConfig> => {
    const response = await api.get<OdooConnectionConfig>(`${BASE_URL}/config/${id}`);
    return response as unknown as OdooConnectionConfig;
  },

  create: async (data: CreateConfigRequest): Promise<OdooConnectionConfig> => {
    const response = await api.post<OdooConnectionConfig>(`${BASE_URL}/config`, data);
    return response as unknown as OdooConnectionConfig;
  },

  update: async (id: string, data: UpdateConfigRequest): Promise<OdooConnectionConfig> => {
    const response = await api.put<OdooConnectionConfig>(`${BASE_URL}/config/${id}`, data);
    return response as unknown as OdooConnectionConfig;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/config/${id}`);
  },

  getStats: async (id: string): Promise<Record<string, unknown>> => {
    const response = await api.get<Record<string, unknown>>(`${BASE_URL}/config/${id}/stats`);
    return response as unknown as Record<string, unknown>;
  },
};

// ============================================================
// TEST CONNECTION
// ============================================================

export const connectionApi = {
  test: async (data: TestConnectionRequest): Promise<TestConnectionResponse> => {
    const response = await api.post<TestConnectionResponse>(`${BASE_URL}/test`, data);
    return response as unknown as TestConnectionResponse;
  },

  testConfig: async (configId: string): Promise<TestConnectionResponse> => {
    const response = await api.post<TestConnectionResponse>(`${BASE_URL}/config/${configId}/test`, {});
    return response as unknown as TestConnectionResponse;
  },
};

// ============================================================
// IMPORT OPERATIONS
// ============================================================

export const importApi = {
  fullSync: async (configId: string, fullSync = false): Promise<ImportHistory[]> => {
    const url = `${BASE_URL}/import/full?config_id=${configId}&full_sync=${fullSync}`;
    const response = await api.post<ImportHistory[]>(url, {});
    return response as unknown as ImportHistory[];
  },

  selectiveImport: async (configId: string, data: SelectiveImportRequest): Promise<ImportHistory[]> => {
    const response = await api.post<ImportHistory[]>(`${BASE_URL}/config/${configId}/import/selective`, data);
    return response as unknown as ImportHistory[];
  },

  importProducts: async (configId: string, fullSync = false): Promise<ImportHistory> => {
    const url = `${BASE_URL}/import/products?config_id=${configId}&full_sync=${fullSync}`;
    const response = await api.post<ImportHistory>(url, {});
    return response as unknown as ImportHistory;
  },

  importContacts: async (configId: string, fullSync = false): Promise<ImportHistory> => {
    const url = `${BASE_URL}/import/contacts?config_id=${configId}&full_sync=${fullSync}`;
    const response = await api.post<ImportHistory>(url, {});
    return response as unknown as ImportHistory;
  },

  importSuppliers: async (configId: string, fullSync = false): Promise<ImportHistory> => {
    const url = `${BASE_URL}/import/suppliers?config_id=${configId}&full_sync=${fullSync}`;
    const response = await api.post<ImportHistory>(url, {});
    return response as unknown as ImportHistory;
  },

  importInvoices: async (configId: string, fullSync = false): Promise<ImportHistory> => {
    const url = `${BASE_URL}/import/invoices?config_id=${configId}&full_sync=${fullSync}`;
    const response = await api.post<ImportHistory>(url, {});
    return response as unknown as ImportHistory;
  },

  importQuotes: async (configId: string, fullSync = false): Promise<ImportHistory> => {
    const url = `${BASE_URL}/import/quotes?config_id=${configId}&full_sync=${fullSync}`;
    const response = await api.post<ImportHistory>(url, {});
    return response as unknown as ImportHistory;
  },

  importInterventions: async (configId: string, fullSync = false): Promise<ImportHistory> => {
    const url = `${BASE_URL}/import/interventions?config_id=${configId}&full_sync=${fullSync}`;
    const response = await api.post<ImportHistory>(url, {});
    return response as unknown as ImportHistory;
  },
};

// ============================================================
// SCHEDULING
// ============================================================

export const scheduleApi = {
  configure: async (configId: string, data: ScheduleConfig): Promise<ScheduleConfigResponse> => {
    const response = await api.put<ScheduleConfigResponse>(`${BASE_URL}/config/${configId}/schedule`, data);
    return response as unknown as ScheduleConfigResponse;
  },

  pause: async (configId: string): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>(`${BASE_URL}/config/${configId}/schedule/pause`, {});
    return response as unknown as { message: string };
  },

  resume: async (configId: string): Promise<{ message: string; next_scheduled_run?: string }> => {
    const response = await api.post<{ message: string; next_scheduled_run?: string }>(`${BASE_URL}/config/${configId}/schedule/resume`, {});
    return response as unknown as { message: string; next_scheduled_run?: string };
  },

  getNextRuns: async (configId: string, count = 5): Promise<NextRunsResponse> => {
    const response = await api.get<NextRunsResponse>(`${BASE_URL}/config/${configId}/schedule/next-runs?count=${count}`);
    return response as unknown as NextRunsResponse;
  },
};

// ============================================================
// HISTORY
// ============================================================

export const historyApi = {
  list: async (configId?: string, limit = 50): Promise<ImportHistory[]> => {
    let url = `${BASE_URL}/history?limit=${limit}`;
    if (configId) url += `&config_id=${configId}`;
    const response = await api.get<ImportHistory[]>(url);
    return response as unknown as ImportHistory[];
  },

  search: async (params: HistorySearchParams): Promise<HistorySearchResponse> => {
    const response = await api.post<HistorySearchResponse>(`${BASE_URL}/history/search`, params);
    return response as unknown as HistorySearchResponse;
  },

  getDetail: async (historyId: string): Promise<ImportHistory> => {
    const response = await api.get<ImportHistory>(`${BASE_URL}/history/${historyId}`);
    return response as unknown as ImportHistory;
  },
};

export const odooApi = {
  config: configApi,
  connection: connectionApi,
  import: importApi,
  schedule: scheduleApi,
  history: historyApi,
};

export default odooApi;
