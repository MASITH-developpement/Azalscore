/**
 * AZALSCORE Module - Qualite - NC Stats Tab
 * Onglet statistiques et metriques
 */

import React from 'react';
import {
  BarChart3, TrendingUp, Clock, Calendar, Target, AlertTriangle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { NonConformance } from '../types';
import {
  getNCAgeDays, isNCOverdue,
  NC_STATUS_CONFIG, SEVERITY_CONFIG
} from '../types';
import { formatDate } from '@/utils/formatters';

/**
 * NCStatsTab - Statistiques
 */
export const NCStatsTab: React.FC<TabContentProps<NonConformance>> = ({ data: nc }) => {
  const ageDays = getNCAgeDays(nc);
  const isOverdue = isNCOverdue(nc);
  const statusConfig = NC_STATUS_CONFIG[nc.status];
  const severityConfig = SEVERITY_CONFIG[nc.severity];

  // Calculer les metriques
  const hasRootCause = !!nc.root_cause;
  const hasCorrectiveAction = !!nc.corrective_action;
  const hasPreventiveAction = !!nc.preventive_action;
  const completionScore = [hasRootCause, hasCorrectiveAction, hasPreventiveAction].filter(Boolean).length;

  return (
    <div className="azals-std-tab-content">
      {/* Metriques principales */}
      <Grid cols={4} gap="md" className="mb-4">
        <Card>
          <div className="azals-stat text-center">
            <Clock size={24} className="text-primary mx-auto mb-2" />
            <span className="azals-stat__value text-2xl">{ageDays}</span>
            <span className="azals-stat__label">jours d'age</span>
          </div>
        </Card>

        <Card>
          <div className="azals-stat text-center">
            <Target size={24} className={`mx-auto mb-2 ${isOverdue ? 'text-danger' : 'text-success'}`} />
            <span className={`azals-stat__value text-2xl ${isOverdue ? 'text-danger' : ''}`}>
              {nc.target_date ? (isOverdue ? 'Depasse' : 'OK') : '-'}
            </span>
            <span className="azals-stat__label">Objectif</span>
          </div>
        </Card>

        <Card>
          <div className="azals-stat text-center">
            <BarChart3 size={24} className="text-primary mx-auto mb-2" />
            <span className="azals-stat__value text-2xl">{completionScore}/3</span>
            <span className="azals-stat__label">Etapes completees</span>
          </div>
        </Card>

        <Card>
          <div className="azals-stat text-center">
            <AlertTriangle size={24} className={`mx-auto mb-2 text-${severityConfig.color}`} />
            <span className={`azals-stat__value text-2xl text-${severityConfig.color}`}>
              {severityConfig.label}
            </span>
            <span className="azals-stat__label">Gravite</span>
          </div>
        </Card>
      </Grid>

      {/* Progression du traitement */}
      <Card title="Progression du traitement" icon={<TrendingUp size={18} />} className="mb-4">
        <div className="azals-progress-steps">
          <div className={`azals-progress-step ${nc.status !== 'OPEN' ? 'azals-progress-step--completed' : 'azals-progress-step--active'}`}>
            <div className="azals-progress-step__indicator">1</div>
            <div className="azals-progress-step__content">
              <h4>Ouverture</h4>
              <p className="text-sm text-muted">NC detectee et enregistree</p>
            </div>
          </div>

          <div className={`azals-progress-step ${hasRootCause ? 'azals-progress-step--completed' : nc.status === 'IN_ANALYSIS' ? 'azals-progress-step--active' : ''}`}>
            <div className="azals-progress-step__indicator">2</div>
            <div className="azals-progress-step__content">
              <h4>Analyse</h4>
              <p className="text-sm text-muted">Identification de la cause racine</p>
            </div>
          </div>

          <div className={`azals-progress-step ${hasCorrectiveAction ? 'azals-progress-step--completed' : nc.status === 'ACTION_PLANNED' ? 'azals-progress-step--active' : ''}`}>
            <div className="azals-progress-step__indicator">3</div>
            <div className="azals-progress-step__content">
              <h4>Action corrective</h4>
              <p className="text-sm text-muted">Definition et mise en oeuvre</p>
            </div>
          </div>

          <div className={`azals-progress-step ${nc.status === 'CLOSED' ? 'azals-progress-step--completed' : ''}`}>
            <div className="azals-progress-step__indicator">4</div>
            <div className="azals-progress-step__content">
              <h4>Cloture</h4>
              <p className="text-sm text-muted">Verification et fermeture</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Timeline (ERP only) */}
      <Card
        title="Timeline"
        icon={<Calendar size={18} />}
        className="azals-std-field--secondary"
      >
        <div className="azals-timeline-horizontal">
          <div className="azals-timeline-horizontal__item">
            <div className="azals-timeline-horizontal__date">
              {formatDate(nc.detected_date)}
            </div>
            <div className="azals-timeline-horizontal__label">Detection</div>
          </div>

          {nc.target_date && (
            <div className={`azals-timeline-horizontal__item ${isOverdue ? 'azals-timeline-horizontal__item--danger' : ''}`}>
              <div className="azals-timeline-horizontal__date">
                {formatDate(nc.target_date)}
              </div>
              <div className="azals-timeline-horizontal__label">Objectif</div>
            </div>
          )}

          {nc.closed_date && (
            <div className="azals-timeline-horizontal__item azals-timeline-horizontal__item--success">
              <div className="azals-timeline-horizontal__date">
                {formatDate(nc.closed_date)}
              </div>
              <div className="azals-timeline-horizontal__label">Cloture</div>
            </div>
          )}
        </div>

        {isOverdue && (
          <div className="azals-alert azals-alert--danger mt-4">
            <AlertTriangle size={18} />
            <div>
              <strong>Objectif depasse</strong>
              <p className="text-sm">
                Cette NC aurait du etre cloturee le {formatDate(nc.target_date)}.
              </p>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default NCStatsTab;
