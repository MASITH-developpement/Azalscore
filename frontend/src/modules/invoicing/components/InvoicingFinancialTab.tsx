/**
 * AZALSCORE Module - Invoicing - Financial Tab
 * Onglet informations financieres du document
 */

import React from 'react';
import {
  DollarSign, TrendingUp, CreditCard, AlertCircle, CheckCircle2, Clock
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Document } from '../types';
import {
  getDaysUntilDue, isDocumentOverdue,
  PAYMENT_TERMS, PAYMENT_METHODS
} from '../types';
import { formatCurrency, formatDate, formatPercent } from '@/utils/formatters';

/**
 * InvoicingFinancialTab - Informations financieres
 */
export const InvoicingFinancialTab: React.FC<TabContentProps<Document>> = ({ data: doc }) => {
  const daysUntilDue = getDaysUntilDue(doc);
  const isOverdue = isDocumentOverdue(doc);

  const getPaymentTermLabel = (value?: string): string => {
    if (!value) return 'Non defini';
    return PAYMENT_TERMS.find(t => t.value === value)?.label || value;
  };

  const getPaymentMethodLabel = (value?: string): string => {
    if (!value) return 'Non defini';
    return PAYMENT_METHODS.find(m => m.value === value)?.label || value;
  };

  // Calculer le statut de paiement
  const paymentReceived = doc.stats?.payment_received || 0;
  const paymentPending = doc.stats?.payment_pending || doc.total - paymentReceived;
  const paymentPercentage = doc.total > 0 ? (paymentReceived / doc.total) * 100 : 0;

  return (
    <div className="azals-std-tab-content">
      {/* Resume financier */}
      <Card title="Resume financier" icon={<DollarSign size={18} />}>
        <Grid cols={4} gap="md">
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-sm text-muted mb-1">Total HT</div>
            <div className="text-xl font-bold">{formatCurrency(doc.subtotal, doc.currency)}</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-sm text-muted mb-1">TVA</div>
            <div className="text-xl font-bold">{formatCurrency(doc.tax_amount, doc.currency)}</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-sm text-muted mb-1">Remise</div>
            <div className="text-xl font-bold text-orange">
              {doc.discount_amount > 0 ? `-${formatCurrency(doc.discount_amount, doc.currency)}` : '-'}
            </div>
          </div>
          <div className="text-center p-4 bg-primary-50 rounded border-2 border-primary">
            <div className="text-sm text-primary mb-1">Total TTC</div>
            <div className="text-2xl font-bold text-primary">{formatCurrency(doc.total, doc.currency)}</div>
          </div>
        </Grid>
      </Card>

      {/* Statut de paiement (factures uniquement) */}
      {doc.type === 'INVOICE' && (
        <Card title="Statut de paiement" icon={<CreditCard size={18} />} className="mt-4">
          {doc.status === 'PAID' ? (
            <div className="flex items-center gap-3 p-4 bg-green-50 rounded border border-green-200">
              <CheckCircle2 size={24} className="text-green-500" />
              <div>
                <div className="font-medium text-green-700">Facture payee</div>
                {doc.paid_at && (
                  <div className="text-sm text-green-600">Regle le {formatDate(doc.paid_at)}</div>
                )}
              </div>
            </div>
          ) : (
            <>
              {isOverdue && (
                <div className="flex items-center gap-3 p-4 bg-red-50 rounded border border-red-200 mb-4">
                  <AlertCircle size={24} className="text-red-500" />
                  <div>
                    <div className="font-medium text-red-700">Facture en retard</div>
                    <div className="text-sm text-red-600">
                      Echeance depassee de {Math.abs(daysUntilDue || 0)} jour(s)
                    </div>
                  </div>
                </div>
              )}
              {!isOverdue && daysUntilDue !== null && daysUntilDue <= 7 && daysUntilDue >= 0 && (
                <div className="flex items-center gap-3 p-4 bg-orange-50 rounded border border-orange-200 mb-4">
                  <Clock size={24} className="text-orange-500" />
                  <div>
                    <div className="font-medium text-orange-700">Echeance proche</div>
                    <div className="text-sm text-orange-600">
                      {daysUntilDue === 0 ? "Echeance aujourd'hui" : `${daysUntilDue} jour(s) restant(s)`}
                    </div>
                  </div>
                </div>
              )}

              <Grid cols={3} gap="md">
                <div className="azals-field">
                  <label className="azals-field__label">Montant du</label>
                  <div className="azals-field__value text-xl font-bold text-primary">
                    {formatCurrency(doc.total, doc.currency)}
                  </div>
                </div>
                <div className="azals-field">
                  <label className="azals-field__label">Recu</label>
                  <div className="azals-field__value text-xl font-bold text-green">
                    {formatCurrency(paymentReceived, doc.currency)}
                  </div>
                </div>
                <div className="azals-field">
                  <label className="azals-field__label">Reste a payer</label>
                  <div className={`azals-field__value text-xl font-bold ${paymentPending > 0 ? 'text-orange' : 'text-green'}`}>
                    {formatCurrency(paymentPending, doc.currency)}
                  </div>
                </div>
              </Grid>

              {/* Barre de progression */}
              <div className="mt-4">
                <div className="flex justify-between text-sm mb-1">
                  <span>Progression du paiement</span>
                  <span>{formatPercent(paymentPercentage)}</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all"
                    style={{ width: `${Math.min(paymentPercentage, 100)}%` }}
                  />
                </div>
              </div>
            </>
          )}
        </Card>
      )}

      {/* Conditions de paiement */}
      <Card title="Conditions de paiement" icon={<Clock size={18} />} className="mt-4">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Conditions</label>
            <div className="azals-field__value">{getPaymentTermLabel(doc.payment_terms)}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Mode de paiement</label>
            <div className="azals-field__value">{getPaymentMethodLabel(doc.payment_method)}</div>
          </div>
          {doc.due_date && (
            <div className="azals-field">
              <label className="azals-field__label">Date d'echeance</label>
              <div className={`azals-field__value ${isOverdue ? 'text-danger font-medium' : ''}`}>
                {formatDate(doc.due_date)}
              </div>
            </div>
          )}
          <div className="azals-field">
            <label className="azals-field__label">Devise</label>
            <div className="azals-field__value">{doc.currency}</div>
          </div>
        </Grid>
      </Card>

      {/* Analyse de marge (ERP only) */}
      {doc.stats && (doc.stats.margin_percent !== undefined) && (
        <Card
          title="Analyse de rentabilite"
          icon={<TrendingUp size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <Grid cols={3} gap="md">
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-sm text-muted mb-1">Cout de revient</div>
              <div className="text-lg font-bold">
                {formatCurrency(doc.stats.cost_total || 0, doc.currency)}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-sm text-muted mb-1">Marge brute</div>
              <div className={`text-lg font-bold ${(doc.stats.margin_amount || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                {formatCurrency(doc.stats.margin_amount || 0, doc.currency)}
              </div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded">
              <div className="text-sm text-muted mb-1">Taux de marge</div>
              <div className={`text-lg font-bold ${(doc.stats.margin_percent || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                {formatPercent(doc.stats.margin_percent || 0)}
              </div>
            </div>
          </Grid>
        </Card>
      )}
    </div>
  );
};

export default InvoicingFinancialTab;
