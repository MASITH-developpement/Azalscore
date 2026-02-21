/**
 * AZALSCORE Module - Compliance - Audit IA Tab
 * Onglet Assistant IA pour l'audit
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  TrendingUp, AlertTriangle, ThumbsUp, Play, CheckCircle2,
  FileText, AlertCircle
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
import { formatPercent } from '@/utils/formatters';
import {
  hasCriticalFindings, hasOpenFindings,
  isAuditCompleted, isAuditInProgress, isAuditPlanned
} from '../types';
import type { Audit } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * AuditIATab - Assistant IA
 */
export const AuditIATab: React.FC<TabContentProps<Audit>> = ({ data: audit }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(audit);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(audit);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const conformityScore = audit.score ?? Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cet audit et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de conformité - Composant partagé */}
      <Card title="Score de conformité" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={conformityScore}
          label="Conformité"
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
            <h4>Score</h4>
            <p className={`text-lg font-medium ${audit.score && audit.score >= 80 ? 'text-green-600' : audit.score && audit.score >= 60 ? 'text-orange-600' : 'text-red-600'}`}>
              {audit.score !== undefined ? formatPercent(audit.score) : '-'}
            </p>
            <p className="text-sm text-muted">conformite</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Constats</h4>
            <p className="text-lg font-medium text-primary">{audit.findings_count}</p>
            <p className="text-sm text-muted">identifies</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Critiques</h4>
            <p className={`text-lg font-medium ${audit.critical_findings > 0 ? 'text-red-600' : 'text-green-600'}`}>
              {audit.critical_findings}
            </p>
            <p className="text-sm text-muted">constat(s)</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Plan d&apos;action</h4>
            <p className="text-lg font-medium text-blue-600">
              {formatPercent(audit.action_plan_progress || 0)}
            </p>
            <p className="text-sm text-muted">progression</p>
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
 * Générer les actions suggérées basées sur l'audit
 */
