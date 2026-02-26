/**
 * AZALSCORE - Profile API
 * ========================
 * Complete typed API client for User Profile management.
 * Covers: Profile, Security, Sessions, API Tokens
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const profileKeys = {
  all: ['profile'] as const,
  current: () => [...profileKeys.all, 'current'] as const,
  sessions: () => [...profileKeys.all, 'sessions'] as const,
  tokens: () => [...profileKeys.all, 'tokens'] as const,
  mfaStatus: () => [...profileKeys.all, 'mfa'] as const,
  activity: () => [...profileKeys.all, 'activity'] as const,
  preferences: () => [...profileKeys.all, 'preferences'] as const,
};

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  phone?: string | null;
  photo?: string | null;
  api_token?: string | null;
  role: string;
  roles: string[];
  permissions: string[];
  language: string;
  timezone: string;
  date_format: string;
  created_at: string;
  updated_at: string;
  last_login_at?: string | null;
}

export interface UserSession {
  id: string;
  device: string;
  browser: string;
  os: string;
  ip_address: string;
  location?: string | null;
  is_current: boolean;
  last_activity_at: string;
  created_at: string;
}

export interface APIToken {
  id: string;
  name: string;
  token_preview: string;
  last_used_at?: string | null;
  expires_at?: string | null;
  permissions: string[];
  created_at: string;
}

export interface MFAStatus {
  enabled: boolean;
  method?: 'totp' | 'sms' | 'email' | null;
  backup_codes_remaining?: number | null;
  last_verified_at?: string | null;
}

export interface ActivityLogEntry {
  id: string;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  date_format: string;
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
    marketing: boolean;
  };
  dashboard: {
    default_page?: string | null;
    widgets: string[];
  };
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface ProfileUpdate {
  name?: string;
  email?: string;
  phone?: string;
  photo?: string;
  language?: string;
  timezone?: string;
  date_format?: string;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface MFASetup {
  method: 'totp' | 'sms' | 'email';
  phone_number?: string;
}

export interface MFASetupResponse {
  secret?: string;
  qr_code?: string;
  backup_codes?: string[];
  verification_required: boolean;
}

export interface MFAVerification {
  code: string;
}

export interface APITokenCreate {
  name: string;
  permissions?: string[];
  expires_in_days?: number;
}

export interface APITokenCreateResponse {
  token: string;
  token_preview: string;
  expires_at?: string | null;
}

// ============================================================================
// HOOKS - PROFILE
// ============================================================================

export function useProfile() {
  return useQuery({
    queryKey: profileKeys.current(),
    queryFn: async () => {
      const response = await api.get<UserProfile>('/web/profile');
      return response;
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ProfileUpdate) => {
      return api.put<UserProfile>('/web/profile', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.current() });
    },
  });
}

export function useUploadProfilePhoto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('photo', file);
      return api.post<{ photo_url: string }>('/web/profile/photo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.current() });
    },
  });
}

export function useDeleteProfilePhoto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return api.delete('/web/profile/photo');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.current() });
    },
  });
}

// ============================================================================
// HOOKS - PASSWORD
// ============================================================================

export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: PasswordChange) => {
      return api.post('/web/profile/change-password', data);
    },
  });
}

export function useRequestPasswordReset() {
  return useMutation({
    mutationFn: async (email: string) => {
      return api.post('/auth/forgot-password', { email });
    },
  });
}

// ============================================================================
// HOOKS - MFA (TWO-FACTOR AUTHENTICATION)
// ============================================================================

export function useMFAStatus() {
  return useQuery({
    queryKey: profileKeys.mfaStatus(),
    queryFn: async () => {
      const response = await api.get<MFAStatus>('/web/profile/mfa');
      return response;
    },
  });
}

export function useSetupMFA() {
  return useMutation({
    mutationFn: async (data: MFASetup) => {
      return api.post<MFASetupResponse>('/web/profile/mfa/setup', data);
    },
  });
}

export function useVerifyMFA() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: MFAVerification) => {
      return api.post('/web/profile/mfa/verify', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.mfaStatus() });
    },
  });
}

export function useDisableMFA() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { password: string; code: string }) => {
      return api.post('/web/profile/mfa/disable', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.mfaStatus() });
    },
  });
}

export function useRegenerateMFABackupCodes() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { password: string }) => {
      return api.post<{ backup_codes: string[] }>('/web/profile/mfa/backup-codes', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.mfaStatus() });
    },
  });
}

// ============================================================================
// HOOKS - SESSIONS
// ============================================================================

export function useSessions() {
  return useQuery({
    queryKey: profileKeys.sessions(),
    queryFn: async () => {
      const response = await api.get<{ items: UserSession[] }>('/web/profile/sessions');
      return response;
    },
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: string) => {
      return api.delete(`/web/profile/sessions/${sessionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.sessions() });
    },
  });
}

export function useRevokeAllSessions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (excludeCurrent: boolean = true) => {
      return api.post('/web/profile/sessions/revoke-all', { exclude_current: excludeCurrent });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.sessions() });
    },
  });
}

// ============================================================================
// HOOKS - API TOKENS
// ============================================================================

export function useAPITokens() {
  return useQuery({
    queryKey: profileKeys.tokens(),
    queryFn: async () => {
      const response = await api.get<{ items: APIToken[] }>('/web/profile/tokens');
      return response;
    },
  });
}

export function useCreateAPIToken() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: APITokenCreate) => {
      return api.post<APITokenCreateResponse>('/web/profile/tokens', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.tokens() });
    },
  });
}

export function useGenerateAPIToken() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return api.post<{ api_token: string }>('/web/profile/generate-token');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.current() });
      queryClient.invalidateQueries({ queryKey: profileKeys.tokens() });
    },
  });
}

export function useRevokeAPIToken() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tokenId: string) => {
      return api.delete(`/web/profile/tokens/${tokenId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.tokens() });
    },
  });
}

// ============================================================================
// HOOKS - ACTIVITY
// ============================================================================

export function useActivityLog(filters?: {
  action?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...profileKeys.activity(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.action) params.append('action', filters.action);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ActivityLogEntry[]; total: number }>(
        `/web/profile/activity${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

// ============================================================================
// HOOKS - PREFERENCES
// ============================================================================

export function usePreferences() {
  return useQuery({
    queryKey: profileKeys.preferences(),
    queryFn: async () => {
      const response = await api.get<UserPreferences>('/web/profile/preferences');
      return response;
    },
  });
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<UserPreferences>) => {
      return api.put<UserPreferences>('/web/profile/preferences', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.preferences() });
    },
  });
}

// ============================================================================
// HOOKS - ACCOUNT ACTIONS
// ============================================================================

export function useExportMyData() {
  return useMutation({
    mutationFn: async (format: 'json' | 'csv') => {
      return api.post<{ download_url: string; expires_at: string }>(
        '/web/profile/export',
        { format }
      );
    },
  });
}

export function useDeleteMyAccount() {
  return useMutation({
    mutationFn: async (data: { password: string; reason?: string }) => {
      return api.post('/web/profile/delete-account', data);
    },
  });
}
