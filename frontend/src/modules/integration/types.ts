/**
 * AZALS MODULE GAP-086 - Types Integration
 * =========================================
 *
 * Types TypeScript pour le module Integration.
 */

// ============================================================================
// ENUMS
// ============================================================================

export type ConnectorType =
  | 'google_drive'
  | 'google_sheets'
  | 'google_calendar'
  | 'gmail'
  | 'microsoft_365'
  | 'microsoft_dynamics'
  | 'outlook'
  | 'teams'
  | 'onedrive'
  | 'sharepoint'
  | 'slack'
  | 'discord'
  | 'twilio'
  | 'sendgrid'
  | 'salesforce'
  | 'hubspot'
  | 'pipedrive'
  | 'zoho_crm'
  | 'sage'
  | 'cegid'
  | 'pennylane'
  | 'quickbooks'
  | 'xero'
  | 'odoo'
  | 'sap'
  | 'netsuite'
  | 'shopify'
  | 'woocommerce'
  | 'prestashop'
  | 'magento'
  | 'stripe'
  | 'paypal'
  | 'gocardless'
  | 'mollie'
  | 'qonto'
  | 'swan'
  | 'bridge'
  | 'plaid'
  | 'mailchimp'
  | 'brevo'
  | 'klaviyo'
  | 'activecampaign'
  | 'dropbox'
  | 'aws_s3'
  | 'zapier'
  | 'make'
  | 'n8n'
  | 'rest_api'
  | 'graphql'
  | 'webhook'
  | 'custom';

export type AuthType =
  | 'none'
  | 'api_key'
  | 'oauth2'
  | 'oauth1'
  | 'basic'
  | 'bearer'
  | 'hmac'
  | 'jwt'
  | 'certificate'
  | 'custom';

export type ConnectionStatus =
  | 'pending'
  | 'configuring'
  | 'connected'
  | 'disconnected'
  | 'error'
  | 'expired'
  | 'rate_limited'
  | 'maintenance';

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

export type SyncDirection = 'inbound' | 'outbound' | 'bidirectional';

export type SyncMode = 'realtime' | 'scheduled' | 'manual' | 'on_demand';

export type SyncFrequency =
  | 'every_minute'
  | 'every_5_minutes'
  | 'every_15_minutes'
  | 'every_30_minutes'
  | 'hourly'
  | 'every_2_hours'
  | 'every_6_hours'
  | 'daily'
  | 'weekly'
  | 'monthly';

export type SyncStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'completed'
  | 'partial'
  | 'failed'
  | 'cancelled'
  | 'timeout'
  | 'retrying';

export type ConflictResolution =
  | 'source_wins'
  | 'target_wins'
  | 'newest_wins'
  | 'oldest_wins'
  | 'manual'
  | 'merge'
  | 'skip';

export type EntityType =
  | 'customer'
  | 'supplier'
  | 'contact'
  | 'product'
  | 'order'
  | 'invoice'
  | 'payment'
  | 'transaction'
  | 'lead'
  | 'opportunity'
  | 'project'
  | 'task'
  | 'ticket'
  | 'file'
  | 'event'
  | 'message'
  | 'custom';

export type WebhookDirection = 'inbound' | 'outbound';

export type WebhookStatus = 'active' | 'paused' | 'disabled' | 'error';

export type LogLevel = 'debug' | 'info' | 'warning' | 'error' | 'critical';

// ============================================================================
// CONNECTOR DEFINITION
// ============================================================================

export interface ConnectorDefinition {
  id: string;
  connector_type: ConnectorType;
  name: string;
  display_name: string;
  description: string | null;
  category: string | null;
  icon_url: string | null;
  logo_url: string | null;
  color: string | null;
  auth_type: AuthType;
  base_url: string | null;
  api_version: string | null;
  oauth_authorize_url: string | null;
  oauth_token_url: string | null;
  oauth_scopes: string[];
  oauth_pkce_required: boolean;
  required_fields: string[];
  optional_fields: string[];
  supported_entities: string[];
  supported_directions: string[];
  rate_limit_requests: number;
  rate_limit_daily: number | null;
  supports_webhooks: boolean;
  webhook_events: string[];
  documentation_url: string | null;
  setup_guide_url: string | null;
  is_active: boolean;
  is_beta: boolean;
  is_premium: boolean;
}

