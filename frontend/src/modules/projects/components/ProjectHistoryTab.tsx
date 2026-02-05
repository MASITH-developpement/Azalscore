/**
 * AZALSCORE Module - Projects - Project History Tab
 * Onglet historique du projet
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  Play, Pause, CheckCircle, XCircle, Target, Users
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Project, ProjectHistoryEntry, Milestone } from '../types';
import { formatDateTime, formatDate } from '@/utils/formatters';
import {
  PROJECT_STATUS_CONFIG, MILESTONE_STATUS_CONFIG
} from '../types';

/**
 * ProjectHistoryTab - Historique du projet
 */
export const ProjectHistoryTab: React.FC<TabContentProps<Project>> = ({ data: project }) => {
  // Generer l'historique combine
  const history = generateHistoryFromProject(project);

  return (
    <div className="azals-std-tab-content">
      {/* Jalons */}
      {project.milestones && project.milestones.length > 0 && (
        <Card title="Jalons du projet" icon={<Target size={18} />} className="mb-4">
          <div className="azals-milestones">
            {project.milestones.map((milestone) => (
              <MilestoneItem key={milestone.id} milestone={milestone} />
            ))}
          </div>
        </Card>
      )}

      {/* Timeline des evenements */}
      <Card title="Historique des evenements" icon={<Clock size={18} />}>
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

      {/* Journal d'audit detaille (ERP only) */}
      <Card
        title="Journal d'audit detaille"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <table className="azals-table azals-table--simple azals-table--compact">
          <thead>
            <tr>
              <th>Date/Heure</th>
              <th>Action</th>
              <th>Utilisateur</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry) => (
              <tr key={entry.id}>
                <td className="text-muted text-sm">{formatDateTime(entry.timestamp)}</td>
                <td>{entry.action}</td>
                <td>{entry.user_name || 'Systeme'}</td>
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
 * Composant jalon
 */
const MilestoneItem: React.FC<{ milestone: Milestone }> = ({ milestone }) => {
  const statusConfig = MILESTONE_STATUS_CONFIG[milestone.status] || MILESTONE_STATUS_CONFIG.PENDING;

  return (
    <div className={`azals-milestone azals-milestone--${milestone.status.toLowerCase()}`}>
      <div className="azals-milestone__icon">
        {milestone.status === 'COMPLETED' ? (
          <CheckCircle size={20} className="text-green-500" />
        ) : milestone.status === 'OVERDUE' ? (
          <XCircle size={20} className="text-red-500" />
        ) : (
          <Target size={20} className="text-gray-400" />
        )}
      </div>
      <div className="azals-milestone__content">
        <div className="azals-milestone__header">
          <span className="azals-milestone__name font-medium">{milestone.name}</span>
          <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--sm`}>
            {statusConfig.label}
          </span>
        </div>
        {milestone.description && (
          <p className="azals-milestone__description text-sm text-muted">{milestone.description}</p>
        )}
        <div className="azals-milestone__date text-sm">
          <Clock size={12} className="inline mr-1" />
          Echeance: {formatDate(milestone.due_date)}
          {milestone.completed_at && (
            <span className="text-success ml-2">
              (Atteint le {formatDate(milestone.completed_at)})
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Composant entree de timeline
 */
interface HistoryEntryProps {
  entry: ProjectHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation')) {
      return <CheckCircle size={16} className="text-success" />;
    }
    if (action.includes('demarre') || action.includes('active')) {
      return <Play size={16} className="text-blue-500" />;
    }
    if (action.includes('pause') || action.includes('suspendu')) {
      return <Pause size={16} className="text-orange-500" />;
    }
    if (action.includes('termine') || action.includes('complete')) {
      return <CheckCircle size={16} className="text-green-500" />;
    }
    if (action.includes('annule')) {
      return <XCircle size={16} className="text-danger" />;
    }
    if (action.includes('membre') || action.includes('equipe')) {
      return <Users size={16} className="text-purple-500" />;
    }
    if (action.includes('jalon') || action.includes('milestone')) {
      return <Target size={16} className="text-cyan-500" />;
    }
    if (action.includes('modifie') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
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
 * Generer l'historique a partir des donnees du projet
 */
function generateHistoryFromProject(project: Project): ProjectHistoryEntry[] {
  const history: ProjectHistoryEntry[] = [];

  // Creation du projet
  history.push({
    id: 'created',
    timestamp: project.created_at,
    action: 'Projet cree',
    user_name: project.created_by,
    details: `Code: ${project.code}, Nom: ${project.name}`,
  });

  // Date de debut
  if (project.start_date) {
    history.push({
      id: 'started',
      timestamp: project.start_date,
      action: 'Projet demarre',
      details: PROJECT_STATUS_CONFIG[project.status].label,
    });
  }

  // Jalons atteints
  project.milestones?.filter(m => m.completed_at).forEach((milestone, index) => {
    history.push({
      id: `milestone-${index}`,
      timestamp: milestone.completed_at!,
      action: 'Jalon atteint',
      details: milestone.name,
    });
  });

  // Date de fin
  if (project.actual_end_date) {
    history.push({
      id: 'completed',
      timestamp: project.actual_end_date,
      action: 'Projet termine',
      details: `Progression finale: ${project.progress}%`,
    });
  }

  // Derniere modification
  if (project.updated_at && project.updated_at !== project.created_at) {
    history.push({
      id: 'updated',
      timestamp: project.updated_at,
      action: 'Projet modifie',
      user_name: project.updated_by,
      details: 'Mise a jour des informations',
    });
  }

  // Historique fourni par l'API
  if (project.history && project.history.length > 0) {
    history.push(...project.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default ProjectHistoryTab;
