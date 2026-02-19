/**
 * AZALSCORE Module - CRM - Customer History Tab
 * Onglet historique et activités du client
 */

import React from 'react';
import {
  Clock, User, Edit, Phone, Mail, Calendar,
  FileText, ArrowRight, CheckSquare, MessageSquare
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDateTime, formatDate } from '@/utils/formatters';
import {
  CUSTOMER_TYPE_CONFIG,
  ACTIVITY_TYPE_CONFIG, ACTIVITY_STATUS_CONFIG
} from '../types';
import type { Customer, CustomerHistoryEntry, Activity } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * CustomerHistoryTab - Historique et activités du client
 */
export const CustomerHistoryTab: React.FC<TabContentProps<Customer>> = ({ data: customer }) => {
  // Générer l'historique combiné
  const history = generateHistoryFromCustomer(customer);
  const activities = customer.activities || [];

  // Séparer activités planifiées et terminées
  const plannedActivities = activities.filter(a => a.status === 'PLANNED');
  const completedActivities = activities.filter(a => a.status === 'DONE');

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Activités planifiées */}
        <Card title="Activités à venir" icon={<Calendar size={18} />}>
          {plannedActivities.length > 0 ? (
            <div className="azals-activities-list">
              {plannedActivities.map((activity) => (
                <ActivityItem key={activity.id} activity={activity} />
              ))}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Calendar size={32} className="text-muted" />
              <p className="text-muted">Aucune activité planifiée</p>
            </div>
          )}
        </Card>

        {/* Activités terminées */}
        <Card title="Activités récentes" icon={<CheckSquare size={18} />}>
          {completedActivities.length > 0 ? (
            <div className="azals-activities-list">
              {completedActivities.slice(0, 5).map((activity) => (
                <ActivityItem key={activity.id} activity={activity} />
              ))}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <CheckSquare size={32} className="text-muted" />
              <p className="text-muted">Aucune activité récente</p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Timeline des modifications */}
      <Card title="Historique des modifications" icon={<Clock size={18} />} className="mt-4">
        {history.length > 0 ? (
          <div className="azals-timeline">
            {history.map((entry, index) => (
              <HistoryEntry
                key={entry.id}
                entry={entry}
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

      {/* Journal d'audit détaillé (ERP only) */}
      <Card
        title="Journal d'audit détaillé"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <table className="azals-table azals-table--simple azals-table--compact">
          <thead>
            <tr>
              <th>Date/Heure</th>
              <th>Action</th>
              <th>Utilisateur</th>
              <th>Détails</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry) => (
              <tr key={entry.id}>
                <td className="text-muted text-sm">{formatDateTime(entry.timestamp)}</td>
                <td>{entry.action}</td>
                <td>{entry.user_name || 'Système'}</td>
                <td className="text-muted text-sm">
                  {entry.details || '-'}
                  {entry.old_value && entry.new_value && (
                    <span className="ml-2">
                      <span className="text-danger">{entry.old_value}</span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className="text-success">{entry.new_value}</span>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

/**
 * Composant item d'activité
 */
interface ActivityItemProps {
  activity: Activity;
}

const ActivityItem: React.FC<ActivityItemProps> = ({ activity }) => {
  const typeConfig = ACTIVITY_TYPE_CONFIG[activity.type];
  const statusConfig = ACTIVITY_STATUS_CONFIG[activity.status];

  const getIcon = () => {
    switch (activity.type) {
      case 'CALL':
        return <Phone size={16} className={`text-${typeConfig.color}`} />;
      case 'EMAIL':
        return <Mail size={16} className={`text-${typeConfig.color}`} />;
      case 'MEETING':
        return <Calendar size={16} className={`text-${typeConfig.color}`} />;
      case 'TASK':
        return <CheckSquare size={16} className={`text-${typeConfig.color}`} />;
      case 'NOTE':
        return <MessageSquare size={16} className={`text-${typeConfig.color}`} />;
      default:
        return <Clock size={16} className="text-muted" />;
    }
  };

  return (
    <div className={`azals-activity-item azals-activity-item--${activity.status.toLowerCase()}`}>
      <div className="azals-activity-item__icon">{getIcon()}</div>
      <div className="azals-activity-item__content">
        <div className="azals-activity-item__header">
          <span className="azals-activity-item__subject font-medium">{activity.subject}</span>
          <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--sm`}>
            {statusConfig.label}
          </span>
        </div>
        {activity.description && (
          <p className="azals-activity-item__description text-sm text-muted">
            {activity.description}
          </p>
        )}
        <div className="azals-activity-item__meta text-sm text-muted">
          <span>
            <Calendar size={12} />
            {activity.due_date ? formatDate(activity.due_date) : formatDate(activity.created_at)}
          </span>
          {activity.assigned_to_name && (
            <span>
              <User size={12} />
              {activity.assigned_to_name}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Composant entrée de timeline
 */
interface HistoryEntryProps {
  entry: CustomerHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('créé') || action.includes('création')) {
      return <FileText size={16} className="text-primary" />;
    }
    if (action.includes('converti')) {
      return <ArrowRight size={16} className="text-success" />;
    }
    if (action.includes('modifié') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    if (action.includes('contact') || action.includes('appel') || action.includes('email')) {
      return <Phone size={16} className="text-blue" />;
    }
    return <Clock size={16} className="text-muted" />;
  };

  return (
    <div className={`azals-timeline__entry ${isFirst ? 'azals-timeline__entry--first' : ''} ${isLast ? 'azals-timeline__entry--last' : ''}`}>
      <div className="azals-timeline__icon">{getIcon()}</div>
      <div className="azals-timeline__content">
        <div className="azals-timeline__header">
          <span className="azals-timeline__action">{entry.action}</span>
          <span className="azals-timeline__time text-muted">
            {formatDateTime(entry.timestamp)}
          </span>
        </div>
        {entry.user_name && (
          <div className="azals-timeline__user text-sm">
            <User size={12} className="mr-1" />
            {entry.user_name}
          </div>
        )}
        {entry.details && (
          <p className="azals-timeline__details text-muted text-sm mt-1">
            {entry.details}
          </p>
        )}
        {entry.old_value && entry.new_value && (
          <div className="azals-timeline__change text-sm mt-1">
            <span className="text-danger line-through">{entry.old_value}</span>
            <ArrowRight size={12} className="mx-2" />
            <span className="text-success">{entry.new_value}</span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Générer l'historique à partir des données du client
 */
function generateHistoryFromCustomer(customer: Customer): CustomerHistoryEntry[] {
  const history: CustomerHistoryEntry[] = [];

  // Création
  history.push({
    id: 'created',
    timestamp: customer.created_at,
    action: 'Client créé',
    user_name: customer.created_by,
    details: `Code: ${customer.code}, Type: ${CUSTOMER_TYPE_CONFIG[customer.type].label}`,
  });

  // Dernière modification
  if (customer.updated_at && customer.updated_at !== customer.created_at) {
    history.push({
      id: 'updated',
      timestamp: customer.updated_at,
      action: 'Fiche modifiée',
      details: 'Mise à jour des informations',
    });
  }

  // Dernier contact
  if (customer.last_contact_date) {
    history.push({
      id: 'last-contact',
      timestamp: customer.last_contact_date,
      action: 'Dernier contact',
    });
  }

  // Dernière commande
  if (customer.last_order_date) {
    history.push({
      id: 'last-order',
      timestamp: customer.last_order_date,
      action: 'Dernière commande',
    });
  }

  // Historique fourni par l'API
  if (customer.history && customer.history.length > 0) {
    history.push(...customer.history);
  }

  // Trier par date décroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default CustomerHistoryTab;
