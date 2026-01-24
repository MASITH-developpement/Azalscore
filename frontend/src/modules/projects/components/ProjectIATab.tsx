/**
 * AZALSCORE Module - Projects - Project IA Tab
 * Onglet Assistant IA pour le projet
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Calendar, Target, Clock, Euro,
  Users, CheckSquare
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Project } from '../types';
import {
  formatDate, formatCurrency, formatPercent, formatHours,
  PROJECT_STATUS_CONFIG,
  isProjectOverdue, isProjectNearDeadline, isBudgetOverrun,
  getDaysRemaining, getRemainingBudget, getBudgetUsedPercent,
  getTaskCountByStatus, getOverdueTasks, getTotalLoggedHours,
  getTotalEstimatedHours, getMilestoneStats, getNextMilestone
} from '../types';

/**
 * ProjectIATab - Assistant IA pour le projet
 */
export const ProjectIATab: React.FC<TabContentProps<Project>> = ({ data: project }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Generer les insights
  const insights = generateInsights(project);

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
            J'ai analyse ce projet et identifie{' '}
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

      {/* Score sante projet */}
      <Card title="Sante du projet" icon={<TrendingUp size={18} />} className="mb-4">
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
            {isProjectOverdue(project) && (
              <SuggestedAction
                title="Revoir le planning"
                description="Le projet est en retard sur l'echeance prevue."
                confidence={95}
                icon={<Calendar size={16} />}
              />
            )}
            {isBudgetOverrun(project) && (
              <SuggestedAction
                title="Controler les depenses"
                description="Le budget est depasse."
                confidence={90}
                icon={<Euro size={16} />}
              />
            )}
            {getOverdueTasks(project).length > 0 && (
              <SuggestedAction
                title="Traiter les taches en retard"
                description={`${getOverdueTasks(project).length} tache(s) en retard.`}
                confidence={85}
                icon={<CheckSquare size={16} />}
              />
            )}
            {getNextMilestone(project) && (
              <SuggestedAction
                title="Preparer le prochain jalon"
                description={`Jalon "${getNextMilestone(project)!.name}" a venir.`}
                confidence={80}
                icon={<Target size={16} />}
              />
            )}
            {(!project.team_members || project.team_members.length === 0) && (
              <SuggestedAction
                title="Constituer l'equipe"
                description="Aucun membre assigne au projet."
                confidence={75}
                icon={<Users size={16} />}
              />
            )}
            {project.progress < 100 && project.status === 'ACTIVE' && (
              <SuggestedAction
                title="Suivre l'avancement"
                description={`Progression actuelle: ${formatPercent(project.progress)}`}
                confidence={70}
                icon={<TrendingUp size={16} />}
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
              {formatPercent(getBudgetUsedPercent(project))} utilise
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
              Estime: {formatHours(getTotalEstimatedHours(project))}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Taches</h4>
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
 * Generer les insights bases sur le projet
 */
function generateInsights(project: Project): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (project.status === 'ACTIVE') {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Projet actif',
      description: 'Le projet est en cours de realisation.',
    });
  } else if (project.status === 'COMPLETED') {
    insights.push({
      id: 'completed',
      type: 'success',
      title: 'Projet termine',
      description: 'Le projet a ete mene a bien.',
    });
  } else if (project.status === 'PAUSED') {
    insights.push({
      id: 'paused',
      type: 'warning',
      title: 'Projet en pause',
      description: 'Le projet est actuellement suspendu.',
    });
  }

  // Echeance
  if (isProjectOverdue(project)) {
    const daysLate = Math.abs(getDaysRemaining(project) || 0);
    insights.push({
      id: 'overdue',
      type: 'warning',
      title: 'Projet en retard',
      description: `${daysLate} jour(s) de retard sur l'echeance.`,
    });
  } else if (isProjectNearDeadline(project)) {
    insights.push({
      id: 'near-deadline',
      type: 'warning',
      title: 'Echeance proche',
      description: `${getDaysRemaining(project)} jours restants avant l'echeance.`,
    });
  } else if (getDaysRemaining(project) !== null && getDaysRemaining(project)! > 30) {
    insights.push({
      id: 'on-track',
      type: 'success',
      title: 'Planning respecte',
      description: 'Le projet est dans les temps.',
    });
  }

  // Budget
  const budgetPercent = getBudgetUsedPercent(project);
  if (isBudgetOverrun(project)) {
    insights.push({
      id: 'budget-overrun',
      type: 'warning',
      title: 'Budget depasse',
      description: `${formatPercent(budgetPercent)} du budget utilise.`,
    });
  } else if (budgetPercent > 80 && budgetPercent <= 100) {
    insights.push({
      id: 'budget-high',
      type: 'warning',
      title: 'Budget presque epuise',
      description: `${formatPercent(100 - budgetPercent)} de marge restante.`,
    });
  } else if (project.budget && budgetPercent <= 80) {
    insights.push({
      id: 'budget-ok',
      type: 'success',
      title: 'Budget maitrise',
      description: `${formatPercent(100 - budgetPercent)} du budget encore disponible.`,
    });
  }

  // Taches
  const taskCounts = getTaskCountByStatus(project);
  const totalTasks = (project.tasks || []).length;
  const overdueTasks = getOverdueTasks(project);

  if (overdueTasks.length > 0) {
    insights.push({
      id: 'overdue-tasks',
      type: 'warning',
      title: 'Taches en retard',
      description: `${overdueTasks.length} tache(s) depassent leur echeance.`,
    });
  }

  if (totalTasks > 0 && taskCounts.DONE === totalTasks) {
    insights.push({
      id: 'all-tasks-done',
      type: 'success',
      title: 'Toutes taches terminees',
      description: 'Toutes les taches du projet sont completees.',
    });
  } else if (totalTasks > 0 && taskCounts.DONE / totalTasks > 0.75) {
    insights.push({
      id: 'tasks-progress',
      type: 'success',
      title: 'Bonne progression',
      description: `${Math.round((taskCounts.DONE / totalTasks) * 100)}% des taches completees.`,
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

  // Equipe
  if (!project.team_members || project.team_members.length === 0) {
    insights.push({
      id: 'no-team',
      type: 'suggestion',
      title: 'Equipe non constituee',
      description: 'Aucun membre assigne au projet.',
    });
  }

  // Temps
  const loggedHours = getTotalLoggedHours(project);
  const estimatedHours = getTotalEstimatedHours(project);
  if (estimatedHours > 0 && loggedHours > estimatedHours * 1.2) {
    insights.push({
      id: 'time-overrun',
      type: 'warning',
      title: 'Depassement de temps',
      description: `${formatHours(loggedHours - estimatedHours)} de plus que prevu.`,
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
