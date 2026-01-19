/**
 * AZALSCORE Module - Administration
 * Utilisateurs, Rôles, Capacités, Tenants, Modules, Logs
 * Données fournies par API - AUCUNE logique métier
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Users,
  Shield,
  Building2,
  Puzzle,
  FileText,
  Plus,
  Edit,
  Trash2,
  Key,
  Lock,
  Unlock,
  AlertTriangle,
  Palette,
} from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard, useCanBreakGlass } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { DynamicForm } from '@ui/forms';
import { Button, ButtonGroup, Modal, ConfirmDialog } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import { z } from 'zod';
import type { PaginatedResponse, TableColumn, DashboardKPI, User, Tenant, ModuleInfo } from '@/types';

// ============================================================
// TYPES
// ============================================================

interface AdminUser extends User {
  created_at: string;
  last_login?: string;
  login_count: number;
}

interface Role {
  id: string;
  name: string;
  description: string;
  capabilities: string[];
  user_count: number;
  is_system: boolean;
}

interface Capability {
  code: string;
  name: string;
  description: string;
  module: string;
  is_sensitive: boolean;
}

interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details?: Record<string, unknown>;
  ip_address: string;
}

interface AdminStats {
  total_users: number;
  active_users: number;
  total_roles: number;
  total_tenants: number;
  active_modules: number;
}

// ============================================================
// API HOOKS
// ============================================================

const useAdminStats = () => {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: async () => {
      const response = await api.get<AdminStats>('/v1/admin/stats');
      return response.data;
    },
  });
};

const useUsers = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['admin', 'users', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<AdminUser>>(
        `/v1/admin/users?page=${page}&page_size=${pageSize}`
      );
      return response.data;
    },
  });
};

const useRoles = () => {
  return useQuery({
    queryKey: ['admin', 'roles'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Role>>('/v1/admin/roles');
      return response;
    },
  });
};

const useCapabilitiesList = () => {
  return useQuery({
    queryKey: ['admin', 'capabilities'],
    queryFn: async () => {
      const response = await api.get<Capability[]>('/v1/admin/capabilities');
      return response.data;
    },
  });
};

const useTenants = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['admin', 'tenants', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Tenant>>(
        `/v1/admin/tenants?page=${page}&page_size=${pageSize}`
      );
      return response.data;
    },
  });
};

const useModules = () => {
  return useQuery({
    queryKey: ['admin', 'modules'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<ModuleInfo>>('/v1/admin/modules');
      return response.data;
    },
  });
};

const useAuditLogs = (page = 1, pageSize = 50) => {
  return useQuery({
    queryKey: ['admin', 'logs', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<AuditLog>>(
        `/v1/admin/audit-logs?page=${page}&page_size=${pageSize}`
      );
      return response.data;
    },
  });
};

const useCreateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<AdminUser>) => {
      const response = await api.post<AdminUser>('/v1/admin/users', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
};

const useUpdateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<AdminUser> }) => {
      const response = await api.put<AdminUser>(`/v1/admin/users/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
};

const useToggleUserActive = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, active }: { id: string; active: boolean }) => {
      await api.post(`/v1/admin/users/${id}/${active ? 'activate' : 'deactivate'}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
};

// ============================================================
// ADMIN DASHBOARD
// ============================================================

export const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: stats, isLoading } = useAdminStats();
  const canBreakGlass = useCanBreakGlass();

  const kpis: DashboardKPI[] = stats
    ? [
        {
          id: 'users',
          label: 'Utilisateurs',
          value: stats.total_users,
          trend: 'stable',
        },
        {
          id: 'active_users',
          label: 'Utilisateurs actifs',
          value: stats.active_users,
        },
        {
          id: 'roles',
          label: 'Rôles',
          value: stats.total_roles,
        },
        {
          id: 'modules',
          label: 'Modules actifs',
          value: stats.active_modules,
        },
      ]
    : [];

  return (
    <PageWrapper title="Administration" subtitle="Gestion du système">
      {isLoading ? (
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      ) : (
        <>
          <section className="azals-section">
            <Grid cols={4} gap="md">
              {kpis.map((kpi) => (
                <KPICard key={kpi.id} kpi={kpi} />
              ))}
            </Grid>
          </section>

          <section className="azals-section">
            <Grid cols={3} gap="md">
              <Card
                title="Utilisateurs"
                className="azals-admin-card"
                actions={
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/admin/users')}
                  >
                    Gérer
                  </Button>
                }
              >
                <div className="azals-admin-card__icon">
                  <Users size={32} />
                </div>
                <p>Gérer les comptes utilisateurs, leurs rôles et permissions.</p>
              </Card>

              <Card
                title="Rôles & Capacités"
                className="azals-admin-card"
                actions={
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/admin/roles')}
                  >
                    Gérer
                  </Button>
                }
              >
                <div className="azals-admin-card__icon">
                  <Shield size={32} />
                </div>
                <p>Définir les rôles et attribuer les capacités d'accès.</p>
              </Card>

              <Card
                title="Tenants"
                className="azals-admin-card"
                actions={
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/admin/tenants')}
                  >
                    Gérer
                  </Button>
                }
              >
                <div className="azals-admin-card__icon">
                  <Building2 size={32} />
                </div>
                <p>Gérer les organisations clientes et leurs paramètres.</p>
              </Card>

              <Card
                title="Modules"
                className="azals-admin-card"
                actions={
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/admin/modules')}
                  >
                    Gérer
                  </Button>
                }
              >
                <div className="azals-admin-card__icon">
                  <Puzzle size={32} />
                </div>
                <p>Activer ou désactiver les modules du système.</p>
              </Card>

              <Card
                title="Journaux d'audit"
                className="azals-admin-card"
                actions={
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/admin/logs')}
                  >
                    Consulter
                  </Button>
                }
              >
                <div className="azals-admin-card__icon">
                  <FileText size={32} />
                </div>
                <p>Consulter l'historique des actions système.</p>
              </Card>

              <Card
                title="Personnalisation"
                className="azals-admin-card"
                actions={
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/admin/branding')}
                  >
                    Configurer
                  </Button>
                }
              >
                <div className="azals-admin-card__icon">
                  <Palette size={32} />
                </div>
                <p>Modifier le favicon, logo et identité visuelle.</p>
              </Card>

              {/* Break-Glass - Visible UNIQUEMENT si capacité présente */}
              {canBreakGlass && (
                <Card
                  title="Break-Glass Souverain"
                  className="azals-admin-card azals-admin-card--danger"
                  actions={
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => navigate('/admin/break-glass')}
                    >
                      Accéder
                    </Button>
                  }
                >
                  <div className="azals-admin-card__icon azals-admin-card__icon--danger">
                    <AlertTriangle size={32} />
                  </div>
                  <p>Procédure d'urgence - Accès réservé au créateur.</p>
                </Card>
              )}
            </Grid>
          </section>
        </>
      )}
    </PageWrapper>
  );
};

