/**
 * AZALSCORE Module - Admin - User Permissions Tab
 * Onglet permissions utilisateur
 */

import React, { useState } from 'react';
import {
  Shield, CheckCircle2, Eye, Edit3,
  Trash2, Settings, Lock, Search
} from 'lucide-react';
import { Input } from '@ui/forms';
import { Card, Grid } from '@ui/layout';
import { PERMISSION_CATEGORY_CONFIG } from '../types';
import type { AdminUser, Permission } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * UserPermissionsTab - Permissions utilisateur
 */
export const UserPermissionsTab: React.FC<TabContentProps<AdminUser>> = ({ data: user }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const permissions = user.permissions || [];
  const role = user.role;
  const rolePermissions = role?.permissions || [];

  // Grouper les permissions par module
  const groupedPermissions = permissions.reduce((acc, perm) => {
    if (!acc[perm.module]) {
      acc[perm.module] = [];
    }
    acc[perm.module].push(perm);
    return acc;
  }, {} as Record<string, Permission[]>);

  const filteredModules = Object.entries(groupedPermissions).filter(([module, perms]) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return module.toLowerCase().includes(term) ||
           perms.some(p => p.name.toLowerCase().includes(term) || p.code.toLowerCase().includes(term));
  });

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'READ':
        return <Eye size={14} />;
      case 'WRITE':
        return <Edit3 size={14} />;
      case 'DELETE':
        return <Trash2 size={14} />;
      case 'ADMIN':
        return <Settings size={14} />;
      default:
        return <Lock size={14} />;
    }
  };

  return (
    <div className="azals-std-tab-content">
      {/* Resume du role */}
      <Card title="Role attribue" icon={<Shield size={18} />}>
        {role ? (
          <div className="p-4 bg-purple-50 rounded">
            <div className="flex items-center gap-3 mb-2">
              <span className="azals-badge azals-badge--purple text-lg">{role.name}</span>
              {role.is_system && (
                <span className="azals-badge azals-badge--orange text-xs">Systeme</span>
              )}
            </div>
            <p className="text-sm text-muted">{role.description || 'Aucune description'}</p>
            <div className="mt-3 flex items-center gap-4 text-sm">
              <span>
                <strong>{rolePermissions.length}</strong> permissions
              </span>
              <span>
                <strong>{role.user_count}</strong> utilisateurs avec ce role
              </span>
            </div>
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Shield size={32} className="text-muted" />
            <p className="text-muted">Aucun role assigne</p>
          </div>
        )}
      </Card>

      {/* Permissions detaillees */}
      <Card title="Permissions effectives" icon={<CheckCircle2 size={18} />} className="mt-4">
        <div className="mb-4">
          <Input
            value={searchTerm}
            onChange={setSearchTerm}
            placeholder="Rechercher une permission..."
            className="max-w-md"
          />
        </div>

        {filteredModules.length > 0 ? (
          <div className="space-y-4">
            {filteredModules.map(([module, perms]) => (
              <div key={module} className="border rounded p-3">
                <h4 className="font-medium mb-3 text-primary">{module}</h4>
                <div className="grid grid-cols-2 gap-2">
                  {perms.map((perm) => {
                    const categoryConfig = PERMISSION_CATEGORY_CONFIG[perm.category] || { label: perm.category, color: 'gray' };
                    return (
                      <div
                        key={perm.id}
                        className="flex items-center gap-2 p-2 bg-gray-50 rounded text-sm"
                      >
                        <CheckCircle2 size={14} className="text-green-600 flex-shrink-0" />
                        <span className="flex-1">{perm.name}</span>
                        <span className={`azals-badge azals-badge--${categoryConfig.color} text-xs flex items-center gap-1`}>
                          {getCategoryIcon(perm.category)}
                          {categoryConfig.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : permissions.length === 0 ? (
          <div className="azals-empty azals-empty--sm">
            <Lock size={32} className="text-muted" />
            <p className="text-muted">Aucune permission attribuee</p>
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Search size={32} className="text-muted" />
            <p className="text-muted">Aucune permission trouvee pour "{searchTerm}"</p>
          </div>
        )}
      </Card>

      {/* Permissions du role (ERP only) */}
      {rolePermissions.length > 0 && (
        <Card title="Permissions du role" icon={<Shield size={18} />} className="mt-4 azals-std-field--secondary">
          <div className="flex flex-wrap gap-2">
            {rolePermissions.map((permCode, index) => (
              <span key={index} className="azals-badge azals-badge--gray font-mono text-xs">
                {permCode}
              </span>
            ))}
          </div>
        </Card>
      )}

      {/* Statistiques */}
      <Card title="Statistiques d'acces" icon={<Settings size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={4} gap="md">
          <div className="text-center p-3 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">
              {permissions.filter(p => p.category === 'READ').length}
            </div>
            <div className="text-sm text-muted">Lecture</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">
              {permissions.filter(p => p.category === 'WRITE').length}
            </div>
            <div className="text-sm text-muted">Ecriture</div>
          </div>
          <div className="text-center p-3 bg-red-50 rounded">
            <div className="text-2xl font-bold text-red-600">
              {permissions.filter(p => p.category === 'DELETE').length}
            </div>
            <div className="text-sm text-muted">Suppression</div>
          </div>
          <div className="text-center p-3 bg-purple-50 rounded">
            <div className="text-2xl font-bold text-purple-600">
              {permissions.filter(p => p.category === 'ADMIN').length}
            </div>
            <div className="text-sm text-muted">Admin</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default UserPermissionsTab;
