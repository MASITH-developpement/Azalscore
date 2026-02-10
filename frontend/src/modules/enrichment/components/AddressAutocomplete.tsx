/**
 * AZALS Module - Auto-Enrichment - AddressAutocomplete Component
 * ===============================================================
 * Composant d'autocomplete d'adresses francaises.
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useAddressAutocomplete } from '../hooks';
import type { AddressSuggestion, AddressAutocompleteProps } from '../types';

// ============================================================================
// COMPONENT
// ============================================================================

export function AddressAutocomplete({
  value = '',
  onChange,
  onSelect,
  placeholder = "Rechercher une adresse...",
  disabled = false,
  className = '',
}: AddressAutocompleteProps): JSX.Element {
  const [inputValue, setInputValue] = useState(value ?? '');
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const hookResult = useAddressAutocomplete({
      debounceMs: 200,
      minLength: 3,
      limit: 5,
      onSelect: (suggestion) => {
        setInputValue(suggestion.label);
        setIsOpen(false);
        onSelect?.(suggestion);
      },
    });

  // Defensive: ensure suggestions is always an array
  const suggestions = hookResult?.suggestions ?? [];
  const { isLoading, error, search, select, reset } = hookResult ?? {
    isLoading: false,
    error: null,
    search: async () => {},
    select: () => {},
    reset: () => {},
  };

  // Sync with external value
  useEffect(() => {
    if (value !== inputValue) {
      setInputValue(value);
    }
  }, [value]);

  // Open dropdown when suggestions available
  useEffect(() => {
    if (suggestions.length > 0) {
      setIsOpen(true);
      setHighlightedIndex(-1);
    }
  }, [suggestions]);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setInputValue(newValue);
      onChange?.(newValue);
      search(newValue);
    },
    [onChange, search]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (!isOpen || suggestions.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev < suggestions.length - 1 ? prev + 1 : 0
          );
          break;

        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex((prev) =>
            prev > 0 ? prev - 1 : suggestions.length - 1
          );
          break;

        case 'Enter':
          e.preventDefault();
          if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
            select(suggestions[highlightedIndex]);
          }
          break;

        case 'Escape':
          setIsOpen(false);
          setHighlightedIndex(-1);
          break;
      }
    },
    [isOpen, suggestions, highlightedIndex, select]
  );

  const handleSuggestionClick = useCallback(
    (suggestion: AddressSuggestion) => {
      select(suggestion);
    },
    [select]
  );

  const handleFocus = useCallback(() => {
    if (suggestions.length > 0) {
      setIsOpen(true);
    }
  }, [suggestions]);

  const handleClear = useCallback(() => {
    setInputValue('');
    onChange?.('');
    reset();
    inputRef.current?.focus();
  }, [onChange, reset]);

  return (
    <div
      ref={wrapperRef}
      className={`address-autocomplete ${className}`}
    >
      {/* Input */}
      <div className="address-autocomplete__input-wrapper">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          placeholder={placeholder}
          disabled={disabled}
          className="address-autocomplete__input"
          autoComplete="off"
          role="combobox"
          aria-expanded={isOpen}
          aria-controls="address-suggestions"
          aria-autocomplete="list"
        />

        {/* Loading / Clear */}
        <div className="address-autocomplete__actions">
          {isLoading && (
            <span className="address-autocomplete__spinner">&#8635;</span>
          )}
          {inputValue && !isLoading && (
            <button
              type="button"
              onClick={handleClear}
              className="address-autocomplete__clear"
              title="Effacer"
            >
              &#10005;
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="address-autocomplete__error">
          {error.message}
        </div>
      )}

      {/* Suggestions Dropdown */}
      {isOpen && suggestions.length > 0 && (
        <ul
          id="address-suggestions"
          className="address-autocomplete__dropdown"
          role="listbox"
        >
          {suggestions.map((suggestion, index) => (
            <li
              key={`${suggestion.label}-${index}`}
              role="option"
              aria-selected={index === highlightedIndex}
              className={`
                address-autocomplete__suggestion
                ${index === highlightedIndex ? 'address-autocomplete__suggestion--highlighted' : ''}
              `}
              onClick={() => handleSuggestionClick(suggestion)}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              <div className="address-autocomplete__suggestion-main">
                {suggestion.address_line1 || suggestion.label.split(',')[0]}
              </div>
              <div className="address-autocomplete__suggestion-sub">
                {suggestion.postal_code} {suggestion.city}
                {suggestion.context && (
                  <span className="address-autocomplete__suggestion-context">
                    {' '}- {suggestion.context}
                  </span>
                )}
              </div>
              {(suggestion.score ?? 0) > 0.8 && (
                <span className="address-autocomplete__suggestion-badge">
                  Exact
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      <style>{`
        .address-autocomplete {
          position: relative;
          width: 100%;
        }

        .address-autocomplete__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .address-autocomplete__input {
          width: 100%;
          padding: 0.5rem 2.5rem 0.5rem 0.75rem;
          border: 1px solid #d1d5db;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          transition: border-color 0.15s, box-shadow 0.15s;
        }

        .address-autocomplete__input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .address-autocomplete__input:disabled {
          background-color: #f3f4f6;
          cursor: not-allowed;
        }

        .address-autocomplete__actions {
          position: absolute;
          right: 0.5rem;
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }

        .address-autocomplete__spinner {
          animation: spin 1s linear infinite;
          color: #6b7280;
          font-size: 1rem;
        }

        .address-autocomplete__clear {
          background: none;
          border: none;
          padding: 0.25rem;
          cursor: pointer;
          color: #9ca3af;
          font-size: 0.75rem;
          line-height: 1;
          border-radius: 50%;
          transition: background-color 0.15s, color 0.15s;
        }

        .address-autocomplete__clear:hover {
          background: #f3f4f6;
          color: #374151;
        }

        .address-autocomplete__error {
          margin-top: 0.25rem;
          font-size: 0.75rem;
          color: #ef4444;
        }

        .address-autocomplete__dropdown {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          z-index: 50;
          margin-top: 0.25rem;
          padding: 0.25rem 0;
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1),
                      0 4px 6px -2px rgba(0, 0, 0, 0.05);
          list-style: none;
          max-height: 20rem;
          overflow-y: auto;
        }

        .address-autocomplete__suggestion {
          position: relative;
          padding: 0.625rem 0.75rem;
          cursor: pointer;
          transition: background-color 0.15s;
        }

        .address-autocomplete__suggestion:hover,
        .address-autocomplete__suggestion--highlighted {
          background: #f3f4f6;
        }

        .address-autocomplete__suggestion-main {
          font-size: 0.875rem;
          font-weight: 500;
          color: #111827;
        }

        .address-autocomplete__suggestion-sub {
          font-size: 0.75rem;
          color: #6b7280;
          margin-top: 0.125rem;
        }

        .address-autocomplete__suggestion-context {
          color: #9ca3af;
        }

        .address-autocomplete__suggestion-badge {
          position: absolute;
          right: 0.75rem;
          top: 50%;
          transform: translateY(-50%);
          padding: 0.125rem 0.375rem;
          font-size: 0.625rem;
          font-weight: 600;
          text-transform: uppercase;
          background: #dbeafe;
          color: #1d4ed8;
          border-radius: 0.25rem;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default AddressAutocomplete;
