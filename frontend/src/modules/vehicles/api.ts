/**
 * AZALSCORE - Vehicles API
 * ========================
 * API client pour le module Flotte Vehicules
 * Couvre: Vehicules, Pleins carburant, Frais kilometriques
 */

import { api } from '@/core/api-client';
import type { Vehicule, FuelType } from './types';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type { Vehicule, FuelType };

// ============================================================================
// LOCAL TYPES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface FuelLog {
  id: string;
  vehicle_id: string;
  date: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  mileage: number;
  station_name?: string;
  fuel_type: FuelType;
  created_at: string;
}

export interface MileageLog {
  id: string;
  vehicle_id: string;
  date: string;
  km_start: number;
  km_end: number;
  km_distance: number;
  purpose?: string;
  affaire_id?: string;
  affaire_reference?: string;
  cost_total: number;
  co2_total: number;
  created_at: string;
}

export interface VehicleStats {
  total_vehicles: number;
  active_vehicles: number;
  total_km: number;
  avg_cost_km: number;
  avg_co2_km: number;
  total_fuel_cost: number;
  total_maintenance_cost: number;
}

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface VehicleFilters {
  is_active?: boolean;
  fuel_type?: FuelType;
  employe_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface VehicleCreate {
  immatriculation: string;
  marque: string;
  modele: string;
  type_carburant: FuelType;
  conso_100km: number;
  prix_carburant: number;
  cout_entretien_km?: number;
  assurance_mois?: number;
  km_mois_estime?: number;
  prix_achat?: number;
  duree_amort_km?: number;
  co2_km?: number;
  norme_euro?: string;
  kilometrage_actuel?: number;
  date_mise_service?: string;
  employe_id?: string;
}

export interface FuelLogCreate {
  vehicle_id: string;
  date: string;
  quantity: number;
  unit_price: number;
  mileage: number;
  station_name?: string;
  fuel_type: FuelType;
}

export interface MileageLogCreate {
  vehicle_id: string;
  date: string;
  km_start: number;
  km_end: number;
  purpose?: string;
  affaire_id?: string;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/fleet';

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

export const vehiclesApi = {
  // ==========================================================================
  // Stats
  // ==========================================================================

  /**
   * Recupere les statistiques de la flotte
   */
  getStats: () =>
    api.get<VehicleStats>(`${BASE_PATH}/stats`),

  // ==========================================================================
  // Vehicles
  // ==========================================================================

  /**
   * Liste les vehicules
   */
  list: (filters?: VehicleFilters) =>
    api.get<PaginatedResponse<Vehicule>>(
      `${BASE_PATH}/vehicles${buildQueryString(filters || {})}`
    ),

  /**
   * Recupere un vehicule par son ID
   */
  get: (id: string) =>
    api.get<Vehicule>(`${BASE_PATH}/vehicles/${id}`),

  /**
   * Cree un nouveau vehicule
   */
  create: (data: VehicleCreate) =>
    api.post<Vehicule>(`${BASE_PATH}/vehicles`, data),

  /**
   * Met a jour un vehicule
   */
  update: (id: string, data: Partial<VehicleCreate>) =>
    api.put<Vehicule>(`${BASE_PATH}/vehicles/${id}`, data),

  /**
   * Supprime un vehicule
   */
  delete: (id: string) =>
    api.delete(`${BASE_PATH}/vehicles/${id}`),

  /**
   * Active/desactive un vehicule
   */
  toggle: (id: string, isActive: boolean) =>
    api.patch<Vehicule>(`${BASE_PATH}/vehicles/${id}`, { is_active: isActive }),

  /**
   * Affecte un vehicule a un employe
   */
  assign: (id: string, employeId: string | null) =>
    api.patch<Vehicule>(`${BASE_PATH}/vehicles/${id}`, { employe_id: employeId }),

  /**
   * Met a jour le kilometrage
   */
  updateMileage: (id: string, kilometrage: number) =>
    api.patch<Vehicule>(`${BASE_PATH}/vehicles/${id}`, { kilometrage_actuel: kilometrage }),

  // ==========================================================================
  // Fuel Logs
  // ==========================================================================

  /**
   * Liste les pleins d'un vehicule
   */
  listFuelLogs: (vehicleId: string) =>
    api.get<FuelLog[]>(`${BASE_PATH}/vehicles/${vehicleId}/fuel-logs`),

  /**
   * Ajoute un plein
   */
  addFuelLog: (data: FuelLogCreate) =>
    api.post<FuelLog>(`${BASE_PATH}/vehicles/${data.vehicle_id}/fuel-logs`, data),

  /**
   * Supprime un plein
   */
  deleteFuelLog: (vehicleId: string, logId: string) =>
    api.delete(`${BASE_PATH}/vehicles/${vehicleId}/fuel-logs/${logId}`),

  // ==========================================================================
  // Mileage Logs (Frais kilometriques)
  // ==========================================================================

  /**
   * Liste les trajets d'un vehicule
   */
  listMileageLogs: (vehicleId: string) =>
    api.get<MileageLog[]>(`${BASE_PATH}/vehicles/${vehicleId}/mileage-logs`),

  /**
   * Ajoute un trajet
   */
  addMileageLog: (data: MileageLogCreate) =>
    api.post<MileageLog>(`${BASE_PATH}/vehicles/${data.vehicle_id}/mileage-logs`, data),

  /**
   * Supprime un trajet
   */
  deleteMileageLog: (vehicleId: string, logId: string) =>
    api.delete(`${BASE_PATH}/vehicles/${vehicleId}/mileage-logs/${logId}`),

  /**
   * Liste tous les trajets (pour une affaire)
   */
  listAllMileageLogs: (affaireId?: string) =>
    api.get<MileageLog[]>(
      `${BASE_PATH}/mileage-logs${affaireId ? `?affaire_id=${affaireId}` : ''}`
    ),

  // ==========================================================================
  // Documents
  // ==========================================================================

  /**
   * Liste les documents d'un vehicule
   */
  listDocuments: (vehicleId: string) =>
    api.get<Array<{ id: string; name: string; type: string; url: string; created_at: string }>>(
      `${BASE_PATH}/vehicles/${vehicleId}/documents`
    ),

  /**
   * Upload un document
   */
  uploadDocument: (vehicleId: string, file: File, type?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (type) formData.append('type', type);
    return api.post(`${BASE_PATH}/vehicles/${vehicleId}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /**
   * Supprime un document
   */
  deleteDocument: (vehicleId: string, documentId: string) =>
    api.delete(`${BASE_PATH}/vehicles/${vehicleId}/documents/${documentId}`),
};

export default vehiclesApi;
