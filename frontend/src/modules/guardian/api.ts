/**
 * AZALSCORE - Guardian API
 * ========================
 * Complete typed API client for Guardian (Auto-correction) module.
 * Covers: Error Detection, Correction Rules, Alerts, Statistics
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const guardianKeys = {
  all: ['guardian'] as const,
  errors: () => [...guardianKeys.all, 'errors'] as const,
  error: (id: string) => [...guardianKeys.errors(), id] as const,
  rules: () => [...guardianKeys.all, 'rules'] as const,
  rule: (id: string) => [...guardianKeys.rules(), id] as const,
  corrections: () => [...guardianKeys.all, 'corrections'] as const,
  alerts: () => [...guardianKeys.all, 'alerts'] as const,
  stats: () => [...guardianKeys.all, 'stats'] as const,
  dashboard: () => [...guardianKeys.all, 'dashboard'] as const,
  config: () => [...guardianKeys.all, 'config'] as const,
};

// ============================================================================
// TYPES - ERROR DETECTION
// ============================================================================

export type ErrorSeverity = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
export type ErrorType = 'VALIDATION' | 'BUSINESS' | 'TECHNICAL' | 'SECURITY' | 'PERFORMANCE';
export type Environment = 'development' | 'staging' | 'production';

export interface ErrorDetection {
  id: string;
  tenant_id: string;
  error_type: ErrorType;
  severity: ErrorSeverity;
  message: string;
  stack_trace?: string | null;
  context: Record<string, unknown>;
  source: string;
  environment: Environment;
  user_id?: string | null;
  session_id?: string | null;
  request_id?: string | null;
  url?: string | null;
  corrected: boolean;
  correction_id?: string | null;
  created_at: string;
}

export interface ErrorDetectionCreate {
  error_type: ErrorType;
  severity: ErrorSeverity;
  message: string;
  stack_trace?: string;
  context?: Record<string, unknown>;
  source: string;
  url?: string;
}

// ============================================================================
// TYPES - CORRECTION RULES
// ============================================================================

export type CorrectionStatus = 'PENDING' | 'APPLIED' | 'FAILED' | 'ROLLED_BACK';

export interface CorrectionRule {
  id: string;
  tenant_id: string;
  name: string;
  description: string;
  error_pattern: string;
  error_type: ErrorType;
  severity_threshold: ErrorSeverity;
  correction_action: string;
  auto_apply: boolean;
  requires_approval: boolean;
  max_retries: number;
  cooldown_seconds: number;
  is_active: boolean;
  success_count: number;
  failure_count: number;
  created_at: string;
  updated_at: string;
}

export interface CorrectionRuleCreate {
  name: string;
  description: string;
  error_pattern: string;
  error_type: ErrorType;
  severity_threshold?: ErrorSeverity;
  correction_action: string;
  auto_apply?: boolean;
  requires_approval?: boolean;
  max_retries?: number;
  cooldown_seconds?: number;
}

export interface CorrectionRuleUpdate {
  name?: string;
  description?: string;
  error_pattern?: string;
  correction_action?: string;
  auto_apply?: boolean;
  requires_approval?: boolean;
  is_active?: boolean;
}

// ============================================================================
// TYPES - CORRECTIONS
// ============================================================================

export interface CorrectionRegistry {
  id: string;
  tenant_id: string;
  error_id: string;
  rule_id?: string | null;
  status: CorrectionStatus;
  action_taken: string;
  action_details: Record<string, unknown>;
  before_state?: Record<string, unknown> | null;
  after_state?: Record<string, unknown> | null;
  retry_count: number;
  applied_at?: string | null;
  applied_by?: string | null;
  rolled_back_at?: string | null;
  rolled_back_by?: string | null;
  rollback_reason?: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - ALERTS
// ============================================================================

export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';

export interface GuardianAlert {
  id: string;
  tenant_id: string;
  title: string;
  message: string;
  severity: ErrorSeverity;
  status: AlertStatus;
  error_count: number;
  first_occurrence: string;
  last_occurrence: string;
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - STATISTICS & DASHBOARD
// ============================================================================

export interface GuardianStatistics {
  total_errors: number;
  errors_by_severity: Record<ErrorSeverity, number>;
  errors_by_type: Record<ErrorType, number>;
  corrections_applied: number;
  corrections_success_rate: number;
  active_alerts: number;
  avg_correction_time_ms: number;
  top_error_sources: { source: string; count: number }[];
}

export interface GuardianDashboard {
  stats: GuardianStatistics;
  recent_errors: ErrorDetection[];
  active_alerts: GuardianAlert[];
  recent_corrections: CorrectionRegistry[];
  health_score: number;
}

export interface GuardianConfig {
  auto_correction_enabled: boolean;
  max_auto_corrections_per_hour: number;
  alert_threshold: number;
  notification_channels: string[];
  ignored_patterns: string[];
  environments_enabled: Environment[];
}

// ============================================================================
// HOOKS - ERROR DETECTION
// ============================================================================

export function useErrors(filters?: {
  severity?: ErrorSeverity;
  error_type?: ErrorType;
  corrected?: boolean;
  from_date?: string;
  to_date?: string;
}) {
  return useQuery({
    queryKey: [...guardianKeys.errors(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.severity) params.append('severity', filters.severity);
      if (filters?.error_type) params.append('error_type', filters.error_type);
      if (filters?.corrected !== undefined) params.append('corrected', String(filters.corrected));
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const response = await api.get<{ items: ErrorDetection[]; total: number }>(
        `/guardian/errors${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useError(id: string) {
  return useQuery({
    queryKey: guardianKeys.error(id),
    queryFn: async () => {
      const response = await api.get<ErrorDetection>(`/guardian/errors/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useReportError() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ErrorDetectionCreate) => {
      return api.post<ErrorDetection>('/guardian/errors', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guardianKeys.errors() });
      queryClient.invalidateQueries({ queryKey: guardianKeys.stats() });
    },
  });
}

// ============================================================================
// HOOKS - CORRECTION RULES
// ============================================================================

export function useCorrectionRules(filters?: { is_active?: boolean; error_type?: ErrorType }) {
  return useQuery({
    queryKey: [...guardianKeys.rules(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters?.error_type) params.append('error_type', filters.error_type);
      const queryString = params.toString();
      const response = await api.get<{ items: CorrectionRule[]; total: number }>(
        `/guardian/rules${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCorrectionRule(id: string) {
  return useQuery({
    queryKey: guardianKeys.rule(id),
    queryFn: async () => {
      const response = await api.get<CorrectionRule>(`/guardian/rules/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateCorrectionRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CorrectionRuleCreate) => {
      return api.post<CorrectionRule>('/guardian/rules', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guardianKeys.rules() });
    },
  });
}

export function useUpdateCorrectionRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: CorrectionRuleUpdate }) => {
      return api.put<CorrectionRule>(`/guardian/rules/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: guardianKeys.rules() });
      queryClient.invalidateQueries({ queryKey: guardianKeys.rule(id) });
    },
  });
}

export function useDeleteCorrectionRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/guardian/rules/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guardianKeys.rules() });
    },
  });
}

export function useTestCorrectionRule() {
  return useMutation({
    mutationFn: async ({ id, testData }: { id: string; testData: Record<string, unknown> }) => {
      return api.post<{ success: boolean; result: Record<string, unknown> }>(
        `/guardian/rules/${id}/test`,
        testData
      );
    },
  });
}

// ============================================================================
// HOOKS - CORRECTIONS
// ============================================================================

export function useCorrections(filters?: { status?: CorrectionStatus }) {
  return useQuery({
    queryKey: [...guardianKeys.corrections(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const response = await api.get<{ items: CorrectionRegistry[]; total: number }>(
        `/guardian/corrections${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useApplyCorrection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ errorId, ruleId }: { errorId: string; ruleId?: string }) => {
      return api.post<CorrectionRegistry>('/guardian/corrections/apply', {
        error_id: errorId,
        rule_id: ruleId,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guardianKeys.corrections() });
      queryClient.invalidateQueries({ queryKey: guardianKeys.errors() });
      queryClient.invalidateQueries({ queryKey: guardianKeys.stats() });
    },
  });
}

export function useRollbackCorrection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.post(`/guardian/corrections/${id}/rollback`, { reason });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guardianKeys.corrections() });
      queryClient.invalidateQueries({ queryKey: guardianKeys.errors() });
    },
  });
}

// ============================================================================
// HOOKS - ALERTS
// ============================================================================

export function useGuardianAlerts(filters?: { status?: AlertStatus; severity?: ErrorSeverity }) {
  return useQuery({
    queryKey: [...guardianKeys.alerts(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.severity) params.append('severity', filters.severity);
      const queryString = params.toString();
      const response = await api.get<{ items: GuardianAlert[]; total: number }>(
        `/guardian/alerts${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/guardian/alerts/${id}/acknowledge`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guardianKeys.alerts() });
    },
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, resolution }: { id: string; resolution?: string }) => {
      return api.post(`/guardian/alerts/${id}/resolve`, { resolution });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guardianKeys.alerts() });
    },
  });
}

// ============================================================================
// HOOKS - STATISTICS & DASHBOARD
// ============================================================================

export function useGuardianStats() {
  return useQuery({
    queryKey: guardianKeys.stats(),
    queryFn: async () => {
      const response = await api.get<GuardianStatistics>('/guardian/stats');
      return response;
    },
  });
}

export function useGuardianDashboard() {
  return useQuery({
    queryKey: guardianKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<GuardianDashboard>('/guardian/dashboard');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - CONFIG
// ============================================================================

export function useGuardianConfig() {
  return useQuery({
    queryKey: guardianKeys.config(),
    queryFn: async () => {
      const response = await api.get<GuardianConfig>('/guardian/config');
      return response;
    },
  });
}

export function useUpdateGuardianConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<GuardianConfig>) => {
      return api.put<GuardianConfig>('/guardian/config', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: guardianKeys.config() });
    },
  });
}
