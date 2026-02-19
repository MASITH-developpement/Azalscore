/**
 * AZALSCORE Module - Subscriptions - IA Tab
 * Onglet Assistant IA pour l'abonnement
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  TrendingUp, AlertTriangle, CheckCircle, Gift, Repeat, XCircle, ThumbsUp
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
import { formatCurrency } from '@/utils/formatters';
import {
  getSubscriptionAgeDays, getDaysUntilRenewal,
  getTrialDaysRemaining, getTotalPaid,
  isActive, isInTrial, isPastDue, isCancelled, willCancel,
  SUBSCRIPTION_STATUS_CONFIG
} from '../types';
import type { Subscription } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * SubscriptionIATab - Assistant IA
 */
export const SubscriptionIATab: React.FC<TabContentProps<Subscription>> = ({ data: subscription }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(subscription);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(subscription);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const retentionScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cet abonnement et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de rétention - Composant partagé */}
      <Card title="Score de rétention" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={retentionScore}
          label="Rétention"
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur l'abonnement
 */
function generateSuggestedActions(subscription: Subscription): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isInTrial(subscription)) {
    actions.push({
      id: 'trial',
      title: 'Client en essai',
      description: 'Planifier un suivi pour maximiser la conversion.',
      confidence: 95,
      icon: <Gift size={16} />,
      actionLabel: 'Suivre',
    });
  }

  if (isPastDue(subscription)) {
    actions.push({
      id: 'past-due',
      title: 'Paiement en retard',
      description: 'Contacter le client pour résoudre le problème de paiement.',
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Relancer',
    });
  }

  if (willCancel(subscription)) {
    actions.push({
      id: 'will-cancel',
      title: 'Annulation en cours',
      description: 'Proposer une offre de rétention.',
      confidence: 90,
      icon: <XCircle size={16} />,
      actionLabel: 'Retenir',
    });
  }

  if (getDaysUntilRenewal(subscription) <= 7 && isActive(subscription)) {
    actions.push({
      id: 'renewal-soon',
      title: 'Renouvellement proche',
      description: 'Vérifier que le moyen de paiement est valide.',
      confidence: 85,
      icon: <Repeat size={16} />,
      actionLabel: 'Vérifier',
    });
  }

  if (getSubscriptionAgeDays(subscription) > 365 && isActive(subscription)) {
    actions.push({
      id: 'loyal',
      title: 'Client fidèle',
      description: 'Envisager une offre spéciale anniversaire.',
      confidence: 80,
      icon: <CheckCircle size={16} />,
      actionLabel: 'Offrir',
    });
  }

  if (isActive(subscription) && !willCancel(subscription) && !isPastDue(subscription)) {
    actions.push({
      id: 'healthy',
      title: 'Abonnement sain',
      description: 'Aucune action requise.',
      confidence: 100,
      icon: <ThumbsUp size={16} />,
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur l'abonnement
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
