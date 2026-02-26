/**
 * AZALSCORE Module - Admin - RolesView
 * Vue de gestion des roles
 */

import React, { useState } from 'react';
import { Edit3, Trash2 } from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import type { Role } from '../types';
import { useRoles, useCreateRole, useUpdateRole, useDeleteRole, usePermissions } from '../hooks';

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface Permission {
  id: string;
  code: string;
  name: string;
  description?: string;
  module: string;
}

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

// Modal formulaire role
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

  const permissionsByModule = permissions.reduce((acc, perm) => {
    const module = perm.module || 'Autre';
    if (!acc[module]) acc[module] = [];
    acc[module].push(perm);
    return acc;
  }, {} as Record<string, Permission[]>);

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

  const availableParentRoles = roles.filter(r => r.id !== editingRole?.id);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={editingRole ? `Modifier: ${editingRole.name}` : 'Nouveau role'}
    >
      <form onSubmit={handleSubmit} className="max-h-[70vh] overflow-y-auto">
        <div className="space-y-4">
          <div className="azals-field">
            <label htmlFor="role-form-code" className="block text-sm font-medium mb-1">Code *</label>
            <input
              id="role-form-code"
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

          <div className="azals-field">
            <label htmlFor="role-form-name" className="block text-sm font-medium mb-1">Nom *</label>
            <input
              id="role-form-name"
              type="text"
              className="azals-input w-full px-3 py-2 border rounded-md"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Nom du role"
              autoFocus={!!editingRole}
              required
            />
          </div>

          <div className="azals-field">
            <label htmlFor="role-form-desc" className="block text-sm font-medium mb-1">Description</label>
            <textarea
              id="role-form-desc"
              className="azals-input w-full px-3 py-2 border rounded-md"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description du role (optionnel)"
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="azals-field">
              <label htmlFor="role-form-level" className="block text-sm font-medium mb-1">Niveau (0-10)</label>
              <input
                id="role-form-level"
                type="number"
                className="azals-input w-full px-3 py-2 border rounded-md"
                value={level}
                onChange={(e) => setLevel(Math.max(0, Math.min(10, parseInt(e.target.value) || 0)))}
                min={0}
                max={10}
              />
              <small className="text-gray-500">0 = plus eleve</small>
            </div>

            {!editingRole && (
              <div className="azals-field">
                <label htmlFor="role-form-parent" className="block text-sm font-medium mb-1">Role parent</label>
                <select
                  id="role-form-parent"
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

            {editingRole && (
              <div className="azals-field">
                <label htmlFor="role-form-status" className="block text-sm font-medium mb-1">Statut</label>
                <select
                  id="role-form-status"
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

          <div className="grid grid-cols-2 gap-4">
            <div className="azals-field">
              <label htmlFor="role-form-max-users" className="block text-sm font-medium mb-1">Max utilisateurs</label>
              <input
                id="role-form-max-users"
                type="number"
                className="azals-input w-full px-3 py-2 border rounded-md"
                value={maxUsers}
                onChange={(e) => setMaxUsers(e.target.value)}
                placeholder="Illimite"
                min={1}
              />
            </div>

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
      <DataTable columns={columns} data={roles} isLoading={isLoading} keyField="id" filterable />

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

export default RolesView;
