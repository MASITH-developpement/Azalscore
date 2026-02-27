/**
 * AZALSCORE Module - Dashboards Types
 * Types TypeScript pour le module de tableaux de bord
 */

// ============================================================================
// ENUMS
// ============================================================================

export type DashboardType =
  | 'personal'
  | 'operational'
  | 'executive'
  | 'analytical';

export type WidgetType =
  | 'kpi'
  | 'chart'
  | 'table'
  | 'gauge'
  | 'list'
  | 'map'
  | 'calendar'
  | 'text'
  | 'iframe';

export type ChartType =
  | 'line'
  | 'bar'
  | 'area'
  | 'pie'
  | 'donut'
  | 'radar'
  | 'scatter'
  | 'treemap'
  | 'funnel';

export type DataSourceType =
  | 'database'
  | 'api'
  | 'module'
  | 'file'
  | 'manual';

export type RefreshFrequency =
  | 'realtime'
  | 'minute_1'
  | 'minute_5'
  | 'minute_15'
  | 'minute_30'
  | 'hourly'
  | 'daily'
  | 'manual';

export type AlertSeverity =
  | 'info'
  | 'warning'
  | 'error'
  | 'critical';

export type AlertOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'greater_or_equal'
  | 'less_or_equal'
  | 'between'
  | 'contains';

export type SharePermission =
  | 'view'
  | 'edit'
  | 'admin';

export type ExportFormat =
  | 'pdf'
  | 'excel'
  | 'csv'
  | 'png'
  | 'json';

// ============================================================================
// DASHBOARD
// ============================================================================

export interface Dashboard {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  type: DashboardType;
  icon?: string;
  color?: string;
  is_default: boolean;
  is_active: boolean;
  owner_id: string;
  owner_name?: string;
  tags: string[];
  refresh_frequency: RefreshFrequency;
  layout_config: Record<string, unknown>;
  widgets: Widget[];
  created_at: string;
  updated_at?: string;
}

export interface DashboardCreate {
  code: string;
  name: string;
  description?: string;
  type?: DashboardType;
  icon?: string;
  color?: string;
  is_default?: boolean;
  tags?: string[];
  refresh_frequency?: RefreshFrequency;
  layout_config?: Record<string, unknown>;
}

export interface DashboardUpdate {
  name?: string;
  description?: string;
  type?: DashboardType;
  icon?: string;
  color?: string;
  is_default?: boolean;
  is_active?: boolean;
  tags?: string[];
  refresh_frequency?: RefreshFrequency;
  layout_config?: Record<string, unknown>;
}

// ============================================================================
// WIDGET
// ============================================================================

export interface Widget {
  id: string;
  dashboard_id: string;
  name: string;
  type: WidgetType;
  chart_type?: ChartType;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
  data_source_id?: string;
  query_id?: string;
  config: Record<string, unknown>;
  filters: Record<string, unknown>;
  thresholds: WidgetThreshold[];
  is_visible: boolean;
  created_at: string;
  updated_at?: string;
}

export interface WidgetCreate {
  name: string;
  type: WidgetType;
  chart_type?: ChartType;
  width?: number;
  height?: number;
  data_source_id?: string;
  query_id?: string;
  config?: Record<string, unknown>;
}

export interface WidgetUpdate {
  name?: string;
  chart_type?: ChartType;
  config?: Record<string, unknown>;
  filters?: Record<string, unknown>;
  is_visible?: boolean;
}

export interface WidgetLayoutUpdate {
  widget_id: string;
  position_x: number;
  position_y: number;
  width: number;
  height: number;
}

export interface WidgetThreshold {
  min?: number;
  max?: number;
  color: string;
  label?: string;
}

// ============================================================================
// DATA SOURCE
// ============================================================================

