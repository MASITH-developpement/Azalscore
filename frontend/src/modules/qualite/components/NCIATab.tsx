/**
 * AZALSCORE Module - Qualite - NC IA Tab
 * Onglet Assistant IA pour la non-conformite
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ThumbsDown, ChevronRight,
  Search, CheckCircle, Shield, Clock
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { NonConformance } from '../types';
import {
  SEVERITY_CONFIG, NC_STATUS_CONFIG,
  getNCAge, getNCAgeDays, isNCOverdue, canCloseNC
} from '../types';

/**
 * NCIATab - Assistant IA
 */
export const NCIATab: React.FC<TabContentProps<NonConformance>> = ({ data: nc }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Generer les insights
  const insights = generateInsights(nc);

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
            J'ai analyse cette non-conformite et identifie{' '}
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
          <Button variant="ghost" leftIcon={<Search size={16} />}>
            Suggerer cause racine
          </Button>
        </div>
      </div>

      {/* Score de resolution */}
      <Card title="Probabilite de resolution" icon={<TrendingUp size={18} />} className="mb-4">
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
            {isNCOverdue(nc) && (
              <SuggestedAction
                title="Objectif depasse"
                description="Revoir la date objectif ou accelerer le traitement."
                confidence={100}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {!nc.root_cause && nc.status !== 'CLOSED' && (
              <SuggestedAction
                title="Identifier la cause racine"
                description="Utiliser la methode des 5 pourquoi."
                confidence={95}
                icon={<Search size={16} />}
              />
            )}
            {nc.root_cause && !nc.corrective_action && (
              <SuggestedAction
                title="Definir l'action corrective"
                description="Action pour corriger le probleme."
                confidence={90}
                icon={<CheckCircle size={16} />}
              />
            )}
            {nc.corrective_action && !nc.preventive_action && (
              <SuggestedAction
                title="Ajouter action preventive"
                description="Eviter la recurrence du probleme."
                confidence={85}
                icon={<Shield size={16} />}
              />
            )}
            {canCloseNC(nc) && (
              <SuggestedAction
                title="Cloturer la NC"
                description="Toutes les conditions sont remplies."
                confidence={80}
                icon={<CheckCircle size={16} />}
              />
            )}
            {getNCAgeDays(nc) > 30 && nc.status !== 'CLOSED' && (
              <SuggestedAction
                title="NC ancienne"
                description="Cette NC a plus de 30 jours."
                confidence={75}
                icon={<Clock size={16} />}
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
            <p className={`text-lg font-medium text-${NC_STATUS_CONFIG[nc.status].color}`}>
              {NC_STATUS_CONFIG[nc.status].label}
            </p>
            <p className="text-sm text-muted">
              {NC_STATUS_CONFIG[nc.status].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Gravite</h4>
            <p className={`text-lg font-medium text-${SEVERITY_CONFIG[nc.severity].color}`}>
              {SEVERITY_CONFIG[nc.severity].label}
            </p>
            <p className="text-sm text-muted">
              {SEVERITY_CONFIG[nc.severity].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Age</h4>
            <p className="text-lg font-medium text-primary">
              {getNCAge(nc)}
            </p>
            <p className="text-sm text-muted">
              Depuis la detection
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Completion</h4>
            <p className="text-lg font-medium">
              {[nc.root_cause, nc.corrective_action, nc.preventive_action].filter(Boolean).length}/3
            </p>
            <p className="text-sm text-muted">
              Etapes d'analyse
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
 * Generer les insights bases sur la NC
 */
function generateInsights(nc: NonConformance): Insight[] {
  const insights: Insight[] = [];

  // Objectif
  if (isNCOverdue(nc)) {
    insights.push({
      id: 'overdue',
      type: 'warning',
      title: 'Objectif depasse',
      description: 'La date objectif est depassee.',
    });
  } else if (nc.target_date) {
    insights.push({
      id: 'on-track',
      type: 'success',
      title: 'Dans les delais',
      description: 'L\'objectif n\'est pas encore depasse.',
    });
  }

  // Statut
  if (nc.status === 'CLOSED') {
    insights.push({
      id: 'closed',
      type: 'success',
      title: 'NC cloturee',
      description: 'Le probleme a ete resolu.',
    });
  } else if (nc.status === 'ACTION_PLANNED') {
    insights.push({
      id: 'action-planned',
      type: 'success',
      title: 'Action definie',
      description: 'Action corrective planifiee.',
    });
  } else if (nc.status === 'IN_ANALYSIS') {
    insights.push({
      id: 'in-analysis',
      type: 'suggestion',
      title: 'En analyse',
      description: 'Analyse en cours.',
    });
  } else if (nc.status === 'OPEN') {
    insights.push({
      id: 'open',
      type: 'warning',
      title: 'NC ouverte',
      description: 'Necessite une prise en charge.',
    });
  }

  // Cause racine
  if (nc.root_cause) {
    insights.push({
      id: 'root-cause',
      type: 'success',
      title: 'Cause identifiee',
      description: 'La cause racine a ete determinee.',
    });
  } else if (nc.status !== 'CLOSED') {
    insights.push({
      id: 'no-root-cause',
      type: 'warning',
      title: 'Cause non identifiee',
      description: 'La cause racine n\'est pas encore connue.',
    });
  }

  // Actions
  if (nc.corrective_action) {
    insights.push({
      id: 'corrective',
      type: 'success',
      title: 'Action corrective',
      description: 'Action corrective definie.',
    });
  }

  if (nc.preventive_action) {
    insights.push({
      id: 'preventive',
      type: 'success',
      title: 'Action preventive',
      description: 'Mesures de prevention en place.',
    });
  } else if (nc.corrective_action && nc.status !== 'CLOSED') {
    insights.push({
      id: 'no-preventive',
      type: 'suggestion',
      title: 'Action preventive',
      description: 'Envisager une action preventive.',
    });
  }

  // Gravite
  if (nc.severity === 'CRITICAL') {
    insights.push({
      id: 'critical',
      type: 'warning',
      title: 'Gravite critique',
      description: 'Necessite une attention immediate.',
    });
  }

  // Age
  const ageDays = getNCAgeDays(nc);
  if (ageDays > 30 && nc.status !== 'CLOSED') {
    insights.push({
      id: 'old',
      type: 'warning',
      title: 'NC ancienne',
      description: `Cette NC a ${ageDays} jours.`,
    });
  }

  return insights;
}

export default NCIATab;
