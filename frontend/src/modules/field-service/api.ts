/**
 * AZALSCORE - Field Service API
 * ==============================
 * Client API typé pour la gestion des interventions terrain
 */

import { api } from '@core/api-client';

// ============================================================================
// HELPERS
// ============================================================================

function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const str = query.toString();
  return str ? `?${str}` : '';
}

// ============================================================================
// ENUMS
// ============================================================================

export type InterventionStatus = 'PLANNED' | 'ASSIGNED' | 'EN_ROUTE' | 'ON_SITE' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type InterventionPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT' | 'EMERGENCY';
export type InterventionType = 'INSTALLATION' | 'MAINTENANCE' | 'REPAIR' | 'INSPECTION' | 'DELIVERY' | 'OTHER';
export type TechnicianStatus = 'AVAILABLE' | 'BUSY' | 'EN_ROUTE' | 'ON_SITE' | 'BREAK' | 'OFFLINE';

// ============================================================================
// TYPES - Zones
// ============================================================================

export interface Zone {
  id: number;
  tenant_id: string;
  name: string;
  code: string;
  description: string | null;
  polygon: Array<{ lat: number; lng: number }> | null;
  color: string;
  is_active: boolean;
  technicians_count: number;
  created_at: string;
}

export interface ZoneCreate {
  name: string;
  code: string;
  description?: string | null;
  polygon?: Array<{ lat: number; lng: number }> | null;
  color?: string;
}

export type ZoneUpdate = Partial<ZoneCreate> & { is_active?: boolean };

// ============================================================================
// TYPES - Technicians
// ============================================================================

export interface Technician {
  id: number;
  tenant_id: string;
  user_id: number;
  name: string;
  email: string;
  phone: string | null;
  status: TechnicianStatus;
  zone_ids: number[];
  skills: string[];
  vehicle_id: number | null;
  current_location: { lat: number; lng: number } | null;
  location_updated_at: string | null;
  max_interventions_per_day: number;
  today_interventions_count: number;
  is_active: boolean;
  created_at: string;
}

export interface TechnicianCreate {
  user_id: number;
  phone?: string | null;
  zone_ids?: number[];
  skills?: string[];
  vehicle_id?: number | null;
  max_interventions_per_day?: number;
}

export type TechnicianUpdate = Partial<TechnicianCreate> & { is_active?: boolean };

export interface TechnicianLocation {
  lat: number;
  lng: number;
  accuracy?: number;
  heading?: number;
  speed?: number;
}

// ============================================================================
// TYPES - Vehicles
// ============================================================================

export interface Vehicle {
  id: number;
  tenant_id: string;
  registration: string;
  brand: string;
  model: string;
  year: number | null;
  type: string;
  capacity: string | null;
  current_mileage: number;
  next_service_mileage: number | null;
  insurance_expiry: string | null;
  technical_inspection_expiry: string | null;
  assigned_technician_id: number | null;
  is_active: boolean;
  created_at: string;
}

export interface VehicleCreate {
  registration: string;
  brand: string;
  model: string;
  year?: number | null;
  type: string;
  capacity?: string | null;
  current_mileage?: number;
  next_service_mileage?: number | null;
  insurance_expiry?: string | null;
  technical_inspection_expiry?: string | null;
}

export type VehicleUpdate = Partial<VehicleCreate> & { is_active?: boolean };

// ============================================================================
// TYPES - Interventions
// ============================================================================

