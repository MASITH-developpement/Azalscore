/**
 * AZALSCORE Module - POS - Session IA Tab
 * Onglet Assistant IA pour la session
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  TrendingUp, AlertTriangle, CheckCircle2,
  Banknote, ShoppingCart, Clock, ThumbsUp
} from 'lucide-react';
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';
import { Card, Grid } from '@ui/layout';
import { formatCurrency, formatPercent } from '@/utils/formatters';
import {
  isSessionOpen, isSessionClosed, isSessionSuspended,
  hasCashDifference, hasSignificantDifference, hasTransactions,
  hasReturns, getCashPaymentPercentage
} from '../types';
import type { POSSession } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * SessionIATab - Assistant IA
 */
export const SessionIATab: React.FC<TabContentProps<POSSession>> = ({ data: session }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(session);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(session);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const performanceScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cette session et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Performance de la session - Composant partagé */}
      <Card title="Performance" icon={<TrendingUp size={18} />} className="mb-4">
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
            <h4>Ventes</h4>
            <p className="text-lg font-medium text-green-600">
              {formatCurrency(session.total_sales)}
            </p>
            <p className="text-sm text-muted">brut</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Transactions</h4>
            <p className="text-lg font-medium text-primary">{session.total_transactions}</p>
            <p className="text-sm text-muted">effectuees</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Panier moyen</h4>
            <p className="text-lg font-medium text-blue-600">
              {formatCurrency(session.average_basket)}
            </p>
            <p className="text-sm text-muted">par transaction</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Especes</h4>
            <p className="text-lg font-medium text-purple-600">
              {formatPercent(getCashPaymentPercentage(session))}
            </p>
            <p className="text-sm text-muted">des paiements</p>
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
 * Générer les actions suggérées basées sur la session
 */
