/**
 * AZALSCORE Module - Projects - Project IA Tab
 * Onglet Assistant IA pour le projet
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, Calendar, Target, Euro, Users, CheckSquare } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Project } from '../types';
import { formatCurrency, formatPercent, formatHours } from '@/utils/formatters';
import {
  PROJECT_STATUS_CONFIG,
  isProjectOverdue, isProjectNearDeadline, isBudgetOverrun,
  getDaysRemaining, getRemainingBudget, getBudgetUsedPercent,
  getTaskCountByStatus, getOverdueTasks, getTotalLoggedHours,
  getTotalEstimatedHours, getMilestoneStats, getNextMilestone
} from '../types';

// Composants partagés IA (AZA-NF-REUSE)
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';

/**
 * ProjectIATab - Assistant IA pour le projet
 */
export const ProjectIATab: React.FC<TabContentProps<Project>> = ({ data: project }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(project);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(project);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const healthScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce projet et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score santé projet - Composant partagé */}
      <Card title="Santé du projet" icon={<TrendingUp size={18} />} className="mb-4">
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
            <h4>Statut</h4>
            <p className={`text-lg font-medium text-${PROJECT_STATUS_CONFIG[project.status].color}`}>
              {PROJECT_STATUS_CONFIG[project.status].label}
            </p>
            <p className="text-sm text-muted">
              {PROJECT_STATUS_CONFIG[project.status].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Budget</h4>
            <p className={`text-lg font-medium ${isBudgetOverrun(project) ? 'text-danger' : 'text-success'}`}>
              {formatPercent(getBudgetUsedPercent(project))} utilisé
            </p>
            <p className="text-sm text-muted">
              Reste: {formatCurrency(getRemainingBudget(project) || 0, project.currency)}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Temps</h4>
            <p className="text-lg font-medium text-primary">
              {formatHours(getTotalLoggedHours(project))}
            </p>
            <p className="text-sm text-muted">
              Estimé: {formatHours(getTotalEstimatedHours(project))}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Tâches</h4>
            <p className="text-lg font-medium">
              {getTaskCountByStatus(project).DONE} / {(project.tasks || []).length}
            </p>
            <p className="text-sm text-muted">
              {getTaskCountByStatus(project).IN_PROGRESS} en cours
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
 * Générer les actions suggérées basées sur le projet
 */
function generateSuggestedActions(project: Project): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isProjectOverdue(project)) {
    actions.push({
      id: 'review-planning',
      title: 'Revoir le planning',
      description: "Le projet est en retard sur l'échéance prévue.",
      confidence: 95,
      icon: <Calendar size={16} />,
      actionLabel: 'Modifier',
    });
  }

  if (isBudgetOverrun(project)) {
    actions.push({
      id: 'control-expenses',
      title: 'Contrôler les dépenses',
      description: 'Le budget est dépassé.',
      confidence: 90,
      icon: <Euro size={16} />,
      actionLabel: 'Analyser',
    });
  }

  if (getOverdueTasks(project).length > 0) {
    actions.push({
      id: 'handle-overdue-tasks',
      title: 'Traiter les tâches en retard',
      description: `${getOverdueTasks(project).length} tâche(s) en retard.`,
      confidence: 85,
      icon: <CheckSquare size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (getNextMilestone(project)) {
    actions.push({
      id: 'prepare-milestone',
      title: 'Préparer le prochain jalon',
      description: `Jalon "${getNextMilestone(project)!.name}" à venir.`,
      confidence: 80,
      icon: <Target size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (!project.team_members || project.team_members.length === 0) {
    actions.push({
      id: 'build-team',
      title: "Constituer l'équipe",
      description: 'Aucun membre assigné au projet.',
      confidence: 75,
      icon: <Users size={16} />,
      actionLabel: 'Ajouter',
    });
  }

  if (project.progress < 100 && project.status === 'ACTIVE') {
    actions.push({
      id: 'track-progress',
      title: "Suivre l'avancement",
      description: `Progression actuelle: ${formatPercent(project.progress)}`,
      confidence: 70,
      icon: <TrendingUp size={16} />,
      actionLabel: 'Voir',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le projet
 */
function generateInsights(project: Project): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (project.status === 'ACTIVE') {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Projet actif',
      description: 'Le projet est en cours de réalisation.',
    });
  } else if (project.status === 'COMPLETED') {
    insights.push({
      id: 'completed',
      type: 'success',
      title: 'Projet terminé',
      description: 'Le projet a été mené à bien.',
    });
  } else if (project.status === 'PAUSED') {
    insights.push({
      id: 'paused',
      type: 'warning',
      title: 'Projet en pause',
      description: 'Le projet est actuellement suspendu.',
    });
  }

  // Échéance
  if (isProjectOverdue(project)) {
    const daysLate = Math.abs(getDaysRemaining(project) || 0);
    insights.push({
      id: 'overdue',
      type: 'warning',
      title: 'Projet en retard',
      description: `${daysLate} jour(s) de retard sur l'échéance.`,
    });
  } else if (isProjectNearDeadline(project)) {
    insights.push({
      id: 'near-deadline',
      type: 'warning',
      title: 'Échéance proche',
      description: `${getDaysRemaining(project)} jours restants avant l'échéance.`,
    });
  } else if (getDaysRemaining(project) !== null && getDaysRemaining(project)! > 30) {
    insights.push({
      id: 'on-track',
      type: 'success',
      title: 'Planning respecté',
      description: 'Le projet est dans les temps.',
    });
  }

  // Budget
  const budgetPercent = getBudgetUsedPercent(project);
  if (isBudgetOverrun(project)) {
    insights.push({
      id: 'budget-overrun',
      type: 'warning',
      title: 'Budget dépassé',
      description: `${formatPercent(budgetPercent)} du budget utilisé.`,
    });
  } else if (budgetPercent > 80 && budgetPercent <= 100) {
    insights.push({
      id: 'budget-high',
      type: 'warning',
      title: 'Budget presque épuisé',
      description: `${formatPercent(100 - budgetPercent)} de marge restante.`,
    });
  } else if (project.budget && budgetPercent <= 80) {
    insights.push({
      id: 'budget-ok',
      type: 'success',
      title: 'Budget maîtrisé',
      description: `${formatPercent(100 - budgetPercent)} du budget encore disponible.`,
    });
  }

  // Tâches
  const taskCounts = getTaskCountByStatus(project);
  const totalTasks = (project.tasks || []).length;
  const overdueTasks = getOverdueTasks(project);

  if (overdueTasks.length > 0) {
    insights.push({
      id: 'overdue-tasks',
      type: 'warning',
      title: 'Tâches en retard',
      description: `${overdueTasks.length} tâche(s) dépassent leur échéance.`,
    });
  }

  if (totalTasks > 0 && taskCounts.DONE === totalTasks) {
    insights.push({
      id: 'all-tasks-done',
      type: 'success',
      title: 'Toutes tâches terminées',
      description: 'Toutes les tâches du projet sont complétées.',
    });
  } else if (totalTasks > 0 && taskCounts.DONE / totalTasks > 0.75) {
    insights.push({
      id: 'tasks-progress',
      type: 'success',
      title: 'Bonne progression',
      description: `${Math.round((taskCounts.DONE / totalTasks) * 100)}% des tâches complétées.`,
    });
  }

  // Jalons
  const milestoneStats = getMilestoneStats(project);
  if (milestoneStats.overdue > 0) {
    insights.push({
      id: 'overdue-milestones',
      type: 'warning',
      title: 'Jalons en retard',
      description: `${milestoneStats.overdue} jalon(s) non atteint(s).`,
    });
  }

  // Équipe
  if (!project.team_members || project.team_members.length === 0) {
    insights.push({
      id: 'no-team',
      type: 'suggestion',
      title: 'Équipe non constituée',
      description: 'Aucun membre assigné au projet.',
    });
  }

  // Temps
  const loggedHours = getTotalLoggedHours(project);
  const estimatedHours = getTotalEstimatedHours(project);
  if (estimatedHours > 0 && loggedHours > estimatedHours * 1.2) {
    insights.push({
      id: 'time-overrun',
      type: 'warning',
      title: 'Dépassement de temps',
      description: `${formatHours(loggedHours - estimatedHours)} de plus que prévu.`,
    });
  }

  // Description
  if (!project.description) {
    insights.push({
      id: 'no-description',
      type: 'suggestion',
      title: 'Description manquante',
      description: 'Ajouter une description pour clarifier les objectifs.',
    });
  }

  return insights;
}

export default ProjectIATab;
