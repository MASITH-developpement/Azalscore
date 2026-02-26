/**
 * AZALSCORE Module - CRM - Customer Opportunities Tab
 * Onglet opportunités commerciales du client
 */

import React from 'react';
import {
  Target, Euro, Calendar, TrendingUp,
  CheckCircle, XCircle, AlertTriangle, ChevronRight
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatCurrency, formatDate } from '@/utils/formatters';
import {
  OPPORTUNITY_STATUS_CONFIG,
  isOpportunityOpen, isOpportunityWon, isOpportunityLost,
  getWeightedValue, getDaysToClose, isOverdue
} from '../types';
import type { Customer, Opportunity } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * CustomerOpportunitiesTab - Opportunités du client
 */
export const CustomerOpportunitiesTab: React.FC<TabContentProps<Customer>> = ({ data: customer }) => {
  const opportunities = customer.opportunities || [];
  const openOpportunities = opportunities.filter(isOpportunityOpen);
  const wonOpportunities = opportunities.filter(isOpportunityWon);
  const lostOpportunities = opportunities.filter(isOpportunityLost);

  // Calculs
  const totalOpenValue = openOpportunities.reduce((sum, o) => sum + o.amount, 0);
  const _totalWeightedValue = openOpportunities.reduce((sum, o) => sum + getWeightedValue(o), 0);
  const totalWonValue = wonOpportunities.reduce((sum, o) => sum + o.amount, 0);
  const conversionRate = opportunities.length > 0
    ? (wonOpportunities.length / opportunities.length) * 100
    : 0;

  return (
    <div className="azals-std-tab-content">
      {/* Résumé */}
      <Grid cols={4} gap="md" className="mb-4">
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--blue">
            <Target size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">En cours</span>
            <span className="azals-kpi-card__value">{openOpportunities.length}</span>
          </div>
        </Card>
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--purple">
            <Euro size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">Pipeline</span>
            <span className="azals-kpi-card__value">{formatCurrency(totalOpenValue)}</span>
          </div>
        </Card>
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--green">
            <CheckCircle size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">Gagnées</span>
            <span className="azals-kpi-card__value text-success">{formatCurrency(totalWonValue)}</span>
          </div>
        </Card>
        <Card className="azals-kpi-card">
          <div className="azals-kpi-card__icon azals-kpi-card__icon--orange">
            <TrendingUp size={24} />
          </div>
          <div className="azals-kpi-card__content">
            <span className="azals-kpi-card__label">Conversion</span>
            <span className="azals-kpi-card__value">{conversionRate.toFixed(1)}%</span>
          </div>
        </Card>
      </Grid>

      {/* Opportunités en cours */}
      <Card title="Opportunités en cours" icon={<Target size={18} />} className="mb-4">
        {openOpportunities.length > 0 ? (
          <div className="azals-opportunities-list">
            {openOpportunities.map((opportunity) => (
              <OpportunityItem key={opportunity.id} opportunity={opportunity} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Target size={32} className="text-muted" />
            <p className="text-muted">Aucune opportunité en cours</p>
            <Button size="sm" variant="ghost" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createOpportunity', customerId: customer.id } })); }}>
              Créer une opportunité
            </Button>
          </div>
        )}
      </Card>

      {/* Opportunités gagnées / perdues */}
      <Grid cols={2} gap="lg">
        <Card title="Opportunités gagnées" icon={<CheckCircle size={18} />}>
          {wonOpportunities.length > 0 ? (
            <div className="azals-opportunities-list azals-opportunities-list--compact">
              {wonOpportunities.slice(0, 5).map((opportunity) => (
                <OpportunityItemCompact key={opportunity.id} opportunity={opportunity} />
              ))}
              {wonOpportunities.length > 5 && (
                <p className="text-sm text-muted text-center mt-2">
                  +{wonOpportunities.length - 5} autres
                </p>
              )}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <CheckCircle size={24} className="text-muted" />
              <p className="text-muted text-sm">Aucune opportunité gagnée</p>
            </div>
          )}
        </Card>

        <Card title="Opportunités perdues" icon={<XCircle size={18} />} className="azals-std-field--secondary">
          {lostOpportunities.length > 0 ? (
            <div className="azals-opportunities-list azals-opportunities-list--compact">
              {lostOpportunities.slice(0, 5).map((opportunity) => (
                <OpportunityItemCompact key={opportunity.id} opportunity={opportunity} />
              ))}
              {lostOpportunities.length > 5 && (
                <p className="text-sm text-muted text-center mt-2">
                  +{lostOpportunities.length - 5} autres
                </p>
              )}
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <XCircle size={24} className="text-muted" />
              <p className="text-muted text-sm">Aucune opportunité perdue</p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Pipeline visuel (ERP only) */}
      <Card title="Pipeline visuel" icon={<TrendingUp size={18} />} className="mt-4 azals-std-field--secondary">
        <div className="azals-pipeline">
          {(['NEW', 'QUALIFIED', 'PROPOSAL', 'NEGOTIATION'] as const).map((stage) => {
            const stageOpps = openOpportunities.filter(o => o.status === stage);
            const stageConfig = OPPORTUNITY_STATUS_CONFIG[stage];
            const stageValue = stageOpps.reduce((sum, o) => sum + o.amount, 0);
            return (
              <div key={stage} className="azals-pipeline__stage">
                <div className="azals-pipeline__stage-header">
                  <span className={`azals-badge azals-badge--${stageConfig.color}`}>
                    {stageConfig.label}
                  </span>
                  <span className="azals-pipeline__stage-count">{stageOpps.length}</span>
                </div>
                <div className="azals-pipeline__stage-value">
                  {formatCurrency(stageValue)}
                </div>
                <div className="azals-pipeline__stage-weighted text-sm text-muted">
                  Pondéré: {formatCurrency(stageOpps.reduce((sum, o) => sum + getWeightedValue(o), 0))}
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};

/**
 * Composant item d'opportunité détaillé
 */
interface OpportunityItemProps {
  opportunity: Opportunity;
}

const OpportunityItem: React.FC<OpportunityItemProps> = ({ opportunity }) => {
  const statusConfig = OPPORTUNITY_STATUS_CONFIG[opportunity.status];
  const daysToClose = getDaysToClose(opportunity);
  const overdue = isOverdue(opportunity);
  const weightedValue = getWeightedValue(opportunity);

  return (
    <div className={`azals-opportunity-item ${overdue ? 'azals-opportunity-item--overdue' : ''}`}>
      <div className="azals-opportunity-item__header">
        <div className="azals-opportunity-item__title">
          <h4 className="font-medium">{opportunity.name}</h4>
          <span className="text-sm font-mono text-muted ml-2">{opportunity.code}</span>
        </div>
        <span className={`azals-badge azals-badge--${statusConfig.color}`}>
          {statusConfig.label}
        </span>
      </div>
      <div className="azals-opportunity-item__content">
        <div className="azals-opportunity-item__amount">
          <Euro size={14} />
          <span className="font-semibold">{formatCurrency(opportunity.amount)}</span>
          <span className="text-muted text-sm ml-2">
            (pondéré: {formatCurrency(weightedValue)})
          </span>
        </div>
        <div className="azals-opportunity-item__meta">
          <span className="text-sm">
            <TrendingUp size={12} />
            {opportunity.probability}%
          </span>
          {opportunity.expected_close_date && (
            <span className={`text-sm ${overdue ? 'text-danger' : ''}`}>
              {overdue ? <AlertTriangle size={12} /> : <Calendar size={12} />}
              {formatDate(opportunity.expected_close_date)}
              {daysToClose !== null && !overdue && (
                <span className="text-muted ml-1">({daysToClose}j)</span>
              )}
            </span>
          )}
        </div>
      </div>
      {opportunity.description && (
        <p className="azals-opportunity-item__description text-sm text-muted mt-2">
          {opportunity.description}
        </p>
      )}
    </div>
  );
};

/**
 * Composant item d'opportunité compact
 */
const OpportunityItemCompact: React.FC<OpportunityItemProps> = ({ opportunity }) => {
  const _statusConfig = OPPORTUNITY_STATUS_CONFIG[opportunity.status];

  return (
    <div className="azals-opportunity-item-compact">
      <div className="azals-opportunity-item-compact__info">
        <span className="font-medium">{opportunity.name}</span>
        <span className="text-sm text-muted ml-2">{formatCurrency(opportunity.amount)}</span>
      </div>
      <div className="azals-opportunity-item-compact__meta">
        {opportunity.actual_close_date && (
          <span className="text-sm text-muted">{formatDate(opportunity.actual_close_date)}</span>
        )}
        <ChevronRight size={14} className="text-muted" />
      </div>
    </div>
  );
};

export default CustomerOpportunitiesTab;
