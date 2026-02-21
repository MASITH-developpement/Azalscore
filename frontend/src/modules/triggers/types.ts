/**
 * AZALSCORE - Types Module Triggers
 * Types TypeScript correspondant exactement aux schemas backend
 * Conformité AZA-FE-META
 */

// ============================================================
// ENUMS - Correspondance exacte avec models.py
// ============================================================

export type TriggerType = 'THRESHOLD' | 'CONDITION' | 'SCHEDULED' | 'EVENT' | 'MANUAL';

export const TRIGGER_TYPE_LABELS: Record<TriggerType, string> = {
  THRESHOLD: 'Seuil',
  CONDITION: 'Condition',
  SCHEDULED: 'Planifié',
  EVENT: 'Événement',
  MANUAL: 'Manuel',
};

export type TriggerStatus = 'ACTIVE' | 'PAUSED' | 'DISABLED';

export const TRIGGER_STATUS_CONFIG: Record<TriggerStatus, { label: string; color: string }> = {
  ACTIVE: { label: 'Actif', color: 'green' },
  PAUSED: { label: 'En pause', color: 'orange' },
  DISABLED: { label: 'Désactivé', color: 'gray' },
};

export type ConditionOperator =
  | 'eq' | 'ne' | 'gt' | 'ge' | 'lt' | 'le'
  | 'in' | 'not_in' | 'contains' | 'starts_with' | 'ends_with'
  | 'between' | 'is_null' | 'is_not_null';

export const CONDITION_OPERATOR_LABELS: Record<ConditionOperator, string> = {
  eq: 'Égal',
  ne: 'Différent',
  gt: 'Supérieur',
  ge: 'Supérieur ou égal',
  lt: 'Inférieur',
  le: 'Inférieur ou égal',
  in: 'Dans la liste',
  not_in: 'Hors de la liste',
  contains: 'Contient',
  starts_with: 'Commence par',
  ends_with: 'Finit par',
  between: 'Entre',
  is_null: 'Est null',
  is_not_null: 'N\'est pas null',
};

export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL' | 'EMERGENCY';

export const ALERT_SEVERITY_CONFIG: Record<AlertSeverity, { label: string; color: string; icon: string }> = {
  INFO: { label: 'Information', color: 'blue', icon: 'info' },
  WARNING: { label: 'Avertissement', color: 'orange', icon: 'warning' },
  CRITICAL: { label: 'Critique', color: 'red', icon: 'alert' },
  EMERGENCY: { label: 'Urgence', color: 'red', icon: 'emergency' },
};

export type NotificationChannel = 'EMAIL' | 'WEBHOOK' | 'IN_APP' | 'SMS' | 'SLACK' | 'TEAMS';

export const NOTIFICATION_CHANNEL_LABELS: Record<NotificationChannel, string> = {
  EMAIL: 'Email',
  WEBHOOK: 'Webhook',
  IN_APP: 'Application',
  SMS: 'SMS',
  SLACK: 'Slack',
  TEAMS: 'Microsoft Teams',
};

export type NotificationStatus = 'PENDING' | 'SENT' | 'FAILED' | 'DELIVERED' | 'READ';

export const NOTIFICATION_STATUS_CONFIG: Record<NotificationStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'gray' },
  SENT: { label: 'Envoyé', color: 'blue' },
  FAILED: { label: 'Échoué', color: 'red' },
  DELIVERED: { label: 'Délivré', color: 'green' },
  READ: { label: 'Lu', color: 'green' },
};

export type ReportFrequency = 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'YEARLY' | 'CUSTOM';

export const REPORT_FREQUENCY_LABELS: Record<ReportFrequency, string> = {
  DAILY: 'Quotidien',
  WEEKLY: 'Hebdomadaire',
  MONTHLY: 'Mensuel',
  QUARTERLY: 'Trimestriel',
  YEARLY: 'Annuel',
  CUSTOM: 'Personnalisé',
};

export type EscalationLevel = 'L1' | 'L2' | 'L3' | 'L4';

export const ESCALATION_LEVEL_CONFIG: Record<EscalationLevel, { label: string; description: string }> = {
  L1: { label: 'Niveau 1', description: 'Opérationnel' },
  L2: { label: 'Niveau 2', description: 'Manager' },
  L3: { label: 'Niveau 3', description: 'Direction' },
  L4: { label: 'Niveau 4', description: 'Dirigeant' },
};

// ============================================================
// TYPES PRINCIPAUX - Correspondance schemas.py
// ============================================================

