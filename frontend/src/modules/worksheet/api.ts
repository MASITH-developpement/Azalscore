/**
 * AZALSCORE - Worksheet API
 * =========================
 * API client pour le module Feuille de Travail Unique
 * Couvre: Clients, Produits, Documents
 */

import { api } from '@/core/api-client';
import { unwrapApiResponse } from '@/types';

// ============================================================================
// TYPES
// ============================================================================

export type DocumentType = 'QUOTE' | 'INVOICE' | 'ORDER' | 'INTERVENTION';

export interface Client {
  id: string;
  code: string;
  name: string;
  email?: string;
  phone?: string;
  address_line1?: string;
  city?: string;
  postal_code?: string;
  country_code?: string;
  tax_id?: string;
}

export interface Product {
  id: string;
  code: string;
  name: string;
  sale_price?: number;
  purchase_price?: number;
  unit?: string;
}

export interface LineData {
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  discount_percent?: number;
}

export interface DocumentCreate {
  type: DocumentType;
  customer_id: string;
  date?: string;
  notes?: string;
  lines: LineData[];
}

export interface DocumentResult {
  id: string;
  number?: string;
  reference?: string;
  type: string;
  status: string;
  total?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

// ============================================================================
// API CLIENT
// ============================================================================

export const worksheetApi = {
  // ==========================================================================
  // Clients
  // ==========================================================================

  /**
   * Recupere la liste des clients pour lookup
   */
  getClients: async (pageSize = 100) => {
    const response = await api.get<{ items: Client[] }>(
      `/commercial/customers?page_size=${pageSize}&is_active=true`
    );
    const data = unwrapApiResponse<{ items: Client[] }>(response);
    return data?.items || [];
  },

  /**
   * Cree un nouveau client
   */
  createClient: async (data: Partial<Client>) => {
    const response = await api.post<Client>('/commercial/customers', data);
    return response as unknown as Client;
  },

  // ==========================================================================
  // Products
  // ==========================================================================

  /**
   * Recupere la liste des produits pour lookup
   */
  getProducts: async (pageSize = 100) => {
    const response = await api.get<{ items: Product[] }>(
      `/inventory/products?page_size=${pageSize}&is_active=true`
    );
    const data = unwrapApiResponse<{ items: Product[] }>(response);
    return data?.items || [];
  },

  /**
   * Cree un nouveau produit
   */
  createProduct: async (data: Partial<Product>) => {
    const response = await api.post<Product>('/inventory/products', data);
    return response as unknown as Product;
  },

  // ==========================================================================
  // Documents
  // ==========================================================================

  /**
   * Cree un document (devis, facture, commande)
   */
  createDocument: async (data: DocumentCreate) => {
    const endpoint = '/commercial/documents';
    const payload = {
      type: data.type,
      customer_id: data.customer_id,
      date: data.date || new Date().toISOString().split('T')[0],
      notes: data.notes,
      lines: data.lines.map(l => ({
        description: l.description,
        quantity: l.quantity,
        unit_price: l.unit_price,
        tax_rate: l.tax_rate,
        discount_percent: l.discount_percent || 0,
      })),
    };
    return api.post<DocumentResult>(endpoint, payload);
  },

  /**
   * Cree une intervention
   */
  createIntervention: async (data: {
    client_id: string;
    titre: string;
    description?: string;
  }) => {
    const payload = {
      client_id: data.client_id,
      titre: data.titre,
      description: data.description,
      type_intervention: 'MAINTENANCE',
      priorite: 'NORMAL',
    };
    return api.post('/interventions', payload);
  },
};

export default worksheetApi;