// ============================================================================
// CONNECTION
// ============================================================================

export interface Connection {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;
  connector_type: ConnectorType;
  auth_type: AuthType;
  base_url: string | null;
  api_version: string | null;
  settings: Record<string, unknown>;
  status: ConnectionStatus;
  health_status: HealthStatus;
  last_connected_at: string | null;
  last_error: string | null;
  last_error_at: string | null;
  last_health_check: string | null;
  consecutive_errors: number;
  success_rate_24h: number | null;
  avg_response_time_ms: number | null;
  is_active: boolean;
  is_deleted: boolean;
  version: number;
  created_at: string;
  updated_at: string | null;
}

export interface ConnectionListItem {
  id: string;
  code: string;
  name: string;
  connector_type: string;
  auth_type: AuthType;
  status: ConnectionStatus;
  health_status: HealthStatus;
  is_active: boolean;
  last_connected_at: string | null;
  created_at: string;
}

export interface ConnectionCreate {
  name: string;
  code?: string;
  description?: string;
  connector_type: ConnectorType;
  auth_type: AuthType;
  base_url?: string;
  api_version?: string;
  credentials?: Record<string, string>;
  custom_headers?: Record<string, string>;
  settings?: Record<string, unknown>;
}

export interface ConnectionUpdate {
  name?: string;
  description?: string;
  base_url?: string;
  api_version?: string;
  credentials?: Record<string, string>;
  custom_headers?: Record<string, string>;
  settings?: Record<string, unknown>;
  is_active?: boolean;
}

export interface ConnectionHealth {
  connection_id: string;
  is_healthy: boolean;
  status: ConnectionStatus;
  health_status: HealthStatus;
  last_check_at: string;
  response_time_ms: number;
  error: string | null;
  details: Record<string, unknown> | null;
}

export interface ConnectionStats {
  connection_id: string;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  success_rate: number;
  total_records_synced: number;
  avg_execution_time_seconds: number;
  last_execution_at: string | null;
  executions_last_24h: number;
  records_last_24h: number;
}

// ============================================================================
// DATA MAPPING
// ============================================================================

export interface FieldMapping {
  source_field: string;
  target_field: string;
  transform?: string;
  transform_rule_code?: string;
  default_value?: unknown;
  is_required: boolean;
  source_type?: string;
  target_type?: string;
}

export interface DataMapping {
  id: string;
  tenant_id: string;
  connection_id: string;
  code: string;
  name: string;
  description: string | null;
  entity_type: EntityType;
  source_entity: string;
  target_entity: string;
  direction: SyncDirection;
  field_mappings: FieldMapping[];
  source_key_field: string | null;
  target_key_field: string | null;
  source_filter: Record<string, unknown> | null;
  target_filter: Record<string, unknown> | null;
  conflict_resolution: ConflictResolution;
  batch_size: number;
  is_active: boolean;
  version: number;
  created_at: string;
  updated_at: string | null;
}

export interface DataMappingCreate {
  name: string;
  code?: string;
  description?: string;
  connection_id: string;
  entity_type: EntityType;
  source_entity: string;
  target_entity: string;
  direction?: SyncDirection;
  field_mappings?: FieldMapping[];
  source_key_field?: string;
  target_key_field?: string;
  source_filter?: Record<string, unknown>;
  target_filter?: Record<string, unknown>;
  conflict_resolution?: ConflictResolution;
  batch_size?: number;
}

// ============================================================================
// SYNC CONFIGURATION
// ============================================================================

