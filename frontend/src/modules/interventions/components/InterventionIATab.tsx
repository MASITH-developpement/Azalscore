/**
 * AZALSCORE Module - INTERVENTIONS - IA Tab
 * Onglet Assistant IA pour l'intervention
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  TrendingUp, AlertTriangle, ChevronRight, Calendar, FileText
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
import { formatDate, formatDuration } from '@/utils/formatters';
import { useAnalyseIA } from '../api';
import {
  isLate, getDaysUntilIntervention,
  getDurationVariance, canStart, canComplete, canPlan, canValidate, canUnblock
} from '../types';
import type { Intervention } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * InterventionIATab - Assistant IA pour l'intervention
 * Fournit des insights, suggestions et analyses automatiques
 */
export const InterventionIATab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Backend IA analysis (audit-proof)
  const { data: analyseIA, refetch: refetchIA } = useAnalyseIA(intervention.id);

  // Fallback: générer les insights localement si l'API ne répond pas
  const insights = generateInsights(intervention);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Utiliser les données backend si disponibles
  const backendScore = analyseIA?.score_preparation;
  const backendDeductions = analyseIA?.score_deductions || [];
  const backendActions = analyseIA?.actions_suggerees || [];
  const backendResume = analyseIA?.resume_ia;

  // Calcul du score de préparation
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const preparationScore = backendScore ?? Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(intervention, backendActions);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    refetchIA().finally(() => setIsAnalyzing(false));
  };

  // Construire le sous-titre du panel
  const panelSubtitle = backendResume ||
    `J'ai analysé cette intervention et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de préparation - Composant partagé */}
      <Card title="Score de préparation" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={preparationScore}
          label="Préparation"
          details={
            backendDeductions.length > 0
              ? backendDeductions.join(' • ')
              : `${positiveCount} points positifs, ${warningCount} alertes, ${suggestionCount} suggestions`
          }
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Interface backend action
 */
interface BackendAction {
  label: string;
  action: string;
  confiance: number;
}

/**
 * Générer les actions suggérées basées sur l'intervention
 */
function generateSuggestedActions(
  intervention: Intervention,
  backendActions: BackendAction[]
): SuggestedActionData[] {
  // Si des actions backend sont disponibles, les utiliser
  if (backendActions.length > 0) {
    return backendActions.map((action, idx) => ({
      id: `backend-${idx}`,
      title: action.label,
      description: `Action : ${action.action}`,
      confidence: Math.round(action.confiance * 100),
      icon: <ChevronRight size={16} />,
    }));
  }

  // Sinon, générer les actions localement
  const actions: SuggestedActionData[] = [];

  if (canValidate(intervention)) {
    actions.push({
      id: 'validate-draft',
      title: 'Valider le brouillon',
      description: 'Passez l\'intervention au statut À planifier.',
      confidence: 90,
      icon: <ChevronRight size={16} />,
      actionLabel: 'Valider',
    });
  }

  if (canPlan(intervention)) {
    actions.push({
      id: 'plan-intervention',
      title: 'Planifier l\'intervention',
      description: 'Définissez une date et assignez un intervenant.',
      confidence: 90,
      icon: <Calendar size={16} />,
      actionLabel: 'Planifier',
    });
  }

  if (canStart(intervention)) {
    actions.push({
      id: 'start-intervention',
      title: 'Démarrer l\'intervention',
      description: 'L\'intervention est planifiée et peut être démarrée.',
      confidence: 85,
      icon: <ChevronRight size={16} />,
      actionLabel: 'Démarrer',
    });
  }

  if (canComplete(intervention)) {
    actions.push({
      id: 'complete-intervention',
      title: 'Terminer l\'intervention',
      description: 'Complétez le rapport et clôturez l\'intervention.',
      confidence: 90,
      icon: <ChevronRight size={16} />,
      actionLabel: 'Terminer',
    });
  }

  if (canUnblock(intervention)) {
    actions.push({
      id: 'unblock-intervention',
      title: 'Débloquer l\'intervention',
      description: 'L\'intervention est bloquée et doit être débloquée pour reprendre.',
      confidence: 95,
      icon: <ChevronRight size={16} />,
      actionLabel: 'Débloquer',
    });
  }

  if (intervention.statut === 'TERMINEE' && !intervention.rapport?.is_signed) {
    actions.push({
      id: 'sign-report',
      title: 'Faire signer le rapport',
      description: 'Le rapport n\'a pas encore été signé par le client.',
      confidence: 85,
      icon: <FileText size={16} />,
      actionLabel: 'Signer',
    });
  }

  if (intervention.statut === 'TERMINEE' && !intervention.facture_id && intervention.facturable !== false) {
    actions.push({
      id: 'invoice-intervention',
      title: 'Facturer l\'intervention',
      description: 'L\'intervention est terminée et peut être facturée.',
      confidence: 95,
      icon: <FileText size={16} />,
      actionLabel: 'Facturer',
    });
  }

  if (isLate(intervention)) {
    actions.push({
      id: 'reschedule',
      title: 'Replanifier',
      description: 'L\'intervention est en retard. Définissez une nouvelle date.',
      confidence: 85,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Replanifier',
    });
  }

  return actions;
}

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
