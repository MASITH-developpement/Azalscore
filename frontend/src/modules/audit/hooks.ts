/**
 * AZALSCORE Module - Audit Hooks
 * React Query hooks for Audit module
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import type {
  AuditLog,
  AuditLogListResponse,
  AuditLogFilters,
  AuditSession,
  AuditDashboardResponse,
  AuditStats,
  Metric,
  MetricValue,
  Benchmark,
  BenchmarkResult,
  ComplianceCheck,
  ComplianceSummary,
  RetentionRule,
  AuditExport,
} from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const auditKeys = {
  all: ['audit'] as const,
  dashboard: () => [...auditKeys.all, 'dashboard'] as const,
  stats: () => [...auditKeys.all, 'stats'] as const,
  logs: (filters?: AuditLogFilters) => [...auditKeys.all, 'logs', filters] as const,
  log: (id: string) => [...auditKeys.all, 'log', id] as const,
  entityHistory: (entityType: string, entityId: string) => [...auditKeys.all, 'entity-history', entityType, entityId] as const,
  userActivity: (userId: string) => [...auditKeys.all, 'user-activity', userId] as const,
  sessions: () => [...auditKeys.all, 'sessions'] as const,
  metrics: (module?: string) => [...auditKeys.all, 'metrics', module] as const,
  metricValues: (metricCode: string, fromDate?: string, toDate?: string) => [...auditKeys.all, 'metric-values', metricCode, fromDate, toDate] as const,
  benchmarks: (benchmarkType?: string) => [...auditKeys.all, 'benchmarks', benchmarkType] as const,
  benchmarkResults: (benchmarkId: string) => [...auditKeys.all, 'benchmark-results', benchmarkId] as const,
  complianceChecks: (framework?: string, status?: string) => [...auditKeys.all, 'compliance-checks', framework, status] as const,
  complianceSummary: (framework?: string) => [...auditKeys.all, 'compliance-summary', framework] as const,
  retentionRules: () => [...auditKeys.all, 'retention-rules'] as const,
  exports: () => [...auditKeys.all, 'exports'] as const,
};

// ============================================================================
// DASHBOARD & STATS
// ============================================================================

export const useAuditDashboard = () => {
  return useQuery({
    queryKey: auditKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<AuditDashboardResponse>('/audit/dashboard');
      return response.data;
    },
  });
};

export const useAuditStats = () => {
  return useQuery({
    queryKey: auditKeys.stats(),
    queryFn: async () => {
      const response = await api.get<AuditStats>('/audit/stats');
      return response.data;
    },
  });
};

// ============================================================================
// LOGS
// ============================================================================

export const useAuditLogs = (filters?: AuditLogFilters) => {
  return useQuery({
    queryKey: auditKeys.logs(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.action) params.append('action', filters.action);
      if (filters?.level) params.append('level', filters.level);
      if (filters?.category) params.append('category', filters.category);
      if (filters?.module) params.append('module', filters.module);
      if (filters?.entity_type) params.append('entity_type', filters.entity_type);
      if (filters?.entity_id) params.append('entity_id', filters.entity_id);
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.session_id) params.append('session_id', filters.session_id);
      if (filters?.success !== undefined) params.append('success', String(filters.success));
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.search_text) params.append('search_text', filters.search_text);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.page_size) params.append('page_size', String(filters.page_size));

      const url = `/audit/logs${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<AuditLogListResponse>(url);
      return response.data;
    },
  });
};

export const useAuditLog = (id: string) => {
  return useQuery({
    queryKey: auditKeys.log(id),
    queryFn: async () => {
      const response = await api.get<AuditLog>(`/audit/logs/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useEntityHistory = (entityType: string, entityId: string) => {
  return useQuery({
    queryKey: auditKeys.entityHistory(entityType, entityId),
    queryFn: async () => {
      const response = await api.get<AuditLog[]>(`/audit/logs/entity/${entityType}/${entityId}`);
      return response.data;
    },
    enabled: !!entityType && !!entityId,
  });
};

export const useUserActivity = (userId: string) => {
  return useQuery({
    queryKey: auditKeys.userActivity(userId),
    queryFn: async () => {
      const response = await api.get<AuditLog[]>(`/audit/logs/user/${userId}`);
      return response.data;
    },
    enabled: !!userId,
  });
};

// ============================================================================
// SESSIONS
// ============================================================================

export const useActiveSessions = () => {
  return useQuery({
    queryKey: auditKeys.sessions(),
    queryFn: async () => {
      const response = await api.get<AuditSession[]>('/audit/sessions');
      return response.data;
    },
  });
};

export const useTerminateSession = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ sessionId, reason }: { sessionId: string; reason?: string }) => {
      const url = reason
        ? `/audit/sessions/${sessionId}/terminate?reason=${encodeURIComponent(reason)}`
        : `/audit/sessions/${sessionId}/terminate`;
      await api.post(url);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.sessions() });
      queryClient.invalidateQueries({ queryKey: auditKeys.dashboard() });
    },
  });
};

// ============================================================================
// METRICS
// ============================================================================

export const useMetrics = (module?: string) => {
  return useQuery({
    queryKey: auditKeys.metrics(module),
    queryFn: async () => {
      const url = module ? `/audit/metrics?module=${module}` : '/audit/metrics';
      const response = await api.get<Metric[]>(url);
      return response.data;
    },
  });
};

export const useMetricValues = (metricCode: string, fromDate?: string, toDate?: string) => {
  return useQuery({
    queryKey: auditKeys.metricValues(metricCode, fromDate, toDate),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      const url = `/audit/metrics/${metricCode}/values${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<MetricValue[]>(url);
      return response.data;
    },
    enabled: !!metricCode,
  });
};

// ============================================================================
// BENCHMARKS
// ============================================================================

export const useBenchmarks = (benchmarkType?: string) => {
  return useQuery({
    queryKey: auditKeys.benchmarks(benchmarkType),
    queryFn: async () => {
      const url = benchmarkType ? `/audit/benchmarks?benchmark_type=${benchmarkType}` : '/audit/benchmarks';
      const response = await api.get<Benchmark[]>(url);
      return response.data;
    },
  });
};

export const useBenchmarkResults = (benchmarkId: string) => {
  return useQuery({
    queryKey: auditKeys.benchmarkResults(benchmarkId),
    queryFn: async () => {
      const response = await api.get<BenchmarkResult[]>(`/audit/benchmarks/${benchmarkId}/results`);
      return response.data;
    },
    enabled: !!benchmarkId,
  });
};

export const useRunBenchmark = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (benchmarkId: string) => {
      const response = await api.post<BenchmarkResult>(`/audit/benchmarks/${benchmarkId}/run`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit', 'benchmarks'] });
      queryClient.invalidateQueries({ queryKey: ['audit', 'benchmark-results'] });
    },
  });
};

// ============================================================================
// COMPLIANCE
// ============================================================================

export const useComplianceChecks = (framework?: string, status?: string) => {
  return useQuery({
    queryKey: auditKeys.complianceChecks(framework, status),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (framework) params.append('framework', framework);
      if (status) params.append('status', status);
      const url = `/audit/compliance/checks${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<ComplianceCheck[]>(url);
      return response.data;
    },
  });
};

export const useComplianceSummary = (framework?: string) => {
  return useQuery({
    queryKey: auditKeys.complianceSummary(framework),
    queryFn: async () => {
      const url = framework ? `/audit/compliance/summary?framework=${framework}` : '/audit/compliance/summary';
      const response = await api.get<ComplianceSummary>(url);
      return response.data;
    },
  });
};

// ============================================================================
// RETENTION & EXPORTS
// ============================================================================

export const useRetentionRules = () => {
  return useQuery({
    queryKey: auditKeys.retentionRules(),
    queryFn: async () => {
      const response = await api.get<RetentionRule[]>('/audit/retention/rules');
      return response.data;
    },
  });
};

export const useApplyRetentionRules = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post('/audit/retention/apply');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.retentionRules() });
    },
  });
};

export const useExports = () => {
  return useQuery({
    queryKey: auditKeys.exports(),
    queryFn: async () => {
      const response = await api.get<AuditExport[]>('/audit/exports');
      return response.data;
    },
  });
};

export const useCreateExport = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { export_type: string; format?: string; date_from?: string; date_to?: string }) => {
      const response = await api.post<AuditExport>('/audit/exports', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: auditKeys.exports() });
    },
  });
};
