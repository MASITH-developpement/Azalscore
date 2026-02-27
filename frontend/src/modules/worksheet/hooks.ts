/**
 * AZALSCORE - Worksheet React Query Hooks
 * ========================================
 * Hooks pour le module Feuille de Travail Unique
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { worksheetApi } from './api';
import type { Client, Product, DocumentCreate, LineData, DocumentType } from './api';

// ============================================================================
// RE-EXPORTS (types for index.tsx)
// ============================================================================

export type { Client, Product, LineData, DocumentType };

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const worksheetKeys = {
  all: ['worksheet'] as const,

  // Clients
  clients: () => [...worksheetKeys.all, 'clients'] as const,
  clientsLookup: () => [...worksheetKeys.clients(), 'lookup'] as const,

  // Products
  products: () => [...worksheetKeys.all, 'products'] as const,
  productsLookup: () => [...worksheetKeys.products(), 'lookup'] as const,

  // Documents
  documents: () => [...worksheetKeys.all, 'documents'] as const,
};

// ============================================================================
// CLIENT HOOKS
// ============================================================================

/**
 * Récupère la liste des clients pour lookup
 */
export const useClients = () => {
  return useQuery({
    queryKey: worksheetKeys.clientsLookup(),
    queryFn: () => worksheetApi.getClients(),
    staleTime: 5 * 60 * 1000, // 5 minutes cache
  });
};

/**
 * Crée un nouveau client
 */
export const useCreateClient = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Client>) => worksheetApi.createClient(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: worksheetKeys.clients() });
    },
  });
};

// ============================================================================
// PRODUCT HOOKS
// ============================================================================

/**
 * Récupère la liste des produits pour lookup
 */
export const useProducts = () => {
  return useQuery({
    queryKey: worksheetKeys.productsLookup(),
    queryFn: () => worksheetApi.getProducts(),
    staleTime: 5 * 60 * 1000, // 5 minutes cache
  });
};

/**
 * Crée un nouveau produit
 */
export const useCreateProduct = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Product>) => worksheetApi.createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: worksheetKeys.products() });
    },
  });
};

// ============================================================================
// DOCUMENT HOOKS
// ============================================================================

interface DocumentData {
  type: DocumentType;
  client_id: string;
  client?: Client;
  date: string;
  lines: (LineData & { id: string })[];
  notes?: string;
}

/**
 * Sauvegarde un document (devis, facture, commande, intervention)
 */
export const useSaveDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: DocumentData) => {
      if (data.type === 'INTERVENTION') {
        return worksheetApi.createIntervention({
          client_id: data.client_id,
          titre: data.lines[0]?.description || 'Intervention',
          description: data.notes,
        });
      }

      const documentData: DocumentCreate = {
        type: data.type,
        customer_id: data.client_id,
        date: data.date,
        notes: data.notes,
        lines: data.lines.map(l => ({
          description: l.description,
          quantity: l.quantity,
          unit_price: l.unit_price,
          tax_rate: l.tax_rate,
          discount_percent: 0,
        })),
      };

      return worksheetApi.createDocument(documentData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: worksheetKeys.documents() });
    },
  });
};
