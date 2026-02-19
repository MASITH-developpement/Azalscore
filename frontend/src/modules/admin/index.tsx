import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Users, Building, Shield, Database, Activity, AlertTriangle,
  User, Key, Clock, Sparkles, ArrowLeft, Edit3, Lock, Unlock, Trash2,
  Package
} from 'lucide-react';
import { Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { api } from '@core/api-client';
import { useAuth } from '@core/auth';
import { useCapabilitiesStore } from '@core/capabilities';
import { serializeFilters } from '@core/query-keys';
import { Button, Modal } from '@ui/actions';
import { StatCard } from '@ui/dashboards';
import { Select, Input } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { BaseViewStandard } from '@ui/standards';
import { DataTable } from '@ui/tables';
import type { AvailableModule } from '@/constants/modules';
import type { TableColumn, ApiMutationError } from '@/types';
import { unwrapApiResponse } from '@/types';

// Type for Pydantic validation error
interface ValidationErrorDetail {
  loc: string[];
  msg: string;
  type?: string;
}

interface ValidationError {
  message?: string;
  response?: {
    data?: {
      detail?: string | ValidationErrorDetail[];
    };
  };
  detail?: ValidationErrorDetail[];
}
import { formatDateTime } from '@/utils/formatters';
import {
  UserInfoTab, UserPermissionsTab, UserActivityTab,
  UserHistoryTab, UserIATab, SequencesView, EnrichmentProvidersView
} from './components';
import {
  USER_STATUS_CONFIG, getUserFullName, isUserActive, isUserLocked,
  hasTwoFactorEnabled, mustChangePassword
} from './types';
import type { AdminUser, Role } from './types';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition } from '@ui/standards';

// ============================================================================
// HOOK: Charger les modules depuis l'API (source unique de verite)
// ============================================================================

interface ModulesResponse {
  categories: string[];
  modules: AvailableModule[];
  modules_by_category: Record<string, AvailableModule[]>;
}

const useAvailableModules = () => {
  return useQuery({
    queryKey: ['admin', 'modules', 'available'],
    queryFn: async (): Promise<ModulesResponse> => {
      try {
        console.log('[Admin] Fetching available modules...');
        const response = await api.get<ModulesResponse>('/admin/modules/available');
        const data = response?.data || response;
        console.log('[Admin] Modules loaded:', data?.modules?.length || 0);
        return data as ModulesResponse;
      } catch (err) {
        console.error('[Admin] Error loading modules:', err);
        // Fallback vide si API non disponible
        return { categories: [], modules: [], modules_by_category: {} };
      }
    },
    staleTime: 30 * 1000, // Cache 30 secondes (réduit pour debug)
    retry: 2,
  });
};

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavProps {
  tabs: { id: string; label: string }[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <nav className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </nav>
);

// ============================================================================
// TYPES INTERNES
// ============================================================================

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

interface AuditLog {
  id: string;
  timestamp: string;
  user_id?: string;
  user_name?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
}

interface BackupConfig {
  id: string;
  name: string;
  type: 'FULL' | 'INCREMENTAL' | 'DIFFERENTIAL';
  schedule: string;
  retention_days: number;
  destination: 'LOCAL' | 'S3' | 'GCS' | 'AZURE';
  last_backup?: string;
  last_status?: 'SUCCESS' | 'FAILED' | 'IN_PROGRESS';
  is_active: boolean;
}

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

// ============================================================================
// CONSTANTES
// ============================================================================

const USER_STATUSES = [
  { value: 'ACTIVE', label: 'Actif', color: 'green' },
  { value: 'INACTIVE', label: 'Inactif', color: 'gray' },
  { value: 'SUSPENDED', label: 'Suspendu', color: 'red' },
  { value: 'PENDING', label: 'En attente', color: 'orange' }
];

const TENANT_STATUSES = [
  { value: 'ACTIVE', label: 'Actif', color: 'green' },
  { value: 'INACTIVE', label: 'Inactif', color: 'gray' },
  { value: 'TRIAL', label: 'Essai', color: 'blue' },
  { value: 'SUSPENDED', label: 'Suspendu', color: 'red' }
];

const TENANT_PLANS = [
  { value: 'FREE', label: 'Gratuit' },
  { value: 'STARTER', label: 'Starter' },
  { value: 'PROFESSIONAL', label: 'Professionnel' },
  { value: 'ENTERPRISE', label: 'Enterprise' }
];

// Modules charges dynamiquement depuis l'API via useAvailableModules()

const BACKUP_TYPES = [
  { value: 'FULL', label: 'Complete' },
  { value: 'INCREMENTAL', label: 'Incrementale' },
  { value: 'DIFFERENTIAL', label: 'Differentielle' }
];

const BACKUP_DESTINATIONS = [
  { value: 'LOCAL', label: 'Local' },
  { value: 'S3', label: 'AWS S3' },
  { value: 'GCS', label: 'Google Cloud' },
  { value: 'AZURE', label: 'Azure Blob' }
];

// ============================================================================
// HELPERS
// ============================================================================

const _formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const formatDateTimeFn = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

interface StatusInfo {
  value: string;
  label: string;
  color: string;
}

const getStatusInfo = (statuses: StatusInfo[], status: string): StatusInfo => {
  return statuses.find(s => s.value === status) || { value: status, label: status, color: 'gray' };
};

const _formatBytes = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
};

// ============================================================================
// API HOOKS
// ============================================================================

const useAdminDashboard = () => {
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
        // Gérer les deux formats possibles
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

const useUsers = (filters?: { status?: string; role_id?: string }) => {
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
        // Gérer les deux formats possibles (réponse directe ou enveloppée dans data)
        const data = unwrapApiResponse<{ items: User[]; total: number }>(res);
        return data?.items || [];
      } catch {
        return [];
      }
    },
    retry: false
  });
};

