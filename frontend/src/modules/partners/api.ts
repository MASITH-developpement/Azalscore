/**
 * AZALSCORE - Partners API
 * ========================
 * API client pour le module Partenaires
 * Couvre: Clients, Fournisseurs, Contacts
 */

import { api } from '@/core/api-client';
import type { Partner, Client } from './types';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type { Partner, Client };

// ============================================================================
// TYPES - Request/Response
// ============================================================================

export type PartnerType = 'client' | 'supplier' | 'contact';

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PartnerFilters {
  search?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface PartnerCreate {
  name: string;
  code?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  fax?: string;
  website?: string;
  address?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  state?: string;
  country?: string;
  vat_number?: string;
  siret?: string;
  siren?: string;
  legal_form?: string;
  capital?: number;
  employee_count?: number;
  naf_code?: string;
  notes?: string;
  tags?: string[];
  is_active?: boolean;
}

export interface PartnerUpdate extends Partial<PartnerCreate> {}

export interface PartnerDocument {
  id: string;
  name: string;
  type: string;
  url: string;
  size?: number;
  created_at: string;
}

export interface PartnerTransaction {
  id: string;
  type: 'invoice' | 'order' | 'quote' | 'payment';
  reference: string;
  date: string;
  amount: number;
  currency: string;
  status: string;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/partners';

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

function getTypePath(type: PartnerType): string {
  return `${type}s`; // clients, suppliers, contacts
}

// ============================================================================
// API CLIENT
// ============================================================================

export const partnersApi = {
  // ==========================================================================
  // Partners (Generic)
  // ==========================================================================

  /**
   * Liste les partenaires d'un type donné
   */
  list: (type: PartnerType, filters?: PartnerFilters) =>
    api.get<PaginatedResponse<Partner>>(
      `${BASE_PATH}/${getTypePath(type)}${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère un partenaire par son ID
   */
  get: (type: PartnerType, id: string) =>
    api.get<Partner>(`${BASE_PATH}/${getTypePath(type)}/${id}`),

  /**
   * Crée un nouveau partenaire
   */
  create: (type: PartnerType, data: PartnerCreate) =>
    api.post<Partner>(`${BASE_PATH}/${getTypePath(type)}`, data),

  /**
   * Met à jour un partenaire
   */
  update: (type: PartnerType, id: string, data: PartnerUpdate) =>
    api.put<Partner>(`${BASE_PATH}/${getTypePath(type)}/${id}`, data),

  /**
   * Supprime un partenaire
   */
  delete: (type: PartnerType, id: string) =>
    api.delete(`${BASE_PATH}/${getTypePath(type)}/${id}`),

  /**
   * Archive un partenaire (désactive)
   */
  archive: (type: PartnerType, id: string) =>
    api.post<Partner>(`${BASE_PATH}/${getTypePath(type)}/${id}/archive`, {}),

  /**
   * Réactive un partenaire
   */
  restore: (type: PartnerType, id: string) =>
    api.post<Partner>(`${BASE_PATH}/${getTypePath(type)}/${id}/restore`, {}),

  // ==========================================================================
  // Clients (Shortcuts)
  // ==========================================================================

  /**
   * Liste les clients
   */
  listClients: (filters?: PartnerFilters) =>
    partnersApi.list('client', filters),

  /**
   * Récupère un client par son ID
   */
  getClient: (id: string) =>
    partnersApi.get('client', id),

  /**
   * Crée un nouveau client
   */
  createClient: (data: PartnerCreate) =>
    partnersApi.create('client', data),

  /**
   * Met à jour un client
   */
  updateClient: (id: string, data: PartnerUpdate) =>
    partnersApi.update('client', id, data),

  // ==========================================================================
  // Suppliers (Shortcuts)
  // ==========================================================================

  /**
   * Liste les fournisseurs
   */
  listSuppliers: (filters?: PartnerFilters) =>
    partnersApi.list('supplier', filters),

  /**
   * Récupère un fournisseur par son ID
   */
  getSupplier: (id: string) =>
    partnersApi.get('supplier', id),

  /**
   * Crée un nouveau fournisseur
   */
  createSupplier: (data: PartnerCreate) =>
    partnersApi.create('supplier', data),

  /**
   * Met à jour un fournisseur
   */
  updateSupplier: (id: string, data: PartnerUpdate) =>
    partnersApi.update('supplier', id, data),

  // ==========================================================================
  // Contacts (Shortcuts)
  // ==========================================================================

  /**
   * Liste les contacts
   */
  listContacts: (filters?: PartnerFilters) =>
    partnersApi.list('contact', filters),

  /**
   * Récupère un contact par son ID
   */
  getContact: (id: string) =>
    partnersApi.get('contact', id),

  /**
   * Crée un nouveau contact
   */
  createContact: (data: PartnerCreate) =>
    partnersApi.create('contact', data),

  /**
   * Met à jour un contact
   */
  updateContact: (id: string, data: PartnerUpdate) =>
    partnersApi.update('contact', id, data),

  // ==========================================================================
  // Documents
  // ==========================================================================

  /**
   * Liste les documents d'un partenaire
   */
  listDocuments: (type: PartnerType, partnerId: string) =>
    api.get<PartnerDocument[]>(`${BASE_PATH}/${getTypePath(type)}/${partnerId}/documents`),

  /**
   * Upload un document
   */
  uploadDocument: (type: PartnerType, partnerId: string, file: File, name?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    return api.post<PartnerDocument>(
      `${BASE_PATH}/${getTypePath(type)}/${partnerId}/documents`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  },

  // ==========================================================================
  // Transactions
  // ==========================================================================

  /**
   * Liste les transactions d'un partenaire
   */
  listTransactions: (type: PartnerType, partnerId: string) =>
    api.get<PartnerTransaction[]>(`${BASE_PATH}/${getTypePath(type)}/${partnerId}/transactions`),
};

export default partnersApi;
