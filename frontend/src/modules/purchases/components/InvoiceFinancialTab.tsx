/**
 * AZALSCORE Module - Purchases - Invoice Financial Tab
 * Onglet financier de la facture fournisseur
 */

import React from 'react';
import { Euro, TrendingUp, CreditCard, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import { formatCurrency } from '@/utils/formatters';
import {
  calculateVATBreakdown,
  canPayInvoice, isOverdue, getDaysUntilDue
} from '../types';
import type { PurchaseInvoice } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * InvoiceFinancialTab - Financier
 */
export const InvoiceFinancialTab: React.FC<TabContentProps<PurchaseInvoice>> = ({ data: invoice }) => {
  const vatBreakdown = calculateVATBreakdown(invoice.lines);
  const overdue = isOverdue(invoice.due_date);
  const daysUntilDue = getDaysUntilDue(invoice.due_date);
  const amountPaid = invoice.amount_paid || 0;
  const amountRemaining = invoice.amount_remaining || (invoice.total_ttc - amountPaid);
  const paymentProgress = invoice.total_ttc > 0 ? (amountPaid / invoice.total_ttc) * 100 : 0;

  return (
    <div className="azals-std-tab-content">
      {/* Resume financier */}
      <Card title="Resume financier" icon={<Euro size={18} />}>
        <Grid cols={4} gap="md">
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-sm text-muted mb-1">Lignes</div>
            <div className="text-2xl font-bold">{invoice.lines.length}</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-sm text-muted mb-1">Total HT</div>
            <div className="text-xl font-bold text-blue-600">
              {formatCurrency(invoice.total_ht, invoice.currency)}
            </div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded">
            <div className="text-sm text-muted mb-1">Total TVA</div>
            <div className="text-xl font-bold text-orange-600">
              {formatCurrency(invoice.total_tax, invoice.currency)}
            </div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-sm text-muted mb-1">Total TTC</div>
            <div className="text-xl font-bold text-green-600">
              {formatCurrency(invoice.total_ttc, invoice.currency)}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Statut de paiement */}
      <Card title="Paiement" icon={<CreditCard size={18} />} className="mt-4">
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-muted">Progression du paiement</span>
            <span className="font-medium">{paymentProgress.toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full ${paymentProgress >= 100 ? 'bg-green-500' : paymentProgress > 0 ? 'bg-blue-500' : 'bg-gray-300'}`}
              style={{ width: `${Math.min(paymentProgress, 100)}%` }}
            />
          </div>
        </div>

        <Grid cols={3} gap="md">
          <div className="p-4 bg-green-50 rounded">
            <div className="text-sm text-muted mb-1">Paye</div>
            <div className="text-xl font-bold text-green-600">
              {formatCurrency(amountPaid, invoice.currency)}
            </div>
          </div>
          <div className={`p-4 rounded ${overdue ? 'bg-red-50' : 'bg-orange-50'}`}>
            <div className="text-sm text-muted mb-1">Reste a payer</div>
            <div className={`text-xl font-bold ${overdue ? 'text-red-600' : 'text-orange-600'}`}>
              {formatCurrency(amountRemaining, invoice.currency)}
              {overdue && <AlertTriangle size={16} className="inline ml-1" />}
            </div>
          </div>
          <div className="p-4 bg-gray-50 rounded">
            <div className="text-sm text-muted mb-1">Echeance</div>
            <div className={`text-lg font-medium ${overdue ? 'text-red-600' : ''}`}>
              {invoice.due_date ? (
                <>
                  {new Date(invoice.due_date).toLocaleDateString('fr-FR')}
                  {!overdue && daysUntilDue !== null && daysUntilDue <= 7 && (
                    <span className="text-warning text-sm ml-1">({daysUntilDue}j)</span>
                  )}
                </>
              ) : (
                '-'
              )}
            </div>
          </div>
        </Grid>

        {canPayInvoice(invoice) && (
          <div className="mt-4">
            <Button leftIcon={<CreditCard size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'recordPayment', invoiceId: invoice.id } })); }}>
              Enregistrer un paiement
            </Button>
          </div>
        )}

        {invoice.status === 'PAID' && (
          <div className="mt-4 p-4 bg-green-50 rounded flex items-center gap-2">
            <CheckCircle2 size={20} className="text-green-600" />
            <span className="text-green-700 font-medium">Facture integralement payee</span>
          </div>
        )}
      </Card>

      {/* Ventilation TVA */}
      <Card title="Ventilation TVA" icon={<TrendingUp size={18} />} className="mt-4 azals-std-field--secondary">
        {vatBreakdown.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Taux de TVA</th>
                <th className="text-right">Base HT</th>
                <th className="text-right">Montant TVA</th>
                <th className="text-right">Total TTC</th>
              </tr>
            </thead>
            <tbody>
              {vatBreakdown.map((item) => (
                <tr key={item.rate}>
                  <td className="font-medium">{item.rate}%</td>
                  <td className="text-right">{formatCurrency(item.base, invoice.currency)}</td>
                  <td className="text-right">{formatCurrency(item.amount, invoice.currency)}</td>
                  <td className="text-right font-medium">
                    {formatCurrency(item.base + item.amount, invoice.currency)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 font-bold">
                <td>Total</td>
                <td className="text-right">{formatCurrency(invoice.total_ht, invoice.currency)}</td>
                <td className="text-right">{formatCurrency(invoice.total_tax, invoice.currency)}</td>
                <td className="text-right text-primary">{formatCurrency(invoice.total_ttc, invoice.currency)}</td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <div className="text-muted text-center py-4">Aucune ligne avec TVA</div>
        )}
      </Card>
    </div>
  );
};

export default InvoiceFinancialTab;
