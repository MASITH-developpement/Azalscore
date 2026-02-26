/**
 * AZALSCORE Module - Invoicing - LinesEditor
 * Editeur de lignes de document
 */

import React, { useState, useMemo } from 'react';
import { Plus, Edit, Trash2, AlertCircle } from 'lucide-react';
import { Button } from '@ui/actions';
import type { LineFormData } from '../types';
import { calculateLineTotal } from '../types';
import { LineEditor as LineEditorModal } from './index';

const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency
  }).format(amount);
};

interface LinesEditorProps {
  lines: LineFormData[];
  onChange: (lines: LineFormData[]) => void;
  readOnly?: boolean;
  currency?: string;
}

const LinesEditor: React.FC<LinesEditorProps> = ({ lines, onChange, readOnly = false, currency = 'EUR' }) => {
  const [showModal, setShowModal] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  const openAddModal = () => {
    setEditingIndex(null);
    setShowModal(true);
  };

  const openEditModal = (index: number) => {
    setEditingIndex(index);
    setShowModal(true);
  };

  const handleSaveLine = (lineData: LineFormData) => {
    if (editingIndex !== null) {
      const newLines = [...lines];
      newLines[editingIndex] = { ...newLines[editingIndex], ...lineData };
      onChange(newLines);
    } else {
      const newLine: LineFormData = {
        ...lineData,
        id: lineData.id || `temp-${Date.now()}`,
      };
      onChange([...lines, newLine]);
    }
    setShowModal(false);
    setEditingIndex(null);
  };

  const removeLine = (index: number) => {
    const newLines = lines.filter((_, i) => i !== index);
    onChange(newLines);
  };

  const totals = useMemo(() => {
    return lines.reduce(
      (acc, line) => {
        const calc = calculateLineTotal(line);
        return {
          subtotal: acc.subtotal + calc.subtotal,
          taxAmount: acc.taxAmount + calc.taxAmount,
          total: acc.total + calc.total,
        };
      },
      { subtotal: 0, taxAmount: 0, total: 0 }
    );
  }, [lines]);

  const editingLineData = editingIndex !== null ? lines[editingIndex] : undefined;

  return (
    <div className="azals-line-editor">
      <div className="azals-line-editor__header">
        <h3>Lignes du document</h3>
        {!readOnly && (
          <Button
            size="sm"
            leftIcon={<Plus size={14} />}
            onClick={openAddModal}
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
              <th style={{ width: '35%' }}>Description</th>
              <th style={{ width: '10%' }}>Qte</th>
              <th style={{ width: '12%' }}>Prix unit. HT</th>
              <th style={{ width: '10%' }}>Remise</th>
              <th style={{ width: '8%' }}>TVA</th>
              <th style={{ width: '15%' }}>Total HT</th>
              {!readOnly && <th style={{ width: '10%' }}>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {lines.map((line, index) => {
              const calc = calculateLineTotal(line);

              return (
                <tr key={line.id || index}>
                  <td>
                    <div className="font-medium">{line.description || <em className="text-muted">Sans description</em>}</div>
                    {line.unit && <div className="text-xs text-muted">Unite: {line.unit}</div>}
                  </td>
                  <td className="text-right">{line.quantity}</td>
                  <td className="text-right">{formatCurrency(line.unit_price, currency)}</td>
                  <td className="text-right">
                    {line.discount_percent > 0 ? (
                      <span className="text-orange">{line.discount_percent}%</span>
                    ) : '-'}
                  </td>
                  <td className="text-right">{line.tax_rate}%</td>
                  <td className="text-right font-medium">{formatCurrency(calc.subtotal, currency)}</td>
                  {!readOnly && (
                    <td>
                      <div className="flex gap-1">
                        <button
                          type="button"
                          className="azals-btn-icon"
                          onClick={() => openEditModal(index)}
                          title="Modifier"
                        >
                          <Edit size={14} />
                        </button>
                        <button
                          type="button"
                          className="azals-btn-icon azals-btn-icon--danger"
                          onClick={() => removeLine(index)}
                          title="Supprimer"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
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

      {showModal && (
        <LineEditorModal
          initialData={editingLineData}
          currency={currency}
          onSave={handleSaveLine}
          onCancel={() => {
            setShowModal(false);
            setEditingIndex(null);
          }}
          isModal={true}
        />
      )}
    </div>
  );
};

export default LinesEditor;
