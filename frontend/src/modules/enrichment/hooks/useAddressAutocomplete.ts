/**
 * AZALS Module - Auto-Enrichment - useAddressAutocomplete Hook
 * =============================================================
 * Hook pour l'autocomplete d'adresses francaises.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { getAddressSuggestions } from '../api';
import type { AddressSuggestion, UseAddressAutocompleteResult } from '../types';

// ============================================================================
// CONFIGURATION
// ============================================================================

const DEFAULT_DEBOUNCE_MS = 200;
const DEFAULT_MIN_LENGTH = 3;
const DEFAULT_LIMIT = 5;

// ============================================================================
// HOOK
// ============================================================================

export interface UseAddressAutocompleteOptions {
  debounceMs?: number;
  minLength?: number;
  limit?: number;
  onSelect?: (suggestion: AddressSuggestion) => void;
  onError?: (error: Error) => void;
}

export function useAddressAutocomplete(
  options?: UseAddressAutocompleteOptions
): UseAddressAutocompleteResult {
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [selectedSuggestion, setSelectedSuggestion] = useState<AddressSuggestion | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastQueryRef = useRef<string>('');

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const search = useCallback(
    async (query: string) => {
      const trimmedQuery = query.trim();

      // Clear previous debounce
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      // Abort previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Check minimum length
      const minLen = options?.minLength ?? DEFAULT_MIN_LENGTH;
      if (trimmedQuery.length < minLen) {
        setSuggestions([]);
        return;
      }

      // Skip if same query
      if (trimmedQuery === lastQueryRef.current) {
        return;
      }

      const doSearch = async () => {
        lastQueryRef.current = trimmedQuery;
        setIsLoading(true);
        setError(null);

        abortControllerRef.current = new AbortController();

        try {
          const limit = options?.limit ?? DEFAULT_LIMIT;
          const results = await getAddressSuggestions(trimmedQuery, limit);
          // Defensive: always ensure we have an array
          setSuggestions(Array.isArray(results) ? results : []);
        } catch (err) {
          // Ignore abort errors
          if (err instanceof Error && err.name === 'AbortError') {
            return;
          }

          const error = err instanceof Error ? err : new Error('Erreur de recherche');
          setError(error);
          options?.onError?.(error);
          setSuggestions([]);
        } finally {
          setIsLoading(false);
        }
      };

      // Apply debounce
      const debounceMs = options?.debounceMs ?? DEFAULT_DEBOUNCE_MS;
      debounceRef.current = setTimeout(doSearch, debounceMs);
    },
    [options]
  );

  const select = useCallback(
    (suggestion: AddressSuggestion) => {
      setSelectedSuggestion(suggestion);
      setSuggestions([]);
      lastQueryRef.current = suggestion.label;
      options?.onSelect?.(suggestion);
    },
    [options]
  );

  const reset = useCallback(() => {
    setSuggestions([]);
    setError(null);
    setSelectedSuggestion(null);
    lastQueryRef.current = '';

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    suggestions,
    isLoading,
    error,
    search,
    select,
    reset,
  };
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Parse une adresse complete en composants.
 */
export function parseAddress(suggestion: AddressSuggestion): {
  address_line1: string;
  postal_code: string;
  city: string;
  coordinates?: { lat: number; lng: number };
} {
  return {
    address_line1: suggestion.address_line1 || suggestion.label.split(',')[0] || '',
    postal_code: suggestion.postal_code,
    city: suggestion.city,
    coordinates:
      suggestion.latitude && suggestion.longitude
        ? { lat: suggestion.latitude, lng: suggestion.longitude }
        : undefined,
  };
}

/**
 * Formate une adresse pour affichage.
 */
export function formatAddress(suggestion: AddressSuggestion): string {
  const parts: string[] = [];

  if (suggestion.address_line1) {
    parts.push(suggestion.address_line1);
  }

  if (suggestion.postal_code && suggestion.city) {
    parts.push(`${suggestion.postal_code} ${suggestion.city}`);
  } else if (suggestion.city) {
    parts.push(suggestion.city);
  }

  return parts.join(', ');
}

export default useAddressAutocomplete;