export interface Intervention {
  id: number;
  tenant_id: string;
  intervention_number: string;
  type: InterventionType;
  status: InterventionStatus;
  priority: InterventionPriority;
  subject: string;
  description: string | null;
  customer_id: number | null;
  customer_name: string | null;
  contact_name: string | null;
  contact_phone: string | null;
  address: string;
  lat: number | null;
  lng: number | null;
  zone_id: number | null;
  technician_id: number | null;
  technician_name: string | null;
  scheduled_date: string;
  scheduled_start_time: string | null;
  scheduled_end_time: string | null;
  actual_start_time: string | null;
  actual_end_time: string | null;
  duration_minutes: number | null;
  travel_time_minutes: number | null;
  equipment_ids: number[];
  parts_used: Array<{ item_id: number; quantity: number }>;
  labor_cost: number;
  parts_cost: number;
  total_cost: number;
  signature_url: string | null;
  photos: string[];
  notes: string | null;
  customer_feedback: string | null;
  rating: number | null;
  created_at: string;
  updated_at: string;
}

export interface InterventionCreate {
  type: InterventionType;
  priority?: InterventionPriority;
  subject: string;
  description?: string | null;
  customer_id?: number | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  address: string;
  lat?: number | null;
  lng?: number | null;
  zone_id?: number | null;
  technician_id?: number | null;
  scheduled_date: string;
  scheduled_start_time?: string | null;
  scheduled_end_time?: string | null;
  equipment_ids?: number[];
  notes?: string | null;
}

export type InterventionUpdate = Partial<InterventionCreate>;

export interface InterventionAssign {
  technician_id: number;
  scheduled_date?: string;
  scheduled_start_time?: string;
}

export interface InterventionStart {
  actual_start_time?: string;
  travel_time_minutes?: number;
  notes?: string;
}

export interface InterventionComplete {
  actual_end_time?: string;
  parts_used?: Array<{ item_id: number; quantity: number }>;
  labor_cost?: number;
  notes?: string;
  signature_data?: string;
  photos?: string[];
}

