/**
 * AZALSCORE - Auto Configuration API
 * ====================================
 * Complete typed API client for Auto Configuration module.
 * Covers: Profiles, Assignments, Overrides, Onboarding, Offboarding
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const autoconfigKeys = {
  all: ['autoconfig'] as const,

  // Profiles
  profiles: () => [...autoconfigKeys.all, 'profiles'] as const,
  profile: (id: string) => [...autoconfigKeys.profiles(), id] as const,
  profileByCode: (code: string) => [...autoconfigKeys.profiles(), 'code', code] as const,

  // Assignments
  assignments: () => [...autoconfigKeys.all, 'assignments'] as const,
  userAssignment: (userId: string) => [...autoconfigKeys.assignments(), 'user', userId] as const,
  userEffectiveConfig: (userId: string) => [...autoconfigKeys.all, 'effective', userId] as const,

  // Overrides
  overrides: () => [...autoconfigKeys.all, 'overrides'] as const,
  override: (id: string) => [...autoconfigKeys.overrides(), id] as const,
  pendingOverrides: () => [...autoconfigKeys.overrides(), 'pending'] as const,

  // Onboarding
  onboardings: () => [...autoconfigKeys.all, 'onboardings'] as const,
  onboarding: (id: string) => [...autoconfigKeys.onboardings(), id] as const,

  // Offboarding
  offboardings: () => [...autoconfigKeys.all, 'offboardings'] as const,
  offboarding: (id: string) => [...autoconfigKeys.offboardings(), id] as const,

  // Logs
  logs: () => [...autoconfigKeys.all, 'logs'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type ProfileLevel = 'EXECUTIVE' | 'MANAGER' | 'SENIOR' | 'STANDARD' | 'JUNIOR' | 'INTERN';
export type OverrideType = 'EXECUTIVE' | 'IT_ADMIN' | 'TEMPORARY' | 'EMERGENCY';
export type OverrideStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'REVOKED';
export type OnboardingStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type OffboardingStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type DepartureType = 'RESIGNATION' | 'TERMINATION' | 'END_OF_CONTRACT' | 'RETIREMENT';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface Profile {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  level: ProfileLevel;
  hierarchy_order: number;
  title_patterns: string[];
  department_patterns: string[];
  default_roles: string[];
  default_permissions: string[];
  default_modules: string[];
  max_data_access_level: number;
  requires_mfa: boolean;
  requires_training: boolean;
  is_active: boolean;
  is_system: boolean;
  priority: number;
  created_at: string;
}

export interface ProfileAssignment {
  id: number;
  tenant_id: string;
  user_id: number;
  profile_id: number;
  profile_code: string;
  profile_name: string;
  job_title?: string | null;
  department?: string | null;
  manager_id?: number | null;
  is_active: boolean;
  is_auto: boolean;
  assigned_at: string;
  assigned_by?: number | null;
}

export interface EffectiveConfig {
  profile_code?: string | null;
  profile_name?: string | null;
  roles: string[];
  permissions: string[];
  modules: string[];
  requires_mfa: boolean;
  data_access_level: number;
  overrides_applied: number;
}

export interface ProfileOverride {
  id: number;
  tenant_id: string;
  user_id: number;
  override_type: OverrideType;
  status: OverrideStatus;
  added_roles?: string[] | null;
  removed_roles?: string[] | null;
  added_permissions?: string[] | null;
  removed_permissions?: string[] | null;
  added_modules?: string[] | null;
  removed_modules?: string[] | null;
  reason: string;
  business_justification?: string | null;
  starts_at?: string | null;
  expires_at?: string | null;
  requested_by: number;
  requested_at: string;
  approved_by?: number | null;
  approved_at?: string | null;
  rejected_by?: number | null;
  rejected_at?: string | null;
  rejection_reason?: string | null;
}

export interface Onboarding {
  id: number;
  tenant_id: string;
  user_id?: number | null;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  job_title: string;
  department?: string | null;
  manager_id?: number | null;
  start_date: string;
  detected_profile_id?: number | null;
  detected_profile_code?: string | null;
  profile_override?: number | null;
  status: OnboardingStatus;
  steps_completed: Record<string, boolean>;
  welcome_email_sent: boolean;
  manager_notified: boolean;
  it_notified: boolean;
  created_at: string;
  completed_at?: string | null;
}

export interface Offboarding {
  id: number;
  tenant_id: string;
  user_id: number;
  departure_date: string;
  departure_type: DepartureType;
  transfer_to_user_id?: number | null;
  transfer_notes?: string | null;
  status: OffboardingStatus;
  steps_completed: Record<string, boolean>;
  account_deactivated: boolean;
  access_revoked: boolean;
  data_archived: boolean;
  data_deleted: boolean;
  manager_notified: boolean;
  it_notified: boolean;
  team_notified: boolean;
  created_at: string;
  completed_at?: string | null;
}

export interface AutoConfigLog {
  id: number;
  tenant_id: string;
  action: string;
  entity_type: string;
  entity_id?: number | null;
  user_id?: number | null;
  source: string;
  triggered_by?: number | null;
  success: boolean;
  error_message?: string | null;
  details?: Record<string, unknown> | null;
  created_at: string;
}

export interface ProfileDetectionResult {
  detected: boolean;
  profile?: Profile | null;
  confidence: number;
}

export interface ExecutionResult {
  steps: string[];
  errors: string[];
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface ProfileCreate {
  code: string;
  name: string;
  description?: string;
  level: ProfileLevel;
  hierarchy_order?: number;
  title_patterns?: string[];
  department_patterns?: string[];
  default_roles: string[];
  default_permissions?: string[];
  default_modules?: string[];
  max_data_access_level?: number;
  requires_mfa?: boolean;
  requires_training?: boolean;
  priority?: number;
}

export interface ProfileUpdate {
  name?: string;
  description?: string;
  title_patterns?: string[];
  department_patterns?: string[];
  default_roles?: string[];
  default_permissions?: string[];
  default_modules?: string[];
  max_data_access_level?: number;
  requires_mfa?: boolean;
  requires_training?: boolean;
  is_active?: boolean;
  priority?: number;
}

export interface ManualAssignmentRequest {
  user_id: number;
  profile_code: string;
  job_title?: string;
  department?: string;
}

export interface AutoAssignmentRequest {
  user_id: number;
  job_title: string;
  department?: string;
  manager_id?: number;
}

export interface OverrideRequest {
  user_id: number;
  override_type: OverrideType;
  reason: string;
  business_justification?: string;
  added_roles?: string[];
  removed_roles?: string[];
  added_permissions?: string[];
  removed_permissions?: string[];
  added_modules?: string[];
  removed_modules?: string[];
  expires_at?: string;
}

export interface OnboardingCreate {
  email: string;
  first_name?: string;
  last_name?: string;
  job_title: string;
  department?: string;
  manager_id?: number;
  start_date: string;
  profile_override?: number;
}

export interface OffboardingCreate {
  user_id: number;
  departure_date: string;
  departure_type: DepartureType;
  transfer_to_user_id?: number;
  transfer_notes?: string;
}

// ============================================================================
// HOOKS - PROFILES
// ============================================================================

export function useProfiles(filters?: {
  level?: ProfileLevel;
  is_active?: boolean;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...autoconfigKeys.profiles(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.level) params.append('level', filters.level);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Profile[]; total: number }>(
        `/autoconfig/profiles${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useProfile(id: string) {
  return useQuery({
    queryKey: autoconfigKeys.profile(id),
    queryFn: async () => {
      const response = await api.get<Profile>(`/autoconfig/profiles/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useProfileByCode(code: string) {
  return useQuery({
    queryKey: autoconfigKeys.profileByCode(code),
    queryFn: async () => {
      const response = await api.get<Profile>(`/autoconfig/profiles/code/${code}`);
      return response;
    },
    enabled: !!code,
  });
}

export function useCreateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ProfileCreate) => {
      return api.post<Profile>('/autoconfig/profiles', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.profiles() });
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ProfileUpdate }) => {
      return api.put<Profile>(`/autoconfig/profiles/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.profiles() });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.profile(id) });
    },
  });
}

export function useDeleteProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/autoconfig/profiles/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.profiles() });
    },
  });
}

export function useDetectProfile() {
  return useMutation({
    mutationFn: async ({ jobTitle, department }: { jobTitle: string; department?: string }) => {
      return api.post<ProfileDetectionResult>('/autoconfig/profiles/detect', {
        job_title: jobTitle,
        department,
      });
    },
  });
}

// ============================================================================
// HOOKS - ASSIGNMENTS
// ============================================================================

export function useAssignments(filters?: {
  profile_id?: number;
  is_active?: boolean;
  is_auto?: boolean;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...autoconfigKeys.assignments(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.profile_id) params.append('profile_id', String(filters.profile_id));
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters?.is_auto !== undefined) params.append('is_auto', String(filters.is_auto));
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ProfileAssignment[]; total: number }>(
        `/autoconfig/assignments${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useUserAssignment(userId: string) {
  return useQuery({
    queryKey: autoconfigKeys.userAssignment(userId),
    queryFn: async () => {
      const response = await api.get<ProfileAssignment>(`/autoconfig/assignments/user/${userId}`);
      return response;
    },
    enabled: !!userId,
  });
}

export function useUserEffectiveConfig(userId: string) {
  return useQuery({
    queryKey: autoconfigKeys.userEffectiveConfig(userId),
    queryFn: async () => {
      const response = await api.get<EffectiveConfig>(`/autoconfig/effective/${userId}`);
      return response;
    },
    enabled: !!userId,
  });
}

export function useAssignProfileManually() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ManualAssignmentRequest) => {
      return api.post<ProfileAssignment>('/autoconfig/assignments/manual', data);
    },
    onSuccess: (_, { user_id }) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.assignments() });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.userAssignment(String(user_id)) });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.userEffectiveConfig(String(user_id)) });
    },
  });
}

export function useAssignProfileAuto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: AutoAssignmentRequest) => {
      return api.post<ProfileAssignment>('/autoconfig/assignments/auto', data);
    },
    onSuccess: (_, { user_id }) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.assignments() });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.userAssignment(String(user_id)) });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.userEffectiveConfig(String(user_id)) });
    },
  });
}

export function useRemoveAssignment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      return api.delete(`/autoconfig/assignments/user/${userId}`);
    },
    onSuccess: (_, userId) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.assignments() });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.userAssignment(userId) });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.userEffectiveConfig(userId) });
    },
  });
}

// ============================================================================
// HOOKS - OVERRIDES
// ============================================================================

export function useOverrides(filters?: {
  user_id?: number;
  override_type?: OverrideType;
  status?: OverrideStatus;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...autoconfigKeys.overrides(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.user_id) params.append('user_id', String(filters.user_id));
      if (filters?.override_type) params.append('override_type', filters.override_type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ProfileOverride[]; total: number }>(
        `/autoconfig/overrides${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function usePendingOverrides() {
  return useQuery({
    queryKey: autoconfigKeys.pendingOverrides(),
    queryFn: async () => {
      const response = await api.get<{ items: ProfileOverride[]; total: number }>(
        '/autoconfig/overrides?status=PENDING'
      );
      return response;
    },
  });
}

export function useOverride(id: string) {
  return useQuery({
    queryKey: autoconfigKeys.override(id),
    queryFn: async () => {
      const response = await api.get<ProfileOverride>(`/autoconfig/overrides/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useRequestOverride() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OverrideRequest) => {
      return api.post<ProfileOverride>('/autoconfig/overrides', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.overrides() });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.pendingOverrides() });
    },
  });
}

export function useApproveOverride() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<ProfileOverride>(`/autoconfig/overrides/${id}/approve`);
    },
    onSuccess: (result, id) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.overrides() });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.override(id) });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.pendingOverrides() });
      if (result.data?.user_id) {
        queryClient.invalidateQueries({ queryKey: autoconfigKeys.userEffectiveConfig(String(result.data.user_id)) });
      }
    },
  });
}

export function useRejectOverride() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.post<ProfileOverride>(`/autoconfig/overrides/${id}/reject`, { rejection_reason: reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.overrides() });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.override(id) });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.pendingOverrides() });
    },
  });
}

export function useRevokeOverride() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<ProfileOverride>(`/autoconfig/overrides/${id}/revoke`);
    },
    onSuccess: (result, id) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.overrides() });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.override(id) });
      if (result.data?.user_id) {
        queryClient.invalidateQueries({ queryKey: autoconfigKeys.userEffectiveConfig(String(result.data.user_id)) });
      }
    },
  });
}

// ============================================================================
// HOOKS - ONBOARDING
// ============================================================================

export function useOnboardings(filters?: {
  status?: OnboardingStatus;
  from_date?: string;
  to_date?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...autoconfigKeys.onboardings(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Onboarding[]; total: number }>(
        `/autoconfig/onboardings${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useOnboarding(id: string) {
  return useQuery({
    queryKey: autoconfigKeys.onboarding(id),
    queryFn: async () => {
      const response = await api.get<Onboarding>(`/autoconfig/onboardings/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateOnboarding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OnboardingCreate) => {
      return api.post<Onboarding>('/autoconfig/onboardings', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.onboardings() });
    },
  });
}

export function useExecuteOnboarding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<ExecutionResult>(`/autoconfig/onboardings/${id}/execute`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.onboarding(id) });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.onboardings() });
    },
  });
}

export function useCancelOnboarding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Onboarding>(`/autoconfig/onboardings/${id}/cancel`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.onboarding(id) });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.onboardings() });
    },
  });
}

export function useResendWelcomeEmail() {
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/autoconfig/onboardings/${id}/resend-welcome`);
    },
  });
}

// ============================================================================
// HOOKS - OFFBOARDING
// ============================================================================

export function useOffboardings(filters?: {
  status?: OffboardingStatus;
  departure_type?: DepartureType;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...autoconfigKeys.offboardings(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.departure_type) params.append('departure_type', filters.departure_type);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Offboarding[]; total: number }>(
        `/autoconfig/offboardings${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useOffboarding(id: string) {
  return useQuery({
    queryKey: autoconfigKeys.offboarding(id),
    queryFn: async () => {
      const response = await api.get<Offboarding>(`/autoconfig/offboardings/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateOffboarding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OffboardingCreate) => {
      return api.post<Offboarding>('/autoconfig/offboardings', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.offboardings() });
    },
  });
}

export function useExecuteOffboarding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<ExecutionResult>(`/autoconfig/offboardings/${id}/execute`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.offboarding(id) });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.offboardings() });
    },
  });
}

export function useCancelOffboarding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Offboarding>(`/autoconfig/offboardings/${id}/cancel`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.offboarding(id) });
      queryClient.invalidateQueries({ queryKey: autoconfigKeys.offboardings() });
    },
  });
}

// ============================================================================
// HOOKS - LOGS
// ============================================================================

export function useAutoConfigLogs(filters?: {
  action?: string;
  entity_type?: string;
  user_id?: number;
  success?: boolean;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...autoconfigKeys.logs(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.action) params.append('action', filters.action);
      if (filters?.entity_type) params.append('entity_type', filters.entity_type);
      if (filters?.user_id) params.append('user_id', String(filters.user_id));
      if (filters?.success !== undefined) params.append('success', String(filters.success));
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: AutoConfigLog[]; total: number; page: number; page_size: number }>(
        `/autoconfig/logs${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}
