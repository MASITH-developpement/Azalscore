/**
 * AZALSCORE Module - DEVIS - Lines Tab
 * Onglet lignes du devis
 */

import React from 'react';
import { Package, Plus, Trash2, Edit, Copy } from 'lucide-react';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Devis, DocumentLine } from '../types';
import { formatCurrency } from '../types';

/**
 * DevisLinesTab - Affichage et gestion des lignes du devis
 */
export const DevisLinesTab: React.FC<TabContentProps<Devis>> = ({ data: devis }) => {
  const canEdit = devis.status === 'DRAFT';

  if (!devis.lines || devis.lines.length === 0) {
    return (
      <div className="azals-std-tab-content">
        <div className="azals-empty">
          <Package size={48} className="text-muted" />
          <h3>Aucune ligne</h3>
          <p>Ce devis ne contient pas encore de lignes.</p>
          {canEdit && (
            <Button leftIcon={<Plus size={16} />}>
              Ajouter une ligne
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="azals-std-tab-content">
      {/* Actions si éditable */}
      {canEdit && (
        <div className="azals-std-tab-actions mb-4">
          <Button variant="secondary" leftIcon={<Plus size={16} />}>
            Ajouter une ligne
          </Button>
          <Button variant="ghost" leftIcon={<Copy size={16} />}>
            Dupliquer la sélection
          </Button>
        </div>
      )}

      {/* Tableau des lignes */}
      <div className="azals-table-container">
        <table className="azals-table azals-table--hover">
          <thead>
            <tr>
              <th className="azals-table__th">#</th>
              <th className="azals-table__th azals-std-field--secondary">Code</th>
              <th className="azals-table__th">Description</th>
              <th className="azals-table__th text-right">Qté</th>
              <th className="azals-table__th text-right">P.U. HT</th>
              <th className="azals-table__th text-right azals-std-field--secondary">Remise</th>
              <th className="azals-table__th text-right azals-std-field--secondary">TVA</th>
              <th className="azals-table__th text-right">Total HT</th>
              {canEdit && <th className="azals-table__th" style={{ width: 80 }}></th>}
            </tr>
          </thead>
          <tbody>
            {devis.lines.map((line) => (
              <LineRow key={line.id} line={line} canEdit={canEdit} currency={devis.currency} />
            ))}
          </tbody>
          <tfoot>
            <tr className="azals-table__subtotal">
              <td colSpan={canEdit ? 7 : 6} className="text-right">
                <strong>Sous-total HT</strong>
              </td>
              <td className="text-right">
                <strong>{formatCurrency(devis.subtotal, devis.currency)}</strong>
              </td>
              {canEdit && <td></td>}
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Résumé des lignes (mode ERP) */}
      <div className="azals-std-field--secondary mt-4">
        <div className="azals-stats-bar">
          <div className="azals-stats-bar__item">
            <span className="azals-stats-bar__label">Nombre de lignes</span>
            <span className="azals-stats-bar__value">{devis.lines.length}</span>
          </div>
          <div className="azals-stats-bar__item">
            <span className="azals-stats-bar__label">Produits distincts</span>
            <span className="azals-stats-bar__value">
              {new Set(devis.lines.filter(l => l.product_id).map(l => l.product_id)).size}
            </span>
          </div>
          <div className="azals-stats-bar__item">
            <span className="azals-stats-bar__label">Quantité totale</span>
            <span className="azals-stats-bar__value">
              {devis.lines.reduce((sum, l) => sum + l.quantity, 0)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Composant ligne de tableau
 */
interface LineRowProps {
  line: DocumentLine;
  canEdit: boolean;
  currency: string;
}

const LineRow: React.FC<LineRowProps> = ({ line, canEdit, currency }) => {
  return (
    <tr className="azals-table__row">
      <td className="azals-table__td text-muted">{line.line_number}</td>
      <td className="azals-table__td azals-std-field--secondary">
        {line.product_code ? (
          <span className="azals-badge azals-badge--gray">{line.product_code}</span>
        ) : (
          <span className="text-muted">-</span>
        )}
      </td>
      <td className="azals-table__td">
        <div>{line.description}</div>
        {line.product_id && (
          <div className="text-muted text-sm azals-std-field--secondary">
            Réf: {line.product_id}
          </div>
        )}
      </td>
      <td className="azals-table__td text-right">
        {line.quantity}
        {line.unit && <span className="text-muted ml-1">{line.unit}</span>}
      </td>
      <td className="azals-table__td text-right">
        {formatCurrency(line.unit_price, currency)}
      </td>
      <td className="azals-table__td text-right azals-std-field--secondary">
        {line.discount_percent > 0 ? (
          <span className="text-success">-{line.discount_percent}%</span>
        ) : (
          <span className="text-muted">-</span>
        )}
      </td>
      <td className="azals-table__td text-right azals-std-field--secondary">
        {line.tax_rate}%
      </td>
      <td className="azals-table__td text-right font-medium">
        {formatCurrency(line.subtotal, currency)}
      </td>
      {canEdit && (
        <td className="azals-table__td">
          <div className="azals-btn-group">
            <button className="azals-btn-icon" title="Modifier">
              <Edit size={14} />
            </button>
            <button className="azals-btn-icon azals-btn-icon--danger" title="Supprimer">
              <Trash2 size={14} />
            </button>
          </div>
        </td>
      )}
    </tr>
  );
};

export default DevisLinesTab;
