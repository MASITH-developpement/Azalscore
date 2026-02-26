/**
 * AZALSCORE Module - Payments - Payment History Tab
 * Onglet historique du paiement
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  CheckCircle, XCircle, AlertCircle, CreditCard, RotateCcw
} from 'lucide-react';
import { Card } from '@ui/layout';
import { formatDateTime } from '@/utils/formatters';
import {
  PAYMENT_STATUS_CONFIG,
  getMethodLabel
} from '../types';
import type { Payment, PaymentHistoryEntry } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * PaymentHistoryTab - Historique
 */
export const PaymentHistoryTab: React.FC<TabContentProps<Payment>> = ({ data: payment }) => {
  // Generer l'historique combine
  const history = generateHistoryFromPayment(payment);

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
  entry: PaymentHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('initie')) {
      return <CreditCard size={16} className="text-blue-500" />;
    }
    if (action.includes('complete') || action.includes('reussi')) {
      return <CheckCircle size={16} className="text-green-500" />;
    }
    if (action.includes('echoue') || action.includes('annule')) {
      return <XCircle size={16} className="text-red-500" />;
    }
    if (action.includes('rembours')) {
      return <RotateCcw size={16} className="text-orange-500" />;
    }
    if (action.includes('modif')) {
      return <Edit size={16} className="text-warning" />;
    }
    if (action.includes('attente') || action.includes('cours')) {
      return <AlertCircle size={16} className="text-orange-500" />;
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
 * Generer l'historique a partir des donnees du paiement
 */
function generateHistoryFromPayment(payment: Payment): PaymentHistoryEntry[] {
  const history: PaymentHistoryEntry[] = [];

  // Creation du paiement
  history.push({
    id: 'created',
    timestamp: payment.created_at,
    action: 'Paiement initie',
    details: `Montant: ${payment.amount} ${payment.currency} - Methode: ${getMethodLabel(payment.method)}`,
  });

  // Traitement
  if (payment.processed_at && payment.status !== 'PENDING') {
    const statusConfig = PAYMENT_STATUS_CONFIG[payment.status];
    history.push({
      id: 'processed',
      timestamp: payment.processed_at,
      action: payment.status === 'COMPLETED' ? 'Paiement complete' :
              payment.status === 'FAILED' ? 'Paiement echoue' :
              payment.status === 'CANCELLED' ? 'Paiement annule' :
              `Statut: ${statusConfig.label}`,
      details: payment.error_message || (payment.status === 'COMPLETED' ? 'Transaction effectuee avec succes' : undefined),
    });
  }

  // Remboursements
  if (payment.refunds && payment.refunds.length > 0) {
    payment.refunds.forEach((refund, index) => {
      history.push({
        id: `refund-${refund.id || index}`,
        timestamp: refund.created_at,
        action: 'Remboursement demande',
        details: `${refund.amount} ${payment.currency} - ${refund.reason}`,
      });
      if (refund.processed_at && refund.status === 'COMPLETED') {
        history.push({
          id: `refund-completed-${refund.id || index}`,
          timestamp: refund.processed_at,
          action: 'Remboursement effectue',
          details: `${refund.amount} ${payment.currency}`,
        });
      }
    });
  }

  // Historique fourni par l'API
  if (payment.history && payment.history.length > 0) {
    history.push(...payment.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default PaymentHistoryTab;
