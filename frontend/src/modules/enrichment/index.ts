/**
 * AZALS Module - Auto-Enrichment
 * ===============================
 * Module d'auto-enrichissement des formulaires via APIs externes.
 *
 * APIs gratuites supportees:
 * - SIRENE/INSEE: Lookup entreprises francaises (SIRET/SIREN)
 * - API Adresse gouv.fr: Autocomplete adresses francaises
 * - Open Food Facts: Produits alimentaires par code-barres
 * - Open Beauty Facts: Produits cosmetiques
 * - Open Pet Food Facts: Produits animaliers
 *
 * Usage:
 * ```tsx
 * import { SiretLookup, AddressAutocomplete, BarcodeLookup } from '@/modules/enrichment';
 *
 * // Dans un formulaire Contact
 * <SiretLookup
 *   value={siret}
 *   onEnrich={(fields) => {
 *     form.setValue('name', fields.name);
 *     form.setValue('address', fields.address_line1);
 *   }}
 * />
 *
 * // Autocomplete adresse
 * <AddressAutocomplete
 *   value={address}
 *   onSelect={(suggestion) => {
 *     form.setValue('address', suggestion.address_line1);
 *     form.setValue('city', suggestion.city);
 *     form.setValue('postal_code', suggestion.postal_code);
 *   }}
 * />
 *
 * // Lookup produit
 * <BarcodeLookup
 *   value={barcode}
 *   onEnrich={(fields) => {
 *     form.setValue('name', fields.name);
 *     form.setValue('brand', fields.brand);
 *     form.setValue('description', fields.description);
 *   }}
 * />
 * ```
 */

// ============================================================================
// COMPONENTS
// ============================================================================

export {
  SiretLookup,
  AddressAutocomplete,
  BarcodeLookup,
  EnrichmentPreview,
  CompanyAutocomplete,
  RiskAnalysis,
  RiskDisplay,
  ScoreGauge,
} from './components';

// ============================================================================
// HOOKS
// ============================================================================

export {
  useSiretLookup,
  isValidSiret,
  isValidSiren,
  detectType,
  useAddressAutocomplete,
  parseAddress,
  formatAddress,
  useBarcodeLookup,
  detectBarcodeType,
  isValidBarcode,
  formatBarcode,
  useRiskAnalysis,
  useInternalScore,
} from './hooks';

export type {
  UseSiretLookupResult,
  UseAddressAutocompleteOptions,
  UseBarcodeLookupResult,
  BarcodeType,
  UseRiskAnalysisResult,
  UseRiskAnalysisOptions,
  UseInternalScoreResult,
  InternalScoreResult,
  InternalScoreMetrics,
} from './hooks';

// ============================================================================
// API
// ============================================================================

export {
  enrichmentApi,
  lookup,
  lookupSiret,
  lookupSiren,
  lookupBarcode,
  analyzeRisk,
  getInternalScore,
  getAddressSuggestions,
  acceptEnrichment,
  getHistory,
  getHistoryById,
  getStats,
} from './api';

// ============================================================================
// TYPES
// ============================================================================

export type {
  EnrichmentProvider,
  EnrichmentStatus,
  EnrichmentAction,
  LookupType,
  EntityType,
  EnrichmentLookupRequest,
  EnrichmentLookupResponse,
  EnrichmentAcceptRequest,
  EnrichmentHistoryItem,
  EnrichmentStats,
  AddressSuggestion,
  EnrichedContactFields,
  EnrichedProductFields,
  SiretLookupProps,
  AddressAutocompleteProps,
  BarcodeLookupProps,
  EnrichmentPreviewProps,
  // Risk Analysis types
  RiskLevel,
  RiskSeverity,
  RiskFactor,
  RiskAnalysis as RiskAnalysisData,
  EnrichedRiskFields,
  RiskAnalysisProps,
  RiskAnalysisDisplayProps,
} from './types';
