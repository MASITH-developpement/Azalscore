/**
 * AZALS Module - Auto-Enrichment - useSiretLookup Hook
 * =====================================================
 * Hook pour la recherche d'entreprises par SIRET/SIREN.
 */

import { useState, useCallback, useRef } from 'react';
import { lookupSiret, lookupSiren } from '../api';
import type {
  EnrichmentLookupResponse,
  EnrichedContactFields,
  UseLookupOptions,
} from '../types';

// ============================================================================
// VALIDATION
// ============================================================================

/**
 * Valide un numero SIRET (14 chiffres).
 */
export function isValidSiret(value: string): boolean {
  const clean = value.replace(/\s/g, '');
  if (!/^\d{14}$/.test(clean)) return false;

  // Algorithme de Luhn pour validation
  let sum = 0;
  for (let i = 0; i < 14; i++) {
    let digit = parseInt(clean[i], 10);
    if (i % 2 === 0) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
  }
  return sum % 10 === 0;
}

/**
 * Valide un numero SIREN (9 chiffres).
 */
export function isValidSiren(value: string): boolean {
  const clean = value.replace(/\s/g, '');
  if (!/^\d{9}$/.test(clean)) return false;

  // Algorithme de Luhn
  let sum = 0;
  for (let i = 0; i < 9; i++) {
    let digit = parseInt(clean[i], 10);
    if (i % 2 === 1) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
  }
  return sum % 10 === 0;
}

/**
 * Detecte si la valeur est un SIRET ou SIREN.
 */
export function detectType(value: string): 'siret' | 'siren' | null {
  const clean = value.replace(/\s/g, '');
  if (clean.length === 14 && isValidSiret(clean)) return 'siret';
  if (clean.length === 9 && isValidSiren(clean)) return 'siren';
  return null;
}

// ============================================================================
// HOOK
// ============================================================================

export interface UseSiretLookupResult {
  data: EnrichmentLookupResponse | null;
  fields: EnrichedContactFields | null;
  isLoading: boolean;
  error: Error | null;
  historyId: string | null;
  lookup: (value: string) => Promise<void>;
  reset: () => void;
  validationType: 'siret' | 'siren' | null;
}

export function useSiretLookup(options?: UseLookupOptions): UseSiretLookupResult {
  const [data, setData] = useState<EnrichmentLookupResponse | null>(null);
  const [fields, setFields] = useState<EnrichedContactFields | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [historyId, setHistoryId] = useState<string | null>(null);
  const [validationType, setValidationType] = useState<'siret' | 'siren' | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastValueRef = useRef<string>('');

  const lookup = useCallback(
    async (value: string) => {
      const clean = value.replace(/\s/g, '');

      // Debounce
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      // Minimum length check
      const minLen = options?.minLength ?? 9;
      if (clean.length < minLen) {
        return;
      }

      // Avoid duplicate calls
      if (clean === lastValueRef.current) {
        return;
      }

      // Detect type
      const type = detectType(clean);
      if (!type) {
        setError(new Error('Numero invalide. SIRET (14 chiffres) ou SIREN (9 chiffres) attendu.'));
        return;
      }

      setValidationType(type);
      lastValueRef.current = clean;

      const doLookup = async () => {
        setIsLoading(true);
        setError(null);

        try {
          const result = type === 'siret'
            ? await lookupSiret(clean)
            : await lookupSiren(clean);

          setData(result);

          if (result.success && result.enriched_fields) {
            const enrichedFields = result.enriched_fields as EnrichedContactFields;
            setFields(enrichedFields);

            if (result.history_id) {
              setHistoryId(result.history_id);
              options?.onSuccess?.(result);
            }
          } else if (result.error) {
            setError(new Error(result.error));
            options?.onError?.(new Error(result.error));
          }
        } catch (err) {
          const error = err instanceof Error ? err : new Error('Erreur de recherche');
          setError(error);
          options?.onError?.(error);
        } finally {
          setIsLoading(false);
        }
      };

      // Apply debounce
      const debounceMs = options?.debounceMs ?? 300;
      debounceRef.current = setTimeout(doLookup, debounceMs);
    },
    [options]
  );

  const reset = useCallback(() => {
    setData(null);
    setFields(null);
    setError(null);
    setHistoryId(null);
    setValidationType(null);
    lastValueRef.current = '';
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
  }, []);

  return {
    data,
    fields,
    isLoading,
    error,
    historyId,
    lookup,
    reset,
    validationType,
  };
}

export default useSiretLookup;
