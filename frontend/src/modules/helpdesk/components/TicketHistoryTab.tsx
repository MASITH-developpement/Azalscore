/**
 * AZALSCORE Module - Helpdesk - Ticket History Tab
 * Onglet historique du ticket
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  CheckCircle, AlertTriangle, MessageSquare, UserPlus, Tag
} from 'lucide-react';
import { Card } from '@ui/layout';
import { formatDateTime } from '@/utils/formatters';
import type { Ticket, TicketHistoryEntry } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * TicketHistoryTab - Historique du ticket
 */
export const TicketHistoryTab: React.FC<TabContentProps<Ticket>> = ({ data: ticket }) => {
  // Generer l'historique combine
  const history = generateHistoryFromTicket(ticket);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique des evenements" icon={<Clock size={18} />}>
        {history.length > 0 ? (
          <div className="azals-timeline">
            {history.map((entry, index) => (
              <HistoryEntry
                key={entry.id}
                entry={entry}
                isFirst={index === 0}
                isLast={index === history.length - 1}
              />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Clock size={32} className="text-muted" />
            <p className="text-muted">Aucun historique disponible</p>
          </div>
        )}
      </Card>

      {/* Journal d'audit detaille (ERP only) */}
      <Card
        title="Journal d'audit detaille"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <table className="azals-table azals-table--simple azals-table--compact">
          <thead>
            <tr>
              <th>Date/Heure</th>
              <th>Action</th>
              <th>Utilisateur</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry) => (
              <tr key={entry.id}>
                <td className="text-muted text-sm">{formatDateTime(entry.timestamp)}</td>
                <td>{entry.action}</td>
                <td>{entry.user_name || 'Systeme'}</td>
                <td className="text-muted text-sm">
                  {entry.details || '-'}
                  {entry.old_value && entry.new_value && (
                    <span className="ml-2">
                      <span className="text-danger">{entry.old_value}</span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className="text-success">{entry.new_value}</span>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

/**
 * Composant entree de timeline
 */
interface HistoryEntryProps {
  entry: TicketHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation') || action.includes('ouvert')) {
      return <CheckCircle size={16} className="text-success" />;
    }
    if (action.includes('message') || action.includes('reponse')) {
      return <MessageSquare size={16} className="text-blue-500" />;
    }
    if (action.includes('assigne') || action.includes('attribue')) {
      return <UserPlus size={16} className="text-purple-500" />;
    }
    if (action.includes('statut') || action.includes('status')) {
      return <Tag size={16} className="text-orange-500" />;
    }
    if (action.includes('priorite')) {
      return <AlertTriangle size={16} className="text-yellow-500" />;
    }
    if (action.includes('resolu') || action.includes('ferme')) {
      return <CheckCircle size={16} className="text-green-500" />;
    }
    if (action.includes('modifie') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    return <Clock size={16} className="text-muted" />;
  };

  return (
    <div className={`azals-timeline__entry ${isFirst ? 'azals-timeline__entry--first' : ''} ${isLast ? 'azals-timeline__entry--last' : ''}`}>
      <div className="azals-timeline__icon">{getIcon()}</div>
      <div className="azals-timeline__content">
        <div className="azals-timeline__header">
          <span className="azals-timeline__action">{entry.action}</span>
          <span className="azals-timeline__time text-muted">
            {formatDateTime(entry.timestamp)}
          </span>
        </div>
        {entry.user_name && (
          <div className="azals-timeline__user text-sm">
            <User size={12} className="mr-1" />
            {entry.user_name}
          </div>
        )}
        {entry.details && (
          <p className="azals-timeline__details text-muted text-sm mt-1">
            {entry.details}
          </p>
        )}
        {entry.old_value && entry.new_value && (
          <div className="azals-timeline__change text-sm mt-1">
            <span className="text-danger line-through">{entry.old_value}</span>
            <ArrowRight size={12} className="mx-2" />
            <span className="text-success">{entry.new_value}</span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Generer l'historique a partir des donnees du ticket
 */
function generateHistoryFromTicket(ticket: Ticket): TicketHistoryEntry[] {
  const history: TicketHistoryEntry[] = [];

  // Creation du ticket
  history.push({
    id: 'created',
    timestamp: ticket.created_at,
    action: 'Ticket cree',
    user_name: ticket.created_by,
    details: `Sujet: ${ticket.subject}`,
  });

  // Premiere reponse
  if (ticket.first_response_at) {
    const firstMessage = ticket.messages?.find(m => !m.is_internal);
    history.push({
      id: 'first-response',
      timestamp: ticket.first_response_at,
      action: 'Premiere reponse envoyee',
      user_name: firstMessage?.author_name,
      details: 'Reponse initiale au client',
    });
  }

  // Messages (seulement les 5 derniers pour la timeline)
  const recentMessages = (ticket.messages || []).slice(-5);
  recentMessages.forEach((msg, index) => {
    history.push({
      id: `message-${index}`,
      timestamp: msg.created_at,
      action: msg.is_internal ? 'Note interne ajoutee' : 'Message envoye',
      user_name: msg.author_name,
      details: msg.content.substring(0, 100) + (msg.content.length > 100 ? '...' : ''),
    });
  });

  // Resolution
  if (ticket.resolved_at) {
    history.push({
      id: 'resolved',
      timestamp: ticket.resolved_at,
      action: 'Ticket resolu',
      details: 'Le probleme a ete resolu',
    });
  }

  // Fermeture
  if (ticket.closed_at) {
    history.push({
      id: 'closed',
      timestamp: ticket.closed_at,
      action: 'Ticket ferme',
      details: 'Le ticket a ete cloture',
    });
  }

  // Historique fourni par l'API
  if (ticket.history && ticket.history.length > 0) {
    history.push(...ticket.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default TicketHistoryTab;