function generateSuggestedActions(audit: Audit): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isAuditPlanned(audit)) {
    actions.push({
      id: 'start',
      title: "Démarrer l'audit",
      description: "L'audit est planifié et peut être lancé.",
      confidence: 90,
      icon: <Play size={16} />,
      actionLabel: 'Démarrer',
    });
  }

  if (isAuditInProgress(audit) && !audit.report_url) {
    actions.push({
      id: 'report',
      title: 'Générer le rapport',
      description: "L'audit est terminé, générez le rapport.",
      confidence: 85,
      icon: <FileText size={16} />,
      actionLabel: 'Générer',
    });
  }

  if (isAuditInProgress(audit) && audit.report_url) {
    actions.push({
      id: 'close',
      title: "Clôturer l'audit",
      description: "Le rapport est disponible, clôturez l'audit.",
      confidence: 95,
      icon: <CheckCircle2 size={16} />,
      actionLabel: 'Clôturer',
    });
  }

  if (hasCriticalFindings(audit)) {
    actions.push({
      id: 'critical',
      title: 'Traiter les constats critiques',
      description: `${audit.critical_findings} constat(s) critique(s) à traiter.`,
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Traiter',
    });
  }

  if (hasOpenFindings(audit) && !hasCriticalFindings(audit)) {
    actions.push({
      id: 'findings',
      title: 'Traiter les constats',
      description: 'Des constats sont en attente de traitement.',
      confidence: 80,
      icon: <AlertCircle size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (isAuditCompleted(audit) && !hasOpenFindings(audit)) {
    actions.push({
      id: 'ok',
      title: 'Audit conforme',
      description: 'Tous les constats ont été traités.',
      confidence: 100,
      icon: <ThumbsUp size={16} />,
    });
  }

  if (audit.action_plan_status === 'IN_PROGRESS') {
    actions.push({
      id: 'action-plan',
      title: "Suivre le plan d'action",
      description: `Progression: ${formatPercent(audit.action_plan_progress || 0)}`,
      confidence: 75,
      icon: <TrendingUp size={16} />,
      actionLabel: 'Suivre',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur l'audit
 */
function generateInsights(audit: Audit): Insight[] {
  const insights: Insight[] = [];

  // Statut audit
  if (isAuditCompleted(audit)) {
    insights.push({
      id: 'completed',
      type: 'success',
      title: 'Audit termine',
      description: 'L\'audit a ete realise et cloture.',
    });
  } else if (isAuditInProgress(audit)) {
    insights.push({
      id: 'in-progress',
      type: 'suggestion',
      title: 'Audit en cours',
      description: 'L\'audit est actuellement en cours de realisation.',
    });
  } else if (isAuditPlanned(audit)) {
    insights.push({
      id: 'planned',
      type: 'suggestion',
      title: 'Audit planifie',
      description: 'L\'audit est programme et en attente de demarrage.',
    });
  }

  // Score
  if (audit.score !== undefined) {
    if (audit.score >= 80) {
      insights.push({
        id: 'good-score',
        type: 'success',
        title: 'Bon score de conformite',
        description: `Score de ${formatPercent(audit.score)} - niveau satisfaisant.`,
      });
    } else if (audit.score >= 60) {
      insights.push({
        id: 'avg-score',
        type: 'suggestion',
        title: 'Score a ameliorer',
        description: `Score de ${formatPercent(audit.score)} - des ameliorations sont necessaires.`,
      });
    } else {
      insights.push({
        id: 'low-score',
        type: 'warning',
        title: 'Score insuffisant',
        description: `Score de ${formatPercent(audit.score)} - actions correctives urgentes.`,
      });
    }
  }

  // Constats critiques
  if (hasCriticalFindings(audit)) {
    insights.push({
      id: 'critical-findings',
      type: 'warning',
      title: 'Constats critiques',
      description: `${audit.critical_findings} constat(s) critique(s) identifies.`,
    });
  } else if (audit.findings_count > 0) {
    insights.push({
      id: 'has-findings',
      type: 'suggestion',
      title: 'Constats identifies',
      description: `${audit.findings_count} constat(s) sans criticite majeure.`,
    });
  } else if (isAuditCompleted(audit)) {
    insights.push({
      id: 'no-findings',
      type: 'success',
      title: 'Aucun constat',
      description: 'Aucun constat identifie lors de l\'audit.',
    });
  }

  // Rapport
  if (audit.report_url) {
    insights.push({
      id: 'has-report',
      type: 'success',
      title: 'Rapport disponible',
      description: 'Le rapport d\'audit est disponible.',
    });
  } else if (isAuditCompleted(audit) || isAuditInProgress(audit)) {
    insights.push({
      id: 'no-report',
      type: 'suggestion',
      title: 'Rapport manquant',
      description: 'Le rapport d\'audit n\'est pas encore disponible.',
    });
  }

  // Plan d'action
  if (audit.action_plan_status === 'COMPLETED') {
    insights.push({
      id: 'action-plan-done',
      type: 'success',
      title: 'Plan d\'action termine',
      description: 'Toutes les actions correctives sont terminees.',
    });
  } else if (audit.action_plan_status === 'IN_PROGRESS') {
    insights.push({
      id: 'action-plan-progress',
      type: 'suggestion',
      title: 'Plan d\'action en cours',
      description: `Progression: ${formatPercent(audit.action_plan_progress || 0)}.`,
    });
  } else if (hasOpenFindings(audit)) {
    insights.push({
      id: 'action-plan-pending',
      type: 'warning',
      title: 'Plan d\'action a definir',
      description: 'Des constats necessitent un plan d\'action.',
    });
  }

  // Auditeur
  if (audit.auditor || audit.lead_auditor) {
    insights.push({
      id: 'has-auditor',
      type: 'success',
      title: 'Auditeur assigne',
      description: `Audit realise par ${audit.auditor || audit.lead_auditor}.`,
    });
  }

  return insights;
}

export default AuditIATab;
