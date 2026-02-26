/**
 * AZALSCORE - Purchases API
 * =========================
 * API client pour le module Achats
 * Couvre: Fournisseurs, Commandes d'achat, Factures fournisseurs
 */

import { api } from '@/core/api-client';
import type {
  Supplier,
  PurchaseOrder,
  PurchaseInvoice,
  SupplierStatus,
} from './types';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type { Supplier, PurchaseOrder, PurchaseInvoice, SupplierStatus };

// ============================================================================
// LOCAL TYPES (not exported from types.ts)
// ============================================================================

export type OrderStatus = 'DRAFT' | 'SENT' | 'CONFIRMED' | 'PARTIAL' | 'RECEIVED' | 'INVOICED' | 'CANCELLED';
export type InvoiceStatus = 'DRAFT' | 'VALIDATED' | 'PAID' | 'PARTIAL' | 'CANCELLED';

// ============================================================================
// TYPES - Request/Response
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PurchaseSummary {
  pending_orders: number;
  pending_value: number;
  validated_this_month: number;
  pending_invoices: number;
  total_suppliers: number;
  active_suppliers: number;
}

export interface SupplierFilters {
  status?: SupplierStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface OrderFilters {
  status?: OrderStatus;
  supplier_id?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface InvoiceFilters {
  status?: InvoiceStatus;
  supplier_id?: string;
  order_id?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface SupplierCreate {
  code?: string;
  name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  tax_id?: string;
  siret?: string;
  payment_terms?: string;
  notes?: string;
}

export interface OrderLineCreate {
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate?: number;
  discount_percent?: number;
}

export interface OrderCreate {
  supplier_id: string;
  date?: string;
  expected_date?: string;
  reference?: string;
  notes?: string;
  lines: OrderLineCreate[];
}

export interface InvoiceCreate {
  supplier_id: string;
  order_id?: string;
  date: string;
  due_date?: string;
  supplier_reference?: string;
  notes?: string;
  lines: OrderLineCreate[];
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/purchases';

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

export const purchasesApi = {
  // ==========================================================================
  // Dashboard
  // ==========================================================================

  /**
   * Récupère le résumé des achats
   */
  getSummary: () =>
    api.get<PurchaseSummary>(`${BASE_PATH}/summary`),

  // ==========================================================================
  // Suppliers (Fournisseurs)
  // ==========================================================================

  /**
   * Liste les fournisseurs
   */
  listSuppliers: (filters?: SupplierFilters) =>
    api.get<PaginatedResponse<Supplier>>(
      `${BASE_PATH}/suppliers${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère un fournisseur par son ID
   */
  getSupplier: (id: string) =>
    api.get<Supplier>(`${BASE_PATH}/suppliers/${id}`),

  /**
   * Crée un nouveau fournisseur
   */
  createSupplier: (data: SupplierCreate) =>
    api.post<Supplier>(`${BASE_PATH}/suppliers`, data),

  /**
   * Met à jour un fournisseur
   */
  updateSupplier: (id: string, data: Partial<SupplierCreate>) =>
    api.put<Supplier>(`${BASE_PATH}/suppliers/${id}`, data),

  /**
   * Supprime un fournisseur
   */
  deleteSupplier: (id: string) =>
    api.delete(`${BASE_PATH}/suppliers/${id}`),

  /**
   * Approuve un fournisseur
   */
  approveSupplier: (id: string) =>
    api.post<Supplier>(`${BASE_PATH}/suppliers/${id}/approve`, {}),

  /**
   * Bloque un fournisseur
   */
  blockSupplier: (id: string) =>
    api.post<Supplier>(`${BASE_PATH}/suppliers/${id}/block`, {}),

  // ==========================================================================
  // Orders (Commandes d'achat)
  // ==========================================================================

  /**
   * Liste les commandes d'achat
   */
  listOrders: (filters?: OrderFilters) =>
    api.get<PaginatedResponse<PurchaseOrder>>(
      `${BASE_PATH}/orders${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère une commande par son ID
   */
  getOrder: (id: string) =>
    api.get<PurchaseOrder>(`${BASE_PATH}/orders/${id}`),

  /**
   * Crée une nouvelle commande
   */
  createOrder: (data: OrderCreate) =>
    api.post<PurchaseOrder>(`${BASE_PATH}/orders`, data),

  /**
   * Met à jour une commande
   */
  updateOrder: (id: string, data: Partial<OrderCreate>) =>
    api.put<PurchaseOrder>(`${BASE_PATH}/orders/${id}`, data),

  /**
   * Supprime une commande (brouillon uniquement)
   */
  deleteOrder: (id: string) =>
    api.delete(`${BASE_PATH}/orders/${id}`),

  /**
   * Valide une commande
   */
  validateOrder: (id: string) =>
    api.post<PurchaseOrder>(`${BASE_PATH}/orders/${id}/validate`, {}),

  /**
   * Confirme une commande (fournisseur)
   */
  confirmOrder: (id: string) =>
    api.post<PurchaseOrder>(`${BASE_PATH}/orders/${id}/confirm`, {}),

  /**
   * Marque une commande comme reçue
   */
  receiveOrder: (id: string, data?: { notes?: string }) =>
    api.post<PurchaseOrder>(`${BASE_PATH}/orders/${id}/receive`, data || {}),

  /**
   * Annule une commande
   */
  cancelOrder: (id: string) =>
    api.post<PurchaseOrder>(`${BASE_PATH}/orders/${id}/cancel`, {}),

  /**
   * Crée une facture depuis une commande
   */
  createInvoiceFromOrder: (orderId: string) =>
    api.post<PurchaseInvoice>(`${BASE_PATH}/orders/${orderId}/invoice`, {}),

  // ==========================================================================
  // Invoices (Factures fournisseurs)
  // ==========================================================================

  /**
   * Liste les factures fournisseurs
   */
  listInvoices: (filters?: InvoiceFilters) =>
    api.get<PaginatedResponse<PurchaseInvoice>>(
      `${BASE_PATH}/invoices${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère une facture par son ID
   */
  getInvoice: (id: string) =>
    api.get<PurchaseInvoice>(`${BASE_PATH}/invoices/${id}`),

  /**
   * Crée une nouvelle facture
   */
  createInvoice: (data: InvoiceCreate) =>
    api.post<PurchaseInvoice>(`${BASE_PATH}/invoices`, data),

  /**
   * Met à jour une facture
   */
  updateInvoice: (id: string, data: Partial<InvoiceCreate>) =>
    api.put<PurchaseInvoice>(`${BASE_PATH}/invoices/${id}`, data),

  /**
   * Supprime une facture (brouillon uniquement)
   */
  deleteInvoice: (id: string) =>
    api.delete(`${BASE_PATH}/invoices/${id}`),

  /**
   * Valide une facture
   */
  validateInvoice: (id: string) =>
    api.post<PurchaseInvoice>(`${BASE_PATH}/invoices/${id}/validate`, {}),

  /**
   * Annule une facture
   */
  cancelInvoice: (id: string) =>
    api.post<PurchaseInvoice>(`${BASE_PATH}/invoices/${id}/cancel`, {}),
};

export default purchasesApi;