export interface SyncConfiguration {
  id: string;
  tenant_id: string;
  connection_id: string;
  mapping_id: string;
  code: string;
  name: string;
  description: string | null;
  direction: SyncDirection;
  sync_mode: SyncMode;
  frequency: SyncFrequency | null;
  cron_expression: string | null;
  timezone: string;
  next_run_at: string | null;
  last_run_at: string | null;
  last_run_status: SyncStatus | null;
  max_retries: number;
  retry_delay_seconds: number;
  use_delta_sync: boolean;
  delta_field: string | null;
  notify_on_error: boolean;
  notify_on_success: boolean;
  notification_emails: string[];
  notification_webhook_url: string | null;
  is_active: boolean;
  is_paused: boolean;
  pause_reason: string | null;
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  total_records_synced: number;
  version: number;
  created_at: string;
  updated_at: string | null;
}

export interface SyncConfigurationCreate {
  name: string;
  code?: string;
  description?: string;
  connection_id: string;
  mapping_id: string;
  direction: SyncDirection;
  sync_mode?: SyncMode;
  frequency?: SyncFrequency;
  cron_expression?: string;
  timezone?: string;
  max_retries?: number;
  retry_delay_seconds?: number;
  use_delta_sync?: boolean;
  delta_field?: string;
  notify_on_error?: boolean;
  notify_on_success?: boolean;
  notification_emails?: string[];
  notification_webhook_url?: string;
}

// ============================================================================
// SYNC EXECUTION
// ============================================================================

export interface SyncExecution {
  id: string;
  tenant_id: string;
  connection_id: string | null;
  config_id: string | null;
  execution_number: string;
  direction: SyncDirection;
  entity_type: EntityType;
  started_at: string;
  completed_at: string | null;
  duration_seconds: number | null;
  status: SyncStatus;
  total_records: number;
  processed_records: number;
  created_records: number;
  updated_records: number;
  deleted_records: number;
  skipped_records: number;
  failed_records: number;
  progress_percent: number;
  current_step: string | null;
  error_count: number;
  errors: Array<Record<string, unknown>>;
  last_error: string | null;
  retry_count: number;
  is_retry: boolean;
  triggered_by: string | null;
  created_at: string;
}

export interface SyncExecutionCreate {
  config_id?: string;
  connection_id?: string;
  mapping_id?: string;
  direction?: SyncDirection;
  force_full_sync?: boolean;
}

// ============================================================================
// EXECUTION LOG
// ============================================================================

export interface ExecutionLog {
  id: string;
  execution_id: string;
  level: LogLevel;
  message: string;
  source_id: string | null;
  target_id: string | null;
  entity_type: string | null;
  action: string | null;
  error_code: string | null;
  error_details: Record<string, unknown> | null;
  processing_time_ms: number | null;
  timestamp: string;
}

// ============================================================================
// SYNC CONFLICT
// ============================================================================

export interface SyncConflict {
  id: string;
  tenant_id: string;
  execution_id: string;
  source_id: string;
  target_id: string;
  entity_type: EntityType;
  source_data: Record<string, unknown>;
  target_data: Record<string, unknown>;
  conflicting_fields: string[];
  resolution_strategy: ConflictResolution | null;
  resolved_data: Record<string, unknown> | null;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_notes: string | null;
  is_resolved: boolean;
  is_ignored: boolean;
  created_at: string;
}

export interface ConflictResolve {
  resolution_strategy: ConflictResolution;
  resolved_data?: Record<string, unknown>;
  resolution_notes?: string;
}

// ============================================================================
// WEBHOOK
// ============================================================================

export interface Webhook {
  id: string;
  tenant_id: string;
  connection_id: string;
  code: string;
  name: string;
  description: string | null;
  direction: WebhookDirection;
  endpoint_path: string | null;
  secret_key: string | null;
  target_url: string | null;
  http_method: string;
  headers: Record<string, string>;
  auth_type: AuthType | null;
  subscribed_events: string[];
  payload_template: string | null;
  include_metadata: boolean;
  max_retries: number;
  retry_delay_seconds: number;
  timeout_seconds: number;
  status: WebhookStatus;
  is_active: boolean;
  last_triggered_at: string | null;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  last_error: string | null;
  last_error_at: string | null;
  version: number;
  created_at: string;
  updated_at: string | null;
}

