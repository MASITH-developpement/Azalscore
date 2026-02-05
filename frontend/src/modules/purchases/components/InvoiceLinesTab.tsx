/**
 * AZALSCORE Module - Purchases - Invoice Lines Tab
 * Onglet lignes de la facture fournisseur
 */

import React from 'react';
import { List, Plus, AlertCircle } from 'lucide-react';
import { Card } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { PurchaseInvoice } from '../types';
import { calculateLineTotal, canEditInvoice } from '../types';
import { formatCurrency, formatPercent } from '@/utils/formatters';

/**
 * InvoiceLinesTab - Lignes de facture
 */
export const InvoiceLinesTab: React.FC<TabContentProps<PurchaseInvoice>> = ({ data: invoice }) => {
  const canEdit = canEditInvoice(invoice);

  return (
    <div className="azals-std-tab-content">
      <Card
        title="Lignes de facture"
        icon={<List size={18} />}
        actions={
          canEdit && (
            <Button variant="secondary" size="sm" leftIcon={<Plus size={14} />}>
              Ajouter une ligne
            </Button>
          )
        }
      >
        {invoice.lines.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th style={{ width: '40%' }}>Description</th>
                <th className="text-right" style={{ width: '10%' }}>Qte</th>
                <th className="text-right" style={{ width: '15%' }}>Prix unit. HT</th>
                <th className="text-right" style={{ width: '10%' }}>Remise</th>
                <th className="text-right" style={{ width: '10%' }}>TVA</th>
                <th className="text-right" style={{ width: '15%' }}>Total HT</th>
              </tr>
            </thead>
            <tbody>
              {invoice.lines.map((line, index) => {
                const calc = calculateLineTotal(line);
                return (
                  <tr key={line.id || index}>
                    <td>{line.description || <em className="text-muted">Sans description</em>}</td>
                    <td className="text-right">{line.quantity}</td>
                    <td className="text-right">{formatCurrency(line.unit_price, invoice.currency)}</td>
                    <td className="text-right">
                      {line.discount_percent > 0 ? (
                        <span className="text-orange-600">-{formatPercent(line.discount_percent)}</span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="text-right">{formatPercent(line.tax_rate)}</td>
                    <td className="text-right font-medium">{formatCurrency(calc.subtotal, invoice.currency)}</td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr className="border-t-2">
                <td colSpan={5} className="text-right font-medium">Total HT</td>
                <td className="text-right font-medium">{formatCurrency(invoice.total_ht, invoice.currency)}</td>
              </tr>
              <tr>
                <td colSpan={5} className="text-right text-muted">Total TVA</td>
                <td className="text-right text-muted">{formatCurrency(invoice.total_tax, invoice.currency)}</td>
              </tr>
              <tr className="bg-gray-50">
                <td colSpan={5} className="text-right font-bold text-lg">Total TTC</td>
                <td className="text-right font-bold text-lg text-primary">
                  {formatCurrency(invoice.total_ttc, invoice.currency)}
                </td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <AlertCircle size={32} className="text-muted" />
            <p className="text-muted">Aucune ligne de facture</p>
            {canEdit && (
              <Button variant="secondary" size="sm" leftIcon={<Plus size={14} />} className="mt-2">
                Ajouter une ligne
              </Button>
            )}
          </div>
        )}
      </Card>

      {/* Resume par taux de TVA (ERP only) */}
      {invoice.lines.length > 0 && (
        <Card title="Ventilation TVA" className="mt-4 azals-std-field--secondary">
          <table className="azals-table azals-table--simple azals-table--compact">
            <thead>
              <tr>
                <th>Taux</th>
                <th className="text-right">Base HT</th>
                <th className="text-right">Montant TVA</th>
              </tr>
            </thead>
            <tbody>
              {getVATBreakdown(invoice.lines, invoice.currency).map((item) => (
                <tr key={item.rate}>
                  <td>{formatPercent(item.rate)}</td>
                  <td className="text-right">{formatCurrency(item.base, invoice.currency)}</td>
                  <td className="text-right">{formatCurrency(item.amount, invoice.currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
};

/**
 * Calcul ventilation TVA
 */
function getVATBreakdown(lines: PurchaseInvoice['lines'], currency: string) {
  const breakdown: Record<number, { base: number; amount: number }> = {};

  lines.forEach((line) => {
    const calc = calculateLineTotal(line);
    if (!breakdown[line.tax_rate]) {
      breakdown[line.tax_rate] = { base: 0, amount: 0 };
    }
    breakdown[line.tax_rate].base += calc.subtotal;
    breakdown[line.tax_rate].amount += calc.taxAmount;
  });

  return Object.entries(breakdown)
    .map(([rate, data]) => ({
      rate: parseFloat(rate),
      base: data.base,
      amount: data.amount,
    }))
    .sort((a, b) => a.rate - b.rate);
}

export default InvoiceLinesTab;
