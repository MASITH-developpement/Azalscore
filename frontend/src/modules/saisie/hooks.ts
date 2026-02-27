/**
 * AZALSCORE - Saisie React Query Hooks
 * =====================================
 * Hooks pour le module Saisie Rapide (Quick Entry)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { saisieApi } from './api';
import type {
  QuickCustomer,
  QuickProduct,
  QuickLine,
  QuickDocumentResult,
  CustomerCreate,
} from './api';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type { QuickCustomer, QuickProduct, QuickLine, QuickDocumentResult };

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const saisieKeys = {
  all: ['saisie'] as const,

  // Customers
  customers: () => [...saisieKeys.all, 'customers'] as const,
  customerSearch: (search: string) => [...saisieKeys.customers(), 'search', search] as const,

  // Products
  products: () => [...saisieKeys.all, 'products'] as const,
  productSearch: (search: string) => [...saisieKeys.products(), 'search', search] as const,

  // Documents
  documents: () => [...saisieKeys.all, 'documents'] as const,
};

// ============================================================================
// CUSTOMER HOOKS
// ============================================================================

/**
 * Recherche de clients pour autocompletion
 */
export const useQuickCustomers = (search: string) => {
  return useQuery({
    queryKey: saisieKeys.customerSearch(search),
    queryFn: async () => {
      if (!search || search.length < 2) return [];
      try {
        const response = await saisieApi.searchCustomers({ search });
        return (response as unknown as { items: QuickCustomer[] }).items || [];
      } catch {
        return [];
      }
    },
    enabled: search.length >= 2,
  });
};

/**
 * Création rapide de client
 */
export const useCreateQuickCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CustomerCreate) => {
      const response = await saisieApi.createCustomer(data);
      return response as unknown as QuickCustomer;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: saisieKeys.customers() });
      queryClient.invalidateQueries({ queryKey: ['partners', 'clients'] });
    },
  });
};

// ============================================================================
// PRODUCT HOOKS
// ============================================================================

/**
 * Recherche de produits pour autocompletion
 */
export const useQuickProducts = (search: string) => {
  return useQuery({
    queryKey: saisieKeys.productSearch(search),
    queryFn: async () => {
      if (!search || search.length < 2) return [];
      try {
        const response = await saisieApi.searchProducts({ search });
        return (response as unknown as { items: QuickProduct[] }).items || [];
      } catch {
        return [];
      }
    },
    enabled: search.length >= 2,
  });
};

// ============================================================================
// DOCUMENT HOOKS
// ============================================================================

interface QuickLineWithId extends QuickLine {
  id: string;
  product_id?: string;
}

/**
 * Création rapide de devis
 */
export const useCreateQuickDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      customer_id: string;
      lines: Omit<QuickLineWithId, 'id'>[];
      notes?: string;
    }) => {
      const response = await saisieApi.createDocument({
        type: 'QUOTE',
        customer_id: data.customer_id,
        validity_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        notes: data.notes,
        lines: data.lines.map(({ product_id: _productId, ...line }) => line),
      });
      return response as unknown as QuickDocumentResult;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: saisieKeys.documents() });
      queryClient.invalidateQueries({ queryKey: ['documents', 'QUOTE'] });
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};
