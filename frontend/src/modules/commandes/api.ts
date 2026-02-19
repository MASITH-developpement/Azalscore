/**
 * AZALSCORE - Commandes API
 * =========================
 * API client pour le module Commandes
 * Utilise l'API commerciale partagée
 *
 * Numérotation: COM-YY-MM-XXXX
 * Flux: CRM → DEV → [COM] → AFF → FAC/AVO → CPT
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

export type { CommercialDocument as Commande } from '@/core/commercial-api';
export type { DocumentCreate as CommandeCreate } from '@/core/commercial-api';
export type { DocumentUpdate as CommandeUpdate } from '@/core/commercial-api';
export type { DocumentLine, DocumentLineCreate } from '@/core/commercial-api';
export type { Customer } from '@/core/commercial-api';

// ============================================================================
// TYPES SPÉCIFIQUES COMMANDES
// ============================================================================

export interface CommandeFilters extends Omit<DocumentFilters, 'type'> {}

// ============================================================================
// API CLIENT COMMANDES
// ============================================================================

export const commandesApi = {
  // ==========================================================================
  // Commandes
  // ==========================================================================

  /**
   * Liste les commandes
   */
  list: (filters?: CommandeFilters) =>
    commercialApi.listDocuments({
      ...filters,
      type: 'ORDER',
    }),

  /**
   * Récupère une commande par son ID
   */
  get: (id: string) => commercialApi.getDocument(id),

  /**
   * Crée une nouvelle commande
   */
  create: (data: Omit<DocumentCreate, 'type'>) =>
    commercialApi.createDocument({
      ...data,
      type: 'ORDER',
    }),

  /**
   * Met à jour une commande
   */
  update: (id: string, data: DocumentUpdate) =>
    commercialApi.updateDocument(id, data),

  /**
   * Supprime une commande (brouillon uniquement)
   */
  delete: (id: string) => commercialApi.deleteDocument(id),

  /**
   * Valide une commande
   */
  validate: (id: string) => commercialApi.validateDocument(id),

  /**
   * Marque une commande comme livrée
   */
  markDelivered: (id: string) => commercialApi.markOrderDelivered(id),

  /**
   * Crée une facture depuis une commande
   */
  createInvoice: (id: string) => commercialApi.createInvoiceFromOrder(id),

  /**
   * Crée une affaire depuis une commande
   */
  createAffaire: (id: string) => commercialApi.createAffaireFromOrder(id),

  // ==========================================================================
  // Lignes
  // ==========================================================================

  /**
   * Ajoute une ligne à la commande
   */
  addLine: (commandeId: string, data: DocumentLineCreate) =>
    commercialApi.addLine(commandeId, data),

  /**
   * Met à jour une ligne
   */
  updateLine: (commandeId: string, lineId: string, data: Partial<DocumentLineCreate>) =>
    commercialApi.updateLine(commandeId, lineId, data),

  /**
   * Supprime une ligne
   */
  deleteLine: (commandeId: string, lineId: string) =>
    commercialApi.deleteLine(commandeId, lineId),

  // ==========================================================================
  // Clients
  // ==========================================================================

  /**
   * Recherche des clients
   */
  searchCustomers: (filters?: CustomerFilters) =>
    commercialApi.listCustomers(filters),
};

export default commandesApi;
