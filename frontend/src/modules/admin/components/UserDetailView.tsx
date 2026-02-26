/**
 * AZALSCORE Module - Admin - UserDetailView
 * Vue de detail d'un utilisateur avec BaseViewStandard
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { User, Shield, Activity, Clock, Sparkles, ArrowLeft, Edit3, Lock, Unlock } from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { BaseViewStandard } from '@ui/standards';
import { formatDateTime } from '@/utils/formatters';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition } from '@ui/standards';
import type { AdminUser } from '../types';
import { USER_STATUS_CONFIG, getUserFullName, isUserActive, isUserLocked, hasTwoFactorEnabled, mustChangePassword } from '../types';
import { useUser, useUpdateUserStatus } from '../hooks';
import { UserInfoTab, UserPermissionsTab, UserActivityTab, UserHistoryTab, UserIATab } from './index';

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
          <p className="text-red-600">Impossible de charger l&apos;utilisateur</p>
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

export default UserDetailView;
