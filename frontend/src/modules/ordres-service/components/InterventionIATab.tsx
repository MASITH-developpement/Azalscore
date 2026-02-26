/**
 * AZALSCORE Module - Ordres de Service - Intervention IA Tab
 * Onglet Assistant IA pour l'intervention
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  TrendingUp, AlertTriangle, Clock, User, Calendar, Euro, Camera
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
import {
  STATUT_CONFIG, PRIORITE_CONFIG,
  isInterventionLate, isInterventionToday, getInterventionAge,
  canStartIntervention, canCompleteIntervention, canInvoiceIntervention,
  getPhotoCount
} from '../types';
import type { Intervention } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * InterventionIATab - Assistant IA
 */
export const InterventionIATab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(intervention);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(intervention);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const successScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cette intervention et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de succès - Composant partagé */}
      <Card title="Probabilité de succès" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={successScore}
          label="Succès"
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur l'intervention
 */
function generateSuggestedActions(intervention: Intervention): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isInterventionLate(intervention)) {
    actions.push({
      id: 'late',
      title: 'Intervention en retard',
      description: "Replanifier ou démarrer l'intervention.",
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Replanifier',
    });
  }

  if (canStartIntervention(intervention) && isInterventionToday(intervention)) {
    actions.push({
      id: 'start',
      title: "Démarrer l'intervention",
      description: "Intervention prévue aujourd'hui.",
      confidence: 95,
      icon: <Calendar size={16} />,
      actionLabel: 'Démarrer',
    });
  }

  if (!intervention.intervenant_id && intervention.statut === 'A_PLANIFIER') {
    actions.push({
      id: 'assign',
      title: 'Assigner un intervenant',
      description: 'Aucun technicien assigné.',
      confidence: 90,
      icon: <User size={16} />,
      actionLabel: 'Assigner',
    });
  }

  if (canCompleteIntervention(intervention)) {
    actions.push({
      id: 'complete',
      title: "Terminer l'intervention",
      description: 'Ajouter le compte-rendu et clôturer.',
      confidence: 85,
      icon: <Clock size={16} />,
      actionLabel: 'Terminer',
    });
  }

  if (canInvoiceIntervention(intervention)) {
    actions.push({
      id: 'invoice',
      title: 'Créer la facture',
      description: "L'intervention est terminée.",
      confidence: 80,
      icon: <Euro size={16} />,
      actionLabel: 'Facturer',
    });
  }

  if (intervention.statut === 'EN_COURS' && getPhotoCount(intervention) === 0) {
    actions.push({
      id: 'photos',
      title: 'Prendre des photos',
      description: "Documenter l'intervention.",
      confidence: 75,
      icon: <Camera size={16} />,
      actionLabel: 'Ajouter',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur l'intervention
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
  } else if (intervention.intervenant_name) {
    insights.push({
      id: 'has-technician',
      type: 'success',
      title: 'Intervenant assigne',
      description: `${intervention.intervenant_name} est assigne.`,
    });
  }

  // Priorite
  if (intervention.priorite === 'URGENT') {
    insights.push({
      id: 'urgent',
      type: 'warning',
      title: 'Priorite urgente',
      description: 'Intervention immediate requise.',
    });
  } else if (intervention.priorite === 'HIGH') {
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
