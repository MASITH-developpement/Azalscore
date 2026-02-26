/**
 * AZALSCORE Module - Purchases - Line Editor
 * ==========================================
 * Editeur de lignes pour commandes et factures
 */

import React, { useState, useMemo } from 'react';
import { Plus, Trash2, AlertCircle } from 'lucide-react';
import { Button } from '@ui/actions';
import { calculateLineTotal, TVA_RATES, type PurchaseOrderLine } from '../types';

// ============================================================================
// Types
// ============================================================================

export interface LineFormData {
  id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  discount_percent: number;
}

interface LineEditorProps {
  lines: LineFormData[];
  onChange: (lines: LineFormData[]) => void;
  readOnly?: boolean;
  currency?: string;
}

// ============================================================================
// Helpers
// ============================================================================

const formatCurrency = (value: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
  }).format(value);
};

// ============================================================================
// Component
// ============================================================================

export const LineEditor: React.FC<LineEditorProps> = ({
  lines,
  onChange,
  readOnly = false,
  currency = 'EUR',
}) => {
  const [editingLine, setEditingLine] = useState<number | null>(null);

  const addLine = () => {
    const newLine: LineFormData = {
      id: `temp-${Date.now()}`,
      description: '',
      quantity: 1,
      unit_price: 0,
      discount_percent: 0,
      tax_rate: 20,
    };
    onChange([...lines, newLine]);
    setEditingLine(lines.length);
  };

  const updateLine = (index: number, updates: Partial<LineFormData>) => {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], ...updates };
    onChange(newLines);
  };

  const removeLine = (index: number) => {
    const newLines = lines.filter((_, i) => i !== index);
    onChange(newLines);
    setEditingLine(null);
  };

  const totals = useMemo(() => {
    return lines.reduce(
      (acc, line) => {
        const calc = calculateLineTotal(line as PurchaseOrderLine);
        return {
          subtotal: acc.subtotal + calc.subtotal,
          taxAmount: acc.taxAmount + calc.taxAmount,
          total: acc.total + calc.total,
        };
      },
      { subtotal: 0, taxAmount: 0, total: 0 }
    );
  }, [lines]);

  return (
    <div className="azals-line-editor">
      <div className="azals-line-editor__header">
        <h3>Lignes</h3>
        {!readOnly && (
          <Button
            size="sm"
            leftIcon={<Plus size={14} />}
            onClick={addLine}
          >
            Ajouter une ligne
          </Button>
        )}
      </div>

      {lines.length === 0 ? (
        <div className="azals-line-editor__empty">
          <AlertCircle size={24} />
          <p>Aucune ligne. {!readOnly && 'Cliquez sur "Ajouter une ligne" pour commencer.'}</p>
        </div>
      ) : (
        <table className="azals-line-editor__table">
          <thead>
            <tr>
              <th style={{ width: '40%' }}>Description</th>
              <th style={{ width: '10%' }}>Qte</th>
              <th style={{ width: '15%' }}>Prix unit. HT</th>
              <th style={{ width: '10%' }}>Remise</th>
              <th style={{ width: '10%' }}>TVA</th>
              <th style={{ width: '10%' }}>Total HT</th>
              {!readOnly && <th style={{ width: '5%' }}></th>}
            </tr>
          </thead>
          <tbody>
            {lines.map((line, index) => {
              const calc = calculateLineTotal(line as PurchaseOrderLine);
              const isEditing = editingLine === index && !readOnly;

              return (
                <tr key={line.id || index} className={isEditing ? 'editing' : ''}>
                  <td>
                    {isEditing ? (
                      <input
                        type="text"
                        className="azals-input azals-input--sm"
                        value={line.description}
                        onChange={(e) => updateLine(index, { description: e.target.value })}
                        placeholder="Description"
                        autoFocus
                      />
                    ) : (
                      <span
                        className={readOnly ? '' : 'clickable'}
                        onClick={() => !readOnly && setEditingLine(index)}
                      >
                        {line.description || <em className="text-muted">Cliquez pour editer</em>}
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        className="azals-input azals-input--sm"
                        value={line.quantity}
                        onChange={(e) => updateLine(index, { quantity: parseFloat(e.target.value) || 0 })}
                        min="0"
                        step="0.01"
                      />
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {line.quantity}
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        className="azals-input azals-input--sm"
                        value={line.unit_price}
                        onChange={(e) => updateLine(index, { unit_price: parseFloat(e.target.value) || 0 })}
                        min="0"
                        step="0.01"
                      />
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {formatCurrency(line.unit_price, currency)}
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <input
                        type="number"
                        className="azals-input azals-input--sm"
                        value={line.discount_percent}
                        onChange={(e) => updateLine(index, { discount_percent: parseFloat(e.target.value) || 0 })}
                        min="0"
                        max="100"
                        step="0.1"
                      />
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {line.discount_percent}%
                      </span>
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <select
                        className="azals-select azals-select--sm"
                        value={line.tax_rate}
                        onChange={(e) => updateLine(index, { tax_rate: parseFloat(e.target.value) })}
                      >
                        {TVA_RATES.map((rate) => (
                          <option key={rate.value} value={rate.value}>
                            {rate.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span onClick={() => !readOnly && setEditingLine(index)}>
                        {line.tax_rate}%
                      </span>
                    )}
                  </td>
                  <td className="text-right font-medium">
                    {formatCurrency(calc.subtotal, currency)}
                  </td>
                  {!readOnly && (
                    <td>
                      <button
                        type="button"
                        className="azals-btn-icon azals-btn-icon--danger"
                        onClick={() => removeLine(index)}
                        title="Supprimer"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      <div className="azals-line-editor__totals">
        <div className="azals-line-editor__total-row">
          <span>Total HT</span>
          <span>{formatCurrency(totals.subtotal, currency)}</span>
        </div>
        <div className="azals-line-editor__total-row">
          <span>Total TVA</span>
          <span>{formatCurrency(totals.taxAmount, currency)}</span>
        </div>
        <div className="azals-line-editor__total-row azals-line-editor__total-row--main">
          <span>Total TTC</span>
          <span>{formatCurrency(totals.total, currency)}</span>
        </div>
      </div>
    </div>
  );
};

export default LineEditor;
