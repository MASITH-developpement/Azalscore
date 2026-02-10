/**
 * AZALSCORE Module - Subscriptions - History Tab
 * Onglet historique de l'abonnement
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  CheckCircle, XCircle, AlertCircle, CreditCard, Gift, Repeat
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Subscription, SubscriptionHistoryEntry } from '../types';
import {
  SUBSCRIPTION_STATUS_CONFIG
} from '../types';
import { formatDateTime, formatCurrency } from '@/utils/formatters';

/**
 * SubscriptionHistoryTab - Historique
 */
export const SubscriptionHistoryTab: React.FC<TabContentProps<Subscription>> = ({ data: subscription }) => {
  const history = generateHistoryFromSubscription(subscription);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique de l'abonnement" icon={<Clock size={18} />}>
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
  entry: SubscriptionHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('souscri')) {
      return <CheckCircle size={16} className="text-green-500" />;
    }
    if (action.includes('essai') || action.includes('trial')) {
      return <Gift size={16} className="text-blue-500" />;
    }
    if (action.includes('renouvel')) {
      return <Repeat size={16} className="text-green-500" />;
    }
    if (action.includes('paiement') || action.includes('factur')) {
      return <CreditCard size={16} className="text-blue-500" />;
    }
    if (action.includes('annul')) {
      return <XCircle size={16} className="text-red-500" />;
    }
    if (action.includes('modif') || action.includes('chang')) {
      return <Edit size={16} className="text-warning" />;
    }
    if (action.includes('expir')) {
      return <AlertCircle size={16} className="text-gray-500" />;
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
 * Generer l'historique a partir des donnees de l'abonnement
 */
function generateHistoryFromSubscription(subscription: Subscription): SubscriptionHistoryEntry[] {
  const history: SubscriptionHistoryEntry[] = [];
  const statusConfig = SUBSCRIPTION_STATUS_CONFIG[subscription.status];

  // Creation de l'abonnement
  history.push({
    id: 'created',
    timestamp: subscription.created_at,
    action: 'Abonnement souscrit',
    details: `Plan: ${subscription.plan_name} - ${formatCurrency(subscription.amount, subscription.currency)}`,
  });

  // Debut de l'essai
  if (subscription.trial_start) {
    history.push({
      id: 'trial-start',
      timestamp: subscription.trial_start,
      action: 'Periode d\'essai demarree',
      details: subscription.trial_end ? `Jusqu'au ${new Date(subscription.trial_end).toLocaleDateString('fr-FR')}` : undefined,
    });
  }

  // Fin de l'essai
  if (subscription.trial_end && subscription.status !== 'TRIAL') {
    history.push({
      id: 'trial-end',
      timestamp: subscription.trial_end,
      action: 'Periode d\'essai terminee',
      details: 'Passage en abonnement payant',
    });
  }

  // Factures payees
  if (subscription.invoices) {
    subscription.invoices
      .filter(inv => inv.status === 'PAID' && inv.paid_at)
      .forEach((invoice, index) => {
        history.push({
          id: `invoice-paid-${index}`,
          timestamp: invoice.paid_at!,
          action: 'Paiement recu',
          details: `Facture ${invoice.number} - ${formatCurrency(invoice.amount, subscription.currency)}`,
        });
      });
  }

  // Annulation demandee
  if (subscription.cancel_at_period_end && !subscription.cancelled_at) {
    history.push({
      id: 'cancel-scheduled',
      timestamp: subscription.updated_at || subscription.created_at,
      action: 'Annulation programmee',
      details: `Prendra effet le ${new Date(subscription.current_period_end).toLocaleDateString('fr-FR')}`,
    });
  }

  // Annulation effective
  if (subscription.cancelled_at) {
    history.push({
      id: 'cancelled',
      timestamp: subscription.cancelled_at,
      action: 'Abonnement annule',
      details: statusConfig.description,
    });
  }

  // Historique fourni par l'API
  if (subscription.history && subscription.history.length > 0) {
    history.push(...subscription.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default SubscriptionHistoryTab;
