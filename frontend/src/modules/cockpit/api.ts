/**
 * AZALSCORE - Cockpit API
 * =======================
 * API client pour le module Cockpit (Vue globale flux commercial)
 * Agrege les donnees de: CRM, Devis, Commandes, ODS, Affaires, Factures
 */

import { api } from '@/core/api-client';

// ============================================================================
// TYPES
// ============================================================================

export interface FluxStats {
  crm: { prospects: number; clients: number; opportunites: number };
  devis: { total: number; en_attente: number; acceptes: number; refuses: number; montant_total: number };
  commandes: { total: number; en_cours: number; livrees: number; montant_total: number };
  ods: { total: number; a_planifier: number; en_cours: number; terminees: number };
  affaires: { total: number; en_cours: number; terminees: number; ca_total: number };
  factures: { total: number; en_attente: number; payees: number; montant_total: number; montant_encaisse: number };
}

export interface RecentItem {
  id: string;
  reference: string;
  label: string;
  type: 'devis' | 'commande' | 'ods' | 'affaire' | 'facture';
  status: string;
  date: string;
  montant?: number;
}

export interface RiskAlert {
  id: string;
  identifier: string;
  partner_name: string;
  score: number;
  level: 'elevated' | 'high';
  level_label: string;
  alerts: string[];
  recommendation: string;
  analyzed_at: string;
}

export interface StrategicKPIData {
  kpi: string;
  value: number;
  unit: string;
  status: string;
  color: string;
  details: Record<string, unknown>;
  recommendations: string[];
}

export interface AllStrategicKPIs {
  cash_runway: StrategicKPIData;
  profit_margin: StrategicKPIData;
  customer_concentration: StrategicKPIData;
  working_capital: StrategicKPIData;
  employee_productivity: StrategicKPIData;
  generated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

export interface DocumentItem {
  id: string;
  reference: string;
  customer_name?: string;
  status: string;
  created_at: string;
  total?: number;
  subtotal?: number;
}

export interface InterventionItem {
  id: string;
  reference: string;
  title?: string;
  status: string;
  created_at: string;
}

export interface ProjectItem {
  id: string;
  reference: string;
  name?: string;
  status: string;
  budget_total?: number;
}

export interface OpportunityItem {
  id: string;
  name: string;
  status: string;
}

// ============================================================================
// API CLIENT
// ============================================================================

export const cockpitApi = {
  // ==========================================================================
  // Strategic KPIs
  // ==========================================================================

  /**
   * Recupere tous les KPIs strategiques
   */
  getStrategicKPIs: () =>
    api.get<AllStrategicKPIs>('/cockpit/helpers/all-strategic'),

  // ==========================================================================
  // Risk Alerts
  // ==========================================================================

  /**
   * Recupere les alertes de risque
   */
  getRiskAlerts: () =>
    api.get<RiskAlert[]>('/enrichment/risk/alerts'),

  // ==========================================================================
  // Data Aggregation (pour calcul des stats)
  // ==========================================================================

  /**
   * Liste les clients
   */
  getCustomers: (pageSize = 1) =>
    api.get<PaginatedResponse<unknown>>(`/commercial/customers?page_size=${pageSize}`),

  /**
   * Liste les opportunites
   */
  getOpportunities: (pageSize = 100) =>
    api.get<PaginatedResponse<OpportunityItem>>(`/commercial/opportunities?page_size=${pageSize}`),

  /**
   * Liste les devis
   */
  getDevis: (pageSize = 100) =>
    api.get<PaginatedResponse<DocumentItem>>(`/commercial/documents?type=QUOTE&page_size=${pageSize}`),

  /**
   * Liste les commandes
   */
  getCommandes: (pageSize = 100) =>
    api.get<PaginatedResponse<DocumentItem>>(`/commercial/documents?type=ORDER&page_size=${pageSize}`),

  /**
   * Liste les factures
   */
  getFactures: (pageSize = 100) =>
    api.get<PaginatedResponse<DocumentItem>>(`/commercial/documents?type=INVOICE&page_size=${pageSize}`),

  /**
   * Liste les interventions
   */
  getInterventions: (pageSize = 100) =>
    api.get<PaginatedResponse<InterventionItem>>(`/interventions?page_size=${pageSize}`),

  /**
   * Liste les projets/affaires
   */
  getProjects: (limit = 200) =>
    api.get<PaginatedResponse<ProjectItem>>(`/projects?limit=${limit}`),

  // ==========================================================================
  // Recent Activity (limite)
  // ==========================================================================

  /**
   * Recupere les devis recents
   */
  getRecentDevis: (limit = 5) =>
    api.get<PaginatedResponse<DocumentItem>>(`/commercial/documents?type=QUOTE&limit=${limit}`),

  /**
   * Recupere les commandes recentes
   */
  getRecentCommandes: (limit = 5) =>
    api.get<PaginatedResponse<DocumentItem>>(`/commercial/documents?type=ORDER&limit=${limit}`),

  /**
   * Recupere les interventions recentes
   */
  getRecentInterventions: (limit = 5) =>
    api.get<PaginatedResponse<InterventionItem>>(`/interventions?limit=${limit}`),

  /**
   * Recupere les factures recentes
   */
  getRecentFactures: (limit = 5) =>
    api.get<PaginatedResponse<DocumentItem>>(`/commercial/documents?type=INVOICE&limit=${limit}`),
};

export default cockpitApi;
