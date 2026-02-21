/**
 * AZALSCORE Module - Admin - User History Tab
 * Onglet historique utilisateur
 */

import React from 'react';
import {
  Clock, User, Edit3, Trash2, Plus, Shield,
  Key, CheckCircle2, XCircle, ArrowRight
} from 'lucide-react';
import { Card } from '@ui/layout';
import { formatDateTime } from '@/utils/formatters';
import type { AdminUser, UserHistoryEntry } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * UserHistoryTab - Historique utilisateur
 */
export const UserHistoryTab: React.FC<TabContentProps<AdminUser>> = ({ data: user }) => {
  const auditLogs = user.audit_logs || [];
  const history = generateHistoryFromUser(user);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique des modifications" icon={<Clock size={18} />}>
        {history.length > 0 ? (
          <div className="azals-timeline">
            {history.map((item, index) => (
              <HistoryEntryComponent
                key={item.id}
                entry={item}
                isFirst={index === 0}
                isLast={index === history.length - 1}
              />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Clock size={32} className="text-muted" />
            <p className="text-muted">Aucun historique disponible</p>
          </div>
        )}
      </Card>

      {/* Journal d'audit (ERP only) */}
      <Card title="Journal d'audit" icon={<Shield size={18} />} className="mt-4 azals-std-field--secondary">
        {auditLogs.length > 0 ? (
          <table className="azals-table azals-table--simple azals-table--compact">
            <thead>
              <tr>
                <th>Date/Heure</th>
                <th>Action</th>
                <th>Ressource</th>
                <th>Statut</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((log) => (
                <tr key={log.id}>
                  <td className="text-muted text-sm">{formatDateTime(log.timestamp)}</td>
                  <td>{log.action}</td>
                  <td>
                    {log.resource_type}
                    {log.resource_id && (
                      <code className="ml-2 text-xs">{log.resource_id}</code>
                    )}
                  </td>
                  <td>
                    <span className={`azals-badge azals-badge--${log.status === 'SUCCESS' ? 'green' : 'red'} text-xs`}>
                      {log.status === 'SUCCESS' ? 'OK' : 'Echec'}
                    </span>
                  </td>
                  <td className="font-mono text-xs">{log.ip_address || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Shield size={32} className="text-muted" />
            <p className="text-muted">Aucun log d&apos;audit</p>
          </div>
        )}
      </Card>
    </div>
  );
};

/**
 * Composant entree de timeline
 */
interface HistoryEntryComponentProps {
  entry: UserHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntryComponent: React.FC<HistoryEntryComponentProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation')) {
      return <Plus size={16} className="text-green-500" />;
    }
    if (action.includes('modif') || action.includes('mise a jour')) {
      return <Edit3 size={16} className="text-blue-500" />;
    }
    if (action.includes('suppr')) {
      return <Trash2 size={16} className="text-red-500" />;
    }
    if (action.includes('role') || action.includes('permission')) {
      return <Shield size={16} className="text-purple-500" />;
    }
    if (action.includes('mot de passe') || action.includes('password')) {
      return <Key size={16} className="text-orange-500" />;
    }
    if (action.includes('activ') || action.includes('debloque')) {
      return <CheckCircle2 size={16} className="text-green-500" />;
    }
    if (action.includes('desactiv') || action.includes('bloque') || action.includes('suspen')) {
      return <XCircle size={16} className="text-red-500" />;
    }
    return <Clock size={16} className="text-muted" />;
  };

  return (
    <div className={`azals-timeline__entry ${isFirst ? 'azals-timeline__entry--first' : ''} ${isLast ? 'azals-timeline__entry--last' : ''}`}>
      <div className="azals-timeline__icon">{getIcon()}</div>
      <div className="azals-timeline__content">
        <div className="azals-timeline__header">
          <span className="azals-timeline__action">{entry.action}</span>
          <span className="azals-timeline__time text-muted">{formatDateTime(entry.timestamp)}</span>
        </div>
        {entry.performed_by && (
          <div className="azals-timeline__user text-sm">
            <User size={12} className="mr-1" />
            {entry.performed_by}
          </div>
        )}
        {entry.field && entry.old_value !== undefined && entry.new_value !== undefined && (
          <div className="azals-timeline__change text-sm mt-1">
            <span className="font-medium">{entry.field}:</span>
            <span className="ml-2 text-red-600 line-through">{entry.old_value || '(vide)'}</span>
            <ArrowRight size={12} className="mx-2 inline" />
            <span className="text-green-600">{entry.new_value || '(vide)'}</span>
          </div>
        )}
        {entry.details && (
          <p className="azals-timeline__details text-muted text-sm mt-1">{entry.details}</p>
        )}
      </div>
    </div>
  );
};

/**
 * Generer l'historique a partir des donnees utilisateur
 */
function generateHistoryFromUser(user: AdminUser): UserHistoryEntry[] {
  const history: UserHistoryEntry[] = [];

  // Creation
  history.push({
    id: 'created',
    timestamp: user.created_at,
    action: 'Utilisateur cree',
    performed_by: user.created_by || 'Systeme',
    details: `Compte ${user.username} cree avec l'email ${user.email}`
  });

  // Changement de mot de passe
  if (user.password_changed_at && user.password_changed_at !== user.created_at) {
    history.push({
      id: 'password-changed',
      timestamp: user.password_changed_at,
      action: 'Mot de passe modifie',
      details: 'Le mot de passe a ete change'
    });
  }

  // Derniere modification
  if (user.updated_at !== user.created_at) {
    history.push({
      id: 'updated',
      timestamp: user.updated_at,
      action: 'Profil mis a jour'
    });
  }

  // Derniere connexion
  if (user.last_login) {
    history.push({
      id: 'last-login',
      timestamp: user.last_login,
      action: 'Derniere connexion',
      details: user.last_ip ? `Depuis ${user.last_ip}` : undefined
    });
  }

  // Trier par date decroissante
  return history.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
}

export default UserHistoryTab;
