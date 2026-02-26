/**
 * AZALSCORE Module - Production - Order IA Tab
 * Onglet Assistant IA pour l'ordre de fabrication
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, AlertTriangle, Clock, Package, Settings, Target } from 'lucide-react';
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';
import { Card, Grid } from '@ui/layout';
import { formatDuration, formatCurrency, formatPercent } from '@/utils/formatters';
import {
  ORDER_STATUS_CONFIG, ORDER_PRIORITY_CONFIG,
  isLate, isUrgent, getCompletionRate, getScrapRate,
  getCostVariance, getDurationVariance,
  isDraft, isConfirmed, isInProgress, isDone
} from '../types';
import type { ProductionOrder } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * OrderIATab - Assistant IA pour l'ordre de fabrication
 */
export const OrderIATab: React.FC<TabContentProps<ProductionOrder>> = ({ data: order }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(order);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(order);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const performanceScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cet ordre de fabrication et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de performance - Composant partagé */}
      <Card title="Score de performance" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={performanceScore}
          label="Performance"
          details={`${positiveCount} points positifs, ${warningCount} alertes, ${suggestionCount} suggestions`}
        />
      </Card>

      <Grid cols={2} gap="lg">
        {/* Insights - Composant partagé */}
        <Card title="Insights IA">
          <InsightList insights={sharedInsights} />
        </Card>

        {/* Actions suggérées - Composant partagé */}
        <Card title="Actions suggérées">
          <SuggestedActionList
            actions={suggestedActions}
            emptyMessage="Aucune action suggérée pour le moment"
          />
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur l'ordre
 */
function generateSuggestedActions(order: ProductionOrder): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isDraft(order)) {
    actions.push({
      id: 'confirm',
      title: "Confirmer l'ordre",
      description: "Valider l'ordre pour lancer la production.",
      confidence: 90,
      icon: <Target size={16} />,
      actionLabel: 'Confirmer',
    });
  }

  if (isConfirmed(order)) {
    actions.push({
      id: 'start',
      title: 'Démarrer la production',
      description: 'Lancer les opérations de fabrication.',
      confidence: 85,
      icon: <Settings size={16} />,
      actionLabel: 'Démarrer',
    });
  }

  if (isInProgress(order) && getCompletionRate(order) >= 0.9) {
    actions.push({
      id: 'close',
      title: "Clôturer l'ordre",
      description: 'La production est presque terminée.',
      confidence: Math.round(getCompletionRate(order) * 100),
      icon: <Target size={16} />,
      actionLabel: 'Clôturer',
    });
  }

  if (isLate(order)) {
    actions.push({
      id: 'reschedule',
      title: 'Replanifier',
      description: "L'ordre est en retard, ajuster le planning.",
      confidence: 75,
      icon: <Clock size={16} />,
      actionLabel: 'Replanifier',
    });
  }

  if (getScrapRate(order) > 0.05) {
    actions.push({
      id: 'scrap-analysis',
      title: 'Analyser les rebuts',
      description: 'Taux de rebut élevé - investigation recommandée.',
      confidence: 80,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Analyser',
    });
  }

  if (!order.responsible_name) {
    actions.push({
      id: 'assign',
      title: 'Assigner un responsable',
      description: 'Aucun responsable désigné pour cet ordre.',
      confidence: 70,
      icon: <Package size={16} />,
      actionLabel: 'Assigner',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur l'ordre
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
