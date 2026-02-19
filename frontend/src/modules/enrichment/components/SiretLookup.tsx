/**
 * AZALS Module - Auto-Enrichment - SiretLookup Component
 * =======================================================
 * Composant de recherche d'entreprise par SIRET/SIREN ou par nom.
 * Supporte l'autocomplete pour la recherche par nom.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { acceptEnrichment, searchCompanyByName } from '../api';
import { useSiretLookup, isValidSiret, isValidSiren } from '../hooks';
import type { CompanySuggestion , EnrichedContactFields, SiretLookupProps } from '../types';

// ============================================================================
// COMPONENT
// ============================================================================

export function SiretLookup({
  value = '',
  onEnrich,
  onHistoryId,
  disabled = false,
  className = '',
}: SiretLookupProps): JSX.Element {
  const [inputValue, setInputValue] = useState(value ?? '');
  const [showPreview, setShowPreview] = useState(false);
  const [searchMode, setSearchMode] = useState<'siret' | 'name'>('siret');

  // Name search state
  const [suggestions, setSuggestions] = useState<CompanySuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  const hookResult = useSiretLookup({
      debounceMs: 500,
      minLength: 9,
    });

  // Defensive: ensure hook result is properly destructured
  const {
    fields = null,
    isLoading = false,
    error = null,
    historyId = null,
    lookup = async () => {},
    reset = () => {},
    validationType = null
  } = hookResult ?? {};

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

  // Show preview when we have fields
  useEffect(() => {
    if (fields && Object.keys(fields).length > 0) {
      setShowPreview(true);
    }
  }, [fields]);

  // Close suggestions when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Detect search mode based on input
  const detectSearchMode = useCallback((val: string): 'siret' | 'name' => {
    const clean = val.replace(/\s/g, '');
    // If it starts with digits or is all digits, treat as SIRET/SIREN
    if (/^\d+$/.test(clean) && clean.length <= 14) {
      return 'siret';
    }
    // Otherwise treat as name search
    return 'name';
  }, []);

  const handleChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setInputValue(newValue);

      const mode = detectSearchMode(newValue);
      setSearchMode(mode);

      if (mode === 'siret') {
        // SIRET/SIREN mode
        setShowSuggestions(false);
        setSuggestions([]);
        lookup(newValue);
      } else {
        // Name search mode
        reset();
        setShowPreview(false);

        // Debounce name search
        if (searchTimeoutRef.current) {
          clearTimeout(searchTimeoutRef.current);
        }

        if (newValue.length >= 2) {
          setIsSearching(true);
          searchTimeoutRef.current = setTimeout(async () => {
            try {
              const results = await searchCompanyByName(newValue);
              const validResults = Array.isArray(results) ? results : [];
              setSuggestions(validResults);
              setShowSuggestions(validResults.length > 0);
            } catch (err) {
              console.error('Error searching companies:', err);
              setSuggestions([]);
            } finally {
              setIsSearching(false);
            }
          }, 300);
        } else {
          setSuggestions([]);
          setShowSuggestions(false);
        }
      }
    },
    [lookup, reset, detectSearchMode]
  );

  const handleSelectSuggestion = useCallback((suggestion: CompanySuggestion) => {
    setInputValue(suggestion.siret || suggestion.siren);
    setShowSuggestions(false);
    setSuggestions([]);
    setSearchMode('siret');

    // Create enriched fields from suggestion
    const enrichedFields: EnrichedContactFields = {
      name: suggestion.name,
      company_name: suggestion.name,
      siret: suggestion.siret,
      siren: suggestion.siren,
      address_line1: suggestion.address,
      city: suggestion.city,
      postal_code: suggestion.postal_code,
    };

    onEnrich?.(enrichedFields);
  }, [onEnrich]);

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

  // Validation status
  const getValidationStatus = (): 'valid' | 'invalid' | 'pending' | null => {
    if (searchMode === 'name') return null;
    if (!inputValue || (inputValue?.length ?? 0) < 9) return null;
    if (isLoading) return 'pending';

    const clean = inputValue.replace(/\s/g, '');
    if (clean.length === 14 && isValidSiret(clean)) return 'valid';
    if (clean.length === 9 && isValidSiren(clean)) return 'valid';
    if (clean.length >= 9) return 'invalid';

    return null;
  };

  const validationStatus = getValidationStatus();

  return (
    <div className={`siret-lookup ${className}`} ref={wrapperRef}>
      {/* Input Field */}
      <div className="siret-lookup__input-wrapper">
        <input
          type="text"
          value={inputValue}
          onChange={handleChange}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder="SIRET, SIREN ou nom d'entreprise"
          disabled={disabled}
          className={`
            siret-lookup__input
            ${validationStatus === 'valid' ? 'siret-lookup__input--valid' : ''}
            ${validationStatus === 'invalid' ? 'siret-lookup__input--invalid' : ''}
            ${isLoading || isSearching ? 'siret-lookup__input--loading' : ''}
          `}
        />

        {/* Status Indicator */}
        <div className="siret-lookup__status">
          {(isLoading || isSearching) && (
            <span className="siret-lookup__spinner" title="Recherche en cours...">
              &#8635;
            </span>
          )}
          {validationStatus === 'valid' && !isLoading && (
            <span className="siret-lookup__check" title={validationType?.toUpperCase()}>
              &#10003;
            </span>
          )}
          {validationStatus === 'invalid' && !isLoading && (
            <span className="siret-lookup__error" title="Numero invalide">
              &#10007;
            </span>
          )}
          {searchMode === 'name' && !isSearching && (inputValue?.length ?? 0) >= 2 && (
            <span className="siret-lookup__search-icon" title="Recherche par nom">
              &#128269;
            </span>
          )}
        </div>
      </div>

      {/* Suggestions Dropdown (Name Search) */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="siret-lookup__suggestions">
          {suggestions.map((suggestion, index) => (
            <div
              key={`${suggestion.siret}-${index}`}
              className="siret-lookup__suggestion"
              onClick={() => handleSelectSuggestion(suggestion)}
            >
              <div className="siret-lookup__suggestion-name">
                {suggestion.name}
              </div>
              <div className="siret-lookup__suggestion-details">
                <span>{suggestion.siret}</span>
                {suggestion.city && <span> • {suggestion.postal_code} {suggestion.city}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="siret-lookup__error-message">
          {error.message}
        </div>
      )}

      {/* Preview Panel */}
      {showPreview && fields && (
        <div className="siret-lookup__preview">
          <div className="siret-lookup__preview-header">
            <span>Donnees trouvees</span>
            <span className="siret-lookup__preview-source">
              Source: INSEE
            </span>
          </div>

          <div className="siret-lookup__preview-fields">
            {fields.name && (
              <div className="siret-lookup__preview-field">
                <label>Raison sociale</label>
                <span>{fields.name}</span>
              </div>
            )}
            {fields.legal_form && (
              <div className="siret-lookup__preview-field">
                <label>Forme juridique</label>
                <span>{fields.legal_form}</span>
              </div>
            )}
            {fields.address_line1 && (
              <div className="siret-lookup__preview-field">
                <label>Adresse</label>
                <span>
                  {fields.address_line1}
                  {fields.postal_code && fields.city && (
                    <>, {fields.postal_code} {fields.city}</>
                  )}
                </span>
              </div>
            )}
            {fields.naf_code && (
              <div className="siret-lookup__preview-field">
                <label>Code NAF</label>
                <span>{fields.naf_code} - {fields.naf_label}</span>
              </div>
            )}
          </div>

          <div className="siret-lookup__preview-actions">
            <button
              type="button"
              onClick={handleAccept}
              className="siret-lookup__btn siret-lookup__btn--accept"
            >
              Utiliser ces donnees
            </button>
            <button
              type="button"
              onClick={handleReject}
              className="siret-lookup__btn siret-lookup__btn--reject"
            >
              Ignorer
            </button>
          </div>
        </div>
      )}

      <style>{`
        .siret-lookup {
          position: relative;
        }

        .siret-lookup__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .siret-lookup__input {
          width: 100%;
          padding: 0.5rem 2.5rem 0.5rem 0.75rem;
          border: 1px solid #d1d5db;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .siret-lookup__input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .siret-lookup__input--valid {
          border-color: #10b981;
        }

        .siret-lookup__input--invalid {
          border-color: #ef4444;
        }

        .siret-lookup__input--loading {
          background-color: #f9fafb;
        }

        .siret-lookup__status {
          position: absolute;
          right: 0.75rem;
          display: flex;
          align-items: center;
        }

        .siret-lookup__spinner {
          animation: spin 1s linear infinite;
          color: #6b7280;
        }

        .siret-lookup__check {
          color: #10b981;
          font-weight: bold;
        }

        .siret-lookup__error {
          color: #ef4444;
          font-weight: bold;
        }

        .siret-lookup__search-icon {
          color: #6b7280;
          font-size: 0.875rem;
        }

        .siret-lookup__error-message {
          margin-top: 0.25rem;
          font-size: 0.75rem;
          color: #ef4444;
        }

        /* Suggestions Dropdown */
        .siret-lookup__suggestions {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          z-index: 50;
          margin-top: 0.25rem;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
          max-height: 300px;
          overflow-y: auto;
        }

        .siret-lookup__suggestion {
          padding: 0.75rem;
          cursor: pointer;
          border-bottom: 1px solid #f3f4f6;
          transition: background-color 0.15s;
        }

        .siret-lookup__suggestion:last-child {
          border-bottom: none;
        }

        .siret-lookup__suggestion:hover {
          background-color: #f3f4f6;
        }

        .siret-lookup__suggestion-name {
          font-weight: 500;
          font-size: 0.875rem;
          color: #111827;
        }

        .siret-lookup__suggestion-details {
          font-size: 0.75rem;
          color: #6b7280;
          margin-top: 0.25rem;
        }

        .siret-lookup__preview {
          margin-top: 0.5rem;
          padding: 1rem;
          background: #f9fafb;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
        }

        .siret-lookup__preview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
          font-weight: 600;
          font-size: 0.875rem;
        }

        .siret-lookup__preview-source {
          font-size: 0.75rem;
          color: #6b7280;
          font-weight: normal;
        }

        .siret-lookup__preview-fields {
          display: grid;
          gap: 0.5rem;
        }

        .siret-lookup__preview-field {
          display: grid;
          grid-template-columns: 8rem 1fr;
          gap: 0.5rem;
          font-size: 0.875rem;
        }

        .siret-lookup__preview-field label {
          color: #6b7280;
        }

        .siret-lookup__preview-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e5e7eb;
        }

        .siret-lookup__btn {
          padding: 0.5rem 1rem;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.15s;
        }

        .siret-lookup__btn--accept {
          background: #3b82f6;
          color: white;
          border: none;
        }

        .siret-lookup__btn--accept:hover {
          background: #2563eb;
        }

        .siret-lookup__btn--reject {
          background: white;
          color: #374151;
          border: 1px solid #d1d5db;
        }

        .siret-lookup__btn--reject:hover {
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

export default SiretLookup;
