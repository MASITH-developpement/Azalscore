/**
 * AZALSCORE - Backup API
 * =======================
 * Complete typed API client for Backup & Restore management.
 * Covers: Configuration, Backups, Restores, Statistics
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const backupKeys = {
  all: ['backup'] as const,
  config: () => [...backupKeys.all, 'config'] as const,
  list: () => [...backupKeys.all, 'list'] as const,
  detail: (id: string) => [...backupKeys.all, id] as const,
  restores: () => [...backupKeys.all, 'restores'] as const,
  restore: (id: string) => [...backupKeys.restores(), id] as const,
  stats: () => [...backupKeys.all, 'stats'] as const,
  dashboard: () => [...backupKeys.all, 'dashboard'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type BackupFrequency = 'DAILY' | 'WEEKLY' | 'MONTHLY';
export type BackupType = 'FULL' | 'INCREMENTAL' | 'DIFFERENTIAL';
export type BackupStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface BackupConfig {
  id: string;
  tenant_id: string;
  encryption_algorithm: string;
  frequency: BackupFrequency;
  backup_hour: number;
  backup_day: number;
  backup_day_of_month: number;
  retention_days: number;
  max_backups: number;
  storage_path?: string | null;
  storage_type: string;
  include_attachments: boolean;
  compress: boolean;
  verify_after_backup: boolean;
  is_active: boolean;
  last_backup_at?: string | null;
  next_backup_at?: string | null;
  created_at: string;
}

export interface Backup {
  id: string;
  tenant_id: string;
  reference: string;
  backup_type: BackupType;
  status: BackupStatus;
  file_name?: string | null;
  file_size?: number | null;
  file_checksum?: string | null;
  is_encrypted: boolean;
  encryption_algorithm: string;
  records_count: number;
  include_attachments: boolean;
  is_compressed: boolean;
  started_at?: string | null;
  completed_at?: string | null;
  duration_seconds?: number | null;
  last_restored_at?: string | null;
  restore_count: number;
  notes?: string | null;
  error_message?: string | null;
  triggered_by?: string | null;
  created_at: string;
}

export interface BackupDetail extends Backup {
  file_path?: string | null;
  encryption_iv?: string | null;
  tables_included: string[];
}

export interface RestoreResult {
  id: string;
  backup_id: string;
  tenant_id: string;
  status: BackupStatus;
  target_type: string;
  target_tenant_id?: string | null;
  tables_restored: string[];
  records_restored: number;
  started_at?: string | null;
  completed_at?: string | null;
  duration_seconds?: number | null;
  error_message?: string | null;
  created_at: string;
}

export interface BackupStats {
  total_backups: number;
  total_size_bytes: number;
  last_backup_at?: string | null;
  last_backup_status?: BackupStatus | null;
  next_backup_at?: string | null;
  success_rate: number;
  average_duration_seconds: number;
}

export interface BackupDashboard {
  config?: BackupConfig | null;
  stats: BackupStats;
  recent_backups: Backup[];
  recent_restores: RestoreResult[];
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface BackupConfigCreate {
  frequency?: BackupFrequency;
  backup_hour?: number;
  backup_day?: number;
  backup_day_of_month?: number;
  retention_days?: number;
  max_backups?: number;
  storage_path?: string;
  storage_type?: string;
  include_attachments?: boolean;
  compress?: boolean;
  verify_after_backup?: boolean;
}

export interface BackupConfigUpdate {
  frequency?: BackupFrequency;
  backup_hour?: number;
  backup_day?: number;
  backup_day_of_month?: number;
  retention_days?: number;
  max_backups?: number;
  storage_path?: string;
  storage_type?: string;
  include_attachments?: boolean;
  compress?: boolean;
  verify_after_backup?: boolean;
  is_active?: boolean;
}

export interface BackupCreate {
  backup_type?: BackupType;
  include_attachments?: boolean;
  notes?: string;
}

export interface RestoreRequest {
  backup_id: string;
  target_type?: string;
  target_tenant_id?: string;
  tables_to_restore?: string[];
}

// ============================================================================
// HOOKS - CONFIGURATION
// ============================================================================

export function useBackupConfig() {
  return useQuery({
    queryKey: backupKeys.config(),
    queryFn: async () => {
      const response = await api.get<BackupConfig>('/backup/config');
      return response;
    },
  });
}

export function useCreateBackupConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BackupConfigCreate) => {
      return api.post<BackupConfig>('/backup/config', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: backupKeys.config() });
      queryClient.invalidateQueries({ queryKey: backupKeys.dashboard() });
    },
  });
}

export function useUpdateBackupConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BackupConfigUpdate) => {
      return api.put<BackupConfig>('/backup/config', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: backupKeys.config() });
      queryClient.invalidateQueries({ queryKey: backupKeys.dashboard() });
    },
  });
}

export function useToggleBackupSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (enabled: boolean) => {
      return api.post<BackupConfig>('/backup/config/toggle', { is_active: enabled });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: backupKeys.config() });
    },
  });
}

// ============================================================================
// HOOKS - BACKUPS
// ============================================================================

export function useBackups(filters?: {
  status?: BackupStatus;
  backup_type?: BackupType;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...backupKeys.list(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.backup_type) params.append('backup_type', filters.backup_type);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Backup[]; total: number }>(
        `/backup/backups${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useBackup(id: string) {
  return useQuery({
    queryKey: backupKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<BackupDetail>(`/backup/backups/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data?: BackupCreate) => {
      return api.post<Backup>('/backup/backups', data || {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: backupKeys.list() });
      queryClient.invalidateQueries({ queryKey: backupKeys.stats() });
      queryClient.invalidateQueries({ queryKey: backupKeys.dashboard() });
    },
  });
}

export function useTriggerBackupNow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (backupType?: BackupType) => {
      return api.post<Backup>('/backup/trigger', { backup_type: backupType || 'FULL' });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: backupKeys.list() });
      queryClient.invalidateQueries({ queryKey: backupKeys.stats() });
      queryClient.invalidateQueries({ queryKey: backupKeys.dashboard() });
    },
  });
}

export function useCancelBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Backup>(`/backup/backups/${id}/cancel`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: backupKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: backupKeys.list() });
    },
  });
}

export function useDeleteBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/backup/backups/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: backupKeys.list() });
      queryClient.invalidateQueries({ queryKey: backupKeys.stats() });
    },
  });
}

export function useDownloadBackup() {
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.get<{ download_url: string; expires_at: string }>(
        `/backup/backups/${id}/download`
      );
      return response;
    },
  });
}

export function useVerifyBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<{ valid: boolean; message: string; checksum_match: boolean }>(
        `/backup/backups/${id}/verify`
      );
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: backupKeys.detail(id) });
    },
  });
}

// ============================================================================
// HOOKS - RESTORES
// ============================================================================

export function useRestores(filters?: {
  status?: BackupStatus;
  backup_id?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...backupKeys.restores(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.backup_id) params.append('backup_id', filters.backup_id);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: RestoreResult[]; total: number }>(
        `/backup/restores${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useRestore(id: string) {
  return useQuery({
    queryKey: backupKeys.restore(id),
    queryFn: async () => {
      const response = await api.get<RestoreResult>(`/backup/restores/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useRestoreBackup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RestoreRequest) => {
      return api.post<RestoreResult>('/backup/restore', data);
    },
    onSuccess: (_, { backup_id }) => {
      queryClient.invalidateQueries({ queryKey: backupKeys.restores() });
      queryClient.invalidateQueries({ queryKey: backupKeys.detail(backup_id) });
      queryClient.invalidateQueries({ queryKey: backupKeys.dashboard() });
    },
  });
}

export function usePreviewRestore() {
  return useMutation({
    mutationFn: async (backupId: string) => {
      return api.post<{
        backup: Backup;
        tables: Array<{ name: string; records: number }>;
        estimated_duration_seconds: number;
        warnings: string[];
      }>(`/backup/backups/${backupId}/restore-preview`);
    },
  });
}

// ============================================================================
// HOOKS - STATISTICS & DASHBOARD
// ============================================================================

export function useBackupStats() {
  return useQuery({
    queryKey: backupKeys.stats(),
    queryFn: async () => {
      const response = await api.get<BackupStats>('/backup/stats');
      return response;
    },
  });
}

export function useBackupDashboard() {
  return useQuery({
    queryKey: backupKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<BackupDashboard>('/backup/dashboard');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - STORAGE MANAGEMENT
// ============================================================================

export function useBackupStorageInfo() {
  return useQuery({
    queryKey: [...backupKeys.all, 'storage'],
    queryFn: async () => {
      const response = await api.get<{
        total_size_bytes: number;
        used_size_bytes: number;
        available_size_bytes: number;
        backup_count: number;
        oldest_backup_date?: string;
        newest_backup_date?: string;
      }>('/backup/storage');
      return response;
    },
  });
}

export function useCleanupOldBackups() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (options?: { keep_last?: number; older_than_days?: number }) => {
      return api.post<{ deleted_count: number; freed_bytes: number }>(
        '/backup/cleanup',
        options || {}
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: backupKeys.list() });
      queryClient.invalidateQueries({ queryKey: backupKeys.stats() });
    },
  });
}

// ============================================================================
// HOOKS - EXPORT/IMPORT BACKUP FILES
// ============================================================================

export function useExportBackupToS3() {
  return useMutation({
    mutationFn: async ({ backupId, s3Bucket, s3Key }: {
      backupId: string;
      s3Bucket: string;
      s3Key: string;
    }) => {
      return api.post<{ success: boolean; s3_url: string }>(
        `/backup/backups/${backupId}/export-s3`,
        { s3_bucket: s3Bucket, s3_key: s3Key }
      );
    },
  });
}

export function useImportBackupFromS3() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ s3Bucket, s3Key }: { s3Bucket: string; s3Key: string }) => {
      return api.post<Backup>('/backup/import-s3', { s3_bucket: s3Bucket, s3_key: s3Key });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: backupKeys.list() });
    },
  });
}
