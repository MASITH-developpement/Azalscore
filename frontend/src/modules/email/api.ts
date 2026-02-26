/**
 * AZALSCORE - Email API
 * =====================
 * Complete typed API client for Email module.
 * Covers: Config, Templates, Sending, Tracking, Stats
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const emailKeys = {
  all: ['email'] as const,
  config: () => [...emailKeys.all, 'config'] as const,
  templates: () => [...emailKeys.all, 'templates'] as const,
  template: (id: string) => [...emailKeys.templates(), id] as const,
  sent: () => [...emailKeys.all, 'sent'] as const,
  queued: () => [...emailKeys.all, 'queued'] as const,
  stats: () => [...emailKeys.all, 'stats'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type EmailType =
  | 'transactional' | 'notification' | 'marketing'
  | 'system' | 'verification' | 'password_reset'
  | 'welcome' | 'invoice' | 'reminder' | 'alert';

export type EmailStatus =
  | 'queued' | 'sending' | 'sent' | 'delivered'
  | 'opened' | 'clicked' | 'bounced' | 'failed'
  | 'spam' | 'unsubscribed';

export type EmailProvider = 'smtp' | 'brevo' | 'sendgrid' | 'mailgun' | 'ses';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface EmailConfig {
  id: string;
  tenant_id: string;
  smtp_host?: string | null;
  smtp_port: number;
  smtp_username?: string | null;
  smtp_use_tls: boolean;
  smtp_use_ssl: boolean;
  provider: EmailProvider;
  from_email: string;
  from_name: string;
  reply_to_email?: string | null;
  max_emails_per_hour: number;
  max_emails_per_day: number;
  track_opens: boolean;
  track_clicks: boolean;
  is_active: boolean;
  is_verified: boolean;
  last_verified_at?: string | null;
  created_at: string;
}

export interface EmailTemplate {
  id: string;
  tenant_id?: string | null;
  code: string;
  name: string;
  email_type: EmailType;
  subject: string;
  body_html: string;
  body_text?: string | null;
  variables: string[];
  language: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SentEmail {
  id: string;
  tenant_id: string;
  to_email: string;
  to_name?: string | null;
  cc_emails: string[];
  bcc_emails: string[];
  email_type: EmailType;
  template_code?: string | null;
  subject: string;
  status: EmailStatus;
  sent_at?: string | null;
  delivered_at?: string | null;
  opened_at?: string | null;
  clicked_at?: string | null;
  bounced_at?: string | null;
  bounce_reason?: string | null;
  external_id?: string | null;
  created_at: string;
}

export interface QueuedEmail {
  id: string;
  tenant_id: string;
  to_email: string;
  subject: string;
  email_type: EmailType;
  priority: number;
  scheduled_at?: string | null;
  retry_count: number;
  max_retries: number;
  created_at: string;
}

export interface EmailStats {
  total_sent: number;
  sent_today: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
  failed: number;
  delivery_rate: number;
  open_rate: number;
  click_rate: number;
  bounce_rate: number;
  by_type: Record<EmailType, number>;
  by_status: Record<EmailStatus, number>;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface EmailConfigCreate {
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string;
  smtp_password?: string;
  smtp_use_tls?: boolean;
  smtp_use_ssl?: boolean;
  provider?: EmailProvider;
  api_key?: string;
  api_endpoint?: string;
  from_email: string;
  from_name: string;
  reply_to_email?: string;
  max_emails_per_hour?: number;
  max_emails_per_day?: number;
  track_opens?: boolean;
  track_clicks?: boolean;
}

export interface EmailConfigUpdate {
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string;
  smtp_password?: string;
  smtp_use_tls?: boolean;
  smtp_use_ssl?: boolean;
  provider?: EmailProvider;
  api_key?: string;
  api_endpoint?: string;
  from_email?: string;
  from_name?: string;
  reply_to_email?: string;
  max_emails_per_hour?: number;
  max_emails_per_day?: number;
  track_opens?: boolean;
  track_clicks?: boolean;
  is_active?: boolean;
}

export interface EmailTemplateCreate {
  code: string;
  name: string;
  email_type: EmailType;
  subject: string;
  body_html: string;
  body_text?: string;
  variables?: string[];
  language?: string;
}

export interface EmailTemplateUpdate {
  name?: string;
  subject?: string;
  body_html?: string;
  body_text?: string;
  variables?: string[];
  language?: string;
  is_active?: boolean;
}

export interface SendEmailRequest {
  to_email: string;
  to_name?: string;
  cc_emails?: string[];
  bcc_emails?: string[];
  email_type: EmailType;
  template_code?: string;
  subject?: string;
  body_html?: string;
  body_text?: string;
  variables?: Record<string, unknown>;
  attachments?: Array<{ name: string; content: string; content_type: string }>;
  schedule_at?: string;
  priority?: number;
}

// ============================================================================
// HOOKS - CONFIG
// ============================================================================

export function useEmailConfig() {
  return useQuery({
    queryKey: emailKeys.config(),
    queryFn: async () => {
      const response = await api.get<EmailConfig>('/email/config');
      return response;
    },
  });
}

export function useCreateEmailConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: EmailConfigCreate) => {
      return api.post<EmailConfig>('/email/config', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailKeys.config() });
    },
  });
}

export function useUpdateEmailConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: EmailConfigUpdate) => {
      return api.put<EmailConfig>('/email/config', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailKeys.config() });
    },
  });
}

export function useVerifyEmailConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return api.post<{ verified: boolean; message: string }>('/email/config/verify');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailKeys.config() });
    },
  });
}

export function useTestEmailConfig() {
  return useMutation({
    mutationFn: async (to_email: string) => {
      return api.post<{ success: boolean; message: string }>('/email/config/test', { to_email });
    },
  });
}

// ============================================================================
// HOOKS - TEMPLATES
// ============================================================================

export function useEmailTemplates(filters?: { email_type?: EmailType; is_active?: boolean }) {
  return useQuery({
    queryKey: [...emailKeys.templates(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.email_type) params.append('email_type', filters.email_type);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: EmailTemplate[] }>(
        `/email/templates${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useEmailTemplate(id: string) {
  return useQuery({
    queryKey: emailKeys.template(id),
    queryFn: async () => {
      const response = await api.get<EmailTemplate>(`/email/templates/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useEmailTemplateByCode(code: string) {
  return useQuery({
    queryKey: [...emailKeys.templates(), 'code', code],
    queryFn: async () => {
      const response = await api.get<EmailTemplate>(`/email/templates/code/${code}`);
      return response;
    },
    enabled: !!code,
  });
}

export function useCreateEmailTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: EmailTemplateCreate) => {
      return api.post<EmailTemplate>('/email/templates', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailKeys.templates() });
    },
  });
}

export function useUpdateEmailTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: EmailTemplateUpdate }) => {
      return api.put<EmailTemplate>(`/email/templates/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: emailKeys.templates() });
      queryClient.invalidateQueries({ queryKey: emailKeys.template(id) });
    },
  });
}

export function useDeleteEmailTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/email/templates/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailKeys.templates() });
    },
  });
}

export function usePreviewEmailTemplate() {
  return useMutation({
    mutationFn: async (data: { template_id?: string; code?: string; variables?: Record<string, unknown> }) => {
      return api.post<{ subject: string; body_html: string; body_text: string }>(
        '/email/templates/preview',
        data
      );
    },
  });
}

// ============================================================================
// HOOKS - SENDING
// ============================================================================

export function useSendEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SendEmailRequest) => {
      return api.post<{ email_id: string; status: EmailStatus }>('/email/send', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailKeys.sent() });
      queryClient.invalidateQueries({ queryKey: emailKeys.stats() });
    },
  });
}

export function useSendBulkEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      recipients: Array<{ email: string; name?: string; variables?: Record<string, unknown> }>;
      template_code: string;
      email_type: EmailType;
    }) => {
      return api.post<{ queued_count: number; failed_count: number }>('/email/send-bulk', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailKeys.queued() });
      queryClient.invalidateQueries({ queryKey: emailKeys.stats() });
    },
  });
}

// ============================================================================
// HOOKS - SENT EMAILS
// ============================================================================

export function useSentEmails(filters?: {
  email_type?: EmailType;
  status?: EmailStatus;
  to_email?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...emailKeys.sent(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.email_type) params.append('email_type', filters.email_type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.to_email) params.append('to_email', filters.to_email);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: SentEmail[]; total: number }>(
        `/email/sent${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useResendEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<{ email_id: string }>(`/email/sent/${id}/resend`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailKeys.sent() });
    },
  });
}

// ============================================================================
// HOOKS - QUEUED EMAILS
// ============================================================================

export function useQueuedEmails(filters?: { page?: number; per_page?: number }) {
  return useQuery({
    queryKey: [...emailKeys.queued(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: QueuedEmail[]; total: number }>(
        `/email/queue${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCancelQueuedEmail() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/email/queue/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailKeys.queued() });
    },
  });
}

export function useProcessQueue() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return api.post<{ processed: number; failed: number }>('/email/queue/process');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailKeys.queued() });
      queryClient.invalidateQueries({ queryKey: emailKeys.sent() });
    },
  });
}

// ============================================================================
// HOOKS - STATS
// ============================================================================

export function useEmailStats(filters?: { from_date?: string; to_date?: string }) {
  return useQuery({
    queryKey: [...emailKeys.stats(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const response = await api.get<EmailStats>(
        `/email/stats${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

// ============================================================================
// HOOKS - UNSUBSCRIBE
// ============================================================================

export function useUnsubscribeList() {
  return useQuery({
    queryKey: [...emailKeys.all, 'unsubscribed'],
    queryFn: async () => {
      const response = await api.get<{ items: Array<{ email: string; unsubscribed_at: string }> }>(
        '/email/unsubscribed'
      );
      return response;
    },
  });
}

export function useRemoveFromUnsubscribe() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (email: string) => {
      return api.delete(`/email/unsubscribed/${encodeURIComponent(email)}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...emailKeys.all, 'unsubscribed'] });
    },
  });
}