export interface InterventionListResponse {
  items: Intervention[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ============================================================================
// TYPES - Routes (Tournées)
// ============================================================================

export interface Route {
  id: number;
  tenant_id: string;
  name: string;
  date: string;
  technician_id: number;
  technician_name: string;
  zone_id: number | null;
  interventions: number[];
  status: 'DRAFT' | 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED';
  total_distance_km: number | null;
  estimated_duration_minutes: number | null;
  start_address: string | null;
  end_address: string | null;
  optimized: boolean;
  created_at: string;
}

export interface RouteCreate {
  name: string;
  date: string;
  technician_id: number;
  zone_id?: number | null;
  interventions?: number[];
  start_address?: string | null;
  end_address?: string | null;
}

export type RouteUpdate = Partial<RouteCreate>;

// ============================================================================
// TYPES - Time Entries
// ============================================================================

export interface TimeEntry {
  id: number;
  tenant_id: string;
  technician_id: number;
  intervention_id: number | null;
  entry_type: 'WORK' | 'TRAVEL' | 'BREAK' | 'ADMIN';
  start_time: string;
  end_time: string | null;
  duration_minutes: number | null;
  description: string | null;
  is_billable: boolean;
  created_at: string;
}

export interface TimeEntryCreate {
  intervention_id?: number | null;
  entry_type: 'WORK' | 'TRAVEL' | 'BREAK' | 'ADMIN';
  start_time: string;
  end_time?: string | null;
  description?: string | null;
  is_billable?: boolean;
}

export type TimeEntryUpdate = Partial<TimeEntryCreate>;

// ============================================================================
// TYPES - Expenses
// ============================================================================

export interface Expense {
  id: number;
  tenant_id: string;
  technician_id: number;
  intervention_id: number | null;
  expense_type: 'FUEL' | 'PARKING' | 'TOLL' | 'MEAL' | 'PARTS' | 'OTHER';
  amount: number;
  currency: string;
  description: string;
  receipt_url: string | null;
  date: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'REIMBURSED';
  created_at: string;
}

export interface ExpenseCreate {
  intervention_id?: number | null;
  expense_type: 'FUEL' | 'PARKING' | 'TOLL' | 'MEAL' | 'PARTS' | 'OTHER';
  amount: number;
  description: string;
  receipt_data?: string;
  date: string;
}

// ============================================================================
// TYPES - Contracts (Service Contracts)
// ============================================================================

export interface ServiceContract {
  id: number;
  tenant_id: string;
  contract_number: string;
  customer_id: number;
  customer_name: string;
  name: string;
  description: string | null;
  start_date: string;
  end_date: string;
  value: number;
  billing_frequency: 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
  included_interventions: number;
  used_interventions: number;
  sla_response_hours: number | null;
  equipment_ids: number[];
  status: 'DRAFT' | 'ACTIVE' | 'EXPIRED' | 'CANCELLED';
  auto_renew: boolean;
  created_at: string;
}

export interface ServiceContractCreate {
  customer_id: number;
  name: string;
  description?: string | null;
  start_date: string;
  end_date: string;
  value: number;
  billing_frequency?: 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
  included_interventions?: number;
  sla_response_hours?: number | null;
  equipment_ids?: number[];
  auto_renew?: boolean;
}

export type ServiceContractUpdate = Partial<ServiceContractCreate>;

// ============================================================================
// TYPES - Templates
// ============================================================================

export interface InterventionTemplate {
  id: number;
  tenant_id: string;
  name: string;
  type: InterventionType;
  description: string | null;
  estimated_duration_minutes: number;
  checklist: Array<{ item: string; required: boolean }>;
  required_skills: string[];
  default_parts: Array<{ item_id: number; quantity: number }>;
  is_active: boolean;
  created_at: string;
}

export interface InterventionTemplateCreate {
  name: string;
  type: InterventionType;
  description?: string | null;
  estimated_duration_minutes: number;
  checklist?: Array<{ item: string; required: boolean }>;
  required_skills?: string[];
  default_parts?: Array<{ item_id: number; quantity: number }>;
}

export type InterventionTemplateUpdate = Partial<InterventionTemplateCreate> & { is_active?: boolean };

// ============================================================================
// TYPES - Dashboard & Stats
// ============================================================================

export interface FieldServiceDashboard {
  interventions_today: number;
  interventions_pending: number;
  interventions_completed_today: number;
  technicians_active: number;
  technicians_available: number;
  avg_response_time_hours: number;
  avg_completion_time_minutes: number;
  customer_satisfaction: number;
  revenue_today: number;
  revenue_month: number;
  by_status: Record<InterventionStatus, number>;
  by_priority: Record<InterventionPriority, number>;
  recent_interventions: Intervention[];
  technician_locations: Array<{
    technician_id: number;
    name: string;
    status: TechnicianStatus;
    lat: number;
    lng: number;
    current_intervention_id: number | null;
  }>;
}

export interface InterventionStats {
  total: number;
  by_status: Record<InterventionStatus, number>;
  by_type: Record<InterventionType, number>;
  by_priority: Record<InterventionPriority, number>;
  avg_duration_minutes: number;
  avg_rating: number;
  completion_rate: number;
}

// ============================================================================
// API CLIENT
// ============================================================================

const BASE_PATH = '/v1/field-service';

export const fieldServiceApi = {
  // Dashboard
  getDashboard: () =>
    api.get<FieldServiceDashboard>(`${BASE_PATH}/dashboard`),

  getStats: (params?: { date_from?: string; date_to?: string; technician_id?: number }) =>
    api.get<InterventionStats>(`${BASE_PATH}/stats${qs(params || {})}`),

  // Zones
  listZones: (params?: { active_only?: boolean }) =>
    api.get<Zone[]>(`${BASE_PATH}/zones${qs(params || {})}`),

  getZone: (id: number) =>
    api.get<Zone>(`${BASE_PATH}/zones/${id}`),

  createZone: (data: ZoneCreate) =>
    api.post<Zone>(`${BASE_PATH}/zones`, data),

  updateZone: (id: number, data: ZoneUpdate) =>
    api.put<Zone>(`${BASE_PATH}/zones/${id}`, data),

  deleteZone: (id: number) =>
    api.delete(`${BASE_PATH}/zones/${id}`),

  // Technicians
  listTechnicians: (params?: { status?: TechnicianStatus; zone_id?: number; active_only?: boolean }) =>
    api.get<Technician[]>(`${BASE_PATH}/technicians${qs(params || {})}`),

  getTechnician: (id: number) =>
    api.get<Technician>(`${BASE_PATH}/technicians/${id}`),

  createTechnician: (data: TechnicianCreate) =>
    api.post<Technician>(`${BASE_PATH}/technicians`, data),

  updateTechnician: (id: number, data: TechnicianUpdate) =>
    api.put<Technician>(`${BASE_PATH}/technicians/${id}`, data),

  updateTechnicianStatus: (id: number, status: TechnicianStatus) =>
    api.post<Technician>(`${BASE_PATH}/technicians/${id}/status`, { status }),

  updateTechnicianLocation: (id: number, location: TechnicianLocation) =>
    api.post<Technician>(`${BASE_PATH}/technicians/${id}/location`, location),

  getTechnicianSchedule: (id: number, params?: { date_from?: string; date_to?: string }) =>
    api.get<Intervention[]>(`${BASE_PATH}/technicians/${id}/schedule${qs(params || {})}`),

  // Vehicles
  listVehicles: (params?: { active_only?: boolean }) =>
    api.get<Vehicle[]>(`${BASE_PATH}/vehicles${qs(params || {})}`),

  getVehicle: (id: number) =>
    api.get<Vehicle>(`${BASE_PATH}/vehicles/${id}`),

  createVehicle: (data: VehicleCreate) =>
    api.post<Vehicle>(`${BASE_PATH}/vehicles`, data),

  updateVehicle: (id: number, data: VehicleUpdate) =>
    api.put<Vehicle>(`${BASE_PATH}/vehicles/${id}`, data),

  assignVehicle: (vehicleId: number, technicianId: number | null) =>
    api.post<Vehicle>(`${BASE_PATH}/vehicles/${vehicleId}/assign`, { technician_id: technicianId }),

  // Interventions
  listInterventions: (params?: {
    page?: number;
    page_size?: number;
    status?: InterventionStatus;
    priority?: InterventionPriority;
    type?: InterventionType;
    technician_id?: number;
    customer_id?: number;
    zone_id?: number;
    date_from?: string;
    date_to?: string;
    search?: string;
  }) =>
    api.get<InterventionListResponse>(`${BASE_PATH}/interventions${qs(params || {})}`),

  getIntervention: (id: number) =>
    api.get<Intervention>(`${BASE_PATH}/interventions/${id}`),

  createIntervention: (data: InterventionCreate) =>
    api.post<Intervention>(`${BASE_PATH}/interventions`, data),

  updateIntervention: (id: number, data: InterventionUpdate) =>
    api.patch<Intervention>(`${BASE_PATH}/interventions/${id}`, data),

  assignIntervention: (id: number, data: InterventionAssign) =>
    api.post<Intervention>(`${BASE_PATH}/interventions/${id}/assign`, data),

  startIntervention: (id: number, data: InterventionStart) =>
    api.post<Intervention>(`${BASE_PATH}/interventions/${id}/start`, data),

  completeIntervention: (id: number, data: InterventionComplete) =>
    api.post<Intervention>(`${BASE_PATH}/interventions/${id}/complete`, data),

  cancelIntervention: (id: number, reason?: string) =>
    api.post<Intervention>(`${BASE_PATH}/interventions/${id}/cancel`, { reason }),

  addInterventionPhoto: (id: number, photoData: string) =>
    api.post<Intervention>(`${BASE_PATH}/interventions/${id}/photos`, { photo_data: photoData }),

  addInterventionSignature: (id: number, signatureData: string) =>
    api.post<Intervention>(`${BASE_PATH}/interventions/${id}/signature`, { signature_data: signatureData }),

  // Routes (Tournées)
  listRoutes: (params?: { technician_id?: number; date_from?: string; date_to?: string; status?: string }) =>
    api.get<Route[]>(`${BASE_PATH}/routes${qs(params || {})}`),

  getRoute: (id: number) =>
    api.get<Route>(`${BASE_PATH}/routes/${id}`),

  createRoute: (data: RouteCreate) =>
    api.post<Route>(`${BASE_PATH}/routes`, data),

  updateRoute: (id: number, data: RouteUpdate) =>
    api.patch<Route>(`${BASE_PATH}/routes/${id}`, data),

  optimizeRoute: (id: number) =>
    api.post<Route>(`${BASE_PATH}/routes/${id}/optimize`),

  startRoute: (id: number) =>
    api.post<Route>(`${BASE_PATH}/routes/${id}/start`),

  completeRoute: (id: number) =>
    api.post<Route>(`${BASE_PATH}/routes/${id}/complete`),

  // Time Entries
  listTimeEntries: (params?: { technician_id?: number; intervention_id?: number; date_from?: string; date_to?: string }) =>
    api.get<TimeEntry[]>(`${BASE_PATH}/time-entries${qs(params || {})}`),

  createTimeEntry: (data: TimeEntryCreate) =>
    api.post<TimeEntry>(`${BASE_PATH}/time-entries`, data),

  updateTimeEntry: (id: number, data: TimeEntryUpdate) =>
    api.patch<TimeEntry>(`${BASE_PATH}/time-entries/${id}`, data),

  deleteTimeEntry: (id: number) =>
    api.delete(`${BASE_PATH}/time-entries/${id}`),

  // Expenses
  listExpenses: (params?: { technician_id?: number; status?: string; date_from?: string; date_to?: string }) =>
    api.get<Expense[]>(`${BASE_PATH}/expenses${qs(params || {})}`),

  createExpense: (data: ExpenseCreate) =>
    api.post<Expense>(`${BASE_PATH}/expenses`, data),

  approveExpense: (id: number) =>
    api.post<Expense>(`${BASE_PATH}/expenses/${id}/approve`),

  rejectExpense: (id: number, reason?: string) =>
    api.post<Expense>(`${BASE_PATH}/expenses/${id}/reject`, { reason }),

  // Service Contracts
  listContracts: (params?: { customer_id?: number; status?: string }) =>
    api.get<ServiceContract[]>(`${BASE_PATH}/contracts${qs(params || {})}`),

  getContract: (id: number) =>
    api.get<ServiceContract>(`${BASE_PATH}/contracts/${id}`),

  createContract: (data: ServiceContractCreate) =>
    api.post<ServiceContract>(`${BASE_PATH}/contracts`, data),

  updateContract: (id: number, data: ServiceContractUpdate) =>
    api.patch<ServiceContract>(`${BASE_PATH}/contracts/${id}`, data),

  renewContract: (id: number, newEndDate: string) =>
    api.post<ServiceContract>(`${BASE_PATH}/contracts/${id}/renew`, { new_end_date: newEndDate }),

  // Templates
  listTemplates: (params?: { type?: InterventionType; active_only?: boolean }) =>
    api.get<InterventionTemplate[]>(`${BASE_PATH}/templates${qs(params || {})}`),

  getTemplate: (id: number) =>
    api.get<InterventionTemplate>(`${BASE_PATH}/templates/${id}`),

  createTemplate: (data: InterventionTemplateCreate) =>
    api.post<InterventionTemplate>(`${BASE_PATH}/templates`, data),

  updateTemplate: (id: number, data: InterventionTemplateUpdate) =>
    api.patch<InterventionTemplate>(`${BASE_PATH}/templates/${id}`, data),

  createInterventionFromTemplate: (templateId: number, data: Partial<InterventionCreate>) =>
    api.post<Intervention>(`${BASE_PATH}/templates/${templateId}/create-intervention`, data),
};

export default fieldServiceApi;
