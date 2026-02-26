/**
 * AZALSCORE - Types Module Audit & Benchmark
 * Types TypeScript correspondant exactement aux schemas backend
 * Conformite AZA-FE-META
 */

// ============================================================
// ENUMS - Correspondance exacte avec models.py
// ============================================================

export type AuditAction =
  | 'CREATE' | 'READ' | 'UPDATE' | 'DELETE'
  | 'LOGIN' | 'LOGOUT' | 'LOGIN_FAILED'
  | 'PASSWORD_CHANGE' | 'PASSWORD_RESET'
  | 'PERMISSION_GRANT' | 'PERMISSION_REVOKE'
  | 'EXPORT' | 'IMPORT'
  | 'APPROVE' | 'REJECT' | 'SUBMIT' | 'CANCEL'
  | 'ARCHIVE' | 'RESTORE'
  | 'SEND' | 'RECEIVE'
  | 'ERROR' | 'WARNING' | 'SYSTEM';

export const AUDIT_ACTION_LABELS: Record<AuditAction, string> = {
  CREATE: 'Creation',
  READ: 'Lecture',
  UPDATE: 'Modification',
  DELETE: 'Suppression',
  LOGIN: 'Connexion',
  LOGOUT: 'Deconnexion',
  LOGIN_FAILED: 'Echec connexion',
  PASSWORD_CHANGE: 'Changement MDP',
  PASSWORD_RESET: 'Reset MDP',
  PERMISSION_GRANT: 'Attribution droit',
  PERMISSION_REVOKE: 'Revocation droit',
  EXPORT: 'Export',
  IMPORT: 'Import',
  APPROVE: 'Approbation',
  REJECT: 'Rejet',
  SUBMIT: 'Soumission',
  CANCEL: 'Annulation',
  ARCHIVE: 'Archivage',
  RESTORE: 'Restauration',
  SEND: 'Envoi',
  RECEIVE: 'Reception',
  ERROR: 'Erreur',
  WARNING: 'Avertissement',
  SYSTEM: 'Systeme',
};

export type AuditLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

export const AUDIT_LEVEL_CONFIG: Record<AuditLevel, { label: string; color: string }> = {
  DEBUG: { label: 'Debug', color: 'gray' },
  INFO: { label: 'Info', color: 'blue' },
  WARNING: { label: 'Warning', color: 'orange' },
  ERROR: { label: 'Erreur', color: 'red' },
  CRITICAL: { label: 'Critique', color: 'red' },
};

export type AuditCategory = 'BUSINESS' | 'SECURITY' | 'SYSTEM' | 'COMPLIANCE' | 'ACCESS' | 'DATA';

export const AUDIT_CATEGORY_LABELS: Record<AuditCategory, string> = {
  BUSINESS: 'Metier',
  SECURITY: 'Securite',
  SYSTEM: 'Systeme',
  COMPLIANCE: 'Conformite',
  ACCESS: 'Acces',
  DATA: 'Donnees',
};

export type RetentionPolicy = 'SHORT' | 'MEDIUM' | 'LONG' | 'PERMANENT';

export const RETENTION_POLICY_CONFIG: Record<RetentionPolicy, { label: string; days: number | null }> = {
  SHORT: { label: 'Court (30j)', days: 30 },
  MEDIUM: { label: 'Moyen (1 an)', days: 365 },
  LONG: { label: 'Long (7 ans)', days: 2555 },
  PERMANENT: { label: 'Permanent', days: null },
};

export type MetricType = 'COUNTER' | 'GAUGE' | 'HISTOGRAM' | 'SUMMARY';

export const METRIC_TYPE_LABELS: Record<MetricType, string> = {
  COUNTER: 'Compteur',
  GAUGE: 'Jauge',
  HISTOGRAM: 'Histogramme',
  SUMMARY: 'Resume',
};

export type BenchmarkStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export const BENCHMARK_STATUS_CONFIG: Record<BenchmarkStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'gray' },
  RUNNING: { label: 'En cours', color: 'blue' },
  COMPLETED: { label: 'Termine', color: 'green' },
  FAILED: { label: 'Echoue', color: 'red' },
  CANCELLED: { label: 'Annule', color: 'gray' },
};

export type ComplianceFramework = 'RGPD' | 'ISO27001' | 'SOC2' | 'HIPAA' | 'PCI_DSS' | 'CUSTOM';

