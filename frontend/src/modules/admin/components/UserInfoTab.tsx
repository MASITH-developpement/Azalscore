/**
 * AZALSCORE Module - Admin - User Info Tab
 * Onglet informations generales utilisateur
 */

import React from 'react';
import {
  User, Mail, Shield, Calendar, Clock, Key,
  Smartphone, AlertTriangle, CheckCircle2
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { AdminUser } from '../types';
import {
  getUserFullName,
  USER_STATUS_CONFIG, hasTwoFactorEnabled, mustChangePassword,
  getPasswordAgeDays, isPasswordOld
} from '../types';
import { formatDate, formatDateTime } from '@/utils/formatters';

/**
 * UserInfoTab - Informations utilisateur
 */
export const UserInfoTab: React.FC<TabContentProps<AdminUser>> = ({ data: user }) => {
  const statusConfig = USER_STATUS_CONFIG[user.status] || { label: user.status || 'Inconnu', color: 'gray' as const };

  return (
    <div className="azals-std-tab-content">
      {/* Identite */}
      <Card title="Identite" icon={<User size={18} />}>
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Nom d'utilisateur</label>
            <div className="azals-field__value font-mono">{user.username}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Email</label>
            <div className="azals-field__value flex items-center gap-2">
              <Mail size={14} className="text-muted" />
              {user.email}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Statut</label>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
          </div>
        </Grid>
        <Grid cols={3} gap="md" className="mt-4">
          <div className="azals-field">
            <label className="azals-field__label">Prenom</label>
            <div className="azals-field__value">{user.first_name || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Nom</label>
            <div className="azals-field__value">{user.last_name || '-'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Nom complet</label>
            <div className="azals-field__value font-medium">{getUserFullName(user)}</div>
          </div>
        </Grid>
      </Card>

      {/* Role et permissions */}
      <Card title="Role et acces" icon={<Shield size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Role</label>
            <div className="azals-field__value">
              {user.role_name ? (
                <span className="azals-badge azals-badge--purple">{user.role_name}</span>
              ) : (
                <span className="text-muted">Non assigne</span>
              )}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">ID Role</label>
            <div className="azals-field__value font-mono text-sm azals-std-field--secondary">
              {user.role_id || '-'}
            </div>
          </div>
        </Grid>
        {user.role && (
          <div className="mt-4 p-3 bg-purple-50 rounded azals-std-field--secondary">
            <p className="text-sm text-purple-700">
              {user.role.description || `Role ${user.role.name} avec ${user.role.permissions?.length || 0} permissions`}
            </p>
          </div>
        )}
      </Card>

      {/* Securite */}
      <Card title="Securite" icon={<Key size={18} />} className="mt-4">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Authentification 2FA</label>
            <div className="azals-field__value flex items-center gap-2">
              {hasTwoFactorEnabled(user) ? (
                <>
                  <Smartphone size={16} className="text-green-600" />
                  <span className="text-green-600 font-medium">Active</span>
                </>
              ) : (
                <>
                  <Smartphone size={16} className="text-gray-400" />
                  <span className="text-muted">Desactive</span>
                </>
              )}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Mot de passe</label>
            <div className="azals-field__value">
              {mustChangePassword(user) ? (
                <span className="flex items-center gap-2 text-orange-600">
                  <AlertTriangle size={16} />
                  Changement requis
                </span>
              ) : isPasswordOld(user) ? (
                <span className="flex items-center gap-2 text-orange-600">
                  <AlertTriangle size={16} />
                  Ancien ({getPasswordAgeDays(user)}j)
                </span>
              ) : (
                <span className="flex items-center gap-2 text-green-600">
                  <CheckCircle2 size={16} />
                  OK
                </span>
              )}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Change le</label>
            <div className="azals-field__value">
              {user.password_changed_at ? formatDate(user.password_changed_at) : 'Jamais'}
            </div>
          </div>
        </Grid>
        <Grid cols={2} gap="md" className="mt-4 azals-std-field--secondary">
          <div className="azals-field">
            <label className="azals-field__label">Echecs de connexion</label>
            <div className={`azals-field__value ${user.failed_login_count > 3 ? 'text-red-600 font-medium' : ''}`}>
              {user.failed_login_count}
            </div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Derniere IP</label>
            <div className="azals-field__value font-mono text-sm">
              {user.last_ip || '-'}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Dates */}
      <Card title="Dates" icon={<Calendar size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={3} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Cree le</label>
            <div className="azals-field__value">{formatDateTime(user.created_at)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Modifie le</label>
            <div className="azals-field__value">{formatDateTime(user.updated_at)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Derniere connexion</label>
            <div className="azals-field__value">
              {user.last_login ? formatDateTime(user.last_login) : 'Jamais'}
            </div>
          </div>
        </Grid>
        <Grid cols={2} gap="md" className="mt-4">
          <div className="azals-field">
            <label className="azals-field__label">Cree par</label>
            <div className="azals-field__value">{user.created_by || 'Systeme'}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Nombre de connexions</label>
            <div className="azals-field__value">{user.login_count}</div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default UserInfoTab;