const useUser = (id: string | undefined) => {
  return useQuery({
    queryKey: ['admin', 'user', id],
    queryFn: async (): Promise<AdminUser | null> => {
      try {
        const response = await api.get<AdminUser>(`/iam/users/${id}`, {
          headers: { 'X-Silent-Error': 'true' }
        });
        // Gérer les deux formats possibles (objet direct ou enveloppé)
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

// Helper pour extraire un tableau d'une réponse API multi-format
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

const useRoles = () => {
  return useQuery({
    queryKey: ['admin', 'roles'],
    queryFn: async (): Promise<Role[]> => {
      try {
        const response = await api.get<Role[]>('/iam/roles', {
          headers: { 'X-Silent-Error': 'true' }
        });
        return extractArrayFromResponse<Role>(response);
      } catch (err) {
        console.error('[useRoles] Error:', err);
        return [];
      }
    },
    retry: false
  });
};

const useCreateRole = () => {
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

const useUpdateRole = () => {
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

const useDeleteRole = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/iam/roles/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] })
  });
};

interface Permission {
  id: string;
  code: string;
  name: string;
  description?: string;
  module: string;
}

const usePermissions = () => {
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

// Types pour les capabilities par module
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

// Hook pour récupérer toutes les capabilities groupées par module
const useCapabilitiesByModule = () => {
  return useQuery({
    queryKey: ['admin', 'capabilities-modules'],
    queryFn: async (): Promise<CapabilitiesByModule> => {
      const response = await api.get('/iam/capabilities/modules');

      // La réponse est directement l'objet CAPABILITIES_BY_MODULE
      const data = response as unknown;
      if (data && typeof data === 'object' && !Array.isArray(data)) {
        const obj = data as Record<string, any>;
        const keys = Object.keys(obj);

        // Vérifier que c'est bien le format attendu (au moins un module avec capabilities)
        const firstKey = keys[0];
        if (firstKey && obj[firstKey]?.capabilities) {
          return obj as CapabilitiesByModule;
        }
      }

      return {};
    },
    retry: 2,
    staleTime: 5 * 60 * 1000 // 5 minutes
  });
};

// Hook pour récupérer les permissions d'un utilisateur
const useUserPermissions = (userId: string | undefined) => {
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

// Hook pour mettre à jour les permissions d'un utilisateur
const useUpdateUserPermissions = () => {
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

const useTenants = (filters?: { status?: string; plan?: string }) => {
  return useQuery({
    queryKey: ['admin', 'tenants', serializeFilters(filters)],
    queryFn: async (): Promise<Tenant[]> => {
      try {
        const response = await api.get<Tenant[]>('/tenants', {
          headers: { 'X-Silent-Error': 'true' }
        });
        // Gérer les deux formats possibles (tableau direct ou enveloppé)
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

const useAuditLogs = (filters?: { resource_type?: string }) => {
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

const useBackupConfigs = () => {
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

const useCreateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<User> & { password: string }) => {
      const res = await api.post('/iam/users', data);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
  });
};

const useUpdateUserStatus = () => {
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

const useUpdateUser = () => {
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

const useDeleteUser = () => {
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

const useRunBackup = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`/backup/${id}/run`);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'backups'] })
  });
};

// ============================================================================
// USER DETAIL VIEW (BaseViewStandard)
// ============================================================================

const UserDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: user, isLoading, error } = useUser(id);
  const updateStatus = useUpdateUserStatus();

  if (isLoading) {
    return (
      <PageWrapper title="Chargement..." subtitle="Utilisateur">
        <div className="azals-loading">Chargement...</div>
      </PageWrapper>
    );
  }

  if (error || !user) {
    return (
      <PageWrapper title="Erreur" subtitle="Utilisateur non trouve">
        <Card>
          <p className="text-red-600">Impossible de charger l'utilisateur</p>
          <Button onClick={() => navigate('/admin')} className="mt-4">Retour</Button>
        </Card>
      </PageWrapper>
    );
  }

  const statusConfig = USER_STATUS_CONFIG[user.status] || { label: user.status || 'Inconnu', color: 'gray' as const };

  const tabs: TabDefinition<AdminUser>[] = [
    { id: 'info', label: 'Informations', icon: <User size={16} />, component: UserInfoTab },
    { id: 'permissions', label: 'Permissions', icon: <Shield size={16} />, component: UserPermissionsTab },
    { id: 'activity', label: 'Activite', icon: <Activity size={16} />, component: UserActivityTab, badge: user.sessions?.filter(s => s.is_active).length },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: UserHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: UserIATab }
  ];

  const infoBarItems: InfoBarItem[] = [
    {
      id: 'status',
      label: 'Statut',
      value: statusConfig.label,
      valueColor: statusConfig.color
    },
    {
      id: 'role',
      label: 'Role',
      value: user.role_name || 'Non assigne',
      valueColor: user.role_name ? 'purple' : 'gray'
    },
    {
      id: '2fa',
      label: '2FA',
      value: hasTwoFactorEnabled(user) ? 'Active' : 'Desactive',
      valueColor: hasTwoFactorEnabled(user) ? 'green' : 'orange'
    },
    {
      id: 'logins',
      label: 'Connexions',
      value: String(user.login_count),
      valueColor: 'blue'
    }
  ];

  const sidebarSections: SidebarSection[] = [
    {
      id: 'security',
      title: 'Securite',
      items: [
        { id: 'status', label: 'Statut', value: statusConfig.label },
        { id: '2fa', label: 'Double authentification', value: hasTwoFactorEnabled(user) ? 'Oui' : 'Non' },
        { id: 'pwd', label: 'Changement MDP requis', value: mustChangePassword(user) ? 'Oui' : 'Non' },
        { id: 'failures', label: 'Echecs de connexion', value: String(user.failed_login_count) }
      ]
    },
    {
      id: 'activity',
      title: 'Activite',
      items: [
        { id: 'logins', label: 'Connexions totales', value: String(user.login_count) },
        { id: 'last', label: 'Derniere connexion', value: user.last_login ? formatDateTime(user.last_login) : 'Jamais' },
        { id: 'sessions', label: 'Sessions actives', value: String(user.sessions?.filter(s => s.is_active).length || 0) }
      ]
    },
    {
      id: 'dates',
      title: 'Dates',
      items: [
        { id: 'created', label: 'Creation', value: formatDateTime(user.created_at) },
        { id: 'updated', label: 'Modification', value: formatDateTime(user.updated_at) }
      ]
    }
  ];

  const headerActions: ActionDefinition[] = [
    {
      id: 'back',
      label: 'Retour',
      icon: <ArrowLeft size={16} />,
      variant: 'secondary',
      onClick: () => navigate('/admin')
    },
    {
      id: 'edit',
      label: 'Modifier',
      icon: <Edit3 size={16} />,
      variant: 'secondary',
      onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'editUser', userId: user.id } })); }
    }
  ];

  const primaryActions: ActionDefinition[] = isUserLocked(user)
    ? [
        {
          id: 'unlock',
          label: 'Debloquer',
          icon: <Unlock size={16} />,
          variant: 'primary',
          onClick: () => updateStatus.mutate({ id: user.id, status: 'ACTIVE' })
        }
      ]
    : [];

  const secondaryActions: ActionDefinition[] = !isUserLocked(user) && isUserActive(user)
    ? [
        {
          id: 'suspend',
          label: 'Suspendre',
          icon: <Lock size={16} />,
          variant: 'danger',
          onClick: () => updateStatus.mutate({ id: user.id, status: 'SUSPENDED' })
        }
      ]
    : [];

  return (
    <BaseViewStandard<AdminUser>
      title={getUserFullName(user)}
      subtitle={`@${user.username}`}
      status={{ label: statusConfig.label, color: statusConfig.color }}
      data={user}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      primaryActions={primaryActions}
      secondaryActions={secondaryActions}
    />
  );
};

// ============================================================================
// COMPOSANTS LISTE
// ============================================================================

