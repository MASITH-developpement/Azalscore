/**
 * AZALSCORE - Invoicing API
 * =========================
 * API client pour le module Facturation (Ventes T0)
 * Couvre: Devis, Commandes, Factures
 *
 * Utilise l'API commerciale partagée
 */

import {
  commercialApi,
  type CommercialDocument,
  type DocumentCreate,
  type DocumentUpdate,
  type DocumentFilters,
  type DocumentLineCreate,
  type DocumentLine,
  type PaginatedResponse,
  type Customer,
  type CustomerFilters,
} from '@/core/commercial-api';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type { CommercialDocument as Document } from '@/core/commercial-api';
export type { DocumentCreate, DocumentUpdate } from '@/core/commercial-api';
export type { DocumentLine, DocumentLineCreate } from '@/core/commercial-api';
export type { Customer } from '@/core/commercial-api';

// ============================================================================
// TYPES SPÉCIFIQUES
// ============================================================================

export type InvoicingDocumentType = 'QUOTE' | 'ORDER' | 'INVOICE';
export type InvoicingDocumentStatus = 'DRAFT' | 'VALIDATED';

export interface InvoicingFilters extends Omit<DocumentFilters, 'type'> {
  type?: InvoicingDocumentType;
}

// ============================================================================
// API CLIENT
// ============================================================================

export const invoicingApi = {
  // ==========================================================================
  // Documents
  // ==========================================================================

  /**
   * Liste les documents par type
   */
  list: (type: InvoicingDocumentType, filters?: InvoicingFilters) =>
    commercialApi.listDocuments({
      ...filters,
      type,
    }),

  /**
   * Récupère un document par son ID
   */
  get: (id: string) => commercialApi.getDocument(id),

  /**
   * Crée un nouveau document
   */
  create: (type: InvoicingDocumentType, data: Omit<DocumentCreate, 'type'>) =>
    commercialApi.createDocument({
      ...data,
      type,
    }),

  /**
   * Met à jour un document
   */
  update: (id: string, data: DocumentUpdate) =>
    commercialApi.updateDocument(id, data),

  /**
   * Supprime un document (brouillon uniquement)
   */
  delete: (id: string) => commercialApi.deleteDocument(id),

  /**
   * Valide un document
   */
  validate: (id: string) => commercialApi.validateDocument(id),

  // ==========================================================================
  // Lignes
  // ==========================================================================

  /**
   * Ajoute une ligne au document
   */
  addLine: (documentId: string, data: DocumentLineCreate) =>
    commercialApi.addLine(documentId, data),

  /**
   * Met à jour une ligne
   */
  updateLine: (documentId: string, lineId: string, data: Partial<DocumentLineCreate>) =>
    commercialApi.updateLine(documentId, lineId, data),

  /**
   * Supprime une ligne
   */
  deleteLine: (documentId: string, lineId: string) =>
    commercialApi.deleteLine(documentId, lineId),

  // ==========================================================================
  // Transformations
  // ==========================================================================

  /**
   * Convertit un devis en commande
   */
  quoteToOrder: (quoteId: string) =>
    commercialApi.convertQuoteToOrder(quoteId),

  /**
   * Crée une facture depuis une commande
   */
  orderToInvoice: (orderId: string) =>
    commercialApi.createInvoiceFromOrder(orderId),

  // ==========================================================================
  // Clients
  // ==========================================================================

  /**
   * Liste les clients
   */
  listCustomers: (filters?: CustomerFilters) =>
    commercialApi.listCustomers(filters),

  /**
   * Récupère un client par son ID
   */
  getCustomer: (id: string) =>
    commercialApi.getCustomer(id),
};

export default invoicingApi;
