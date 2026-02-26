/**
 * AZALSCORE - Commercial API Client
 * ==================================
 * API client partagé pour tous les documents commerciaux:
 * - Devis (QUOTE)
 * - Commandes (ORDER)
 * - Factures (INVOICE)
 * - Avoirs (CREDIT_NOTE)
 *
 * Flux commercial: CRM → DEV → COM/ODS → AFF → FAC/AVO → CPT
 */

import { api } from '@/core/api-client';

// ============================================================================
// ENUMS & TYPES
// ============================================================================

export type DocumentType = 'QUOTE' | 'ORDER' | 'INVOICE' | 'CREDIT_NOTE';

export type DocumentStatus =
  | 'DRAFT'
  | 'VALIDATED'
  | 'SENT'
  | 'CONFIRMED'
  | 'IN_PROGRESS'
  | 'DELIVERED'
  | 'PAID'
  | 'PARTIAL'
  | 'OVERDUE'
  | 'CANCELLED'
  | 'REJECTED'
  | 'EXPIRED';

export type PaymentMethod =
  | 'BANK_TRANSFER'
  | 'CHECK'
  | 'CREDIT_CARD'
  | 'CASH'
  | 'DIRECT_DEBIT'
  | 'OTHER';

// ============================================================================
// INTERFACES - Documents
// ============================================================================

export interface DocumentLine {
  id: string;
  line_number: number;
  product_id?: string;
  product_code?: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount_percent: number;
  discount_amount: number;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
}

export interface DocumentLineCreate {
  product_id?: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount_percent?: number;
  tax_rate?: number;
}

export interface Address {
  line1?: string;
  line2?: string;
  postal_code?: string;
  city?: string;
  country?: string;
}

