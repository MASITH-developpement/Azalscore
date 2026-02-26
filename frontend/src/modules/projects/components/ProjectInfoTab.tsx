/**
 * AZALSCORE Module - Projects - Project Info Tab
 * Onglet informations generales du projet
 */

import React from 'react';
import {
  Folder, User, Building2, Calendar, Target,
  Tag, FileText, Users
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { formatDate, formatPercent } from '@/utils/formatters';
import {
  formatProjectDuration,
  PROJECT_STATUS_CONFIG, PRIORITY_CONFIG, TEAM_ROLE_CONFIG,
  getDaysRemaining, isProjectOverdue, isProjectNearDeadline
} from '../types';
import type { Project, TeamMember } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * ProjectInfoTab - Informations generales du projet
 */
export const ProjectInfoTab: React.FC<TabContentProps<Project>> = ({ data: project }) => {
  const daysRemaining = getDaysRemaining(project);
  const isOverdue = isProjectOverdue(project);
  const isNearDeadline = isProjectNearDeadline(project);

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Informations principales */}
        <Card title="Informations principales" icon={<Folder size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <span className="azals-field__label">Code projet</span>
              <span className="azals-field__value font-mono">{project.code}</span>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Nom</span>
              <span className="azals-field__value">{project.name}</span>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Statut</span>
              <span className={`azals-badge azals-badge--${PROJECT_STATUS_CONFIG[project.status].color}`}>
                {PROJECT_STATUS_CONFIG[project.status].label}
              </span>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Priorite</span>
              <span className={`azals-badge azals-badge--${PRIORITY_CONFIG[project.priority].color}`}>
                {PRIORITY_CONFIG[project.priority].label}
              </span>
            </div>
            {project.description && (
              <div className="azals-field azals-field--full">
                <span className="azals-field__label">Description</span>
                <p className="azals-field__value text-muted">{project.description}</p>
              </div>
            )}
            {project.tags && project.tags.length > 0 && (
              <div className="azals-field azals-field--full">
                <span className="azals-field__label">Tags</span>
                <div className="flex flex-wrap gap-1">
                  {project.tags.map((tag, idx) => (
                    <span key={idx} className="azals-badge azals-badge--gray">
                      <Tag size={12} className="mr-1" />
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Client et responsable */}
        <Card title="Client et responsable" icon={<Building2 size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <span className="azals-field__label">Client</span>
              <span className="azals-field__value">{project.client_name || '-'}</span>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Responsable projet</span>
              <span className="azals-field__value">
                {project.manager_name ? (
                  <span className="flex items-center gap-1">
                    <User size={14} />
                    {project.manager_name}
                  </span>
                ) : '-'}
              </span>
            </div>
          </div>
        </Card>

        {/* Dates et planning */}
        <Card title="Dates et planning" icon={<Calendar size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <span className="azals-field__label">Date de debut</span>
              <span className="azals-field__value">{formatDate(project.start_date)}</span>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Date de fin prevue</span>
              <span className={`azals-field__value ${isOverdue ? 'text-danger' : isNearDeadline ? 'text-warning' : ''}`}>
                {formatDate(project.end_date)}
                {isOverdue && ' (En retard)'}
                {isNearDeadline && !isOverdue && ' (Proche)'}
              </span>
            </div>
            {project.actual_end_date && (
              <div className="azals-field">
                <span className="azals-field__label">Date de fin reelle</span>
                <span className="azals-field__value">{formatDate(project.actual_end_date)}</span>
              </div>
            )}
            <div className="azals-field">
              <span className="azals-field__label">Duree</span>
              <span className="azals-field__value">{formatProjectDuration(project)}</span>
            </div>
            {daysRemaining !== null && project.status === 'ACTIVE' && (
              <div className="azals-field">
                <span className="azals-field__label">Jours restants</span>
                <span className={`azals-field__value font-medium ${daysRemaining < 0 ? 'text-danger' : daysRemaining <= 7 ? 'text-warning' : 'text-success'}`}>
                  {daysRemaining < 0 ? `${Math.abs(daysRemaining)} jours de retard` : `${daysRemaining} jours`}
                </span>
              </div>
            )}
          </div>
        </Card>

        {/* Avancement */}
        <Card title="Avancement" icon={<Target size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field azals-field--full">
              <span className="azals-field__label">Progression globale</span>
              <div className="mt-2">
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-gray-200 rounded-full h-3">
                    <div
                      className={`h-3 rounded-full ${project.progress >= 100 ? 'bg-green-500' : project.progress >= 75 ? 'bg-blue-500' : project.progress >= 50 ? 'bg-yellow-500' : 'bg-gray-400'}`}
                      style={{ width: `${Math.min(project.progress, 100)}%` }}
                    />
                  </div>
                  <span className="font-medium text-lg">{formatPercent(project.progress)}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </Grid>

      {/* Equipe projet (ERP only) */}
      {project.team_members && project.team_members.length > 0 && (
        <Card
          title="Equipe projet"
          icon={<Users size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <div className="azals-team-list">
            {project.team_members.map((member) => (
              <TeamMemberItem key={member.id} member={member} />
            ))}
          </div>
        </Card>
      )}

      {/* Notes (ERP only) */}
      {project.notes && (
        <Card
          title="Notes"
          icon={<FileText size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <p className="text-muted whitespace-pre-wrap">{project.notes}</p>
        </Card>
      )}
    </div>
  );
};

/**
 * Composant membre d'equipe
 */
const TeamMemberItem: React.FC<{ member: TeamMember }> = ({ member }) => {
  const roleConfig = TEAM_ROLE_CONFIG[member.role] || TEAM_ROLE_CONFIG.MEMBER;

  return (
    <div className="azals-team-member">
      <div className="azals-team-member__avatar">
        <User size={20} />
      </div>
      <div className="azals-team-member__info">
        <span className="azals-team-member__name">{member.user_name}</span>
        {member.user_email && (
          <span className="azals-team-member__email text-sm text-muted">{member.user_email}</span>
        )}
      </div>
      <span className={`azals-badge azals-badge--${roleConfig.color}`}>
        {roleConfig.label}
      </span>
      {member.hours_logged !== undefined && (
        <span className="text-sm text-muted">{member.hours_logged}h</span>
      )}
    </div>
  );
};

export default ProjectInfoTab;
