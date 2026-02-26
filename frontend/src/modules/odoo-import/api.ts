/**
 * AZALSCORE - Odoo Import API
 * ============================
 * Complete typed API client for Odoo Import module.
 * Covers: Configurations, Import Operations, Field Mappings, Scheduling, History
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const odooImportKeys = {
  all: ['odoo-import'] as const,
  configs: () => [...odooImportKeys.all, 'configs'] as const,
  config: (id: string) => [...odooImportKeys.configs(), id] as const,
  status: () => [...odooImportKeys.all, 'status'] as const,
  history: () => [...odooImportKeys.all, 'history'] as const,
  historyDetail: (id: string) => [...odooImportKeys.history(), id] as const,
  progress: (importId: string) => [...odooImportKeys.all, 'progress', importId] as const,
  mappings: (configId: string) => [...odooImportKeys.all, 'mappings', configId] as const,
  mapping: (id: string) => [...odooImportKeys.all, 'mapping', id] as const,
  stats: (configId: string) => [...odooImportKeys.all, 'stats', configId] as const,
  schedule: (configId: string) => [...odooImportKeys.all, 'schedule', configId] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type SyncType = 'products' | 'contacts' | 'suppliers' | 'purchase_orders' | 'sale_orders' | 'invoices' | 'quotes' | 'accounting' | 'bank' | 'interventions' | 'full';

export type ImportStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type AuthMethod = 'password' | 'api_key';

export type ScheduleMode = 'disabled' | 'cron' | 'interval';

export type TriggerMethod = 'manual' | 'scheduled' | 'api';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface OdooConnectionConfig {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  odoo_url: string;
  odoo_database: string;
  odoo_version?: string | null;
  auth_method: AuthMethod;
  username: string;
  // credential is never returned for security

  // Sync options
  sync_products: boolean;
  sync_contacts: boolean;
  sync_suppliers: boolean;
  sync_purchase_orders: boolean;
  sync_sale_orders: boolean;
  sync_invoices: boolean;
  sync_quotes: boolean;
  sync_accounting: boolean;
  sync_bank: boolean;
  sync_interventions: boolean;

  // Last sync timestamps
  products_last_sync_at?: string | null;
  contacts_last_sync_at?: string | null;
  suppliers_last_sync_at?: string | null;
  orders_last_sync_at?: string | null;

  // Stats
  total_imports: number;
  total_products_imported: number;
  total_contacts_imported: number;
  total_suppliers_imported: number;
  total_orders_imported: number;
  last_error_message?: string | null;

  // Connection status
  is_active: boolean;
  is_connected: boolean;
  last_connection_test_at?: string | null;

  // Scheduling
  schedule_mode: ScheduleMode;
  schedule_cron_expression?: string | null;
  schedule_interval_minutes?: number | null;
  schedule_timezone: string;
  schedule_paused: boolean;
  next_scheduled_run?: string | null;
  last_scheduled_run?: string | null;

  created_at: string;
  updated_at: string;
}

export interface OdooTestConnectionResponse {
  success: boolean;
  message: string;
  odoo_version?: string | null;
  database_name?: string | null;
  user_name?: string | null;
  available_models?: string[] | null;
}

export interface OdooImportProgress {
  import_id: string;
  sync_type: SyncType;
  status: ImportStatus;
  progress_percent: number;
  current_record: number;
  total_records: number;
  created_count: number;
  updated_count: number;
  error_count: number;
  started_at: string;
  estimated_completion?: string | null;
}

export interface OdooImportHistory {
  id: string;
  config_id: string;
  config_name?: string | null;
  sync_type: SyncType;
  status: ImportStatus;
  started_at: string;
  completed_at?: string | null;
  duration_seconds?: number | null;
  total_records: number;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  error_count: number;
  error_details: Array<Record<string, unknown>>;
  is_delta_sync: boolean;
  delta_from_date?: string | null;
  triggered_by?: string | null;
  trigger_method: TriggerMethod;
  import_summary?: Record<string, unknown> | null;
}

export interface OdooFieldMapping {
  id: string;
  config_id: string;
  odoo_model: string;
  azals_model: string;
  field_mapping: Record<string, string>;
  transformations: Record<string, Record<string, unknown>>;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface OdooDataPreview {
  model: string;
  total_count: number;
  preview_count: number;
  fields: string[];
  records: Array<Record<string, unknown>>;
  mapping_preview: Array<Record<string, unknown>>;
}

export interface OdooImportStatus {
  active_imports: OdooImportProgress[];
  recent_imports: OdooImportHistory[];
  configs: OdooConnectionConfig[];
  total_products_synced: number;
  total_contacts_synced: number;
  total_suppliers_synced: number;
  total_orders_synced: number;
  last_sync_at?: string | null;
  next_scheduled_sync?: string | null;
}

export interface OdooSyncStats {
  config_id: string;
  config_name: string;
  sync_type: SyncType;
  total_syncs: number;
  last_sync_at?: string | null;
  last_sync_status?: ImportStatus | null;
  average_duration_seconds?: number | null;
  total_records_synced: number;
  success_rate: number;
}

export interface OdooScheduleConfig {
  config_id: string;
  mode: ScheduleMode;
  cron_expression?: string | null;
  interval_minutes?: number | null;
  timezone: string;
  is_paused: boolean;
  next_scheduled_run?: string | null;
  last_scheduled_run?: string | null;
  message: string;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface OdooConnectionConfigCreate {
  name: string;
  description?: string;
  odoo_url: string;
  odoo_database: string;
  auth_method?: AuthMethod;
  username: string;
  credential: string;
  sync_products?: boolean;
  sync_contacts?: boolean;
  sync_suppliers?: boolean;
  sync_purchase_orders?: boolean;
  sync_sale_orders?: boolean;
  sync_invoices?: boolean;
  sync_quotes?: boolean;
  sync_accounting?: boolean;
  sync_bank?: boolean;
  sync_interventions?: boolean;
}

export interface OdooConnectionConfigUpdate {
  name?: string;
  description?: string;
  odoo_url?: string;
  odoo_database?: string;
  auth_method?: AuthMethod;
  username?: string;
  credential?: string;
  sync_products?: boolean;
  sync_contacts?: boolean;
  sync_suppliers?: boolean;
  sync_purchase_orders?: boolean;
  sync_sale_orders?: boolean;
  sync_invoices?: boolean;
  sync_quotes?: boolean;
  sync_accounting?: boolean;
  sync_bank?: boolean;
  sync_interventions?: boolean;
  is_active?: boolean;
}

export interface OdooTestConnectionRequest {
  odoo_url: string;
  odoo_database: string;
  auth_method?: AuthMethod;
  username: string;
  credential: string;
}

export interface OdooImportRequest {
  config_id: string;
  sync_type: SyncType;
  full_sync?: boolean;
}

export interface OdooSelectiveImportRequest {
  types: SyncType[];
  full_sync?: boolean;
}

export interface OdooFieldMappingCreate {
  config_id: string;
  odoo_model: string;
  azals_model: string;
  field_mapping: Record<string, string>;
  transformations?: Record<string, Record<string, unknown>>;
  is_active?: boolean;
  priority?: number;
}

export interface OdooFieldMappingUpdate {
  field_mapping?: Record<string, string>;
  transformations?: Record<string, Record<string, unknown>>;
  is_active?: boolean;
  priority?: number;
}

export interface OdooDataPreviewRequest {
  config_id: string;
  model: string;
  limit?: number;
  fields?: string[];
}

export interface OdooScheduleConfigRequest {
  mode: ScheduleMode;
  cron_expression?: string;
  interval_minutes?: number;
  timezone?: string;
}

export interface OdooHistorySearchRequest {
  config_id?: string;
  sync_type?: SyncType;
  status?: ImportStatus;
  trigger_method?: TriggerMethod;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

// ============================================================================
// HOOKS - CONFIGURATIONS
// ============================================================================

export function useOdooConfigs() {
  return useQuery({
    queryKey: odooImportKeys.configs(),
    queryFn: async () => {
      const response = await api.get<OdooConnectionConfig[] | { items: OdooConnectionConfig[] }>('/odoo/config');
      return Array.isArray(response) ? response : response.items || [];
    },
  });
}

export function useOdooConfig(id: string) {
  return useQuery({
    queryKey: odooImportKeys.config(id),
    queryFn: async () => {
      const response = await api.get<OdooConnectionConfig>(`/odoo/config/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateOdooConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OdooConnectionConfigCreate) => {
      return api.post<OdooConnectionConfig>('/odoo/config', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.configs() });
    },
  });
}

export function useUpdateOdooConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: OdooConnectionConfigUpdate }) => {
      return api.put<OdooConnectionConfig>(`/odoo/config/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.config(id) });
      queryClient.invalidateQueries({ queryKey: odooImportKeys.configs() });
    },
  });
}

export function useDeleteOdooConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/odoo/config/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.configs() });
    },
  });
}

// ============================================================================
// HOOKS - CONNECTION TEST
// ============================================================================

export function useTestOdooConnection() {
  return useMutation({
    mutationFn: async (data: OdooTestConnectionRequest) => {
      return api.post<OdooTestConnectionResponse>('/odoo/test', data);
    },
  });
}

export function useTestOdooConfigConnection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (configId: string) => {
      return api.post<OdooTestConnectionResponse>(`/odoo/config/${configId}/test`);
    },
    onSuccess: (_, configId) => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.config(configId) });
    },
  });
}

// ============================================================================
// HOOKS - IMPORT OPERATIONS
// ============================================================================

export function useOdooImportStatus() {
  return useQuery({
    queryKey: odooImportKeys.status(),
    queryFn: async () => {
      const response = await api.get<OdooImportStatus>('/odoo/status');
      return response;
    },
  });
}

export function useStartOdooImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ configId, syncType, fullSync }: { configId: string; syncType: SyncType; fullSync?: boolean }) => {
      const params = new URLSearchParams();
      params.append('config_id', configId);
      if (fullSync) params.append('full_sync', 'true');
      return api.post<OdooImportProgress>(`/odoo/import/${syncType}?${params.toString()}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.status() });
      queryClient.invalidateQueries({ queryKey: odooImportKeys.history() });
    },
  });
}

export function useStartSelectiveImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ configId, data }: { configId: string; data: OdooSelectiveImportRequest }) => {
      return api.post<OdooImportProgress[]>(`/odoo/config/${configId}/import/selective`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.status() });
      queryClient.invalidateQueries({ queryKey: odooImportKeys.history() });
    },
  });
}

export function useCancelOdooImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (importId: string) => {
      return api.post(`/odoo/import/${importId}/cancel`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.status() });
      queryClient.invalidateQueries({ queryKey: odooImportKeys.history() });
    },
  });
}

export function useOdooImportProgress(importId: string) {
  return useQuery({
    queryKey: odooImportKeys.progress(importId),
    queryFn: async () => {
      const response = await api.get<OdooImportProgress>(`/odoo/import/${importId}/progress`);
      return response;
    },
    enabled: !!importId,
    refetchInterval: 2000, // Poll every 2 seconds while import is running
  });
}

// ============================================================================
// HOOKS - HISTORY
// ============================================================================

export function useOdooImportHistory(filters?: OdooHistorySearchRequest) {
  return useQuery({
    queryKey: [...odooImportKeys.history(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.config_id) params.append('config_id', filters.config_id);
      if (filters?.sync_type) params.append('sync_type', filters.sync_type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.trigger_method) params.append('trigger_method', filters.trigger_method);
      if (filters?.date_from) params.append('date_from', filters.date_from);
      if (filters?.date_to) params.append('date_to', filters.date_to);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.page_size) params.append('page_size', String(filters.page_size));
      const queryString = params.toString();
      const response = await api.get<{ items: OdooImportHistory[]; total: number; page: number; page_size: number; total_pages: number } | OdooImportHistory[]>(
        `/odoo/history${queryString ? `?${queryString}` : ''}`
      );
      return Array.isArray(response) ? { items: response, total: response.length } : response;
    },
  });
}

export function useOdooImportHistoryDetail(id: string) {
  return useQuery({
    queryKey: odooImportKeys.historyDetail(id),
    queryFn: async () => {
      const response = await api.get<OdooImportHistory>(`/odoo/history/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

// ============================================================================
// HOOKS - FIELD MAPPINGS
// ============================================================================

export function useOdooFieldMappings(configId: string) {
  return useQuery({
    queryKey: odooImportKeys.mappings(configId),
    queryFn: async () => {
      const response = await api.get<{ items: OdooFieldMapping[] }>(`/odoo/config/${configId}/mappings`);
      return response;
    },
    enabled: !!configId,
  });
}

export function useOdooFieldMapping(id: string) {
  return useQuery({
    queryKey: odooImportKeys.mapping(id),
    queryFn: async () => {
      const response = await api.get<OdooFieldMapping>(`/odoo/mappings/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateOdooFieldMapping() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OdooFieldMappingCreate) => {
      return api.post<OdooFieldMapping>('/odoo/mappings', data);
    },
    onSuccess: (_, { config_id }) => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.mappings(config_id) });
    },
  });
}

export function useUpdateOdooFieldMapping() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, configId, data }: { id: string; configId: string; data: OdooFieldMappingUpdate }) => {
      return api.put<OdooFieldMapping>(`/odoo/mappings/${id}`, data);
    },
    onSuccess: (_, { id, configId }) => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.mapping(id) });
      queryClient.invalidateQueries({ queryKey: odooImportKeys.mappings(configId) });
    },
  });
}

export function useDeleteOdooFieldMapping() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, configId }: { id: string; configId: string }) => {
      return api.delete(`/odoo/mappings/${id}`);
    },
    onSuccess: (_, { configId }) => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.mappings(configId) });
    },
  });
}

// ============================================================================
// HOOKS - DATA PREVIEW
// ============================================================================

export function useOdooDataPreview() {
  return useMutation({
    mutationFn: async (data: OdooDataPreviewRequest) => {
      return api.post<OdooDataPreview>('/odoo/preview', data);
    },
  });
}

// ============================================================================
// HOOKS - STATISTICS
// ============================================================================

export function useOdooSyncStats(configId: string) {
  return useQuery({
    queryKey: odooImportKeys.stats(configId),
    queryFn: async () => {
      const response = await api.get<{ items: OdooSyncStats[] }>(`/odoo/config/${configId}/stats`);
      return response;
    },
    enabled: !!configId,
  });
}

// ============================================================================
// HOOKS - SCHEDULING
// ============================================================================

export function useOdooScheduleConfig(configId: string) {
  return useQuery({
    queryKey: odooImportKeys.schedule(configId),
    queryFn: async () => {
      const response = await api.get<OdooScheduleConfig>(`/odoo/config/${configId}/schedule`);
      return response;
    },
    enabled: !!configId,
  });
}

export function useUpdateOdooSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ configId, data }: { configId: string; data: OdooScheduleConfigRequest }) => {
      return api.put<OdooScheduleConfig>(`/odoo/config/${configId}/schedule`, data);
    },
    onSuccess: (_, { configId }) => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.schedule(configId) });
      queryClient.invalidateQueries({ queryKey: odooImportKeys.config(configId) });
    },
  });
}

export function usePauseOdooSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (configId: string) => {
      return api.post<OdooScheduleConfig>(`/odoo/config/${configId}/schedule/pause`);
    },
    onSuccess: (_, configId) => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.schedule(configId) });
      queryClient.invalidateQueries({ queryKey: odooImportKeys.config(configId) });
    },
  });
}

export function useResumeOdooSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (configId: string) => {
      return api.post<OdooScheduleConfig>(`/odoo/config/${configId}/schedule/resume`);
    },
    onSuccess: (_, configId) => {
      queryClient.invalidateQueries({ queryKey: odooImportKeys.schedule(configId) });
      queryClient.invalidateQueries({ queryKey: odooImportKeys.config(configId) });
    },
  });
}

export function useGetNextRuns(configId: string, count?: number) {
  return useQuery({
    queryKey: [...odooImportKeys.schedule(configId), 'next-runs', count],
    queryFn: async () => {
      const params = count ? `?count=${count}` : '';
      const response = await api.get<{ config_id: string; mode: ScheduleMode; next_runs: string[] }>(
        `/odoo/config/${configId}/schedule/next-runs${params}`
      );
      return response;
    },
    enabled: !!configId,
  });
}

// ============================================================================
// HOOKS - AVAILABLE MODELS
// ============================================================================

export function useOdooAvailableModels(configId: string) {
  return useQuery({
    queryKey: [...odooImportKeys.config(configId), 'models'],
    queryFn: async () => {
      const response = await api.get<{ models: string[] }>(`/odoo/config/${configId}/models`);
      return response;
    },
    enabled: !!configId,
  });
}

export function useOdooModelFields(configId: string, model: string) {
  return useQuery({
    queryKey: [...odooImportKeys.config(configId), 'models', model, 'fields'],
    queryFn: async () => {
      const response = await api.get<{ fields: Array<{ name: string; type: string; label: string }> }>(
        `/odoo/config/${configId}/models/${encodeURIComponent(model)}/fields`
      );
      return response;
    },
    enabled: !!configId && !!model,
  });
}
