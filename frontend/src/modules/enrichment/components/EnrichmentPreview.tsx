/**
 * AZALS Module - Auto-Enrichment - EnrichmentPreview Component
 * =============================================================
 * Composant de preview des donnees enrichies avec selection.
 */

import React, { useState, useCallback, useMemo } from 'react';
import type { EnrichmentPreviewProps } from '../types';

// ============================================================================
// FIELD LABELS
// ============================================================================

const FIELD_LABELS: Record<string, string> = {
  // Contact fields
  name: 'Nom / Raison sociale',
  company_name: 'Nom de l\'entreprise',
  legal_form: 'Forme juridique',
  siret: 'SIRET',
  siren: 'SIREN',
  naf_code: 'Code NAF',
  naf_label: 'Libelle NAF',
  address_line1: 'Adresse',
  address_line2: 'Complement',
  postal_code: 'Code postal',
  city: 'Ville',
  country: 'Pays',
  latitude: 'Latitude',
  longitude: 'Longitude',

  // Product fields
  brand: 'Marque',
  description: 'Description',
  image_url: 'URL Image',
  barcode: 'Code-barres',
  categories: 'Categories',
  nutriscore: 'Nutri-Score',
  ingredients: 'Ingredients',
  allergens: 'Allergenes',
  quantity: 'Quantite',
  labels: 'Labels',
};

// ============================================================================
// COMPONENT
// ============================================================================

