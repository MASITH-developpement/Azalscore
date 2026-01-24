/**
 * AZALSCORE Module - Compliance - Audit IA Tab
 * Onglet Assistant IA pour l'audit
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ChevronRight, Play, CheckCircle2,
  FileText, AlertCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Audit } from '../types';
import {
  formatPercent, hasCriticalFindings, hasOpenFindings,
  isAuditCompleted, isAuditInProgress, isAuditPlanned,
  getNextAuditStatus, AUDIT_STATUS_CONFIG
} from '../types';

/**
 * AuditIATab - Assistant IA
 */
export const AuditIATab: React.FC<TabContentProps<Audit>> = ({ data: audit }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(audit);

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
            J'ai analyse cet audit et identifie{' '}
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

      {/* Score de l'audit */}
      <Card title="Score de conformite" icon={<TrendingUp size={18} />} className="mb-4">
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
                strokeDasharray={`${audit.score || 0}, 100`}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke={audit.score && audit.score >= 80 ? 'var(--azals-success-500)' : audit.score && audit.score >= 60 ? 'var(--azals-warning-500)' : 'var(--azals-danger-500)'}
                strokeWidth="3"
                strokeLinecap="round"
              />
            </svg>
            <span className="azals-score-display__value">
              {audit.score !== undefined ? formatPercent(audit.score) : '-'}
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
            {isAuditPlanned(audit) && (
              <SuggestedAction
                title="Demarrer l'audit"
                description="L'audit est planifie et peut etre lance."
                confidence={90}
                icon={<Play size={16} />}
              />
            )}
            {isAuditInProgress(audit) && !audit.report_url && (
              <SuggestedAction
                title="Generer le rapport"
                description="L'audit est termine, generez le rapport."
                confidence={85}
                icon={<FileText size={16} />}
              />
            )}
            {isAuditInProgress(audit) && audit.report_url && (
              <SuggestedAction
                title="Cloturer l'audit"
                description="Le rapport est disponible, cloturez l'audit."
                confidence={95}
                icon={<CheckCircle2 size={16} />}
              />
            )}
            {hasCriticalFindings(audit) && (
              <SuggestedAction
                title="Traiter les constats critiques"
                description={`${audit.critical_findings} constat(s) critique(s) a traiter.`}
                confidence={100}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {hasOpenFindings(audit) && !hasCriticalFindings(audit) && (
              <SuggestedAction
                title="Traiter les constats"
                description="Des constats sont en attente de traitement."
                confidence={80}
                icon={<AlertCircle size={16} />}
              />
            )}
            {isAuditCompleted(audit) && !hasOpenFindings(audit) && (
              <SuggestedAction
                title="Audit conforme"
                description="Tous les constats ont ete traites."
                confidence={100}
                icon={<ThumbsUp size={16} />}
              />
            )}
            {audit.action_plan_status === 'IN_PROGRESS' && (
              <SuggestedAction
                title="Suivre le plan d'action"
                description={`Progression: ${formatPercent(audit.action_plan_progress || 0)}`}
                confidence={75}
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
            <h4>Plan d'action</h4>
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
 * Generer les insights bases sur l'audit
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
