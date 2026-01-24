/**
 * AZALSCORE Module - Ordres de Service - Intervention IA Tab
 * Onglet Assistant IA pour l'intervention
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ThumbsDown, ChevronRight,
  Clock, User, Calendar, Euro, Camera
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Intervention } from '../types';
import {
  formatDuration, formatCurrency, STATUT_CONFIG, PRIORITE_CONFIG,
  isInterventionLate, isInterventionToday, getInterventionAge,
  canStartIntervention, canCompleteIntervention, canInvoiceIntervention,
  getPhotoCount
} from '../types';

/**
 * InterventionIATab - Assistant IA
 */
export const InterventionIATab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Generer les insights
  const insights = generateInsights(intervention);

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
            J'ai analyse cette intervention et identifie{' '}
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

      {/* Score de succes */}
      <Card title="Probabilite de succes" icon={<TrendingUp size={18} />} className="mb-4">
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
            {isInterventionLate(intervention) && (
              <SuggestedAction
                title="Intervention en retard"
                description="Replanifier ou demarrer l'intervention."
                confidence={100}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {canStartIntervention(intervention) && isInterventionToday(intervention) && (
              <SuggestedAction
                title="Demarrer l'intervention"
                description="Intervention prevue aujourd'hui."
                confidence={95}
                icon={<Calendar size={16} />}
              />
            )}
            {!intervention.intervenant_id && intervention.statut === 'A_PLANIFIER' && (
              <SuggestedAction
                title="Assigner un intervenant"
                description="Aucun technicien assigne."
                confidence={90}
                icon={<User size={16} />}
              />
            )}
            {canCompleteIntervention(intervention) && (
              <SuggestedAction
                title="Terminer l'intervention"
                description="Ajouter le compte-rendu et cloturer."
                confidence={85}
                icon={<Clock size={16} />}
              />
            )}
            {canInvoiceIntervention(intervention) && (
              <SuggestedAction
                title="Creer la facture"
                description="L'intervention est terminee."
                confidence={80}
                icon={<Euro size={16} />}
              />
            )}
            {intervention.statut === 'EN_COURS' && getPhotoCount(intervention) === 0 && (
              <SuggestedAction
                title="Prendre des photos"
                description="Documenter l'intervention."
                confidence={75}
                icon={<Camera size={16} />}
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
            <p className={`text-lg font-medium text-${STATUT_CONFIG[intervention.statut].color}`}>
              {STATUT_CONFIG[intervention.statut].label}
            </p>
            <p className="text-sm text-muted">
              {STATUT_CONFIG[intervention.statut].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Priorite</h4>
            <p className={`text-lg font-medium text-${PRIORITE_CONFIG[intervention.priorite].color}`}>
              {PRIORITE_CONFIG[intervention.priorite].label}
            </p>
            <p className="text-sm text-muted">
              {PRIORITE_CONFIG[intervention.priorite].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Age</h4>
            <p className="text-lg font-medium text-primary">
              {getInterventionAge(intervention)}
            </p>
            <p className="text-sm text-muted">
              Depuis la creation
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Documentation</h4>
            <p className="text-lg font-medium">
              {getPhotoCount(intervention)} photo(s)
            </p>
            <p className="text-sm text-muted">
              {intervention.signature_client ? 'Signature presente' : 'Pas de signature'}
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
 * Generer les insights bases sur l'intervention
 */
function generateInsights(intervention: Intervention): Insight[] {
  const insights: Insight[] = [];

  // Retard
  if (isInterventionLate(intervention)) {
    insights.push({
      id: 'late',
      type: 'warning',
      title: 'Intervention en retard',
      description: 'La date prevue est passee sans demarrage.',
    });
  } else if (isInterventionToday(intervention)) {
    insights.push({
      id: 'today',
      type: 'suggestion',
      title: 'Intervention aujourd\'hui',
      description: 'Prevue pour aujourd\'hui.',
    });
  }

  // Statut
  if (intervention.statut === 'TERMINEE') {
    insights.push({
      id: 'completed',
      type: 'success',
      title: 'Intervention terminee',
      description: 'Les travaux ont ete realises.',
    });
  } else if (intervention.statut === 'EN_COURS') {
    insights.push({
      id: 'in-progress',
      type: 'success',
      title: 'En cours d\'execution',
      description: 'Un technicien est sur place.',
    });
  } else if (intervention.statut === 'PLANIFIEE') {
    insights.push({
      id: 'planned',
      type: 'success',
      title: 'Planifiee',
      description: 'Intervention programmee.',
    });
  } else if (intervention.statut === 'A_PLANIFIER') {
    insights.push({
      id: 'to-plan',
      type: 'suggestion',
      title: 'A planifier',
      description: 'Intervention en attente de planification.',
    });
  }

  // Intervenant
  if (!intervention.intervenant_id && intervention.statut !== 'TERMINEE') {
    insights.push({
      id: 'no-technician',
      type: 'warning',
      title: 'Pas d\'intervenant',
      description: 'Aucun technicien assigne.',
    });
  } else if (intervention.intervenant_nom) {
    insights.push({
      id: 'has-technician',
      type: 'success',
      title: 'Intervenant assigne',
      description: `${intervention.intervenant_nom} est assigne.`,
    });
  }

  // Priorite
  if (intervention.priorite === 'URGENTE') {
    insights.push({
      id: 'urgent',
      type: 'warning',
      title: 'Priorite urgente',
      description: 'Intervention immediate requise.',
    });
  } else if (intervention.priorite === 'HAUTE') {
    insights.push({
      id: 'high-priority',
      type: 'suggestion',
      title: 'Priorite haute',
      description: 'Traitement prioritaire recommande.',
    });
  }

  // Documentation
  const photoCount = getPhotoCount(intervention);
  if (photoCount >= 3) {
    insights.push({
      id: 'good-photos',
      type: 'success',
      title: 'Bien documente',
      description: `${photoCount} photos disponibles.`,
    });
  } else if (intervention.statut === 'TERMINEE' && photoCount === 0) {
    insights.push({
      id: 'no-photos',
      type: 'warning',
      title: 'Pas de photos',
      description: 'Aucune photo pour documenter.',
    });
  }

  // Compte-rendu
  if (intervention.statut === 'TERMINEE' && intervention.commentaire_cloture) {
    insights.push({
      id: 'has-report',
      type: 'success',
      title: 'Compte-rendu complet',
      description: 'Commentaire de cloture present.',
    });
  } else if (intervention.statut === 'TERMINEE' && !intervention.commentaire_cloture) {
    insights.push({
      id: 'no-report',
      type: 'warning',
      title: 'Compte-rendu manquant',
      description: 'Pas de commentaire de cloture.',
    });
  }

  return insights;
}

export default InterventionIATab;