export interface TriggerCondition {
  field?: string;
  operator?: ConditionOperator;
  value?: unknown;
  and?: TriggerCondition[];
  or?: TriggerCondition[];
  not?: TriggerCondition;
}

export interface Trigger {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;

  trigger_type: TriggerType;
  status: TriggerStatus;

  source_module: string;
  source_entity: string | null;
  source_field: string | null;

  condition: TriggerCondition;

  threshold_value: string | null;
  threshold_operator: ConditionOperator | null;

  schedule_cron: string | null;
  schedule_timezone: string | null;

  severity: AlertSeverity;
  escalation_enabled: boolean;
  escalation_delay_minutes: number | null;
  escalation_level: EscalationLevel | null;

  cooldown_minutes: number;
  is_active: boolean;

  last_triggered_at: string | null;
  trigger_count: number;

  created_at: string;
  updated_at: string;
  created_by: string | null;
}

export interface TriggerCreateInput {
  code: string;
  name: string;
  description?: string;
  trigger_type: TriggerType;
  source_module: string;
  source_entity?: string;
  source_field?: string;
  condition: TriggerCondition;
  threshold_value?: string;
  threshold_operator?: ConditionOperator;
  schedule_cron?: string;
  schedule_timezone?: string;
  severity?: AlertSeverity;
  escalation_enabled?: boolean;
  escalation_delay_minutes?: number;
  cooldown_minutes?: number;
  action_template_id?: string;
}

export interface TriggerUpdateInput {
  name?: string;
  description?: string;
  trigger_type?: TriggerType;
  source_module?: string;
  source_entity?: string;
  source_field?: string;
  condition?: TriggerCondition;
  threshold_value?: string;
  threshold_operator?: ConditionOperator;
  schedule_cron?: string;
  schedule_timezone?: string;
  severity?: AlertSeverity;
  escalation_enabled?: boolean;
  escalation_delay_minutes?: number;
  cooldown_minutes?: number;
  action_template_id?: string;
  is_active?: boolean;
}

// ============================================================
// SUBSCRIPTIONS
// ============================================================

export interface TriggerSubscription {
  id: string;
  tenant_id: string;
  trigger_id: string;

  user_id: string | null;
  role_code: string | null;
  group_code: string | null;
  email_external: string | null;

  channel: NotificationChannel;
  channel_config: Record<string, unknown> | null;

  escalation_level: EscalationLevel;
  is_active: boolean;

  created_at: string;
  created_by: string | null;
}

export interface SubscriptionCreateInput {
  trigger_id: string;
  user_id?: string;
  role_code?: string;
  group_code?: string;
  email_external?: string;
  channel?: NotificationChannel;
  channel_config?: Record<string, unknown>;
  escalation_level?: EscalationLevel;
}

// ============================================================
// EVENTS
// ============================================================

export interface TriggerEvent {
  id: string;
  tenant_id: string;
  trigger_id: string;

  triggered_at: string;
  triggered_value: string | null;
  condition_details: Record<string, unknown> | null;

  severity: AlertSeverity;
  escalation_level: EscalationLevel;
  escalated_at: string | null;

  resolved: boolean;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_notes: string | null;
}

export interface ResolveEventInput {
  resolution_notes?: string;
}

export interface FireTriggerInput {
  triggered_value?: string;
  condition_details?: Record<string, unknown>;
}

// ============================================================
// NOTIFICATIONS
// ============================================================

export interface Notification {
  id: string;
  tenant_id: string;
  event_id: string;

  user_id: string | null;
  email: string | null;

  channel: NotificationChannel;
  subject: string | null;
  body: string;

  status: NotificationStatus;

  sent_at: string | null;
  delivered_at: string | null;
  read_at: string | null;
  failed_at: string | null;
  failure_reason: string | null;

  retry_count: number;
  next_retry_at: string | null;
}

// ============================================================
// TEMPLATES
// ============================================================

export interface NotificationTemplate {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;

  subject_template: string | null;
  body_template: string;
  body_html: string | null;

  available_variables: string[] | null;

  is_active: boolean;
  is_system: boolean;

  created_at: string;
  updated_at: string;
  created_by: string | null;
}

export interface TemplateCreateInput {
  code: string;
  name: string;
  description?: string;
  subject_template?: string;
  body_template: string;
  body_html?: string;
  available_variables?: string[];
}

export interface TemplateUpdateInput {
  name?: string;
  description?: string;
  subject_template?: string;
  body_template?: string;
  body_html?: string;
  available_variables?: string[];
  is_active?: boolean;
}

// ============================================================
// SCHEDULED REPORTS
// ============================================================

