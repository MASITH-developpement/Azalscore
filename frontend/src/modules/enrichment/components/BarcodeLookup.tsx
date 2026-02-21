/**
 * AZALS Module - Auto-Enrichment - BarcodeLookup Component
 * =========================================================
 * Composant de recherche de produits par code-barres.
 */

import React, { useState, useCallback, useEffect } from 'react';
import { acceptEnrichment } from '../api';
import { useBarcodeLookup, formatBarcode, detectBarcodeType } from '../hooks';
import type { BarcodeLookupProps } from '../types';

// ============================================================================
// COMPONENT
// ============================================================================

export function BarcodeLookup({
  value = '',
  onEnrich,
  onHistoryId,
  disabled = false,
  className = '',
}: BarcodeLookupProps): JSX.Element {
  const [inputValue, setInputValue] = useState(value ?? '');
  const [showPreview, setShowPreview] = useState(false);

  const {
    fields,
    isLoading,
    error,
    historyId,
    barcodeType,
    lookup,
    reset,
  } = useBarcodeLookup({
    debounceMs: 400,
    minLength: 8,
  });

  // Sync with external value
  useEffect(() => {
    if (value !== inputValue) {
      setInputValue(value);
    }
  }, [value]);

  // Notify parent of history ID
  useEffect(() => {
    if (historyId && onHistoryId) {
      onHistoryId(historyId);
    }
  }, [historyId, onHistoryId]);

  // Show preview when fields available
  useEffect(() => {
    if (fields && Object.keys(fields).length > 0) {
      setShowPreview(true);
    }
  }, [fields]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value.replace(/[^0-9]/g, '');
      setInputValue(newValue);
      lookup(newValue);
    },
    [lookup]
  );

  const handleAccept = useCallback(async () => {
    if (fields && historyId) {
      try {
        await acceptEnrichment(historyId, {
          accepted_fields: Object.keys(fields),
          rejected_fields: [],
        });
        onEnrich?.(fields);
        setShowPreview(false);
        reset();
      } catch (err) {
        console.error('Error accepting enrichment:', err);
      }
    }
  }, [fields, historyId, onEnrich, reset]);

  const handleReject = useCallback(() => {
    setShowPreview(false);
    reset();
  }, [reset]);

  // Get barcode type label
  const getTypeLabel = (): string => {
    const clean = inputValue.replace(/\s/g, '');
    const type = detectBarcodeType(clean);
    switch (type) {
      case 'EAN-13':
        return 'EAN-13';
      case 'EAN-8':
        return 'EAN-8';
      case 'UPC-A':
        return 'UPC-A';
      case 'UPC-E':
        return 'UPC-E';
      default:
        return '';
    }
  };

  return (
    <div className={`barcode-lookup ${className}`}>
      {/* Input Field */}
      <div className="barcode-lookup__input-wrapper">
        <input
          type="text"
          value={formatBarcode(inputValue)}
          onChange={handleChange}
          placeholder="Code-barres (EAN-13, EAN-8, UPC)"
          disabled={disabled}
          className={`
            barcode-lookup__input
            ${error ? 'barcode-lookup__input--error' : ''}
            ${fields ? 'barcode-lookup__input--success' : ''}
          `}
          maxLength={17}
          inputMode="numeric"
          pattern="\d*"
        />

        {/* Status */}
        <div className="barcode-lookup__status">
          {isLoading && (
            <span className="barcode-lookup__spinner" title="Recherche...">
              &#8635;
            </span>
          )}
          {barcodeType !== 'unknown' && !isLoading && (
            <span className="barcode-lookup__type">{getTypeLabel()}</span>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="barcode-lookup__error-message">
          {error.message}
        </div>
      )}

      {/* Preview Panel */}
      {showPreview && fields && (
        <div className="barcode-lookup__preview">
          <div className="barcode-lookup__preview-header">
            <span>Produit trouve</span>
            <span className="barcode-lookup__preview-source">
              Source: Open Facts
            </span>
          </div>

          <div className="barcode-lookup__preview-content">
            {/* Product Image */}
            {fields.image_url && (
              <div className="barcode-lookup__preview-image">
                <img
                  src={fields.image_url}
                  alt={fields.name || 'Produit'}
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </div>
            )}

            {/* Product Fields */}
            <div className="barcode-lookup__preview-fields">
              {fields.name && (
                <div className="barcode-lookup__preview-field">
                  <span className="barcode-lookup__field-label">Nom</span>
                  <span>{fields.name}</span>
                </div>
              )}
              {fields.brand && (
                <div className="barcode-lookup__preview-field">
                  <span className="barcode-lookup__field-label">Marque</span>
                  <span>{fields.brand}</span>
                </div>
              )}
              {fields.description && (
                <div className="barcode-lookup__preview-field barcode-lookup__preview-field--full">
                  <span className="barcode-lookup__field-label">Description</span>
                  <span>{fields.description}</span>
                </div>
              )}
              {fields.categories && (
                <div className="barcode-lookup__preview-field">
                  <span className="barcode-lookup__field-label">Categories</span>
                  <span>{fields.categories}</span>
                </div>
              )}
              {fields.quantity && (
                <div className="barcode-lookup__preview-field">
                  <span className="barcode-lookup__field-label">Quantite</span>
                  <span>{fields.quantity}</span>
                </div>
              )}
              {fields.nutriscore && (
                <div className="barcode-lookup__preview-field">
                  <span className="barcode-lookup__field-label">Nutri-Score</span>
                  <span className={`barcode-lookup__nutriscore barcode-lookup__nutriscore--${fields.nutriscore.toLowerCase()}`}>
                    {fields.nutriscore.toUpperCase()}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="barcode-lookup__preview-actions">
            <button
              type="button"
              onClick={handleAccept}
              className="barcode-lookup__btn barcode-lookup__btn--accept"
            >
              Utiliser ces donnees
            </button>
            <button
              type="button"
              onClick={handleReject}
              className="barcode-lookup__btn barcode-lookup__btn--reject"
            >
              Ignorer
            </button>
          </div>
        </div>
      )}

      <style>{`
        .barcode-lookup {
          position: relative;
        }

        .barcode-lookup__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .barcode-lookup__input {
          width: 100%;
          padding: 0.5rem 4rem 0.5rem 0.75rem;
          border: 1px solid #d1d5db;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          letter-spacing: 0.05em;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .barcode-lookup__input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .barcode-lookup__input--error {
          border-color: #ef4444;
        }

        .barcode-lookup__input--success {
          border-color: #10b981;
        }

        .barcode-lookup__status {
          position: absolute;
          right: 0.75rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .barcode-lookup__spinner {
          animation: spin 1s linear infinite;
          color: #6b7280;
        }

        .barcode-lookup__type {
          font-size: 0.625rem;
          font-weight: 600;
          text-transform: uppercase;
          background: #e5e7eb;
          color: #374151;
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
        }

        .barcode-lookup__error-message {
          margin-top: 0.25rem;
          font-size: 0.75rem;
          color: #ef4444;
        }

        .barcode-lookup__preview {
          margin-top: 0.5rem;
          padding: 1rem;
          background: #f9fafb;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
        }

        .barcode-lookup__preview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
          font-weight: 600;
          font-size: 0.875rem;
        }

        .barcode-lookup__preview-source {
          font-size: 0.75rem;
          color: #6b7280;
          font-weight: normal;
        }

        .barcode-lookup__preview-content {
          display: flex;
          gap: 1rem;
        }

        .barcode-lookup__preview-image {
          flex-shrink: 0;
          width: 80px;
          height: 80px;
          border-radius: 0.375rem;
          overflow: hidden;
          background: white;
          border: 1px solid #e5e7eb;
        }

        .barcode-lookup__preview-image img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .barcode-lookup__preview-fields {
          flex: 1;
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 0.5rem;
        }

        .barcode-lookup__preview-field {
          font-size: 0.875rem;
        }

        .barcode-lookup__preview-field--full {
          grid-column: 1 / -1;
        }

        .barcode-lookup__field-label {
          display: block;
          color: #6b7280;
          font-size: 0.75rem;
          margin-bottom: 0.125rem;
        }

        .barcode-lookup__nutriscore {
          display: inline-block;
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
          font-weight: 600;
          font-size: 0.75rem;
        }

        .barcode-lookup__nutriscore--a { background: #22c55e; color: white; }
        .barcode-lookup__nutriscore--b { background: #84cc16; color: white; }
        .barcode-lookup__nutriscore--c { background: #eab308; color: white; }
        .barcode-lookup__nutriscore--d { background: #f97316; color: white; }
        .barcode-lookup__nutriscore--e { background: #ef4444; color: white; }

        .barcode-lookup__preview-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e5e7eb;
        }

        .barcode-lookup__btn {
          padding: 0.5rem 1rem;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.15s;
        }

        .barcode-lookup__btn--accept {
          background: #3b82f6;
          color: white;
          border: none;
        }

        .barcode-lookup__btn--accept:hover {
          background: #2563eb;
        }

        .barcode-lookup__btn--reject {
          background: white;
          color: #374151;
          border: 1px solid #d1d5db;
        }

        .barcode-lookup__btn--reject:hover {
          background: #f3f4f6;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default BarcodeLookup;
