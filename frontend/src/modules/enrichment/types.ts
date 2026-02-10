/**
 * AZALS Module - Auto-Enrichment - Types
 * =======================================
 * Types TypeScript pour le module d'enrichissement.
 */

// ============================================================================
// ENUMS
// ============================================================================

export type EnrichmentProvider =
  | 'insee'
  | 'adresse_gouv'
  | 'openfoodfacts'
  | 'openbeautyfacts'
  | 'openpetfoodfacts'
  | 'pappers'
  | 'google_places'
  | 'amazon_paapi'
  | 'pages_jaunes';

export type EnrichmentStatus =
  | 'pending'
  | 'success'
  | 'partial'
  | 'not_found'
  | 'error'
  | 'rate_limited';

export type EnrichmentAction = 'pending' | 'accepted' | 'rejected' | 'partial';

export type LookupType = 'siret' | 'siren' | 'address' | 'barcode' | 'name' | 'risk';

export type EntityType = 'contact' | 'product';

// ============================================================================
// RISK ANALYSIS TYPES
// ============================================================================

export type RiskLevel = 'low' | 'medium' | 'elevated' | 'high';
export type RiskSeverity = 'positive' | 'low' | 'medium' | 'high' | 'critical';

export interface RiskFactor {
  factor: string;
  impact: number;
  severity: RiskSeverity;
  source?: string;
}

export interface RiskAnalysis {
  score: number;           // 0-100
  level: RiskLevel;
  level_label: string;
  color: 'green' | 'yellow' | 'orange' | 'red';
  factors: RiskFactor[];
  alerts: string[];
  recommendation: string;
  cotation_bdf?: string;   // Cotation Banque de France
}

export interface EnrichedRiskFields {
  // Champs Contact standards
  name?: string;
  company_name?: string;
  legal_name?: string;
  siret?: string;
  siren?: string;
  address_line1?: string;
  address_line2?: string;
  postal_code?: string;
  city?: string;
  legal_form?: string;
  industry_code?: string;
  industry_label?: string;
  capital?: number;
  effectif?: number;

  // Champs d'analyse de risque
  risk_score?: number;
  risk_level?: RiskLevel;
  risk_level_label?: string;
  risk_alerts?: string[];
  risk_recommendation?: string;

  // Metadata Pappers
  _pappers_risk_analysis?: RiskAnalysis;
}

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface EnrichmentLookupRequest {
  lookup_type: LookupType;
  lookup_value: string;
  entity_type: EntityType;
  entity_id?: string;
}

export interface EnrichmentAcceptRequest {
  accepted_fields: string[];
  rejected_fields: string[];
}

// ============================================================================
// RESPONSE TYPES
// ============================================================================

export interface AddressSuggestion {
  label: string;
  address_line1: string;
  house_number?: string;
  street?: string;
  postal_code: string;
  city: string;
  context?: string;
  latitude?: number;
  longitude?: number;
  score: number;
  type?: string;
}

export interface CompanySuggestion {
  label: string;
  value: string;
  siren: string;
  siret: string;
  name: string;
  address: string;
  city: string;
  postal_code: string;
  data?: Record<string, unknown>;
}

export interface EnrichmentLookupResponse {
  success: boolean;
  enriched_fields: Record<string, unknown>;
  confidence: number;
  source?: string;
  cached: boolean;
  history_id?: string;
  suggestions: AddressSuggestion[] | CompanySuggestion[];
  error?: string;
}

export interface EnrichmentHistoryItem {
  id: string;
  entity_type: string;
  entity_id?: string;
  lookup_type: string;
  lookup_value: string;
  provider: string;
  status: string;
  enriched_fields: Record<string, unknown>;
  confidence_score?: number;
  api_response_time_ms?: number;
  cached: boolean;
  error_message?: string;
  action: string;
  accepted_fields: string[];
  rejected_fields: string[];
  action_at?: string;
  created_at: string;
}

export interface EnrichmentStats {
  total_lookups: number;
  successful_lookups: number;
  cached_lookups: number;
  accepted_enrichments: number;
  rejected_enrichments: number;
  avg_confidence: number;
  avg_response_time_ms: number;
  by_provider: Record<string, number>;
  by_lookup_type: Record<string, number>;
}

// ============================================================================
// CONTACT ENRICHMENT FIELDS
// ============================================================================

export interface EnrichedContactFields {
  name?: string;
  company_name?: string;
  legal_form?: string;
  siret?: string;
  siren?: string;
  naf_code?: string;
  naf_label?: string;
  address?: string;           // Adresse complete (depuis suggestions)
  address_line1?: string;     // Premiere ligne d'adresse
  address_line2?: string;
  postal_code?: string;
  city?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
}

// ============================================================================
// PRODUCT ENRICHMENT FIELDS
// ============================================================================

export interface EnrichedProductFields {
  name?: string;
  brand?: string;
  description?: string;
  image_url?: string;
  barcode?: string;
  categories?: string;
  nutriscore?: string;
  ingredients?: string;
  allergens?: string;
  quantity?: string;
  labels?: string;
}

// ============================================================================
// HOOK TYPES
// ============================================================================

export interface UseLookupOptions {
  onSuccess?: (data: EnrichmentLookupResponse) => void;
  onError?: (error: Error) => void;
  debounceMs?: number;
  minLength?: number;
}

export interface UseLookupResult<T = EnrichmentLookupResponse> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  lookup: (value: string) => Promise<void>;
  reset: () => void;
}

export interface UseAddressAutocompleteResult {
  suggestions: AddressSuggestion[];
  isLoading: boolean;
  error: Error | null;
  search: (query: string) => Promise<void>;
  select: (suggestion: AddressSuggestion) => void;
  reset: () => void;
}

// ============================================================================
// COMPONENT PROPS
// ============================================================================

export interface SiretLookupProps {
  value?: string;
  onEnrich?: (fields: EnrichedContactFields) => void;
  onHistoryId?: (id: string) => void;
  disabled?: boolean;
  className?: string;
}

export interface AddressAutocompleteProps {
  value?: string;
  onChange?: (value: string) => void;
  onSelect?: (suggestion: AddressSuggestion) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export interface BarcodeLookupProps {
  value?: string;
  onEnrich?: (fields: EnrichedProductFields) => void;
  onHistoryId?: (id: string) => void;
  disabled?: boolean;
  className?: string;
}

export interface EnrichmentPreviewProps {
  fields: Record<string, unknown>;
  currentValues?: Record<string, unknown>;
  onAccept: (accepted: string[], rejected: string[]) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export interface RiskAnalysisProps {
  siren?: string;
  siret?: string;
  onAnalysis?: (analysis: RiskAnalysis) => void;
  compact?: boolean;          // Mode compact pour inline
  autoLoad?: boolean;         // Charger automatiquement
  showDetails?: boolean;      // Afficher les details
  className?: string;
}

export interface RiskAnalysisDisplayProps {
  analysis: RiskAnalysis;
  compact?: boolean;
  showDetails?: boolean;
  className?: string;
}