// ============================================================
// USERS MANAGEMENT
// ============================================================

export const UsersPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const { data, isLoading, refetch } = useUsers(page, pageSize);
  const { data: rolesData } = useRoles(); // Pre-fetch roles for modal
  const toggleActive = useToggleUserActive();

  const columns: TableColumn<AdminUser>[] = [
    {
      id: 'email',
      header: 'Email',
      accessor: 'email',
      sortable: true,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      sortable: true,
    },
    {
      id: 'roles',
      header: 'Rôles',
      accessor: 'roles',
      render: (value) => (value as string[]).join(', '),
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Actif</span>
        ) : (
          <span className="azals-badge azals-badge--red">Inactif</span>
        ),
    },
    {
      id: 'last_login',
      header: 'Dernière connexion',
      accessor: 'last_login',
      render: (value) =>
        value ? new Date(value as string).toLocaleString('fr-FR') : 'Jamais',
    },
  ];

  const actions = [
    {
      id: 'edit',
      label: 'Modifier',
      capability: 'admin.users.edit',
      onClick: (row: AdminUser) => navigate(`/admin/users/${row.id}/edit`),
    },
    {
      id: 'toggle',
      label: 'Activer/Désactiver',
      capability: 'admin.users.edit',
      onClick: (row: AdminUser) =>
        toggleActive.mutate({ id: row.id, active: !row.is_active }),
    },
    {
      id: 'reset-password',
      label: 'Réinitialiser mot de passe',
      capability: 'admin.users.edit',
      onClick: (row: AdminUser) => {
        // Reset password logic
      },
    },
  ];

  return (
    <PageWrapper
      title="Utilisateurs"
      actions={
        <CapabilityGuard capability="admin.users.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => setShowCreateModal(true)}>
            Nouvel utilisateur
          </Button>
        </CapabilityGuard>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          actions={actions}
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
        />
      </Card>

      {showCreateModal && (
        <UserFormModal onClose={() => setShowCreateModal(false)} />
      )}
    </PageWrapper>
  );
};

// ============================================================
// USER FORM MODAL
// ============================================================

