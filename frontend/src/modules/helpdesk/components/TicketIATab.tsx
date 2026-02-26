/**
 * AZALSCORE Module - Helpdesk - Ticket IA Tab
 * Onglet Assistant IA pour le ticket
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, AlertTriangle, Clock, User, Target, Zap, MessageSquare } from 'lucide-react';
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
  PRIORITY_CONFIG, STATUS_CONFIG,
  isTicketOverdue, isSlaDueSoon, getTicketAge,
  getPublicMessageCount, getInternalMessageCount,
  getFirstResponseTime, getResolutionTime
} from '../types';
import type { Ticket } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * TicketIATab - Assistant IA pour le ticket
 */
export const TicketIATab: React.FC<TabContentProps<Ticket>> = ({ data: ticket }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(ticket);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(ticket);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const resolutionScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce ticket et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

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

      {/* Analyse détaillée (ERP only) */}
      <Card
        title="Analyse détaillée"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-analysis-grid">
          <div className="azals-analysis-item">
            <h4>Statut</h4>
            <p className={`text-lg font-medium text-${STATUS_CONFIG[ticket.status].color}`}>
              {STATUS_CONFIG[ticket.status].label}
            </p>
            <p className="text-sm text-muted">
              {STATUS_CONFIG[ticket.status].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Priorité</h4>
            <p className={`text-lg font-medium text-${PRIORITY_CONFIG[ticket.priority].color}`}>
              {PRIORITY_CONFIG[ticket.priority].label}
            </p>
            <p className="text-sm text-muted">
              {PRIORITY_CONFIG[ticket.priority].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Âge du ticket</h4>
            <p className="text-lg font-medium text-primary">
              {getTicketAge(ticket)}
            </p>
            <p className="text-sm text-muted">
              {getPublicMessageCount(ticket)} message(s), {getInternalMessageCount(ticket)} note(s)
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Temps de réponse</h4>
            <p className="text-lg font-medium">
              {getFirstResponseTime(ticket) || 'N/A'}
            </p>
            <p className="text-sm text-muted">
              Résolution: {getResolutionTime(ticket) || 'En cours'}
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
 * Générer les actions suggérées basées sur le ticket
 */
function generateSuggestedActions(ticket: Ticket): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isTicketOverdue(ticket)) {
    actions.push({
      id: 'urgent-treatment',
      title: 'Traitement urgent requis',
      description: 'Le SLA est dépassé. Prioriser ce ticket.',
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Traiter',
    });
  }

  if (isSlaDueSoon(ticket) && !isTicketOverdue(ticket)) {
    actions.push({
      id: 'sla-close',
      title: 'SLA proche',
      description: 'Répondre rapidement pour respecter le SLA.',
      confidence: 95,
      icon: <Clock size={16} />,
      actionLabel: 'Répondre',
    });
  }

  if (!ticket.assigned_to_id) {
    actions.push({
      id: 'assign',
      title: 'Assigner le ticket',
      description: "Ce ticket n'est pas encore assigné.",
      confidence: 90,
      icon: <User size={16} />,
      actionLabel: 'Assigner',
    });
  }

  if (ticket.status === 'WAITING') {
    actions.push({
      id: 'followup',
      title: 'Relancer le client',
      description: 'En attente de réponse depuis un moment.',
      confidence: 85,
      icon: <MessageSquare size={16} />,
      actionLabel: 'Relancer',
    });
  }

  if (ticket.status === 'RESOLVED') {
    actions.push({
      id: 'survey',
      title: 'Demander une évaluation',
      description: 'Envoyer un sondage de satisfaction.',
      confidence: 80,
      icon: <Target size={16} />,
      actionLabel: 'Envoyer',
    });
  }

  if (ticket.status === 'IN_PROGRESS') {
    actions.push({
      id: 'update-client',
      title: 'Mettre à jour le client',
      description: "Informer le client de l'avancement.",
      confidence: 75,
      icon: <Zap size={16} />,
      actionLabel: 'Informer',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le ticket
 */
function generateInsights(ticket: Ticket): Insight[] {
  const insights: Insight[] = [];

  // SLA
  if (isTicketOverdue(ticket)) {
    insights.push({
      id: 'sla-overdue',
      type: 'warning',
      title: 'SLA dépassé',
      description: 'Ce ticket a dépassé son délai de traitement.',
    });
  } else if (isSlaDueSoon(ticket)) {
    insights.push({
      id: 'sla-soon',
      type: 'warning',
      title: 'SLA proche',
      description: 'Le délai de traitement approche.',
    });
  } else if (ticket.sla_due_date) {
    insights.push({
      id: 'sla-ok',
      type: 'success',
      title: 'SLA respecté',
      description: 'Le ticket est dans les délais.',
    });
  }

  // Statut
  if (ticket.status === 'RESOLVED' || ticket.status === 'CLOSED') {
    insights.push({
      id: 'resolved',
      type: 'success',
      title: 'Ticket résolu',
      description: 'Le problème a été traité.',
    });
  } else if (ticket.status === 'IN_PROGRESS') {
    insights.push({
      id: 'in-progress',
      type: 'success',
      title: 'En cours de traitement',
      description: 'Un agent travaille sur ce ticket.',
    });
  } else if (ticket.status === 'WAITING') {
    insights.push({
      id: 'waiting',
      type: 'suggestion',
      title: 'En attente',
      description: 'En attente de réponse du client.',
    });
  } else if (ticket.status === 'OPEN') {
    insights.push({
      id: 'open',
      type: 'suggestion',
      title: 'Ticket ouvert',
      description: 'Ce ticket nécessite une prise en charge.',
    });
  }

  // Assignation
  if (!ticket.assigned_to_id) {
    insights.push({
      id: 'unassigned',
      type: 'warning',
      title: 'Non assigné',
      description: "Ce ticket n'est assigné à personne.",
    });
  } else {
    insights.push({
      id: 'assigned',
      type: 'success',
      title: 'Ticket assigné',
      description: `Assigné à ${ticket.assigned_to_name || 'un agent'}.`,
    });
  }

  // Première réponse
  if (ticket.first_response_at) {
    insights.push({
      id: 'first-response',
      type: 'success',
      title: 'Première réponse envoyée',
      description: `Répondu en ${getFirstResponseTime(ticket)}.`,
    });
  } else if (ticket.status !== 'CLOSED' && ticket.status !== 'RESOLVED') {
    insights.push({
      id: 'no-response',
      type: 'warning',
      title: 'Pas de réponse',
      description: "Le client n'a pas encore reçu de réponse.",
    });
  }

  // Priorité
  if (ticket.priority === 'URGENT') {
    insights.push({
      id: 'urgent',
      type: 'warning',
      title: 'Priorité urgente',
      description: 'Ce ticket nécessite une attention immédiate.',
    });
  } else if (ticket.priority === 'HIGH') {
    insights.push({
      id: 'high-priority',
      type: 'suggestion',
      title: 'Priorité haute',
      description: 'Traitement prioritaire recommandé.',
    });
  }

  // Messages
  const publicMsgs = getPublicMessageCount(ticket);
  if (publicMsgs >= 5) {
    insights.push({
      id: 'many-messages',
      type: 'suggestion',
      title: 'Conversation longue',
      description: `${publicMsgs} échanges - Envisager un appel téléphonique.`,
    });
  }

  return insights;
}

export default TicketIATab;
