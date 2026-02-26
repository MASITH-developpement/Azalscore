/**
 * AZALSCORE Module - Admin - Hooks
 * React Query hooks pour le module administration
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import { unwrapApiResponse } from '@/types';
import type { AvailableModule } from '@/constants/modules';
import type { AdminUser, Role, AuditLog, BackupConfig } from './types';

// ============================================================================
// TYPES
// ============================================================================

interface AdminDashboard {
  total_users: number;
  active_users: number;
  total_tenants: number;
  active_tenants: number;
  total_roles: number;
  storage_used_gb: number;
  api_calls_today: number;
  errors_today: number;
}

interface ModulesResponse {
  categories: string[];
  modules: AvailableModule[];
  modules_by_category: Record<string, AvailableModule[]>;
}

interface User {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role_id?: string;
  role_name?: string;
  status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED' | 'PENDING';
  last_login?: string;
  created_at: string;
  default_view?: string;
}

interface Tenant {
  id: string;
  tenant_id: string;
  name: string;
  email: string;
  status: 'ACTIVE' | 'INACTIVE' | 'TRIAL' | 'SUSPENDED' | 'PENDING';
  plan: 'STARTER' | 'PROFESSIONAL' | 'ENTERPRISE' | 'CUSTOM';
  modules_enabled: string[];
  max_users: number;
  max_storage_gb: number;
  storage_used_gb: number;
  created_at: string;
}

interface Permission {
  id: string;
  code: string;
  name: string;
  description?: string;
  module: string;
}

interface CapabilityInfo {
  code: string;
  name: string;
  description: string;
}

interface ModuleCapabilities {
  name: string;
  icon: string;
  capabilities: CapabilityInfo[];
}

type CapabilitiesByModule = Record<string, ModuleCapabilities>;

// ============================================================================
// HELPERS
// ============================================================================

function extractArrayFromResponse<T>(response: unknown): T[] {
  if (Array.isArray(response)) {
    return response;
  }
  if (response && typeof response === 'object') {
    const r = response as Record<string, unknown>;
    if (Array.isArray(r.data)) return r.data;
    if (Array.isArray(r.items)) return r.items;
    const keys = Object.keys(r);
    if (keys.length === 1 && Array.isArray(r[keys[0]])) {
      return r[keys[0]] as T[];
    }
  }
  return [];
}

// ============================================================================
// DASHBOARD & MODULES
// ============================================================================

export const useAdminDashboard = () => {
  return useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: async (): Promise<AdminDashboard> => {
      const defaultDashboard: AdminDashboard = {
        total_users: 0,
        active_users: 0,
        total_tenants: 1,
        active_tenants: 1,
        total_roles: 0,
        storage_used_gb: 0,
        api_calls_today: 0,
        errors_today: 0
      };
      try {
        const response = await api.get<AdminDashboard>('/admin/dashboard', {
          headers: { 'X-Silent-Error': 'true' }
        });
        if (response && typeof response === 'object' && 'data' in response) {
          return (response as { data: AdminDashboard }).data || defaultDashboard;
        }
        return (response as AdminDashboard) || defaultDashboard;
      } catch {
        return defaultDashboard;
      }
    },
    retry: false
  });
};

export const useAvailableModules = () => {
  return useQuery({
    queryKey: ['admin', 'modules', 'available'],
    queryFn: async (): Promise<ModulesResponse> => {
      try {
        const response = await api.get<ModulesResponse>('/admin/modules/available');
        const data = response?.data || response;
        return data as ModulesResponse;
      } catch {
        return { categories: [], modules: [], modules_by_category: {} };
      }
    },
    staleTime: 30 * 1000,
    retry: 2,
  });
};

// ============================================================================
// USERS
// ============================================================================

export const useUsers = (filters?: { status?: string; role_id?: string }) => {
  return useQuery({
    queryKey: ['admin', 'users', serializeFilters(filters)],
    queryFn: async (): Promise<User[]> => {
      try {
        const params = new URLSearchParams();
        if (filters?.status) params.append('is_active', filters.status === 'active' ? 'true' : 'false');
        if (filters?.role_id) params.append('role_code', filters.role_id);
        const queryString = params.toString();
        const res = await api.get<{ items: User[]; total: number }>(`/iam/users${queryString ? `?${queryString}` : ''}`, {
          headers: { 'X-Silent-Error': 'true' }
        });
        const data = unwrapApiResponse<{ items: User[]; total: number }>(res);
        return data?.items || [];
      } catch {
        return [];
      }
    },
    retry: false
  });
};

export const useUser = (id: string | undefined) => {
  return useQuery({
    queryKey: ['admin', 'user', id],
    queryFn: async (): Promise<AdminUser | null> => {
      try {
        const response = await api.get<AdminUser>(`/iam/users/${id}`, {
          headers: { 'X-Silent-Error': 'true' }
        });
        if (response && typeof response === 'object' && 'data' in response) {
          return (response as { data: AdminUser }).data || null;
        }
        return response as AdminUser || null;
      } catch {
        return null;
      }
    },
    enabled: !!id,
    retry: false
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<User> & { password: string }) => {
      const res = await api.post('/iam/users', data);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
  });
};

export const useUpdateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<User> }) => {
      const res = await api.patch(`/iam/users/${id}`, data);
      return unwrapApiResponse(res);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'user'] });
    }
  });
};

export const useUpdateUserStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      const res = await api.patch(`/iam/users/${id}`, { status });
      return unwrapApiResponse(res);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'user'] });
    }
  });
};

export const useDeleteUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.delete(`/iam/users/${id}`);
      return unwrapApiResponse(res);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    }
  });
};

// ============================================================================
// ROLES
// ============================================================================

export const useRoles = () => {
  return useQuery({
    queryKey: ['admin', 'roles'],
    queryFn: async (): Promise<Role[]> => {
      try {
        const response = await api.get<Role[]>('/iam/roles', {
          headers: { 'X-Silent-Error': 'true' }
        });
        return extractArrayFromResponse<Role>(response);
      } catch {
        return [];
      }
    },
    retry: false
  });
};

export const useCreateRole = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      code: string;
      name: string;
      description?: string;
      level?: number;
      parent_code?: string;
      permission_codes?: string[];
      requires_approval?: boolean;
      max_users?: number;
    }) => {
      const res = await api.post('/iam/roles', data);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] })
  });
};

export const useUpdateRole = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: {
      id: string;
      data: {
        name?: string;
        description?: string;
        level?: number;
        requires_approval?: boolean;
        max_users?: number;
        is_active?: boolean;
      }
    }) => {
      const res = await api.patch(`/iam/roles/${id}`, data);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] })
  });
};

export const useDeleteRole = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/iam/roles/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] })
  });
};

// ============================================================================
// PERMISSIONS
// ============================================================================

export const usePermissions = () => {
  return useQuery({
    queryKey: ['admin', 'permissions'],
    queryFn: async (): Promise<Permission[]> => {
      try {
        const response = await api.get<{ items: Permission[] }>('/iam/permissions', {
          headers: { 'X-Silent-Error': 'true' }
        });
        return extractArrayFromResponse<Permission>(response);
      } catch {
        return [];
      }
    },
    retry: false
  });
};

export const useCapabilitiesByModule = () => {
  return useQuery({
    queryKey: ['admin', 'capabilities-modules'],
    queryFn: async (): Promise<CapabilitiesByModule> => {
      const response = await api.get('/iam/capabilities/modules');
      const data = response as unknown;
      if (data && typeof data === 'object' && !Array.isArray(data)) {
        const obj = data as Record<string, unknown>;
        const keys = Object.keys(obj);
        const firstKey = keys[0];
        const firstModule = obj[firstKey] as { capabilities?: unknown[] } | undefined;
        if (firstKey && firstModule?.capabilities) {
          return obj as CapabilitiesByModule;
        }
      }
      return {};
    },
    retry: 2,
    staleTime: 5 * 60 * 1000
  });
};

export const useUserPermissions = (userId: string | undefined) => {
  return useQuery({
    queryKey: ['admin', 'user-permissions', userId],
    queryFn: async (): Promise<string[]> => {
      if (!userId) return [];
      try {
        const response = await api.get<string[]>(`/iam/users/${userId}/permissions`, {
          headers: { 'X-Silent-Error': 'true' }
        });
        if (Array.isArray(response)) return response;
        return [];
      } catch {
        return [];
      }
    },
    enabled: !!userId,
    retry: false
  });
};

export const useUpdateUserPermissions = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ userId, capabilities }: { userId: string; capabilities: string[] }) => {
      const res = await api.put(`/iam/users/${userId}/permissions`, { capabilities });
      return res;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'user-permissions', variables.userId] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'user', variables.userId] });
    }
  });
};

// ============================================================================
// TENANTS
// ============================================================================

export const useTenants = (filters?: { status?: string; plan?: string }) => {
  return useQuery({
    queryKey: ['admin', 'tenants', serializeFilters(filters)],
    queryFn: async (): Promise<Tenant[]> => {
      try {
        const response = await api.get<Tenant[]>('/tenants', {
          headers: { 'X-Silent-Error': 'true' }
        });
        if (Array.isArray(response)) {
          return response as Tenant[];
        }
        if (response && typeof response === 'object' && 'data' in response) {
          return (response as { data: Tenant[] }).data || [];
        }
        return [];
      } catch {
        return [];
      }
    },
    retry: false
  });
};

export const useSuspendTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tenantId: string) => {
      const res = await api.post(`/tenants/${tenantId}/suspend`);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] })
  });
};

export const useActivateTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tenantId: string) => {
      const res = await api.post(`/tenants/${tenantId}/activate`);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] })
  });
};

export const useCancelTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tenantId: string) => {
      const res = await api.post(`/tenants/${tenantId}/cancel`);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] })
  });
};

export const useUpdateTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ tenantId, data }: { tenantId: string; data: Partial<Tenant> }) => {
      const res = await api.put(`/tenants/${tenantId}`, data);
      return unwrapApiResponse(res);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] });
    }
  });
};

// ============================================================================
// AUDIT
// ============================================================================

export const useAuditLogs = (filters?: { resource_type?: string }) => {
  return useQuery({
    queryKey: ['admin', 'audit-logs', serializeFilters(filters)],
    queryFn: async (): Promise<AuditLog[]> => {
      try {
        const params = new URLSearchParams();
        if (filters?.resource_type) params.append('resource_type', filters.resource_type);
        const queryString = params.toString();
        const response = await api.get<AuditLog[]>(`/audit/logs${queryString ? `?${queryString}` : ''}`, {
          headers: { 'X-Silent-Error': 'true' }
        });
        if (Array.isArray(response)) {
          return response as AuditLog[];
        }
        if (response && typeof response === 'object' && 'data' in response) {
          return (response as { data: AuditLog[] }).data || [];
        }
        return [];
      } catch {
        return [];
      }
    },
    retry: false
  });
};

// ============================================================================
// BACKUPS
// ============================================================================

export const useBackupConfigs = () => {
  return useQuery({
    queryKey: ['admin', 'backups'],
    queryFn: async (): Promise<BackupConfig[]> => {
      try {
        const response = await api.get<BackupConfig[]>('/backup/config', {
          headers: { 'X-Silent-Error': 'true' }
        });
        if (Array.isArray(response)) {
          return response as BackupConfig[];
        }
        if (response && typeof response === 'object' && 'data' in response) {
          return (response as { data: BackupConfig[] }).data || [];
        }
        return [];
      } catch {
        return [];
      }
    },
    retry: false
  });
};

export const useRunBackup = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`/backup/${id}/run`);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'backups'] })
  });
};

// Re-export types for convenience
export type { User, Tenant, Permission, CapabilitiesByModule, ModuleCapabilities, CapabilityInfo, AdminDashboard };
