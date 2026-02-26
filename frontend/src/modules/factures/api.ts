/**
 * AZALSCORE - Factures API
 * ========================
 * API client pour le module Factures & Avoirs
 * Utilise l'API commerciale partagée
 *
 * Numérotation: FAC-YY-MM-XXXX / AVO-YY-MM-XXXX
 * Flux: COM/ODS/AFF → [FAC/AVO] → CPT
 */

import {
  commercialApi,
  type CommercialDocument,
  type DocumentCreate,
  type DocumentUpdate,
  type DocumentFilters,
  type PaginatedResponse,
  type Payment,
  type PaymentCreate,
  type Customer,
  type CustomerFilters,
} from '@/core/commercial-api';

// ============================================================================
// RE-EXPORTS pour faciliter l'import depuis le module
// ============================================================================

export type { CommercialDocument as Facture } from '@/core/commercial-api';
export type { DocumentCreate as FactureCreate } from '@/core/commercial-api';
export type { DocumentUpdate as FactureUpdate } from '@/core/commercial-api';
export type { Payment, PaymentCreate } from '@/core/commercial-api';
export type { Customer } from '@/core/commercial-api';

// ============================================================================
// TYPES SPÉCIFIQUES FACTURES
// ============================================================================

export type FactureType = 'INVOICE' | 'CREDIT_NOTE';

export interface FactureFilters extends Omit<DocumentFilters, 'type'> {
  type?: FactureType;
}

// ============================================================================
// API CLIENT FACTURES
// ============================================================================

export const facturesApi = {
  // ==========================================================================
  // Factures
  // ==========================================================================

  /**
   * Liste les factures (INVOICE) ou avoirs (CREDIT_NOTE)
   */
  list: (filters?: FactureFilters) =>
    commercialApi.listDocuments({
      ...filters,
      type: filters?.type || 'INVOICE',
    }),

  /**
   * Récupère une facture par son ID
   */
  get: (id: string) => commercialApi.getDocument(id),

  /**
   * Crée une nouvelle facture
   */
  create: (data: Omit<DocumentCreate, 'type'> & { type?: FactureType }) =>
    commercialApi.createDocument({
      ...data,
      type: data.type || 'INVOICE',
    }),

  /**
   * Met à jour une facture
   */
  update: (id: string, data: DocumentUpdate) =>
    commercialApi.updateDocument(id, data),

  /**
   * Valide une facture
   */
  validate: (id: string) => commercialApi.validateDocument(id),

  /**
   * Envoie une facture au client
   */
  send: (id: string) => commercialApi.sendDocument(id),

  /**
   * Annule une facture
   */
  cancel: (id: string) => commercialApi.cancelDocument(id),

  /**
   * Crée un avoir depuis une facture
   */
  createCreditNote: (invoiceId: string) =>
    commercialApi.createCreditNote(invoiceId),

  // ==========================================================================
  // Paiements
  // ==========================================================================

  /**
   * Liste les paiements d'une facture
   */
  listPayments: (factureId: string) =>
    commercialApi.listPayments(factureId),

  /**
   * Enregistre un paiement sur une facture
   */
  createPayment: (data: PaymentCreate) =>
    commercialApi.createPayment(data),

  // ==========================================================================
  // Clients
  // ==========================================================================

  /**
   * Recherche des clients
   */
  searchCustomers: (filters?: CustomerFilters) =>
    commercialApi.listCustomers(filters),
};

export default facturesApi;
