/**
 * AZALSCORE - Affaires API
 * ========================
 * API client pour le module Affaires (Projets)
 * Couvre: Affaires, Tâches, Budget, Planning
 */

import { api } from '@/core/api-client';

// ============================================================================
// TYPES
// ============================================================================

export type AffaireStatus = 'draft' | 'planning' | 'in_progress' | 'on_hold' | 'completed' | 'cancelled';
export type AffairePriority = 'low' | 'medium' | 'high' | 'critical';

export interface Affaire {
  id: string;
  reference?: string;
  code?: string;
  name: string;
  description?: string;
  customer_id?: string;
  customer_name?: string;
  status: AffaireStatus;
  priority: AffairePriority;
  progress_percent?: number;
  planned_budget?: number;
  actual_cost?: number;
  planned_start_date?: string;
  planned_end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  manager_id?: string;
  manager_name?: string;
  team_members?: Array<{
    id: string;
    name: string;
    role?: string;
  }>;
  tags?: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface AffaireTask {
  id: string;
  affaire_id: string;
  name: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: AffairePriority;
  assigned_to?: string;
  assigned_to_name?: string;
  due_date?: string;
  completed_at?: string;
  estimated_hours?: number;
  actual_hours?: number;
  order_index: number;
  created_at: string;
}

export interface AffaireDocument {
  id: string;
  affaire_id: string;
  name: string;
  type: string;
  url?: string;
  size?: number;
  created_at: string;
  created_by?: string;
}

export interface AffaireStats {
  total: number;
  draft: number;
  planning: number;
  in_progress: number;
  on_hold: number;
  completed: number;
  cancelled: number;
  total_budget: number;
  total_actual_cost: number;
}

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface AffaireFilters {
  status?: AffaireStatus;
  priority?: AffairePriority;
  customer_id?: string;
  manager_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface AffaireCreate {
  name: string;
  code?: string;
  description?: string;
  customer_id?: string;
  status?: AffaireStatus;
  priority?: AffairePriority;
  planned_budget?: number;
  planned_start_date?: string;
  planned_end_date?: string;
  manager_id?: string;
  tags?: string[];
  notes?: string;
}

export interface AffaireUpdate extends Partial<AffaireCreate> {
  progress_percent?: number;
  actual_cost?: number;
  actual_start_date?: string;
  actual_end_date?: string;
}

export interface TaskCreate {
  name: string;
  description?: string;
  priority?: AffairePriority;
  assigned_to?: string;
  due_date?: string;
  estimated_hours?: number;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/projects';

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

export const affairesApi = {
  // ==========================================================================
  // Dashboard
  // ==========================================================================

  /**
   * Récupère les statistiques des affaires
   */
  getStats: () =>
    api.get<AffaireStats>(`${BASE_PATH}/stats`),

  // ==========================================================================
  // Affaires
  // ==========================================================================

  /**
   * Liste les affaires avec filtres
   */
  list: (filters?: AffaireFilters) =>
    api.get<PaginatedResponse<Affaire>>(
      `${BASE_PATH}${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère une affaire par son ID
   */
  get: (id: string) =>
    api.get<Affaire>(`${BASE_PATH}/${id}`),

  /**
   * Crée une nouvelle affaire
   */
  create: (data: AffaireCreate) =>
    api.post<Affaire>(BASE_PATH, data),

  /**
   * Met à jour une affaire
   */
  update: (id: string, data: AffaireUpdate) =>
    api.put<Affaire>(`${BASE_PATH}/${id}`, data),

  /**
   * Supprime une affaire
   */
  delete: (id: string) =>
    api.delete(`${BASE_PATH}/${id}`),

  // ==========================================================================
  // Workflow
  // ==========================================================================

  /**
   * Démarre une affaire
   */
  start: (id: string) =>
    api.post<Affaire>(`${BASE_PATH}/${id}/start`, {}),

  /**
   * Met en pause une affaire
   */
  pause: (id: string) =>
    api.post<Affaire>(`${BASE_PATH}/${id}/pause`, {}),

  /**
   * Reprend une affaire
   */
  resume: (id: string) =>
    api.post<Affaire>(`${BASE_PATH}/${id}/resume`, {}),

  /**
   * Termine une affaire
   */
  complete: (id: string) =>
    api.post<Affaire>(`${BASE_PATH}/${id}/complete`, {}),

  /**
   * Annule une affaire
   */
  cancel: (id: string) =>
    api.post<Affaire>(`${BASE_PATH}/${id}/cancel`, {}),

  // ==========================================================================
  // Tasks
  // ==========================================================================

  /**
   * Liste les tâches d'une affaire
   */
  listTasks: (affaireId: string) =>
    api.get<AffaireTask[]>(`${BASE_PATH}/${affaireId}/tasks`),

  /**
   * Crée une tâche
   */
  createTask: (affaireId: string, data: TaskCreate) =>
    api.post<AffaireTask>(`${BASE_PATH}/${affaireId}/tasks`, data),

  /**
   * Met à jour une tâche
   */
  updateTask: (affaireId: string, taskId: string, data: Partial<TaskCreate>) =>
    api.put<AffaireTask>(`${BASE_PATH}/${affaireId}/tasks/${taskId}`, data),

  /**
   * Termine une tâche
   */
  completeTask: (affaireId: string, taskId: string) =>
    api.post<AffaireTask>(`${BASE_PATH}/${affaireId}/tasks/${taskId}/complete`, {}),

  /**
   * Supprime une tâche
   */
  deleteTask: (affaireId: string, taskId: string) =>
    api.delete(`${BASE_PATH}/${affaireId}/tasks/${taskId}`),

  // ==========================================================================
  // Documents
  // ==========================================================================

  /**
   * Liste les documents d'une affaire
   */
  listDocuments: (affaireId: string) =>
    api.get<AffaireDocument[]>(`${BASE_PATH}/${affaireId}/documents`),

  /**
   * Upload un document
   */
  uploadDocument: (affaireId: string, file: File, name?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    return api.post<AffaireDocument>(
      `${BASE_PATH}/${affaireId}/documents`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  },

  /**
   * Supprime un document
   */
  deleteDocument: (affaireId: string, documentId: string) =>
    api.delete(`${BASE_PATH}/${affaireId}/documents/${documentId}`),
};

export default affairesApi;
