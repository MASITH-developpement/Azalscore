/**
 * AZALSCORE - Cache partagé
 *
 * Service central pour précharger et mettre en cache
 * les données communes utilisées dans toute l'application.
 *
 * RÈGLE AZALSCORE : Un seul chargement initial, pas de re-fetch inutile.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import type { PaginatedResponse } from '@/types';

// ============================================================
// TYPES
// ============================================================

export interface CachedClient {
  id: string;
  code?: string;
  name: string;
  email?: string;
  phone?: string;
  mobile?: string;
  address?: string;
  address_line1?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  country_code?: string;
  vat_number?: string;
  payment_terms?: string;
  is_active: boolean;
  type?: string;
}

export interface CachedSupplier {
  id: string;
  code?: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  tax_id?: string;
  payment_terms?: string;
  status: string;
}

export interface CachedProduct {
  id: string;
  code: string;
  name: string;
  description?: string;
  unit_price: number;
  unit: string;
  tax_rate: number;
  is_active: boolean;
}

// ============================================================
// CONSTANTES - Durée de cache
// ============================================================

// Cache pendant 30 minutes - les données de référence changent rarement
const CACHE_STALE_TIME = 1000 * 60 * 30;

// Cache pendant 1 heure avant invalidation
const CACHE_GC_TIME = 1000 * 60 * 60;

// ============================================================
// QUERY KEYS (centralisées)
// ============================================================

export const CACHE_KEYS = {
  clients: ['shared', 'clients'] as const,
  suppliers: ['shared', 'suppliers'] as const,
  products: ['shared', 'products'] as const,
} as const;

// ============================================================
// HOOKS DE CACHE PARTAGÉ
// ============================================================

/**
 * Hook pour obtenir tous les clients actifs (avec cache)
 */
export const useSharedClients = () => {
  return useQuery({
    queryKey: CACHE_KEYS.clients,
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<CachedClient>>(
        '/v1/partners/clients?page_size=500&is_active=true'
      );
      return (response as unknown as PaginatedResponse<CachedClient>).items;
    },
    staleTime: CACHE_STALE_TIME,
    gcTime: CACHE_GC_TIME,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
};

/**
 * Hook pour obtenir tous les fournisseurs actifs (avec cache)
 */
export const useSharedSuppliers = () => {
  return useQuery({
    queryKey: CACHE_KEYS.suppliers,
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<CachedSupplier>>(
        '/v1/purchases/suppliers?page_size=500&status=APPROVED'
      );
      return (response as unknown as PaginatedResponse<CachedSupplier>).items;
    },
    staleTime: CACHE_STALE_TIME,
    gcTime: CACHE_GC_TIME,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
};

/**
 * Hook pour obtenir tous les produits actifs (avec cache)
 */
export const useSharedProducts = () => {
  return useQuery({
    queryKey: CACHE_KEYS.products,
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<CachedProduct>>(
        '/v1/products?page_size=500&is_active=true'
      );
      return (response as unknown as PaginatedResponse<CachedProduct>).items;
    },
    staleTime: CACHE_STALE_TIME,
    gcTime: CACHE_GC_TIME,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
};

// ============================================================
// UTILITAIRES D'INVALIDATION
// ============================================================

/**
 * Hook pour invalider le cache partagé
 * À utiliser après création/modification d'un client ou fournisseur
 */
export const useInvalidateSharedCache = () => {
  const queryClient = useQueryClient();

  return {
    invalidateClients: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.clients });
    },
    invalidateSuppliers: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.suppliers });
    },
    invalidateProducts: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEYS.products });
    },
    invalidateAll: () => {
      queryClient.invalidateQueries({ queryKey: ['shared'] });
    },
  };
};

// ============================================================
// PRÉCHARGEMENT AU DÉMARRAGE
// ============================================================

/**
 * Précharge les données communes au démarrage de l'application
 * À appeler dans App.tsx après l'authentification
 */
export const usePrefetchSharedData = () => {
  const queryClient = useQueryClient();

  const prefetch = async () => {
    // Précharger en parallèle
    await Promise.all([
      queryClient.prefetchQuery({
        queryKey: CACHE_KEYS.clients,
        queryFn: async () => {
          const response = await api.get<PaginatedResponse<CachedClient>>(
            '/v1/partners/clients?page_size=500&is_active=true'
          );
          return (response as unknown as PaginatedResponse<CachedClient>).items;
        },
        staleTime: CACHE_STALE_TIME,
      }),
      queryClient.prefetchQuery({
        queryKey: CACHE_KEYS.suppliers,
        queryFn: async () => {
          const response = await api.get<PaginatedResponse<CachedSupplier>>(
            '/v1/purchases/suppliers?page_size=500&status=APPROVED'
          );
          return (response as unknown as PaginatedResponse<CachedSupplier>).items;
        },
        staleTime: CACHE_STALE_TIME,
      }),
    ]);
  };

  return { prefetch };
};
