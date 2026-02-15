/**
 * AZALSCORE Module - INVENTORY - ProductAutocomplete Component
 * =============================================================
 * Composant de recherche de produit par code/nom avec autocomplete.
 * Remplit automatiquement les champs d'une ligne de document.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { searchProducts } from '../api';
import type { ProductSuggestion, EnrichedDocumentLineFields } from '../types';

// ============================================================================
// TYPES
// ============================================================================

export interface ProductAutocompleteProps {
  value?: string;
  onChange?: (value: string) => void;
  onSelect?: (fields: EnrichedDocumentLineFields) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  minLength?: number;
  debounceMs?: number;
  categoryId?: string;
  defaultTaxRate?: number;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function ProductAutocomplete({
  value = '',
  onChange,
  onSelect,
  placeholder = 'Rechercher un produit...',
  disabled = false,
  className = '',
  minLength = 2,
  debounceMs = 300,
  categoryId,
  defaultTaxRate = 20.0,
}: ProductAutocompleteProps): JSX.Element {
  const [inputValue, setInputValue] = useState(value ?? '');
  const [suggestions, setSuggestions] = useState<ProductSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const lastSearchRef = useRef<string>('');
  const isUserTypingRef = useRef(false);
  const lastInputValueRef = useRef(inputValue);

  // Sync with external value
  useEffect(() => {
    if (isUserTypingRef.current) {
      return;
    }
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
      isUserTypingRef.current = true;

      setInputValue(newValue);
      lastInputValueRef.current = newValue;
      onChange?.(newValue);
      setHighlightedIndex(-1);

      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }

      if (newValue.length < minLength) {
        setSuggestions([]);
        setShowSuggestions(false);
        lastSearchRef.current = '';
        setTimeout(() => { isUserTypingRef.current = false; }, 50);
        return;
      }

      if (newValue === lastSearchRef.current) {
        setTimeout(() => { isUserTypingRef.current = false; }, 50);
        return;
      }

      setIsSearching(true);
      searchTimeoutRef.current = setTimeout(async () => {
        try {
          lastSearchRef.current = newValue;
          const results = await searchProducts(newValue, 10, categoryId);
          const validResults = Array.isArray(results) ? results : [];
          if (lastSearchRef.current === newValue) {
            setSuggestions(validResults);
            setShowSuggestions(validResults.length > 0);
          }
        } catch (err) {
          console.error('Error searching products:', err);
          if (lastSearchRef.current === newValue) {
            setSuggestions([]);
            setShowSuggestions(false);
          }
        } finally {
          if (lastSearchRef.current === newValue) {
            setIsSearching(false);
          }
          isUserTypingRef.current = false;
        }
      }, debounceMs);
    },
    [onChange, minLength, debounceMs, categoryId]
  );

  const handleSelectSuggestion = useCallback((suggestion: ProductSuggestion) => {
    isUserTypingRef.current = true;

    // Update input with product name
    setInputValue(suggestion.name);
    lastInputValueRef.current = suggestion.name;
    onChange?.(suggestion.name);
    setShowSuggestions(false);
    setSuggestions([]);
    lastSearchRef.current = '';

    // Create enriched fields for document line
    const enrichedFields: EnrichedDocumentLineFields = {
      product_id: suggestion.id,
      product_code: suggestion.code,
      description: suggestion.name,
      unit: suggestion.unit,
      unit_price: suggestion.sale_price ?? 0,
      tax_rate: defaultTaxRate,
    };

    onSelect?.(enrichedFields);

    setTimeout(() => { isUserTypingRef.current = false; }, 100);
  }, [onChange, onSelect, defaultTaxRate]);

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

  const formatPrice = (price?: number, currency?: string) => {
    if (price === undefined || price === null) return '-';
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: currency || 'EUR',
    }).format(price);
  };

  return (
    <div className={`product-autocomplete ${className}`} ref={wrapperRef}>
      <div className="product-autocomplete__input-wrapper">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          placeholder={placeholder}
          disabled={disabled}
          className={`product-autocomplete__input ${isSearching ? 'product-autocomplete__input--loading' : ''}`}
          autoComplete="off"
        />

        {/* Status Indicator */}
        <div className="product-autocomplete__status">
          {isSearching && (
            <span className="product-autocomplete__spinner" title="Recherche en cours...">
              &#8635;
            </span>
          )}
          {!isSearching && (inputValue?.length ?? 0) >= minLength && (
            <span className="product-autocomplete__search-icon">
              &#128269;
            </span>
          )}
        </div>
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="product-autocomplete__suggestions">
          {suggestions.map((suggestion, index) => (
            <div
              key={suggestion.id}
              className={`product-autocomplete__suggestion ${
                index === highlightedIndex ? 'product-autocomplete__suggestion--highlighted' : ''
              }`}
              onClick={() => handleSelectSuggestion(suggestion)}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              <div className="product-autocomplete__suggestion-main">
                <span className="product-autocomplete__suggestion-code">
                  {suggestion.code}
                </span>
                <span className="product-autocomplete__suggestion-name">
                  {suggestion.name}
                </span>
              </div>
              <div className="product-autocomplete__suggestion-details">
                {suggestion.category_name && (
                  <span className="product-autocomplete__suggestion-category">
                    {suggestion.category_name}
                  </span>
                )}
                <span className="product-autocomplete__suggestion-price">
                  {formatPrice(suggestion.sale_price, suggestion.currency)}
                </span>
                <span className="product-autocomplete__suggestion-unit">
                  / {suggestion.unit}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <style>{`
        .product-autocomplete {
          position: relative;
          width: 100%;
        }

        .product-autocomplete__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .product-autocomplete__input {
          width: 100%;
          padding: 0.5rem 2.5rem 0.5rem 0.75rem;
          border: 1px solid #d1d5db;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .product-autocomplete__input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .product-autocomplete__input--loading {
          background-color: #f9fafb;
        }

        .product-autocomplete__input:disabled {
          background-color: #f3f4f6;
          cursor: not-allowed;
        }

        .product-autocomplete__status {
          position: absolute;
          right: 0.75rem;
          display: flex;
          align-items: center;
          pointer-events: none;
        }

        .product-autocomplete__spinner {
          animation: product-spin 1s linear infinite;
          color: #3b82f6;
          font-size: 1rem;
        }

        .product-autocomplete__search-icon {
          color: #9ca3af;
          font-size: 0.875rem;
        }

        /* Suggestions Dropdown */
        .product-autocomplete__suggestions {
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

        .product-autocomplete__suggestion {
          padding: 0.75rem 1rem;
          cursor: pointer;
          border-bottom: 1px solid #f3f4f6;
          transition: background-color 0.1s;
        }

        .product-autocomplete__suggestion:last-child {
          border-bottom: none;
        }

        .product-autocomplete__suggestion:hover,
        .product-autocomplete__suggestion--highlighted {
          background-color: #eff6ff;
        }

        .product-autocomplete__suggestion-main {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.25rem;
        }

        .product-autocomplete__suggestion-code {
          font-family: monospace;
          font-size: 0.75rem;
          font-weight: 600;
          color: #4f46e5;
          background: #eef2ff;
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
        }

        .product-autocomplete__suggestion-name {
          font-weight: 500;
          font-size: 0.875rem;
          color: #111827;
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .product-autocomplete__suggestion-details {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 0.75rem;
          color: #6b7280;
        }

        .product-autocomplete__suggestion-category {
          background: #f3f4f6;
          padding: 0.125rem 0.375rem;
          border-radius: 0.25rem;
        }

        .product-autocomplete__suggestion-price {
          font-weight: 600;
          color: #059669;
        }

        .product-autocomplete__suggestion-unit {
          color: #9ca3af;
        }

        @keyframes product-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default ProductAutocomplete;