const userCreateSchema = z.object({
  email: z.string().email('Email invalide'),
  password: z.string().min(8, 'Le mot de passe doit contenir au moins 8 caractères'),
  role: z.string().min(1, 'Un rôle est requis'),
});

const userEditSchema = z.object({
  email: z.string().email('Email invalide'),
  role: z.string().min(1, 'Un rôle est requis'),
});

interface UserFormModalProps {
  user?: AdminUser;
  onClose: () => void;
}

const UserFormModal: React.FC<UserFormModalProps> = ({ user, onClose }) => {
  const { data: roles, isLoading: rolesLoading } = useRoles();
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();

  const roleOptions = roles?.data.items.map((r: Role) => ({ value: r.id, label: r.name })) || [];

  const fields = user
    ? [
        {
          name: 'email',
          label: 'Email',
          type: 'email' as const,
          required: true,
          disabled: true,
        },
        {
          name: 'role',
          label: 'Rôle',
          type: 'select' as const,
          required: true,
          placeholder: rolesLoading ? 'Chargement...' : 'Sélectionner un rôle',
          options: roleOptions,
        },
      ]
    : [
        {
          name: 'email',
          label: 'Email',
          type: 'email' as const,
          required: true,
        },
        {
          name: 'password',
          label: 'Mot de passe',
          type: 'password' as const,
          required: true,
          placeholder: 'Minimum 8 caractères',
        },
        {
          name: 'role',
          label: 'Rôle',
          type: 'select' as const,
          required: true,
          placeholder: rolesLoading ? 'Chargement...' : 'Sélectionner un rôle',
          options: roleOptions,
        },
      ];

  const handleSubmit = async (data: z.infer<typeof userCreateSchema> | z.infer<typeof userEditSchema>) => {
    if (user) {
      const payload = {
        roles: [(data as z.infer<typeof userEditSchema>).role],
      };
      await updateUser.mutateAsync({ id: user.id, data: payload });
    } else {
      const createData = data as z.infer<typeof userCreateSchema>;
      const payload = {
        email: createData.email,
        password: createData.password,
        roles: [createData.role],
      };
      await createUser.mutateAsync(payload);
    }
    onClose();
  };

  // Transform user data for form (roles array -> single role)
  const defaultValues = user
    ? {
        email: user.email,
        role: user.roles?.[0] || '',
      }
    : undefined;

  return (
    <Modal
      isOpen
      onClose={onClose}
      title={user ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur'}
      size="md"
    >
      <DynamicForm
        fields={fields}
        schema={user ? userEditSchema : userCreateSchema}
        defaultValues={defaultValues}
        onSubmit={handleSubmit}
        onCancel={onClose}
        isLoading={createUser.isPending || updateUser.isPending || rolesLoading}
        submitLabel={user ? 'Enregistrer' : 'Créer'}
      />
    </Modal>
  );
};

// ============================================================
// ROLES MANAGEMENT
// ============================================================

export const RolesPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading } = useRoles();

  const columns: TableColumn<Role>[] = [
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
    },
    {
      id: 'description',
      header: 'Description',
      accessor: 'description',
    },
    {
      id: 'capabilities',
      header: 'Capacités',
      accessor: 'capabilities',
      render: (value) => `${(value as string[]).length} capacités`,
    },
    {
      id: 'user_count',
      header: 'Utilisateurs',
      accessor: 'user_count',
    },
    {
      id: 'is_system',
      header: 'Type',
      accessor: 'is_system',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--blue">Système</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Personnalisé</span>
        ),
    },
  ];

  const actions = [
    {
      id: 'view',
      label: 'Voir les capacités',
      onClick: (row: Role) => navigate(`/admin/roles/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      capability: 'admin.roles.edit',
      onClick: (row: Role) => navigate(`/admin/roles/${row.id}/edit`),
      isHidden: (row: Role) => row.is_system,
    },
  ];

  return (
    <PageWrapper
      title="Rôles & Capacités"
      actions={
        <CapabilityGuard capability="admin.roles.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/admin/roles/new')}>
            Nouveau rôle
          </Button>
        </CapabilityGuard>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.data.items || []}
          keyField="id"
          actions={actions}
          isLoading={isLoading}
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// AUDIT LOGS
// ============================================================

export const AuditLogsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  const { data, isLoading, refetch } = useAuditLogs(page, pageSize);

  const columns: TableColumn<AuditLog>[] = [
    {
      id: 'timestamp',
      header: 'Date/Heure',
      accessor: 'timestamp',
      sortable: true,
      render: (value) => new Date(value as string).toLocaleString('fr-FR'),
    },
    {
      id: 'user_email',
      header: 'Utilisateur',
      accessor: 'user_email',
    },
    {
      id: 'action',
      header: 'Action',
      accessor: 'action',
    },
    {
      id: 'resource_type',
      header: 'Ressource',
      accessor: 'resource_type',
    },
    {
      id: 'ip_address',
      header: 'Adresse IP',
      accessor: 'ip_address',
    },
  ];

  return (
    <PageWrapper title="Journaux d'audit">
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage="Aucun événement"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// BRANDING SETTINGS
// ============================================================

interface BrandingConfig {
  title: string;
  favicon_url: string;
  logo_url: string | null;
  primary_color: string;
  secondary_color: string;
  enable_tenant_branding: boolean;
}

const useBrandingConfig = () => {
  return useQuery({
    queryKey: ['admin', 'branding'],
    queryFn: async () => {
      const response = await api.get<BrandingConfig>('/v1/branding');
      return response.data;
    },
  });
};

export const BrandingPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: config, isLoading } = useBrandingConfig();
  const [faviconFile, setFaviconFile] = useState<File | null>(null);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [faviconPreview, setFaviconPreview] = useState<string | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleFaviconChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFaviconFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setFaviconPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setLogoFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setLogoPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const uploadFavicon = async () => {
    if (!faviconFile) return;
    setUploading(true);
    setMessage(null);
    try {
      const formData = new FormData();
      formData.append('file', faviconFile);
      await api.post('/v1/branding/favicon', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage({ type: 'success', text: 'Favicon mis à jour. Rechargez la page pour voir les changements.' });
      setFaviconFile(null);
      setFaviconPreview(null);
      queryClient.invalidateQueries({ queryKey: ['admin', 'branding'] });
    } catch (err) {
      setMessage({ type: 'error', text: 'Erreur lors de l\'upload du favicon' });
    } finally {
      setUploading(false);
    }
  };

  const uploadLogo = async () => {
    if (!logoFile) return;
    setUploading(true);
    setMessage(null);
    try {
      const formData = new FormData();
      formData.append('file', logoFile);
      await api.post('/v1/branding/logo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage({ type: 'success', text: 'Logo mis à jour avec succès.' });
      setLogoFile(null);
      setLogoPreview(null);
      queryClient.invalidateQueries({ queryKey: ['admin', 'branding'] });
    } catch (err) {
      setMessage({ type: 'error', text: 'Erreur lors de l\'upload du logo' });
    } finally {
      setUploading(false);
    }
  };

  const resetFavicon = async () => {
    setUploading(true);
    setMessage(null);
    try {
      await api.delete('/v1/branding/favicon');
      setMessage({ type: 'success', text: 'Favicon réinitialisé par défaut.' });
      queryClient.invalidateQueries({ queryKey: ['admin', 'branding'] });
    } catch (err) {
      setMessage({ type: 'error', text: 'Erreur lors de la réinitialisation' });
    } finally {
      setUploading(false);
    }
  };

  const resetLogo = async () => {
    setUploading(true);
    setMessage(null);
    try {
      await api.delete('/v1/branding/logo');
      setMessage({ type: 'success', text: 'Logo supprimé.' });
      queryClient.invalidateQueries({ queryKey: ['admin', 'branding'] });
    } catch (err) {
      setMessage({ type: 'error', text: 'Erreur lors de la suppression' });
    } finally {
      setUploading(false);
    }
  };

  if (isLoading) {
    return (
      <PageWrapper title="Personnalisation">
        <Card><p>Chargement...</p></Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper title="Personnalisation" subtitle="Favicon, logo et identité visuelle">
      {message && (
        <div style={{
          padding: '12px 16px',
          marginBottom: '16px',
          borderRadius: '8px',
          backgroundColor: message.type === 'success' ? '#dcfce7' : '#fee2e2',
          color: message.type === 'success' ? '#166534' : '#991b1b',
          border: `1px solid ${message.type === 'success' ? '#86efac' : '#fecaca'}`,
        }}>
          {message.text}
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Favicon */}
        <Card>
          <h3 style={{ marginBottom: '16px', fontSize: '16px', fontWeight: 600 }}>
            Favicon (icône onglet)
          </h3>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '8px',
              backgroundColor: '#f3f4f6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px dashed #d1d5db',
            }}>
              <img
                src={faviconPreview || config?.favicon_url || '/static/favicon.png'}
                alt="Favicon"
                style={{ maxWidth: '48px', maxHeight: '48px' }}
              />
            </div>
            <div>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>
                Favicon actuel
              </p>
              <p style={{ fontSize: '12px', color: '#9ca3af' }}>
                Format: PNG, ICO, JPG • Max: 2 MB
              </p>
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <input
              type="file"
              accept=".png,.ico,.jpg,.jpeg,.svg"
              onChange={handleFaviconChange}
              style={{ display: 'none' }}
              id="favicon-upload"
            />
            <label
              htmlFor="favicon-upload"
              style={{
                display: 'inline-block',
                padding: '8px 16px',
                backgroundColor: '#1e40af',
                color: 'white',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                marginRight: '8px',
              }}
            >
              Choisir un fichier
            </label>
            {faviconFile && (
              <span style={{ fontSize: '14px', color: '#374151' }}>
                {faviconFile.name}
              </span>
            )}
          </div>

          <ButtonGroup>
            <Button
              onClick={uploadFavicon}
              disabled={!faviconFile || uploading}
              variant="primary"
            >
              {uploading ? 'Upload...' : 'Enregistrer le favicon'}
            </Button>
            <Button
              onClick={resetFavicon}
              disabled={uploading}
              variant="secondary"
            >
              Réinitialiser
            </Button>
          </ButtonGroup>
        </Card>

        {/* Logo */}
        <Card>
          <h3 style={{ marginBottom: '16px', fontSize: '16px', fontWeight: 600 }}>
            Logo entreprise
          </h3>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            <div style={{
              width: '120px',
              height: '60px',
              borderRadius: '8px',
              backgroundColor: '#f3f4f6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px dashed #d1d5db',
            }}>
              {(logoPreview || config?.logo_url) ? (
                <img
                  src={logoPreview || config?.logo_url || ''}
                  alt="Logo"
                  style={{ maxWidth: '100px', maxHeight: '50px' }}
                />
              ) : (
                <span style={{ color: '#9ca3af', fontSize: '12px' }}>Aucun logo</span>
              )}
            </div>
            <div>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>
                Logo actuel
              </p>
              <p style={{ fontSize: '12px', color: '#9ca3af' }}>
                Format: PNG, JPG, SVG • Max: 2 MB
              </p>
            </div>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <input
              type="file"
              accept=".png,.jpg,.jpeg,.svg"
              onChange={handleLogoChange}
              style={{ display: 'none' }}
              id="logo-upload"
            />
            <label
              htmlFor="logo-upload"
              style={{
                display: 'inline-block',
                padding: '8px 16px',
                backgroundColor: '#1e40af',
                color: 'white',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                marginRight: '8px',
              }}
            >
              Choisir un fichier
            </label>
            {logoFile && (
              <span style={{ fontSize: '14px', color: '#374151' }}>
                {logoFile.name}
              </span>
            )}
          </div>

          <ButtonGroup>
            <Button
              onClick={uploadLogo}
              disabled={!logoFile || uploading}
              variant="primary"
            >
              {uploading ? 'Upload...' : 'Enregistrer le logo'}
            </Button>
            <Button
              onClick={resetLogo}
              disabled={uploading || !config?.logo_url}
              variant="secondary"
            >
              Supprimer
            </Button>
          </ButtonGroup>
        </Card>
      </Grid>

      {/* Info */}
      <Card style={{ marginTop: '24px' }}>
        <h3 style={{ marginBottom: '12px', fontSize: '16px', fontWeight: 600 }}>
          Informations
        </h3>
        <ul style={{ fontSize: '14px', color: '#6b7280', lineHeight: '1.8', paddingLeft: '20px' }}>
          <li>Le <strong>favicon</strong> apparaît dans l'onglet du navigateur (recommandé: 32x32 ou 64x64 pixels)</li>
          <li>Le <strong>logo</strong> peut être utilisé dans l'interface et les documents (recommandé: format horizontal)</li>
          <li>Les changements de favicon nécessitent un rechargement complet de la page (Ctrl+Shift+R)</li>
          <li>Formats supportés: PNG, JPG, ICO, SVG</li>
        </ul>
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// MODULE ROUTER
// ============================================================

export const AdminRoutes: React.FC = () => (
  <Routes>
    <Route index element={<AdminDashboard />} />
    <Route path="users" element={<UsersPage />} />
    <Route path="roles" element={<RolesPage />} />
    <Route path="logs" element={<AuditLogsPage />} />
    <Route path="branding" element={<BrandingPage />} />
  </Routes>
);

export default AdminRoutes;