export interface DataSource {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  type: DataSourceType;
  connection_string?: string;
  config: Record<string, unknown>;
  refresh_frequency: RefreshFrequency;
  last_refresh_at?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface DataSourceCreate {
  code: string;
  name: string;
  description?: string;
  type: DataSourceType;
  connection_string?: string;
  config?: Record<string, unknown>;
  refresh_frequency?: RefreshFrequency;
}

export interface DataSourceUpdate {
  name?: string;
  description?: string;
  connection_string?: string;
  config?: Record<string, unknown>;
  refresh_frequency?: RefreshFrequency;
  is_active?: boolean;
}

// ============================================================================
// DATA QUERY
// ============================================================================

export interface DataQuery {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  data_source_id: string;
  query_text: string;
  parameters: Record<string, QueryParameter>;
  result_schema?: Record<string, unknown>;
  cache_ttl_seconds?: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface QueryParameter {
  type: 'string' | 'number' | 'date' | 'boolean';
  required: boolean;
  default?: unknown;
  label?: string;
}

export interface DataQueryCreate {
  code: string;
  name: string;
  description?: string;
  data_source_id?: string;
  query_text: string;
  parameters?: Record<string, QueryParameter>;
}

export interface DataQueryUpdate {
  name?: string;
  description?: string;
  query_text?: string;
  parameters?: Record<string, QueryParameter>;
  cache_ttl_seconds?: number;
  is_active?: boolean;
}

// ============================================================================
// SHARE
// ============================================================================

export interface DashboardShare {
  id: string;
  dashboard_id: string;
  shared_with_user?: string;
  shared_with_role?: string;
  permission: SharePermission;
  is_public_link: boolean;
  public_token?: string;
  expires_at?: string;
  is_active: boolean;
  created_at: string;
}

export interface ShareCreate {
  shared_with_user?: string;
  shared_with_role?: string;
  permission: SharePermission;
  is_public_link?: boolean;
  expires_at?: string;
}

export interface ShareUpdate {
  permission?: SharePermission;
  expires_at?: string;
  is_active?: boolean;
}

// ============================================================================
// ALERT RULE
// ============================================================================

export interface AlertRule {
  id: string;
  tenant_id: string;
  dashboard_id?: string;
  widget_id?: string;
  code: string;
  name: string;
  description?: string;
  metric_name: string;
  operator: AlertOperator;
  threshold_value: number | string;
  threshold_value_2?: number | string;
  severity: AlertSeverity;
  notification_channels: string[];
  is_active: boolean;
  last_triggered_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface AlertRuleCreate {
  code: string;
  name: string;
  description?: string;
  dashboard_id?: string;
  widget_id?: string;
  metric_name: string;
  operator: AlertOperator;
  threshold_value: number;
  threshold_value_2?: number;
  severity: AlertSeverity;
  notification_channels?: string[];
}

export interface AlertRuleUpdate {
  name?: string;
  description?: string;
  metric_name?: string;
  operator?: AlertOperator;
  threshold_value?: number;
  threshold_value_2?: number;
  severity?: AlertSeverity;
  notification_channels?: string[];
  is_active?: boolean;
}

// ============================================================================
// ALERT
// ============================================================================

export interface Alert {
  id: string;
  tenant_id: string;
  rule_id: string;
  rule_name: string;
  severity: AlertSeverity;
  message: string;
  metric_value: number | string;
  is_acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  acknowledge_note?: string;
  is_resolved: boolean;
  resolved_at?: string;
  resolution_note?: string;
  snoozed_until?: string;
  triggered_at: string;
}

// ============================================================================
// SCHEDULED REPORT
// ============================================================================

export interface ScheduledReport {
  id: string;
  tenant_id: string;
  dashboard_id: string;
  dashboard_name: string;
  code: string;
  name: string;
  cron_expression: string;
  format: ExportFormat;
  recipients: string[];
  is_active: boolean;
  last_run_at?: string;
  next_run_at?: string;
  created_at: string;
}

export interface ScheduledReportCreate {
  code: string;
  name: string;
  dashboard_id?: string;
  cron_expression: string;
  format: ExportFormat;
  recipients: string[];
}

export interface ScheduledReportUpdate {
  name?: string;
  cron_expression?: string;
  format?: ExportFormat;
  recipients?: string[];
  is_active?: boolean;
}

// ============================================================================
// USER PREFERENCE
// ============================================================================

export interface UserPreference {
  id: string;
  user_id: string;
  default_dashboard_id?: string;
  theme: 'light' | 'dark' | 'auto';
  refresh_interval: number;
  timezone: string;
  notifications_enabled: boolean;
  created_at: string;
  updated_at?: string;
}

export interface UserPreferenceCreate {
  default_dashboard_id?: string;
  theme?: 'light' | 'dark' | 'auto';
  refresh_interval?: number;
  timezone?: string;
  notifications_enabled?: boolean;
}

export interface UserPreferenceUpdate {
  default_dashboard_id?: string;
  theme?: 'light' | 'dark' | 'auto';
  refresh_interval?: number;
  timezone?: string;
  notifications_enabled?: boolean;
}

// ============================================================================
// TEMPLATE
// ============================================================================

export interface DashboardTemplate {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  type: DashboardType;
  category: string;
  is_public: boolean;
  preview_image_url?: string;
  layout_config: Record<string, unknown>;
  widget_templates: WidgetCreate[];
  created_at: string;
}

export interface TemplateCreate {
  code: string;
  name: string;
  description?: string;
  type: DashboardType;
  category: string;
  is_public?: boolean;
  preview_image_url?: string;
}

export interface TemplateUpdate {
  name?: string;
  description?: string;
  category?: string;
  is_public?: boolean;
  preview_image_url?: string;
}

// ============================================================================
// FAVORITE
// ============================================================================

export interface Favorite {
  id: string;
  user_id: string;
  dashboard_id: string;
  dashboard_name: string;
  display_order: number;
  created_at: string;
}

export interface FavoriteCreate {
  dashboard_id: string;
  display_order?: number;
}

// ============================================================================
// EXPORT
// ============================================================================

export interface ExportRequest {
  format: ExportFormat;
  widget_ids?: string[];
  include_filters?: boolean;
  options?: Record<string, unknown>;
}

export interface ExportResponse {
  file_url: string;
  file_name: string;
  format: ExportFormat;
  size_bytes: number;
  expires_at: string;
}

// ============================================================================
// LIST RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export type DashboardListResponse = PaginatedResponse<Dashboard>;
export type TemplateListResponse = PaginatedResponse<DashboardTemplate>;
export type AlertListResponse = PaginatedResponse<Alert>;

// ============================================================================
// FILTERS
// ============================================================================

export interface DashboardFilters {
  type?: DashboardType;
  is_active?: boolean;
  owner_id?: string;
  tags?: string[];
  search?: string;
  page?: number;
  page_size?: number;
}

// ============================================================================
// CONFIG CONSTANTS
// ============================================================================

export const DASHBOARD_TYPE_CONFIG: Record<DashboardType, { label: string; color: string }> = {
  personal: { label: 'Personnel', color: 'blue' },
  operational: { label: 'Operationnel', color: 'green' },
  executive: { label: 'Executif', color: 'purple' },
  analytical: { label: 'Analytique', color: 'orange' },
};

export const WIDGET_TYPE_CONFIG: Record<WidgetType, { label: string; icon: string }> = {
  kpi: { label: 'KPI', icon: 'Target' },
  chart: { label: 'Graphique', icon: 'BarChart' },
  table: { label: 'Tableau', icon: 'Table' },
  gauge: { label: 'Jauge', icon: 'Gauge' },
  list: { label: 'Liste', icon: 'List' },
  map: { label: 'Carte', icon: 'Map' },
  calendar: { label: 'Calendrier', icon: 'Calendar' },
  text: { label: 'Texte', icon: 'Type' },
  iframe: { label: 'IFrame', icon: 'Globe' },
};

export const CHART_TYPE_CONFIG: Record<ChartType, { label: string; icon: string }> = {
  line: { label: 'Ligne', icon: 'TrendingUp' },
  bar: { label: 'Barres', icon: 'BarChart' },
  area: { label: 'Aire', icon: 'AreaChart' },
  pie: { label: 'Camembert', icon: 'PieChart' },
  donut: { label: 'Donut', icon: 'Circle' },
  radar: { label: 'Radar', icon: 'Radar' },
  scatter: { label: 'Nuage', icon: 'ScatterChart' },
  treemap: { label: 'Treemap', icon: 'LayoutGrid' },
  funnel: { label: 'Entonnoir', icon: 'Filter' },
};

export const ALERT_SEVERITY_CONFIG: Record<AlertSeverity, { label: string; color: string }> = {
  info: { label: 'Info', color: 'blue' },
  warning: { label: 'Avertissement', color: 'yellow' },
  error: { label: 'Erreur', color: 'orange' },
  critical: { label: 'Critique', color: 'red' },
};
