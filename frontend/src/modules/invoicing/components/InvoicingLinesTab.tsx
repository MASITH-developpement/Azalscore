/**
 * AZALSCORE Module - Invoicing - Lines Tab
 * Onglet lignes du document
 */

import React from 'react';
import { ShoppingCart, Package, Percent, Calculator } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Document, DocumentLine } from '../types';
import { formatCurrency, formatPercent, calculateLineTotal } from '../types';

/**
 * InvoicingLinesTab - Lignes du document
 */
export const InvoicingLinesTab: React.FC<TabContentProps<Document>> = ({ data: doc }) => {
  const lines = doc.lines || [];

  // Grouper les lignes par taux de TVA pour le recap
  const taxBreakdown = lines.reduce((acc, line) => {
    const rate = line.tax_rate;
    if (!acc[rate]) {
      acc[rate] = { base: 0, tax: 0 };
    }
    acc[rate].base += line.subtotal;
    acc[rate].tax += line.tax_amount;
    return acc;
  }, {} as Record<number, { base: number; tax: number }>);

  return (
    <div className="azals-std-tab-content">
      {/* Liste des lignes */}
      <Card title={`Lignes (${lines.length})`} icon={<ShoppingCart size={18} />}>
        {lines.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="azals-table azals-table--simple">
              <thead>
                <tr>
                  <th style={{ width: '5%' }}>#</th>
                  <th style={{ width: '35%' }}>Description</th>
                  <th style={{ width: '10%' }} className="text-right">Qte</th>
                  <th style={{ width: '15%' }} className="text-right">Prix unit. HT</th>
                  <th style={{ width: '10%' }} className="text-right">Remise</th>
                  <th style={{ width: '10%' }} className="text-right">TVA</th>
                  <th style={{ width: '15%' }} className="text-right">Total HT</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line, index) => (
                  <LineRow key={line.id} line={line} index={index + 1} currency={doc.currency} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <ShoppingCart size={32} className="text-muted" />
            <p className="text-muted">Aucune ligne</p>
          </div>
        )}
      </Card>

      {/* Recapitulatif TVA (ERP only) */}
      {Object.keys(taxBreakdown).length > 0 && (
        <Card
          title="Recapitulatif TVA"
          icon={<Percent size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <table className="azals-table azals-table--simple azals-table--compact">
            <thead>
              <tr>
                <th>Taux TVA</th>
                <th className="text-right">Base HT</th>
                <th className="text-right">Montant TVA</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(taxBreakdown)
                .sort(([a], [b]) => Number(a) - Number(b))
                .map(([rate, { base, tax }]) => (
                  <tr key={rate}>
                    <td>{formatPercent(Number(rate))}</td>
                    <td className="text-right">{formatCurrency(base, doc.currency)}</td>
                    <td className="text-right">{formatCurrency(tax, doc.currency)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Totaux */}
      <Card title="Totaux" icon={<Calculator size={18} />} className="mt-4">
        <div className="azals-totals">
          <div className="azals-totals__row">
            <span>Total HT</span>
            <span className="font-medium">{formatCurrency(doc.subtotal, doc.currency)}</span>
          </div>
          {doc.discount_amount > 0 && (
            <div className="azals-totals__row text-muted">
              <span>Remise globale ({formatPercent(doc.discount_percent)})</span>
              <span>-{formatCurrency(doc.discount_amount, doc.currency)}</span>
            </div>
          )}
          <div className="azals-totals__row">
            <span>Total TVA</span>
            <span>{formatCurrency(doc.tax_amount, doc.currency)}</span>
          </div>
          <div className="azals-totals__row azals-totals__row--main">
            <span>Total TTC</span>
            <span className="text-xl font-bold text-primary">
              {formatCurrency(doc.total, doc.currency)}
            </span>
          </div>
        </div>
      </Card>

      {/* Stats marge (ERP only) */}
      {doc.stats && (doc.stats.margin_amount !== undefined || doc.stats.cost_total !== undefined) && (
        <Card
          title="Analyse"
          icon={<Package size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <Grid cols={3} gap="md">
            {doc.stats.cost_total !== undefined && (
              <div className="azals-field">
                <label className="azals-field__label">Cout total</label>
                <div className="azals-field__value">
                  {formatCurrency(doc.stats.cost_total, doc.currency)}
                </div>
              </div>
            )}
            {doc.stats.margin_amount !== undefined && (
              <div className="azals-field">
                <label className="azals-field__label">Marge</label>
                <div className={`azals-field__value ${(doc.stats.margin_amount || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                  {formatCurrency(doc.stats.margin_amount, doc.currency)}
                </div>
              </div>
            )}
            {doc.stats.margin_percent !== undefined && (
              <div className="azals-field">
                <label className="azals-field__label">Taux de marge</label>
                <div className={`azals-field__value ${(doc.stats.margin_percent || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                  {formatPercent(doc.stats.margin_percent)}
                </div>
              </div>
            )}
          </Grid>
        </Card>
      )}
    </div>
  );
};

/**
 * Composant ligne
 */
interface LineRowProps {
  line: DocumentLine;
  index: number;
  currency: string;
}

const LineRow: React.FC<LineRowProps> = ({ line, index, currency }) => {
  return (
    <tr>
      <td className="text-muted">{index}</td>
      <td>
        <div className="font-medium">{line.description}</div>
        {line.product_code && (
          <div className="text-sm text-muted">Ref: {line.product_code}</div>
        )}
        {line.notes && (
          <div className="text-sm text-muted italic">{line.notes}</div>
        )}
      </td>
      <td className="text-right">
        {line.quantity}
        {line.unit && <span className="text-muted ml-1">{line.unit}</span>}
      </td>
      <td className="text-right">{formatCurrency(line.unit_price, currency)}</td>
      <td className="text-right">
        {line.discount_percent > 0 ? (
          <span className="text-orange">{formatPercent(line.discount_percent)}</span>
        ) : '-'}
      </td>
      <td className="text-right">{formatPercent(line.tax_rate)}</td>
      <td className="text-right font-medium">{formatCurrency(line.subtotal, currency)}</td>
    </tr>
  );
};

export default InvoicingLinesTab;
