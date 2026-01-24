/**
 * AZALSCORE Module - AFFAIRES - IA Tab
 * Onglet Assistant IA pour l'affaire
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Target, Calendar, Euro, Clock
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Affaire } from '../types';
import {
  formatCurrency, formatDate, formatPercent,
  isLate, getDaysRemaining, getBudgetStatus, getProgressStatus
} from '../types';

/**
 * AffaireIATab - Assistant IA pour l'affaire
 * Fournit des insights, suggestions et analyses automatiques
 */
export const AffaireIATab: React.FC<TabContentProps<Affaire>> = ({ data: affaire }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights basés sur les données de l'affaire
  const insights = generateInsights(affaire);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA proéminent (mode AZALSCORE) */}
      <div className="azals-std-ia-panel azals-std-azalscore-only">
        <div className="azals-std-ia-panel__header">
          <Sparkles size={24} className="azals-std-ia-panel__icon" />
          <h3 className="azals-std-ia-panel__title">Assistant AZALSCORE IA</h3>
        </div>
        <div className="azals-std-ia-panel__content">
          <p>
            J'ai analysé cette affaire et identifié{' '}
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

      {/* Score de santé projet */}
      <Card title="Score de santé projet" icon={<Target size={18} />} className="mb-4">
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
        {/* Alertes et suggestions */}
        <Card title="Insights IA" icon={<Lightbulb size={18} />}>
          <div className="azals-insights-list">
            {insights.map((insight) => (
              <InsightItem key={insight.id} insight={insight} />
            ))}
          </div>
        </Card>

        {/* Actions suggérées */}
        <Card title="Actions suggérées" icon={<ChevronRight size={18} />}>
          <div className="azals-suggested-actions">
            {affaire.status === 'PLANIFIE' && (
              <SuggestedAction
                title="Démarrer l'affaire"
                description="L'affaire est planifiée et peut être démarrée."
                confidence={85}
                icon={<ChevronRight size={16} />}
              />
            )}
            {affaire.status === 'EN_COURS' && affaire.progress >= 100 && (
              <SuggestedAction
                title="Clôturer l'affaire"
                description="L'avancement est à 100%. Vous pouvez clôturer l'affaire."
                confidence={95}
                icon={<Target size={16} />}
              />
            )}
            {affaire.status === 'TERMINE' && (affaire.total_invoiced || 0) < (affaire.budget_total || 0) && (
              <SuggestedAction
                title="Facturer l'affaire"
                description={`Il reste ${formatCurrency((affaire.budget_total || 0) - (affaire.total_invoiced || 0))} à facturer.`}
                confidence={90}
                icon={<Euro size={16} />}
              />
            )}
            {isLate(affaire) && (
              <SuggestedAction
                title="Mettre à jour la planification"
                description="L'échéance est dépassée. Révisez la date de fin."
                confidence={85}
                icon={<Calendar size={16} />}
              />
            )}
            {getBudgetStatus(affaire) !== 'ok' && (
              <SuggestedAction
                title="Revoir le budget"
                description="Le budget est sous pression. Analysez les coûts."
                confidence={80}
                icon={<AlertTriangle size={16} />}
              />
            )}
          </div>
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
 * Composant action suggérée
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
