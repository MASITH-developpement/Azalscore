/**
 * AZALSCORE - CRM API
 * ===================
 * API client pour le module CRM (Gestion Relation Client)
 * Couvre: Clients, Opportunités, Pipeline, Activités
 */

import { api } from '@/core/api-client';
import type {
  Customer,
  Contact,
  Opportunity,
  Activity,
  PipelineStats,
  SalesDashboard,
  CustomerStats,
  CustomerType,
  OpportunityStatus,
  ActivityType,
  ActivityStatus,
} from './types';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type {
  Customer,
  Contact,
  Opportunity,
  Activity,
  PipelineStats,
  SalesDashboard,
  CustomerStats,
  CustomerType,
  OpportunityStatus,
  ActivityType,
  ActivityStatus,
};

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

export interface CustomerFilters {
  type?: CustomerType;
  search?: string;
  is_active?: boolean;
  assigned_to?: string;
  industry?: string;
  page?: number;
  page_size?: number;
}

export interface OpportunityFilters {
  status?: OpportunityStatus;
  customer_id?: string;
  assigned_to?: string;
  min_amount?: number;
  max_amount?: number;
  page?: number;
  page_size?: number;
}

export interface ActivityFilters {
  type?: ActivityType;
  status?: ActivityStatus;
  customer_id?: string;
  opportunity_id?: string;
  assigned_to?: string;
  page?: number;
  page_size?: number;
}

export interface CustomerCreate {
  name: string;
  legal_name?: string;
  type?: CustomerType;
  email?: string;
  phone?: string;
  mobile?: string;
  website?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  country_code?: string;
  tax_id?: string;
  registration_number?: string;
  industry?: string;
  source?: string;
  notes?: string;
  tags?: string[];
}

export interface OpportunityCreate {
  name: string;
  description?: string;
  customer_id: string;
  contact_id?: string;
  status?: OpportunityStatus;
  probability?: number;
  amount: number;
  currency?: string;
  expected_close_date?: string;
  source?: string;
  notes?: string;
}

export interface ActivityCreate {
  customer_id: string;
  contact_id?: string;
  opportunity_id?: string;
  type: ActivityType;
  status?: ActivityStatus;
  subject: string;
  description?: string;
  due_date?: string;
  assigned_to?: string;
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

export const crmApi = {
  // ==========================================================================
  // Dashboard
  // ==========================================================================

  /**
   * Récupère le tableau de bord commercial
   */
  getDashboard: () =>
    api.get<SalesDashboard>(`${BASE_PATH}/dashboard`),

  /**
   * Récupère les statistiques du pipeline
   */
  getPipelineStats: () =>
    api.get<PipelineStats>(`${BASE_PATH}/pipeline/stats`),

  /**
   * Récupère les statistiques d'un client
   */
  getCustomerStats: (customerId: string) =>
    api.get<CustomerStats>(`${BASE_PATH}/customers/${customerId}/stats`),

  // ==========================================================================
  // Customers (Clients)
  // ==========================================================================

  /**
   * Liste les clients avec filtres
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

  /**
   * Crée un nouveau client
   */
  createCustomer: (data: CustomerCreate) =>
    api.post<Customer>(`${BASE_PATH}/customers`, data),

  /**
   * Met à jour un client
   */
  updateCustomer: (customerId: string, data: Partial<CustomerCreate>) =>
    api.put<Customer>(`${BASE_PATH}/customers/${customerId}`, data),

  /**
   * Supprime un client
   */
  deleteCustomer: (customerId: string) =>
    api.delete(`${BASE_PATH}/customers/${customerId}`),

  /**
   * Convertit un prospect en client
   */
  convertProspect: (customerId: string) =>
    api.post<Customer>(`${BASE_PATH}/customers/${customerId}/convert`, {}),

  // ==========================================================================
  // Contacts
  // ==========================================================================

  /**
   * Liste les contacts d'un client
   */
  listContacts: (customerId: string) =>
    api.get<Contact[]>(`${BASE_PATH}/customers/${customerId}/contacts`),

  /**
   * Ajoute un contact à un client
   */
  createContact: (customerId: string, data: Partial<Contact>) =>
    api.post<Contact>(`${BASE_PATH}/customers/${customerId}/contacts`, data),

  /**
   * Met à jour un contact
   */
  updateContact: (customerId: string, contactId: string, data: Partial<Contact>) =>
    api.put<Contact>(`${BASE_PATH}/customers/${customerId}/contacts/${contactId}`, data),

  /**
   * Supprime un contact
   */
  deleteContact: (customerId: string, contactId: string) =>
    api.delete(`${BASE_PATH}/customers/${customerId}/contacts/${contactId}`),

  // ==========================================================================
  // Opportunities
  // ==========================================================================

  /**
   * Liste les opportunités avec filtres
   */
  listOpportunities: (filters?: OpportunityFilters) =>
    api.get<PaginatedResponse<Opportunity>>(
      `${BASE_PATH}/opportunities${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère une opportunité par son ID
   */
  getOpportunity: (opportunityId: string) =>
    api.get<Opportunity>(`${BASE_PATH}/opportunities/${opportunityId}`),

  /**
   * Crée une nouvelle opportunité
   */
  createOpportunity: (data: OpportunityCreate) =>
    api.post<Opportunity>(`${BASE_PATH}/opportunities`, data),

  /**
   * Met à jour une opportunité
   */
  updateOpportunity: (opportunityId: string, data: Partial<OpportunityCreate>) =>
    api.put<Opportunity>(`${BASE_PATH}/opportunities/${opportunityId}`, data),

  /**
   * Marque une opportunité comme gagnée
   */
  winOpportunity: (opportunityId: string, winReason?: string) =>
    api.post<Opportunity>(`${BASE_PATH}/opportunities/${opportunityId}/win`, { win_reason: winReason }),

  /**
   * Marque une opportunité comme perdue
   */
  loseOpportunity: (opportunityId: string, lossReason?: string) =>
    api.post<Opportunity>(`${BASE_PATH}/opportunities/${opportunityId}/lose`, { loss_reason: lossReason }),

  /**
   * Crée un devis depuis une opportunité
   */
  createQuoteFromOpportunity: (opportunityId: string) =>
    api.post<{ id: string; number: string }>(`${BASE_PATH}/opportunities/${opportunityId}/quote`, {}),

  // ==========================================================================
  // Activities
  // ==========================================================================

  /**
   * Liste les activités avec filtres
   */
  listActivities: (filters?: ActivityFilters) =>
    api.get<PaginatedResponse<Activity>>(
      `${BASE_PATH}/activities${buildQueryString(filters || {})}`
    ),

  /**
   * Crée une nouvelle activité
   */
  createActivity: (data: ActivityCreate) =>
    api.post<Activity>(`${BASE_PATH}/activities`, data),

  /**
   * Met à jour une activité
   */
  updateActivity: (activityId: string, data: Partial<ActivityCreate>) =>
    api.put<Activity>(`${BASE_PATH}/activities/${activityId}`, data),

  /**
   * Marque une activité comme terminée
   */
  completeActivity: (activityId: string) =>
    api.post<Activity>(`${BASE_PATH}/activities/${activityId}/complete`, {}),

  /**
   * Annule une activité
   */
  cancelActivity: (activityId: string) =>
    api.post<Activity>(`${BASE_PATH}/activities/${activityId}/cancel`, {}),
};

export default crmApi;
