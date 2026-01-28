/**
 * AZALSCORE Module - INTERVENTIONS - Lines Tab
 * Onglet équipe et réalisation de l'intervention
 */

import React from 'react';
import {
  Users, Clock, Calendar, CheckCircle2, AlertCircle,
  Play, Pause, User, Timer, TrendingUp, TrendingDown
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Intervention, InterventionEquipeMembre } from '../types';
import { getDurationVariance, STATUT_CONFIG } from '../types';
import { formatDate, formatDateTime, formatDuration } from '@/utils/formatters';

/**
 * InterventionLinesTab - Équipe et suivi de réalisation
 */
export const InterventionLinesTab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const equipe = intervention.equipe || [];
  const durationVariance = getDurationVariance(intervention);

  return (
    <div className="azals-std-tab-content">
      {/* Résumé temps */}
      <Grid cols={4} gap="md" className="mb-4">
        <div className="azals-stat-card">
          <div className="azals-stat-card__icon azals-stat-card__icon--blue">
            <Timer size={20} />
          </div>
          <div className="azals-stat-card__content">
            <span className="azals-stat-card__value">{formatDuration(intervention.duree_prevue_minutes)}</span>
            <span className="azals-stat-card__label">Durée prévue</span>
          </div>
        </div>
        <div className="azals-stat-card">
          <div className={`azals-stat-card__icon ${intervention.duree_reelle_minutes ? 'azals-stat-card__icon--green' : 'azals-stat-card__icon--gray'}`}>
            <Clock size={20} />
          </div>
          <div className="azals-stat-card__content">
            <span className="azals-stat-card__value">{formatDuration(intervention.duree_reelle_minutes)}</span>
            <span className="azals-stat-card__label">Durée réelle</span>
          </div>
        </div>
        <div className="azals-stat-card">
          <div className={`azals-stat-card__icon ${durationVariance !== null && durationVariance > 0 ? 'azals-stat-card__icon--orange' : 'azals-stat-card__icon--green'}`}>
            {durationVariance !== null && durationVariance > 0 ? <TrendingUp size={20} /> : <TrendingDown size={20} />}
          </div>
          <div className="azals-stat-card__content">
            <span className={`azals-stat-card__value ${durationVariance !== null && durationVariance > 0 ? 'text-warning' : 'text-success'}`}>
              {durationVariance !== null ? `${durationVariance > 0 ? '+' : ''}${formatDuration(Math.abs(durationVariance))}` : '-'}
            </span>
            <span className="azals-stat-card__label">Écart</span>
          </div>
        </div>
        <div className="azals-stat-card">
          <div className="azals-stat-card__icon azals-stat-card__icon--purple">
            <Users size={20} />
          </div>
          <div className="azals-stat-card__content">
            <span className="azals-stat-card__value">{equipe.length || 1}</span>
            <span className="azals-stat-card__label">Intervenant(s)</span>
          </div>
        </div>
      </Grid>

      <Grid cols={2} gap="lg">
        {/* Équipe */}
        <Card title="Équipe d'intervention" icon={<Users size={18} />}>
          {equipe.length > 0 ? (
            <div className="azals-team-list">
              {equipe.map((membre) => (
                <TeamMemberItem key={membre.id} membre={membre} />
              ))}
            </div>
          ) : intervention.intervenant_name ? (
            <div className="azals-team-list">
              <div className="azals-team-item">
                <div className="azals-team-item__avatar azals-team-item__avatar--primary">
                  <User size={16} />
                </div>
                <div className="azals-team-item__info">
                  <span className="azals-team-item__name">{intervention.intervenant_name}</span>
                  <span className="azals-team-item__role text-muted">Intervenant principal</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Users size={32} className="text-muted" />
              <p className="text-muted">Aucun intervenant assigné</p>
            </div>
          )}
        </Card>

        {/* Suivi temps réel */}
        <Card title="Suivi de réalisation" icon={<Clock size={18} />}>
          <div className="azals-timeline-compact">
            {/* Création */}
            <TimelineItem
              icon={<Calendar size={14} />}
              label="Création"
              date={formatDate(intervention.created_at)}
              status="done"
            />

            {/* Planification */}
            {intervention.date_prevue && (
              <TimelineItem
                icon={<Calendar size={14} />}
                label="Planifiée pour"
                date={`${formatDate(intervention.date_prevue)} ${intervention.heure_prevue || ''}`}
                status={intervention.statut === 'A_PLANIFIER' ? 'pending' : 'done'}
              />
            )}

            {/* Début */}
            {intervention.date_debut_reelle ? (
              <TimelineItem
                icon={<Play size={14} />}
                label="Démarrée"
                date={formatDateTime(intervention.date_debut_reelle)}
                status="done"
              />
            ) : intervention.statut === 'PLANIFIEE' && (
              <TimelineItem
                icon={<Play size={14} />}
                label="En attente de démarrage"
                status="pending"
              />
            )}

            {/* Fin */}
            {intervention.date_fin_reelle ? (
              <TimelineItem
                icon={<CheckCircle2 size={14} />}
                label="Terminée"
                date={formatDateTime(intervention.date_fin_reelle)}
                status="done"
              />
            ) : intervention.statut === 'EN_COURS' && (
              <TimelineItem
                icon={<Clock size={14} />}
                label="En cours..."
                status="active"
              />
            )}
          </div>
        </Card>
      </Grid>

      {/* Détail temps (ERP only) */}
      <Card title="Détail des temps" icon={<Timer size={18} />} className="mt-4 azals-std-field--secondary">
        <table className="azals-table azals-table--simple">
          <thead>
            <tr>
              <th>Phase</th>
              <th>Prévu</th>
              <th>Réel</th>
              <th className="text-right">Écart</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="font-medium">Intervention complète</td>
              <td>{formatDuration(intervention.duree_prevue_minutes)}</td>
              <td>{formatDuration(intervention.duree_reelle_minutes)}</td>
              <td className={`text-right ${durationVariance !== null && durationVariance > 0 ? 'text-danger' : durationVariance !== null ? 'text-success' : ''}`}>
                {durationVariance !== null ? `${durationVariance > 0 ? '+' : ''}${formatDuration(Math.abs(durationVariance))}` : '-'}
              </td>
            </tr>
          </tbody>
        </table>

        {/* Résumé du rapport si disponible */}
        {intervention.rapport && intervention.rapport.temps_passe_minutes && (
          <div className="mt-4 pt-4 border-t">
            <h4 className="text-sm font-medium mb-2">Temps déclaré au rapport</h4>
            <p className="text-lg font-medium">{formatDuration(intervention.rapport.temps_passe_minutes)}</p>
          </div>
        )}
      </Card>

      {/* Matériel utilisé */}
      {(intervention.materiel_utilise || intervention.rapport?.materiel_utilise) && (
        <Card title="Matériel utilisé" icon={<CheckCircle2 size={18} />} className="mt-4">
          <p className="whitespace-pre-wrap">
            {intervention.materiel_utilise || intervention.rapport?.materiel_utilise}
          </p>
        </Card>
      )}
    </div>
  );
};

