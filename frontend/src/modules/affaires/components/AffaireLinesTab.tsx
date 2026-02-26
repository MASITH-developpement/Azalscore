/**
 * AZALSCORE Module - AFFAIRES - Lines Tab
 * Onglet interventions et ressources de l'affaire
 */

import React from 'react';
import {
  Wrench, Users, Clock, Calendar, CheckCircle2, AlertCircle,
  ExternalLink, User, Plus
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatDate } from '@/utils/formatters';
import { formatDuration } from '../types';
import type { Affaire, TeamMember, AffaireIntervention } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * AffaireLinesTab - Interventions et ressources de l'affaire
 */
export const AffaireLinesTab: React.FC<TabContentProps<Affaire>> = ({ data: affaire }) => {
  const interventions = affaire.interventions || [];
  const teamMembers = affaire.team_members || [];

  const totalHoursAllocated = teamMembers.reduce((sum, m) => sum + (m.hours_allocated || 0), 0);
  const totalHoursSpent = teamMembers.reduce((sum, m) => sum + (m.hours_spent || 0), 0);
  const totalInterventionHours = interventions.reduce((sum, i) => sum + (i.duration_hours || 0), 0);

  return (
    <div className="azals-std-tab-content">
      {/* Résumé ressources */}
      <Grid cols={3} gap="md" className="mb-4">
        <div className="azals-stat-card">
          <div className="azals-stat-card__icon azals-stat-card__icon--blue">
            <Users size={20} />
          </div>
          <div className="azals-stat-card__content">
            <span className="azals-stat-card__value">{teamMembers.length}</span>
            <span className="azals-stat-card__label">Membres équipe</span>
          </div>
        </div>
        <div className="azals-stat-card">
          <div className="azals-stat-card__icon azals-stat-card__icon--purple">
            <Wrench size={20} />
          </div>
          <div className="azals-stat-card__content">
            <span className="azals-stat-card__value">{interventions.length}</span>
            <span className="azals-stat-card__label">Interventions</span>
          </div>
        </div>
        <div className="azals-stat-card">
          <div className="azals-stat-card__icon azals-stat-card__icon--green">
            <Clock size={20} />
          </div>
          <div className="azals-stat-card__content">
            <span className="azals-stat-card__value">{formatDuration(totalInterventionHours)}</span>
            <span className="azals-stat-card__label">Heures réalisées</span>
          </div>
        </div>
      </Grid>

      <Grid cols={2} gap="lg">
        {/* Équipe */}
        <Card
          title="Équipe projet"
          icon={<Users size={18} />}
        >
          {teamMembers.length > 0 ? (
            <div className="azals-team-list">
              {teamMembers.map((member) => (
                <TeamMemberItem key={member.id} member={member} />
              ))}
              {/* Totaux */}
              <div className="azals-team-list__footer azals-std-field--secondary">
                <span>Total</span>
                <span>{formatDuration(totalHoursAllocated)} allouées</span>
                <span>{formatDuration(totalHoursSpent)} réalisées</span>
              </div>
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Users size={32} className="text-muted" />
              <p className="text-muted">Aucun membre assigné</p>
              {affaire.status !== 'TERMINE' && affaire.status !== 'ANNULE' && (
                <Button size="sm" variant="ghost" leftIcon={<Plus size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'addTeamMember', affaireId: affaire.id } })); }}>
                  Ajouter un membre
                </Button>
              )}
            </div>
          )}
        </Card>

        {/* Interventions */}
        <Card
          title="Interventions"
          icon={<Wrench size={18} />}
        >
          {interventions.length > 0 ? (
            <div className="azals-intervention-list">
              {interventions.map((intervention) => (
                <InterventionItem key={intervention.id} intervention={intervention} />
              ))}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Wrench size={32} className="text-muted" />
              <p className="text-muted">Aucune intervention</p>
              {affaire.status !== 'TERMINE' && affaire.status !== 'ANNULE' && (
                <Button
                  size="sm"
                  variant="ghost"
                  leftIcon={<Plus size={14} />}
                  onClick={() => {
                    window.dispatchEvent(new CustomEvent('azals:navigate', {
                      detail: { view: 'interventions', params: { action: 'create', affaire_id: affaire.id } }
                    }));
                  }}
                >
                  Créer une intervention
                </Button>
              )}
            </div>
          )}
        </Card>
      </Grid>

      {/* Détail heures (ERP only) */}
      {teamMembers.length > 0 && (
        <Card title="Détail des heures" icon={<Clock size={18} />} className="mt-4 azals-std-field--secondary">
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Membre</th>
                <th>Rôle</th>
                <th className="text-right">H. allouées</th>
                <th className="text-right">H. réalisées</th>
                <th className="text-right">Écart</th>
                <th className="text-right">%</th>
              </tr>
            </thead>
            <tbody>
              {teamMembers.map((member) => {
                const allocated = member.hours_allocated || 0;
                const spent = member.hours_spent || 0;
                const diff = spent - allocated;
                const pct = allocated > 0 ? (spent / allocated) * 100 : 0;
                return (
                  <tr key={member.id}>
                    <td className="font-medium">{member.name}</td>
                    <td className="text-muted">{member.role || '-'}</td>
                    <td className="text-right">{formatDuration(allocated)}</td>
                    <td className="text-right">{formatDuration(spent)}</td>
                    <td className={`text-right ${diff > 0 ? 'text-danger' : diff < 0 ? 'text-success' : ''}`}>
                      {diff > 0 ? '+' : ''}{formatDuration(Math.abs(diff))}
                    </td>
                    <td className={`text-right ${pct > 100 ? 'text-danger' : pct > 90 ? 'text-warning' : ''}`}>
                      {pct.toFixed(0)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr className="font-medium">
                <td colSpan={2}>Total</td>
                <td className="text-right">{formatDuration(totalHoursAllocated)}</td>
                <td className="text-right">{formatDuration(totalHoursSpent)}</td>
                <td className={`text-right ${totalHoursSpent > totalHoursAllocated ? 'text-danger' : 'text-success'}`}>
                  {totalHoursSpent > totalHoursAllocated ? '+' : ''}{formatDuration(Math.abs(totalHoursSpent - totalHoursAllocated))}
                </td>
                <td className="text-right">
                  {totalHoursAllocated > 0 ? ((totalHoursSpent / totalHoursAllocated) * 100).toFixed(0) : 0}%
                </td>
              </tr>
            </tfoot>
          </table>
        </Card>
      )}
    </div>
  );
};

/**
 * Item membre équipe
 */
const TeamMemberItem: React.FC<{ member: TeamMember }> = ({ member }) => {
  const pct = member.hours_allocated && member.hours_allocated > 0
    ? ((member.hours_spent || 0) / member.hours_allocated) * 100
    : 0;

  return (
    <div className="azals-team-item">
      <div className="azals-team-item__avatar">
        <User size={16} />
      </div>
      <div className="azals-team-item__info">
        <span className="azals-team-item__name">{member.name}</span>
        {member.role && <span className="azals-team-item__role text-muted">{member.role}</span>}
      </div>
      <div className="azals-team-item__hours azals-std-field--secondary">
        <span className="text-muted">{formatDuration(member.hours_spent || 0)} / {formatDuration(member.hours_allocated || 0)}</span>
        <div className="azals-mini-progress">
          <div
            className="azals-mini-progress__fill"
            style={{
              width: `${Math.min(pct, 100)}%`,
              backgroundColor: pct > 100 ? 'var(--azals-danger-500)' : 'var(--azals-primary-500)',
            }}
          />
        </div>
      </div>
    </div>
  );
};

/**
 * Item intervention
 */
const InterventionItem: React.FC<{ intervention: AffaireIntervention }> = ({ intervention }) => {
  const getStatusIcon = () => {
    switch (intervention.status.toLowerCase()) {
      case 'termine':
      case 'completed':
        return <CheckCircle2 size={14} className="text-success" />;
      case 'en_cours':
      case 'in_progress':
        return <Clock size={14} className="text-primary" />;
      default:
        return <AlertCircle size={14} className="text-muted" />;
    }
  };

  return (
    <div
      className="azals-intervention-item"
      onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', {
        detail: { view: 'interventions', params: { id: intervention.id } }
      }))}
    >
      <div className="azals-intervention-item__status">{getStatusIcon()}</div>
      <div className="azals-intervention-item__info">
        <span className="azals-intervention-item__ref">{intervention.reference}</span>
        <span className="azals-intervention-item__date text-muted">
          <Calendar size={12} className="mr-1" />
          {formatDate(intervention.date)}
        </span>
      </div>
      {intervention.technician_name && (
        <span className="azals-intervention-item__tech text-muted">
          <User size={12} className="mr-1" />
          {intervention.technician_name}
        </span>
      )}
      {intervention.duration_hours && (
        <span className="azals-intervention-item__duration">
          {formatDuration(intervention.duration_hours)}
        </span>
      )}
      <ExternalLink size={14} className="azals-intervention-item__arrow text-muted" />
    </div>
  );
};

export default AffaireLinesTab;
