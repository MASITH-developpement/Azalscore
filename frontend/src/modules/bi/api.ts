/**
 * AZALSCORE - BI (Business Intelligence) API
 * ==========================================
 * Client API typé pour les tableaux de bord, rapports, KPIs et alertes
 */

import { api } from '@core/api-client';

// ============================================================================
// HELPERS
// ============================================================================

function buildQueryString(params: Record<string, string | number | boolean | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// ENUMS
// ============================================================================

export type DashboardType = 'EXECUTIVE' | 'OPERATIONAL' | 'ANALYTICAL' | 'CUSTOM';
export type WidgetType = 'CHART' | 'KPI' | 'TABLE' | 'TEXT' | 'IMAGE' | 'MAP' | 'CUSTOM';
export type ChartType = 'LINE' | 'BAR' | 'PIE' | 'DONUT' | 'AREA' | 'SCATTER' | 'RADAR' | 'GAUGE' | 'FUNNEL' | 'HEATMAP';
export type RefreshFrequency = 'ON_DEMAND' | 'REALTIME' | 'MINUTE' | 'HOURLY' | 'DAILY' | 'WEEKLY' | 'MONTHLY';
export type ReportType = 'STANDARD' | 'AD_HOC' | 'SCHEDULED' | 'TEMPLATE';
export type ReportFormat = 'PDF' | 'EXCEL' | 'CSV' | 'HTML' | 'JSON';
export type ReportStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
export type KPICategory = 'FINANCIAL' | 'OPERATIONAL' | 'CUSTOMER' | 'HR' | 'SALES' | 'MARKETING' | 'QUALITY' | 'CUSTOM';
export type KPITrend = 'UP' | 'DOWN' | 'STABLE';
export type AlertSeverity = 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'SNOOZED';
export type DataSourceType = 'DATABASE' | 'API' | 'FILE' | 'INTERNAL';

// ============================================================================
// TYPES - DASHBOARDS
// ============================================================================

export interface DashboardCreate {
  code: string;
  name: string;
  description?: string | null;
  dashboard_type?: DashboardType;
  layout?: Record<string, unknown> | null;
  theme?: string;
  refresh_frequency?: RefreshFrequency;
  auto_refresh?: boolean;
  global_filters?: Record<string, unknown> | null;
  default_date_range?: string | null;
  is_shared?: boolean;
  shared_with?: number[] | null;
  is_default?: boolean;
  is_public?: boolean;
}

export interface DashboardUpdate {
  name?: string;
  description?: string | null;
  dashboard_type?: DashboardType;
  layout?: Record<string, unknown> | null;
  theme?: string;
  refresh_frequency?: RefreshFrequency;
  auto_refresh?: boolean;
  global_filters?: Record<string, unknown> | null;
  default_date_range?: string | null;
  is_shared?: boolean;
  shared_with?: number[] | null;
  is_default?: boolean;
  is_public?: boolean;
  is_active?: boolean;
}

export interface Dashboard {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  dashboard_type: DashboardType;
  owner_id: number;
  layout: Record<string, unknown> | null;
  theme: string;
  refresh_frequency: RefreshFrequency;
  auto_refresh: boolean;
  global_filters: Record<string, unknown> | null;
  default_date_range: string | null;
  is_shared: boolean;
  shared_with: number[] | null;
  is_default: boolean;
  is_public: boolean;
  view_count: number;
  last_viewed_at: string | null;
  is_active: boolean;
  widgets: Widget[];
  created_at: string;
  updated_at: string;
  created_by: number | null;
}

export interface DashboardList {
  id: number;
  code: string;
  name: string;
  description: string | null;
  dashboard_type: DashboardType;
  owner_id: number;
  is_shared: boolean;
  is_public: boolean;
  view_count: number;
  widget_count: number;
  created_at: string;
}

export interface DashboardStats {
  dashboard_id: number;
  dashboard_name: string;
  widget_count: number;
  view_count: number;
  last_viewed_at: string | null;
  avg_load_time_ms: number | null;
  active_users: number;
}

// ============================================================================
// TYPES - WIDGETS
// ============================================================================

export interface WidgetFilter {
  id: number;
  widget_id: number;
  field_name: string;
  operator: string;
  value: unknown | null;
  is_dynamic: boolean;
}

export interface WidgetFilterCreate {
  field_name: string;
  operator: string;
  value?: unknown | null;
  is_dynamic?: boolean;
}

export interface WidgetCreate {
  title: string;
  widget_type: WidgetType;
  chart_type?: ChartType | null;
  position_x?: number;
  position_y?: number;
  width?: number;
  height?: number;
  config?: Record<string, unknown> | null;
  chart_options?: Record<string, unknown> | null;
  colors?: string[] | null;
  static_data?: unknown | null;
  data_mapping?: Record<string, string> | null;
  drill_down_config?: Record<string, unknown> | null;
  click_action?: Record<string, unknown> | null;
  show_title?: boolean;
  show_legend?: boolean;
  show_toolbar?: boolean;
  data_source_id?: number | null;
  query_id?: number | null;
  kpi_id?: number | null;
  filters?: WidgetFilterCreate[] | null;
}

export interface WidgetUpdate {
  title?: string;
  widget_type?: WidgetType;
  chart_type?: ChartType | null;
  position_x?: number;
  position_y?: number;
  width?: number;
  height?: number;
  data_source_id?: number | null;
  query_id?: number | null;
  kpi_id?: number | null;
  config?: Record<string, unknown> | null;
  chart_options?: Record<string, unknown> | null;
  colors?: string[] | null;
  static_data?: unknown | null;
  data_mapping?: Record<string, string> | null;
  show_title?: boolean;
  show_legend?: boolean;
  show_toolbar?: boolean;
  is_active?: boolean;
}

export interface Widget {
  id: number;
  dashboard_id: number;
  title: string;
  widget_type: WidgetType;
  chart_type: ChartType | null;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  data_source_id: number | null;
  query_id: number | null;
  kpi_id: number | null;
  config: Record<string, unknown> | null;
  chart_options: Record<string, unknown> | null;
  colors: string[] | null;
  static_data: unknown | null;
  data_mapping: Record<string, string> | null;
  drill_down_config: Record<string, unknown> | null;
  click_action: Record<string, unknown> | null;
  show_title: boolean;
  show_legend: boolean;
  show_toolbar: boolean;
  is_active: boolean;
  display_order: number;
  filters: WidgetFilter[];
  created_at: string;
  updated_at: string;
}

export interface WidgetPosition {
  widget_id: number;
  position_x: number;
  position_y: number;
  width?: number;
  height?: number;
}

// ============================================================================
// TYPES - REPORTS
// ============================================================================

export interface ReportScheduleCreate {
  name: string;
  cron_expression?: string | null;
  frequency?: RefreshFrequency | null;
  parameters?: Record<string, unknown> | null;
  output_format?: ReportFormat;
  recipients?: string[] | null;
  distribution_method?: string;
  timezone?: string;
  is_enabled?: boolean;
}

export interface ReportSchedule {
  id: number;
  report_id: number;
  name: string;
  cron_expression: string | null;
  frequency: RefreshFrequency | null;
  parameters: Record<string, unknown> | null;
  output_format: ReportFormat;
  recipients: string[] | null;
  distribution_method: string;
  timezone: string;
  next_run_at: string | null;
  last_run_at: string | null;
  last_status: ReportStatus | null;
  is_enabled: boolean;
  created_at: string;
}

export interface ReportCreate {
  code: string;
  name: string;
  description?: string | null;
  report_type: ReportType;
  template?: string | null;
  template_file?: string | null;
  data_sources?: Record<string, unknown>[] | null;
  queries?: Record<string, unknown>[] | null;
  parameters?: Record<string, unknown> | null;
  available_formats?: string[];
  default_format?: ReportFormat;
  page_size?: string;
  orientation?: string;
  is_public?: boolean;
  allowed_roles?: string[] | null;
}

export interface ReportUpdate {
  name?: string;
  description?: string | null;
  report_type?: ReportType;
  template?: string | null;
  template_file?: string | null;
  data_sources?: Record<string, unknown>[] | null;
  queries?: Record<string, unknown>[] | null;
  parameters?: Record<string, unknown> | null;
  available_formats?: string[];
  default_format?: ReportFormat;
  page_size?: string;
  orientation?: string;
  is_public?: boolean;
  allowed_roles?: string[] | null;
  is_active?: boolean;
}

export interface Report {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  report_type: ReportType;
  owner_id: number;
  template: string | null;
  template_file: string | null;
  data_sources: Record<string, unknown>[] | null;
  queries: Record<string, unknown>[] | null;
  parameters: Record<string, unknown> | null;
  available_formats: string[];
  default_format: ReportFormat;
  page_size: string;
  orientation: string;
  is_public: boolean;
  allowed_roles: string[] | null;
  is_active: boolean;
  version: number;
  schedules: ReportSchedule[];
  created_at: string;
  updated_at: string;
  created_by: number | null;
}

export interface ReportList {
  id: number;
  code: string;
  name: string;
  description: string | null;
  report_type: ReportType;
  owner_id: number;
  is_public: boolean;
  available_formats: string[];
  schedule_count: number;
  created_at: string;
}

export interface ReportExecuteRequest {
  output_format?: ReportFormat;
  parameters?: Record<string, unknown> | null;
  async_execution?: boolean;
}

export interface ReportExecution {
  id: number;
  report_id: number;
  schedule_id: number | null;
  status: ReportStatus;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  parameters: Record<string, unknown> | null;
  output_format: ReportFormat;
  file_path: string | null;
  file_size: number | null;
  file_url: string | null;
  row_count: number | null;
  error_message: string | null;
  triggered_by: number | null;
  created_at: string;
}

// ============================================================================
// TYPES - KPIs
// ============================================================================

export interface KPITargetCreate {
  year: number;
  month?: number | null;
  quarter?: number | null;
  target_value: number;
  min_value?: number | null;
  max_value?: number | null;
  notes?: string | null;
}

export interface KPITarget {
  id: number;
  kpi_id: number;
  year: number;
  month: number | null;
  quarter: number | null;
  target_value: number;
  min_value: number | null;
  max_value: number | null;
  notes: string | null;
  current_value: number | null;
  achievement_percentage: number | null;
  created_at: string;
}

export interface KPIValueCreate {
  period_date: string;
  period_type?: string;
  value: number;
  dimension?: string | null;
  dimension_value?: string | null;
  extra_data?: Record<string, unknown> | null;
  source?: string;
}

export interface KPIValue {
  id: number;
  kpi_id: number;
  period_date: string;
  period_type: string;
  value: number;
  dimension: string | null;
  dimension_value: string | null;
  extra_data: Record<string, unknown> | null;
  previous_value: number | null;
  change_percentage: number | null;
  trend: KPITrend;
  source: string;
  calculated_at: string;
}

export interface KPICreate {
  code: string;
  name: string;
  description?: string | null;
  category: KPICategory;
  formula?: string | null;
  unit?: string | null;
  precision?: number;
  aggregation_method?: string;
  display_format?: string | null;
  good_threshold?: number | null;
  warning_threshold?: number | null;
  bad_threshold?: number | null;
  higher_is_better?: boolean;
  refresh_frequency?: RefreshFrequency;
  compare_to_previous?: boolean;
  comparison_period?: string;
  data_source_id?: number | null;
  query?: string | null;
}

export interface KPIUpdate {
  name?: string;
  description?: string | null;
  category?: KPICategory;
  formula?: string | null;
  unit?: string | null;
  precision?: number;
  aggregation_method?: string;
  data_source_id?: number | null;
  query?: string | null;
  display_format?: string | null;
  good_threshold?: number | null;
  warning_threshold?: number | null;
  bad_threshold?: number | null;
  higher_is_better?: boolean;
  refresh_frequency?: RefreshFrequency;
  compare_to_previous?: boolean;
  comparison_period?: string;
  is_active?: boolean;
}

export interface KPI {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  category: KPICategory;
  formula: string | null;
  unit: string | null;
  precision: number;
  aggregation_method: string;
  display_format: string | null;
  good_threshold: number | null;
  warning_threshold: number | null;
  bad_threshold: number | null;
  higher_is_better: boolean;
  refresh_frequency: RefreshFrequency;
  compare_to_previous: boolean;
  comparison_period: string;
  data_source_id: number | null;
  query: string | null;
  last_calculated_at: string | null;
  is_active: boolean;
  is_system: boolean;
  created_at: string;
  updated_at: string;
  created_by: number | null;
  current_value: number | null;
  previous_value: number | null;
  change_percentage: number | null;
  trend: KPITrend | null;
  target: KPITarget | null;
}

export interface KPIList {
  id: number;
  code: string;
  name: string;
  category: KPICategory;
  unit: string | null;
  current_value: number | null;
  change_percentage: number | null;
  trend: KPITrend | null;
  is_active: boolean;
}

// ============================================================================
// TYPES - ALERTS
// ============================================================================

export interface AlertRuleCreate {
  code: string;
  name: string;
  description?: string | null;
  severity: AlertSeverity;
  source_type: string;
  source_id?: number | null;
  condition: Record<string, unknown>;
  check_frequency?: RefreshFrequency;
  notification_channels?: string[] | null;
  recipients?: string[] | null;
  cooldown_minutes?: number;
  auto_resolve?: boolean;
  is_enabled?: boolean;
}

export interface AlertRuleUpdate {
  name?: string;
  description?: string | null;
  severity?: AlertSeverity;
  source_type?: string;
  source_id?: number | null;
  condition?: Record<string, unknown>;
  check_frequency?: RefreshFrequency;
  notification_channels?: string[] | null;
  recipients?: string[] | null;
  cooldown_minutes?: number;
  auto_resolve?: boolean;
  is_enabled?: boolean;
}

export interface AlertRule {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  severity: AlertSeverity;
  source_type: string;
  source_id: number | null;
  condition: Record<string, unknown>;
  check_frequency: RefreshFrequency;
  notification_channels: string[] | null;
  recipients: string[] | null;
  cooldown_minutes: number;
  auto_resolve: boolean;
  is_enabled: boolean;
  last_checked_at: string | null;
  last_triggered_at: string | null;
  created_at: string;
  created_by: number | null;
}

export interface Alert {
  id: number;
  tenant_id: string;
  rule_id: number | null;
  title: string;
  message: string;
  severity: AlertSeverity;
  status: AlertStatus;
  source_type: string | null;
  source_id: number | null;
  source_value: number | null;
  threshold_value: number | null;
  context: Record<string, unknown> | null;
  link: string | null;
  acknowledged_at: string | null;
  acknowledged_by: number | null;
  resolved_at: string | null;
  resolved_by: number | null;
  resolution_notes: string | null;
  snoozed_until: string | null;
  notifications_sent: Record<string, unknown> | null;
  triggered_at: string;
  created_at: string;
}

export interface AlertList {
  id: number;
  title: string;
  severity: AlertSeverity;
  status: AlertStatus;
  source_type: string | null;
  triggered_at: string;
}

export interface AlertAcknowledge {
  notes?: string | null;
}

export interface AlertResolve {
  resolution_notes: string;
}

export interface AlertSnooze {
  snooze_until: string;
}

// ============================================================================
// TYPES - DATA SOURCES
// ============================================================================

export interface DataSourceCreate {
  code: string;
  name: string;
  description?: string | null;
  source_type: DataSourceType;
  connection_config?: Record<string, unknown> | null;
  schema_definition?: Record<string, unknown> | null;
  refresh_frequency?: RefreshFrequency;
  cache_enabled?: boolean;
  cache_ttl_seconds?: number;
  is_encrypted?: boolean;
  allowed_roles?: string[] | null;
}

export interface DataSourceUpdate {
  name?: string;
  description?: string | null;
  connection_config?: Record<string, unknown> | null;
  schema_definition?: Record<string, unknown> | null;
  refresh_frequency?: RefreshFrequency;
  cache_enabled?: boolean;
  cache_ttl_seconds?: number;
  allowed_roles?: string[] | null;
  is_active?: boolean;
}

export interface DataSource {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  source_type: DataSourceType;
  connection_config: Record<string, unknown> | null;
  schema_definition: Record<string, unknown> | null;
  refresh_frequency: RefreshFrequency;
  cache_enabled: boolean;
  cache_ttl_seconds: number;
  is_encrypted: boolean;
  allowed_roles: string[] | null;
  is_active: boolean;
  is_system: boolean;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
  created_by: number | null;
}

// ============================================================================
// TYPES - DATA QUERIES
// ============================================================================

export interface DataQueryCreate {
  code: string;
  name: string;
  description?: string | null;
  query_type?: string;
  query_text?: string | null;
  parameters?: Record<string, unknown> | null;
  result_columns?: Array<Record<string, string>> | null;
  cache_enabled?: boolean;
  cache_ttl_seconds?: number;
  data_source_id?: number | null;
}

export interface DataQuery {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  data_source_id: number | null;
  query_type: string;
  query_text: string | null;
  parameters: Record<string, unknown> | null;
  result_columns: Array<Record<string, string>> | null;
  cache_enabled: boolean;
  cache_ttl_seconds: number;
  sample_data: unknown | null;
  last_executed_at: string | null;
  last_execution_time_ms: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: number | null;
}

// ============================================================================
// TYPES - BOOKMARKS
// ============================================================================

export interface BookmarkCreate {
  item_type: string;
  item_id: number;
  item_name?: string | null;
  folder?: string | null;
}

export interface Bookmark {
  id: number;
  user_id: number;
  item_type: string;
  item_id: number;
  item_name: string | null;
  folder: string | null;
  display_order: number;
  created_at: string;
}

// ============================================================================
// TYPES - EXPORTS
// ============================================================================

export interface ExportRequest {
  export_type: string;
  item_type?: string | null;
  item_id?: number | null;
  format: ReportFormat;
  parameters?: Record<string, unknown> | null;
  filename?: string | null;
}

export interface Export {
  id: number;
  export_type: string;
  item_type: string | null;
  item_id: number | null;
  item_name: string | null;
  format: ReportFormat;
  file_name: string | null;
  file_url: string | null;
  file_size: number | null;
  status: ReportStatus;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

// ============================================================================
// TYPES - OVERVIEW
// ============================================================================

export interface AlertSummary {
  total: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  recent: AlertList[];
}

export interface BIOverview {
  dashboards: Record<string, unknown>;
  reports: Record<string, unknown>;
  kpis: Record<string, unknown>;
  alerts: AlertSummary;
  exports: Record<string, unknown>;
  data_sources: Record<string, unknown>;
}

// ============================================================================
// API CLIENT
// ============================================================================

const BASE_PATH = '/v1/bi';

export const biApi = {
  // --------------------------------------------------------------------------
  // Overview
  // --------------------------------------------------------------------------
  getOverview: () =>
    api.get<BIOverview>(`${BASE_PATH}/overview`),

  // --------------------------------------------------------------------------
  // Dashboards
  // --------------------------------------------------------------------------
  createDashboard: (data: DashboardCreate) =>
    api.post<Dashboard>(`${BASE_PATH}/dashboards`, data),

  listDashboards: (params?: {
    dashboard_type?: DashboardType;
    owner_only?: boolean;
    skip?: number;
    limit?: number;
  }) =>
    api.get<DashboardList[]>(`${BASE_PATH}/dashboards${buildQueryString(params || {})}`),

  getDashboard: (dashboardId: number) =>
    api.get<Dashboard>(`${BASE_PATH}/dashboards/${dashboardId}`),

  updateDashboard: (dashboardId: number, data: DashboardUpdate) =>
    api.put<Dashboard>(`${BASE_PATH}/dashboards/${dashboardId}`, data),

  deleteDashboard: (dashboardId: number) =>
    api.delete(`${BASE_PATH}/dashboards/${dashboardId}`),

  duplicateDashboard: (dashboardId: number, newCode: string, newName: string) =>
    api.post<Dashboard>(`${BASE_PATH}/dashboards/${dashboardId}/duplicate${buildQueryString({
      new_code: newCode,
      new_name: newName,
    })}`),

  getDashboardStats: (dashboardId: number) =>
    api.get<DashboardStats>(`${BASE_PATH}/dashboards/${dashboardId}/stats`),

  // --------------------------------------------------------------------------
  // Widgets
  // --------------------------------------------------------------------------
  addWidget: (dashboardId: number, data: WidgetCreate) =>
    api.post<Widget>(`${BASE_PATH}/dashboards/${dashboardId}/widgets`, data),

  updateWidget: (widgetId: number, data: WidgetUpdate) =>
    api.put<Widget>(`${BASE_PATH}/widgets/${widgetId}`, data),

  deleteWidget: (widgetId: number) =>
    api.delete(`${BASE_PATH}/widgets/${widgetId}`),

  updateWidgetPositions: (dashboardId: number, positions: WidgetPosition[]) =>
    api.put<{ success: boolean }>(`${BASE_PATH}/dashboards/${dashboardId}/widgets/positions`, positions),

  // --------------------------------------------------------------------------
  // Reports
  // --------------------------------------------------------------------------
  createReport: (data: ReportCreate) =>
    api.post<Report>(`${BASE_PATH}/reports`, data),

  listReports: (params?: {
    report_type?: ReportType;
    skip?: number;
    limit?: number;
  }) =>
    api.get<ReportList[]>(`${BASE_PATH}/reports${buildQueryString(params || {})}`),

  getReport: (reportId: number) =>
    api.get<Report>(`${BASE_PATH}/reports/${reportId}`),

  updateReport: (reportId: number, data: ReportUpdate) =>
    api.put<Report>(`${BASE_PATH}/reports/${reportId}`, data),

  deleteReport: (reportId: number) =>
    api.delete(`${BASE_PATH}/reports/${reportId}`),

  executeReport: (reportId: number, request: ReportExecuteRequest) =>
    api.post<ReportExecution>(`${BASE_PATH}/reports/${reportId}/execute`, request),

  getReportExecutions: (reportId: number, skip = 0, limit = 20) =>
    api.get<ReportExecution[]>(`${BASE_PATH}/reports/${reportId}/executions${buildQueryString({ skip, limit })}`),

  createSchedule: (reportId: number, data: ReportScheduleCreate) =>
    api.post<ReportSchedule>(`${BASE_PATH}/reports/${reportId}/schedules`, data),

  // --------------------------------------------------------------------------
  // KPIs
  // --------------------------------------------------------------------------
  createKPI: (data: KPICreate) =>
    api.post<KPI>(`${BASE_PATH}/kpis`, data),

  listKPIs: (params?: {
    category?: KPICategory;
    skip?: number;
    limit?: number;
  }) =>
    api.get<KPIList[]>(`${BASE_PATH}/kpis${buildQueryString(params || {})}`),

  getKPI: (kpiId: number) =>
    api.get<KPI>(`${BASE_PATH}/kpis/${kpiId}`),

  updateKPI: (kpiId: number, data: KPIUpdate) =>
    api.put<KPI>(`${BASE_PATH}/kpis/${kpiId}`, data),

  recordKPIValue: (kpiId: number, data: KPIValueCreate) =>
    api.post<KPIValue>(`${BASE_PATH}/kpis/${kpiId}/values`, data),

  getKPIValues: (kpiId: number, params?: {
    start_date?: string;
    end_date?: string;
    period_type?: string;
    limit?: number;
  }) =>
    api.get<KPIValue[]>(`${BASE_PATH}/kpis/${kpiId}/values${buildQueryString(params || {})}`),

  setKPITarget: (kpiId: number, data: KPITargetCreate) =>
    api.post<KPITarget>(`${BASE_PATH}/kpis/${kpiId}/targets`, data),

  // --------------------------------------------------------------------------
  // Alert Rules
  // --------------------------------------------------------------------------
  createAlertRule: (data: AlertRuleCreate) =>
    api.post<AlertRule>(`${BASE_PATH}/alert-rules`, data),

  listAlertRules: (skip = 0, limit = 50) =>
    api.get<AlertRule[]>(`${BASE_PATH}/alert-rules${buildQueryString({ skip, limit })}`),

  getAlertRule: (ruleId: number) =>
    api.get<AlertRule>(`${BASE_PATH}/alert-rules/${ruleId}`),

  updateAlertRule: (ruleId: number, data: AlertRuleUpdate) =>
    api.put<AlertRule>(`${BASE_PATH}/alert-rules/${ruleId}`, data),

  // --------------------------------------------------------------------------
  // Alerts
  // --------------------------------------------------------------------------
  listAlerts: (params?: {
    status?: AlertStatus;
    severity?: AlertSeverity;
    skip?: number;
    limit?: number;
  }) =>
    api.get<AlertList[]>(`${BASE_PATH}/alerts${buildQueryString({
      status_filter: params?.status,
      severity: params?.severity,
      skip: params?.skip,
      limit: params?.limit,
    })}`),

  getAlert: (alertId: number) =>
    api.get<Alert>(`${BASE_PATH}/alerts/${alertId}`),

  acknowledgeAlert: (alertId: number, data: AlertAcknowledge) =>
    api.post<Alert>(`${BASE_PATH}/alerts/${alertId}/acknowledge`, data),

  resolveAlert: (alertId: number, data: AlertResolve) =>
    api.post<Alert>(`${BASE_PATH}/alerts/${alertId}/resolve`, data),

  snoozeAlert: (alertId: number, data: AlertSnooze) =>
    api.post<Alert>(`${BASE_PATH}/alerts/${alertId}/snooze`, data),

  // --------------------------------------------------------------------------
  // Data Sources
  // --------------------------------------------------------------------------
  createDataSource: (data: DataSourceCreate) =>
    api.post<DataSource>(`${BASE_PATH}/data-sources`, data),

  listDataSources: (params?: {
    source_type?: DataSourceType;
    skip?: number;
    limit?: number;
  }) =>
    api.get<DataSource[]>(`${BASE_PATH}/data-sources${buildQueryString(params || {})}`),

  getDataSource: (sourceId: number) =>
    api.get<DataSource>(`${BASE_PATH}/data-sources/${sourceId}`),

  updateDataSource: (sourceId: number, data: DataSourceUpdate) =>
    api.put<DataSource>(`${BASE_PATH}/data-sources/${sourceId}`, data),

  // --------------------------------------------------------------------------
  // Data Queries
  // --------------------------------------------------------------------------
  createQuery: (data: DataQueryCreate) =>
    api.post<DataQuery>(`${BASE_PATH}/queries`, data),

  listQueries: (skip = 0, limit = 50) =>
    api.get<DataQuery[]>(`${BASE_PATH}/queries${buildQueryString({ skip, limit })}`),

  getQuery: (queryId: number) =>
    api.get<DataQuery>(`${BASE_PATH}/queries/${queryId}`),

  // --------------------------------------------------------------------------
  // Bookmarks
  // --------------------------------------------------------------------------
  createBookmark: (data: BookmarkCreate) =>
    api.post<Bookmark>(`${BASE_PATH}/bookmarks`, data),

  listBookmarks: (itemType?: string) =>
    api.get<Bookmark[]>(`${BASE_PATH}/bookmarks${buildQueryString({ item_type: itemType })}`),

  deleteBookmark: (bookmarkId: number) =>
    api.delete(`${BASE_PATH}/bookmarks/${bookmarkId}`),

  // --------------------------------------------------------------------------
  // Exports
  // --------------------------------------------------------------------------
  createExport: (data: ExportRequest) =>
    api.post<Export>(`${BASE_PATH}/exports`, data),

  listExports: (skip = 0, limit = 20) =>
    api.get<Export[]>(`${BASE_PATH}/exports${buildQueryString({ skip, limit })}`),

  getExport: (exportId: number) =>
    api.get<Export>(`${BASE_PATH}/exports/${exportId}`),
};

export default biApi;
