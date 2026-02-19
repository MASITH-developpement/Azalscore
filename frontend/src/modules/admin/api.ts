/**
 * AZALSCORE - Admin API
 * =====================
 * API client pour le module Administration
 * Couvre: Utilisateurs, Rôles, Tenants, Audit, Configuration
 */

import { api } from '@/core/api-client';
import type { AdminUser, Role } from './types';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type { AdminUser, Role };

// ============================================================================
// TYPES
// ============================================================================

export type UserStatus = 'ACTIVE' | 'INACTIVE' | 'SUSPENDED' | 'PENDING';
export type TenantStatus = 'ACTIVE' | 'INACTIVE' | 'TRIAL' | 'SUSPENDED' | 'PENDING';
export type TenantPlan = 'FREE' | 'STARTER' | 'PROFESSIONAL' | 'ENTERPRISE' | 'CUSTOM';

export interface User {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role_id?: string;
  role_name?: string;
  status: UserStatus;
  last_login?: string;
  default_view?: string;
  two_factor_enabled?: boolean;
  must_change_password?: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Tenant {
  id: string;
  tenant_id: string;
  name: string;
  email: string;
  status: TenantStatus;
  plan: TenantPlan;
  modules_enabled: string[];
  max_users: number;
  max_storage_gb: number;
  storage_used_gb: number;
  created_at: string;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id?: string;
  user_name?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
}

export interface AdminDashboard {
  total_users: number;
  active_users: number;
  total_tenants: number;
  active_tenants: number;
  total_roles: number;
  storage_used_gb: number;
  api_calls_today: number;
  errors_today: number;
}

export interface ModulesResponse {
  categories: string[];
  modules: Array<{
    id: string;
    name: string;
    category: string;
    is_enabled: boolean;
  }>;
  modules_by_category: Record<string, Array<{
    id: string;
    name: string;
    is_enabled: boolean;
  }>>;
}

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface UserFilters {
  status?: UserStatus;
  role_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface TenantFilters {
  status?: TenantStatus;
  plan?: TenantPlan;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface AuditFilters {
  user_id?: string;
  action?: string;
  resource_type?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  role_id?: string;
  default_view?: string;
}

export interface UserUpdate extends Partial<Omit<UserCreate, 'password'>> {
  status?: UserStatus;
}

export interface RoleCreate {
  name: string;
  description?: string;
  permissions: string[];
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/admin';

function buildQueryString<T extends object>(params: T): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// API CLIENT
// ============================================================================

export const adminApi = {
  // ==========================================================================
  // Dashboard
  // ==========================================================================

  /**
   * Récupère le tableau de bord admin
   */
  getDashboard: () =>
    api.get<AdminDashboard>(`${BASE_PATH}/dashboard`),

  /**
   * Récupère les modules disponibles
   */
  getAvailableModules: () =>
    api.get<ModulesResponse>(`${BASE_PATH}/modules/available`),

  // ==========================================================================
  // Users
  // ==========================================================================

  /**
   * Liste les utilisateurs
   */
  listUsers: (filters?: UserFilters) =>
    api.get<PaginatedResponse<User>>(
      `${BASE_PATH}/users${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère un utilisateur par son ID
   */
  getUser: (id: string) =>
    api.get<User>(`${BASE_PATH}/users/${id}`),

  /**
   * Crée un nouvel utilisateur
   */
  createUser: (data: UserCreate) =>
    api.post<User>(`${BASE_PATH}/users`, data),

  /**
   * Met à jour un utilisateur
   */
  updateUser: (id: string, data: UserUpdate) =>
    api.put<User>(`${BASE_PATH}/users/${id}`, data),

  /**
   * Supprime un utilisateur
   */
  deleteUser: (id: string) =>
    api.delete(`${BASE_PATH}/users/${id}`),

  /**
   * Active un utilisateur
   */
  activateUser: (id: string) =>
    api.post<User>(`${BASE_PATH}/users/${id}/activate`, {}),

  /**
   * Suspend un utilisateur
   */
  suspendUser: (id: string) =>
    api.post<User>(`${BASE_PATH}/users/${id}/suspend`, {}),

  /**
   * Réinitialise le mot de passe
   */
  resetUserPassword: (id: string) =>
    api.post<{ temporary_password: string }>(`${BASE_PATH}/users/${id}/reset-password`, {}),

  /**
   * Force le 2FA
   */
  enforceTwoFactor: (id: string) =>
    api.post<User>(`${BASE_PATH}/users/${id}/enforce-2fa`, {}),

  // ==========================================================================
  // Roles
  // ==========================================================================

  /**
   * Liste les rôles
   */
  listRoles: () =>
    api.get<Role[]>(`${BASE_PATH}/roles`),

  /**
   * Récupère un rôle par son ID
   */
  getRole: (id: string) =>
    api.get<Role>(`${BASE_PATH}/roles/${id}`),

  /**
   * Crée un nouveau rôle
   */
  createRole: (data: RoleCreate) =>
    api.post<Role>(`${BASE_PATH}/roles`, data),

  /**
   * Met à jour un rôle
   */
  updateRole: (id: string, data: Partial<RoleCreate>) =>
    api.put<Role>(`${BASE_PATH}/roles/${id}`, data),

  /**
   * Supprime un rôle
   */
  deleteRole: (id: string) =>
    api.delete(`${BASE_PATH}/roles/${id}`),

  // ==========================================================================
  // Tenants
  // ==========================================================================

  /**
   * Liste les tenants
   */
  listTenants: (filters?: TenantFilters) =>
    api.get<PaginatedResponse<Tenant>>(
      `${BASE_PATH}/tenants${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère un tenant par son ID
   */
  getTenant: (id: string) =>
    api.get<Tenant>(`${BASE_PATH}/tenants/${id}`),

  /**
   * Active un tenant
   */
  activateTenant: (id: string) =>
    api.post<Tenant>(`${BASE_PATH}/tenants/${id}/activate`, {}),

  /**
   * Suspend un tenant
   */
  suspendTenant: (id: string) =>
    api.post<Tenant>(`${BASE_PATH}/tenants/${id}/suspend`, {}),

  /**
   * Met à jour les modules d'un tenant
   */
  updateTenantModules: (id: string, modules: string[]) =>
    api.put<Tenant>(`${BASE_PATH}/tenants/${id}/modules`, { modules }),

  // ==========================================================================
  // Audit
  // ==========================================================================

  /**
   * Liste les logs d'audit
   */
  listAuditLogs: (filters?: AuditFilters) =>
    api.get<PaginatedResponse<AuditLog>>(
      `${BASE_PATH}/audit${buildQueryString(filters || {})}`
    ),

  /**
   * Exporte les logs d'audit
   */
  exportAuditLogs: (filters?: AuditFilters) =>
    api.get<Blob>(`${BASE_PATH}/audit/export${buildQueryString(filters || {})}`, {
      responseType: 'blob',
    }),
};

export default adminApi;
