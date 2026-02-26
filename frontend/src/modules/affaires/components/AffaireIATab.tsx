/**
 * AZALSCORE Module - AFFAIRES - IA Tab
 * Onglet Assistant IA pour l'affaire
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, Target, ChevronRight, Calendar, Euro, AlertTriangle } from 'lucide-react';
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
  isLate, getDaysRemaining, getBudgetStatus, getProgressStatus
} from '../types';
import type { Affaire } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * AffaireIATab - Assistant IA pour l'affaire
 * Fournit des insights, suggestions et analyses automatiques
 */
export const AffaireIATab: React.FC<TabContentProps<Affaire>> = ({ data: affaire }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights basés sur les données de l'affaire
  const insights = generateInsights(affaire);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(affaire);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const healthScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cette affaire et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de santé projet - Composant partagé */}
      <Card title="Score de santé projet" icon={<Target size={18} />} className="mb-4">
        <IAScoreCircle
          score={healthScore}
          label="Santé"
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

      {/* Analyse détaillée (ERP only) */}
      <Card
        title="Analyse détaillée"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-analysis-grid">
          <div className="azals-analysis-item">
            <h4>Santé budget</h4>
            <p className={`text-lg font-medium ${getBudgetStatus(affaire) === 'danger' ? 'text-danger' : getBudgetStatus(affaire) === 'warning' ? 'text-warning' : 'text-success'}`}>
              {getBudgetStatus(affaire) === 'danger' ? 'Critique' : getBudgetStatus(affaire) === 'warning' ? 'Attention' : 'Bon'}
            </p>
            <p className="text-sm text-muted">Consommation: {formatPercent((affaire.budget_spent || 0) / Math.max(affaire.budget_total || 1, 1) * 100)}</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Respect délais</h4>
            <p className={`text-lg font-medium ${isLate(affaire) ? 'text-danger' : 'text-success'}`}>
              {isLate(affaire) ? 'En retard' : getDaysRemaining(affaire.end_date) !== null && getDaysRemaining(affaire.end_date)! <= 7 ? 'Proche' : 'Dans les temps'}
            </p>
            <p className="text-sm text-muted">
              {getDaysRemaining(affaire.end_date) !== null
                ? getDaysRemaining(affaire.end_date)! > 0
                  ? `${getDaysRemaining(affaire.end_date)} jours restants`
                  : `${Math.abs(getDaysRemaining(affaire.end_date)!)} jours de retard`
                : 'Non planifié'}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Progression</h4>
            <p className={`text-lg font-medium ${getProgressStatus(affaire) === 'danger' ? 'text-danger' : getProgressStatus(affaire) === 'warning' ? 'text-warning' : 'text-success'}`}>
              {formatPercent(affaire.progress)}
            </p>
            <p className="text-sm text-muted">Avancement réel</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Facturation</h4>
            <p className="text-lg font-medium">
              {formatPercent((affaire.total_invoiced || 0) / Math.max(affaire.budget_total || 1, 1) * 100)}
            </p>
            <p className="text-sm text-muted">Du budget facturé</p>
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
 * Générer les actions suggérées basées sur l'affaire
 */