export interface ReportRecipients {
  users?: string[];
  roles?: string[];
  emails?: string[];
}

export interface ScheduledReport {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;

  report_type: string;
  report_config: Record<string, unknown> | null;

  frequency: ReportFrequency;
  schedule_day: number | null;
  schedule_time: string | null;
  schedule_timezone: string;
  schedule_cron: string | null;

  recipients: ReportRecipients;
  output_format: string;

  is_active: boolean;

  last_generated_at: string | null;
  next_generation_at: string | null;
  generation_count: number;

  created_at: string;
  updated_at: string;
  created_by: string | null;
}

export interface ScheduledReportCreateInput {
  code: string;
  name: string;
  description?: string;
  report_type: string;
  report_config?: Record<string, unknown>;
  frequency: ReportFrequency;
  schedule_day?: number;
  schedule_time?: string;
  schedule_timezone?: string;
  schedule_cron?: string;
  recipients: ReportRecipients;
  output_format?: string;
}

export interface ScheduledReportUpdateInput {
  name?: string;
  description?: string;
  report_config?: Record<string, unknown>;
  frequency?: ReportFrequency;
  schedule_day?: number;
  schedule_time?: string;
  schedule_timezone?: string;
  recipients?: ReportRecipients;
  output_format?: string;
  is_active?: boolean;
}

export interface ReportHistory {
  id: string;
  tenant_id: string;
  report_id: string;

  generated_at: string;
  generated_by: string | null;

  file_name: string;
  file_path: string | null;
  file_size: number | null;
  file_format: string;

  sent_to: Record<string, unknown> | null;
  sent_at: string | null;

  success: boolean;
  error_message: string | null;
}

// ============================================================
// WEBHOOKS
// ============================================================

export interface WebhookEndpoint {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string | null;

  url: string;
  method: string;
  headers: Record<string, string> | null;

  auth_type: string | null;
  // auth_config omis pour sécurité

  max_retries: number;
  retry_delay_seconds: number;

  is_active: boolean;
  last_success_at: string | null;
  last_failure_at: string | null;
  consecutive_failures: number;

  created_at: string;
  updated_at: string;
  created_by: string | null;
}

export interface WebhookCreateInput {
  code: string;
  name: string;
  description?: string;
  url: string;
  method?: string;
  headers?: Record<string, string>;
  auth_type?: string;
  auth_config?: Record<string, string>;
  max_retries?: number;
  retry_delay_seconds?: number;
}

export interface WebhookUpdateInput {
  name?: string;
  description?: string;
  url?: string;
  method?: string;
  headers?: Record<string, string>;
  auth_type?: string;
  auth_config?: Record<string, string>;
  max_retries?: number;
  retry_delay_seconds?: number;
  is_active?: boolean;
}

export interface WebhookTestResult {
  success: boolean;
  status_code: number | null;
  response_time_ms: number | null;
  error: string | null;
}

// ============================================================
// LOGS
// ============================================================

export interface TriggerLog {
  id: string;
  tenant_id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: Record<string, unknown> | null;
  success: boolean;
  error_message: string | null;
  created_at: string;
}

// ============================================================
// DASHBOARD & STATS
// ============================================================

export interface TriggerStats {
  total_triggers: number;
  active_triggers: number;
  paused_triggers: number;
  disabled_triggers: number;

  total_events_24h: number;
  unresolved_events: number;
  critical_events: number;

  total_notifications_24h: number;
  pending_notifications: number;
  failed_notifications: number;

  scheduled_reports: number;
  reports_generated_24h: number;
}

export interface TriggerDashboard {
  stats: TriggerStats;
  recent_events: TriggerEvent[];
  upcoming_reports: ScheduledReport[];
}

// ============================================================
// API RESPONSE TYPES
// ============================================================

export interface TriggerListResponse {
  triggers: Trigger[];
  total: number;
}

export interface EventListResponse {
  events: TriggerEvent[];
  total: number;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
}

export interface TriggerLogListResponse {
  logs: TriggerLog[];
  total: number;
}

// ============================================================
// FILTER TYPES
// ============================================================

export interface TriggerFilters {
  source_module?: string;
  trigger_type?: TriggerType;
  include_inactive?: boolean;
}

export interface EventFilters {
  trigger_id?: string;
  resolved?: boolean;
  severity?: AlertSeverity;
  from_date?: string;
  to_date?: string;
  limit?: number;
}

export interface LogFilters {
  action?: string;
  entity_type?: string;
  from_date?: string;
  to_date?: string;
  limit?: number;
}
