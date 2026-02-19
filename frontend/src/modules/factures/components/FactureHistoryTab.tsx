/**
 * AZALSCORE Module - FACTURES - History Tab
 * Onglet historique et audit de la facture
 */

import React from 'react';
import {
  Clock, User, Edit, Check, Send, Plus,
  FileText, ArrowRight, CreditCard, Ban, AlertTriangle
} from 'lucide-react';
import { Card } from '@ui/layout';
import { formatDateTime, formatCurrency } from '@/utils/formatters';
import { STATUS_CONFIG, PAYMENT_METHODS } from '../types';
import type { Facture, FactureHistoryEntry } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * FactureHistoryTab - Historique et audit trail de la facture
 */
export const FactureHistoryTab: React.FC<TabContentProps<Facture>> = ({ data: facture }) => {
  // Générer l'historique à partir des données de la facture
  const history = generateHistoryFromFacture(facture);

  return (
    <div className="azals-std-tab-content">
      <Card title="Historique des modifications" icon={<Clock size={18} />}>
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

      {/* Détail des paiements */}
      {facture.payments && facture.payments.length > 0 && (
        <Card title="Historique des paiements" icon={<CreditCard size={18} />} className="mt-4">
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Date</th>
                <th>Mode</th>
                <th>Référence</th>
                <th className="text-right">Montant</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {facture.payments.map((payment) => (
                <tr key={payment.id}>
                  <td>{formatDateTime(payment.date)}</td>
                  <td>{PAYMENT_METHODS[payment.method].label}</td>
                  <td>{payment.reference || '-'}</td>
                  <td className="text-right text-success">
                    {formatCurrency(payment.amount, facture.currency)}
                  </td>
                  <td className="text-muted text-sm">{payment.notes || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Détail des changements (ERP only) */}
      <Card
        title="Journal d'audit détaillé"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <table className="azals-table azals-table--simple azals-table--compact">
          <thead>
            <tr>
              <th>Date/Heure</th>
              <th>Action</th>
              <th>Utilisateur</th>
              <th>Détails</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry) => (
              <tr key={entry.id}>
                <td className="text-muted text-sm">{formatDateTime(entry.timestamp)}</td>
                <td>{entry.action}</td>
                <td>{entry.user_name || 'Système'}</td>
                <td className="text-muted text-sm">
                  {entry.details || '-'}
                  {entry.old_value && entry.new_value && (
                    <span className="ml-2">
                      <span className="text-danger">{entry.old_value}</span>
                      <ArrowRight size={12} className="mx-1" />
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
 * Composant entrée de timeline
 */
interface HistoryEntryProps {
  entry: FactureHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('créé') || action.includes('création')) {
      return <Plus size={16} className="text-success" />;
    }
    if (action.includes('validé') || action.includes('validation')) {
      return <Check size={16} className="text-primary" />;
    }
    if (action.includes('envoyé') || action.includes('envoi')) {
      return <Send size={16} className="text-purple" />;
    }
    if (action.includes('paiement') || action.includes('encaiss')) {
      return <CreditCard size={16} className="text-success" />;
    }
    if (action.includes('payé') || action.includes('soldé')) {
      return <CreditCard size={16} className="text-green" />;
    }
    if (action.includes('modifié') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    if (action.includes('annulé')) {
      return <Ban size={16} className="text-danger" />;
    }
    if (action.includes('retard')) {
      return <AlertTriangle size={16} className="text-danger" />;
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
 * Générer l'historique à partir des données de la facture
 */
function generateHistoryFromFacture(facture: Facture): FactureHistoryEntry[] {
  const history: FactureHistoryEntry[] = [];

  // Création
  history.push({
    id: 'created',
    timestamp: facture.created_at,
    action: `${facture.type === 'CREDIT_NOTE' ? 'Avoir' : 'Facture'} créé${facture.type === 'CREDIT_NOTE' ? '' : 'e'}`,
    user_name: facture.created_by,
    details: `Numéro: ${facture.number}${facture.parent_number ? ` (depuis ${facture.parent_number})` : ''}`,
  });

  // Validation
  if (facture.validated_at) {
    history.push({
      id: 'validated',
      timestamp: facture.validated_at,
      action: 'Document validé',
      user_name: facture.validated_by,
      old_value: STATUS_CONFIG.DRAFT.label,
      new_value: STATUS_CONFIG.VALIDATED.label,
    });
  }

  // Envoi
  if (facture.sent_at) {
    history.push({
      id: 'sent',
      timestamp: facture.sent_at,
      action: 'Envoyé au client',
      old_value: STATUS_CONFIG.VALIDATED.label,
      new_value: STATUS_CONFIG.SENT.label,
    });
  }

  // Paiements
  if (facture.payments && facture.payments.length > 0) {
    facture.payments.forEach((payment, _index) => {
      history.push({
        id: `payment-${payment.id}`,
        timestamp: payment.date,
        action: 'Paiement reçu',
        user_name: payment.created_by,
        details: `${PAYMENT_METHODS[payment.method].label}: ${formatCurrency(payment.amount, facture.currency)}${payment.reference ? ` (Réf: ${payment.reference})` : ''}`,
      });
    });
  }

  // Soldé
  if (facture.paid_at || facture.status === 'PAID') {
    history.push({
      id: 'paid',
      timestamp: facture.paid_at || facture.updated_at,
      action: 'Document soldé',
      details: `Montant total: ${formatCurrency(facture.total, facture.currency)}`,
      new_value: STATUS_CONFIG.PAID.label,
    });
  }

  // Annulation
  if (facture.status === 'CANCELLED') {
    history.push({
      id: 'cancelled',
      timestamp: facture.updated_at,
      action: 'Document annulé',
      new_value: STATUS_CONFIG.CANCELLED.label,
    });
  }

  // Trier par date décroissante (plus récent en premier)
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default FactureHistoryTab;
