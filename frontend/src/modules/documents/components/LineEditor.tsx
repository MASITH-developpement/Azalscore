/**
 * AZALSCORE - Module Documents Unifié
 * Éditeur de lignes universel
 *
 * Optimisations:
 * - React.memo pour éviter les re-renders inutiles
 * - useCallback pour les handlers
 * - useMemo pour les calculs de totaux
 */

import React, { useState, useMemo, useCallback, memo } from 'react';
import { Plus, Trash2, AlertCircle } from 'lucide-react';
import { useTranslation } from '@core/i18n';
import { Button } from '@ui/actions';
import { TVA_RATES, DEFAULT_TVA_RATE, formatCurrency, calculateLineTotal } from '../constants';
import type { LineFormData } from '../types';

// ============================================================
// TYPES
// ============================================================

interface LineEditorProps {
  lines: LineFormData[];
  onChange: (lines: LineFormData[]) => void;
  readOnly?: boolean;
  currency?: string;
}

interface LineRowProps {
  line: LineFormData;
  index: number;
  isEditing: boolean;
  readOnly: boolean;
  currency: string;
  onUpdate: (index: number, updates: Partial<LineFormData>) => void;
  onRemove: (index: number) => void;
  onStartEdit: (index: number) => void;
  t: (key: string) => string;
}

// ============================================================
// COMPOSANT - Ligne individuelle (mémoïsé)
// ============================================================

const LineRow = memo<LineRowProps>(({
  line,
  index,
  isEditing,
  readOnly,
  currency,
  onUpdate,
  onRemove,
  onStartEdit,
  t,
}) => {
  const { subtotal } = calculateLineTotal(
    line.quantity,
    line.unit_price,
    line.discount_percent,
    line.tax_rate
  );

  const handleClick = useCallback(() => {
    if (!readOnly) {
      onStartEdit(index);
    }
  }, [readOnly, index, onStartEdit]);

  return (
    <tr className={isEditing ? 'editing' : ''}>
      <td>
        {isEditing ? (
          <input
            type="text"
            className="azals-input azals-input--sm"
            value={line.description}
            onChange={(e) => onUpdate(index, { description: e.target.value })}
            placeholder={t('documents.lines.description')}
            autoFocus
          />
        ) : (
          <span
            className={readOnly ? '' : 'clickable'}
            onClick={handleClick}
          >
            {line.description || (
              <em className="text-muted">{t('documents.lines.clickToEdit')}</em>
            )}
          </span>
        )}
      </td>
      <td>
        {isEditing ? (
          <input
            type="number"
            className="azals-input azals-input--sm"
            value={line.quantity}
            onChange={(e) => onUpdate(index, { quantity: parseFloat(e.target.value) || 0 })}
            min="0"
            step="0.01"
          />
        ) : (
          <span onClick={handleClick}>{line.quantity}</span>
        )}
      </td>
      <td>
        {isEditing ? (
          <input
            type="number"
            className="azals-input azals-input--sm"
            value={line.unit_price}
            onChange={(e) => onUpdate(index, { unit_price: parseFloat(e.target.value) || 0 })}
            min="0"
            step="0.01"
          />
        ) : (
          <span onClick={handleClick}>{formatCurrency(line.unit_price, currency)}</span>
        )}
      </td>
      <td>
        {isEditing ? (
          <input
            type="number"
            className="azals-input azals-input--sm"
            value={line.discount_percent}
            onChange={(e) => onUpdate(index, { discount_percent: parseFloat(e.target.value) || 0 })}
            min="0"
            max="100"
            step="0.1"
          />
        ) : (
          <span onClick={handleClick}>{line.discount_percent}%</span>
        )}
      </td>
      <td>
        {isEditing ? (
          <select
            className="azals-select azals-select--sm"
            value={line.tax_rate}
            onChange={(e) => onUpdate(index, { tax_rate: parseFloat(e.target.value) })}
          >
            {TVA_RATES.map((rate) => (
              <option key={rate.value} value={rate.value}>
                {rate.value}%
              </option>
            ))}
          </select>
        ) : (
          <span onClick={handleClick}>{line.tax_rate}%</span>
        )}
      </td>
      <td className="text-right font-medium">
        {formatCurrency(subtotal, currency)}
      </td>
      {!readOnly && (
        <td>
          <button
            type="button"
            className="azals-btn-icon azals-btn-icon--danger"
            onClick={() => onRemove(index)}
            title={t('common.delete')}
          >
            <Trash2 size={14} />
          </button>
        </td>
      )}
    </tr>
  );
});

