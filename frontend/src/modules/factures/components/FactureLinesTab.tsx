/**
 * AZALSCORE Module - FACTURES - Lines Tab
 * Onglet lignes de la facture
 */

import React from 'react';
import { Package, Hash, Percent, Info } from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Facture, DocumentLine } from '../types';
import { formatCurrency } from '../types';

/**
 * FactureLinesTab - Affichage des lignes de la facture
 */
export const FactureLinesTab: React.FC<TabContentProps<Facture>> = ({ data: facture }) => {
  const lines = facture.lines || [];
  const isCreditNote = facture.type === 'CREDIT_NOTE';

  if (lines.length === 0) {
    return (
      <div className="azals-std-tab-content">
        <Card>
          <div className="azals-empty">
            <Package size={48} className="text-muted" />
            <h3>Aucune ligne</h3>
            <p className="text-muted">Cette facture ne contient pas encore de lignes.</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="azals-std-tab-content">
      {/* Résumé rapide */}
      <div className="azals-stats-bar mb-4">
        <div className="azals-stats-bar__item">
          <Package size={16} />
          <span>{lines.length} ligne{lines.length > 1 ? 's' : ''}</span>
        </div>
        <div className="azals-stats-bar__item">
          <span className="text-muted">Sous-total HT:</span>
          <strong className={isCreditNote ? 'text-danger' : ''}>
            {isCreditNote && '-'}{formatCurrency(facture.subtotal, facture.currency)}
          </strong>
        </div>
      </div>

      {/* Tableau des lignes */}
      <Card noPadding>
        <table className="azals-table azals-table--hover">
          <thead>
            <tr>
              <th className="azals-std-field--secondary" style={{ width: '50px' }}>#</th>
              <th className="azals-std-field--secondary" style={{ width: '100px' }}>Code</th>
              <th>Description</th>
              <th className="text-right" style={{ width: '80px' }}>Qté</th>
              <th className="text-right azals-std-field--secondary" style={{ width: '100px' }}>P.U. HT</th>
              <th className="text-right azals-std-field--secondary" style={{ width: '80px' }}>Remise</th>
              <th className="text-right azals-std-field--secondary" style={{ width: '80px' }}>TVA</th>
              <th className="text-right" style={{ width: '120px' }}>Total HT</th>
            </tr>
          </thead>
          <tbody>
            {lines.map((line) => (
              <LineRow key={line.id} line={line} currency={facture.currency} isCreditNote={isCreditNote} />
            ))}
          </tbody>
          <tfoot>
            <tr className="azals-table__subtotal">
              <td colSpan={7} className="text-right">Sous-total HT</td>
              <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                {isCreditNote && '-'}{formatCurrency(facture.subtotal, facture.currency)}
              </td>
            </tr>
            {facture.discount_amount > 0 && (
              <tr>
                <td colSpan={7} className="text-right">
                  Remise globale ({facture.discount_percent}%)
                </td>
                <td className="text-right text-danger">
                  -{formatCurrency(facture.discount_amount, facture.currency)}
                </td>
              </tr>
            )}
            <tr>
              <td colSpan={7} className="text-right">TVA</td>
              <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                {isCreditNote && '-'}{formatCurrency(facture.tax_amount, facture.currency)}
              </td>
            </tr>
            <tr className="azals-table__total">
              <td colSpan={7} className="text-right"><strong>Total TTC</strong></td>
              <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
                <strong>
                  {isCreditNote && '-'}{formatCurrency(facture.total, facture.currency)}
                </strong>
              </td>
            </tr>
          </tfoot>
        </table>
      </Card>

      {/* Légende (ERP only) */}
      <div className="azals-legend mt-4 azals-std-field--secondary">
        <div className="azals-legend__item">
          <Hash size={14} />
          <span>Code produit du catalogue</span>
        </div>
        <div className="azals-legend__item">
          <Percent size={14} />
          <span>Remise ligne appliquée sur le prix unitaire</span>
        </div>
        {isCreditNote && (
          <div className="azals-legend__item text-danger">
            <Info size={14} />
            <span>Avoir: montants négatifs (remboursement)</span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Composant ligne de tableau
 */
const LineRow: React.FC<{ line: DocumentLine; currency: string; isCreditNote: boolean }> = ({
  line,
  currency,
  isCreditNote
}) => {
  const hasDiscount = line.discount_percent > 0;

  return (
    <tr>
      <td className="text-muted azals-std-field--secondary">{line.line_number}</td>
      <td className="azals-std-field--secondary">
        {line.product_code ? (
          <code className="azals-code azals-code--sm">{line.product_code}</code>
        ) : (
          <span className="text-muted">-</span>
        )}
      </td>
      <td>
        <div className="azals-line-description">
          <span>{line.description}</span>
        </div>
      </td>
      <td className="text-right">
        <span className="azals-quantity">
          {line.quantity}
          {line.unit && <span className="text-muted ml-1">{line.unit}</span>}
        </span>
      </td>
      <td className="text-right azals-std-field--secondary">
        {formatCurrency(line.unit_price, currency)}
      </td>
      <td className="text-right azals-std-field--secondary">
        {hasDiscount ? (
          <span className="text-warning">{line.discount_percent}%</span>
        ) : (
          <span className="text-muted">-</span>
        )}
      </td>
      <td className="text-right azals-std-field--secondary">
        {line.tax_rate}%
      </td>
      <td className={`text-right ${isCreditNote ? 'text-danger' : ''}`}>
        <strong>
          {isCreditNote && '-'}{formatCurrency(line.subtotal, currency)}
        </strong>
      </td>
    </tr>
  );
};

export default FactureLinesTab;