export interface WebhookInboundCreate {
  name: string;
  code?: string;
  description?: string;
  connection_id: string;
  subscribed_events: string[];
  signature_header?: string;
  signature_algorithm?: string;
}

export interface WebhookOutboundCreate {
  name: string;
  code?: string;
  description?: string;
  connection_id: string;
  target_url: string;
  http_method?: string;
  headers?: Record<string, string>;
  auth_type?: AuthType;
  auth_credentials?: Record<string, string>;
  subscribed_events: string[];
  payload_template?: string;
  include_metadata?: boolean;
  max_retries?: number;
  retry_delay_seconds?: number;
  timeout_seconds?: number;
}

export interface WebhookLog {
  id: string;
  webhook_id: string;
  direction: WebhookDirection;
  event_type: string | null;
  event_id: string | null;
  request_url: string | null;
  request_method: string | null;
  response_status_code: number | null;
  duration_ms: number | null;
  success: boolean;
  error_message: string | null;
  retry_count: number;
  source_ip: string | null;
  timestamp: string;
}

export interface WebhookTest {
  success: boolean;
  status_code: number | null;
  response_time_ms: number | null;
  response_body: string | null;
  error: string | null;
}

// ============================================================================
// STATISTICS
// ============================================================================

export interface IntegrationStats {
  tenant_id: string;
  total_connections: number;
  active_connections: number;
  connected_connections: number;
  error_connections: number;
  total_mappings: number;
  active_mappings: number;
  total_sync_configs: number;
  active_sync_configs: number;
  pending_conflicts: number;
  executions_today: number;
  executions_last_7_days: number;
  records_synced_today: number;
  records_synced_last_7_days: number;
  failed_executions_today: number;
  success_rate_today: number;
  success_rate_7_days: number;
  by_connector_type: Record<string, number>;
  by_entity_type: Record<string, number>;
  by_status: Record<string, number>;
}

// ============================================================================
// PAGINATED RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface AutocompleteItem {
  id: string;
  code: string;
  name: string;
  label: string;
  extra?: Record<string, unknown>;
}

// ============================================================================
// FILTERS
// ============================================================================

export interface ConnectionFilters {
  search?: string;
  connector_type?: ConnectorType[];
  status?: ConnectionStatus[];
  health_status?: HealthStatus[];
  is_active?: boolean;
}

export interface SyncExecutionFilters {
  connection_id?: string;
  config_id?: string;
  status?: SyncStatus[];
  direction?: SyncDirection;
  entity_type?: EntityType;
  date_from?: string;
  date_to?: string;
}

export interface ConflictFilters {
  execution_id?: string;
  entity_type?: EntityType;
  is_resolved?: boolean;
}

// ============================================================================
// CONNECTOR CATEGORIES
// ============================================================================

export const CONNECTOR_CATEGORIES: Record<string, string> = {
  productivity: 'Productivite',
  communication: 'Communication',
  crm: 'CRM',
  accounting: 'Comptabilite',
  erp: 'ERP',
  ecommerce: 'E-commerce',
  payment: 'Paiement',
  banking: 'Banque',
  marketing: 'Marketing',
  storage: 'Stockage',
  custom: 'Personnalise',
};

// ============================================================================
// STATUS COLORS
// ============================================================================

export const CONNECTION_STATUS_COLORS: Record<ConnectionStatus, string> = {
  pending: 'gray',
  configuring: 'blue',
  connected: 'green',
  disconnected: 'gray',
  error: 'red',
  expired: 'orange',
  rate_limited: 'yellow',
  maintenance: 'purple',
};

export const HEALTH_STATUS_COLORS: Record<HealthStatus, string> = {
  healthy: 'green',
  degraded: 'yellow',
  unhealthy: 'red',
  unknown: 'gray',
};

export const SYNC_STATUS_COLORS: Record<SyncStatus, string> = {
  pending: 'gray',
  queued: 'blue',
  running: 'blue',
  completed: 'green',
  partial: 'yellow',
  failed: 'red',
  cancelled: 'gray',
  timeout: 'orange',
  retrying: 'purple',
};