export const COMPLIANCE_FRAMEWORK_LABELS: Record<ComplianceFramework, string> = {
  RGPD: 'RGPD',
  ISO27001: 'ISO 27001',
  SOC2: 'SOC 2',
  HIPAA: 'HIPAA',
  PCI_DSS: 'PCI DSS',
  CUSTOM: 'Personnalise',
};

export type ComplianceStatus = 'PENDING' | 'COMPLIANT' | 'NON_COMPLIANT' | 'N/A';

export const COMPLIANCE_STATUS_CONFIG: Record<ComplianceStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'gray' },
  COMPLIANT: { label: 'Conforme', color: 'green' },
  NON_COMPLIANT: { label: 'Non conforme', color: 'red' },
  'N/A': { label: 'Non applicable', color: 'gray' },
};

// ============================================================
// TYPES PRINCIPAUX - AUDIT LOGS
// ============================================================

export interface AuditLog {
  id: string;
  tenant_id: string;

  action: AuditAction;
  level: AuditLevel;
  category: AuditCategory;

  module: string;
  entity_type: string | null;
  entity_id: string | null;

  user_id: string | null;
  user_email: string | null;
  user_role: string | null;

  session_id: string | null;
  request_id: string | null;
  ip_address: string | null;
  user_agent: string | null;

  description: string | null;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  diff: Record<string, unknown> | null;
  extra_data: Record<string, unknown> | null;

  success: boolean;
  error_message: string | null;
  error_code: string | null;

  duration_ms: number | null;

  retention_policy: RetentionPolicy | null;
  expires_at: string | null;

  created_at: string;
}

export interface AuditLogListResponse {
  logs: AuditLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuditLogFilters {
  action?: AuditAction;
  level?: AuditLevel;
  category?: AuditCategory;
  module?: string;
  entity_type?: string;
  entity_id?: string;
  user_id?: string;
  session_id?: string;
  success?: boolean;
  from_date?: string;
  to_date?: string;
  search_text?: string;
  page?: number;
  page_size?: number;
}

// ============================================================
// SESSIONS
// ============================================================

export interface AuditSession {
  id: string;
  tenant_id: string;
  session_id: string;
  user_id: string;
  user_email: string | null;

  login_at: string;
  logout_at: string | null;
  last_activity_at: string;

  ip_address: string | null;
  device_type: string | null;
  browser: string | null;
  os: string | null;
  country: string | null;
  city: string | null;

  actions_count: number;
  reads_count: number;
  writes_count: number;

  is_active: boolean;
  terminated_reason: string | null;
}

// ============================================================
// METRIQUES
// ============================================================

export interface Metric {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;

  metric_type: MetricType;
  unit: string | null;
  module: string | null;

  aggregation_period: string;
  retention_days: number;

  warning_threshold: number | null;
  critical_threshold: number | null;

  is_active: boolean;
  is_system: boolean;

  created_at: string;
}

export interface MetricCreateInput {
  code: string;
  name: string;
  description?: string;
  metric_type: MetricType;
  unit?: string;
  module?: string;
  aggregation_period?: string;
  retention_days?: number;
  warning_threshold?: number;
  critical_threshold?: number;
}

export interface MetricValue {
  id: string;
  metric_code: string;
  value: number;
  min_value: number | null;
  max_value: number | null;
  avg_value: number | null;
  count: number;
  period_start: string;
  period_end: string;
  dimensions: Record<string, unknown> | null;
}

export interface MetricValueInput {
  metric_code: string;
  value: number;
  dimensions?: Record<string, unknown>;
  timestamp?: string;
}

// ============================================================
// BENCHMARKS
// ============================================================

export interface Benchmark {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  version: string;

  benchmark_type: string;
  module: string | null;

  config: Record<string, unknown> | null;
  baseline: Record<string, unknown> | null;

  is_scheduled: boolean;
  schedule_cron: string | null;
  last_run_at: string | null;
  next_run_at: string | null;

  status: BenchmarkStatus;
  is_active: boolean;

  created_at: string;
  updated_at: string;
  created_by: string | null;
}

export interface BenchmarkCreateInput {
  code: string;
  name: string;
  description?: string;
  version?: string;
  benchmark_type: string;
  module?: string;
  config?: Record<string, unknown>;
  baseline?: Record<string, unknown>;
  is_scheduled?: boolean;
  schedule_cron?: string;
}

export interface BenchmarkResult {
  id: string;
  tenant_id: string;
  benchmark_id: string;

  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;

