/**
 * AZALS MODULE - Contacts Unifiés - API Client
 * ============================================
 *
 * Client API pour la gestion des contacts.
 * Utilise le client API central pour l'authentification.
 */

import { api } from '@core/api-client';
import type {
  Contact,
  ContactCreate,
  ContactUpdate,
  ContactList,
  ContactLookupList,
  ContactFilters,
  ContactPerson,
  ContactPersonCreate,
  ContactPersonUpdate,
  ContactAddress,
  ContactAddressCreate,
  ContactAddressUpdate,
  ContactStats,
  RelationType,
} from './types';

const API_BASE = '/contacts';

// ============================================================================
// HELPERS
// ============================================================================

function buildQueryString(params: Record<string, string | number | boolean | undefined>): string {
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
// CONTACTS API
// ============================================================================

export const contactsApi = {
  /**
   * Créer un nouveau contact
   */
  async create(data: ContactCreate): Promise<Contact> {
    const response = await api.post<Contact>(API_BASE, data);
    return response.data;
  },

  /**
   * Lister les contacts avec filtres et pagination
   */
  async list(filters: ContactFilters = {}): Promise<ContactList> {
    const queryString = buildQueryString({
      entity_type: filters.entity_type,
      relation_type: filters.relation_type,
      is_active: filters.is_active,
      search: filters.search,
      page: filters.page,
      page_size: filters.page_size,
    });
    const response = await api.get<ContactList>(`${API_BASE}${queryString}`);
    return response.data;
  },

  /**
   * Recherche rapide pour les sélecteurs (lookup)
   */
  async lookup(relationFilter?: RelationType, search?: string, limit = 50): Promise<ContactLookupList> {
    const queryString = buildQueryString({
      relation_type: relationFilter,
      search,
      limit,
    });
    const response = await api.get<ContactLookupList>(`${API_BASE}/lookup${queryString}`);
    return response.data;
  },

  /**
   * Récupérer un contact par ID
   */
  async get(id: string): Promise<Contact> {
    const response = await api.get<Contact>(`${API_BASE}/${id}`);
    return response.data;
  },

  /**
   * Récupérer un contact par code
   */
  async getByCode(code: string): Promise<Contact> {
    const response = await api.get<Contact>(`${API_BASE}/code/${code}`);
    return response.data;
  },

  /**
   * Mettre à jour un contact
   */
  async update(id: string, data: ContactUpdate): Promise<Contact> {
    const response = await api.put<Contact>(`${API_BASE}/${id}`, data);
    return response.data;
  },

  /**
   * Supprimer un contact (soft delete par défaut)
   */
  async delete(id: string, permanent = false): Promise<void> {
    const queryString = permanent ? '?permanent=true' : '';
    await api.delete(`${API_BASE}/${id}${queryString}`);
  },

  /**
   * Récupérer les statistiques d'un contact
   */
  async getStats(id: string): Promise<ContactStats> {
    const response = await api.get<ContactStats>(`${API_BASE}/${id}/stats`);
    return response.data;
  },

  /**
   * Uploader le logo d'un contact
   */
  async uploadLogo(id: string, file: File): Promise<Contact> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<Contact>(`${API_BASE}/${id}/logo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  /**
   * Supprimer le logo d'un contact
   */
  async deleteLogo(id: string): Promise<Contact> {
    const response = await api.delete<Contact>(`${API_BASE}/${id}/logo`);
    return response.data;
  },
};

// ============================================================================
// PERSONNES DE CONTACT API
// ============================================================================

export const contactPersonsApi = {
  /**
   * Ajouter une personne de contact
   */
  async create(contactId: string, data: ContactPersonCreate): Promise<ContactPerson> {
    const response = await api.post<ContactPerson>(`${API_BASE}/${contactId}/persons`, data);
    return response.data;
  },

  /**
   * Lister les personnes d'un contact
   */
  async list(contactId: string, isActive?: boolean): Promise<ContactPerson[]> {
    const queryString = isActive !== undefined ? `?is_active=${isActive}` : '';
    const response = await api.get<ContactPerson[]>(`${API_BASE}/${contactId}/persons${queryString}`);
    return response.data;
  },

  /**
   * Récupérer une personne de contact
   */
  async get(contactId: string, personId: string): Promise<ContactPerson> {
    const response = await api.get<ContactPerson>(`${API_BASE}/${contactId}/persons/${personId}`);
    return response.data;
  },

  /**
   * Mettre à jour une personne de contact
   */
  async update(contactId: string, personId: string, data: ContactPersonUpdate): Promise<ContactPerson> {
    const response = await api.put<ContactPerson>(`${API_BASE}/${contactId}/persons/${personId}`, data);
    return response.data;
  },

  /**
   * Supprimer une personne de contact
   */
  async delete(contactId: string, personId: string): Promise<void> {
    await api.delete(`${API_BASE}/${contactId}/persons/${personId}`);
  },
};

// ============================================================================
// ADRESSES API
// ============================================================================

export const contactAddressesApi = {
  /**
   * Ajouter une adresse
   */
  async create(contactId: string, data: ContactAddressCreate): Promise<ContactAddress> {
    const response = await api.post<ContactAddress>(`${API_BASE}/${contactId}/addresses`, data);
    return response.data;
  },

  /**
   * Lister les adresses d'un contact
   */
  async list(contactId: string, isActive?: boolean): Promise<ContactAddress[]> {
    const queryString = isActive !== undefined ? `?is_active=${isActive}` : '';
    const response = await api.get<ContactAddress[]>(`${API_BASE}/${contactId}/addresses${queryString}`);
    return response.data;
  },

  /**
   * Récupérer une adresse
   */
  async get(contactId: string, addressId: string): Promise<ContactAddress> {
    const response = await api.get<ContactAddress>(`${API_BASE}/${contactId}/addresses/${addressId}`);
    return response.data;
  },

  /**
   * Mettre à jour une adresse
   */
  async update(contactId: string, addressId: string, data: ContactAddressUpdate): Promise<ContactAddress> {
    const response = await api.put<ContactAddress>(`${API_BASE}/${contactId}/addresses/${addressId}`, data);
    return response.data;
  },

  /**
   * Supprimer une adresse
   */
  async delete(contactId: string, addressId: string): Promise<void> {
    await api.delete(`${API_BASE}/${contactId}/addresses/${addressId}`);
  },
};
