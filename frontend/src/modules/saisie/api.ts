/**
 * AZALSCORE - Saisie API
 * ======================
 * API client pour le module Saisie Rapide (Quick Entry)
 * Couvre: Clients, Produits, Documents (Devis, Factures, Commandes)
 */

import { api } from '@/core/api-client';

// ============================================================================
// TYPES
// ============================================================================

export interface QuickCustomer {
  id: string;
  code?: string;
  name: string;
  email?: string;
  phone?: string;
  mobile?: string;
  address_line1?: string;
  city?: string;
  postal_code?: string;
  country_code?: string;
  tax_id?: string;
  siret?: string;
}

export interface QuickProduct {
  id: string;
  code: string;
  name: string;
  unit_price: number;
  unit?: string;
  tax_rate?: number;
}

export interface QuickLine {
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  discount_percent?: number;
}

export interface QuickDocumentCreate {
  type: 'QUOTE' | 'INVOICE' | 'ORDER';
  customer_id: string;
  date?: string;
  validity_date?: string;
  notes?: string;
  lines: QuickLine[];
}

export interface QuickDocumentResult {
  id: string;
  number: string;
  type: string;
  status: string;
  total: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface CustomerSearchParams {
  search: string;
  page_size?: number;
  is_active?: boolean;
}

export interface ProductSearchParams {
  search: string;
  page_size?: number;
  is_active?: boolean;
}

export interface CustomerCreate {
  name: string;
  email?: string;
  phone?: string;
  mobile?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country_code?: string;
  siret?: string;
  tax_id?: string;
}

export interface ProductCreate {
  code: string;
  name: string;
  sale_price?: number;
  purchase_price?: number;
  unit?: string;
  tax_rate?: number;
}

// ============================================================================
// HELPERS
// ============================================================================

function buildQueryString<T extends object>(params: T): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// API CLIENT
// ============================================================================

export const saisieApi = {
  // ==========================================================================
  // Customers
  // ==========================================================================

  /**
   * Recherche de clients pour autocompletion
   */
  searchCustomers: (params: CustomerSearchParams) =>
    api.get<PaginatedResponse<QuickCustomer>>(
      `/partners/clients${buildQueryString({
        search: params.search,
        page_size: params.page_size || 10,
        is_active: params.is_active ?? true,
      })}`
    ),

  /**
   * Cree un nouveau client rapide
   */
  createCustomer: (data: CustomerCreate) =>
    api.post<QuickCustomer>('/partners/clients', {
      ...data,
      type: 'CUSTOMER',
      is_active: true,
    }),

  // ==========================================================================
  // Products
  // ==========================================================================

  /**
   * Recherche de produits pour autocompletion
   */
  searchProducts: (params: ProductSearchParams) =>
    api.get<PaginatedResponse<QuickProduct>>(
      `/inventory/products${buildQueryString({
        search: params.search,
        page_size: params.page_size || 10,
        is_active: params.is_active ?? true,
      })}`
    ),

  /**
   * Cree un nouveau produit rapide
   */
  createProduct: (data: ProductCreate) =>
    api.post<QuickProduct>('/inventory/products', {
      ...data,
      is_active: true,
    }),

  // ==========================================================================
  // Documents
  // ==========================================================================

  /**
   * Cree un document commercial (devis, facture, commande)
   */
  createDocument: (data: QuickDocumentCreate) =>
    api.post<QuickDocumentResult>('/commercial/documents', {
      type: data.type,
      customer_id: data.customer_id,
      date: data.date || new Date().toISOString().split('T')[0],
      validity_date: data.validity_date,
      notes: data.notes,
      lines: data.lines.map((line, index) => ({
        line_number: index + 1,
        description: line.description,
        quantity: line.quantity,
        unit_price: line.unit_price,
        tax_rate: line.tax_rate,
        discount_percent: line.discount_percent || 0,
      })),
    }),

  /**
   * Cree une intervention
   */
  createIntervention: (data: {
    client_id: string;
    titre: string;
    description?: string;
    type_intervention?: string;
    priorite?: string;
  }) =>
    api.post('/interventions', {
      ...data,
      type_intervention: data.type_intervention || 'MAINTENANCE',
      priorite: data.priorite || 'NORMAL',
    }),
};

export default saisieApi;
