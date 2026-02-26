/**
 * AZALSCORE Module - Admin - UsersView
 * Vue de gestion des utilisateurs
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit3, Trash2 } from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { Select, Input } from '@ui/forms';
import { Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { useUsers, useRoles, useCreateUser, useUpdateUser, useDeleteUser, useUpdateUserStatus } from '../hooks';

// Types
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

const USER_STATUSES = [
  { value: 'ACTIVE', label: 'Actif', color: 'green' },
  { value: 'INACTIVE', label: 'Inactif', color: 'gray' },
  { value: 'SUSPENDED', label: 'Suspendu', color: 'red' },
  { value: 'PENDING', label: 'En attente', color: 'orange' }
];

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

const parseValidationErrors = (error: ValidationError): Record<string, string> => {
  const errors: Record<string, string> = {};
  try {
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
    if (window.confirm(`Etes-vous sur de vouloir supprimer l'utilisateur "${user.username}" ?`)) {
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
    { id: 'last_name', header: 'Nom', accessor: 'last_name', render: (_, row) =>
      `${(row as User).first_name || ''} ${(row as User).last_name || ''}`.trim() || '-'
    },
    { id: 'role_name', header: 'Role', accessor: 'role_name', render: (v) => (v as string) || '-' },
    { id: 'last_login', header: 'Derniere connexion', accessor: 'last_login', render: (v) => (v as string) ? formatDateTime(v as string) : 'Jamais' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v, row) => (
      <div onClick={(e) => e.stopPropagation()} role="presentation">
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
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()} role="presentation">
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

      {/* Modal creation */}
      <Modal isOpen={showModal} onClose={handleCloseModal} title="Nouvel utilisateur">
        <form onSubmit={handleSubmit}>
          {fieldErrors.general && (
            <div className="azals-alert azals-alert--error mb-4">
              {fieldErrors.general}
            </div>
          )}
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="admin-first-name">Prenom</label>
              <Input
                id="admin-first-name"
                value={formData.first_name || ''}
                onChange={(v) => setFormData({ ...formData, first_name: v })}
                error={!!fieldErrors.first_name}
              />
              {fieldErrors.first_name && <span className="azals-field__error">{fieldErrors.first_name}</span>}
            </div>
            <div className="azals-field">
              <label htmlFor="admin-last-name">Nom</label>
              <Input
                id="admin-last-name"
                value={formData.last_name || ''}
                onChange={(v) => setFormData({ ...formData, last_name: v })}
                error={!!fieldErrors.last_name}
              />
              {fieldErrors.last_name && <span className="azals-field__error">{fieldErrors.last_name}</span>}
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="admin-username">Nom d&apos;utilisateur *</label>
              <Input
                id="admin-username"
                value={formData.username || ''}
                onChange={(v) => setFormData({ ...formData, username: v })}
                error={!!fieldErrors.username}
              />
              {fieldErrors.username && <span className="azals-field__error">{fieldErrors.username}</span>}
            </div>
            <div className="azals-field">
              <label htmlFor="admin-email">Email *</label>
              <Input
                id="admin-email"
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
              <label htmlFor="admin-password">Mot de passe * <span className="text-muted text-xs">(min. 12 caracteres)</span></label>
              <Input
                id="admin-password"
                type="password"
                value={formData.password}
                onChange={(v) => setFormData({ ...formData, password: v })}
                error={!!fieldErrors.password}
              />
              {fieldErrors.password && <span className="azals-field__error">{fieldErrors.password}</span>}
            </div>
            <div className="azals-field">
              <label htmlFor="admin-role">Role ({roles.length} disponibles)</label>
              <Select
                id="admin-role"
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

      {/* Modal edition */}
      <Modal isOpen={showEditModal} onClose={handleCloseEditModal} title="Modifier l'utilisateur">
        <form onSubmit={handleEditSubmit}>
          {fieldErrors.general && (
            <div className="azals-alert azals-alert--error mb-4">
              {fieldErrors.general}
            </div>
          )}
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="edit-first-name">Prenom</label>
              <Input
                id="edit-first-name"
                value={editFormData.first_name || ''}
                onChange={(v) => setEditFormData({ ...editFormData, first_name: v })}
                error={!!fieldErrors.first_name}
              />
              {fieldErrors.first_name && <span className="azals-field__error">{fieldErrors.first_name}</span>}
            </div>
            <div className="azals-field">
              <label htmlFor="edit-last-name">Nom</label>
              <Input
                id="edit-last-name"
                value={editFormData.last_name || ''}
                onChange={(v) => setEditFormData({ ...editFormData, last_name: v })}
                error={!!fieldErrors.last_name}
              />
              {fieldErrors.last_name && <span className="azals-field__error">{fieldErrors.last_name}</span>}
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label htmlFor="edit-username">Nom d&apos;utilisateur *</label>
              <Input
                id="edit-username"
                value={editFormData.username || ''}
                onChange={(v) => setEditFormData({ ...editFormData, username: v })}
                error={!!fieldErrors.username}
              />
              {fieldErrors.username && <span className="azals-field__error">{fieldErrors.username}</span>}
            </div>
            <div className="azals-field">
              <label htmlFor="edit-email">Email *</label>
              <Input
                id="edit-email"
                type="email"
                value={editFormData.email || ''}
                onChange={(v) => setEditFormData({ ...editFormData, email: v })}
                error={!!fieldErrors.email}
              />
              {fieldErrors.email && <span className="azals-field__error">{fieldErrors.email}</span>}
            </div>
          </Grid>
          <div className="azals-field mt-4">
            <label htmlFor="edit-default-view">Vue par defaut apres connexion</label>
            <Select
              id="edit-default-view"
              value={editFormData.default_view || ''}
              onChange={(v) => setEditFormData({ ...editFormData, default_view: v || undefined })}
              options={[
                { value: '', label: 'Automatique (selon le role)' },
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
                { value: 'vehicules', label: 'Vehicules' },
                { value: 'compta', label: 'Comptabilite' },
                { value: 'tresorerie', label: 'Tresorerie' },
              ]}
            />
            <span className="text-xs text-gray-500 mt-1 block">
              Definit la premiere page affichee lors de la connexion de l&apos;utilisateur
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

export default UsersView;
