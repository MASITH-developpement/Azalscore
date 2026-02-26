/**
 * AZALSCORE - Audit API
 * =====================
 * Complete typed API client for Audit Trail module.
 * Covers: Audit Logs, Sessions, Compliance, Exports
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const auditKeys = {
  all: ['audit'] as const,
  logs: () => [...auditKeys.all, 'logs'] as const,
  log: (id: string) => [...auditKeys.logs(), id] as const,
  sessions: () => [...auditKeys.all, 'sessions'] as const,
  compliance: () => [...auditKeys.all, 'compliance'] as const,
  exports: () => [...auditKeys.all, 'exports'] as const,
  stats: () => [...auditKeys.all, 'stats'] as const,
};

// ============================================================================
// TYPES
// ============================================================================

export type AuditAction = 'CREATE' | 'UPDATE' | 'DELETE' | 'READ' | 'LOGIN' | 'LOGOUT' | 'EXPORT' | 'IMPORT';

export interface AuditLog {
  id: string;
  tenant_id: string;
  user_id: string;
  user_email?: string;
  action: AuditAction;
  entity_type: string;
  entity_id?: string;
  description: string;
  old_values?: Record<string, unknown> | null;
  new_values?: Record<string, unknown> | null;
  diff?: Record<string, unknown> | null;
  ip_address?: string;
  user_agent?: string;
  session_id?: string;
  created_at: string;
}

export interface AuditSession {
  id: string;
  tenant_id: string;
  user_id: string;
  user_email: string;
  started_at: string;
  ended_at?: string | null;
  ip_address: string;
  user_agent: string;
  is_active: boolean;
  actions_count: number;
}

export interface AuditExport {
  id: string;
  tenant_id: string;
  requested_by: string;
  format: 'JSON' | 'CSV' | 'PDF';
  filters: Record<string, unknown>;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  file_url?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface AuditStats {
  total_logs: number;
  logs_today: number;
  active_sessions: number;
  by_action: Record<AuditAction, number>;
  by_entity_type: Record<string, number>;
  top_users: { user_id: string; email: string; count: number }[];
}

// ============================================================================
// HOOKS - AUDIT LOGS
// ============================================================================

export function useAuditLogs(filters?: {
  user_id?: string;
  action?: AuditAction;
  entity_type?: string;
  entity_id?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...auditKeys.logs(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.action) params.append('action', filters.action);
      if (filters?.entity_type) params.append('entity_type', filters.entity_type);
      if (filters?.entity_id) params.append('entity_id', filters.entity_id);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: AuditLog[]; total: number }>(
        `/audit/logs${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useAuditLog(id: string) {
  return useQuery({
    queryKey: auditKeys.log(id),
    queryFn: async () => {
      const response = await api.get<AuditLog>(`/audit/logs/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useEntityHistory(entityType: string, entityId: string) {
  return useQuery({
    queryKey: [...auditKeys.logs(), 'entity', entityType, entityId],
    queryFn: async () => {
      const response = await api.get<{ items: AuditLog[] }>(
        `/audit/logs/entity/${entityType}/${entityId}`
      );
      return response;
    },
    enabled: !!entityType && !!entityId,
  });
}

// ============================================================================
// HOOKS - SESSIONS
// ============================================================================

export function useAuditSessions(filters?: { user_id?: string; is_active?: boolean }) {
  return useQuery({
    queryKey: [...auditKeys.sessions(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: AuditSession[]; total: number }>(
        `/audit/sessions${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useTerminateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: string) => {
      return api.post(`/audit/sessions/${sessionId}/terminate`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.sessions() });
    },
  });
}

// ============================================================================
// HOOKS - EXPORTS
// ============================================================================

export function useAuditExports() {
  return useQuery({
    queryKey: auditKeys.exports(),
    queryFn: async () => {
      const response = await api.get<{ items: AuditExport[] }>('/audit/exports');
      return response;
    },
  });
}

export function useCreateAuditExport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      format: 'JSON' | 'CSV' | 'PDF';
      filters?: Record<string, unknown>;
    }) => {
      return api.post<AuditExport>('/audit/exports', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.exports() });
    },
  });
}

// ============================================================================
// HOOKS - STATS
// ============================================================================

export function useAuditStats() {
  return useQuery({
    queryKey: auditKeys.stats(),
    queryFn: async () => {
      const response = await api.get<AuditStats>('/audit/stats');
      return response;
    },
  });
}
