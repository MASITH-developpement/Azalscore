/**
 * AZALSCORE Module - Subscriptions - Billing Tab
 * Onglet facturation et paiements
 */

import React from 'react';
import {
  Receipt, CreditCard, Download, CheckCircle, Clock, XCircle, AlertCircle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Subscription, SubscriptionInvoice } from '../types';
import {
  formatCurrency, formatDate, getTotalPaid, getPaidInvoicesCount,
  INVOICE_STATUS_CONFIG
} from '../types';

/**
 * SubscriptionBillingTab - Facturation
 */
export const SubscriptionBillingTab: React.FC<TabContentProps<Subscription>> = ({ data: subscription }) => {
  const invoices = subscription.invoices || [];
  const totalPaid = getTotalPaid(subscription);
  const paidCount = getPaidInvoicesCount(subscription);

  return (
    <div className="azals-std-tab-content">
      {/* Resume facturation */}
      <Card className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-muted">Total facture</div>
            <div className="text-3xl font-bold text-primary">
              {formatCurrency(totalPaid, subscription.currency)}
            </div>
            <div className="text-sm text-muted mt-1">
              {paidCount} facture{paidCount > 1 ? 's' : ''} payee{paidCount > 1 ? 's' : ''}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted">Valeur a vie estimee</div>
            <div className="text-2xl font-bold text-success">
              {formatCurrency(subscription.lifetime_value || totalPaid * 1.5, subscription.currency)}
            </div>
          </div>
        </div>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Moyen de paiement */}
        <Card title="Moyen de paiement" icon={<CreditCard size={18} />}>
          <div className="space-y-3">
            {subscription.payment_method_last_four ? (
              <>
                <div className="azals-std-field">
                  <label>Carte enregistree</label>
                  <div className="flex items-center gap-2">
                    <CreditCard size={16} className="text-muted" />
                    <span className="font-mono">**** **** **** {subscription.payment_method_last_four}</span>
                  </div>
                </div>
                <Button variant="secondary" size="sm">
                  Modifier le moyen de paiement
                </Button>
              </>
            ) : (
              <div className="text-center py-4">
                <CreditCard size={32} className="text-muted mx-auto mb-2" />
                <p className="text-muted">Aucun moyen de paiement enregistre</p>
                <Button variant="secondary" size="sm" className="mt-2">
                  Ajouter une carte
                </Button>
              </div>
            )}
          </div>
        </Card>

        {/* Prochaine facture */}
        <Card title="Prochaine facture" icon={<Receipt size={18} />}>
          <div className="space-y-3">
            <div className="azals-std-field">
              <label>Date d'emission</label>
              <div>{formatDate(subscription.current_period_end)}</div>
            </div>
            <div className="azals-std-field">
              <label>Montant prevu</label>
              <div className="text-lg font-bold">
                {formatCurrency(subscription.amount, subscription.currency)}
              </div>
            </div>
            {subscription.cancel_at_period_end && (
              <div className="text-sm text-warning">
                <AlertCircle size={14} className="inline mr-1" />
                Aucune facture prevue (annulation en cours)
              </div>
            )}
          </div>
        </Card>
      </Grid>

      {/* Historique des factures */}
      <Card title="Historique des factures" icon={<Receipt size={18} />} className="mt-4">
        {invoices.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>N Facture</th>
                <th>Periode</th>
                <th>Montant</th>
                <th>Statut</th>
                <th>Payee le</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((invoice) => (
                <InvoiceRow key={invoice.id} invoice={invoice} currency={subscription.currency} />
              ))}
            </tbody>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Receipt size={32} className="text-muted" />
            <p className="text-muted">Aucune facture pour cet abonnement</p>
          </div>
        )}
      </Card>
    </div>
  );
};

/**
 * Composant ligne de facture
 */
interface InvoiceRowProps {
  invoice: SubscriptionInvoice;
  currency: string;
}

const InvoiceRow: React.FC<InvoiceRowProps> = ({ invoice, currency }) => {
  const statusConfig = INVOICE_STATUS_CONFIG[invoice.status];

  const getStatusIcon = () => {
    switch (invoice.status) {
      case 'PAID':
        return <CheckCircle size={14} className="text-success" />;
      case 'OPEN':
        return <Clock size={14} className="text-blue-500" />;
      case 'VOID':
      case 'UNCOLLECTIBLE':
        return <XCircle size={14} className="text-danger" />;
      default:
        return <AlertCircle size={14} className="text-muted" />;
    }
  };

  return (
    <tr>
      <td>
        <code className="font-mono text-sm">{invoice.number}</code>
      </td>
      <td className="text-sm text-muted">
        {formatDate(invoice.period_start)} - {formatDate(invoice.period_end)}
      </td>
      <td className="font-medium">
        {formatCurrency(invoice.amount, currency)}
      </td>
      <td>
        <span className={`azals-badge azals-badge--${statusConfig.color}`}>
          {getStatusIcon()}
          <span className="ml-1">{statusConfig.label}</span>
        </span>
      </td>
      <td className="text-sm">
        {invoice.paid_at ? formatDate(invoice.paid_at) : '-'}
      </td>
      <td>
        <Button variant="ghost" size="sm" leftIcon={<Download size={14} />}>
          PDF
        </Button>
      </td>
    </tr>
  );
};

export default SubscriptionBillingTab;
