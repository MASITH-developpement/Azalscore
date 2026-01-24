/**
 * AZALSCORE Module - INTERVENTIONS - IA Tab
 * Onglet Assistant IA pour l'intervention
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Clock, Calendar, MapPin, FileText
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Intervention } from '../types';
import {
  formatDate, formatDuration, isLate, getDaysUntilIntervention,
  getDurationVariance, canStart, canComplete, canPlan
} from '../types';

/**
 * InterventionIATab - Assistant IA pour l'intervention
 * Fournit des insights, suggestions et analyses automatiques
 */
export const InterventionIATab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights basés sur les données de l'intervention
  const insights = generateInsights(intervention);

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
            J'ai analysé cette intervention et identifié{' '}
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

      {/* Score de préparation */}
      <Card title="Score de préparation" icon={<TrendingUp size={18} />} className="mb-4">
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
            {canPlan(intervention) && (
              <SuggestedAction
                title="Planifier l'intervention"
                description="Définissez une date et assignez un intervenant."
                confidence={90}
                icon={<Calendar size={16} />}
              />
            )}
            {canStart(intervention) && (
              <SuggestedAction
                title="Démarrer l'intervention"
                description="L'intervention est planifiée et peut être démarrée."
                confidence={85}
                icon={<ChevronRight size={16} />}
              />
            )}
            {canComplete(intervention) && (
              <SuggestedAction
                title="Terminer l'intervention"
                description="Complétez le rapport et clôturez l'intervention."
                confidence={90}
                icon={<ChevronRight size={16} />}
              />
            )}
            {intervention.statut === 'TERMINEE' && !intervention.rapport?.is_signed && (
              <SuggestedAction
                title="Faire signer le rapport"
                description="Le rapport n'a pas encore été signé par le client."
                confidence={85}
                icon={<FileText size={16} />}
              />
            )}
            {intervention.statut === 'TERMINEE' && !intervention.facture_id && intervention.facturable !== false && (
              <SuggestedAction
                title="Facturer l'intervention"
                description="L'intervention est terminée et peut être facturée."
                confidence={95}
                icon={<FileText size={16} />}
              />
            )}
            {isLate(intervention) && (
              <SuggestedAction
                title="Replanifier"
                description="L'intervention est en retard. Définissez une nouvelle date."
                confidence={85}
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
            <h4>Planning</h4>
            <p className={`text-lg font-medium ${isLate(intervention) ? 'text-danger' : 'text-success'}`}>
              {isLate(intervention) ? 'En retard' : intervention.date_prevue ? 'Planifiée' : 'Non planifiée'}
            </p>
            <p className="text-sm text-muted">
              {intervention.date_prevue ? formatDate(intervention.date_prevue) : 'Date non définie'}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Intervenant</h4>
            <p className={`text-lg font-medium ${intervention.intervenant_name ? 'text-success' : 'text-warning'}`}>
              {intervention.intervenant_name ? 'Assigné' : 'Non assigné'}
            </p>
            <p className="text-sm text-muted">{intervention.intervenant_name || 'À définir'}</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Durée</h4>
            <p className="text-lg font-medium">
              {formatDuration(intervention.duree_reelle_minutes || intervention.duree_prevue_minutes)}
            </p>
            <p className="text-sm text-muted">
              {intervention.duree_reelle_minutes ? 'Réalisée' : 'Prévue'}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Rapport</h4>
            <p className={`text-lg font-medium ${intervention.rapport?.is_signed ? 'text-success' : intervention.rapport ? 'text-warning' : 'text-muted'}`}>
              {intervention.rapport?.is_signed ? 'Signé' : intervention.rapport ? 'Non signé' : 'Aucun'}
            </p>
            <p className="text-sm text-muted">
              {intervention.rapport ? (intervention.rapport.is_signed ? 'Complet' : 'En attente signature') : 'À créer'}
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
 * Générer les insights basés sur l'intervention
 */
function generateInsights(intervention: Intervention): Insight[] {
  const insights: Insight[] = [];
  const daysUntil = getDaysUntilIntervention(intervention);
  const durationVariance = getDurationVariance(intervention);

  // Vérifier le planning
  if (isLate(intervention)) {
    insights.push({
      id: 'late',
      type: 'warning',
      title: 'Intervention en retard',
      description: `La date prévue (${formatDate(intervention.date_prevue)}) est dépassée.`,
    });
  } else if (daysUntil !== null && daysUntil === 0) {
    insights.push({
      id: 'today',
      type: 'suggestion',
      title: 'Intervention aujourd\'hui',
      description: 'L\'intervention est prévue pour aujourd\'hui.',
    });
  } else if (daysUntil !== null && daysUntil <= 2 && daysUntil > 0) {
    insights.push({
      id: 'soon',
      type: 'suggestion',
      title: 'Intervention imminente',
      description: `L'intervention est prévue dans ${daysUntil} jour(s).`,
    });
  } else if (intervention.date_prevue) {
    insights.push({
      id: 'planned',
      type: 'success',
      title: 'Intervention planifiée',
      description: `Prévue pour le ${formatDate(intervention.date_prevue)}.`,
    });
  }

  // Vérifier l'intervenant
  if (!intervention.intervenant_name && intervention.statut !== 'TERMINEE') {
    insights.push({
      id: 'no-tech',
      type: 'warning',
      title: 'Pas d\'intervenant',
      description: 'Aucun intervenant n\'est assigné à cette intervention.',
    });
  } else if (intervention.intervenant_name) {
    insights.push({
      id: 'tech-assigned',
      type: 'success',
      title: 'Intervenant assigné',
      description: `${intervention.intervenant_name} est responsable.`,
    });
  }

  // Vérifier l'adresse
  if (intervention.adresse_intervention || intervention.adresse_ligne1) {
    insights.push({
      id: 'address-ok',
      type: 'success',
      title: 'Adresse renseignée',
      description: 'Le lieu d\'intervention est défini.',
    });
  } else if (intervention.statut !== 'TERMINEE') {
    insights.push({
      id: 'no-address',
      type: 'suggestion',
      title: 'Adresse manquante',
      description: 'L\'adresse d\'intervention n\'est pas renseignée.',
    });
  }

  // Vérifier la durée
  if (durationVariance !== null) {
    if (durationVariance > 30) {
      insights.push({
        id: 'overtime',
        type: 'warning',
        title: 'Dépassement de temps',
        description: `L'intervention a duré ${formatDuration(Math.abs(durationVariance))} de plus que prévu.`,
      });
    } else if (durationVariance < -15) {
      insights.push({
        id: 'faster',
        type: 'success',
        title: 'Intervention rapide',
        description: `Terminée ${formatDuration(Math.abs(durationVariance))} plus tôt que prévu.`,
      });
    }
  }

  // Vérifier le rapport
  if (intervention.statut === 'TERMINEE') {
    if (intervention.rapport?.is_signed) {
      insights.push({
        id: 'report-signed',
        type: 'success',
        title: 'Rapport signé',
        description: 'Le rapport d\'intervention a été signé par le client.',
      });
    } else if (intervention.rapport) {
      insights.push({
        id: 'report-unsigned',
        type: 'suggestion',
        title: 'Rapport non signé',
        description: 'Le rapport n\'a pas encore été signé par le client.',
      });
    } else {
      insights.push({
        id: 'no-report',
        type: 'warning',
        title: 'Pas de rapport',
        description: 'L\'intervention est terminée mais aucun rapport n\'a été créé.',
      });
    }
  }

  // Vérifier la facturation
  if (intervention.statut === 'TERMINEE' && intervention.facturable !== false) {
    if (intervention.facture_id) {
      insights.push({
        id: 'invoiced',
        type: 'success',
        title: 'Facturée',
        description: `Facture ${intervention.facture_reference} créée.`,
      });
    } else {
      insights.push({
        id: 'to-invoice',
        type: 'suggestion',
        title: 'À facturer',
        description: 'L\'intervention peut être facturée.',
      });
    }
  }

  // Priorité urgente
  if (intervention.priorite === 'URGENT' && intervention.statut !== 'TERMINEE') {
    insights.push({
      id: 'urgent',
      type: 'warning',
      title: 'Intervention urgente',
      description: 'Cette intervention est marquée comme priorité urgente.',
    });
  }

  return insights;
}

export default InterventionIATab;
