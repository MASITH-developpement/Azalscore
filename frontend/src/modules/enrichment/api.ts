/**
 * AZALS Module - Auto-Enrichment - API Client
 * ============================================
 * Client API pour les endpoints d'enrichissement.
 */

import { api } from '@/core/api-client';
import type {
  EnrichmentLookupRequest,
  EnrichmentLookupResponse,
  EnrichmentAcceptRequest,
  EnrichmentHistoryItem,
  EnrichmentStats,
  AddressSuggestion,
  CompanySuggestion,
  LookupType,
  EntityType,
  EnrichedRiskFields,
} from './types';

// Re-export CompanySuggestion for convenience
export type { CompanySuggestion } from './types';

const BASE_URL = '/v3/enrichment';

// ============================================================================
// LOOKUP API
// ============================================================================

/**
 * Recherche d'enrichissement generique.
 */
export async function lookup(
  request: EnrichmentLookupRequest
): Promise<EnrichmentLookupResponse> {
  const response = await api.post<EnrichmentLookupResponse>(
    `${BASE_URL}/lookup`,
    request
  );
  return response as unknown as EnrichmentLookupResponse;
}

/**
 * Recherche entreprise par SIRET.
 */
export async function lookupSiret(siret: string): Promise<EnrichmentLookupResponse> {
  // Nettoyer le SIRET (retirer espaces)
  const cleanSiret = siret.replace(/\s/g, '');
  const response = await api.get<EnrichmentLookupResponse>(
    `${BASE_URL}/siret/${cleanSiret}`
  );
  return response as unknown as EnrichmentLookupResponse;
}

/**
 * Recherche entreprise par SIREN.
 */
export async function lookupSiren(siren: string): Promise<EnrichmentLookupResponse> {
  const cleanSiren = siren.replace(/\s/g, '');
  return lookup({
    lookup_type: 'siren' as LookupType,
    lookup_value: cleanSiren,
    entity_type: 'contact' as EntityType,
  });
}

/**
 * Recherche produit par code-barres.
 */
export async function lookupBarcode(barcode: string): Promise<EnrichmentLookupResponse> {
  const cleanBarcode = barcode.replace(/\s/g, '');
  const response = await api.get<EnrichmentLookupResponse>(
    `${BASE_URL}/barcode/${cleanBarcode}`
  );
  return response as unknown as EnrichmentLookupResponse;
}

/**
 * Analyse de risque entreprise via Pappers.
 * Retourne score, niveau, cotation BDF, procedures collectives.
 */
export async function analyzeRisk(
  identifier: string
): Promise<EnrichmentLookupResponse> {
  // Nettoyer l'identifiant (retirer espaces)
  const cleanId = identifier.replace(/\s/g, '');
  const response = await api.get<EnrichmentLookupResponse>(
    `${BASE_URL}/risk/${cleanId}`
  );
  return response as unknown as EnrichmentLookupResponse;
}

/**
 * Score interne d'un client basé sur son historique.
 * Fonctionne pour tous: particuliers, professionnels, donneurs d'ordre.
 */
export async function getInternalScore(
  customerId: string
): Promise<EnrichmentLookupResponse> {
  const response = await api.get<EnrichmentLookupResponse>(
    `${BASE_URL}/score/internal/${customerId}`
  );
  return response as unknown as EnrichmentLookupResponse;
}

/**
 * Recherche entreprise par nom (autocomplete).
 */
export async function searchCompanyByName(
  query: string,
  limit: number = 10
): Promise<CompanySuggestion[]> {
  if (query.length < 2) return [];

  try {
    const response = await lookup({
      lookup_type: 'name' as LookupType,
      lookup_value: query,
      entity_type: 'contact' as EntityType,
    });

    if (response.success && Array.isArray(response.suggestions)) {
      return response.suggestions as CompanySuggestion[];
    }

    return [];
  } catch (error) {
    console.error('[Enrichment] Company search error:', error);
    return [];
  }
}

/**
 * Autocomplete d'adresses francaises.
 */
export async function getAddressSuggestions(
  query: string,
  limit: number = 5
): Promise<AddressSuggestion[]> {
  if (query.length < 3) return [];

  try {
    const url = `${BASE_URL}/address/suggestions?q=${encodeURIComponent(query)}&limit=${limit}`;
    const result = await api.get<AddressSuggestion[]>(url, { timeout: 5000 });
    // Ensure we always return an array
    if (Array.isArray(result)) {
      return result;
    }
    return [];
  } catch (error) {
    console.error('[Enrichment] Address suggestions error:', error);
    return [];
  }
}

// ============================================================================
// ACCEPT/REJECT API
// ============================================================================

/**
 * Accepte ou rejette les donnees enrichies.
 */
export async function acceptEnrichment(
  historyId: string,
  request: EnrichmentAcceptRequest
): Promise<{ message: string; history_id: string; action: string }> {
  const response = await api.post<{ message: string; history_id: string; action: string }>(
    `${BASE_URL}/${historyId}/accept`,
    request
  );
  return response as unknown as { message: string; history_id: string; action: string };
}

// ============================================================================
// HISTORY API
// ============================================================================

/**
 * Recupere l'historique des enrichissements.
 */
export async function getHistory(params?: {
  entity_type?: string;
  entity_id?: string;
  provider?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<EnrichmentHistoryItem[]> {
  const queryParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value));
      }
    });
  }
  const queryString = queryParams.toString();
  const url = queryString ? `${BASE_URL}/history?${queryString}` : `${BASE_URL}/history`;

  const response = await api.get<EnrichmentHistoryItem[]>(url);
  return response as unknown as EnrichmentHistoryItem[];
}

/**
 * Recupere un enrichissement par son ID.
 */
export async function getHistoryById(historyId: string): Promise<EnrichmentHistoryItem> {
  const response = await api.get<EnrichmentHistoryItem>(
    `${BASE_URL}/history/${historyId}`
  );
  return response as unknown as EnrichmentHistoryItem;
}

// ============================================================================
// STATS API
// ============================================================================

/**
 * Recupere les statistiques d'enrichissement.
 */
export async function getStats(days: number = 30): Promise<EnrichmentStats> {
  const response = await api.get<EnrichmentStats>(
    `${BASE_URL}/stats?days=${days}`
  );
  return response as unknown as EnrichmentStats;
}

// ============================================================================
// EXPORT
// ============================================================================

export const enrichmentApi = {
  lookup,
  lookupSiret,
  lookupSiren,
  lookupBarcode,
  analyzeRisk,
  getInternalScore,
  searchCompanyByName,
  getAddressSuggestions,
  acceptEnrichment,
  getHistory,
  getHistoryById,
  getStats,
};

export default enrichmentApi;
