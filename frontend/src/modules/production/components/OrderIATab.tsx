/**
 * AZALSCORE Module - Production - Order IA Tab
 * Onglet Assistant IA pour l'ordre de fabrication
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Clock, Package, Settings, Target
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { ProductionOrder } from '../types';
import {
  formatDuration, formatCurrency, formatPercent,
  ORDER_STATUS_CONFIG, ORDER_PRIORITY_CONFIG,
  isLate, isUrgent, getCompletionRate, getScrapRate,
  getCostVariance, getDurationVariance,
  isDraft, isConfirmed, isInProgress, isDone
} from '../types';

/**
 * OrderIATab - Assistant IA pour l'ordre de fabrication
 */
export const OrderIATab: React.FC<TabContentProps<ProductionOrder>> = ({ data: order }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Generer les insights
  const insights = generateInsights(order);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  return (
    <div className="azals-std-tab-content">
      {/* En-tete IA (mode AZALSCORE) */}
      <div className="azals-std-ia-panel azals-std-azalscore-only">
        <div className="azals-std-ia-panel__header">
          <Sparkles size={24} className="azals-std-ia-panel__icon" />
          <h3 className="azals-std-ia-panel__title">Assistant AZALSCORE IA</h3>
        </div>
        <div className="azals-std-ia-panel__content">
          <p>
            J'ai analyse cet ordre de fabrication et identifie{' '}
            <strong>{insights.length} points d'attention</strong>.
            {insights.filter(i => i.type === 'warning').length > 0 && (
              <span className="text-warning ml-1">
                ({insights.filter(i => i.type === 'warning').length} alertes)
              </span>
            )}
          </p>
        </div>
        <div className="azals-std-ia-panel__actions">
          <Button
            variant="secondary"
            leftIcon={<RefreshCw size={16} className={isAnalyzing ? 'azals-spin' : ''} />}
            onClick={handleRefreshAnalysis}
            disabled={isAnalyzing}
          >
            Relancer l'analyse
          </Button>
          <Button variant="ghost" leftIcon={<MessageSquare size={16} />}>
            Poser une question
          </Button>
        </div>
      </div>

      {/* Score de performance */}
      <Card title="Score de performance" icon={<TrendingUp size={18} />} className="mb-4">
        <div className="azals-score-display">
          <div className="azals-score-display__circle">
            <svg viewBox="0 0 36 36" className="azals-score-display__svg">
              <path
                className="azals-score-display__bg"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="3"
              />
              <path
                className="azals-score-display__fg"
                strokeDasharray={`${insights.filter(i => i.type !== 'warning').length * 20}, 100`}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="var(--azals-primary-500)"
                strokeWidth="3"
                strokeLinecap="round"
              />
            </svg>
            <span className="azals-score-display__value">
              {Math.round((insights.filter(i => i.type !== 'warning').length / Math.max(insights.length, 1)) * 100)}%
            </span>
          </div>
          <div className="azals-score-display__details">
            <p>
              {insights.filter(i => i.type === 'success').length} points positifs,{' '}
              {insights.filter(i => i.type === 'warning').length} alertes,{' '}
              {insights.filter(i => i.type === 'suggestion').length} suggestions
            </p>
          </div>
        </div>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Insights */}
        <Card title="Insights IA" icon={<Lightbulb size={18} />}>
          <div className="azals-insights-list">
            {insights.map((insight) => (
              <InsightItem key={insight.id} insight={insight} />
            ))}
          </div>
        </Card>

        {/* Actions suggerees */}
        <Card title="Actions suggerees" icon={<ChevronRight size={18} />}>
          <div className="azals-suggested-actions">
            {isDraft(order) && (
              <SuggestedAction
                title="Confirmer l'ordre"
                description="Valider l'ordre pour lancer la production."
                confidence={90}
                icon={<Target size={16} />}
              />
            )}
            {isConfirmed(order) && (
              <SuggestedAction
                title="Demarrer la production"
                description="Lancer les operations de fabrication."
                confidence={85}
                icon={<Settings size={16} />}
              />
            )}
            {isInProgress(order) && getCompletionRate(order) >= 0.9 && (
              <SuggestedAction
                title="Cloturer l'ordre"
                description="La production est presque terminee."
                confidence={getCompletionRate(order) * 100}
                icon={<Target size={16} />}
              />
            )}
            {isLate(order) && (
              <SuggestedAction
                title="Replanifier"
                description="L'ordre est en retard, ajuster le planning."
                confidence={75}
                icon={<Clock size={16} />}
              />
            )}
            {getScrapRate(order) > 0.05 && (
              <SuggestedAction
                title="Analyser les rebuts"
                description="Taux de rebut eleve - investigation recommandee."
                confidence={80}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {!order.responsible_name && (
              <SuggestedAction
                title="Assigner un responsable"
                description="Aucun responsable designe pour cet ordre."
                confidence={70}
                icon={<Package size={16} />}
              />
            )}
          </div>
        </Card>
      </Grid>

      {/* Analyse detaillee (ERP only) */}
      <Card
        title="Analyse detaillee"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-analysis-grid">
          <div className="azals-analysis-item">
            <h4>Statut</h4>
            <p className={`text-lg font-medium text-${ORDER_STATUS_CONFIG[order.status].color}`}>
              {ORDER_STATUS_CONFIG[order.status].label}
            </p>
            <p className="text-sm text-muted">
              {ORDER_STATUS_CONFIG[order.status].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Avancement</h4>
            <p className={`text-lg font-medium ${
              getCompletionRate(order) >= 1 ? 'text-success' :
              getCompletionRate(order) >= 0.5 ? 'text-warning' : 'text-muted'
            }`}>
              {formatPercent(getCompletionRate(order))}
            </p>
            <p className="text-sm text-muted">
              {order.quantity_produced} / {order.quantity_planned} {order.unit || 'unites'}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Ecart cout</h4>
            {getCostVariance(order) !== null ? (
              <>
                <p className={`text-lg font-medium ${
                  getCostVariance(order)! > 0 ? 'text-danger' :
                  getCostVariance(order)! < 0 ? 'text-success' : ''
                }`}>
                  {getCostVariance(order)! > 0 ? '+' : ''}{formatCurrency(getCostVariance(order)!)}
                </p>
                <p className="text-sm text-muted">
                  vs budget {formatCurrency(order.cost_planned || 0)}
                </p>
              </>
            ) : (
              <p className="text-muted">Non disponible</p>
            )}
          </div>
          <div className="azals-analysis-item">
            <h4>Ecart duree</h4>
            {getDurationVariance(order) !== null ? (
              <>
                <p className={`text-lg font-medium ${
                  getDurationVariance(order)! > 0 ? 'text-danger' :
                  getDurationVariance(order)! < 0 ? 'text-success' : ''
                }`}>
                  {getDurationVariance(order)! > 0 ? '+' : ''}{formatDuration(Math.abs(getDurationVariance(order)!))}
                </p>
                <p className="text-sm text-muted">
                  vs prevu {formatDuration(order.duration_planned || 0)}
                </p>
              </>
            ) : (
              <p className="text-muted">Non disponible</p>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
};

/**
 * Types pour les insights
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Composant item d'insight
 */
const InsightItem: React.FC<{ insight: Insight }> = ({ insight }) => {
  const getIcon = () => {
    switch (insight.type) {
      case 'success':
        return <ThumbsUp size={16} className="text-success" />;
      case 'warning':
        return <AlertTriangle size={16} className="text-warning" />;
      case 'suggestion':
        return <Lightbulb size={16} className="text-primary" />;
    }
  };

  return (
    <div className={`azals-insight azals-insight--${insight.type}`}>
      <div className="azals-insight__icon">{getIcon()}</div>
      <div className="azals-insight__content">
        <h4 className="azals-insight__title">{insight.title}</h4>
        <p className="azals-insight__description">{insight.description}</p>
      </div>
    </div>
  );
};

/**
 * Composant action suggeree
 */
interface SuggestedActionProps {
  title: string;
  description: string;
  confidence: number;
  icon?: React.ReactNode;
}

const SuggestedAction: React.FC<SuggestedActionProps> = ({ title, description, confidence, icon }) => {
  return (
    <div className="azals-suggested-action">
      <div className="azals-suggested-action__content">
        <h4>
          {icon && <span className="mr-2">{icon}</span>}
          {title}
        </h4>
        <p className="text-muted text-sm">{description}</p>
      </div>
      <div className="azals-suggested-action__confidence">
        <span className={`azals-confidence azals-confidence--${confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low'}`}>
          {confidence}%
        </span>
      </div>
    </div>
  );
};

/**
 * Generer les insights bases sur l'ordre
 */
function generateInsights(order: ProductionOrder): Insight[] {
  const insights: Insight[] = [];

  // Statut de l'ordre
  if (isDone(order)) {
    insights.push({
      id: 'completed',
      type: 'success',
      title: 'Ordre termine',
      description: `Production achevee avec ${order.quantity_produced} unites.`,
    });
  } else if (isInProgress(order)) {
    const rate = getCompletionRate(order);
    if (rate >= 0.75) {
      insights.push({
        id: 'near-completion',
        type: 'success',
        title: 'Production avancee',
        description: `${formatPercent(rate)} de la production realisee.`,
      });
    } else {
      insights.push({
        id: 'in-progress',
        type: 'suggestion',
        title: 'Production en cours',
        description: `Avancement: ${formatPercent(rate)}.`,
      });
    }
  }

  // Retard
  if (isLate(order)) {
    insights.push({
      id: 'late',
      type: 'warning',
      title: 'Ordre en retard',
      description: 'La date d\'echeance est depassee.',
    });
  }

  // Priorite
  if (isUrgent(order)) {
    insights.push({
      id: 'urgent',
      type: 'warning',
      title: 'Priorite elevee',
      description: `Ordre marque comme ${ORDER_PRIORITY_CONFIG[order.priority].label.toLowerCase()}.`,
    });
  }

  // Taux de rebut
  const scrapRate = getScrapRate(order);
  if (scrapRate > 0.1) {
    insights.push({
      id: 'high-scrap',
      type: 'warning',
      title: 'Taux de rebut eleve',
      description: `${formatPercent(scrapRate)} de rebuts - investigation necessaire.`,
    });
  } else if (scrapRate > 0 && scrapRate <= 0.02) {
    insights.push({
      id: 'low-scrap',
      type: 'success',
      title: 'Qualite excellente',
      description: `Taux de rebut tres faible (${formatPercent(scrapRate)}).`,
    });
  }

  // Ecart cout
  const costVar = getCostVariance(order);
  if (costVar !== null) {
    if (costVar > 0 && order.cost_planned && costVar / order.cost_planned > 0.1) {
      insights.push({
        id: 'cost-overrun',
        type: 'warning',
        title: 'Depassement de budget',
        description: `Cout reel superieur de ${formatCurrency(costVar)} au budget.`,
      });
    } else if (costVar < 0) {
      insights.push({
        id: 'cost-saving',
        type: 'success',
        title: 'Economie realisee',
        description: `Cout inferieur de ${formatCurrency(Math.abs(costVar))} au budget.`,
      });
    }
  }

  // Ecart duree
  const durationVar = getDurationVariance(order);
  if (durationVar !== null) {
    if (durationVar > 0 && order.duration_planned && durationVar / order.duration_planned > 0.2) {
      insights.push({
        id: 'duration-overrun',
        type: 'warning',
        title: 'Depassement de duree',
        description: `Production plus longue de ${formatDuration(durationVar)} que prevu.`,
      });
    } else if (durationVar < 0) {
      insights.push({
        id: 'duration-saving',
        type: 'success',
        title: 'Gain de temps',
        description: `Production plus rapide de ${formatDuration(Math.abs(durationVar))} que prevu.`,
      });
    }
  }

  // Operations
  const workOrders = order.work_orders || [];
  const doneOps = workOrders.filter(wo => wo.status === 'DONE').length;
  const totalOps = workOrders.length;
  if (totalOps > 0) {
    if (doneOps === totalOps) {
      insights.push({
        id: 'all-ops-done',
        type: 'success',
        title: 'Operations terminees',
        description: `Toutes les ${totalOps} operations sont achevees.`,
      });
    } else if (doneOps > 0) {
      insights.push({
        id: 'ops-progress',
        type: 'suggestion',
        title: 'Operations en cours',
        description: `${doneOps}/${totalOps} operations terminees.`,
      });
    }
  }

  // Responsable manquant
  if (!order.responsible_name) {
    insights.push({
      id: 'no-responsible',
      type: 'suggestion',
      title: 'Responsable non assigne',
      description: 'Designez un responsable pour le suivi.',
    });
  }

  return insights;
}

export default OrderIATab;
