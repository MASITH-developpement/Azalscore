/**
 * AZALS Module - Auto-Enrichment - CompanyAutocomplete Component
 * ===============================================================
 * Composant de recherche d'entreprise par nom avec autocomplete.
 * Remplit automatiquement tous les champs du formulaire.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { searchCompanyByName, lookupSiret } from '../api';
import type { CompanySuggestion, EnrichedContactFields, RiskData } from '../types';

// ============================================================================
// TYPES
// ============================================================================

export interface CompanyAutocompleteProps {
  value?: string;
  onChange?: (value: string) => void;
  onSelect?: (fields: EnrichedContactFields) => void;
  /** Callback appelé automatiquement dès que les données de risque BODACC arrivent */
  onRiskData?: (riskData: RiskData | null) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  minLength?: number;
  debounceMs?: number;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function CompanyAutocomplete({
  value = '',
  onChange,
  onSelect,
  onRiskData,
  placeholder = 'Rechercher une entreprise...',
  disabled = false,
  className = '',
  minLength = 2,
  debounceMs = 300,
}: CompanyAutocompleteProps): JSX.Element {
  // Ensure inputValue is always a string (value could be undefined even with default)
  const [inputValue, setInputValue] = useState(value ?? '');
  const [suggestions, setSuggestions] = useState<CompanySuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const lastSearchRef = useRef<string>('');

  // Track if we're the source of the change to avoid race conditions
  const isUserTypingRef = useRef(false);
  const lastInputValueRef = useRef(inputValue);

  // Sync with external value (only when value truly comes from parent, not from our typing)
  useEffect(() => {
    // If user is typing, ignore external value updates (they're just echoes of our onChange)
    if (isUserTypingRef.current) {
      return;
    }
    // Only sync if value is different from what we have
    if (value !== lastInputValueRef.current) {
      setInputValue(value);
      lastInputValueRef.current = value;
    }
  }, [value]);

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

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;

      // Mark that user is typing to prevent external value sync race conditions
      isUserTypingRef.current = true;

      setInputValue(newValue);
      lastInputValueRef.current = newValue;
      onChange?.(newValue);
      setHighlightedIndex(-1);

      // Clear previous timeout
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }

      // Check minimum length
      if (newValue.length < minLength) {
        setSuggestions([]);
        setShowSuggestions(false);
        lastSearchRef.current = '';
        // Reset typing flag after a short delay
        setTimeout(() => { isUserTypingRef.current = false; }, 50);
        return;
      }

      // Skip if same search
      if (newValue === lastSearchRef.current) {
        setTimeout(() => { isUserTypingRef.current = false; }, 50);
        return;
      }

      // Debounced search
      setIsSearching(true);
      searchTimeoutRef.current = setTimeout(async () => {
        try {
          lastSearchRef.current = newValue;
          const results = await searchCompanyByName(newValue);
          // Defensive: ensure results is always an array
          const validResults = Array.isArray(results) ? results : [];
          // Only update if this is still the current search
          if (lastSearchRef.current === newValue) {
            setSuggestions(validResults);
            setShowSuggestions(validResults.length > 0);
          }
        } catch (err) {
          console.error('Error searching companies:', err);
          if (lastSearchRef.current === newValue) {
            setSuggestions([]);
            setShowSuggestions(false);
          }
        } finally {
          if (lastSearchRef.current === newValue) {
            setIsSearching(false);
          }
          // Reset typing flag after search completes
          isUserTypingRef.current = false;
        }
      }, debounceMs);
    },
    [onChange, minLength, debounceMs]
  );

  const handleSelectSuggestion = useCallback(async (suggestion: CompanySuggestion) => {
    // Mark that we're updating to prevent race conditions
    isUserTypingRef.current = true;

    // Update input with company name
    setInputValue(suggestion.name);
    lastInputValueRef.current = suggestion.name;
    onChange?.(suggestion.name);
    setShowSuggestions(false);
    setSuggestions([]);
    lastSearchRef.current = '';

    // Faire un lookup SIRET pour obtenir les données complètes (INSEE + BODACC)
    if (suggestion.siret) {
      try {
        const response = await lookupSiret(suggestion.siret);
        const fields = response?.enriched_fields as EnrichedContactFields;
        if (fields) {
          // Appeler onSelect avec les données complètes INSEE + BODACC
          onSelect?.(fields);

          // Envoyer les données de risque séparément
          if (onRiskData) {
            if (fields._bodacc_risk_level || fields._risk_level) {
              onRiskData({
                level: fields._bodacc_risk_level || fields._risk_level,
                label: fields._bodacc_risk_label || fields._risk_label,
                reason: fields._bodacc_risk_reason || fields._risk_reason,
                score: fields._bodacc_risk_score ?? fields._risk_score,
                alerts: fields._bodacc_critical_alerts || [],
                sources: fields._sources || [],
              });
            } else {
              onRiskData(null);
            }
          }
        } else {
          // Fallback: données basiques de la suggestion si le lookup échoue
          const basicFields: EnrichedContactFields = {
            name: suggestion.name,
            company_name: suggestion.name,
            siret: suggestion.siret,
            siren: suggestion.siren,
            address: suggestion.address,
            address_line1: suggestion.address,
            city: suggestion.city,
            postal_code: suggestion.postal_code,
          };
          onSelect?.(basicFields);
          onRiskData?.(null);
        }
      } catch (err) {
        console.error('Error fetching company data:', err);
        // Fallback: données basiques de la suggestion
        const basicFields: EnrichedContactFields = {
          name: suggestion.name,
          company_name: suggestion.name,
          siret: suggestion.siret,
          siren: suggestion.siren,
          address: suggestion.address,
          address_line1: suggestion.address,
          city: suggestion.city,
          postal_code: suggestion.postal_code,
        };
        onSelect?.(basicFields);
        onRiskData?.(null);
      }
    } else {
      // Pas de SIRET, utiliser les données basiques
      const basicFields: EnrichedContactFields = {
        name: suggestion.name,
        company_name: suggestion.name,
        siret: suggestion.siret,
        siren: suggestion.siren,
        address: suggestion.address,
        address_line1: suggestion.address,
        city: suggestion.city,
        postal_code: suggestion.postal_code,
      };
      onSelect?.(basicFields);
      onRiskData?.(null);
    }

    // Reset typing flag after a short delay
    setTimeout(() => { isUserTypingRef.current = false; }, 100);
  }, [onChange, onSelect, onRiskData]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
          handleSelectSuggestion(suggestions[highlightedIndex]);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setHighlightedIndex(-1);
        break;
    }
  }, [showSuggestions, suggestions, highlightedIndex, handleSelectSuggestion]);

  const handleFocus = useCallback(() => {
    if (suggestions.length > 0) {
      setShowSuggestions(true);
    }
  }, [suggestions]);

  return (
    <div className={`company-autocomplete ${className}`} ref={wrapperRef}>
      <div className="company-autocomplete__input-wrapper">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          placeholder={placeholder}
          disabled={disabled}
          className={`company-autocomplete__input ${isSearching ? 'company-autocomplete__input--loading' : ''}`}
          autoComplete="off"
        />

        {/* Status Indicator */}
        <div className="company-autocomplete__status">
          {isSearching && (
            <span className="company-autocomplete__spinner" title="Recherche en cours...">
              &#8635;
            </span>
          )}
          {!isSearching && (inputValue?.length ?? 0) >= minLength && (
            <span className="company-autocomplete__search-icon">
              &#128269;
            </span>
          )}
        </div>
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="company-autocomplete__suggestions">
          {suggestions.map((suggestion, index) => (
            <div
              key={`${suggestion.siret}-${index}`}
              className={`company-autocomplete__suggestion ${
                index === highlightedIndex ? 'company-autocomplete__suggestion--highlighted' : ''
              }`}
              onClick={() => handleSelectSuggestion(suggestion)}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              <div className="company-autocomplete__suggestion-name">
                {suggestion.name}
              </div>
              <div className="company-autocomplete__suggestion-details">
                <span className="company-autocomplete__suggestion-siret">
                  {suggestion.siret}
                </span>
                {suggestion.city && (
                  <span className="company-autocomplete__suggestion-location">
                    {suggestion.postal_code} {suggestion.city}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
        .company-autocomplete {
          position: relative;
          width: 100%;
        }

        .company-autocomplete__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .company-autocomplete__input {
          width: 100%;
          padding: 0.5rem 2.5rem 0.5rem 0.75rem;
          border: 1px solid #d1d5db;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .company-autocomplete__input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .company-autocomplete__input--loading {
          background-color: #f9fafb;
        }

        .company-autocomplete__input:disabled {
          background-color: #f3f4f6;
          cursor: not-allowed;
        }

        .company-autocomplete__status {
          position: absolute;
          right: 0.75rem;
          display: flex;
          align-items: center;
          pointer-events: none;
        }

        .company-autocomplete__spinner {
          animation: company-spin 1s linear infinite;
          color: #3b82f6;
          font-size: 1rem;
        }

        .company-autocomplete__search-icon {
          color: #9ca3af;
          font-size: 0.875rem;
        }

        /* Suggestions Dropdown */
        .company-autocomplete__suggestions {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          z-index: 50;
          margin-top: 0.25rem;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
          max-height: 300px;
          overflow-y: auto;
        }

        .company-autocomplete__suggestion {
          padding: 0.75rem 1rem;
          cursor: pointer;
          border-bottom: 1px solid #f3f4f6;
          transition: background-color 0.1s;
        }

        .company-autocomplete__suggestion:last-child {
          border-bottom: none;
        }

        .company-autocomplete__suggestion:hover,
        .company-autocomplete__suggestion--highlighted {
          background-color: #eff6ff;
        }

        .company-autocomplete__suggestion-name {
          font-weight: 600;
          font-size: 0.875rem;
          color: #111827;
          margin-bottom: 0.25rem;
        }

        .company-autocomplete__suggestion-details {
          display: flex;
          gap: 1rem;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .company-autocomplete__suggestion-siret {
          font-family: monospace;
          background: #f3f4f6;
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
        }

        .company-autocomplete__suggestion-location {
          color: #9ca3af;
        }

        @keyframes company-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default CompanyAutocomplete;
