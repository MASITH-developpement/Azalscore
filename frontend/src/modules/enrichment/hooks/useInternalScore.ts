/**
 * AZALS Module - Enrichment - useInternalScore Hook
 * ==================================================
 *
 * Hook pour le scoring interne des clients basé sur leur historique.
 * Fonctionne pour tous les types: particuliers, professionnels, donneurs d'ordre.
 */

import { useState, useCallback, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { getInternalScore } from '../api';
import type { RiskAnalysis } from '../types';

export interface InternalScoreMetrics {
  account_age_days: number;
  total_orders: number;
  total_invoices: number;
  paid_invoices: number;
  overdue_invoices: number;
  total_invoiced: number;
  total_paid: number;
  outstanding: number;
}

export interface InternalScoreResult extends RiskAnalysis {
  customer_name?: string;
  metrics?: InternalScoreMetrics;
  _source?: string;
}

export interface UseInternalScoreResult {
  score: InternalScoreResult | null;
  isLoading: boolean;
  error: string | null;
  historyId: string | null;
  analyze: (customerId: string) => void;
  reset: () => void;
}

export function useInternalScore(): UseInternalScoreResult {
  const [score, setScore] = useState<InternalScoreResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [historyId, setHistoryId] = useState<string | null>(null);

  // Track analyzed customer to prevent duplicate requests
  const analyzedCustomerRef = useRef<string | null>(null);
  const isPendingRef = useRef(false);

  const mutation = useMutation({
    mutationFn: async (customerId: string) => {
      const result = await getInternalScore(customerId);
      return result;
    },
    onSuccess: (data) => {
      isPendingRef.current = false;
      if (data.success && data.enriched_fields?._internal_scoring) {
        const internalScore = data.enriched_fields._internal_scoring as InternalScoreResult;
        setScore(internalScore);
        setHistoryId(data.history_id || null);
        setError(null);
      } else if (data.error) {
        setError(data.error);
        setScore(null);
      }
    },
    onError: (err: Error) => {
      isPendingRef.current = false;
      setError(err.message || 'Erreur lors du calcul du score');
      setScore(null);
    },
  });

  // Stable analyze function that won't change between renders
  const analyze = useCallback((customerId: string) => {
    // Prevent duplicate requests for same customer or while loading
    if (!customerId || isPendingRef.current || analyzedCustomerRef.current === customerId) {
      return;
    }
    // CRITICAL: Set flags BEFORE calling async mutation
    isPendingRef.current = true;
    analyzedCustomerRef.current = customerId;
    mutation.mutate(customerId);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const reset = useCallback(() => {
    setScore(null);
    setError(null);
    setHistoryId(null);
    analyzedCustomerRef.current = null;
    isPendingRef.current = false;
    mutation.reset();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    score,
    isLoading: mutation.isPending,
    error,
    historyId,
    analyze,
    reset,
  };
}

export default useInternalScore;