/**
 * Item membre équipe
 */
const TeamMemberItem: React.FC<{ membre: InterventionEquipeMembre }> = ({ membre }) => {
  return (
    <div className="azals-team-item">
      <div className={`azals-team-item__avatar ${membre.is_principal ? 'azals-team-item__avatar--primary' : ''}`}>
        <User size={16} />
      </div>
      <div className="azals-team-item__info">
        <span className="azals-team-item__name">{membre.name}</span>
        <span className="azals-team-item__role text-muted">
          {membre.role || (membre.is_principal ? 'Intervenant principal' : 'Équipier')}
        </span>
      </div>
    </div>
  );
};

/**
 * Item timeline compact
 */
interface TimelineItemProps {
  icon: React.ReactNode;
  label: string;
  date?: string;
  status: 'done' | 'active' | 'pending';
}

const TimelineItem: React.FC<TimelineItemProps> = ({ icon, label, date, status }) => {
  const getStatusClass = () => {
    switch (status) {
      case 'done': return 'azals-timeline-item--done';
      case 'active': return 'azals-timeline-item--active';
      default: return 'azals-timeline-item--pending';
    }
  };

  return (
    <div className={`azals-timeline-item ${getStatusClass()}`}>
      <div className="azals-timeline-item__icon">{icon}</div>
      <div className="azals-timeline-item__content">
        <span className="azals-timeline-item__label">{label}</span>
        {date && <span className="azals-timeline-item__date text-muted">{date}</span>}
      </div>
    </div>
  );
};

export default InterventionLinesTab;