const UsersView: React.FC = () => {
  const navigate = useNavigate();
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterRole, setFilterRole] = useState<string>('');
  const { data: users = [], isLoading } = useUsers({
    status: filterStatus || undefined,
    role_id: filterRole || undefined
  });
  const { data: roles = [] } = useRoles();
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();
  const updateStatus = useUpdateUserStatus();
  const [showModal, setShowModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<Partial<User> & { password: string }>({ password: '' });
  const [editFormData, setEditFormData] = useState<Partial<User>>({});
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Parser les erreurs de validation Pydantic
  const parseValidationErrors = (error: ValidationError): Record<string, string> => {
    const errors: Record<string, string> = {};
    try {
      // Format: { detail: [{ loc: ['body', 'field'], msg: 'message' }] }
      const details = error?.response?.data?.detail || error?.detail || [];
      if (Array.isArray(details)) {
        details.forEach((err: ValidationErrorDetail) => {
          const field = err.loc?.[err.loc.length - 1] || 'general';
          errors[field] = err.msg;
        });
      }
    } catch {
      errors.general = 'Erreur de validation';
    }
    return errors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFieldErrors({});
    try {
      await createUser.mutateAsync(formData);
      setShowModal(false);
      setFormData({ password: '' });
    } catch (error: unknown) {
      const errors = parseValidationErrors(error as ValidationError);
      setFieldErrors(errors);
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setFieldErrors({});
    setFormData({ password: '' });
  };

  const handleRowClick = (user: User) => {
    navigate(`/admin/users/${user.id}`);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setEditFormData({
      first_name: user.first_name || '',
      last_name: user.last_name || '',
      username: user.username,
      email: user.email,
      role_id: user.role_id || '',
      default_view: user.default_view || ''
    });
    setFieldErrors({});
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;
    setFieldErrors({});
    try {
      // N'envoyer que les champs supportés par l'API
      const { role_id: _role_id, ...updateData } = editFormData;
      await updateUser.mutateAsync({ id: editingUser.id, data: updateData });
      setShowEditModal(false);
      setEditingUser(null);
    } catch (error: unknown) {
      const errors = parseValidationErrors(error as ValidationError);
      setFieldErrors(errors);
    }
  };

  const handleCloseEditModal = () => {
    setShowEditModal(false);
    setEditingUser(null);
    setFieldErrors({});
  };

  const handleDelete = async (user: User) => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer l'utilisateur "${user.username}" ?`)) {
      try {
        await deleteUser.mutateAsync(user.id);
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
        alert('Erreur lors de la suppression de l\'utilisateur');
      }
    }
  };

  const columns: TableColumn<User>[] = [
    { id: 'username', header: 'Utilisateur', accessor: 'username' },
    { id: 'email', header: 'Email', accessor: 'email' },
    { id: 'last_name', header: 'Nom', accessor: 'last_name', render: (v, row) =>
      `${(row as User).first_name || ''} ${(row as User).last_name || ''}`.trim() || '-'
    },
    { id: 'role_name', header: 'Role', accessor: 'role_name', render: (v) => (v as string) || '-' },
    { id: 'last_login', header: 'Derniere connexion', accessor: 'last_login', render: (v) => (v as string) ? formatDateTimeFn(v as string) : 'Jamais' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v, row) => (
      <div onClick={(e) => e.stopPropagation()}>
        <Select
          value={v as string}
          onChange={(val) => {
            updateStatus.mutate({ id: (row as User).id, status: val });
          }}
          options={USER_STATUSES}
          className="w-32"
        />
      </div>
    )},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => {
      const u = row as User;
      return (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <Button size="sm" variant="secondary" onClick={() => handleEdit(u)}>
            <Edit3 size={14} />
          </Button>
          <Button size="sm" variant="danger" onClick={() => handleDelete(u)}>
            <Trash2 size={14} />
          </Button>
        </div>
      );
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Utilisateurs</h3>
        <div className="flex gap-2">
          <Select
            value={filterRole}
            onChange={(val) => setFilterRole(val)}
            options={[{ value: '', label: 'Tous les roles' }, ...roles.map(r => ({ value: r.id, label: r.name }))]}
            className="w-40"
          />
          <Select
            value={filterStatus}
            onChange={(val) => setFilterStatus(val)}
            options={[{ value: '', label: 'Tous statuts' }, ...USER_STATUSES]}
            className="w-32"
          />
          <Button onClick={() => setShowModal(true)}>Nouvel utilisateur</Button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={users}
        isLoading={isLoading}
        keyField="id"
          onRowClick={handleRowClick}
      />

      <Modal isOpen={showModal} onClose={handleCloseModal} title="Nouvel utilisateur">
        <form onSubmit={handleSubmit}>
          {fieldErrors.general && (
            <div className="azals-alert azals-alert--error mb-4">
              {fieldErrors.general}
            </div>
          )}
          <Grid cols={2}>
            <div className="azals-field">
              <label>Prenom</label>
              <Input
                value={formData.first_name || ''}
                onChange={(v) => setFormData({ ...formData, first_name: v })}
                error={!!fieldErrors.first_name}
              />
              {fieldErrors.first_name && <span className="azals-field__error">{fieldErrors.first_name}</span>}
            </div>
            <div className="azals-field">
              <label>Nom</label>
              <Input
                value={formData.last_name || ''}
                onChange={(v) => setFormData({ ...formData, last_name: v })}
                error={!!fieldErrors.last_name}
              />
              {fieldErrors.last_name && <span className="azals-field__error">{fieldErrors.last_name}</span>}
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Nom d'utilisateur *</label>
              <Input
                value={formData.username || ''}
                onChange={(v) => setFormData({ ...formData, username: v })}
                error={!!fieldErrors.username}
              />
              {fieldErrors.username && <span className="azals-field__error">{fieldErrors.username}</span>}
            </div>
            <div className="azals-field">
              <label>Email *</label>
              <Input
                type="email"
                value={formData.email || ''}
                onChange={(v) => setFormData({ ...formData, email: v })}
                error={!!fieldErrors.email}
              />
              {fieldErrors.email && <span className="azals-field__error">{fieldErrors.email}</span>}
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Mot de passe * <span className="text-muted text-xs">(min. 12 caracteres)</span></label>
              <Input
                type="password"
                value={formData.password}
                onChange={(v) => setFormData({ ...formData, password: v })}
                error={!!fieldErrors.password}
              />
              {fieldErrors.password && <span className="azals-field__error">{fieldErrors.password}</span>}
            </div>
            <div className="azals-field">
              <label>Role ({roles.length} disponibles)</label>
              <Select
                value={formData.role_id || ''}
                onChange={(val) => setFormData({ ...formData, role_id: val })}
                options={[{ value: '', label: 'Selectionner...' }, ...roles.map(r => ({ value: r.id, label: r.name }))]}
              />
              {fieldErrors.role_id && <span className="azals-field__error">{fieldErrors.role_id}</span>}
            </div>
          </Grid>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={handleCloseModal}>Annuler</Button>
            <Button type="submit" isLoading={createUser.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>

      {/* Modal d'édition */}
      <Modal isOpen={showEditModal} onClose={handleCloseEditModal} title="Modifier l'utilisateur">
        <form onSubmit={handleEditSubmit}>
          {fieldErrors.general && (
            <div className="azals-alert azals-alert--error mb-4">
              {fieldErrors.general}
            </div>
          )}
          <Grid cols={2}>
            <div className="azals-field">
              <label>Prenom</label>
              <Input
                value={editFormData.first_name || ''}
                onChange={(v) => setEditFormData({ ...editFormData, first_name: v })}
                error={!!fieldErrors.first_name}
              />
              {fieldErrors.first_name && <span className="azals-field__error">{fieldErrors.first_name}</span>}
            </div>
            <div className="azals-field">
              <label>Nom</label>
              <Input
                value={editFormData.last_name || ''}
                onChange={(v) => setEditFormData({ ...editFormData, last_name: v })}
                error={!!fieldErrors.last_name}
              />
              {fieldErrors.last_name && <span className="azals-field__error">{fieldErrors.last_name}</span>}
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Nom d'utilisateur *</label>
              <Input
                value={editFormData.username || ''}
                onChange={(v) => setEditFormData({ ...editFormData, username: v })}
                error={!!fieldErrors.username}
              />
              {fieldErrors.username && <span className="azals-field__error">{fieldErrors.username}</span>}
            </div>
            <div className="azals-field">
              <label>Email *</label>
              <Input
                type="email"
                value={editFormData.email || ''}
                onChange={(v) => setEditFormData({ ...editFormData, email: v })}
                error={!!fieldErrors.email}
              />
              {fieldErrors.email && <span className="azals-field__error">{fieldErrors.email}</span>}
            </div>
          </Grid>
          <div className="azals-field mt-4">
            <label>Vue par défaut après connexion</label>
            <Select
              value={editFormData.default_view || ''}
              onChange={(v) => setEditFormData({ ...editFormData, default_view: v || undefined })}
              options={[
                { value: '', label: 'Automatique (selon le rôle)' },
                { value: 'cockpit', label: 'Cockpit (Tableau de bord)' },
                { value: 'admin', label: 'Administration' },
                { value: 'saisie', label: 'Nouvelle saisie' },
                { value: 'gestion-devis', label: 'Gestion - Devis' },
                { value: 'gestion-commandes', label: 'Gestion - Commandes' },
                { value: 'gestion-interventions', label: 'Gestion - Interventions' },
                { value: 'gestion-factures', label: 'Gestion - Factures' },
                { value: 'gestion-paiements', label: 'Gestion - Paiements' },
                { value: 'affaires', label: 'Affaires' },
                { value: 'crm', label: 'CRM' },
                { value: 'stock', label: 'Stock' },
                { value: 'achats', label: 'Achats' },
                { value: 'projets', label: 'Projets' },
                { value: 'rh', label: 'Ressources Humaines' },
                { value: 'vehicules', label: 'Véhicules' },
                { value: 'compta', label: 'Comptabilité' },
                { value: 'tresorerie', label: 'Trésorerie' },
              ]}
            />
            <span className="text-xs text-gray-500 mt-1 block">
              Définit la première page affichée lors de la connexion de l'utilisateur
            </span>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={handleCloseEditModal}>Annuler</Button>
            <Button type="submit" isLoading={updateUser.isPending}>Enregistrer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

// ============================================================================
// COMPOSANT GESTION PERMISSIONS UTILISATEUR
// ============================================================================

const UserPermissionsModal: React.FC<{
  isOpen: boolean;
  user: User | null;
  onClose: () => void;
}> = ({ isOpen, user, onClose }) => {
  const { data: modulesCaps = {}, isLoading: loadingModules, error: modulesError } = useCapabilitiesByModule();
  const { data: userPerms = [], isLoading: loadingPerms } = useUserPermissions(user?.id);
  const updatePermissions = useUpdateUserPermissions();

  // Pour rafraîchir les capabilities si l'utilisateur modifié est l'utilisateur connecté
  const refreshCapabilities = useCapabilitiesStore((state) => state.refreshCapabilities);
  const { user: _currentUser } = useAuth();

  const [selectedCaps, setSelectedCaps] = useState<Set<string>>(new Set());
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');

  // Debug: log data loading
  React.useEffect(() => {
    if (modulesError) console.error('[UserPermissionsModal] Error:', modulesError);
  }, [modulesCaps, userPerms, modulesError]);

  // Synchroniser les permissions utilisateur avec l'état local
  React.useEffect(() => {
    if (userPerms.length > 0) {
      setSelectedCaps(new Set(userPerms));
    } else {
      setSelectedCaps(new Set());
    }
  }, [userPerms, user?.id]);

  const toggleCapability = (code: string) => {
    setSelectedCaps(prev => {
      const next = new Set(prev);
      if (next.has(code)) {
        next.delete(code);
      } else {
        next.add(code);
      }
      return next;
    });
  };

  const toggleModule = (moduleKey: string) => {
    const module = modulesCaps[moduleKey];
    if (!module) return;

    const moduleCodes = module.capabilities.map(c => c.code);
    const allSelected = moduleCodes.every(c => selectedCaps.has(c));

    setSelectedCaps(prev => {
      const next = new Set(prev);
      if (allSelected) {
        moduleCodes.forEach(c => next.delete(c));
      } else {
        moduleCodes.forEach(c => next.add(c));
      }
      return next;
    });
  };

  const toggleExpandModule = (moduleKey: string) => {
    setExpandedModules(prev => {
      const next = new Set(prev);
      if (next.has(moduleKey)) {
        next.delete(moduleKey);
      } else {
        next.add(moduleKey);
      }
      return next;
    });
  };

  const expandAll = () => {
    setExpandedModules(new Set(Object.keys(modulesCaps)));
  };

  const collapseAll = () => {
    setExpandedModules(new Set());
  };

  const selectAll = () => {
    const allCodes = Object.values(modulesCaps).flatMap(m => m.capabilities.map(c => c.code));
    setSelectedCaps(new Set(allCodes));
  };

  const deselectAll = () => {
    setSelectedCaps(new Set());
  };

  const handleSave = async () => {
    if (!user) return;
    await updatePermissions.mutateAsync({
      userId: user.id,
      capabilities: Array.from(selectedCaps)
    });

    // Toujours rafraîchir les capabilities après enregistrement
    // pour mettre à jour l'affichage des menus immédiatement
    await refreshCapabilities();

    onClose();
  };

  // Filtrer les modules par recherche
  const filteredModules = Object.entries(modulesCaps).filter(([, module]) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    if (module.name.toLowerCase().includes(term)) return true;
    return module.capabilities.some(c =>
      c.name.toLowerCase().includes(term) ||
      c.code.toLowerCase().includes(term)
    );
  });

  // Compter les permissions
  const totalCaps = Object.values(modulesCaps).reduce((acc, m) => acc + m.capabilities.length, 0);
  const selectedCount = selectedCaps.size;

  if (!isOpen || !user) return null;

  const isLoading = loadingModules || loadingPerms;
  const hasModules = Object.keys(modulesCaps).length > 0;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Acces modules: ${user.first_name || ''} ${user.last_name || user.username}`.trim()}
    >
      <div style={{ minWidth: '600px' }}>
        {/* Barre d'outils */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--azals-border)',
          paddingBottom: '12px',
          marginBottom: '12px'
        }}>
          <input
            type="text"
            className="azals-input"
            style={{ width: '200px', padding: '8px 12px', fontSize: '14px' }}
            placeholder="Rechercher..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <div style={{ display: 'flex', gap: '8px', fontSize: '13px' }}>
            <button
              type="button"
              onClick={expandAll}
              style={{ background: 'none', border: 'none', color: 'var(--azals-primary)', cursor: 'pointer' }}
            >
              Tout deplier
            </button>
            <span style={{ color: 'var(--azals-border)' }}>|</span>
            <button
              type="button"
              onClick={collapseAll}
              style={{ background: 'none', border: 'none', color: 'var(--azals-primary)', cursor: 'pointer' }}
            >
              Tout replier
            </button>
            <span style={{ color: 'var(--azals-border)' }}>|</span>
            <button
              type="button"
              onClick={selectAll}
              style={{ background: 'none', border: 'none', color: 'var(--azals-success)', cursor: 'pointer' }}
            >
              Tout activer
            </button>
            <span style={{ color: 'var(--azals-border)' }}>|</span>
            <button
              type="button"
              onClick={deselectAll}
              style={{ background: 'none', border: 'none', color: 'var(--azals-danger)', cursor: 'pointer' }}
            >
              Tout desactiver
            </button>
          </div>
        </div>

        {/* Compteur */}
        <div style={{ fontSize: '14px', color: 'var(--azals-text-muted)', marginBottom: '12px' }}>
          <strong style={{ color: 'var(--azals-primary)' }}>{selectedCount}</strong> / {totalCaps} permissions actives
        </div>

        {/* Liste des modules */}
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--azals-text-muted)' }}>
            Chargement des modules...
          </div>
        ) : modulesError ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--azals-danger)' }}>
            <p>Erreur lors du chargement des modules</p>
            <p style={{ fontSize: '12px', marginTop: '8px', color: 'var(--azals-text-muted)' }}>
              {String((modulesError as Error)?.message || modulesError)}
            </p>
          </div>
        ) : !hasModules ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--azals-text-muted)' }}>
            <p>Aucun module disponible.</p>
            <p style={{ fontSize: '12px', marginTop: '8px' }}>Les modules seront affiches ici.</p>
          </div>
        ) : (
          <div style={{
            maxHeight: '400px',
            overflowY: 'auto',
            border: '1px solid var(--azals-border)',
            borderRadius: 'var(--azals-radius)'
          }}>
            {filteredModules.map(([moduleKey, module]) => {
              const moduleCodes = module.capabilities.map(c => c.code);
              const selectedInModule = moduleCodes.filter(c => selectedCaps.has(c)).length;
              const allSelected = selectedInModule === moduleCodes.length && moduleCodes.length > 0;
              const someSelected = selectedInModule > 0 && !allSelected;
              const isExpanded = expandedModules.has(moduleKey);

              return (
                <div key={moduleKey} style={{ borderBottom: '1px solid var(--azals-border-light)' }}>
                  {/* Header du module */}
                  <div
                    onClick={() => toggleExpandModule(moduleKey)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 16px',
                      background: 'var(--azals-bg)',
                      cursor: 'pointer'
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={allSelected}
                      ref={(el) => { if (el) el.indeterminate = someSelected; }}
                      onChange={(e) => {
                        e.stopPropagation();
                        toggleModule(moduleKey);
                      }}
                      onClick={(e) => e.stopPropagation()}
                      style={{ width: '16px', height: '16px', accentColor: 'var(--azals-primary)' }}
                    />
                    <span style={{ fontWeight: 500, flex: 1 }}>{module.name}</span>
                    <span className="azals-badge azals-badge--blue" style={{ fontSize: '11px' }}>
                      {selectedInModule}/{moduleCodes.length}
                    </span>
                    <span style={{ color: 'var(--azals-text-muted)', fontSize: '12px' }}>
                      {isExpanded ? '▼' : '▶'}
                    </span>
                  </div>

                  {/* Capabilities du module */}
                  {isExpanded && (
                    <div style={{ padding: '8px 16px 8px 44px', background: 'var(--azals-surface)' }}>
                      {module.capabilities
                        .filter(cap => {
                          if (!searchTerm) return true;
                          const term = searchTerm.toLowerCase();
                          return cap.name.toLowerCase().includes(term) ||
                                 cap.code.toLowerCase().includes(term);
                        })
                        .map(cap => (
                          <label
                            key={cap.code}
                            style={{
                              display: 'flex',
                              alignItems: 'flex-start',
                              gap: '10px',
                              padding: '8px',
                              borderRadius: 'var(--azals-radius)',
                              cursor: 'pointer'
                            }}
                          >
                            <input
                              type="checkbox"
                              checked={selectedCaps.has(cap.code)}
                              onChange={() => toggleCapability(cap.code)}
                              style={{ width: '14px', height: '14px', marginTop: '2px', accentColor: 'var(--azals-primary)' }}
                            />
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ fontWeight: 500, fontSize: '13px' }}>{cap.name}</div>
                              <div style={{ fontSize: '12px', color: 'var(--azals-text-muted)' }}>{cap.description}</div>
                              <code style={{ fontSize: '11px', color: 'var(--azals-text-light)' }}>{cap.code}</code>
                            </div>
                          </label>
                        ))}
                    </div>
                  )}
                </div>
              );
            })}

            {filteredModules.length === 0 && hasModules && (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--azals-text-muted)' }}>
                Aucun module trouve pour "{searchTerm}"
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '8px',
          paddingTop: '16px',
          marginTop: '16px',
          borderTop: '1px solid var(--azals-border)'
        }}>
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button
            onClick={handleSave}
            isLoading={updatePermissions.isPending}
            disabled={!hasModules}
          >
            Enregistrer ({selectedCount})
          </Button>
        </div>
      </div>
    </Modal>
  );
};

// ============================================================================
// COMPOSANT LISTE UTILISATEURS AVEC PERMISSIONS
// ============================================================================

const UsersPermissionsView: React.FC = () => {
  const { data: users = [], isLoading } = useUsers({});
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [showPermissionsModal, setShowPermissionsModal] = useState(false);

  const handleOpenPermissions = (user: User) => {
    setSelectedUser(user);
    setShowPermissionsModal(true);
  };

  const columns: TableColumn<User>[] = [
    { id: 'username', header: 'Utilisateur', accessor: 'username' },
    { id: 'email', header: 'Email', accessor: 'email' },
    { id: 'last_name', header: 'Nom', accessor: 'last_name', render: (v, row) =>
      `${(row as User).first_name || ''} ${(row as User).last_name || ''}`.trim() || '-'
    },
    { id: 'role_name', header: 'Role', accessor: 'role_name', render: (v) => (v as string) || '-' },
    { id: 'actions', header: 'Permissions', accessor: 'id', render: (_, row) => {
      const user = row as User;
      return (
        <div onClick={(e) => e.stopPropagation()}>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleOpenPermissions(user)}
          >
            <Key size={14} className="mr-1" />
            Gerer
          </Button>
        </div>
      );
    }}
  ];

  return (
    <Card>
      <div className="mb-4">
        <h3 className="text-lg font-semibold">Gestion des Permissions par Utilisateur</h3>
        <p className="text-sm text-gray-500 mt-1">
          Configurez les acces specifiques a chaque module et fonctionnalite pour chaque utilisateur.
        </p>
      </div>
      <DataTable columns={columns} data={users} isLoading={isLoading} keyField="id"
          filterable />

      <UserPermissionsModal
        isOpen={showPermissionsModal}
        user={selectedUser}
        onClose={() => {
          setShowPermissionsModal(false);
          setSelectedUser(null);
        }}
      />
    </Card>
  );
};

// Interface pour les données du formulaire role
interface RoleFormData {
  code: string;
  name: string;
  description?: string;
  level: number;
  parent_code?: string;
  permission_codes?: string[];
  requires_approval: boolean;
  max_users?: number;
  is_active?: boolean;
}

// Composant formulaire separe pour eviter les problemes de focus
const RoleFormModal: React.FC<{
  isOpen: boolean;
  editingRole: Role | null;
  roles: Role[];
  onClose: () => void;
  onSubmit: (data: RoleFormData) => Promise<void>;
  isLoading: boolean;
}> = ({ isOpen, editingRole, roles, onClose, onSubmit, isLoading }) => {
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [level, setLevel] = useState(5);
  const [parentCode, setParentCode] = useState('');
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [requiresApproval, setRequiresApproval] = useState(false);
  const [maxUsers, setMaxUsers] = useState<string>('');
  const [isActive, setIsActive] = useState(true);
  const [showPermissions, setShowPermissions] = useState(false);

  const { data: permissions = [] } = usePermissions();

  // Grouper les permissions par module
  const permissionsByModule = permissions.reduce((acc, perm) => {
    const module = perm.module || 'Autre';
    if (!acc[module]) acc[module] = [];
    acc[module].push(perm);
    return acc;
  }, {} as Record<string, Permission[]>);

  // Reset form when modal opens/closes or editingRole changes
  React.useEffect(() => {
    if (isOpen) {
      setCode(editingRole?.code || '');
      setName(editingRole?.name || '');
      setDescription(editingRole?.description || '');
      setLevel(editingRole?.level ?? 5);
      setParentCode('');
      setSelectedPermissions(editingRole?.permissions || []);
      setRequiresApproval(editingRole?.requires_approval || false);
      setMaxUsers(editingRole?.max_users?.toString() || '');
      setIsActive(editingRole?.is_active !== false);
      setShowPermissions(false);
    }
  }, [isOpen, editingRole]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const data: RoleFormData = {
      code,
      name,
      description: description || undefined,
      level,
      requires_approval: requiresApproval,
      permission_codes: selectedPermissions.length > 0 ? selectedPermissions : undefined,
    };
    if (!editingRole && parentCode) {
      data.parent_code = parentCode;
    }
    if (maxUsers) {
      data.max_users = parseInt(maxUsers, 10);
    }
    if (editingRole) {
      data.is_active = isActive;
    }
    await onSubmit(data);
  };

  const togglePermission = (code: string) => {
    setSelectedPermissions(prev =>
      prev.includes(code) ? prev.filter(p => p !== code) : [...prev, code]
    );
  };

  const toggleModule = (moduleName: string) => {
    const moduleCodes = permissionsByModule[moduleName].map(p => p.code);
    const allSelected = moduleCodes.every(c => selectedPermissions.includes(c));
    if (allSelected) {
      setSelectedPermissions(prev => prev.filter(p => !moduleCodes.includes(p)));
    } else {
      setSelectedPermissions(prev => [...new Set([...prev, ...moduleCodes])]);
    }
  };

  if (!isOpen) return null;

  // Filtrer les rôles pour le parent (exclure le rôle en cours d'édition)
  const availableParentRoles = roles.filter(r => r.id !== editingRole?.id);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={editingRole ? `Modifier: ${editingRole.name}` : 'Nouveau role'}
    >
      <form onSubmit={handleSubmit} className="max-h-[70vh] overflow-y-auto">
        <div className="space-y-4">
          {/* Code */}
          <div className="azals-field">
            <label className="block text-sm font-medium mb-1">Code *</label>
            <input
              type="text"
              className="azals-input w-full px-3 py-2 border rounded-md uppercase"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, ''))}
              disabled={!!editingRole}
              placeholder="Ex: MANAGER, COMPTABLE..."
              autoFocus={!editingRole}
              required
            />
            {editingRole ? (
              <small className="text-gray-500">Le code ne peut pas etre modifie</small>
            ) : (
              <small className="text-gray-500">Majuscules, chiffres et _ uniquement</small>
            )}
          </div>

          {/* Nom */}
          <div className="azals-field">
            <label className="block text-sm font-medium mb-1">Nom *</label>
            <input
              type="text"
              className="azals-input w-full px-3 py-2 border rounded-md"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Nom du role"
              autoFocus={!!editingRole}
              required
            />
          </div>

          {/* Description */}
          <div className="azals-field">
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              className="azals-input w-full px-3 py-2 border rounded-md"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description du role (optionnel)"
              rows={2}
            />
          </div>

          {/* Niveau et Parent en ligne */}
          <div className="grid grid-cols-2 gap-4">
            {/* Niveau */}
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Niveau (0-10)</label>
              <input
                type="number"
                className="azals-input w-full px-3 py-2 border rounded-md"
                value={level}
                onChange={(e) => setLevel(Math.max(0, Math.min(10, parseInt(e.target.value) || 0)))}
                min={0}
                max={10}
              />
              <small className="text-gray-500">0 = plus eleve</small>
            </div>

            {/* Role parent (creation uniquement) */}
            {!editingRole && (
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Role parent</label>
                <select
                  className="azals-input w-full px-3 py-2 border rounded-md"
                  value={parentCode}
                  onChange={(e) => setParentCode(e.target.value)}
                >
                  <option value="">Aucun</option>
                  {availableParentRoles.map(r => (
                    <option key={r.id} value={r.code}>{r.name}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Actif (modification uniquement) */}
            {editingRole && (
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Statut</label>
                <select
                  className="azals-input w-full px-3 py-2 border rounded-md"
                  value={isActive ? 'true' : 'false'}
                  onChange={(e) => setIsActive(e.target.value === 'true')}
                >
                  <option value="true">Actif</option>
                  <option value="false">Inactif</option>
                </select>
              </div>
            )}
          </div>

          {/* Options */}
          <div className="grid grid-cols-2 gap-4">
            {/* Max utilisateurs */}
            <div className="azals-field">
              <label className="block text-sm font-medium mb-1">Max utilisateurs</label>
              <input
                type="number"
                className="azals-input w-full px-3 py-2 border rounded-md"
                value={maxUsers}
                onChange={(e) => setMaxUsers(e.target.value)}
                placeholder="Illimite"
                min={1}
              />
            </div>

            {/* Requiert approbation */}
            <div className="azals-field flex items-center pt-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={requiresApproval}
                  onChange={(e) => setRequiresApproval(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm">Requiert approbation</span>
              </label>
            </div>
          </div>

          {/* Permissions */}
          <div className="azals-field">
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium">
                Permissions ({selectedPermissions.length} selectionnees)
              </label>
              <button
                type="button"
                className="text-sm text-blue-600 hover:underline"
                onClick={() => setShowPermissions(!showPermissions)}
              >
                {showPermissions ? 'Masquer' : 'Afficher'}
              </button>
            </div>

            {showPermissions && (
              <div className="border rounded-md p-3 max-h-48 overflow-y-auto bg-gray-50">
                {Object.keys(permissionsByModule).length === 0 ? (
                  <p className="text-gray-500 text-sm">Aucune permission disponible</p>
                ) : (
                  Object.entries(permissionsByModule).map(([module, perms]) => {
                    const allSelected = perms.every(p => selectedPermissions.includes(p.code));
                    const someSelected = perms.some(p => selectedPermissions.includes(p.code));
                    return (
                      <div key={module} className="mb-3">
                        <label className="flex items-center gap-2 font-medium text-sm cursor-pointer">
                          <input
                            type="checkbox"
                            checked={allSelected}
                            ref={(el) => { if (el) el.indeterminate = someSelected && !allSelected; }}
                            onChange={() => toggleModule(module)}
                            className="w-4 h-4"
                          />
                          {module}
                        </label>
                        <div className="ml-6 mt-1 space-y-1">
                          {perms.map(perm => (
                            <label key={perm.code} className="flex items-center gap-2 text-sm cursor-pointer">
                              <input
                                type="checkbox"
                                checked={selectedPermissions.includes(perm.code)}
                                onChange={() => togglePermission(perm.code)}
                                className="w-3 h-3"
                              />
                              <span>{perm.name}</span>
                              <span className="text-gray-400 text-xs">({perm.code})</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-4 pt-4 border-t">
          <Button variant="secondary" type="button" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" isLoading={isLoading}>
            {editingRole ? 'Enregistrer' : 'Creer'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

const RolesView: React.FC = () => {
  const { data: roles = [], isLoading } = useRoles();
  const createRole = useCreateRole();
  const updateRole = useUpdateRole();
  const deleteRole = useDeleteRole();

  const [showModal, setShowModal] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);

  const handleOpenCreate = () => {
    setEditingRole(null);
    setShowModal(true);
  };

  const handleOpenEdit = (role: Role) => {
    setEditingRole(role);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingRole(null);
  };

  const handleSubmit = async (data: RoleFormData) => {
    if (editingRole) {
      await updateRole.mutateAsync({
        id: editingRole.id,
        data: {
          name: data.name,
          description: data.description,
          level: data.level,
          requires_approval: data.requires_approval,
          max_users: data.max_users,
          is_active: data.is_active
        }
      });
    } else {
      await createRole.mutateAsync({
        code: data.code,
        name: data.name,
        description: data.description,
        level: data.level,
        parent_code: data.parent_code,
        permission_codes: data.permission_codes,
        requires_approval: data.requires_approval,
        max_users: data.max_users
      });
    }
    handleCloseModal();
  };

  const handleDelete = async (role: Role) => {
    if (role.is_system) {
      alert('Impossible de supprimer un role systeme.');
      return;
    }
    if (role.user_count > 0) {
      alert(`Ce role est assigne a ${role.user_count} utilisateur(s). Retirez-les d'abord.`);
      return;
    }
    if (confirm(`Supprimer le role "${role.name}" ?`)) {
      await deleteRole.mutateAsync(role.id);
    }
  };

  const columns: TableColumn<Role>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'description', header: 'Description', accessor: 'description', render: (v) => (v as string) || '-' },
    { id: 'permissions', header: 'Permissions', accessor: 'permissions', render: (v) => <Badge color="purple">{(v as string[])?.length || 0}</Badge> },
    { id: 'user_count', header: 'Utilisateurs', accessor: 'user_count', render: (v) => <Badge color="blue">{v as number}</Badge> },
    { id: 'created_by', header: 'Createur', accessor: 'is_system', render: (_, row) => {
      const role = row as Role;
      if (role.is_system) {
        return <Badge color="orange">Systeme</Badge>;
      }
      return <span className="text-gray-700">{role.created_by_name || 'Utilisateur'}</span>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => {
      const role = row as Role;
      return (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <Button size="sm" variant="secondary" onClick={() => handleOpenEdit(role)}>
            <Edit3 size={14} />
          </Button>
          {!role.is_system && role.user_count === 0 && (
            <Button
              size="sm"
              variant="danger"
              onClick={() => handleDelete(role)}
            >
              <Trash2 size={14} />
            </Button>
          )}
        </div>
      );
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Roles</h3>
        <Button onClick={handleOpenCreate}>Nouveau role</Button>
      </div>
      <DataTable columns={columns} data={roles} isLoading={isLoading} keyField="id"
          filterable />

      <RoleFormModal
        isOpen={showModal}
        editingRole={editingRole}
        roles={roles}
        onClose={handleCloseModal}
        onSubmit={handleSubmit}
        isLoading={createRole.isPending || updateRole.isPending}
      />
    </Card>
  );
};

// Hooks pour les actions tenant
const useSuspendTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tenantId: string) => {
      const res = await api.post(`/tenants/${tenantId}/suspend`);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] })
  });
};

const useActivateTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tenantId: string) => {
      const res = await api.post(`/tenants/${tenantId}/activate`);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] })
  });
};

const useCancelTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tenantId: string) => {
      const res = await api.post(`/tenants/${tenantId}/cancel`);
      return unwrapApiResponse(res);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'tenants'] })
  });
};

const useUpdateTenant = () => {
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

const TenantsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterPlan, setFilterPlan] = useState<string>('');
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editData, setEditData] = useState<Partial<Tenant>>({});

  // Charger les modules depuis l'API (source unique)
  const { data: modulesData } = useAvailableModules();
  const availableModules = modulesData?.modules || [];
  const modulesByCategory = modulesData?.modules_by_category || {};

  const { data: tenants = [], isLoading } = useTenants({
    status: filterStatus || undefined,
    plan: filterPlan || undefined
  });

  const suspendTenant = useSuspendTenant();
  const activateTenant = useActivateTenant();
  const cancelTenant = useCancelTenant();
  const updateTenant = useUpdateTenant();

  const handleEdit = (tenant: Tenant) => {
    setSelectedTenant(tenant);
    setEditData({
      name: tenant.name,
      max_users: tenant.max_users || 0,
      max_storage_gb: tenant.max_storage_gb || 0,
      modules_enabled: tenant.modules_enabled || [],
    });
    setShowEditModal(true);
  };

  const toggleModule = (moduleCode: string) => {
    const current = editData.modules_enabled || [];
    if (current.includes(moduleCode)) {
      setEditData({ ...editData, modules_enabled: current.filter(m => m !== moduleCode) });
    } else {
      setEditData({ ...editData, modules_enabled: [...current, moduleCode] });
    }
  };

  const handleSaveEdit = async () => {
    if (selectedTenant) {
      try {
        // Envoi direct - memes noms de champs que le backend
        await updateTenant.mutateAsync({
          tenantId: selectedTenant.tenant_id,
          data: editData
        });
        setShowEditModal(false);
        setSelectedTenant(null);
      } catch (err: unknown) {
        alert('Erreur: ' + (err instanceof Error ? err.message : String(err)));
      }
    }
  };

  const handleSuspend = async (tenant: Tenant) => {
    if (confirm(`Suspendre le tenant "${tenant.name}" ?`)) {
      await suspendTenant.mutateAsync(tenant.tenant_id);
    }
  };

  const handleActivate = async (tenant: Tenant) => {
    await activateTenant.mutateAsync(tenant.tenant_id);
  };

  const handleCancel = async (tenant: Tenant) => {
    if (confirm(`ATTENTION: Annuler definitivement le tenant "${tenant.name}" ? Cette action est irreversible.`)) {
      await cancelTenant.mutateAsync(tenant.tenant_id);
    }
  };

  const columns: TableColumn<Tenant>[] = [
    { id: 'tenant_id', header: 'Code', accessor: 'tenant_id', render: (v) => <code className="font-mono text-xs">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'plan', header: 'Plan', accessor: 'plan', render: (v) => {
      const info = TENANT_PLANS.find(p => p.value === (v as string));
      return <Badge color="blue">{info?.label || (v as string)}</Badge>;
    }},
    { id: 'max_users', header: 'Utilisateurs max', accessor: 'max_users', render: (v) => (
      <span className="text-sm">{v as number}</span>
    )},
    { id: 'storage_used_gb', header: 'Stockage', accessor: 'storage_used_gb', render: (v, row) => {
      const tenant = row as Tenant;
      const used = (v as number) || 0;
      const max = tenant.max_storage_gb || 0;
      const percent = max > 0 ? Math.round((used / max) * 100) : 0;
      return (
        <div className="text-sm">
          <span className={percent > 90 ? 'text-red-600 font-semibold' : ''}>{used} Go</span>
          {max > 0 && <span className="text-gray-400">/{max} Go</span>}
        </div>
      );
    }},
    { id: 'modules', header: 'Modules', accessor: 'modules_enabled', render: (v) => {
      const modules = v as string[];
      return <span className="text-sm text-gray-600">{modules?.length || 0} actifs</span>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(TENANT_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => {
      const tenant = row as Tenant;
      return (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <Button size="sm" variant="secondary" onClick={() => handleEdit(tenant)}>
            <Edit3 size={14} />
          </Button>
          {tenant.status === 'ACTIVE' ? (
            <Button size="sm" variant="warning" onClick={() => handleSuspend(tenant)}>
              <Lock size={14} />
            </Button>
          ) : tenant.status === 'SUSPENDED' ? (
            <Button size="sm" variant="success" onClick={() => handleActivate(tenant)}>
              <Unlock size={14} />
            </Button>
          ) : null}
        </div>
      );
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Tenants</h3>
        <div className="flex gap-2">
          <Select
            value={filterPlan}
            onChange={(val) => setFilterPlan(val)}
            options={[{ value: '', label: 'Tous les plans' }, ...TENANT_PLANS]}
            className="w-36"
          />
          <Select
            value={filterStatus}
            onChange={(val) => setFilterStatus(val)}
            options={[{ value: '', label: 'Tous statuts' }, ...TENANT_STATUSES]}
            className="w-32"
          />
        </div>
      </div>
      <DataTable columns={columns} data={tenants} isLoading={isLoading} keyField="id"
          filterable />

      <Modal isOpen={showEditModal} onClose={() => setShowEditModal(false)} title={`Modifier: ${selectedTenant?.name}`} size="lg">
        <div className="space-y-6">
          {/* Informations generales */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Building size={16} />
              Informations generales
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="azals-field">
                <label>Nom</label>
                <Input
                  value={editData.name || ''}
                  onChange={(v) => setEditData({ ...editData, name: v })}
                />
              </div>
              <div className="azals-field">
                <label>Utilisateurs max</label>
                <Input
                  type="number"
                  value={String(editData.max_users || 0)}
                  onChange={(v) => setEditData({ ...editData, max_users: parseInt(v) || 0 })}
                />
              </div>
              <div className="azals-field">
                <label>Stockage max (Go)</label>
                <Input
                  type="number"
                  value={String(editData.max_storage_gb || 0)}
                  onChange={(v) => setEditData({ ...editData, max_storage_gb: parseInt(v) || 0 })}
                />
                <span className="text-xs text-gray-500">Utilise: {selectedTenant?.storage_used_gb || 0} Go</span>
              </div>
            </div>
          </div>

          {/* Modules - groupes par categorie */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Package size={16} />
              Modules actives ({(editData.modules_enabled || []).length}/{availableModules.length})
            </h4>
            <div className="max-h-64 overflow-y-auto border rounded bg-gray-50 p-2 space-y-4">
              {Object.entries(modulesByCategory).map(([category, mods]) => (
                <div key={category}>
                  <h5 className="text-xs font-bold text-gray-600 uppercase mb-2 sticky top-0 bg-gray-50 py-1">
                    {category}
                  </h5>
                  <div className="grid grid-cols-2 gap-2">
                    {mods.map((mod) => {
                      const isEnabled = (editData.modules_enabled || []).includes(mod.code);
                      return (
                        <label
                          key={mod.code}
                          className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                            isEnabled ? 'bg-blue-50 border border-blue-200' : 'bg-white border border-gray-200 hover:bg-gray-100'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isEnabled}
                            onChange={() => toggleModule(mod.code)}
                            className="rounded text-blue-600"
                          />
                          <div>
                            <div className="text-sm font-medium">{mod.name}</div>
                            <div className="text-xs text-gray-500">{mod.description}</div>
                          </div>
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
            <div className="flex gap-2 mt-2">
              <button
                type="button"
                onClick={() => setEditData({ ...editData, modules_enabled: availableModules.map(m => m.code) })}
                className="text-xs text-blue-600 hover:underline"
              >
                Tout selectionner
              </button>
              <button
                type="button"
                onClick={() => setEditData({ ...editData, modules_enabled: [] })}
                className="text-xs text-gray-600 hover:underline"
              >
                Tout deselectionner
              </button>
            </div>
          </div>

          {/* Actions dangereuses */}
          {selectedTenant && selectedTenant.status !== 'SUSPENDED' && (
            <div className="pt-4 border-t border-red-200 bg-red-50 -mx-6 px-6 pb-4 rounded-b">
              <h4 className="text-sm font-semibold text-red-700 mb-2 flex items-center gap-2">
                <AlertTriangle size={16} />
                Zone de danger
              </h4>
              <Button
                variant="danger"
                size="sm"
                onClick={() => {
                  handleCancel(selectedTenant);
                  setShowEditModal(false);
                }}
              >
                Annuler ce tenant definitivement
              </Button>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="secondary" onClick={() => setShowEditModal(false)}>Annuler</Button>
            <Button onClick={handleSaveEdit} isLoading={updateTenant.isPending}>Enregistrer</Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
};

const AuditView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const { data: logs = [], isLoading } = useAuditLogs({
    resource_type: filterType || undefined
  });

  const resourceTypes = [...new Set(logs.map(l => l.resource_type))].map(t => ({ value: t, label: t }));

  const columns: TableColumn<AuditLog>[] = [
    { id: 'timestamp', header: 'Date', accessor: 'timestamp', render: (v) => formatDateTimeFn(v as string) },
    { id: 'user_name', header: 'Utilisateur', accessor: 'user_name', render: (v) => (v as string) || 'Systeme' },
    { id: 'action', header: 'Action', accessor: 'action' },
    { id: 'resource_type', header: 'Type', accessor: 'resource_type', render: (v) => <Badge color="blue">{v as string}</Badge> },
    { id: 'resource_id', header: 'ID Ressource', accessor: 'resource_id', render: (v) => (v as string) ? <code className="font-mono text-xs">{v as string}</code> : '-' },
    { id: 'ip_address', header: 'IP', accessor: 'ip_address', render: (v) => (v as string) || '-' }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Journal d'audit</h3>
        <Select
          value={filterType}
          onChange={(val) => setFilterType(val)}
          options={[{ value: '', label: 'Tous les types' }, ...resourceTypes]}
          className="w-48"
        />
      </div>
      <DataTable columns={columns} data={logs} isLoading={isLoading} keyField="id"
          filterable />
    </Card>
  );
};

const BackupsView: React.FC = () => {
  const { data: backups = [], isLoading } = useBackupConfigs();
  const runBackup = useRunBackup();

  const columns: TableColumn<BackupConfig>[] = [
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = BACKUP_TYPES.find(t => t.value === (v as string));
      return info?.label || (v as string);
    }},
    { id: 'schedule', header: 'Planification', accessor: 'schedule' },
    { id: 'destination', header: 'Destination', accessor: 'destination', render: (v) => {
      const info = BACKUP_DESTINATIONS.find(d => d.value === (v as string));
      return info?.label || (v as string);
    }},
    { id: 'retention_days', header: 'Retention', accessor: 'retention_days', render: (v) => `${v as number} jours` },
    { id: 'last_backup', header: 'Derniere', accessor: 'last_backup', render: (v) => (v as string) ? formatDateTimeFn(v as string) : '-' },
    { id: 'last_status', header: 'Statut', accessor: 'last_status', render: (v) => {
      if (!v) return '-';
      const colors: Record<string, string> = { SUCCESS: 'green', FAILED: 'red', IN_PROGRESS: 'orange' };
      return <Badge color={colors[v as string] || 'gray'}>{v as string}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (v, row) => (
      (row as BackupConfig).is_active ? (
        <Button size="sm" onClick={() => runBackup.mutate((row as BackupConfig).id)}>Lancer</Button>
      ) : null
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Sauvegardes</h3>
        <Button>Nouvelle config</Button>
      </div>
      <DataTable columns={columns} data={backups} isLoading={isLoading} keyField="id"
          filterable />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'users' | 'permissions' | 'roles' | 'tenants' | 'sequences' | 'enrichment' | 'audit' | 'backups';

const AdminDashboardView: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: dashboard } = useAdminDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'users', label: 'Utilisateurs' },
    { id: 'permissions', label: 'Acces Modules' },
    { id: 'roles', label: 'Roles' },
    { id: 'tenants', label: 'Tenants' },
    { id: 'sequences', label: 'Numerotation' },
    { id: 'enrichment', label: 'Enrichissement' },
    { id: 'audit', label: 'Audit' },
    { id: 'backups', label: 'Sauvegardes' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'users':
        return <UsersView />;
      case 'permissions':
        return <UsersPermissionsView />;
      case 'roles':
        return <RolesView />;
      case 'tenants':
        return <TenantsView />;
      case 'sequences':
        return <SequencesView />;
      case 'enrichment':
        return <EnrichmentProvidersView />;
      case 'audit':
        return <AuditView />;
      case 'backups':
        return <BackupsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Utilisateurs actifs"
                value={`${dashboard?.active_users || 0} / ${dashboard?.total_users || 0}`}
                icon={<Users size={20} />}
                variant="default"
                onClick={() => setCurrentView('users')}
              />
              <StatCard
                title="Tenants actifs"
                value={`${dashboard?.active_tenants || 0} / ${dashboard?.total_tenants || 0}`}
                icon={<Building size={20} />}
                variant="default"
                onClick={() => setCurrentView('tenants')}
              />
              <StatCard
                title="Roles"
                value={String(dashboard?.total_roles || 0)}
                icon={<Shield size={20} />}
                variant="success"
                onClick={() => setCurrentView('roles')}
              />
              <StatCard
                title="Stockage utilise"
                value={`${dashboard?.storage_used_gb || 0} GB`}
                icon={<Database size={20} />}
                variant="warning"
              />
            </Grid>
            <Grid cols={2}>
              <StatCard
                title="Appels API (aujourd'hui)"
                value={String(dashboard?.api_calls_today || 0)}
                icon={<Activity size={20} />}
                variant="default"
              />
              <StatCard
                title="Erreurs (aujourd'hui)"
                value={String(dashboard?.errors_today || 0)}
                icon={<AlertTriangle size={20} />}
                variant={dashboard?.errors_today ? 'danger' : 'success'}
                onClick={() => setCurrentView('audit')}
              />
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Administration" subtitle="Gestion des utilisateurs, roles et systeme">
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

const AdminModule: React.FC = () => {
  return (
    <Routes>
      <Route path="users/:id" element={<UserDetailView />} />
      <Route path="*" element={<AdminDashboardView />} />
    </Routes>
  );
};

export default AdminModule;
