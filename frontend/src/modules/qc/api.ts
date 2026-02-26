/**
 * AZALSCORE - QC (Quality Control) API
 * =====================================
 * Complete typed API client for Quality Control module.
 * Covers: QC Rules, Checks, Module Status, Test Results, Reports
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const qcKeys = {
  all: ['qc'] as const,
  rules: () => [...qcKeys.all, 'rules'] as const,
  rule: (id: string) => [...qcKeys.rules(), id] as const,
  checks: () => [...qcKeys.all, 'checks'] as const,
  check: (id: string) => [...qcKeys.checks(), id] as const,
  modules: () => [...qcKeys.all, 'modules'] as const,
  module: (code: string) => [...qcKeys.modules(), code] as const,
  testResults: () => [...qcKeys.all, 'test-results'] as const,
  reports: () => [...qcKeys.all, 'reports'] as const,
  dashboard: () => [...qcKeys.all, 'dashboard'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type QCRuleCategory =
  | 'ARCHITECTURE' | 'SECURITY' | 'PERFORMANCE' | 'CODE_QUALITY'
  | 'TESTING' | 'DOCUMENTATION' | 'API' | 'DATABASE'
  | 'INTEGRATION' | 'COMPLIANCE';

export type QCRuleSeverity = 'INFO' | 'WARNING' | 'CRITICAL' | 'BLOCKER';

export type QCCheckStatus =
  | 'PENDING' | 'RUNNING' | 'PASSED' | 'FAILED' | 'SKIPPED' | 'ERROR';

export type ModuleStatus =
  | 'DRAFT' | 'IN_DEVELOPMENT' | 'READY_FOR_QC' | 'QC_IN_PROGRESS'
  | 'QC_PASSED' | 'QC_FAILED' | 'PRODUCTION' | 'DEPRECATED';

export type QCTestType =
  | 'UNIT' | 'INTEGRATION' | 'E2E' | 'PERFORMANCE' | 'SECURITY' | 'REGRESSION';

export type ValidationPhase =
  | 'PRE_QC' | 'AUTOMATED' | 'MANUAL' | 'FINAL' | 'POST_DEPLOY';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface QCRule {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  category: QCRuleCategory;
  severity: QCRuleSeverity;
  check_type: string;
  applies_to_modules?: string[] | null;
  applies_to_phases?: ValidationPhase[] | null;
  check_config?: Record<string, unknown> | null;
  threshold_value?: number | null;
  auto_fix_available: boolean;
  is_active: boolean;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface QCCheck {
  id: string;
  tenant_id: string;
  module_code: string;
  rule_id: string;
  rule_code: string;
  rule_name: string;
  category: QCRuleCategory;
  severity: QCRuleSeverity;
  status: QCCheckStatus;
  phase: ValidationPhase;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
  result_details?: Record<string, unknown> | null;
  error_message?: string | null;
  auto_fixed: boolean;
  fix_details?: string | null;
  run_by?: string | null;
  created_at: string;
}

export interface QCModule {
  id: string;
  tenant_id: string;
  module_code: string;
  module_name: string;
  version: string;
  status: ModuleStatus;
  last_qc_at?: string | null;
  last_qc_by?: string | null;
  qc_score?: number | null;
  checks_total: number;
  checks_passed: number;
  checks_failed: number;
  checks_skipped: number;
  blockers_count: number;
  criticals_count: number;
  warnings_count: number;
  current_phase?: ValidationPhase | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface QCTestResult {
  id: string;
  tenant_id: string;
  module_code: string;
  test_type: QCTestType;
  test_suite: string;
  test_name: string;
  status: 'passed' | 'failed' | 'skipped' | 'error';
  duration_ms: number;
  error_message?: string | null;
  stack_trace?: string | null;
  assertions_passed: number;
  assertions_failed: number;
  coverage_percent?: number | null;
  run_at: string;
  run_by?: string | null;
}

export interface QCReport {
  id: string;
  tenant_id: string;
  module_code: string;
  report_type: 'full' | 'summary' | 'delta';
  phase: ValidationPhase;
  generated_at: string;
  generated_by: string;
  status: 'pending' | 'generating' | 'ready' | 'failed';
  file_path?: string | null;
  summary: {
    total_checks: number;
    passed: number;
    failed: number;
    skipped: number;
    score: number;
    blockers: number;
    criticals: number;
    recommendations: string[];
  };
}

export interface QCDashboard {
  modules_total: number;
  modules_in_qc: number;
  modules_passed: number;
  modules_failed: number;
  overall_score: number;
  checks_today: number;
  blockers_open: number;
  recent_checks: QCCheck[];
  modules_needing_attention: QCModule[];
  score_trend: Array<{ date: string; score: number }>;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface QCRuleCreate {
  code: string;
  name: string;
  description?: string;
  category: QCRuleCategory;
  severity?: QCRuleSeverity;
  check_type: string;
  applies_to_modules?: string[];
  applies_to_phases?: ValidationPhase[];
  check_config?: Record<string, unknown>;
  threshold_value?: number;
  auto_fix_available?: boolean;
}

export interface QCRuleUpdate {
  name?: string;
  description?: string;
  category?: QCRuleCategory;
  severity?: QCRuleSeverity;
  check_config?: Record<string, unknown>;
  threshold_value?: number;
  auto_fix_available?: boolean;
  is_active?: boolean;
}

// ============================================================================
// HOOKS - QC RULES
// ============================================================================

export function useQCRules(filters?: {
  category?: QCRuleCategory;
  severity?: QCRuleSeverity;
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: [...qcKeys.rules(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.category) params.append('category', filters.category);
      if (filters?.severity) params.append('severity', filters.severity);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: QCRule[] }>(
        `/qc/rules${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useQCRule(id: string) {
  return useQuery({
    queryKey: qcKeys.rule(id),
    queryFn: async () => {
      const response = await api.get<QCRule>(`/qc/rules/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateQCRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: QCRuleCreate) => {
      return api.post<QCRule>('/qc/rules', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qcKeys.rules() });
    },
  });
}

export function useUpdateQCRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: QCRuleUpdate }) => {
      return api.put<QCRule>(`/qc/rules/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: qcKeys.rules() });
      queryClient.invalidateQueries({ queryKey: qcKeys.rule(id) });
    },
  });
}

export function useDeleteQCRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/qc/rules/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qcKeys.rules() });
    },
  });
}

// ============================================================================
// HOOKS - QC CHECKS
// ============================================================================

export function useQCChecks(filters?: {
  module_code?: string;
  category?: QCRuleCategory;
  severity?: QCRuleSeverity;
  status?: QCCheckStatus;
  phase?: ValidationPhase;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...qcKeys.checks(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.module_code) params.append('module_code', filters.module_code);
      if (filters?.category) params.append('category', filters.category);
      if (filters?.severity) params.append('severity', filters.severity);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.phase) params.append('phase', filters.phase);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: QCCheck[]; total: number }>(
        `/qc/checks${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useQCCheck(id: string) {
  return useQuery({
    queryKey: qcKeys.check(id),
    queryFn: async () => {
      const response = await api.get<QCCheck>(`/qc/checks/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useRunQCCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      module_code: string;
      rule_ids?: string[];
      phase?: ValidationPhase;
      auto_fix?: boolean;
    }) => {
      return api.post<{ job_id: string; checks_queued: number }>('/qc/checks/run', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qcKeys.checks() });
      queryClient.invalidateQueries({ queryKey: qcKeys.modules() });
    },
  });
}

export function useRetryQCCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/qc/checks/${id}/retry`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qcKeys.checks() });
    },
  });
}

export function useApplyAutoFix() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<{ success: boolean; fix_details: string }>(`/qc/checks/${id}/auto-fix`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qcKeys.checks() });
    },
  });
}

// ============================================================================
// HOOKS - QC MODULES
// ============================================================================

export function useQCModules(filters?: { status?: ModuleStatus }) {
  return useQuery({
    queryKey: [...qcKeys.modules(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const response = await api.get<{ items: QCModule[] }>(
        `/qc/modules${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useQCModule(code: string) {
  return useQuery({
    queryKey: qcKeys.module(code),
    queryFn: async () => {
      const response = await api.get<QCModule>(`/qc/modules/${code}`);
      return response;
    },
    enabled: !!code,
  });
}

export function useUpdateModuleStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      code,
      status,
      notes,
    }: {
      code: string;
      status: ModuleStatus;
      notes?: string;
    }) => {
      return api.post(`/qc/modules/${code}/status`, { status, notes });
    },
    onSuccess: (_, { code }) => {
      queryClient.invalidateQueries({ queryKey: qcKeys.modules() });
      queryClient.invalidateQueries({ queryKey: qcKeys.module(code) });
    },
  });
}

export function useStartQCPhase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ code, phase }: { code: string; phase: ValidationPhase }) => {
      return api.post(`/qc/modules/${code}/start-phase`, { phase });
    },
    onSuccess: (_, { code }) => {
      queryClient.invalidateQueries({ queryKey: qcKeys.modules() });
      queryClient.invalidateQueries({ queryKey: qcKeys.module(code) });
    },
  });
}

export function useApproveModule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ code, notes }: { code: string; notes?: string }) => {
      return api.post(`/qc/modules/${code}/approve`, { notes });
    },
    onSuccess: (_, { code }) => {
      queryClient.invalidateQueries({ queryKey: qcKeys.modules() });
      queryClient.invalidateQueries({ queryKey: qcKeys.module(code) });
    },
  });
}

export function useRejectModule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ code, reason }: { code: string; reason: string }) => {
      return api.post(`/qc/modules/${code}/reject`, { reason });
    },
    onSuccess: (_, { code }) => {
      queryClient.invalidateQueries({ queryKey: qcKeys.modules() });
      queryClient.invalidateQueries({ queryKey: qcKeys.module(code) });
    },
  });
}

// ============================================================================
// HOOKS - TEST RESULTS
// ============================================================================

export function useQCTestResults(filters?: {
  module_code?: string;
  test_type?: QCTestType;
  status?: string;
  from_date?: string;
  to_date?: string;
}) {
  return useQuery({
    queryKey: [...qcKeys.testResults(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.module_code) params.append('module_code', filters.module_code);
      if (filters?.test_type) params.append('test_type', filters.test_type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const response = await api.get<{ items: QCTestResult[] }>(
        `/qc/test-results${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useRunTests() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      module_code: string;
      test_types?: QCTestType[];
      test_suites?: string[];
    }) => {
      return api.post<{ job_id: string }>('/qc/test-results/run', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qcKeys.testResults() });
    },
  });
}

// ============================================================================
// HOOKS - REPORTS
// ============================================================================

export function useQCReports(filters?: { module_code?: string; report_type?: string }) {
  return useQuery({
    queryKey: [...qcKeys.reports(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.module_code) params.append('module_code', filters.module_code);
      if (filters?.report_type) params.append('report_type', filters.report_type);
      const queryString = params.toString();
      const response = await api.get<{ items: QCReport[] }>(
        `/qc/reports${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useGenerateQCReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      module_code: string;
      report_type: 'full' | 'summary' | 'delta';
      phase?: ValidationPhase;
    }) => {
      return api.post<QCReport>('/qc/reports/generate', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: qcKeys.reports() });
    },
  });
}

export function useDownloadQCReport() {
  return useMutation({
    mutationFn: async (id: string) => {
      return api.get<Blob>(`/qc/reports/${id}/download`, { responseType: 'blob' });
    },
  });
}

// ============================================================================
// HOOKS - DASHBOARD
// ============================================================================

export function useQCDashboard() {
  return useQuery({
    queryKey: qcKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<QCDashboard>('/qc/dashboard');
      return response;
    },
  });
}
