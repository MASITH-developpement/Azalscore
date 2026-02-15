/**
 * AZALSCORE Module - INVENTORY - API Client
 * ==========================================
 * Client API pour les endpoints d'inventaire.
 */

import { api } from '@/core/api-client';
import type { ProductSuggestion } from './types';

const BASE_URL = '/inventory';

// ============================================================================
// PRODUCT AUTOCOMPLETE
// ============================================================================

/**
 * Recherche de produits pour autocomplete.
 * Retourne une liste légère de suggestions.
 *
 * @param query - Terme de recherche (min 2 caractères)
 * @param limit - Nombre max de suggestions (défaut: 10)
 * @param categoryId - Filtrer par catégorie (optionnel)
 */
export async function searchProducts(
  query: string,
  limit: number = 10,
  categoryId?: string
): Promise<ProductSuggestion[]> {
  if (!query || query.length < 2) {
    return [];
  }

  try {
    const params = new URLSearchParams({
      q: query,
      limit: String(limit),
    });

    if (categoryId) {
      params.append('category_id', categoryId);
    }

    const response = await api.get<{
      suggestions: ProductSuggestion[];
      total: number;
    }>(`${BASE_URL}/products/autocomplete?${params.toString()}`);

    // ApiResponse enveloppe les donnees dans .data
    const data = response?.data ?? response;
    if (data && Array.isArray(data.suggestions)) {
      return data.suggestions;
    }

    return [];
  } catch (error) {
    console.error('[Inventory] Product search error:', error);
    return [];
  }
}

// ============================================================================
// EXPORT
// ============================================================================

export const inventoryApi = {
  searchProducts,
};

export default inventoryApi;
