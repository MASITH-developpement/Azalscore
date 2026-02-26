/**
 * AZALSCORE - Triggers API
 * =========================
 * Complete typed API client for Triggers & Notifications module.
 * Covers: Triggers, Events, Subscriptions, Notifications, Templates, Webhooks, Scheduled Reports
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const triggersKeys = {
  all: ['triggers'] as const,
  list: () => [...triggersKeys.all, 'list'] as const,
  detail: (id: string) => [...triggersKeys.all, id] as const,

  // Events
  events: () => [...triggersKeys.all, 'events'] as const,
  event: (id: string) => [...triggersKeys.events(), id] as const,

  // Subscriptions
  subscriptions: (triggerId?: string) => [...triggersKeys.all, 'subscriptions', triggerId] as const,

  // Notifications
  notifications: () => [...triggersKeys.all, 'notifications'] as const,
  myNotifications: () => [...triggersKeys.all, 'my-notifications'] as const,

  // Templates
  templates: () => [...triggersKeys.all, 'templates'] as const,
  template: (id: string) => [...triggersKeys.templates(), id] as const,

  // Scheduled Reports
  reports: () => [...triggersKeys.all, 'reports'] as const,
  report: (id: string) => [...triggersKeys.reports(), id] as const,
  reportHistory: (reportId: string) => [...triggersKeys.report(reportId), 'history'] as const,

  // Webhooks
  webhooks: () => [...triggersKeys.all, 'webhooks'] as const,
  webhook: (id: string) => [...triggersKeys.webhooks(), id] as const,

  // Dashboard & Logs
  dashboard: () => [...triggersKeys.all, 'dashboard'] as const,
  logs: () => [...triggersKeys.all, 'logs'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type TriggerType = 'THRESHOLD' | 'CHANGE' | 'SCHEDULE' | 'EVENT' | 'COMPOUND';
export type TriggerStatus = 'ACTIVE' | 'PAUSED' | 'DISABLED' | 'ERROR';
export type AlertSeverity = 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
export type EscalationLevel = 'L1' | 'L2' | 'L3' | 'MANAGER' | 'EXECUTIVE';
export type NotificationChannel = 'IN_APP' | 'EMAIL' | 'SMS' | 'SLACK' | 'WEBHOOK' | 'TEAMS';
export type NotificationStatus = 'PENDING' | 'SENT' | 'DELIVERED' | 'READ' | 'FAILED';
export type ConditionOperator = 'EQ' | 'NEQ' | 'GT' | 'GTE' | 'LT' | 'LTE' | 'IN' | 'NOT_IN' | 'CONTAINS' | 'NOT_CONTAINS' | 'BETWEEN' | 'IS_NULL' | 'IS_NOT_NULL';
export type ReportFrequency = 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface Trigger {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  trigger_type: TriggerType;
  status: TriggerStatus;
  source_module: string;
  source_entity?: string | null;
  source_field?: string | null;
  condition: Record<string, unknown>;
  threshold_value?: string | null;
  threshold_operator?: ConditionOperator | null;
  schedule_cron?: string | null;
  schedule_timezone?: string | null;
  severity: AlertSeverity;
  escalation_enabled: boolean;
  escalation_delay_minutes?: number | null;
  escalation_level?: EscalationLevel | null;
  cooldown_minutes: number;
  is_active: boolean;
  last_triggered_at?: string | null;
  trigger_count: number;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface TriggerSubscription {
  id: number;
  tenant_id: string;
  trigger_id: number;
  user_id?: number | null;
  role_code?: string | null;
  group_code?: string | null;
  email_external?: string | null;
  channel: NotificationChannel;
  channel_config?: Record<string, unknown> | null;
  escalation_level: EscalationLevel;
  is_active: boolean;
  created_at: string;
  created_by?: number | null;
}

export interface TriggerEvent {
  id: number;
  tenant_id: string;
  trigger_id: number;
  triggered_at: string;
  triggered_value?: string | null;
  condition_details?: Record<string, unknown> | null;
  severity: AlertSeverity;
  escalation_level: EscalationLevel;
  escalated_at?: string | null;
  resolved: boolean;
  resolved_at?: string | null;
  resolved_by?: number | null;
  resolution_notes?: string | null;
}

export interface Notification {
  id: number;
  tenant_id: string;
  event_id: number;
  user_id?: number | null;
  email?: string | null;
  channel: NotificationChannel;
  subject?: string | null;
  body: string;
  status: NotificationStatus;
  sent_at?: string | null;
  delivered_at?: string | null;
  read_at?: string | null;
  failed_at?: string | null;
  failure_reason?: string | null;
  retry_count: number;
  next_retry_at?: string | null;
}

export interface NotificationTemplate {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  subject_template?: string | null;
  body_template: string;
  body_html?: string | null;
  available_variables?: string[] | null;
  is_active: boolean;
  is_system: boolean;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface ScheduledReport {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  report_type: string;
  report_config?: Record<string, unknown> | null;
  frequency: ReportFrequency;
  schedule_day?: number | null;
  schedule_time?: string | null;
  schedule_timezone: string;
  schedule_cron?: string | null;
  recipients: {
    users?: number[];
    roles?: string[];
    emails?: string[];
  };
  output_format: string;
  is_active: boolean;
  last_generated_at?: string | null;
  next_generation_at?: string | null;
  generation_count: number;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface ReportHistory {
  id: number;
  tenant_id: string;
  report_id: number;
  generated_at: string;
  generated_by?: number | null;
  file_name: string;
  file_path?: string | null;
  file_size?: number | null;
  file_format: string;
  sent_to?: Record<string, unknown> | null;
  sent_at?: string | null;
  success: boolean;
  error_message?: string | null;
}

export interface Webhook {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  url: string;
  method: string;
  headers?: Record<string, string> | null;
  auth_type?: string | null;
  max_retries: number;
  retry_delay_seconds: number;
  is_active: boolean;
  last_success_at?: string | null;
  last_failure_at?: string | null;
  consecutive_failures: number;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface TriggerLog {
  id: number;
  tenant_id: string;
  action: string;
  entity_type: string;
  entity_id?: number | null;
  details?: Record<string, unknown> | null;
  success: boolean;
  error_message?: string | null;
  created_at: string;
}

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

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface TriggerCreate {
  code: string;
  name: string;
  description?: string;
  trigger_type: TriggerType;
  source_module: string;
  source_entity?: string;
  source_field?: string;
  condition: Record<string, unknown>;
  threshold_value?: string;
  threshold_operator?: ConditionOperator;
  schedule_cron?: string;
  schedule_timezone?: string;
  severity?: AlertSeverity;
  escalation_enabled?: boolean;
  escalation_delay_minutes?: number;
  cooldown_minutes?: number;
  action_template_id?: number;
}

export interface TriggerUpdate {
  name?: string;
  description?: string;
  trigger_type?: TriggerType;
  source_module?: string;
  source_entity?: string;
  source_field?: string;
  condition?: Record<string, unknown>;
  threshold_value?: string;
  threshold_operator?: ConditionOperator;
  schedule_cron?: string;
  schedule_timezone?: string;
  severity?: AlertSeverity;
  escalation_enabled?: boolean;
  escalation_delay_minutes?: number;
  cooldown_minutes?: number;
  action_template_id?: number;
  is_active?: boolean;
}

export interface SubscriptionCreate {
  trigger_id: number;
  user_id?: number;
  role_code?: string;
  group_code?: string;
  email_external?: string;
  channel?: NotificationChannel;
  channel_config?: Record<string, unknown>;
  escalation_level?: EscalationLevel;
}

export interface TemplateCreate {
  code: string;
  name: string;
  description?: string;
  subject_template?: string;
  body_template: string;
  body_html?: string;
  available_variables?: string[];
}

export interface TemplateUpdate {
  name?: string;
  description?: string;
  subject_template?: string;
  body_template?: string;
  body_html?: string;
  available_variables?: string[];
  is_active?: boolean;
}

export interface ScheduledReportCreate {
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
  recipients: {
    users?: number[];
    roles?: string[];
    emails?: string[];
  };
  output_format?: string;
}

export interface ScheduledReportUpdate {
  name?: string;
  description?: string;
  report_config?: Record<string, unknown>;
  frequency?: ReportFrequency;
  schedule_day?: number;
  schedule_time?: string;
  schedule_timezone?: string;
  recipients?: {
    users?: number[];
    roles?: string[];
    emails?: string[];
  };
  output_format?: string;
  is_active?: boolean;
}

export interface WebhookCreate {
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

export interface WebhookUpdate {
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

// ============================================================================
// HOOKS - TRIGGERS
// ============================================================================

export function useTriggers(filters?: {
  status?: TriggerStatus;
  trigger_type?: TriggerType;
  source_module?: string;
  severity?: AlertSeverity;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...triggersKeys.list(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.trigger_type) params.append('trigger_type', filters.trigger_type);
      if (filters?.source_module) params.append('source_module', filters.source_module);
      if (filters?.severity) params.append('severity', filters.severity);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ triggers: Trigger[]; total: number }>(
        `/triggers${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useTrigger(id: string) {
  return useQuery({
    queryKey: triggersKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Trigger>(`/triggers/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateTrigger() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TriggerCreate) => {
      return api.post<Trigger>('/triggers', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.list() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.dashboard() });
    },
  });
}

export function useUpdateTrigger() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TriggerUpdate }) => {
      return api.put<Trigger>(`/triggers/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.list() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.detail(id) });
    },
  });
}

export function useDeleteTrigger() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/triggers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.list() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.dashboard() });
    },
  });
}

export function usePauseTrigger() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Trigger>(`/triggers/${id}/pause`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: triggersKeys.list() });
    },
  });
}

export function useResumeTrigger() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Trigger>(`/triggers/${id}/resume`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: triggersKeys.list() });
    },
  });
}

export function useFireTrigger() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: {
      id: string;
      data?: { triggered_value?: string; condition_details?: Record<string, unknown> };
    }) => {
      return api.post<TriggerEvent>(`/triggers/${id}/fire`, data || {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.events() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.dashboard() });
    },
  });
}

export function useTestTrigger() {
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<{ would_trigger: boolean; evaluated_condition: Record<string, unknown> }>(
        `/triggers/${id}/test`
      );
    },
  });
}

// ============================================================================
// HOOKS - EVENTS
// ============================================================================

export function useTriggerEvents(filters?: {
  trigger_id?: number;
  severity?: AlertSeverity;
  resolved?: boolean;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...triggersKeys.events(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.trigger_id) params.append('trigger_id', String(filters.trigger_id));
      if (filters?.severity) params.append('severity', filters.severity);
      if (filters?.resolved !== undefined) params.append('resolved', String(filters.resolved));
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ events: TriggerEvent[]; total: number }>(
        `/triggers/events${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useTriggerEvent(id: string) {
  return useQuery({
    queryKey: triggersKeys.event(id),
    queryFn: async () => {
      const response = await api.get<TriggerEvent>(`/triggers/events/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useResolveEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes?: string }) => {
      return api.post<TriggerEvent>(`/triggers/events/${id}/resolve`, { resolution_notes: notes });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.event(id) });
      queryClient.invalidateQueries({ queryKey: triggersKeys.events() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.dashboard() });
    },
  });
}

export function useEscalateEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, level }: { id: string; level?: EscalationLevel }) => {
      return api.post<TriggerEvent>(`/triggers/events/${id}/escalate`, { level });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.event(id) });
      queryClient.invalidateQueries({ queryKey: triggersKeys.events() });
    },
  });
}

// ============================================================================
// HOOKS - SUBSCRIPTIONS
// ============================================================================

export function useTriggerSubscriptions(triggerId?: string) {
  return useQuery({
    queryKey: triggersKeys.subscriptions(triggerId),
    queryFn: async () => {
      const url = triggerId
        ? `/triggers/${triggerId}/subscriptions`
        : '/triggers/subscriptions';
      const response = await api.get<{ items: TriggerSubscription[] }>(url);
      return response;
    },
  });
}

export function useCreateSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SubscriptionCreate) => {
      return api.post<TriggerSubscription>('/triggers/subscriptions', data);
    },
    onSuccess: (_, { trigger_id }) => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.subscriptions(String(trigger_id)) });
      queryClient.invalidateQueries({ queryKey: triggersKeys.subscriptions() });
    },
  });
}

export function useDeleteSubscription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/triggers/subscriptions/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.subscriptions() });
    },
  });
}

// ============================================================================
// HOOKS - NOTIFICATIONS
// ============================================================================

export function useNotifications(filters?: {
  event_id?: number;
  status?: NotificationStatus;
  channel?: NotificationChannel;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...triggersKeys.notifications(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.event_id) params.append('event_id', String(filters.event_id));
      if (filters?.status) params.append('status', filters.status);
      if (filters?.channel) params.append('channel', filters.channel);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ notifications: Notification[]; total: number; unread_count: number }>(
        `/triggers/notifications${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useMyNotifications(filters?: {
  unread_only?: boolean;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...triggersKeys.myNotifications(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.unread_only) params.append('unread_only', 'true');
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ notifications: Notification[]; total: number; unread_count: number }>(
        `/triggers/notifications/me${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/triggers/notifications/${id}/read`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.notifications() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.myNotifications() });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return api.post('/triggers/notifications/mark-all-read');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.myNotifications() });
    },
  });
}

// ============================================================================
// HOOKS - TEMPLATES
// ============================================================================

export function useNotificationTemplates(filters?: {
  search?: string;
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: [...triggersKeys.templates(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.search) params.append('search', filters.search);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: NotificationTemplate[] }>(
        `/triggers/templates${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useNotificationTemplate(id: string) {
  return useQuery({
    queryKey: triggersKeys.template(id),
    queryFn: async () => {
      const response = await api.get<NotificationTemplate>(`/triggers/templates/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TemplateCreate) => {
      return api.post<NotificationTemplate>('/triggers/templates', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.templates() });
    },
  });
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TemplateUpdate }) => {
      return api.put<NotificationTemplate>(`/triggers/templates/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.templates() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.template(id) });
    },
  });
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/triggers/templates/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.templates() });
    },
  });
}

export function usePreviewTemplate() {
  return useMutation({
    mutationFn: async ({ id, variables }: { id: string; variables: Record<string, unknown> }) => {
      return api.post<{ subject: string; body: string; body_html?: string }>(
        `/triggers/templates/${id}/preview`,
        { variables }
      );
    },
  });
}

// ============================================================================
// HOOKS - SCHEDULED REPORTS
// ============================================================================

export function useScheduledReports(filters?: {
  frequency?: ReportFrequency;
  is_active?: boolean;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...triggersKeys.reports(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.frequency) params.append('frequency', filters.frequency);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ScheduledReport[]; total: number }>(
        `/triggers/reports${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useScheduledReport(id: string) {
  return useQuery({
    queryKey: triggersKeys.report(id),
    queryFn: async () => {
      const response = await api.get<ScheduledReport>(`/triggers/reports/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateScheduledReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ScheduledReportCreate) => {
      return api.post<ScheduledReport>('/triggers/reports', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.reports() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.dashboard() });
    },
  });
}

export function useUpdateScheduledReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ScheduledReportUpdate }) => {
      return api.put<ScheduledReport>(`/triggers/reports/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.reports() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.report(id) });
    },
  });
}

export function useDeleteScheduledReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/triggers/reports/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.reports() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.dashboard() });
    },
  });
}

export function useGenerateReportNow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<ReportHistory>(`/triggers/reports/${id}/generate`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.report(id) });
      queryClient.invalidateQueries({ queryKey: triggersKeys.reportHistory(id) });
    },
  });
}

export function useReportHistory(reportId: string) {
  return useQuery({
    queryKey: triggersKeys.reportHistory(reportId),
    queryFn: async () => {
      const response = await api.get<{ items: ReportHistory[] }>(
        `/triggers/reports/${reportId}/history`
      );
      return response;
    },
    enabled: !!reportId,
  });
}

// ============================================================================
// HOOKS - WEBHOOKS
// ============================================================================

export function useWebhooks(filters?: {
  is_active?: boolean;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...triggersKeys.webhooks(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Webhook[]; total: number }>(
        `/triggers/webhooks${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useWebhook(id: string) {
  return useQuery({
    queryKey: triggersKeys.webhook(id),
    queryFn: async () => {
      const response = await api.get<Webhook>(`/triggers/webhooks/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: WebhookCreate) => {
      return api.post<Webhook>('/triggers/webhooks', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.webhooks() });
    },
  });
}

export function useUpdateWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: WebhookUpdate }) => {
      return api.put<Webhook>(`/triggers/webhooks/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.webhooks() });
      queryClient.invalidateQueries({ queryKey: triggersKeys.webhook(id) });
    },
  });
}

export function useDeleteWebhook() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/triggers/webhooks/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: triggersKeys.webhooks() });
    },
  });
}

export function useTestWebhook() {
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<{
        success: boolean;
        status_code?: number;
        response_time_ms?: number;
        error?: string;
      }>(`/triggers/webhooks/${id}/test`);
    },
  });
}

// ============================================================================
// HOOKS - DASHBOARD & LOGS
// ============================================================================

export function useTriggerDashboard() {
  return useQuery({
    queryKey: triggersKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<TriggerDashboard>('/triggers/dashboard');
      return response;
    },
  });
}

export function useTriggerLogs(filters?: {
  action?: string;
  entity_type?: string;
  success?: boolean;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...triggersKeys.logs(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.action) params.append('action', filters.action);
      if (filters?.entity_type) params.append('entity_type', filters.entity_type);
      if (filters?.success !== undefined) params.append('success', String(filters.success));
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ logs: TriggerLog[]; total: number }>(
        `/triggers/logs${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}
