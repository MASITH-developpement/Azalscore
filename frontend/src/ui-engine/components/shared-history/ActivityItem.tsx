/**
 * AZALSCORE - Shared History Component - ActivityItem
 * ====================================================
 * Composant partagé pour afficher une activité.
 * Réutilisable dans tous les modules nécessitant un suivi d'activités.
 */

import React from 'react';
import {
  Phone, Mail, Calendar, CheckSquare, MessageSquare,
  Clock, User, Video, FileText, AlertCircle
} from 'lucide-react';
import { formatDate } from '@/utils/formatters';

/**
 * Types d'activité supportés
 */
export type ActivityType = 'CALL' | 'EMAIL' | 'MEETING' | 'TASK' | 'NOTE' | 'VIDEO' | 'DOCUMENT' | 'ALERT' | 'OTHER';

/**
 * Statuts d'activité supportés
 */
export type ActivityStatus = 'PLANNED' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED';

/**
 * Configuration des types d'activité
 */
export const ACTIVITY_TYPE_CONFIG: Record<ActivityType, { label: string; color: string; icon: React.ReactNode }> = {
  CALL: { label: 'Appel', color: 'blue', icon: <Phone size={16} /> },
  EMAIL: { label: 'Email', color: 'purple', icon: <Mail size={16} /> },
  MEETING: { label: 'Réunion', color: 'green', icon: <Calendar size={16} /> },
  TASK: { label: 'Tâche', color: 'orange', icon: <CheckSquare size={16} /> },
  NOTE: { label: 'Note', color: 'gray', icon: <MessageSquare size={16} /> },
  VIDEO: { label: 'Visio', color: 'indigo', icon: <Video size={16} /> },
  DOCUMENT: { label: 'Document', color: 'yellow', icon: <FileText size={16} /> },
  ALERT: { label: 'Alerte', color: 'red', icon: <AlertCircle size={16} /> },
  OTHER: { label: 'Autre', color: 'gray', icon: <Clock size={16} /> },
};

/**
 * Configuration des statuts d'activité
 */
export const ACTIVITY_STATUS_CONFIG: Record<ActivityStatus, { label: string; color: string }> = {
  PLANNED: { label: 'Planifié', color: 'blue' },
  IN_PROGRESS: { label: 'En cours', color: 'orange' },
  DONE: { label: 'Terminé', color: 'green' },
  CANCELLED: { label: 'Annulé', color: 'gray' },
};

/**
 * Interface d'une activité
 */
export interface ActivityData {
  id: string;
  type: ActivityType;
  status: ActivityStatus;
  subject: string;
  description?: string;
  due_date?: string;
  created_at: string;
  completed_at?: string;
  assigned_to_id?: string;
  assigned_to_name?: string;
  priority?: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  metadata?: Record<string, unknown>;
}

/**
 * Props du composant ActivityItem
 */
export interface ActivityItemProps {
  activity: ActivityData;
  onClick?: (activity: ActivityData) => void;
  onStatusChange?: (activity: ActivityData, newStatus: ActivityStatus) => void;
  showAssignee?: boolean;
  compact?: boolean;
  className?: string;
}

/**
 * ActivityItem - Composant d'affichage d'une activité
 */
export const ActivityItem: React.FC<ActivityItemProps> = ({
  activity,
  onClick,
  onStatusChange,
  showAssignee = true,
  compact = false,
  className = '',
}) => {
  const typeConfig = ACTIVITY_TYPE_CONFIG[activity.type] || ACTIVITY_TYPE_CONFIG.OTHER;
  const statusConfig = ACTIVITY_STATUS_CONFIG[activity.status] || ACTIVITY_STATUS_CONFIG.PLANNED;

  const handleClick = () => {
    if (onClick) {
      onClick(activity);
    }
  };

  const handleStatusToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onStatusChange) {
      const newStatus = activity.status === 'DONE' ? 'PLANNED' : 'DONE';
      onStatusChange(activity, newStatus);
    }
  };

  return (
    <div
      className={`azals-activity-item azals-activity-item--${activity.status.toLowerCase()} ${onClick ? 'cursor-pointer' : ''} ${compact ? 'azals-activity-item--compact' : ''} ${className}`}
      onClick={handleClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      <div
        className={`azals-activity-item__icon text-${typeConfig.color}`}
        onClick={onStatusChange ? handleStatusToggle : undefined}
      >
        {typeConfig.icon}
      </div>
      <div className="azals-activity-item__content">
        <div className="azals-activity-item__header">
          <span className="azals-activity-item__subject font-medium">{activity.subject}</span>
          <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--sm`}>
            {statusConfig.label}
          </span>
        </div>
        {!compact && activity.description && (
          <p className="azals-activity-item__description text-sm text-muted">
            {activity.description}
          </p>
        )}
        <div className="azals-activity-item__meta text-sm text-muted">
          <span>
            <Calendar size={12} className="mr-1" />
            {activity.due_date ? formatDate(activity.due_date) : formatDate(activity.created_at)}
          </span>
          {showAssignee && activity.assigned_to_name && (
            <span>
              <User size={12} className="mr-1" />
              {activity.assigned_to_name}
            </span>
          )}
          {activity.priority && activity.priority !== 'NORMAL' && (
            <span className={`text-${activity.priority === 'URGENT' ? 'danger' : activity.priority === 'HIGH' ? 'warning' : 'muted'}`}>
              {activity.priority === 'URGENT' ? 'Urgent' : activity.priority === 'HIGH' ? 'Prioritaire' : 'Faible'}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Composant pour afficher une liste d'activités
 */
export interface ActivityListProps {
  activities: ActivityData[];
  onActivityClick?: (activity: ActivityData) => void;
  onStatusChange?: (activity: ActivityData, newStatus: ActivityStatus) => void;
  showAssignee?: boolean;
  compact?: boolean;
  emptyMessage?: string;
  maxItems?: number;
  className?: string;
}

export const ActivityList: React.FC<ActivityListProps> = ({
  activities,
  onActivityClick,
  onStatusChange,
  showAssignee = true,
  compact = false,
  emptyMessage = 'Aucune activité',
  maxItems,
  className = '',
}) => {
  if (activities.length === 0) {
    return (
      <div className={`azals-empty azals-empty--sm ${className}`}>
        <Calendar size={32} className="text-muted" />
        <p className="text-muted">{emptyMessage}</p>
      </div>
    );
  }

  const displayedActivities = maxItems ? activities.slice(0, maxItems) : activities;

  return (
    <div className={`azals-activities-list ${className}`}>
      {displayedActivities.map((activity) => (
        <ActivityItem
          key={activity.id}
          activity={activity}
          onClick={onActivityClick}
          onStatusChange={onStatusChange}
          showAssignee={showAssignee}
          compact={compact}
        />
      ))}
    </div>
  );
};

/**
 * Hook utilitaire pour filtrer et grouper les activités
 */
export function useActivityGroups(activities: ActivityData[]) {
  return {
    planned: activities.filter(a => a.status === 'PLANNED'),
    inProgress: activities.filter(a => a.status === 'IN_PROGRESS'),
    done: activities.filter(a => a.status === 'DONE'),
    cancelled: activities.filter(a => a.status === 'CANCELLED'),
    overdue: activities.filter(a =>
      a.status === 'PLANNED' &&
      a.due_date &&
      new Date(a.due_date) < new Date()
    ),
  };
}

export default ActivityItem;
