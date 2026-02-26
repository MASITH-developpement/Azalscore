/**
 * AZALSCORE - IAM API
 * ===================
 * Complete typed API client for IAM (Identity & Access Management) module.
 * Covers: Users, Roles, Permissions, Groups, Sessions, MFA
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const iamKeys = {
  all: ['iam'] as const,
  users: () => [...iamKeys.all, 'users'] as const,
  user: (id: string) => [...iamKeys.users(), id] as const,
  roles: () => [...iamKeys.all, 'roles'] as const,
  role: (id: string) => [...iamKeys.roles(), id] as const,
  permissions: () => [...iamKeys.all, 'permissions'] as const,
  groups: () => [...iamKeys.all, 'groups'] as const,
  group: (id: string) => [...iamKeys.groups(), id] as const,
  sessions: () => [...iamKeys.all, 'sessions'] as const,
  apiKeys: () => [...iamKeys.all, 'api-keys'] as const,
  auditLogs: () => [...iamKeys.all, 'audit-logs'] as const,
};

// ============================================================================
// TYPES - USERS
// ============================================================================

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  username?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  display_name?: string | null;
  phone?: string | null;
  job_title?: string | null;
  department?: string | null;
  locale: string;
  timezone: string;
  default_view?: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_locked: boolean;
  mfa_enabled: boolean;
  created_at: string;
  last_login_at?: string | null;
  roles: string[];
  groups: string[];
}

export interface UserCreate {
  email: string;
  password: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  job_title?: string;
  department?: string;
  locale?: string;
  timezone?: string;
  role_codes?: string[];
  group_codes?: string[];
}

export interface UserUpdate {
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  job_title?: string;
  department?: string;
  locale?: string;
  timezone?: string;
  default_view?: string;
  is_active?: boolean;
}

// ============================================================================
// TYPES - ROLES
// ============================================================================

export interface Permission {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  module: string;
  action: string;
  is_system: boolean;
}

export interface Role {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  is_system: boolean;
  is_active: boolean;
  permissions: string[];
  user_count: number;
  created_at: string;
}

export interface RoleCreate {
  code: string;
  name: string;
  description?: string;
  permission_codes: string[];
}

export interface RoleUpdate {
  name?: string;
  description?: string;
  permission_codes?: string[];
  is_active?: boolean;
}

// ============================================================================
// TYPES - GROUPS
// ============================================================================

export interface Group {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  parent_id?: string | null;
  is_active: boolean;
  member_count: number;
  roles: string[];
  created_at: string;
}

export interface GroupCreate {
  code: string;
  name: string;
  description?: string;
  parent_id?: string;
  role_codes?: string[];
}

export interface GroupUpdate {
  name?: string;
  description?: string;
  parent_id?: string;
  role_codes?: string[];
  is_active?: boolean;
}

// ============================================================================
// TYPES - SESSIONS & API KEYS
// ============================================================================

export interface Session {
  id: string;
  user_id: string;
  user_email: string;
  ip_address: string;
  user_agent: string;
  device_type?: string | null;
  location?: string | null;
  is_current: boolean;
  created_at: string;
  last_active_at: string;
  expires_at: string;
}

export interface ApiKey {
  id: string;
  tenant_id: string;
  name: string;
  key_prefix: string;
  permissions: string[];
  rate_limit: number;
  is_active: boolean;
  last_used_at?: string | null;
  expires_at?: string | null;
  created_at: string;
  created_by: string;
}

export interface ApiKeyCreate {
  name: string;
  permission_codes?: string[];
  rate_limit?: number;
  expires_in_days?: number;
}

// ============================================================================
// TYPES - AUDIT
// ============================================================================

export interface IAMAuditLog {
  id: string;
  tenant_id: string;
  user_id?: string | null;
  user_email?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  details?: Record<string, unknown> | null;
  ip_address?: string | null;
  user_agent?: string | null;
  success: boolean;
  error_message?: string | null;
  created_at: string;
}

// ============================================================================
// HOOKS - USERS
// ============================================================================

export function useUsers(filters?: {
  search?: string;
  role?: string;
  group?: string;
  is_active?: boolean;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...iamKeys.users(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.search) params.append('search', filters.search);
      if (filters?.role) params.append('role', filters.role);
      if (filters?.group) params.append('group', filters.group);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: User[]; total: number; pages: number }>(
        `/iam/users${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useUser(id: string) {
  return useQuery({
    queryKey: iamKeys.user(id),
    queryFn: async () => {
      const response = await api.get<User>(`/iam/users/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCurrentUser() {
  return useQuery({
    queryKey: [...iamKeys.users(), 'me'],
    queryFn: async () => {
      const response = await api.get<User>('/iam/users/me');
      return response;
    },
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: UserCreate) => {
      return api.post<User>('/iam/users', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.users() });
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UserUpdate }) => {
      return api.put<User>(`/iam/users/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.users() });
      queryClient.invalidateQueries({ queryKey: iamKeys.user(id) });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/iam/users/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.users() });
    },
  });
}

export function useActivateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/iam/users/${id}/activate`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.users() });
      queryClient.invalidateQueries({ queryKey: iamKeys.user(id) });
    },
  });
}

export function useDeactivateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/iam/users/${id}/deactivate`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.users() });
      queryClient.invalidateQueries({ queryKey: iamKeys.user(id) });
    },
  });
}

export function useLockUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      return api.post(`/iam/users/${id}/lock`, { reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.users() });
      queryClient.invalidateQueries({ queryKey: iamKeys.user(id) });
    },
  });
}

export function useUnlockUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/iam/users/${id}/unlock`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.users() });
      queryClient.invalidateQueries({ queryKey: iamKeys.user(id) });
    },
  });
}

export function useResetUserPassword() {
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<{ temporary_password: string }>(`/iam/users/${id}/reset-password`);
    },
  });
}

export function useAssignUserRoles() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, roleCodes }: { id: string; roleCodes: string[] }) => {
      return api.post(`/iam/users/${id}/roles`, { role_codes: roleCodes });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.user(id) });
    },
  });
}

export function useAssignUserGroups() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, groupCodes }: { id: string; groupCodes: string[] }) => {
      return api.post(`/iam/users/${id}/groups`, { group_codes: groupCodes });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.user(id) });
    },
  });
}

// ============================================================================
// HOOKS - ROLES
// ============================================================================

export function useRoles(filters?: { is_active?: boolean }) {
  return useQuery({
    queryKey: [...iamKeys.roles(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: Role[] }>(
        `/iam/roles${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useRole(id: string) {
  return useQuery({
    queryKey: iamKeys.role(id),
    queryFn: async () => {
      const response = await api.get<Role>(`/iam/roles/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RoleCreate) => {
      return api.post<Role>('/iam/roles', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.roles() });
    },
  });
}

export function useUpdateRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: RoleUpdate }) => {
      return api.put<Role>(`/iam/roles/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.roles() });
      queryClient.invalidateQueries({ queryKey: iamKeys.role(id) });
    },
  });
}

export function useDeleteRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/iam/roles/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.roles() });
    },
  });
}

// ============================================================================
// HOOKS - PERMISSIONS
// ============================================================================

export function usePermissions(filters?: { module?: string }) {
  return useQuery({
    queryKey: [...iamKeys.permissions(), filters],
    queryFn: async () => {
      const params = filters?.module ? `?module=${filters.module}` : '';
      const response = await api.get<{ items: Permission[] }>(`/iam/permissions${params}`);
      return response;
    },
  });
}

// ============================================================================
// HOOKS - GROUPS
// ============================================================================

export function useGroups(filters?: { is_active?: boolean }) {
  return useQuery({
    queryKey: [...iamKeys.groups(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: Group[] }>(
        `/iam/groups${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useGroup(id: string) {
  return useQuery({
    queryKey: iamKeys.group(id),
    queryFn: async () => {
      const response = await api.get<Group>(`/iam/groups/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: GroupCreate) => {
      return api.post<Group>('/iam/groups', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.groups() });
    },
  });
}

export function useUpdateGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: GroupUpdate }) => {
      return api.put<Group>(`/iam/groups/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.groups() });
      queryClient.invalidateQueries({ queryKey: iamKeys.group(id) });
    },
  });
}

export function useDeleteGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/iam/groups/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.groups() });
    },
  });
}

export function useAddGroupMembers() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, userIds }: { id: string; userIds: string[] }) => {
      return api.post(`/iam/groups/${id}/members`, { user_ids: userIds });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.group(id) });
    },
  });
}

export function useRemoveGroupMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ groupId, userId }: { groupId: string; userId: string }) => {
      return api.delete(`/iam/groups/${groupId}/members/${userId}`);
    },
    onSuccess: (_, { groupId }) => {
      queryClient.invalidateQueries({ queryKey: iamKeys.group(groupId) });
    },
  });
}

// ============================================================================
// HOOKS - SESSIONS
// ============================================================================

export function useSessions(userId?: string) {
  return useQuery({
    queryKey: [...iamKeys.sessions(), userId],
    queryFn: async () => {
      const params = userId ? `?user_id=${userId}` : '';
      const response = await api.get<{ items: Session[] }>(`/iam/sessions${params}`);
      return response;
    },
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (sessionId: string) => {
      return api.delete(`/iam/sessions/${sessionId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.sessions() });
    },
  });
}

export function useRevokeAllSessions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (userId: string) => {
      return api.post(`/iam/users/${userId}/revoke-sessions`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.sessions() });
    },
  });
}

// ============================================================================
// HOOKS - API KEYS
// ============================================================================

export function useApiKeys() {
  return useQuery({
    queryKey: iamKeys.apiKeys(),
    queryFn: async () => {
      const response = await api.get<{ items: ApiKey[] }>('/iam/api-keys');
      return response;
    },
  });
}

export function useCreateApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ApiKeyCreate) => {
      return api.post<{ api_key: ApiKey; secret_key: string }>('/iam/api-keys', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.apiKeys() });
    },
  });
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/iam/api-keys/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: iamKeys.apiKeys() });
    },
  });
}

// ============================================================================
// HOOKS - AUDIT LOGS
// ============================================================================

export function useIAMAuditLogs(filters?: {
  user_id?: string;
  action?: string;
  resource_type?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...iamKeys.auditLogs(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.action) params.append('action', filters.action);
      if (filters?.resource_type) params.append('resource_type', filters.resource_type);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: IAMAuditLog[]; total: number }>(
        `/iam/audit-logs${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

// ============================================================================
// HOOKS - MFA
// ============================================================================

export function useEnableMFA() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return api.post<{ qr_code: string; secret: string; backup_codes: string[] }>('/iam/mfa/enable');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...iamKeys.users(), 'me'] });
    },
  });
}

export function useVerifyMFA() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (code: string) => {
      return api.post<{ success: boolean }>('/iam/mfa/verify', { code });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...iamKeys.users(), 'me'] });
    },
  });
}

export function useDisableMFA() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (password: string) => {
      return api.post('/iam/mfa/disable', { password });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...iamKeys.users(), 'me'] });
    },
  });
}

export function useRegenerateBackupCodes() {
  return useMutation({
    mutationFn: async (password: string) => {
      return api.post<{ backup_codes: string[] }>('/iam/mfa/backup-codes', { password });
    },
  });
}