export function EnrichmentPreview({
  fields,
  currentValues = {},
  onAccept,
  onCancel,
  isLoading = false,
}: EnrichmentPreviewProps): JSX.Element {
  const fieldKeys = useMemo(() => Object.keys(fields), [fields]);

  const [selectedFields, setSelectedFields] = useState<Set<string>>(
    new Set(fieldKeys)
  );

  const toggleField = useCallback((key: string) => {
    setSelectedFields((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  const selectAll = useCallback(() => {
    setSelectedFields(new Set(fieldKeys));
  }, [fieldKeys]);

  const selectNone = useCallback(() => {
    setSelectedFields(new Set());
  }, []);

  const handleAccept = useCallback(() => {
    const accepted = fieldKeys.filter((k) => selectedFields.has(k));
    const rejected = fieldKeys.filter((k) => !selectedFields.has(k));
    onAccept(accepted, rejected);
  }, [fieldKeys, selectedFields, onAccept]);

  // Check if value differs from current
  const isDifferent = useCallback(
    (key: string): boolean => {
      const newVal = fields[key];
      const curVal = currentValues[key];

      if (curVal === undefined || curVal === null || curVal === '') {
        return newVal !== undefined && newVal !== null && newVal !== '';
      }

      return String(newVal) !== String(curVal);
    },
    [fields, currentValues]
  );

  return (
    <div className="enrichment-preview">
      <div className="enrichment-preview__header">
        <h4>Donnees suggerees</h4>
        <div className="enrichment-preview__actions-quick">
          <button
            type="button"
            onClick={selectAll}
            className="enrichment-preview__link"
          >
            Tout selectionner
          </button>
          <span className="enrichment-preview__separator">|</span>
          <button
            type="button"
            onClick={selectNone}
            className="enrichment-preview__link"
          >
            Tout deselectionner
          </button>
        </div>
      </div>

      <div className="enrichment-preview__fields">
        {fieldKeys.map((key) => {
          const value = fields[key];
          const currentValue = currentValues[key];
          const isChecked = selectedFields.has(key);
          const hasDiff = isDifferent(key);
          const label = FIELD_LABELS[key] || key;

          // Skip empty values
          if (value === undefined || value === null || value === '') {
            return null;
          }

          return (
            <div
              key={key}
              className={`
                enrichment-preview__field
                ${isChecked ? 'enrichment-preview__field--selected' : ''}
                ${hasDiff ? 'enrichment-preview__field--different' : ''}
              `}
            >
              <label className="enrichment-preview__field-label">
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleField(key)}
                  className="enrichment-preview__checkbox"
                />
                <span className="enrichment-preview__field-name">{label}</span>
              </label>

              <div className="enrichment-preview__field-values">
                {currentValue !== undefined && currentValue !== '' && (
                  <div className="enrichment-preview__current">
                    <span className="enrichment-preview__current-label">Actuel:</span>
                    <span className="enrichment-preview__current-value">
                      {String(currentValue)}
                    </span>
                  </div>
                )}
                <div className="enrichment-preview__new">
                  <span className="enrichment-preview__new-label">Nouveau:</span>
                  <span className="enrichment-preview__new-value">
                    {String(value)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="enrichment-preview__footer">
        <span className="enrichment-preview__count">
          {selectedFields.size} / {fieldKeys.length} champs selectionnes
        </span>

        <div className="enrichment-preview__actions">
          <button
            type="button"
            onClick={onCancel}
            className="enrichment-preview__btn enrichment-preview__btn--cancel"
            disabled={isLoading}
          >
            Annuler
          </button>
          <button
            type="button"
            onClick={handleAccept}
            className="enrichment-preview__btn enrichment-preview__btn--accept"
            disabled={isLoading || selectedFields.size === 0}
          >
            {isLoading ? 'Enregistrement...' : 'Appliquer la selection'}
          </button>
        </div>
      </div>

      <style>{`
        .enrichment-preview {
          background: #f9fafb;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          overflow: hidden;
        }

        .enrichment-preview__header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem 1rem;
          background: white;
          border-bottom: 1px solid #e5e7eb;
        }

        .enrichment-preview__header h4 {
          margin: 0;
          font-size: 0.875rem;
          font-weight: 600;
          color: #111827;
        }

        .enrichment-preview__actions-quick {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.75rem;
        }

        .enrichment-preview__link {
          background: none;
          border: none;
          color: #3b82f6;
          cursor: pointer;
          padding: 0;
          font-size: inherit;
        }

        .enrichment-preview__link:hover {
          text-decoration: underline;
        }

        .enrichment-preview__separator {
          color: #d1d5db;
        }

        .enrichment-preview__fields {
          padding: 0.75rem 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          max-height: 300px;
          overflow-y: auto;
        }

        .enrichment-preview__field {
          padding: 0.625rem 0.75rem;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 0.375rem;
          transition: border-color 0.15s, background-color 0.15s;
        }

        .enrichment-preview__field--selected {
          border-color: #3b82f6;
          background: #eff6ff;
        }

        .enrichment-preview__field--different {
          border-left: 3px solid #f59e0b;
        }

        .enrichment-preview__field-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
          font-weight: 500;
          font-size: 0.875rem;
          color: #374151;
        }

        .enrichment-preview__checkbox {
          width: 1rem;
          height: 1rem;
          border-radius: 0.25rem;
          border: 1px solid #d1d5db;
          cursor: pointer;
        }

        .enrichment-preview__checkbox:checked {
          background: #3b82f6;
          border-color: #3b82f6;
        }

        .enrichment-preview__field-values {
          margin-top: 0.375rem;
          margin-left: 1.5rem;
          font-size: 0.75rem;
        }

        .enrichment-preview__current,
        .enrichment-preview__new {
          display: flex;
          gap: 0.5rem;
        }

        .enrichment-preview__current {
          color: #6b7280;
          text-decoration: line-through;
          margin-bottom: 0.125rem;
        }

        .enrichment-preview__new {
          color: #059669;
        }

        .enrichment-preview__current-label,
        .enrichment-preview__new-label {
          flex-shrink: 0;
          font-weight: 500;
        }

        .enrichment-preview__footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem 1rem;
          background: white;
          border-top: 1px solid #e5e7eb;
        }

        .enrichment-preview__count {
          font-size: 0.75rem;
          color: #6b7280;
        }

        .enrichment-preview__actions {
          display: flex;
          gap: 0.5rem;
        }

        .enrichment-preview__btn {
          padding: 0.5rem 1rem;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.15s;
        }

        .enrichment-preview__btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .enrichment-preview__btn--accept {
          background: #3b82f6;
          color: white;
          border: none;
        }

        .enrichment-preview__btn--accept:hover:not(:disabled) {
          background: #2563eb;
        }

        .enrichment-preview__btn--cancel {
          background: white;
          color: #374151;
          border: 1px solid #d1d5db;
        }

        .enrichment-preview__btn--cancel:hover:not(:disabled) {
          background: #f3f4f6;
        }
      `}</style>
    </div>
  );
}

export default EnrichmentPreview;
