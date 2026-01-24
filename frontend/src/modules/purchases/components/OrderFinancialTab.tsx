/**
 * AZALSCORE Module - Purchases - Order Financial Tab
 * Onglet financier de la commande
 */

import React from 'react';
import { Euro, TrendingUp, FileText, CreditCard } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { PurchaseOrder } from '../types';
import { formatCurrency, calculateVATBreakdown, ORDER_STATUS_CONFIG } from '../types';

/**
 * OrderFinancialTab - Financier
 */
export const OrderFinancialTab: React.FC<TabContentProps<PurchaseOrder>> = ({ data: order }) => {
  const vatBreakdown = calculateVATBreakdown(order.lines);

  return (
    <div className="azals-std-tab-content">
      {/* Resume financier */}
      <Card title="Resume financier" icon={<Euro size={18} />}>
        <Grid cols={4} gap="md">
          <div className="text-center p-4 bg-gray-50 rounded">
            <div className="text-sm text-muted mb-1">Lignes</div>
            <div className="text-2xl font-bold">{order.lines.length}</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-sm text-muted mb-1">Total HT</div>
            <div className="text-xl font-bold text-blue-600">
              {formatCurrency(order.total_ht, order.currency)}
            </div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded">
            <div className="text-sm text-muted mb-1">Total TVA</div>
            <div className="text-xl font-bold text-orange-600">
              {formatCurrency(order.total_tax, order.currency)}
            </div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-sm text-muted mb-1">Total TTC</div>
            <div className="text-xl font-bold text-green-600">
              {formatCurrency(order.total_ttc, order.currency)}
            </div>
          </div>
        </Grid>
      </Card>

      {/* Ventilation TVA */}
      <Card title="Ventilation TVA" icon={<TrendingUp size={18} />} className="mt-4">
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
                  <td className="text-right">{formatCurrency(item.base, order.currency)}</td>
                  <td className="text-right">{formatCurrency(item.amount, order.currency)}</td>
                  <td className="text-right font-medium">
                    {formatCurrency(item.base + item.amount, order.currency)}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 font-bold">
                <td>Total</td>
                <td className="text-right">{formatCurrency(order.total_ht, order.currency)}</td>
                <td className="text-right">{formatCurrency(order.total_tax, order.currency)}</td>
                <td className="text-right text-primary">{formatCurrency(order.total_ttc, order.currency)}</td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <div className="text-muted text-center py-4">Aucune ligne avec TVA</div>
        )}
      </Card>

      {/* Factures liees */}
      <Card title="Factures liees" icon={<FileText size={18} />} className="mt-4">
        {order.invoice_ids && order.invoice_ids.length > 0 ? (
          <div className="space-y-2">
            {order.invoice_ids.map((invoiceId) => (
              <div
                key={invoiceId}
                className="flex items-center justify-between p-3 bg-gray-50 rounded"
              >
                <span className="font-mono">{invoiceId}</span>
                <span className="azals-badge azals-badge--blue">Facture</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-muted text-center py-4">
            Aucune facture liee a cette commande
          </div>
        )}
      </Card>

      {/* Informations de paiement (ERP only) */}
      <Card title="Informations de paiement" icon={<CreditCard size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={2} gap="md">
          <div className="azals-field">
            <label className="azals-field__label">Devise</label>
            <div className="azals-field__value">{order.currency}</div>
          </div>
          <div className="azals-field">
            <label className="azals-field__label">Statut</label>
            <div className="azals-field__value">
              <span className={`azals-badge azals-badge--${ORDER_STATUS_CONFIG[order.status].color}`}>
                {ORDER_STATUS_CONFIG[order.status].label}
              </span>
            </div>
          </div>
        </Grid>
      </Card>
    </div>
  );
};

export default OrderFinancialTab;
