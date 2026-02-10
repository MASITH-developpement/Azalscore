/**
 * AZALS Module - Auto-Enrichment - useBarcodeLookup Hook
 * =======================================================
 * Hook pour la recherche de produits par code-barres.
 */

import { useState, useCallback, useRef } from 'react';
import { lookupBarcode } from '../api';
import type {
  EnrichmentLookupResponse,
  EnrichedProductFields,
  UseLookupOptions,
} from '../types';

// ============================================================================
// VALIDATION
// ============================================================================

/**
 * Types de codes-barres supportes.
 */
export type BarcodeType = 'EAN-13' | 'EAN-8' | 'UPC-A' | 'UPC-E' | 'unknown';

/**
 * Detecte le type de code-barres.
 */
export function detectBarcodeType(value: string): BarcodeType {
  const clean = value.replace(/\s/g, '');

  if (!/^\d+$/.test(clean)) return 'unknown';

  switch (clean.length) {
    case 13:
      return 'EAN-13';
    case 12:
      return 'UPC-A';
    case 8:
      return clean.startsWith('0') || clean.startsWith('1')
        ? 'UPC-E'
        : 'EAN-8';
    default:
      return 'unknown';
  }
}

/**
 * Valide un code-barres (verification du checksum).
 */
export function isValidBarcode(value: string): boolean {
  const clean = value.replace(/\s/g, '');
  const type = detectBarcodeType(clean);

  if (type === 'unknown') return false;

  // Validation checksum pour EAN-13 et EAN-8
  if (type === 'EAN-13' || type === 'EAN-8') {
    const digits = clean.split('').map(Number);
    const checkDigit = digits.pop()!;

    let sum = 0;
    const multipliers = type === 'EAN-13' ? [1, 3] : [3, 1];

    for (let i = 0; i < digits.length; i++) {
      sum += digits[i] * multipliers[i % 2];
    }

    const calculatedCheck = (10 - (sum % 10)) % 10;
    return calculatedCheck === checkDigit;
  }

  // Pour UPC-A/E, validation simplifiee (longueur uniquement)
  return true;
}

/**
 * Formate un code-barres pour affichage.
 */
export function formatBarcode(value: string): string {
  const clean = value.replace(/\s/g, '');
  const type = detectBarcodeType(clean);

  switch (type) {
    case 'EAN-13':
      // Format: X XXXXXX XXXXXX
      return `${clean.slice(0, 1)} ${clean.slice(1, 7)} ${clean.slice(7)}`;
    case 'EAN-8':
      // Format: XXXX XXXX
      return `${clean.slice(0, 4)} ${clean.slice(4)}`;
    case 'UPC-A':
      // Format: X XXXXX XXXXX X
      return `${clean.slice(0, 1)} ${clean.slice(1, 6)} ${clean.slice(6, 11)} ${clean.slice(11)}`;
    default:
      return clean;
  }
}

// ============================================================================
// HOOK
// ============================================================================

export interface UseBarcodeLookupResult {
  data: EnrichmentLookupResponse | null;
  fields: EnrichedProductFields | null;
  isLoading: boolean;
  error: Error | null;
  historyId: string | null;
  barcodeType: BarcodeType;
  lookup: (value: string) => Promise<void>;
  reset: () => void;
}

export function useBarcodeLookup(options?: UseLookupOptions): UseBarcodeLookupResult {
  const [data, setData] = useState<EnrichmentLookupResponse | null>(null);
  const [fields, setFields] = useState<EnrichedProductFields | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [historyId, setHistoryId] = useState<string | null>(null);
  const [barcodeType, setBarcodeType] = useState<BarcodeType>('unknown');

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastValueRef = useRef<string>('');

  const lookup = useCallback(
    async (value: string) => {
      const clean = value.replace(/\s/g, '');

      // Clear debounce
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }

      // Minimum length
      const minLen = options?.minLength ?? 8;
      if (clean.length < minLen) {
        return;
      }

      // Skip duplicates
      if (clean === lastValueRef.current) {
        return;
      }

      // Detect type
      const type = detectBarcodeType(clean);
      setBarcodeType(type);

      if (type === 'unknown') {
        setError(new Error('Code-barres invalide. Formats acceptes: EAN-13, EAN-8, UPC-A, UPC-E'));
        return;
      }

      // Validate
      if (!isValidBarcode(clean)) {
        setError(new Error('Code-barres invalide (checksum incorrect)'));
        return;
      }

      lastValueRef.current = clean;

      const doLookup = async () => {
        setIsLoading(true);
        setError(null);

        try {
          const result = await lookupBarcode(clean);
          setData(result);

          if (result.success && result.enriched_fields) {
            const productFields = result.enriched_fields as EnrichedProductFields;
            setFields(productFields);

            if (result.history_id) {
              setHistoryId(result.history_id);
              options?.onSuccess?.(result);
            }
          } else if (result.error) {
            // Produit non trouve n'est pas une erreur fatale
            if (result.error.includes('not found') || result.error.includes('introuvable')) {
              setError(new Error('Produit non trouve dans les bases de donnees'));
            } else {
              setError(new Error(result.error));
              options?.onError?.(new Error(result.error));
            }
          }
        } catch (err) {
          const error = err instanceof Error ? err : new Error('Erreur de recherche');
          setError(error);
          options?.onError?.(error);
        } finally {
          setIsLoading(false);
        }
      };

      // Debounce
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
    setBarcodeType('unknown');
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
    barcodeType,
    lookup,
    reset,
  };
}

export default useBarcodeLookup;
