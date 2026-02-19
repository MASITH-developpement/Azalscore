/**
 * AZALSCORE - Qualite API
 * =======================
 * API client pour le module Qualite
 * Couvre: Non-conformites, Regles QC, Inspections
 */

import { api } from '@/core/api-client';
import type { NonConformance, QCRule, QCInspection, QualityDashboard } from './types';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type { NonConformance, QCRule, QCInspection, QualityDashboard };

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface NCFilters {
  type?: string;
  status?: string;
  severity?: string;
  origin?: string;
  product_id?: string;
  lot_number?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface QCRuleFilters {
  type?: string;
  product_id?: string;
  is_active?: boolean;
}

export interface InspectionFilters {
  type?: string;
  status?: string;
  product_id?: string;
  lot_number?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface NCCreate {
  type: string;
  origin: string;
  severity: string;
  detected_date: string;
  description: string;
  product_id?: string;
  lot_number?: string;
  quantity_affected?: number;
  responsible_id?: string;
  target_date?: string;
}

export interface QCRuleCreate {
  code: string;
  name: string;
  type: string;
  product_id?: string;
  parameters?: Array<{
    name: string;
    min_value?: number;
    max_value?: number;
    target_value?: number;
    unit?: string;
  }>;
}

export interface InspectionCreate {
  type: string;
  product_id: string;
  lot_number?: string;
  quantity_inspected: number;
  rule_id?: string;
  notes?: string;
}

// ============================================================================
// HELPERS
// ============================================================================

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

export const qualiteApi = {
  // ==========================================================================
  // Dashboard
  // ==========================================================================

  /**
   * Recupere le tableau de bord qualite
   */
  getDashboard: () =>
    api.get<QualityDashboard>('/quality/dashboard'),

  // ==========================================================================
  // Non-conformites
  // ==========================================================================

  /**
   * Liste les non-conformites
   */
  listNonConformances: (filters?: NCFilters) =>
    api.get<NonConformance[]>(`/quality/non-conformances${buildQueryString(filters || {})}`),

  /**
   * Recupere une NC par son ID
   */
  getNonConformance: (id: string) =>
    api.get<NonConformance>(`/quality/non-conformances/${id}`),

  /**
   * Cree une nouvelle NC
   */
  createNonConformance: (data: NCCreate) =>
    api.post<NonConformance>('/quality/non-conformances', data),

  /**
   * Met a jour une NC
   */
  updateNonConformance: (id: string, data: Partial<NCCreate>) =>
    api.patch<NonConformance>(`/quality/non-conformances/${id}`, data),

  /**
   * Change le statut d'une NC
   */
  updateNCStatus: (id: string, status: string) =>
    api.patch<NonConformance>(`/quality/non-conformances/${id}`, { status }),

  /**
   * Cloture une NC
   */
  closeNonConformance: (id: string) =>
    api.post<NonConformance>(`/quality/non-conformances/${id}/close`, {}),

  /**
   * Ajoute un commentaire a une NC
   */
  addNCComment: (id: string, comment: string) =>
    api.post(`/quality/non-conformances/${id}/comments`, { comment }),

  /**
   * Upload un document sur une NC
   */
  uploadNCDocument: (id: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/quality/non-conformances/${id}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // ==========================================================================
  // Regles QC
  // ==========================================================================

  /**
   * Liste les regles QC
   */
  listQCRules: (filters?: QCRuleFilters) =>
    api.get<QCRule[]>(`/qc/rules${buildQueryString(filters || {})}`),

  /**
   * Recupere une regle par son ID
   */
  getQCRule: (id: string) =>
    api.get<QCRule>(`/qc/rules/${id}`),

  /**
   * Cree une nouvelle regle
   */
  createQCRule: (data: QCRuleCreate) =>
    api.post<QCRule>('/qc/rules', data),

  /**
   * Met a jour une regle
   */
  updateQCRule: (id: string, data: Partial<QCRuleCreate>) =>
    api.put<QCRule>(`/qc/rules/${id}`, data),

  /**
   * Active/desactive une regle
   */
  toggleQCRule: (id: string, isActive: boolean) =>
    api.patch<QCRule>(`/qc/rules/${id}`, { is_active: isActive }),

  /**
   * Supprime une regle
   */
  deleteQCRule: (id: string) =>
    api.delete(`/qc/rules/${id}`),

  // ==========================================================================
  // Inspections
  // ==========================================================================

  /**
   * Liste les inspections
   */
  listInspections: (filters?: InspectionFilters) =>
    api.get<QCInspection[]>(`/qc/inspections${buildQueryString(filters || {})}`),

  /**
   * Recupere une inspection par son ID
   */
  getInspection: (id: string) =>
    api.get<QCInspection>(`/qc/inspections/${id}`),

  /**
   * Cree une nouvelle inspection
   */
  createInspection: (data: InspectionCreate) =>
    api.post<QCInspection>('/qc/inspections', data),

  /**
   * Met a jour une inspection
   */
  updateInspection: (id: string, data: Partial<InspectionCreate>) =>
    api.put<QCInspection>(`/qc/inspections/${id}`, data),

  /**
   * Valide une inspection
   */
  validateInspection: (id: string, results: Record<string, unknown>) =>
    api.post<QCInspection>(`/qc/inspections/${id}/validate`, results),

  /**
   * Annule une inspection
   */
  cancelInspection: (id: string) =>
    api.post<QCInspection>(`/qc/inspections/${id}/cancel`, {}),
};

export default qualiteApi;
