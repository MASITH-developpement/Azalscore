/**
 * AZALS Module - Auto-Enrichment - Hooks Index
 * =============================================
 * Export de tous les hooks d'enrichissement.
 */

export { useSiretLookup, isValidSiret, isValidSiren, detectType } from './useSiretLookup';
export type { UseSiretLookupResult } from './useSiretLookup';

export {
  useAddressAutocomplete,
  parseAddress,
  formatAddress,
} from './useAddressAutocomplete';
export type { UseAddressAutocompleteOptions } from './useAddressAutocomplete';

export {
  useBarcodeLookup,
  detectBarcodeType,
  isValidBarcode,
  formatBarcode,
} from './useBarcodeLookup';
export type { UseBarcodeLookupResult, BarcodeType } from './useBarcodeLookup';

export { useRiskAnalysis } from './useRiskAnalysis';
export type { UseRiskAnalysisResult, UseRiskAnalysisOptions } from './useRiskAnalysis';

export { useInternalScore } from './useInternalScore';
export type {
  UseInternalScoreResult,
  InternalScoreResult,
  InternalScoreMetrics,
} from './useInternalScore';
