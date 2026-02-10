/**
 * AZALS Module - Auto-Enrichment - useRiskAnalysis Hook
 * ======================================================
 * Hook pour l'analyse de risque entreprise via Pappers.
 *
 * IMPORTANT: Ces donnees sont confidentielles.
 * Acces restreint par capability 'enrichment.risk_analysis'.
 */

import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { analyzeRisk } from '../api';
import type { RiskAnalysis, EnrichedRiskFields } from '../types';

export interface UseRiskAnalysisOptions {
  onSuccess?: (analysis: RiskAnalysis) => void;
  onError?: (error: Error) => void;
}

export interface UseRiskAnalysisResult {
  analysis: RiskAnalysis | null;
  enrichedFields: EnrichedRiskFields | null;
  isLoading: boolean;
  error: string | null;
  historyId: string | null;
  cached: boolean;
  analyze: (identifier: string) => Promise<void>;
  reset: () => void;
}

export function useRiskAnalysis(options?: UseRiskAnalysisOptions): UseRiskAnalysisResult {
  const [analysis, setAnalysis] = useState<RiskAnalysis | null>(null);
  const [enrichedFields, setEnrichedFields] = useState<EnrichedRiskFields | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [historyId, setHistoryId] = useState<string | null>(null);
  const [cached, setCached] = useState(false);

  const mutation = useMutation({
    mutationFn: analyzeRisk,
    onSuccess: (response) => {
      if (response.success) {
        const fields = response.enriched_fields as EnrichedRiskFields;
        const riskData = fields._pappers_risk_analysis || null;

        setEnrichedFields(fields);
        setAnalysis(riskData);
        setHistoryId(response.history_id || null);
        setCached(response.cached);
        setError(null);

        if (riskData && options?.onSuccess) {
          options.onSuccess(riskData);
        }
      } else {
        setError(response.error || 'Analyse de risque echouee');
        setAnalysis(null);
        setEnrichedFields(null);
      }
    },
    onError: (err: Error) => {
      const message = err.message || 'Erreur lors de l\'analyse';
      setError(message);
      setAnalysis(null);
      setEnrichedFields(null);
      options?.onError?.(err);
    },
  });

  const analyze = useCallback(async (identifier: string) => {
    const cleaned = identifier.replace(/\s/g, '');
    if (!cleaned || (cleaned.length !== 9 && cleaned.length !== 14)) {
      setError('SIREN (9 chiffres) ou SIRET (14 chiffres) requis');
      return;
    }
    setError(null);
    await mutation.mutateAsync(cleaned);
  }, [mutation]);

  const reset = useCallback(() => {
    setAnalysis(null);
    setEnrichedFields(null);
    setError(null);
    setHistoryId(null);
    setCached(false);
  }, []);

  return {
    analysis,
    enrichedFields,
    isLoading: mutation.isPending,
    error,
    historyId,
    cached,
    analyze,
    reset,
  };
}

export default useRiskAnalysis;
