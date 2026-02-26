/**
 * AZALSCORE Module - Invoicing - Line Editor Component
 * =====================================================
 * Editeur de ligne de document avec ProductAutocomplete integre.
 * Permet d'ajouter ou modifier une ligne de devis/commande/facture.
 */

import React, { useState, useCallback, useEffect } from 'react';
import { X, Save, Calculator, Package } from 'lucide-react';
import { Button } from '@ui/actions';
import { ProductAutocomplete } from '@/modules/inventory/components';
import type { EnrichedDocumentLineFields } from '@/modules/inventory/types';
import { formatCurrency } from '@/utils/formatters';
import { calculateLineTotal, TVA_RATES } from '../types';
import type { LineFormData } from '../types';

// ============================================================================
// TYPES
// ============================================================================

export interface LineEditorProps {
  /** Donnees de la ligne a editer (undefined pour nouvelle ligne) */
  initialData?: Partial<LineFormData>;
  /** Devise du document */
  currency?: string;
  /** Callback lors de la sauvegarde */
  onSave: (line: LineFormData) => void;
  /** Callback lors de l'annulation */
  onCancel: () => void;
  /** Mode modal (true) ou inline (false) */
  isModal?: boolean;
}

interface FormState {
  product_id?: string;
  product_code?: string;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  discount_percent: number;
  tax_rate: number;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function LineEditor({
  initialData,
  currency = 'EUR',
  onSave,
  onCancel,
  isModal = true,
}: LineEditorProps): JSX.Element {
  const [form, setForm] = useState<FormState>({
    product_id: undefined,
    product_code: undefined,
    description: initialData?.description || '',
    quantity: initialData?.quantity || 1,
    unit: initialData?.unit || 'pce',
    unit_price: initialData?.unit_price || 0,
    discount_percent: initialData?.discount_percent || 0,
    tax_rate: initialData?.tax_rate || 20,
  });

  const [searchValue, setSearchValue] = useState('');
  const [totals, setTotals] = useState({ subtotal: 0, taxAmount: 0, total: 0, discountAmount: 0 });

  // Recalculer les totaux quand les valeurs changent
  useEffect(() => {
    const lineData: LineFormData = {
      description: form.description,
      quantity: form.quantity,
      unit: form.unit,
      unit_price: form.unit_price,
      discount_percent: form.discount_percent,
      tax_rate: form.tax_rate,
    };
    setTotals(calculateLineTotal(lineData));
  }, [form.quantity, form.unit_price, form.discount_percent, form.tax_rate]);

  // Quand un produit est selectionne dans l'autocomplete
  const handleProductSelect = useCallback((fields: EnrichedDocumentLineFields) => {
    setForm(prev => ({
      ...prev,
      product_id: fields.product_id,
      product_code: fields.product_code,
      description: fields.description,
      unit: fields.unit || prev.unit,
      unit_price: fields.unit_price,
      tax_rate: fields.tax_rate ?? prev.tax_rate,
    }));
    setSearchValue(fields.description);
  }, []);

  // Mise a jour d'un champ du formulaire
  const handleChange = useCallback((field: keyof FormState, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }));
  }, []);

  // Sauvegarde
  const handleSave = useCallback(() => {
    if (!form.description.trim()) {
      alert('La description est obligatoire');
      return;
    }
    if (form.quantity <= 0) {
      alert('La quantite doit etre positive');
      return;
    }

    const lineData: LineFormData = {
      id: initialData?.id,
      description: form.description.trim(),
      quantity: form.quantity,
      unit: form.unit,
      unit_price: form.unit_price,
      discount_percent: form.discount_percent,
      tax_rate: form.tax_rate,
    };

    onSave(lineData);
  }, [form, initialData?.id, onSave]);

  // Content du formulaire
  const formContent = (
    <div className="line-editor__form">
      {/* Recherche produit */}
      <div className="line-editor__section">
        <span className="line-editor__label" aria-label="Recherche produit">
          <Package size={14} className="mr-1" />
          Produit (optionnel)
        </span>
        <ProductAutocomplete
          value={searchValue}
          onChange={setSearchValue}
          onSelect={handleProductSelect}
          placeholder="Rechercher un produit par code ou nom..."
          className="line-editor__autocomplete"
        />
        {form.product_code && (
          <div className="line-editor__product-info">
            Code produit: <span className="font-medium">{form.product_code}</span>
          </div>
        )}
      </div>

      {/* Description */}
      <div className="line-editor__section">
        <label className="line-editor__label">Description *</label>
        <textarea
          value={form.description}
          onChange={(e) => handleChange('description', e.target.value)}
          placeholder="Description de la ligne..."
          rows={2}
          className="line-editor__textarea"
        />
      </div>

      {/* Quantite, Unite, Prix unitaire */}
      <div className="line-editor__row">
        <div className="line-editor__field line-editor__field--sm">
          <label className="line-editor__label">Quantite *</label>
          <input
            type="number"
            value={form.quantity}
            onChange={(e) => handleChange('quantity', parseFloat(e.target.value) || 0)}
            min="0"
            step="0.01"
            className="line-editor__input"
          />
        </div>

        <div className="line-editor__field line-editor__field--sm">
          <label className="line-editor__label">Unite</label>
          <select
            value={form.unit}
            onChange={(e) => handleChange('unit', e.target.value)}
            className="line-editor__select"
          >
            <option value="pce">piece</option>
            <option value="h">heure</option>
            <option value="j">jour</option>
            <option value="kg">kg</option>
            <option value="m">metre</option>
            <option value="m2">m2</option>
            <option value="m3">m3</option>
            <option value="lot">lot</option>
          </select>
        </div>

        <div className="line-editor__field">
          <label className="line-editor__label">Prix unitaire HT</label>
          <input
            type="number"
            value={form.unit_price}
            onChange={(e) => handleChange('unit_price', parseFloat(e.target.value) || 0)}
            min="0"
            step="0.01"
            className="line-editor__input"
          />
        </div>
      </div>

      {/* Remise et TVA */}
      <div className="line-editor__row">
        <div className="line-editor__field">
          <label className="line-editor__label">Remise %</label>
          <input
            type="number"
            value={form.discount_percent}
            onChange={(e) => handleChange('discount_percent', parseFloat(e.target.value) || 0)}
            min="0"
            max="100"
            step="0.1"
            className="line-editor__input"
          />
        </div>

        <div className="line-editor__field">
          <label className="line-editor__label">TVA</label>
          <select
            value={form.tax_rate}
            onChange={(e) => handleChange('tax_rate', parseFloat(e.target.value))}
            className="line-editor__select"
          >
            {TVA_RATES.map(rate => (
              <option key={rate.value} value={rate.value}>{rate.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Recap des totaux */}
      <div className="line-editor__totals">
        <div className="line-editor__total-row">
          <span>Sous-total HT</span>
          <span>{formatCurrency(totals.subtotal, currency)}</span>
        </div>
        {totals.discountAmount > 0 && (
          <div className="line-editor__total-row line-editor__total-row--discount">
            <span>Remise</span>
            <span>-{formatCurrency(totals.discountAmount, currency)}</span>
          </div>
        )}
        <div className="line-editor__total-row">
          <span>TVA ({form.tax_rate}%)</span>
          <span>{formatCurrency(totals.taxAmount, currency)}</span>
        </div>
        <div className="line-editor__total-row line-editor__total-row--main">
          <span>Total TTC</span>
          <span>{formatCurrency(totals.total, currency)}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="line-editor__actions">
        <Button variant="ghost" onClick={onCancel}>
          Annuler
        </Button>
        <Button variant="primary" onClick={handleSave} leftIcon={<Save size={16} />}>
          {initialData?.id ? 'Modifier' : 'Ajouter'}
        </Button>
      </div>
    </div>
  );

  // Rendu modal ou inline
  if (isModal) {
    return (
      <div className="line-editor-overlay" onClick={onCancel}>
        <div className="line-editor line-editor--modal" onClick={(e) => e.stopPropagation()}>
          <div className="line-editor__header">
            <h3 className="line-editor__title">
              <Calculator size={18} className="mr-2" />
              {initialData?.id ? 'Modifier la ligne' : 'Ajouter une ligne'}
            </h3>
            <button className="line-editor__close" onClick={onCancel}>
              <X size={20} />
            </button>
          </div>
          {formContent}
        </div>
        <style>{lineEditorStyles}</style>
      </div>
    );
  }

  return (
    <div className="line-editor">
      {formContent}
      <style>{lineEditorStyles}</style>
    </div>
  );
}

// ============================================================================
// STYLES
// ============================================================================

const lineEditorStyles = `
  .line-editor-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
    padding: 1rem;
  }

  .line-editor {
    background: white;
    border-radius: 0.5rem;
    max-width: 600px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
  }

  .line-editor--modal {
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  }

  .line-editor__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #e5e7eb;
  }

  .line-editor__title {
    display: flex;
    align-items: center;
    font-size: 1.125rem;
    font-weight: 600;
    color: #111827;
    margin: 0;
  }

  .line-editor__close {
    background: none;
    border: none;
    color: #6b7280;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 0.25rem;
    transition: color 0.15s;
  }

  .line-editor__close:hover {
    color: #111827;
  }

  .line-editor__form {
    padding: 1.5rem;
  }

  .line-editor__section {
    margin-bottom: 1rem;
  }

  .line-editor__label {
    display: flex;
    align-items: center;
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.375rem;
  }

  .line-editor__autocomplete {
    margin-bottom: 0.5rem;
  }

  .line-editor__product-info {
    font-size: 0.75rem;
    color: #6b7280;
    margin-top: 0.25rem;
  }

  .line-editor__textarea,
  .line-editor__input,
  .line-editor__select {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    transition: border-color 0.15s, box-shadow 0.15s;
  }

  .line-editor__textarea:focus,
  .line-editor__input:focus,
  .line-editor__select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .line-editor__textarea {
    resize: vertical;
    min-height: 60px;
  }

  .line-editor__row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .line-editor__field {
    flex: 1;
  }

  .line-editor__field--sm {
    flex: 0 0 100px;
  }

  .line-editor__totals {
    background: #f9fafb;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .line-editor__total-row {
    display: flex;
    justify-content: space-between;
    padding: 0.25rem 0;
    font-size: 0.875rem;
    color: #6b7280;
  }

  .line-editor__total-row--discount {
    color: #ea580c;
  }

  .line-editor__total-row--main {
    border-top: 1px solid #e5e7eb;
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    font-weight: 600;
    color: #111827;
    font-size: 1rem;
  }

  .line-editor__actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
`;

export default LineEditor;
