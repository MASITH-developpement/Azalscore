/**
 * AZALSCORE - Devis API
 * =====================
 * API client pour le module Devis
 * Utilise l'API commerciale partagée
 *
 * Numérotation: DEV-YY-MM-XXXX
 * Flux: CRM → [DEV] → COM/ODS → AFF → FAC/AVO → CPT
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
// RE-EXPORTS pour faciliter l'import depuis le module
// ============================================================================

export type { CommercialDocument as Devis } from '@/core/commercial-api';
export type { DocumentCreate as DevisCreate } from '@/core/commercial-api';
export type { DocumentUpdate as DevisUpdate } from '@/core/commercial-api';
export type { DocumentLine, DocumentLineCreate } from '@/core/commercial-api';
export type { Customer } from '@/core/commercial-api';

// ============================================================================
// TYPES SPÉCIFIQUES DEVIS
// ============================================================================

export interface DevisFilters extends Omit<DocumentFilters, 'type'> {}

// ============================================================================
// API CLIENT DEVIS
// ============================================================================

export const devisApi = {
  // ==========================================================================
  // Devis
  // ==========================================================================

  /**
   * Liste les devis
   */
  list: (filters?: DevisFilters) =>
    commercialApi.listDocuments({
      ...filters,
      type: 'QUOTE',
    }),

  /**
   * Récupère un devis par son ID
   */
  get: (id: string) => commercialApi.getDocument(id),

  /**
   * Crée un nouveau devis
   */
  create: (data: Omit<DocumentCreate, 'type'>) =>
    commercialApi.createDocument({
      ...data,
      type: 'QUOTE',
    }),

  /**
   * Met à jour un devis
   */
  update: (id: string, data: DocumentUpdate) =>
    commercialApi.updateDocument(id, data),

  /**
   * Supprime un devis (brouillon uniquement)
   */
  delete: (id: string) => commercialApi.deleteDocument(id),

  /**
   * Valide un devis
   */
  validate: (id: string) => commercialApi.validateDocument(id),

  /**
   * Envoie un devis au client
   */
  send: (id: string) => commercialApi.sendDocument(id),

  /**
   * Convertit un devis en commande
   */
  convertToOrder: (id: string) => commercialApi.convertQuoteToOrder(id),

  // ==========================================================================
  // Lignes
  // ==========================================================================

  /**
   * Ajoute une ligne au devis
   */
  addLine: (devisId: string, data: DocumentLineCreate) =>
    commercialApi.addLine(devisId, data),

  /**
   * Met à jour une ligne
   */
  updateLine: (devisId: string, lineId: string, data: Partial<DocumentLineCreate>) =>
    commercialApi.updateLine(devisId, lineId, data),

  /**
   * Supprime une ligne
   */
  deleteLine: (devisId: string, lineId: string) =>
    commercialApi.deleteLine(devisId, lineId),

  // ==========================================================================
  // Clients
  // ==========================================================================

  /**
   * Recherche des clients
   */
  searchCustomers: (filters?: CustomerFilters) =>
    commercialApi.listCustomers(filters),
};

export default devisApi;
