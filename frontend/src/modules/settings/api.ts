/**
 * AZALSCORE - Settings API
 * =========================
 * Complete typed API client for Application Settings.
 * Covers: General Settings, Notifications, Integrations, Modules, Email, Security
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const settingsKeys = {
  all: ['settings'] as const,
  general: () => [...settingsKeys.all, 'general'] as const,
  company: () => [...settingsKeys.all, 'company'] as const,
  notifications: () => [...settingsKeys.all, 'notifications'] as const,
  email: () => [...settingsKeys.all, 'email'] as const,
  security: () => [...settingsKeys.all, 'security'] as const,
  integrations: () => [...settingsKeys.all, 'integrations'] as const,
  integration: (id: string) => [...settingsKeys.integrations(), id] as const,
  modules: () => [...settingsKeys.all, 'modules'] as const,
  branding: () => [...settingsKeys.all, 'branding'] as const,
  localization: () => [...settingsKeys.all, 'localization'] as const,
  billing: () => [...settingsKeys.all, 'billing'] as const,
};

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface GeneralSettings {
  company_name: string;
  company_legal_name?: string | null;
  timezone: string;
  language: string;
  date_format: string;
  time_format: string;
  currency: string;
  fiscal_year_start: string;
  week_start: 'monday' | 'sunday';
}

export interface CompanySettings {
  id: string;
  name: string;
  legal_name?: string | null;
  registration_number?: string | null;
  vat_number?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  postal_code?: string | null;
  country: string;
  phone?: string | null;
  email?: string | null;
  website?: string | null;
  logo_url?: string | null;
  favicon_url?: string | null;
}

export interface NotificationSettings {
  email_notifications: boolean;
  push_notifications: boolean;
  sms_notifications: boolean;
  marketing_emails: boolean;
  digest_frequency: 'none' | 'daily' | 'weekly' | 'monthly';
  notification_types: Record<string, {
    email: boolean;
    push: boolean;
    in_app: boolean;
  }>;
}

export interface EmailSettings {
  from_name: string;
  from_email: string;
  reply_to?: string | null;
  smtp_host?: string | null;
  smtp_port?: number | null;
  smtp_username?: string | null;
  smtp_encryption?: 'none' | 'ssl' | 'tls' | null;
  use_custom_smtp: boolean;
  email_footer?: string | null;
  signature_template?: string | null;
}

export interface SecuritySettings {
  password_min_length: number;
  password_require_uppercase: boolean;
  password_require_lowercase: boolean;
  password_require_number: boolean;
  password_require_special: boolean;
  password_expiry_days?: number | null;
  mfa_required: boolean;
  mfa_methods: string[];
  session_timeout_minutes: number;
  max_login_attempts: number;
  lockout_duration_minutes: number;
  ip_whitelist?: string[] | null;
  allowed_domains?: string[] | null;
}

export interface Integration {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  category: string;
  icon?: string | null;
  is_enabled: boolean;
  is_configured: boolean;
  config?: Record<string, unknown> | null;
  last_sync_at?: string | null;
  status: 'connected' | 'disconnected' | 'error';
  error_message?: string | null;
}

export interface ModuleConfig {
  code: string;
  name: string;
  description?: string | null;
  is_enabled: boolean;
  is_core: boolean;
  config?: Record<string, unknown> | null;
  dependencies: string[];
  dependents: string[];
}

export interface BrandingSettings {
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  logo_url?: string | null;
  logo_dark_url?: string | null;
  favicon_url?: string | null;
  custom_css?: string | null;
  login_background?: string | null;
  app_name?: string | null;
}

export interface LocalizationSettings {
  default_language: string;
  available_languages: string[];
  default_timezone: string;
  default_currency: string;
  date_format: string;
  time_format: string;
  number_format: {
    decimal_separator: string;
    thousands_separator: string;
    decimal_places: number;
  };
}

export interface BillingSettings {
  plan: string;
  billing_cycle: 'monthly' | 'yearly';
  billing_email?: string | null;
  billing_address?: {
    line1?: string;
    line2?: string;
    city?: string;
    postal_code?: string;
    country?: string;
  } | null;
  payment_method?: {
    type: 'card' | 'sepa' | 'invoice';
    last4?: string;
    brand?: string;
  } | null;
  next_billing_date?: string | null;
  cancel_at_period_end: boolean;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface GeneralSettingsUpdate {
  company_name?: string;
  timezone?: string;
  language?: string;
  date_format?: string;
  time_format?: string;
  currency?: string;
  fiscal_year_start?: string;
  week_start?: 'monday' | 'sunday';
}

export interface CompanySettingsUpdate {
  name?: string;
  legal_name?: string;
  registration_number?: string;
  vat_number?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  phone?: string;
  email?: string;
  website?: string;
}

export interface NotificationSettingsUpdate {
  email_notifications?: boolean;
  push_notifications?: boolean;
  sms_notifications?: boolean;
  marketing_emails?: boolean;
  digest_frequency?: 'none' | 'daily' | 'weekly' | 'monthly';
  notification_types?: Record<string, {
    email: boolean;
    push: boolean;
    in_app: boolean;
  }>;
}

export interface EmailSettingsUpdate {
  from_name?: string;
  from_email?: string;
  reply_to?: string;
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string;
  smtp_password?: string;
  smtp_encryption?: 'none' | 'ssl' | 'tls';
  use_custom_smtp?: boolean;
  email_footer?: string;
  signature_template?: string;
}

export interface SecuritySettingsUpdate {
  password_min_length?: number;
  password_require_uppercase?: boolean;
  password_require_lowercase?: boolean;
  password_require_number?: boolean;
  password_require_special?: boolean;
  password_expiry_days?: number;
  mfa_required?: boolean;
  mfa_methods?: string[];
  session_timeout_minutes?: number;
  max_login_attempts?: number;
  lockout_duration_minutes?: number;
  ip_whitelist?: string[];
  allowed_domains?: string[];
}

export interface IntegrationConfig {
  api_key?: string;
  api_secret?: string;
  webhook_url?: string;
  settings?: Record<string, unknown>;
}

export interface BrandingSettingsUpdate {
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  custom_css?: string;
  login_background?: string;
  app_name?: string;
}

// ============================================================================
// HOOKS - GENERAL SETTINGS
// ============================================================================

export function useGeneralSettings() {
  return useQuery({
    queryKey: settingsKeys.general(),
    queryFn: async () => {
      const response = await api.get<GeneralSettings>('/settings/general');
      return response;
    },
  });
}

export function useUpdateGeneralSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: GeneralSettingsUpdate) => {
      return api.put<GeneralSettings>('/settings/general', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.general() });
    },
  });
}

// ============================================================================
// HOOKS - COMPANY SETTINGS
// ============================================================================

export function useCompanySettings() {
  return useQuery({
    queryKey: settingsKeys.company(),
    queryFn: async () => {
      const response = await api.get<CompanySettings>('/settings/company');
      return response;
    },
  });
}

export function useUpdateCompanySettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CompanySettingsUpdate) => {
      return api.put<CompanySettings>('/settings/company', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.company() });
    },
  });
}

export function useUploadCompanyLogo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, type }: { file: File; type: 'logo' | 'favicon' }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('type', type);
      return api.post<{ url: string }>('/settings/company/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.company() });
      queryClient.invalidateQueries({ queryKey: settingsKeys.branding() });
    },
  });
}

// ============================================================================
// HOOKS - NOTIFICATION SETTINGS
// ============================================================================

export function useNotificationSettings() {
  return useQuery({
    queryKey: settingsKeys.notifications(),
    queryFn: async () => {
      const response = await api.get<NotificationSettings>('/settings/notifications');
      return response;
    },
  });
}

export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: NotificationSettingsUpdate) => {
      return api.put<NotificationSettings>('/settings/notifications', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.notifications() });
    },
  });
}

// ============================================================================
// HOOKS - EMAIL SETTINGS
// ============================================================================

export function useEmailSettings() {
  return useQuery({
    queryKey: settingsKeys.email(),
    queryFn: async () => {
      const response = await api.get<EmailSettings>('/settings/email');
      return response;
    },
  });
}

export function useUpdateEmailSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: EmailSettingsUpdate) => {
      return api.put<EmailSettings>('/settings/email', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.email() });
    },
  });
}

export function useTestEmailSettings() {
  return useMutation({
    mutationFn: async (recipientEmail: string) => {
      return api.post<{ success: boolean; message: string }>(
        '/settings/email/test',
        { recipient: recipientEmail }
      );
    },
  });
}

// ============================================================================
// HOOKS - SECURITY SETTINGS
// ============================================================================

export function useSecuritySettings() {
  return useQuery({
    queryKey: settingsKeys.security(),
    queryFn: async () => {
      const response = await api.get<SecuritySettings>('/settings/security');
      return response;
    },
  });
}

export function useUpdateSecuritySettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SecuritySettingsUpdate) => {
      return api.put<SecuritySettings>('/settings/security', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.security() });
    },
  });
}

// ============================================================================
// HOOKS - INTEGRATIONS
// ============================================================================

export function useIntegrations(category?: string) {
  return useQuery({
    queryKey: [...settingsKeys.integrations(), category],
    queryFn: async () => {
      const url = category
        ? `/settings/integrations?category=${category}`
        : '/settings/integrations';
      const response = await api.get<{ items: Integration[] }>(url);
      return response;
    },
  });
}

export function useIntegration(id: string) {
  return useQuery({
    queryKey: settingsKeys.integration(id),
    queryFn: async () => {
      const response = await api.get<Integration>(`/settings/integrations/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useConfigureIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, config }: { id: string; config: IntegrationConfig }) => {
      return api.put<Integration>(`/settings/integrations/${id}`, config);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.integrations() });
      queryClient.invalidateQueries({ queryKey: settingsKeys.integration(id) });
    },
  });
}

export function useEnableIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Integration>(`/settings/integrations/${id}/enable`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.integrations() });
      queryClient.invalidateQueries({ queryKey: settingsKeys.integration(id) });
    },
  });
}

export function useDisableIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Integration>(`/settings/integrations/${id}/disable`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.integrations() });
      queryClient.invalidateQueries({ queryKey: settingsKeys.integration(id) });
    },
  });
}

export function useSyncIntegration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<{ success: boolean; message: string }>(
        `/settings/integrations/${id}/sync`
      );
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.integration(id) });
    },
  });
}

export function useTestIntegration() {
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<{ success: boolean; message: string }>(
        `/settings/integrations/${id}/test`
      );
    },
  });
}

// ============================================================================
// HOOKS - MODULES
// ============================================================================

export function useModules() {
  return useQuery({
    queryKey: settingsKeys.modules(),
    queryFn: async () => {
      const response = await api.get<{ items: ModuleConfig[] }>('/settings/modules');
      return response;
    },
  });
}

export function useEnableModule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ code, config }: { code: string; config?: Record<string, unknown> }) => {
      return api.post<ModuleConfig>(`/settings/modules/${code}/enable`, { config });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.modules() });
    },
  });
}

export function useDisableModule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (code: string) => {
      return api.post<ModuleConfig>(`/settings/modules/${code}/disable`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.modules() });
    },
  });
}

export function useUpdateModuleConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ code, config }: { code: string; config: Record<string, unknown> }) => {
      return api.put<ModuleConfig>(`/settings/modules/${code}/config`, config);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.modules() });
    },
  });
}

// ============================================================================
// HOOKS - BRANDING
// ============================================================================

export function useBrandingSettings() {
  return useQuery({
    queryKey: settingsKeys.branding(),
    queryFn: async () => {
      const response = await api.get<BrandingSettings>('/settings/branding');
      return response;
    },
  });
}

export function useUpdateBrandingSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BrandingSettingsUpdate) => {
      return api.put<BrandingSettings>('/settings/branding', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.branding() });
    },
  });
}

export function useUploadBrandingAsset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, type }: { file: File; type: 'logo' | 'logo_dark' | 'favicon' | 'login_background' }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('type', type);
      return api.post<{ url: string }>('/settings/branding/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.branding() });
    },
  });
}

// ============================================================================
// HOOKS - LOCALIZATION
// ============================================================================

export function useLocalizationSettings() {
  return useQuery({
    queryKey: settingsKeys.localization(),
    queryFn: async () => {
      const response = await api.get<LocalizationSettings>('/settings/localization');
      return response;
    },
  });
}

export function useUpdateLocalizationSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<LocalizationSettings>) => {
      return api.put<LocalizationSettings>('/settings/localization', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.localization() });
    },
  });
}

// ============================================================================
// HOOKS - BILLING
// ============================================================================

export function useBillingSettings() {
  return useQuery({
    queryKey: settingsKeys.billing(),
    queryFn: async () => {
      const response = await api.get<BillingSettings>('/settings/billing');
      return response;
    },
  });
}

export function useUpdateBillingSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<BillingSettings>) => {
      return api.put<BillingSettings>('/settings/billing', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.billing() });
    },
  });
}

export function useGetBillingPortalUrl() {
  return useMutation({
    mutationFn: async () => {
      return api.post<{ url: string }>('/settings/billing/portal');
    },
  });
}

// ============================================================================
// HOOKS - EXPORT/IMPORT
// ============================================================================

export function useExportSettings() {
  return useMutation({
    mutationFn: async () => {
      return api.post<{ download_url: string; expires_at: string }>('/settings/export');
    },
  });
}

export function useImportSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post<{ success: boolean; imported: string[] }>('/settings/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.all });
    },
  });
}
