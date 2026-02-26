/**
 * AZALSCORE Module - Invoicing - History Tab
 * Onglet historique du document
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight, CheckCircle2,
  Send, CreditCard, XCircle, Plus
} from 'lucide-react';
import { Card } from '@ui/layout';
import { formatDateTime } from '@/utils/formatters';
import { DOCUMENT_TYPE_CONFIG } from '../types';
import type { Document, DocumentHistoryEntry } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * InvoicingHistoryTab - Historique
 */
export const InvoicingHistoryTab: React.FC<TabContentProps<Document>> = ({ data: doc }) => {
  const history = generateHistoryFromDocument(doc);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique du document" icon={<Clock size={18} />}>
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

      {/* Journal d'audit (ERP only) */}
      <Card
        title="Journal d'audit"
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
  entry: DocumentHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation')) {
      return <Plus size={16} className="text-green-500" />;
    }
    if (action.includes('valid')) {
      return <CheckCircle2 size={16} className="text-blue-500" />;
    }
    if (action.includes('envoy') || action.includes('email')) {
      return <Send size={16} className="text-purple-500" />;
    }
    if (action.includes('pay') || action.includes('regl')) {
      return <CreditCard size={16} className="text-green-500" />;
    }
    if (action.includes('annul')) {
      return <XCircle size={16} className="text-red-500" />;
    }
    if (action.includes('modif')) {
      return <Edit size={16} className="text-orange-500" />;
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
 * Generer l'historique a partir des donnees du document
 */
function generateHistoryFromDocument(doc: Document): DocumentHistoryEntry[] {
  const history: DocumentHistoryEntry[] = [];
  const typeConfig = DOCUMENT_TYPE_CONFIG[doc.type];

  // Creation du document
  history.push({
    id: 'created',
    timestamp: doc.created_at,
    action: `${typeConfig.label} cree`,
    user_name: doc.created_by_name,
    details: `Numero: ${doc.number}`,
  });

  // Validation
  if (doc.validated_at) {
    history.push({
      id: 'validated',
      timestamp: doc.validated_at,
      action: `${typeConfig.label} valide`,
      user_name: doc.validated_by_name,
      details: 'Le document est maintenant verrouille',
    });
  }

  // Envoi
  if (doc.sent_at) {
    history.push({
      id: 'sent',
      timestamp: doc.sent_at,
      action: `${typeConfig.label} envoye`,
      details: doc.customer_email ? `Envoye a ${doc.customer_email}` : 'Envoye au client',
    });
  }

  // Paiement
  if (doc.paid_at) {
    history.push({
      id: 'paid',
      timestamp: doc.paid_at,
      action: 'Paiement recu',
      details: `Montant: ${doc.total} ${doc.currency}`,
    });
  }

  // Annulation
  if (doc.cancelled_at) {
    history.push({
      id: 'cancelled',
      timestamp: doc.cancelled_at,
      action: `${typeConfig.label} annule`,
      details: doc.cancelled_reason || 'Annule par l\'utilisateur',
    });
  }

  // Derniere modification
  if (doc.updated_at && doc.updated_at !== doc.created_at) {
    history.push({
      id: 'updated',
      timestamp: doc.updated_at,
      action: 'Derniere modification',
      details: 'Mise a jour des informations',
    });
  }

  // Historique fourni par l'API
  if (doc.history && doc.history.length > 0) {
    history.push(...doc.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default InvoicingHistoryTab;
