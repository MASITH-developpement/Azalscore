/**
 * AZALSCORE Module - Subscriptions - IA Tab
 * Onglet Assistant IA pour l'abonnement
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ThumbsDown, ChevronRight,
  CheckCircle, Gift, Repeat, CreditCard, XCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Subscription } from '../types';
import {
  formatCurrency, getSubscriptionAgeDays, getDaysUntilRenewal,
  getTrialDaysRemaining, getTotalPaid,
  isActive, isInTrial, isPastDue, isCancelled, willCancel,
  SUBSCRIPTION_STATUS_CONFIG
} from '../types';

/**
 * SubscriptionIATab - Assistant IA
 */
export const SubscriptionIATab: React.FC<TabContentProps<Subscription>> = ({ data: subscription }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(subscription);

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
            J'ai analyse cet abonnement et identifie{' '}
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

      {/* Score de retention */}
      <Card title="Score de retention" icon={<TrendingUp size={18} />} className="mb-4">
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
                strokeDasharray={`${insights.filter(i => i.type !== 'warning').length * 25}, 100`}
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
            {isInTrial(subscription) && (
              <SuggestedAction
                title="Client en essai"
                description="Planifier un suivi pour maximiser la conversion."
                confidence={95}
                icon={<Gift size={16} />}
              />
            )}
            {isPastDue(subscription) && (
              <SuggestedAction
                title="Paiement en retard"
                description="Contacter le client pour resoudre le probleme de paiement."
                confidence={100}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {willCancel(subscription) && (
              <SuggestedAction
                title="Annulation en cours"
                description="Proposer une offre de retention."
                confidence={90}
                icon={<XCircle size={16} />}
              />
            )}
            {getDaysUntilRenewal(subscription) <= 7 && isActive(subscription) && (
              <SuggestedAction
                title="Renouvellement proche"
                description="Verifier que le moyen de paiement est valide."
                confidence={85}
                icon={<Repeat size={16} />}
              />
            )}
            {getSubscriptionAgeDays(subscription) > 365 && isActive(subscription) && (
              <SuggestedAction
                title="Client fidele"
                description="Envisager une offre speciale anniversaire."
                confidence={80}
                icon={<CheckCircle size={16} />}
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
            <p className={`text-lg font-medium text-${SUBSCRIPTION_STATUS_CONFIG[subscription.status].color}`}>
              {SUBSCRIPTION_STATUS_CONFIG[subscription.status].label}
            </p>
            <p className="text-sm text-muted">
              {SUBSCRIPTION_STATUS_CONFIG[subscription.status].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Valeur totale</h4>
            <p className="text-lg font-medium text-primary">
              {formatCurrency(getTotalPaid(subscription), subscription.currency)}
            </p>
            <p className="text-sm text-muted">
              Revenus generes
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Anciennete</h4>
            <p className="text-lg font-medium text-primary">
              {getSubscriptionAgeDays(subscription)}j
            </p>
            <p className="text-sm text-muted">
              Depuis la souscription
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Prochain paiement</h4>
            <p className="text-lg font-medium">
              {getDaysUntilRenewal(subscription)}j
            </p>
            <p className="text-sm text-muted">
              Avant renouvellement
            </p>
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
 * Generer les insights bases sur l'abonnement
 */
function generateInsights(subscription: Subscription): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (isActive(subscription) && !willCancel(subscription)) {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Abonnement actif',
      description: 'L\'abonnement est en cours et le client est engage.',
    });
  }

  if (isInTrial(subscription)) {
    const trialDays = getTrialDaysRemaining(subscription);
    insights.push({
      id: 'trial',
      type: 'suggestion',
      title: 'En periode d\'essai',
      description: trialDays !== null
        ? `${trialDays} jour${trialDays > 1 ? 's' : ''} restant${trialDays > 1 ? 's' : ''} avant conversion.`
        : 'La periode d\'essai est en cours.',
    });
  }

  if (isPastDue(subscription)) {
    insights.push({
      id: 'past-due',
      type: 'warning',
      title: 'Paiement en retard',
      description: 'Action requise pour resoudre le probleme de paiement.',
    });
  }

  if (willCancel(subscription)) {
    insights.push({
      id: 'will-cancel',
      type: 'warning',
      title: 'Annulation programmee',
      description: 'Opportunite de retention avant la fin de periode.',
    });
  }

  if (isCancelled(subscription)) {
    insights.push({
      id: 'cancelled',
      type: 'warning',
      title: 'Abonnement termine',
      description: 'Envisager une campagne de reactivation.',
    });
  }

  // Anciennete
  const ageDays = getSubscriptionAgeDays(subscription);
  if (ageDays > 365 && isActive(subscription)) {
    insights.push({
      id: 'loyal',
      type: 'success',
      title: 'Client fidele',
      description: `Abonne depuis plus d'un an (${Math.floor(ageDays / 365)} an${Math.floor(ageDays / 365) > 1 ? 's' : ''}).`,
    });
  } else if (ageDays < 30 && isActive(subscription)) {
    insights.push({
      id: 'new',
      type: 'suggestion',
      title: 'Nouvel abonne',
      description: 'Periode critique - assurer un bon onboarding.',
    });
  }

  // Renouvellement
  const daysUntilRenewal = getDaysUntilRenewal(subscription);
  if (daysUntilRenewal <= 7 && daysUntilRenewal > 0 && isActive(subscription)) {
    insights.push({
      id: 'renewal-soon',
      type: 'suggestion',
      title: 'Renouvellement imminent',
      description: `Dans ${daysUntilRenewal} jour${daysUntilRenewal > 1 ? 's' : ''}.`,
    });
  }

  // Valeur
  const totalPaid = getTotalPaid(subscription);
  if (totalPaid > 1000) {
    insights.push({
      id: 'high-value',
      type: 'success',
      title: 'Client a haute valeur',
      description: `${formatCurrency(totalPaid, subscription.currency)} de revenus generes.`,
    });
  }

  return insights;
}

export default SubscriptionIATab;