function generateSuggestedActions(affaire: Affaire): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (affaire.status === 'PLANIFIE') {
    actions.push({
      id: 'start',
      title: "Démarrer l'affaire",
      description: "L'affaire est planifiée et peut être démarrée.",
      confidence: 85,
      icon: <ChevronRight size={16} />,
      actionLabel: 'Démarrer',
    });
  }

  if (affaire.status === 'EN_COURS' && affaire.progress >= 100) {
    actions.push({
      id: 'close',
      title: "Clôturer l'affaire",
      description: "L'avancement est à 100%. Vous pouvez clôturer l'affaire.",
      confidence: 95,
      icon: <Target size={16} />,
      actionLabel: 'Clôturer',
    });
  }

  if (affaire.status === 'TERMINE' && (affaire.total_invoiced || 0) < (affaire.budget_total || 0)) {
    actions.push({
      id: 'invoice',
      title: "Facturer l'affaire",
      description: `Il reste ${formatCurrency((affaire.budget_total || 0) - (affaire.total_invoiced || 0))} à facturer.`,
      confidence: 90,
      icon: <Euro size={16} />,
      actionLabel: 'Facturer',
    });
  }

  if (isLate(affaire)) {
    actions.push({
      id: 'update-planning',
      title: 'Mettre à jour la planification',
      description: "L'échéance est dépassée. Révisez la date de fin.",
      confidence: 85,
      icon: <Calendar size={16} />,
      actionLabel: 'Modifier',
    });
  }

  if (getBudgetStatus(affaire) !== 'ok') {
    actions.push({
      id: 'review-budget',
      title: 'Revoir le budget',
      description: 'Le budget est sous pression. Analysez les coûts.',
      confidence: 80,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Analyser',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur l'affaire
 */
function generateInsights(affaire: Affaire): Insight[] {
  const insights: Insight[] = [];
  const daysRemaining = getDaysRemaining(affaire.end_date);
  const budgetStatus = getBudgetStatus(affaire);
  const progressStatus = getProgressStatus(affaire);

  // Vérifier les délais
  if (isLate(affaire)) {
    insights.push({
      id: 'late',
      type: 'warning',
      title: 'Échéance dépassée',
      description: `L'affaire a ${Math.abs(daysRemaining!)} jours de retard. Revoyez la planification.`,
    });
  } else if (daysRemaining !== null && daysRemaining <= 7 && daysRemaining >= 0) {
    insights.push({
      id: 'deadline-soon',
      type: 'suggestion',
      title: 'Échéance proche',
      description: `L'échéance est dans ${daysRemaining} jour(s). Assurez-vous de terminer à temps.`,
    });
  } else if (daysRemaining !== null && daysRemaining > 7) {
    insights.push({
      id: 'deadline-ok',
      type: 'success',
      title: 'Délais respectés',
      description: `${daysRemaining} jours restants avant l'échéance.`,
    });
  }

  // Vérifier le budget
  if (budgetStatus === 'danger') {
    insights.push({
      id: 'budget-over',
      type: 'warning',
      title: 'Budget dépassé',
      description: `Le budget est dépassé de ${formatCurrency(Math.abs(affaire.budget_remaining || 0))}.`,
    });
  } else if (budgetStatus === 'warning') {
    insights.push({
      id: 'budget-warning',
      type: 'warning',
      title: 'Budget presque épuisé',
      description: `Plus de 90% du budget consommé. Reste ${formatCurrency(affaire.budget_remaining || 0)}.`,
    });
  } else if (affaire.budget_total && affaire.budget_total > 0) {
    insights.push({
      id: 'budget-ok',
      type: 'success',
      title: 'Budget maîtrisé',
      description: `${formatPercent((affaire.budget_spent || 0) / affaire.budget_total * 100)} du budget utilisé.`,
    });
  }

  // Vérifier la progression
  if (progressStatus === 'danger' && affaire.status === 'EN_COURS') {
    insights.push({
      id: 'progress-behind',
      type: 'warning',
      title: 'Retard de progression',
      description: `L'avancement (${formatPercent(affaire.progress)}) est en retard par rapport au planning.`,
    });
  } else if (affaire.progress >= 100 && affaire.status === 'EN_COURS') {
    insights.push({
      id: 'progress-complete',
      type: 'suggestion',
      title: 'Prêt à clôturer',
      description: `L'avancement est à 100%. L'affaire peut être clôturée.`,
    });
  } else if (affaire.status === 'TERMINE') {
    insights.push({
      id: 'completed',
      type: 'success',
      title: 'Affaire terminée',
      description: `L'affaire a été clôturée avec succès.`,
    });
  }

  // Vérifier la facturation
  if (affaire.status === 'TERMINE') {
    const invoicedPct = (affaire.total_invoiced || 0) / Math.max(affaire.budget_total || 1, 1) * 100;
    if (invoicedPct < 100) {
      insights.push({
        id: 'invoice-pending',
        type: 'suggestion',
        title: 'Facturation incomplète',
        description: `${formatCurrency((affaire.budget_total || 0) - (affaire.total_invoiced || 0))} restent à facturer.`,
      });
    } else {
      insights.push({
        id: 'invoice-complete',
        type: 'success',
        title: 'Facturation complète',
        description: `L'intégralité du budget a été facturée.`,
      });
    }
  }

  // Vérifier les encaissements
  if ((affaire.total_invoiced || 0) > 0 && (affaire.total_paid || 0) < (affaire.total_invoiced || 0)) {
    const unpaid = (affaire.total_invoiced || 0) - (affaire.total_paid || 0);
    insights.push({
      id: 'payment-pending',
      type: 'suggestion',
      title: 'Paiements en attente',
      description: `${formatCurrency(unpaid)} restent à encaisser.`,
    });
  }

  // Équipe
  if (affaire.team_members && affaire.team_members.length > 0) {
    insights.push({
      id: 'team-assigned',
      type: 'success',
      title: 'Équipe constituée',
      description: `${affaire.team_members.length} membre(s) assigné(s) au projet.`,
    });
  } else if (affaire.status === 'EN_COURS') {
    insights.push({
      id: 'team-missing',
      type: 'suggestion',
      title: 'Équipe non définie',
      description: 'Assignez des membres à cette affaire pour un meilleur suivi.',
    });
  }

  return insights;
}

export default AffaireIATab;