function generateSuggestedActions(session: POSSession): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isSessionOpen(session) && !hasTransactions(session)) {
    actions.push({
      id: 'first-sale',
      title: 'Première vente',
      description: 'La session est ouverte mais aucune transaction.',
      confidence: 90,
      icon: <ShoppingCart size={16} />,
      actionLabel: 'Vendre',
    });
  }

  if (isSessionOpen(session) && hasTransactions(session)) {
    actions.push({
      id: 'session-active',
      title: 'Session active',
      description: `${session.total_transactions} transaction(s) enregistrée(s).`,
      confidence: 100,
      icon: <CheckCircle2 size={16} />,
    });
  }

  if (isSessionSuspended(session)) {
    actions.push({
      id: 'resume',
      title: 'Reprendre la session',
      description: 'La session est suspendue.',
      confidence: 85,
      icon: <Clock size={16} />,
      actionLabel: 'Reprendre',
    });
  }

  if (isSessionOpen(session) && session.total_transactions > 50) {
    actions.push({
      id: 'close',
      title: 'Envisager une clôture',
      description: 'Session longue avec beaucoup de transactions.',
      confidence: 70,
      icon: <CheckCircle2 size={16} />,
      actionLabel: 'Clôturer',
    });
  }

  if (hasSignificantDifference(session)) {
    actions.push({
      id: 'cash-diff',
      title: "Vérifier l'écart de caisse",
      description: `Écart de ${formatCurrency(Math.abs(session.cash_difference || 0))}.`,
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Vérifier',
    });
  }

  if (hasReturns(session)) {
    actions.push({
      id: 'returns',
      title: 'Retours enregistrés',
      description: `${formatCurrency(session.total_returns)} de retours.`,
      confidence: 75,
      icon: <Banknote size={16} />,
    });
  }

  if (isSessionClosed(session) && !hasCashDifference(session)) {
    actions.push({
      id: 'ok',
      title: 'Session conforme',
      description: 'Caisse équilibrée, pas d\'anomalie.',
      confidence: 100,
      icon: <ThumbsUp size={16} />,
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur la session
 */
function generateInsights(session: POSSession): Insight[] {
  const insights: Insight[] = [];

  // Statut session
  if (isSessionClosed(session)) {
    insights.push({
      id: 'closed',
      type: 'success',
      title: 'Session cloturee',
      description: 'La session a ete correctement fermee.',
    });
  } else if (isSessionOpen(session)) {
    insights.push({
      id: 'open',
      type: 'suggestion',
      title: 'Session en cours',
      description: 'La session est actuellement ouverte.',
    });
  } else if (isSessionSuspended(session)) {
    insights.push({
      id: 'suspended',
      type: 'warning',
      title: 'Session suspendue',
      description: 'La session est en pause.',
    });
  }

  // Transactions
  if (session.total_transactions >= 50) {
    insights.push({
      id: 'high-volume',
      type: 'success',
      title: 'Volume eleve',
      description: `${session.total_transactions} transactions effectuees.`,
    });
  } else if (session.total_transactions >= 20) {
    insights.push({
      id: 'normal-volume',
      type: 'suggestion',
      title: 'Volume normal',
      description: `${session.total_transactions} transactions effectuees.`,
    });
  } else if (session.total_transactions > 0) {
    insights.push({
      id: 'low-volume',
      type: 'suggestion',
      title: 'Volume faible',
      description: `Seulement ${session.total_transactions} transaction(s).`,
    });
  }

  // Panier moyen
  if (session.average_basket >= 100) {
    insights.push({
      id: 'high-basket',
      type: 'success',
      title: 'Panier moyen eleve',
      description: `Panier moyen de ${formatCurrency(session.average_basket)}.`,
    });
  } else if (session.average_basket >= 30) {
    insights.push({
      id: 'normal-basket',
      type: 'suggestion',
      title: 'Panier moyen correct',
      description: `Panier moyen de ${formatCurrency(session.average_basket)}.`,
    });
  }

  // Ecart de caisse
  if (hasSignificantDifference(session)) {
    insights.push({
      id: 'cash-diff',
      type: 'warning',
      title: 'Ecart de caisse',
      description: `Ecart de ${formatCurrency(Math.abs(session.cash_difference || 0))} detecte.`,
    });
  } else if (isSessionClosed(session) && !hasCashDifference(session)) {
    insights.push({
      id: 'cash-ok',
      type: 'success',
      title: 'Caisse equilibree',
      description: 'Aucun ecart de caisse.',
    });
  }

  // Retours
  if (session.total_returns > 0) {
    const returnRate = (session.total_returns / session.total_sales) * 100;
    if (returnRate > 10) {
      insights.push({
        id: 'high-returns',
        type: 'warning',
        title: 'Taux de retours eleve',
        description: `${formatPercent(returnRate)} des ventes en retours.`,
      });
    } else {
      insights.push({
        id: 'normal-returns',
        type: 'suggestion',
        title: 'Retours enregistres',
        description: `${formatCurrency(session.total_returns)} en retours.`,
      });
    }
  }

  // Remises
  if (session.discounts_given > 0) {
    const discountRate = (session.discounts_given / session.total_sales) * 100;
    if (discountRate > 15) {
      insights.push({
        id: 'high-discounts',
        type: 'warning',
        title: 'Remises elevees',
        description: `${formatPercent(discountRate)} du CA en remises.`,
      });
    } else {
      insights.push({
        id: 'normal-discounts',
        type: 'suggestion',
        title: 'Remises accordees',
        description: `${formatCurrency(session.discounts_given)} en remises.`,
      });
    }
  }

  // Repartition paiements
  const cashPercent = getCashPaymentPercentage(session);
  if (cashPercent > 70) {
    insights.push({
      id: 'mostly-cash',
      type: 'suggestion',
      title: 'Majoritairement especes',
      description: `${formatPercent(cashPercent)} en paiements especes.`,
    });
  }

  return insights;
}

export default SessionIATab;