LineRow.displayName = 'LineRow';

// ============================================================
// COMPOSANT PRINCIPAL - LineEditor
// ============================================================

export const LineEditor: React.FC<LineEditorProps> = memo(({
  lines,
  onChange,
  readOnly = false,
  currency = 'EUR',
}) => {
  const { t } = useTranslation();
  const [editingLine, setEditingLine] = useState<number | null>(null);

  // Ajouter une nouvelle ligne
  const addLine = useCallback(() => {
    const newLine: LineFormData = {
      id: `temp-${Date.now()}`,
      description: '',
      quantity: 1,
      unit: 'unité',
      unit_price: 0,
      discount_percent: 0,
      tax_rate: DEFAULT_TVA_RATE,
    };
    onChange([...lines, newLine]);
    setEditingLine(lines.length);
  }, [lines, onChange]);

  // Mettre à jour une ligne
  const updateLine = useCallback((index: number, updates: Partial<LineFormData>) => {
    const newLines = [...lines];
    newLines[index] = { ...newLines[index], ...updates };
    onChange(newLines);
  }, [lines, onChange]);

  // Supprimer une ligne
  const removeLine = useCallback((index: number) => {
    const newLines = lines.filter((_, i) => i !== index);
    onChange(newLines);
    setEditingLine(null);
  }, [lines, onChange]);

  // Démarrer l'édition d'une ligne
  const startEdit = useCallback((index: number) => {
    setEditingLine(index);
  }, []);

  // Calcul des totaux (mémoïsé)
  const totals = useMemo(() => {
    return lines.reduce(
      (acc, line) => {
        const calc = calculateLineTotal(
          line.quantity,
          line.unit_price,
          line.discount_percent,
          line.tax_rate
        );
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
        <h3>{t('documents.lines.title')}</h3>
        {!readOnly && (
          <Button
            size="sm"
            leftIcon={<Plus size={14} />}
            onClick={addLine}
          >
            {t('documents.lines.addLine')}
          </Button>
        )}
      </div>

      {lines.length === 0 ? (
        <div className="azals-line-editor__empty">
          <AlertCircle size={24} />
          <p>
            {t('documents.lines.noLines')}{' '}
            {!readOnly && t('documents.lines.clickToAdd')}
          </p>
        </div>
      ) : (
        <table className="azals-line-editor__table">
          <thead>
            <tr>
              <th style={{ width: '40%' }}>{t('documents.lines.description')}</th>
              <th style={{ width: '10%' }}>{t('documents.lines.quantity')}</th>
              <th style={{ width: '15%' }}>{t('documents.lines.unitPrice')}</th>
              <th style={{ width: '10%' }}>{t('documents.lines.discount')}</th>
              <th style={{ width: '10%' }}>{t('documents.lines.tax')}</th>
              <th style={{ width: '10%' }}>{t('documents.lines.totalHT')}</th>
              {!readOnly && <th style={{ width: '5%' }}></th>}
            </tr>
          </thead>
          <tbody>
            {lines.map((line, index) => (
              <LineRow
                key={line.id || index}
                line={line}
                index={index}
                isEditing={editingLine === index && !readOnly}
                readOnly={readOnly}
                currency={currency}
                onUpdate={updateLine}
                onRemove={removeLine}
                onStartEdit={startEdit}
                t={t}
              />
            ))}
          </tbody>
        </table>
      )}

      <div className="azals-line-editor__totals">
        <div className="azals-line-editor__total-row">
          <span>{t('documents.lines.totalHT')}</span>
          <span>{formatCurrency(totals.subtotal, currency)}</span>
        </div>
        <div className="azals-line-editor__total-row">
          <span>{t('documents.lines.totalTVA')}</span>
          <span>{formatCurrency(totals.taxAmount, currency)}</span>
        </div>
        <div className="azals-line-editor__total-row azals-line-editor__total-row--main">
          <span>{t('documents.lines.totalTTC')}</span>
          <span>{formatCurrency(totals.total, currency)}</span>
        </div>
      </div>
    </div>
  );
});

LineEditor.displayName = 'LineEditor';

export default LineEditor;
