/**
 * AZALSCORE Module - POS - Session IA Tab
 * Onglet Assistant IA pour la session
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ChevronRight, CheckCircle2,
  Banknote, ShoppingCart, Clock
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { POSSession } from '../types';
import {
  formatCurrency, formatPercent,
  isSessionOpen, isSessionClosed, isSessionSuspended,
  hasCashDifference, hasSignificantDifference, hasTransactions,
  hasReturns, getCashPaymentPercentage, getCardPaymentPercentage
} from '../types';

/**
 * SessionIATab - Assistant IA
 */
export const SessionIATab: React.FC<TabContentProps<POSSession>> = ({ data: session }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(session);

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
            J'ai analyse cette session et identifie{' '}
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
        </div>
      </div>

      {/* Performance de la session */}
      <Card title="Performance" icon={<TrendingUp size={18} />} className="mb-4">
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
                strokeDasharray={`${Math.min(session.total_transactions, 100)}, 100`}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke={session.total_transactions >= 50 ? 'var(--azals-success-500)' : session.total_transactions >= 20 ? 'var(--azals-warning-500)' : 'var(--azals-danger-500)'}
                strokeWidth="3"
                strokeLinecap="round"
              />
            </svg>
            <span className="azals-score-display__value">
              {session.total_transactions}
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
            {isSessionOpen(session) && !hasTransactions(session) && (
              <SuggestedAction
                title="Premiere vente"
                description="La session est ouverte mais aucune transaction."
                confidence={90}
                icon={<ShoppingCart size={16} />}
              />
            )}
            {isSessionOpen(session) && hasTransactions(session) && (
              <SuggestedAction
                title="Session active"
                description={`${session.total_transactions} transaction(s) enregistree(s).`}
                confidence={100}
                icon={<CheckCircle2 size={16} />}
              />
            )}
            {isSessionSuspended(session) && (
              <SuggestedAction
                title="Reprendre la session"
                description="La session est suspendue."
                confidence={85}
                icon={<Clock size={16} />}
              />
            )}
            {isSessionOpen(session) && session.total_transactions > 50 && (
              <SuggestedAction
                title="Envisager une cloture"
                description="Session longue avec beaucoup de transactions."
                confidence={70}
                icon={<CheckCircle2 size={16} />}
              />
            )}
            {hasSignificantDifference(session) && (
              <SuggestedAction
                title="Verifier l'ecart de caisse"
                description={`Ecart de ${formatCurrency(Math.abs(session.cash_difference || 0))}.`}
                confidence={100}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {hasReturns(session) && (
              <SuggestedAction
                title="Retours enregistres"
                description={`${formatCurrency(session.total_returns)} de retours.`}
                confidence={75}
                icon={<Banknote size={16} />}
              />
            )}
            {isSessionClosed(session) && !hasCashDifference(session) && (
              <SuggestedAction
                title="Session conforme"
                description="Caisse equilibree, pas d'anomalie."
                confidence={100}
                icon={<ThumbsUp size={16} />}
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
 * Generer les insights bases sur la session
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
