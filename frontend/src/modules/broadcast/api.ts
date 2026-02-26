/**
 * AZALSCORE - Broadcast API
 * =========================
 * Complete typed API client for Broadcast (Periodic Diffusion) module.
 * Covers: Templates, Recipient Lists, Schedules, Deliveries, Stats
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const broadcastKeys = {
  all: ['broadcast'] as const,
  templates: () => [...broadcastKeys.all, 'templates'] as const,
  template: (id: string) => [...broadcastKeys.templates(), id] as const,
  recipientLists: () => [...broadcastKeys.all, 'recipient-lists'] as const,
  schedules: () => [...broadcastKeys.all, 'schedules'] as const,
  schedule: (id: string) => [...broadcastKeys.schedules(), id] as const,
  deliveries: () => [...broadcastKeys.all, 'deliveries'] as const,
  stats: () => [...broadcastKeys.all, 'stats'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type DeliveryChannel = 'EMAIL' | 'IN_APP' | 'WEBHOOK' | 'PDF_DOWNLOAD' | 'SMS';

export type BroadcastFrequency =
  | 'ONCE' | 'DAILY' | 'WEEKLY' | 'BIWEEKLY'
  | 'MONTHLY' | 'QUARTERLY' | 'YEARLY' | 'CUSTOM';

export type ContentType = 'DIGEST' | 'NEWSLETTER' | 'REPORT' | 'ALERT' | 'KPI_SUMMARY';

export type BroadcastStatus =
  | 'DRAFT' | 'SCHEDULED' | 'ACTIVE' | 'PAUSED'
  | 'COMPLETED' | 'CANCELLED' | 'ERROR';

export type DeliveryStatus =
  | 'PENDING' | 'SENDING' | 'DELIVERED'
  | 'FAILED' | 'BOUNCED' | 'OPENED' | 'CLICKED';

export type RecipientType = 'USER' | 'GROUP' | 'ROLE' | 'EXTERNAL' | 'DYNAMIC';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface BroadcastTemplate {
  id: number;
  tenant_id?: string | null;
  code: string;
  name: string;
  description?: string | null;
  content_type: ContentType;
  subject_template?: string | null;
  body_template?: string | null;
  html_template?: string | null;
  default_channel: DeliveryChannel;
  available_channels?: string[] | null;
  variables?: Record<string, unknown> | null;
  styling?: Record<string, unknown> | null;
  data_sources?: Array<Record<string, unknown>> | null;
  language: string;
  is_active: boolean;
  is_system: boolean;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface RecipientList {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  recipient_type: RecipientType;
  recipients: Array<{
    id?: string;
    email?: string;
    name?: string;
    type: RecipientType;
  }>;
  filter_query?: Record<string, unknown> | null;
  is_dynamic: boolean;
  is_active: boolean;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface BroadcastSchedule {
  id: number;
  tenant_id: string;
  name: string;
  description?: string | null;
  template_id: number;
  recipient_list_id: number;
  frequency: BroadcastFrequency;
  cron_expression?: string | null;
  timezone: string;
  next_run_at?: string | null;
  last_run_at?: string | null;
  start_date: string;
  end_date?: string | null;
  status: BroadcastStatus;
  channel: DeliveryChannel;
  variables?: Record<string, unknown> | null;
  filters?: Record<string, unknown> | null;
  created_by?: number | null;
  created_at: string;
  updated_at: string;
}

export interface BroadcastDelivery {
  id: number;
  tenant_id: string;
  schedule_id?: number | null;
  template_id: number;
  recipient_email: string;
  recipient_name?: string | null;
  channel: DeliveryChannel;
  status: DeliveryStatus;
  subject?: string | null;
  sent_at?: string | null;
  delivered_at?: string | null;
  opened_at?: string | null;
  clicked_at?: string | null;
  failed_at?: string | null;
  failure_reason?: string | null;
  external_id?: string | null;
  created_at: string;
}

export interface BroadcastStats {
  total_schedules: number;
  active_schedules: number;
  total_deliveries: number;
  deliveries_today: number;
  by_status: Record<DeliveryStatus, number>;
  by_channel: Record<DeliveryChannel, number>;
  open_rate: number;
  click_rate: number;
  bounce_rate: number;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface TemplateCreate {
  code: string;
  name: string;
  description?: string;
  content_type: ContentType;
  subject_template?: string;
  body_template?: string;
  html_template?: string;
  default_channel?: DeliveryChannel;
  available_channels?: string[];
  variables?: Record<string, unknown>;
  styling?: Record<string, unknown>;
  data_sources?: Array<Record<string, unknown>>;
  language?: string;
}

export interface TemplateUpdate {
  name?: string;
  description?: string;
  subject_template?: string;
  body_template?: string;
  html_template?: string;
  default_channel?: DeliveryChannel;
  available_channels?: string[];
  variables?: Record<string, unknown>;
  styling?: Record<string, unknown>;
  data_sources?: Array<Record<string, unknown>>;
  language?: string;
  is_active?: boolean;
}

export interface RecipientListCreate {
  code: string;
  name: string;
  description?: string;
  recipient_type: RecipientType;
  recipients?: Array<{ email: string; name?: string }>;
  filter_query?: Record<string, unknown>;
  is_dynamic?: boolean;
}

export interface ScheduleCreate {
  name: string;
  description?: string;
  template_id: number;
  recipient_list_id: number;
  frequency: BroadcastFrequency;
  cron_expression?: string;
  timezone?: string;
  start_date: string;
  end_date?: string;
  channel?: DeliveryChannel;
  variables?: Record<string, unknown>;
  filters?: Record<string, unknown>;
}

export interface ScheduleUpdate {
  name?: string;
  description?: string;
  frequency?: BroadcastFrequency;
  cron_expression?: string;
  timezone?: string;
  end_date?: string;
  status?: BroadcastStatus;
  channel?: DeliveryChannel;
  variables?: Record<string, unknown>;
  filters?: Record<string, unknown>;
}

// ============================================================================
// HOOKS - TEMPLATES
// ============================================================================

export function useBroadcastTemplates(filters?: {
  content_type?: ContentType;
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: [...broadcastKeys.templates(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.content_type) params.append('content_type', filters.content_type);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: BroadcastTemplate[] }>(
        `/broadcast/templates${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useBroadcastTemplate(id: string) {
  return useQuery({
    queryKey: broadcastKeys.template(id),
    queryFn: async () => {
      const response = await api.get<BroadcastTemplate>(`/broadcast/templates/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateBroadcastTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TemplateCreate) => {
      return api.post<BroadcastTemplate>('/broadcast/templates', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.templates() });
    },
  });
}

export function useUpdateBroadcastTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TemplateUpdate }) => {
      return api.put<BroadcastTemplate>(`/broadcast/templates/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.templates() });
      queryClient.invalidateQueries({ queryKey: broadcastKeys.template(id) });
    },
  });
}

export function useDeleteBroadcastTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/broadcast/templates/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.templates() });
    },
  });
}

export function usePreviewTemplate() {
  return useMutation({
    mutationFn: async (data: { template_id: string; variables?: Record<string, unknown> }) => {
      return api.post<{ subject: string; body: string; html: string }>(
        '/broadcast/templates/preview',
        data
      );
    },
  });
}

// ============================================================================
// HOOKS - RECIPIENT LISTS
// ============================================================================

export function useRecipientLists(filters?: { recipient_type?: RecipientType; is_active?: boolean }) {
  return useQuery({
    queryKey: [...broadcastKeys.recipientLists(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.recipient_type) params.append('recipient_type', filters.recipient_type);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: RecipientList[] }>(
        `/broadcast/recipient-lists${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCreateRecipientList() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RecipientListCreate) => {
      return api.post<RecipientList>('/broadcast/recipient-lists', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.recipientLists() });
    },
  });
}

export function useUpdateRecipientList() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<RecipientListCreate> }) => {
      return api.put<RecipientList>(`/broadcast/recipient-lists/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.recipientLists() });
    },
  });
}

export function useDeleteRecipientList() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/broadcast/recipient-lists/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.recipientLists() });
    },
  });
}

export function useRefreshDynamicList() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<{ member_count: number }>(`/broadcast/recipient-lists/${id}/refresh`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.recipientLists() });
    },
  });
}

// ============================================================================
// HOOKS - SCHEDULES
// ============================================================================

export function useBroadcastSchedules(filters?: {
  status?: BroadcastStatus;
  frequency?: BroadcastFrequency;
}) {
  return useQuery({
    queryKey: [...broadcastKeys.schedules(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.frequency) params.append('frequency', filters.frequency);
      const queryString = params.toString();
      const response = await api.get<{ items: BroadcastSchedule[] }>(
        `/broadcast/schedules${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useBroadcastSchedule(id: string) {
  return useQuery({
    queryKey: broadcastKeys.schedule(id),
    queryFn: async () => {
      const response = await api.get<BroadcastSchedule>(`/broadcast/schedules/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateBroadcastSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ScheduleCreate) => {
      return api.post<BroadcastSchedule>('/broadcast/schedules', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.schedules() });
    },
  });
}

export function useUpdateBroadcastSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ScheduleUpdate }) => {
      return api.put<BroadcastSchedule>(`/broadcast/schedules/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.schedules() });
      queryClient.invalidateQueries({ queryKey: broadcastKeys.schedule(id) });
    },
  });
}

export function useDeleteBroadcastSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/broadcast/schedules/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.schedules() });
    },
  });
}

export function usePauseBroadcastSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/broadcast/schedules/${id}/pause`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.schedules() });
      queryClient.invalidateQueries({ queryKey: broadcastKeys.schedule(id) });
    },
  });
}

export function useResumeBroadcastSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/broadcast/schedules/${id}/resume`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.schedules() });
      queryClient.invalidateQueries({ queryKey: broadcastKeys.schedule(id) });
    },
  });
}

export function useTriggerBroadcastNow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<{ delivery_count: number }>(`/broadcast/schedules/${id}/trigger`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.deliveries() });
    },
  });
}

// ============================================================================
// HOOKS - DELIVERIES
// ============================================================================

export function useBroadcastDeliveries(filters?: {
  schedule_id?: string;
  status?: DeliveryStatus;
  channel?: DeliveryChannel;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...broadcastKeys.deliveries(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.schedule_id) params.append('schedule_id', filters.schedule_id);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.channel) params.append('channel', filters.channel);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: BroadcastDelivery[]; total: number }>(
        `/broadcast/deliveries${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useRetryDelivery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/broadcast/deliveries/${id}/retry`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.deliveries() });
    },
  });
}

// ============================================================================
// HOOKS - STATS
// ============================================================================

export function useBroadcastStats(filters?: { from_date?: string; to_date?: string }) {
  return useQuery({
    queryKey: [...broadcastKeys.stats(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const response = await api.get<BroadcastStats>(
        `/broadcast/stats${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

// ============================================================================
// HOOKS - SEND IMMEDIATE
// ============================================================================

export function useSendImmediate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      template_id: string;
      recipients: Array<{ email: string; name?: string }>;
      channel?: DeliveryChannel;
      variables?: Record<string, unknown>;
    }) => {
      return api.post<{ delivery_ids: number[] }>('/broadcast/send', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: broadcastKeys.deliveries() });
    },
  });
}
