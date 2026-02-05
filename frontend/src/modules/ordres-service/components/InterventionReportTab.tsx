/**
 * AZALSCORE Module - Ordres de Service - Intervention Report Tab
 * Onglet compte-rendu de l'intervention
 */

import React from 'react';
import {
  FileText, CheckCircle, Euro, Clock, AlertTriangle, Star
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Intervention } from '../types';
import {
  getActualDuration, getAmountVariance, getDurationVariance
} from '../types';
import { formatCurrency, formatDuration } from '@/utils/formatters';

/**
 * InterventionReportTab - Compte-rendu
 */
export const InterventionReportTab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const isCompleted = intervention.statut === 'TERMINEE' || intervention.statut === 'ANNULEE';
  const actualDuration = getActualDuration(intervention);
  const durationVariance = getDurationVariance(intervention);
  const amountVariance = getAmountVariance(intervention);

  if (!isCompleted && !intervention.commentaire_cloture) {
    return (
      <div className="azals-std-tab-content">
        <div className="azals-empty">
          <FileText size={48} className="text-muted" />
          <h3>Compte-rendu non disponible</h3>
          <p className="text-muted">
            Le compte-rendu sera disponible une fois l'intervention terminee.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="azals-std-tab-content">
      {/* Statut de cloture */}
      <Card className="mb-4">
        <div className="flex items-center gap-4">
          <div className={`azals-icon-circle azals-icon-circle--${intervention.statut === 'TERMINEE' ? 'success' : 'warning'}`}>
            {intervention.statut === 'TERMINEE' ? (
              <CheckCircle size={24} />
            ) : (
              <AlertTriangle size={24} />
            )}
          </div>
          <div>
            <h3 className="text-lg font-medium">
              {intervention.statut === 'TERMINEE' ? 'Intervention terminee' : 'Intervention annulee'}
            </h3>
            <p className="text-muted">
              {intervention.statut === 'TERMINEE'
                ? 'Les travaux ont ete realises avec succes.'
                : 'L\'intervention a ete annulee.'}
            </p>
          </div>
        </div>
      </Card>

      {/* Commentaire de cloture */}
      <Card title="Compte-rendu" icon={<FileText size={18} />} className="mb-4">
        <p className={intervention.commentaire_cloture ? '' : 'text-muted'}>
          {intervention.commentaire_cloture || 'Aucun commentaire de cloture'}
        </p>
      </Card>

      {/* Bilan temps et couts */}
      <Grid cols={2} gap="lg">
        <Card title="Bilan temps" icon={<Clock size={18} />}>
          <div className="azals-stats-grid">
            <div className="azals-stat">
              <span className="azals-stat__label">Duree estimee</span>
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
            {durationVariance !== null && (
              <div className="azals-stat" style={{ gridColumn: 'span 2' }}>
                <span className="azals-stat__label">Ecart</span>
                <span className={`azals-stat__value ${durationVariance > 0 ? 'text-warning' : 'text-success'}`}>
                  {durationVariance > 0 ? '+' : ''}{formatDuration(Math.abs(durationVariance))}
                  {durationVariance > 0 ? ' (depassement)' : ' (economie)'}
                </span>
              </div>
            )}
          </div>
        </Card>

        <Card title="Bilan financier" icon={<Euro size={18} />}>
          <div className="azals-stats-grid">
            <div className="azals-stat">
              <span className="azals-stat__label">Montant estime</span>
              <span className="azals-stat__value">
                {intervention.montant_ht
                  ? formatCurrency(intervention.montant_ht)
                  : '-'}
              </span>
            </div>
            <div className="azals-stat">
              <span className="azals-stat__label">Montant reel</span>
              <span className="azals-stat__value">
                {intervention.montant_ttc
                  ? formatCurrency(intervention.montant_ttc)
                  : '-'}
              </span>
            </div>
            {amountVariance !== null && (
              <div className="azals-stat" style={{ gridColumn: 'span 2' }}>
                <span className="azals-stat__label">Ecart</span>
                <span className={`azals-stat__value ${amountVariance > 0 ? 'text-warning' : 'text-success'}`}>
                  {amountVariance > 0 ? '+' : ''}{formatCurrency(amountVariance)}
                </span>
              </div>
            )}
          </div>
        </Card>
      </Grid>

      {/* Qualite (ERP only) */}
      <Card
        title="Indicateurs qualite"
        icon={<Star size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={3} gap="md">
          <div className="azals-stat">
            <span className="azals-stat__label">Respect delais</span>
            <span className={`azals-stat__value ${durationVariance && durationVariance > 30 ? 'text-warning' : 'text-success'}`}>
              {durationVariance !== null
                ? (durationVariance <= 30 ? 'Oui' : 'Depassement')
                : '-'}
            </span>
          </div>
          <div className="azals-stat">
            <span className="azals-stat__label">Respect budget</span>
            <span className={`azals-stat__value ${amountVariance && amountVariance > 0 ? 'text-warning' : 'text-success'}`}>
              {amountVariance !== null
                ? (amountVariance <= 0 ? 'Oui' : 'Depassement')
                : '-'}
            </span>
          </div>
          <div className="azals-stat">
            <span className="azals-stat__label">Documentation</span>
            <span className="azals-stat__value">
              {(intervention.photos?.length || 0) > 0 ? 'Complete' : 'Incomplete'}
            </span>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default InterventionReportTab;
