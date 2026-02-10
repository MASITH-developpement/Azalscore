/**
 * AZALSCORE Module - Ordres de Service - Intervention Planning Tab
 * Onglet planification et timing de l'intervention
 */

import React from 'react';
import {
  Calendar, Clock, User, Play, CheckCircle, AlertTriangle, Timer
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Intervention } from '../types';
import {
  getActualDuration, getDurationVariance, isInterventionLate, isInterventionToday, formatDuration as formatDur
} from '../types';
import { formatDate, formatDateTime, formatDuration } from '@/utils/formatters';

/**
 * InterventionPlanningTab - Planification
 */
export const InterventionPlanningTab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const isLate = isInterventionLate(intervention);
  const isToday = isInterventionToday(intervention);
  const actualDuration = getActualDuration(intervention);
  const durationVariance = getDurationVariance(intervention);

  return (
    <div className="azals-std-tab-content">
      {/* Alerte retard */}
      {isLate && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertTriangle size={18} />
          <div>
            <strong>Intervention en retard</strong>
            <p className="text-sm">
              La date prevue ({intervention.date_prevue_debut ? formatDateTime(intervention.date_prevue_debut) : '-'}) est passee mais l'intervention n'a pas demarre.
            </p>
          </div>
        </div>
      )}

      {/* Alerte aujourd'hui */}
      {isToday && intervention.statut === 'PLANIFIEE' && (
        <div className="azals-alert azals-alert--info mb-4">
          <Calendar size={18} />
          <div>
            <strong>Intervention prevue aujourd'hui</strong>
            <p className="text-sm">
              {intervention.date_prevue_debut ? formatDateTime(intervention.date_prevue_debut) : 'Horaire non precise'}
              {intervention.intervenant_name && ` - ${intervention.intervenant_name}`}
            </p>
          </div>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Planification */}
        <Card title="Planification" icon={<Calendar size={18} />}>
          <dl className="azals-dl">
            <dt><Calendar size={14} /> Date debut</dt>
            <dd className={isLate ? 'text-warning' : ''}>
              {intervention.date_prevue_debut ? formatDateTime(intervention.date_prevue_debut) : '-'}
              {isLate && <span className="ml-2 text-warning">(en retard)</span>}
            </dd>

            {intervention.date_prevue_fin && (
              <>
                <dt><Clock size={14} /> Date fin</dt>
                <dd>{formatDateTime(intervention.date_prevue_fin)}</dd>
              </>
            )}

            <dt><Timer size={14} /> Duree prevue</dt>
            <dd>
              {intervention.duree_prevue_minutes
                ? formatDuration(intervention.duree_prevue_minutes)
                : '-'}
            </dd>
          </dl>
        </Card>

        {/* Intervenant */}
        <Card title="Intervenant" icon={<User size={18} />}>
          {intervention.intervenant_name ? (
            <dl className="azals-dl">
              <dt><User size={14} /> Technicien</dt>
              <dd>{intervention.intervenant_name}</dd>
            </dl>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <User size={32} className="text-muted" />
              <p className="text-muted">Aucun intervenant assigne</p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Execution */}
      {(intervention.date_arrivee_site || intervention.date_demarrage || intervention.date_fin) && (
        <Card title="Execution" icon={<Play size={18} />} className="mt-4">
          <div className="azals-timeline">
            {intervention.date_arrivee_site && (
              <div className="azals-timeline__entry">
                <div className="azals-timeline__icon">
                  <CheckCircle size={16} className="text-primary" />
                </div>
                <div className="azals-timeline__content">
                  <span className="azals-timeline__action">Arrivee sur site</span>
                  <span className="azals-timeline__time text-muted">
                    {formatDateTime(intervention.date_arrivee_site)}
                  </span>
                </div>
              </div>
            )}

            {intervention.date_demarrage && (
              <div className="azals-timeline__entry">
                <div className="azals-timeline__icon">
                  <Play size={16} className="text-success" />
                </div>
                <div className="azals-timeline__content">
                  <span className="azals-timeline__action">Debut intervention</span>
                  <span className="azals-timeline__time text-muted">
                    {formatDateTime(intervention.date_demarrage)}
                  </span>
                </div>
              </div>
            )}

            {intervention.date_fin && (
              <div className="azals-timeline__entry azals-timeline__entry--last">
                <div className="azals-timeline__icon">
                  <CheckCircle size={16} className="text-success" />
                </div>
                <div className="azals-timeline__content">
                  <span className="azals-timeline__action">Fin intervention</span>
                  <span className="azals-timeline__time text-muted">
                    {formatDateTime(intervention.date_fin)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Duree reelle (ERP only) */}
      {(actualDuration || intervention.duree_reelle_minutes) && (
        <Card
          title="Temps passe"
          icon={<Timer size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <Grid cols={3} gap="md">
            <div className="azals-stat">
              <span className="azals-stat__label">Duree prevue</span>
              <span className="azals-stat__value">
                {intervention.duree_prevue_minutes
                  ? formatDuration(intervention.duree_prevue_minutes)
                  : '-'}
              </span>
            </div>
            <div className="azals-stat">
              <span className="azals-stat__label">Duree reelle</span>
              <span className="azals-stat__value">
                {actualDuration || '-'}
              </span>
            </div>
            <div className="azals-stat">
              <span className="azals-stat__label">Ecart</span>
              <span className={`azals-stat__value ${durationVariance && durationVariance > 0 ? 'text-warning' : durationVariance && durationVariance < 0 ? 'text-success' : ''}`}>
                {durationVariance !== null
                  ? `${durationVariance > 0 ? '+' : ''}${formatDuration(Math.abs(durationVariance))}`
                  : '-'}
              </span>
            </div>
          </Grid>
        </Card>
      )}
    </div>
  );
};

export default InterventionPlanningTab;
