/**
 * AZALSCORE Module - Qualite - NC IA Tab
 * Onglet Assistant IA pour la non-conformite
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  TrendingUp, AlertTriangle, Search, CheckCircle, Shield, Clock, ThumbsUp
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { NonConformance } from '../types';
import {
  SEVERITY_CONFIG, NC_STATUS_CONFIG,
  getNCAge, getNCAgeDays, isNCOverdue, canCloseNC
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
 * NCIATab - Assistant IA
 */
export const NCIATab: React.FC<TabContentProps<NonConformance>> = ({ data: nc }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(nc);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(nc);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const resolutionScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cette non-conformité et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de résolution - Composant partagé */}
      <Card title="Probabilité de résolution" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={resolutionScore}
          label="Résolution"
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur la NC
 */
function generateSuggestedActions(nc: NonConformance): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isNCOverdue(nc)) {
    actions.push({
      id: 'overdue',
      title: 'Objectif dépassé',
      description: 'Revoir la date objectif ou accélérer le traitement.',
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Replanifier',
    });
  }

  if (!nc.root_cause && nc.status !== 'CLOSED') {
    actions.push({
      id: 'root-cause',
      title: 'Identifier la cause racine',
      description: 'Utiliser la méthode des 5 pourquoi.',
      confidence: 95,
      icon: <Search size={16} />,
      actionLabel: 'Analyser',
    });
  }

  if (nc.root_cause && !nc.corrective_action) {
    actions.push({
      id: 'corrective',
      title: "Définir l'action corrective",
      description: 'Action pour corriger le problème.',
      confidence: 90,
      icon: <CheckCircle size={16} />,
      actionLabel: 'Définir',
    });
  }

  if (nc.corrective_action && !nc.preventive_action) {
    actions.push({
      id: 'preventive',
      title: 'Ajouter action préventive',
      description: 'Éviter la récurrence du problème.',
      confidence: 85,
      icon: <Shield size={16} />,
      actionLabel: 'Ajouter',
    });
  }

  if (canCloseNC(nc)) {
    actions.push({
      id: 'close',
      title: 'Clôturer la NC',
      description: 'Toutes les conditions sont remplies.',
      confidence: 80,
      icon: <CheckCircle size={16} />,
      actionLabel: 'Clôturer',
    });
  }

  if (getNCAgeDays(nc) > 30 && nc.status !== 'CLOSED') {
    actions.push({
      id: 'old',
      title: 'NC ancienne',
      description: 'Cette NC a plus de 30 jours.',
      confidence: 75,
      icon: <Clock size={16} />,
      actionLabel: 'Escalader',
    });
  }

  if (nc.status === 'CLOSED') {
    actions.push({
      id: 'closed',
      title: 'NC résolue',
      description: 'Le problème a été traité avec succès.',
      confidence: 100,
      icon: <ThumbsUp size={16} />,
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur la NC
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