export interface CommercialDocument {
  id: string;
  type: DocumentType;
  number: string;
  reference?: string;
  status: DocumentStatus;
  customer_id: string;
  customer_name?: string;
  customer_code?: string;
  customer_siret?: string;
  customer_siren?: string;
  customer_vat_number?: string;
  parent_id?: string;
  parent_number?: string;
  parent_type?: DocumentType;
  date: string;
  due_date?: string;
  validity_date?: string;
  delivery_date?: string;
  billing_address?: Address;
  delivery_address?: Address;
  subtotal: number;
  discount_amount: number;
  discount_percent: number;
  tax_amount: number;
  total: number;
  currency: string;
  payment_terms?: string;
  payment_method?: PaymentMethod;
  paid_amount: number;
  remaining_amount: number;
  lines: DocumentLine[];
  notes?: string;
  internal_notes?: string;
  terms?: string;
  pdf_url?: string;
  validated_by?: string;
  validated_at?: string;
  sent_at?: string;
  paid_at?: string;
  delivered_at?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentCreate {
  type: DocumentType;
  customer_id: string;
  reference?: string;
  due_date?: string;
  validity_date?: string;
  delivery_date?: string;
  payment_terms?: string;
  payment_method?: PaymentMethod;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  discount_percent?: number;
  lines?: DocumentLineCreate[];
}

export interface DocumentUpdate {
  reference?: string;
  due_date?: string;
  validity_date?: string;
  delivery_date?: string;
  payment_terms?: string;
  payment_method?: PaymentMethod;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  discount_percent?: number;
}

// ============================================================================
// INTERFACES - Payments
// ============================================================================

export interface Payment {
  id: string;
  document_id: string;
  reference?: string;
  method: PaymentMethod;
  amount: number;
  date: string;
  notes?: string;
  created_at: string;
  created_by?: string;
}

export interface PaymentCreate {
  document_id: string;
  method: PaymentMethod;
  amount: number;
  date: string;
  reference?: string;
  notes?: string;
}

// ============================================================================
// INTERFACES - Customer
// ============================================================================

export interface Customer {
  id: string;
  code: string;
  name: string;
  legal_name?: string;
  email?: string;
  phone?: string;
  siret?: string;
  siren?: string;
  vat_number?: string;
  legal_form?: string;
  capital?: number;
  employee_count?: number;
  naf_code?: string;
  creation_date?: string;
  address_line1?: string;
  address_line2?: string;
  postal_code?: string;
  city?: string;
  country?: string;
}

// ============================================================================
// INTERFACES - Pagination
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DocumentFilters {
  type?: DocumentType;
  status?: DocumentStatus;
  customer_id?: string;
  search?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface CustomerFilters {
  search?: string;
  page?: number;
  page_size?: number;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/commercial';

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

export const commercialApi = {
  // ==========================================================================
  // Documents (Devis, Commandes, Factures, Avoirs)
  // ==========================================================================

  /**
   * Liste les documents commerciaux avec filtres
   */
  listDocuments: (filters?: DocumentFilters) =>
    api.get<PaginatedResponse<CommercialDocument>>(
      `${BASE_PATH}/documents${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère un document par son ID
   */
  getDocument: (documentId: string) =>
    api.get<CommercialDocument>(`${BASE_PATH}/documents/${documentId}`),

  /**
   * Crée un nouveau document
   */
  createDocument: (data: DocumentCreate) =>
    api.post<CommercialDocument>(`${BASE_PATH}/documents`, data),

  /**
   * Met à jour un document
   */
  updateDocument: (documentId: string, data: DocumentUpdate) =>
    api.put<CommercialDocument>(`${BASE_PATH}/documents/${documentId}`, data),

  /**
   * Supprime un document (brouillon uniquement)
   */
  deleteDocument: (documentId: string) =>
    api.delete(`${BASE_PATH}/documents/${documentId}`),

  /**
   * Valide un document
   */
  validateDocument: (documentId: string) =>
    api.post<CommercialDocument>(`${BASE_PATH}/documents/${documentId}/validate`, {}),

  /**
   * Envoie un document au client
   */
  sendDocument: (documentId: string) =>
    api.post<CommercialDocument>(`${BASE_PATH}/documents/${documentId}/send`, {}),

  /**
   * Annule un document
   */
  cancelDocument: (documentId: string) =>
    api.post<CommercialDocument>(`${BASE_PATH}/documents/${documentId}/cancel`, {}),

  // ==========================================================================
  // Document Lines
  // ==========================================================================

  /**
   * Ajoute une ligne à un document
   */
  addLine: (documentId: string, data: DocumentLineCreate) =>
    api.post<DocumentLine>(`${BASE_PATH}/documents/${documentId}/lines`, data),

  /**
   * Met à jour une ligne
   */
  updateLine: (documentId: string, lineId: string, data: Partial<DocumentLineCreate>) =>
    api.put<DocumentLine>(`${BASE_PATH}/documents/${documentId}/lines/${lineId}`, data),

  /**
   * Supprime une ligne
   */
  deleteLine: (documentId: string, lineId: string) =>
    api.delete(`${BASE_PATH}/documents/${documentId}/lines/${lineId}`),

  // ==========================================================================
  // Payments (for invoices)
  // ==========================================================================

  /**
   * Liste les paiements d'un document
   */
  listPayments: (documentId: string) =>
    api.get<Payment[]>(`${BASE_PATH}/documents/${documentId}/payments`),

  /**
   * Enregistre un paiement
   */
  createPayment: (data: PaymentCreate) =>
    api.post<Payment>(`${BASE_PATH}/payments`, data),

  // ==========================================================================
  // Conversions
  // ==========================================================================

  /**
   * Convertit un devis en commande
   */
  convertQuoteToOrder: (quoteId: string) =>
    api.post<CommercialDocument>(`${BASE_PATH}/quotes/${quoteId}/convert`, {}),

  /**
   * Crée une facture depuis une commande
   */
  createInvoiceFromOrder: (orderId: string) =>
    api.post<{ id: string; number: string }>(`${BASE_PATH}/orders/${orderId}/invoice`, {}),

  /**
   * Crée un avoir depuis une facture
   */
  createCreditNote: (invoiceId: string) =>
    api.post<CommercialDocument>(`${BASE_PATH}/documents/${invoiceId}/credit-note`, {}),

  /**
   * Crée une affaire depuis une commande
   */
  createAffaireFromOrder: (orderId: string) =>
    api.post<{ id: string; reference: string }>(`${BASE_PATH}/orders/${orderId}/affaire`, {}),

  // ==========================================================================
  // Order-specific
  // ==========================================================================

  /**
   * Marque une commande comme livrée
   */
  markOrderDelivered: (orderId: string) =>
    api.post<CommercialDocument>(`${BASE_PATH}/documents/${orderId}/deliver`, {}),

  // ==========================================================================
  // Customers
  // ==========================================================================

  /**
   * Liste les clients
   */
  listCustomers: (filters?: CustomerFilters) =>
    api.get<PaginatedResponse<Customer>>(
      `${BASE_PATH}/customers${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère un client par son ID
   */
  getCustomer: (customerId: string) =>
    api.get<Customer>(`${BASE_PATH}/customers/${customerId}`),
};

export default commercialApi;
