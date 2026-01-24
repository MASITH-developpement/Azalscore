/**
 * AZALSCORE Module - Helpdesk - Ticket IA Tab
 * Onglet Assistant IA pour le ticket
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Clock, User, Target, Zap
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Ticket } from '../types';
import {
  formatDuration, PRIORITY_CONFIG, STATUS_CONFIG,
  isTicketOverdue, isSlaDueSoon, getTicketAge,
  getPublicMessageCount, getInternalMessageCount,
  getFirstResponseTime, getResolutionTime
} from '../types';

/**
 * TicketIATab - Assistant IA pour le ticket
 */
export const TicketIATab: React.FC<TabContentProps<Ticket>> = ({ data: ticket }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Generer les insights
  const insights = generateInsights(ticket);

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
            J'ai analyse ce ticket et identifie{' '}
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
            Suggerer une reponse
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
            {isTicketOverdue(ticket) && (
              <SuggestedAction
                title="Traitement urgent requis"
                description="Le SLA est depasse. Prioriser ce ticket."
                confidence={100}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {isSlaDueSoon(ticket) && !isTicketOverdue(ticket) && (
              <SuggestedAction
                title="SLA proche"
                description="Repondre rapidement pour respecter le SLA."
                confidence={95}
                icon={<Clock size={16} />}
              />
            )}
            {!ticket.assigned_to_id && (
              <SuggestedAction
                title="Assigner le ticket"
                description="Ce ticket n'est pas encore assigne."
                confidence={90}
                icon={<User size={16} />}
              />
            )}
            {ticket.status === 'WAITING' && (
              <SuggestedAction
                title="Relancer le client"
                description="En attente de reponse depuis un moment."
                confidence={85}
                icon={<MessageSquare size={16} />}
              />
            )}
            {ticket.status === 'RESOLVED' && (
              <SuggestedAction
                title="Demander une evaluation"
                description="Envoyer un sondage de satisfaction."
                confidence={80}
                icon={<Target size={16} />}
              />
            )}
            {ticket.status === 'IN_PROGRESS' && (
              <SuggestedAction
                title="Mettre a jour le client"
                description="Informer le client de l'avancement."
                confidence={75}
                icon={<Zap size={16} />}
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
            <p className={`text-lg font-medium text-${STATUS_CONFIG[ticket.status].color}`}>
              {STATUS_CONFIG[ticket.status].label}
            </p>
            <p className="text-sm text-muted">
              {STATUS_CONFIG[ticket.status].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Priorite</h4>
            <p className={`text-lg font-medium text-${PRIORITY_CONFIG[ticket.priority].color}`}>
              {PRIORITY_CONFIG[ticket.priority].label}
            </p>
            <p className="text-sm text-muted">
              {PRIORITY_CONFIG[ticket.priority].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Age du ticket</h4>
            <p className="text-lg font-medium text-primary">
              {getTicketAge(ticket)}
            </p>
            <p className="text-sm text-muted">
              {getPublicMessageCount(ticket)} message(s), {getInternalMessageCount(ticket)} note(s)
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Temps de reponse</h4>
            <p className="text-lg font-medium">
              {getFirstResponseTime(ticket) || 'N/A'}
            </p>
            <p className="text-sm text-muted">
              Resolution: {getResolutionTime(ticket) || 'En cours'}
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
 * Generer les insights bases sur le ticket
 */
function generateInsights(ticket: Ticket): Insight[] {
  const insights: Insight[] = [];

  // SLA
  if (isTicketOverdue(ticket)) {
    insights.push({
      id: 'sla-overdue',
      type: 'warning',
      title: 'SLA depasse',
      description: 'Ce ticket a depasse son delai de traitement.',
    });
  } else if (isSlaDueSoon(ticket)) {
    insights.push({
      id: 'sla-soon',
      type: 'warning',
      title: 'SLA proche',
      description: 'Le delai de traitement approche.',
    });
  } else if (ticket.sla_due_date) {
    insights.push({
      id: 'sla-ok',
      type: 'success',
      title: 'SLA respecte',
      description: 'Le ticket est dans les delais.',
    });
  }

  // Statut
  if (ticket.status === 'RESOLVED' || ticket.status === 'CLOSED') {
    insights.push({
      id: 'resolved',
      type: 'success',
      title: 'Ticket resolu',
      description: 'Le probleme a ete traite.',
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
      description: 'En attente de reponse du client.',
    });
  } else if (ticket.status === 'OPEN') {
    insights.push({
      id: 'open',
      type: 'suggestion',
      title: 'Ticket ouvert',
      description: 'Ce ticket necessite une prise en charge.',
    });
  }

  // Assignation
  if (!ticket.assigned_to_id) {
    insights.push({
      id: 'unassigned',
      type: 'warning',
      title: 'Non assigne',
      description: 'Ce ticket n\'est assigne a personne.',
    });
  } else {
    insights.push({
      id: 'assigned',
      type: 'success',
      title: 'Ticket assigne',
      description: `Assigne a ${ticket.assigned_to_name || 'un agent'}.`,
    });
  }

  // Premiere reponse
  if (ticket.first_response_at) {
    insights.push({
      id: 'first-response',
      type: 'success',
      title: 'Premiere reponse envoyee',
      description: `Repondu en ${getFirstResponseTime(ticket)}.`,
    });
  } else if (ticket.status !== 'CLOSED' && ticket.status !== 'RESOLVED') {
    insights.push({
      id: 'no-response',
      type: 'warning',
      title: 'Pas de reponse',
      description: 'Le client n\'a pas encore recu de reponse.',
    });
  }

  // Priorite
  if (ticket.priority === 'URGENT') {
    insights.push({
      id: 'urgent',
      type: 'warning',
      title: 'Priorite urgente',
      description: 'Ce ticket necessite une attention immediate.',
    });
  } else if (ticket.priority === 'HIGH') {
    insights.push({
      id: 'high-priority',
      type: 'suggestion',
      title: 'Priorite haute',
      description: 'Traitement prioritaire recommande.',
    });
  }

  // Messages
  const publicMsgs = getPublicMessageCount(ticket);
  if (publicMsgs >= 5) {
    insights.push({
      id: 'many-messages',
      type: 'suggestion',
      title: 'Conversation longue',
      description: `${publicMsgs} echanges - Envisager un appel telephonique.`,
    });
  }

  return insights;
}

export default TicketIATab;