  status: BenchmarkStatus;
  score: number | null;
  passed: boolean | null;
  results: Record<string, unknown> | null;
  summary: string | null;

  previous_score: number | null;
  score_delta: number | null;
  trend: string | null;

  error_message: string | null;
  warnings: string[] | null;

  executed_by: string | null;
}

// ============================================================
// CONFORMITE
// ============================================================

export interface ComplianceCheck {
  id: string;
  tenant_id: string;

  framework: ComplianceFramework;
  control_id: string;
  control_name: string;
  control_description: string | null;

  category: string | null;
  subcategory: string | null;

  check_type: string;
  status: ComplianceStatus;
  last_checked_at: string | null;
  checked_by: string | null;

  actual_result: string | null;
  evidence: Record<string, unknown> | null;
  remediation: string | null;

  severity: string;
  due_date: string | null;

  is_active: boolean;

  created_at: string;
  updated_at: string;
}

export interface ComplianceCheckCreateInput {
  framework: ComplianceFramework;
  control_id: string;
  control_name: string;
  control_description?: string;
  category?: string;
  subcategory?: string;
  check_type: string;
  severity?: string;
  due_date?: string;
}

export interface ComplianceUpdateInput {
  status: ComplianceStatus;
  actual_result?: string;
  evidence?: Record<string, unknown>;
  remediation?: string;
}

export interface ComplianceSummary {
  total: number;
  compliant: number;
  non_compliant: number;
  pending: number;
  not_applicable: number;
  compliance_rate: number;
  by_severity: Record<string, Record<string, number>>;
  by_category: Record<string, Record<string, number>>;
}

// ============================================================
// RETENTION
// ============================================================

export interface RetentionRule {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;

  target_table: string;
  target_module: string | null;

  policy: RetentionPolicy;
  retention_days: number;

  condition: string | null;
  action: string;

  schedule_cron: string | null;
  last_run_at: string | null;
  next_run_at: string | null;
  last_affected_count: number;

  is_active: boolean;

  created_at: string;
  updated_at: string;
}

export interface RetentionRuleCreateInput {
  name: string;
  description?: string;
  target_table: string;
  target_module?: string;
  policy: RetentionPolicy;
  retention_days: number;
  condition?: string;
  action?: string;
  schedule_cron?: string;
}

// ============================================================
// EXPORTS
// ============================================================

export interface AuditExport {
  id: string;
  tenant_id: string;

  export_type: string;
  format: string;

  date_from: string | null;
  date_to: string | null;
  filters: Record<string, unknown> | null;

  status: string;
  progress: number;

  file_path: string | null;
  file_size: number | null;
  records_count: number | null;

  error_message: string | null;

  requested_by: string;
  requested_at: string;
  completed_at: string | null;

  expires_at: string | null;
}

export interface ExportCreateInput {
  export_type: string;
  format?: string;
  date_from?: string;
  date_to?: string;
  filters?: Record<string, unknown>;
}

// ============================================================
// DASHBOARDS
// ============================================================

export interface DashboardWidget {
  id: string;
  type: string;
  title: string;
  config: Record<string, unknown> | null;
  size: string;
}

export interface AuditDashboard {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;

  widgets: DashboardWidget[];
  layout: Record<string, unknown> | null;
  refresh_interval: number;

  is_public: boolean;
  owner_id: string;
  shared_with: string[] | null;

  is_default: boolean;
  is_active: boolean;

  created_at: string;
  updated_at: string;
}

export interface DashboardCreateInput {
  code: string;
  name: string;
  description?: string;
  widgets: DashboardWidget[];
  layout?: Record<string, unknown>;
  refresh_interval?: number;
  is_public?: boolean;
  is_default?: boolean;
}

// ============================================================
// STATISTIQUES
// ============================================================

export interface AuditStats {
  total_logs_24h: number;
  failed_24h: number;
  active_sessions: number;
  unique_users_24h: number;

  logs_by_action: Record<string, number> | null;
  logs_by_module: Record<string, number> | null;
  logs_by_level: Record<string, number> | null;
}

export interface AuditDashboardResponse {
  stats: AuditStats;
  recent_logs: AuditLog[];
  active_sessions: AuditSession[];
  compliance_summary: ComplianceSummary | null;
  latest_benchmarks: BenchmarkResult[] | null;
}
