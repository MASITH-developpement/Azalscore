/**
 * AZALSCORE Module - Purchases - Order Lines Tab
 * Onglet lignes de la commande
 */

import React from 'react';
import { List, Plus, AlertCircle } from 'lucide-react';
import { Card } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { PurchaseOrder } from '../types';
import { calculateLineTotal, canEditOrder } from '../types';
import { formatCurrency, formatPercent } from '@/utils/formatters';

/**
 * OrderLinesTab - Lignes de commande
 */
export const OrderLinesTab: React.FC<TabContentProps<PurchaseOrder>> = ({ data: order }) => {
  const canEdit = canEditOrder(order);

  return (
    <div className="azals-std-tab-content">
      <Card
        title="Lignes de commande"
        icon={<List size={18} />}
        actions={
          canEdit && (
            <Button variant="secondary" size="sm" leftIcon={<Plus size={14} />}>
              Ajouter une ligne
            </Button>
          )
        }
      >
        {order.lines.length > 0 ? (
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
              {order.lines.map((line, index) => {
                const calc = calculateLineTotal(line);
                return (
                  <tr key={line.id || index}>
                    <td>{line.description || <em className="text-muted">Sans description</em>}</td>
                    <td className="text-right">{line.quantity}</td>
                    <td className="text-right">{formatCurrency(line.unit_price, order.currency)}</td>
                    <td className="text-right">
                      {line.discount_percent > 0 ? (
                        <span className="text-orange-600">-{formatPercent(line.discount_percent)}</span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="text-right">{formatPercent(line.tax_rate)}</td>
                    <td className="text-right font-medium">{formatCurrency(calc.subtotal, order.currency)}</td>
                  </tr>
                );
              })}
            </tbody>
            <tfoot>
              <tr className="border-t-2">
                <td colSpan={5} className="text-right font-medium">Total HT</td>
                <td className="text-right font-medium">{formatCurrency(order.total_ht, order.currency)}</td>
              </tr>
              <tr>
                <td colSpan={5} className="text-right text-muted">Total TVA</td>
                <td className="text-right text-muted">{formatCurrency(order.total_tax, order.currency)}</td>
              </tr>
              <tr className="bg-gray-50">
                <td colSpan={5} className="text-right font-bold text-lg">Total TTC</td>
                <td className="text-right font-bold text-lg text-primary">
                  {formatCurrency(order.total_ttc, order.currency)}
                </td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <AlertCircle size={32} className="text-muted" />
            <p className="text-muted">Aucune ligne de commande</p>
            {canEdit && (
              <Button variant="secondary" size="sm" leftIcon={<Plus size={14} />} className="mt-2">
                Ajouter une ligne
              </Button>
            )}
          </div>
        )}
      </Card>

      {/* Resume par taux de TVA (ERP only) */}
      {order.lines.length > 0 && (
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
              {getVATBreakdown(order.lines, order.currency).map((item) => (
                <tr key={item.rate}>
                  <td>{formatPercent(item.rate)}</td>
                  <td className="text-right">{formatCurrency(item.base, order.currency)}</td>
                  <td className="text-right">{formatCurrency(item.amount, order.currency)}</td>
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
function getVATBreakdown(lines: PurchaseOrder['lines'], currency: string) {
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

export default OrderLinesTab;
