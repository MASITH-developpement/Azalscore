/**
 * AZALSCORE - Maintenance Management API (CMMS/GMAO)
 * ===================================================
 * Complete typed API client for maintenance module.
 * Covers: Assets, Meters, Plans, Work Orders, Failures, Spare Parts, Contracts
 */

import { api } from '@/core/api-client';

// ============================================================================
// ENUMS
// ============================================================================

export type AssetCategory =
  | 'MACHINE'
  | 'EQUIPMENT'
  | 'VEHICLE'
  | 'BUILDING'
  | 'INFRASTRUCTURE'
  | 'IT_EQUIPMENT'
  | 'TOOL'
  | 'UTILITY'
  | 'FURNITURE'
  | 'OTHER';

export type AssetStatus =
  | 'ACTIVE'
  | 'INACTIVE'
  | 'IN_MAINTENANCE'
  | 'RESERVED'
  | 'DISPOSED'
  | 'UNDER_REPAIR'
  | 'STANDBY';

export type AssetCriticality = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type MaintenanceType =
  | 'PREVENTIVE'
  | 'CORRECTIVE'
  | 'PREDICTIVE'
  | 'CONDITION_BASED'
  | 'BREAKDOWN'
  | 'IMPROVEMENT'
  | 'INSPECTION'
  | 'CALIBRATION';

export type WorkOrderStatus =
  | 'DRAFT'
  | 'REQUESTED'
  | 'APPROVED'
  | 'PLANNED'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'ON_HOLD'
  | 'COMPLETED'
  | 'VERIFIED'
  | 'CLOSED'
  | 'CANCELLED';

export type WorkOrderPriority =
  | 'EMERGENCY'
  | 'CRITICAL'
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'SCHEDULED';

export type FailureType =
  | 'MECHANICAL'
  | 'ELECTRICAL'
  | 'ELECTRONIC'
  | 'HYDRAULIC'
  | 'PNEUMATIC'
  | 'SOFTWARE'
  | 'OPERATOR_ERROR'
  | 'WEAR'
  | 'CONTAMINATION'
  | 'UNKNOWN';

export type PartRequestStatus =
  | 'REQUESTED'
  | 'APPROVED'
  | 'ORDERED'
  | 'RECEIVED'
  | 'ISSUED'
  | 'CANCELLED';

export type ContractType =
  | 'FULL_SERVICE'
  | 'PREVENTIVE'
  | 'ON_CALL'
  | 'PARTS_ONLY'
  | 'LABOR_ONLY'
  | 'WARRANTY';

export type ContractStatus = 'DRAFT' | 'ACTIVE' | 'SUSPENDED' | 'EXPIRED' | 'TERMINATED';

// ============================================================================
// ASSETS
// ============================================================================

export interface Asset {
  id: number;
  asset_code: string;
  name: string;
  description?: string | null;
  category: AssetCategory;
  asset_type?: string | null;
  status: AssetStatus;
  criticality: AssetCriticality;
  parent_id?: number | null;
  location_id?: number | null;
  location_description?: string | null;
  building?: string | null;
  manufacturer?: string | null;
  model?: string | null;
  serial_number?: string | null;
  year_manufactured?: number | null;
  purchase_date?: string | null;
  installation_date?: string | null;
  warranty_end_date?: string | null;
  last_maintenance_date?: string | null;
  next_maintenance_date?: string | null;
  purchase_cost?: string | null;
  current_value?: string | null;
  operating_hours?: string | null;
  specifications?: Record<string, unknown> | null;
  supplier_id?: number | null;
  responsible_id?: number | null;
  department?: string | null;
  maintenance_strategy?: string | null;
  mtbf_hours?: string | null;
  mttr_hours?: string | null;
  availability_rate?: string | null;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface AssetCreate {
  asset_code: string;
  name: string;
  description?: string | null;
  category: AssetCategory;
  asset_type?: string | null;
  parent_id?: number | null;
  criticality?: AssetCriticality;
  location_id?: number | null;
  location_description?: string | null;
  building?: string | null;
  floor?: string | null;
  area?: string | null;
  manufacturer?: string | null;
  model?: string | null;
  serial_number?: string | null;
  year_manufactured?: number | null;
  purchase_date?: string | null;
  installation_date?: string | null;
  warranty_end_date?: string | null;
  purchase_cost?: string | null;
  replacement_cost?: string | null;
  specifications?: Record<string, unknown> | null;
  power_rating?: string | null;
  supplier_id?: number | null;
  responsible_id?: number | null;
  department?: string | null;
  maintenance_strategy?: string | null;
  notes?: string | null;
}

export interface AssetUpdate {
  name?: string | null;
  description?: string | null;
  category?: AssetCategory | null;
  asset_type?: string | null;
  status?: AssetStatus | null;
  criticality?: AssetCriticality | null;
  parent_id?: number | null;
  location_description?: string | null;
  manufacturer?: string | null;
  model?: string | null;
  specifications?: Record<string, unknown> | null;
  responsible_id?: number | null;
  department?: string | null;
  maintenance_strategy?: string | null;
  notes?: string | null;
}

export interface AssetList {
  items: Asset[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// METERS
// ============================================================================

export interface Meter {
  id: number;
  asset_id: number;
  meter_code: string;
  name: string;
  description?: string | null;
  meter_type: string;
  unit: string;
  current_reading: string;
  last_reading_date?: string | null;
  initial_reading: string;
  alert_threshold?: string | null;
  critical_threshold?: string | null;
  maintenance_trigger_value?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface MeterCreate {
  meter_code: string;
  name: string;
  description?: string | null;
  meter_type: string;
  unit: string;
  initial_reading?: string;
  alert_threshold?: string | null;
  critical_threshold?: string | null;
  maintenance_trigger_value?: string | null;
}

export interface MeterReading {
  id: number;
  meter_id: number;
  reading_date: string;
  reading_value: string;
  delta?: string | null;
  source?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface MeterReadingCreate {
  reading_value: string;
  source?: string;
  notes?: string | null;
}

// ============================================================================
// MAINTENANCE PLANS
// ============================================================================

export interface PlanTask {
  id: number;
  plan_id: number;
  sequence: number;
  task_code?: string | null;
  description: string;
  detailed_instructions?: string | null;
  estimated_duration_minutes?: number | null;
  required_skill?: string | null;
  is_mandatory: boolean;
  required_parts?: Array<Record<string, unknown>> | null;
  check_points?: string[] | null;
  created_at: string;
}

export interface PlanTaskCreate {
  sequence: number;
  task_code?: string | null;
  description: string;
  detailed_instructions?: string | null;
  estimated_duration_minutes?: number | null;
  required_skill?: string | null;
  is_mandatory?: boolean;
  required_parts?: Array<Record<string, unknown>> | null;
  check_points?: string[] | null;
}

export interface MaintenancePlan {
  id: number;
  plan_code: string;
  name: string;
  description?: string | null;
  maintenance_type: MaintenanceType;
  asset_id?: number | null;
  asset_category?: AssetCategory | null;
  trigger_type: string;
  frequency_value?: number | null;
  frequency_unit?: string | null;
  trigger_meter_id?: number | null;
  trigger_meter_interval?: string | null;
  last_execution_date?: string | null;
  next_due_date?: string | null;
  lead_time_days: number;
  estimated_duration_hours?: string | null;
  responsible_id?: number | null;
  is_active: boolean;
  estimated_labor_cost?: string | null;
  estimated_parts_cost?: string | null;
  instructions?: string | null;
  safety_instructions?: string | null;
  required_tools?: string[] | null;
  tasks: PlanTask[];
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface MaintenancePlanCreate {
  plan_code: string;
  name: string;
  description?: string | null;
  maintenance_type: MaintenanceType;
  asset_id?: number | null;
  asset_category?: AssetCategory | null;
  trigger_type?: string;
  frequency_value?: number | null;
  frequency_unit?: string | null;
  trigger_meter_id?: number | null;
  trigger_meter_interval?: string | null;
  lead_time_days?: number;
  estimated_duration_hours?: string | null;
  responsible_id?: number | null;
  estimated_labor_cost?: string | null;
  estimated_parts_cost?: string | null;
  instructions?: string | null;
  safety_instructions?: string | null;
  required_tools?: string[] | null;
  tasks?: PlanTaskCreate[] | null;
}

export interface MaintenancePlanUpdate {
  name?: string | null;
  description?: string | null;
  frequency_value?: number | null;
  frequency_unit?: string | null;
  lead_time_days?: number | null;
  estimated_duration_hours?: string | null;
  responsible_id?: number | null;
  instructions?: string | null;
  safety_instructions?: string | null;
  is_active?: boolean | null;
}

export interface MaintenancePlanList {
  items: MaintenancePlan[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// WORK ORDERS
// ============================================================================

export interface WorkOrderTask {
  id: number;
  work_order_id: number;
  sequence: number;
  description: string;
  instructions?: string | null;
  estimated_minutes?: number | null;
  actual_minutes?: number | null;
  status: string;
  completed_date?: string | null;
  result?: string | null;
  issues_found?: string | null;
}

export interface WorkOrderTaskCreate {
  sequence: number;
  description: string;
  instructions?: string | null;
  estimated_minutes?: number | null;
}

export interface WorkOrderLabor {
  id: number;
  work_order_id: number;
  technician_id: number;
  technician_name?: string | null;
  work_date: string;
  hours_worked: string;
  overtime_hours: string;
  labor_type?: string | null;
  hourly_rate?: string | null;
  total_cost?: string | null;
  work_description?: string | null;
  created_at: string;
}

export interface WorkOrderLaborCreate {
  technician_id: number;
  work_date: string;
  hours_worked: string;
  overtime_hours?: string;
  labor_type?: string;
  hourly_rate?: string | null;
  work_description?: string | null;
}

export interface WorkOrderPart {
  id: number;
  work_order_id: number;
  spare_part_id?: number | null;
  part_code?: string | null;
  part_description: string;
  quantity_planned?: string | null;
  quantity_used: string;
  unit?: string | null;
  unit_cost?: string | null;
  total_cost?: string | null;
  source?: string | null;
  created_at: string;
}

export interface WorkOrderPartCreate {
  spare_part_id?: number | null;
  part_description: string;
  quantity_used: string;
  unit?: string | null;
  unit_cost?: string | null;
  source?: string;
  notes?: string | null;
}

export interface WorkOrder {
  id: number;
  wo_number: string;
  title: string;
  description?: string | null;
  maintenance_type: MaintenanceType;
  asset_id: number;
  priority: WorkOrderPriority;
  status: WorkOrderStatus;
  component_id?: number | null;
  source?: string | null;
  source_reference?: string | null;
  maintenance_plan_id?: number | null;
  failure_id?: number | null;
  requester_id?: number | null;
  request_date?: string | null;
  request_description?: string | null;
  scheduled_start_date?: string | null;
  scheduled_end_date?: string | null;
  due_date?: string | null;
  actual_start_date?: string | null;
  actual_end_date?: string | null;
  downtime_hours?: string | null;
  assigned_to_id?: number | null;
  external_vendor_id?: number | null;
  work_instructions?: string | null;
  safety_precautions?: string | null;
  tools_required?: string[] | null;
  location_description?: string | null;
  completion_notes?: string | null;
  completed_by_id?: number | null;
  verification_required: boolean;
  verified_by_id?: number | null;
  verified_date?: string | null;
  estimated_labor_hours?: string | null;
  estimated_labor_cost?: string | null;
  estimated_parts_cost?: string | null;
  actual_labor_hours?: string | null;
  actual_labor_cost?: string | null;
  actual_parts_cost?: string | null;
  meter_reading_end?: string | null;
  notes?: string | null;
  tasks: WorkOrderTask[];
  labor_entries: WorkOrderLabor[];
  parts_used: WorkOrderPart[];
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface WorkOrderCreate {
  title: string;
  description?: string | null;
  maintenance_type: MaintenanceType;
  asset_id: number;
  component_id?: number | null;
  priority?: WorkOrderPriority;
  maintenance_plan_id?: number | null;
  failure_id?: number | null;
  requester_id?: number | null;
  request_description?: string | null;
  scheduled_start_date?: string | null;
  scheduled_end_date?: string | null;
  due_date?: string | null;
  assigned_to_id?: number | null;
  external_vendor_id?: number | null;
  work_instructions?: string | null;
  safety_precautions?: string | null;
  tools_required?: string[] | null;
  location_description?: string | null;
  estimated_labor_hours?: string | null;
  estimated_parts_cost?: string | null;
  tasks?: WorkOrderTaskCreate[] | null;
}

export interface WorkOrderUpdate {
  title?: string | null;
  description?: string | null;
  priority?: WorkOrderPriority | null;
  status?: WorkOrderStatus | null;
  scheduled_start_date?: string | null;
  scheduled_end_date?: string | null;
  due_date?: string | null;
  assigned_to_id?: number | null;
  external_vendor_id?: number | null;
  work_instructions?: string | null;
  safety_precautions?: string | null;
  location_description?: string | null;
  notes?: string | null;
}

export interface WorkOrderComplete {
  completion_notes: string;
  meter_reading_end?: string | null;
}

export interface WorkOrderList {
  items: WorkOrder[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// FAILURES
// ============================================================================

export interface Failure {
  id: number;
  failure_number: string;
  asset_id: number;
  failure_type: FailureType;
  description: string;
  failure_date: string;
  component_id?: number | null;
  symptoms?: string | null;
  detected_date?: string | null;
  reported_date?: string | null;
  resolved_date?: string | null;
  production_stopped: boolean;
  downtime_hours?: string | null;
  production_loss_units?: string | null;
  estimated_cost_impact?: string | null;
  reported_by_id?: number | null;
  work_order_id?: number | null;
  resolution?: string | null;
  root_cause?: string | null;
  corrective_action?: string | null;
  preventive_action?: string | null;
  meter_reading?: string | null;
  status: string;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface FailureCreate {
  asset_id: number;
  failure_type: FailureType;
  description: string;
  failure_date: string;
  component_id?: number | null;
  symptoms?: string | null;
  production_stopped?: boolean;
  downtime_hours?: string | null;
  meter_reading?: string | null;
  notes?: string | null;
}

export interface FailureUpdate {
  description?: string | null;
  symptoms?: string | null;
  production_stopped?: boolean | null;
  downtime_hours?: string | null;
  estimated_cost_impact?: string | null;
  resolution?: string | null;
  root_cause?: string | null;
  corrective_action?: string | null;
  preventive_action?: string | null;
  status?: string | null;
  notes?: string | null;
}

export interface FailureList {
  items: Failure[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// SPARE PARTS
// ============================================================================

export interface SparePart {
  id: number;
  part_code: string;
  name: string;
  description?: string | null;
  category?: string | null;
  manufacturer?: string | null;
  manufacturer_part_number?: string | null;
  preferred_supplier_id?: number | null;
  unit: string;
  unit_cost?: string | null;
  last_purchase_price?: string | null;
  min_stock_level: string;
  max_stock_level?: string | null;
  reorder_point?: string | null;
  reorder_quantity?: string | null;
  lead_time_days?: number | null;
  criticality?: AssetCriticality | null;
  shelf_life_days?: number | null;
  is_active: boolean;
  product_id?: number | null;
  notes?: string | null;
  specifications?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface SparePartCreate {
  part_code: string;
  name: string;
  description?: string | null;
  category?: string | null;
  manufacturer?: string | null;
  manufacturer_part_number?: string | null;
  preferred_supplier_id?: number | null;
  unit?: string;
  unit_cost?: string | null;
  min_stock_level?: string;
  max_stock_level?: string | null;
  reorder_point?: string | null;
  reorder_quantity?: string | null;
  lead_time_days?: number | null;
  criticality?: AssetCriticality | null;
  shelf_life_days?: number | null;
  product_id?: number | null;
  notes?: string | null;
  specifications?: Record<string, unknown> | null;
}

export interface SparePartUpdate {
  name?: string | null;
  description?: string | null;
  category?: string | null;
  manufacturer?: string | null;
  preferred_supplier_id?: number | null;
  unit_cost?: string | null;
  min_stock_level?: string | null;
  max_stock_level?: string | null;
  reorder_point?: string | null;
  lead_time_days?: number | null;
  criticality?: AssetCriticality | null;
  is_active?: boolean | null;
  notes?: string | null;
}

export interface SparePartList {
  items: SparePart[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// PART REQUESTS
// ============================================================================

export interface PartRequest {
  id: number;
  request_number: string;
  work_order_id?: number | null;
  spare_part_id?: number | null;
  part_description: string;
  quantity_requested: string;
  unit?: string | null;
  quantity_approved?: string | null;
  quantity_issued?: string | null;
  priority: WorkOrderPriority;
  required_date?: string | null;
  status: PartRequestStatus;
  requester_id?: number | null;
  request_date?: string | null;
  request_reason?: string | null;
  approved_by_id?: number | null;
  approved_date?: string | null;
  issued_by_id?: number | null;
  issued_date?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PartRequestCreate {
  work_order_id?: number | null;
  spare_part_id?: number | null;
  part_description: string;
  quantity_requested: string;
  unit?: string | null;
  priority?: WorkOrderPriority;
  required_date?: string | null;
  request_reason?: string | null;
}

export interface PartRequestList {
  items: PartRequest[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// CONTRACTS
// ============================================================================

export interface Contract {
  id: number;
  contract_code: string;
  name: string;
  description?: string | null;
  contract_type: ContractType;
  status: ContractStatus;
  vendor_id: number;
  vendor_contact?: string | null;
  vendor_phone?: string | null;
  vendor_email?: string | null;
  start_date: string;
  end_date: string;
  renewal_date?: string | null;
  notice_period_days?: number | null;
  auto_renewal: boolean;
  covered_assets?: number[] | null;
  coverage_description?: string | null;
  exclusions?: string | null;
  response_time_hours?: number | null;
  resolution_time_hours?: number | null;
  availability_guarantee?: string | null;
  contract_value?: string | null;
  annual_cost?: string | null;
  payment_frequency?: string | null;
  includes_parts: boolean;
  includes_labor: boolean;
  includes_travel: boolean;
  max_interventions?: number | null;
  interventions_used: number;
  manager_id?: number | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  created_by?: number | null;
}

export interface ContractCreate {
  contract_code: string;
  name: string;
  description?: string | null;
  contract_type: ContractType;
  vendor_id: number;
  vendor_contact?: string | null;
  vendor_phone?: string | null;
  vendor_email?: string | null;
  start_date: string;
  end_date: string;
  renewal_date?: string | null;
  notice_period_days?: number | null;
  auto_renewal?: boolean;
  covered_assets?: number[] | null;
  coverage_description?: string | null;
  exclusions?: string | null;
  response_time_hours?: number | null;
  resolution_time_hours?: number | null;
  contract_value?: string | null;
  annual_cost?: string | null;
  payment_frequency?: string | null;
  includes_parts?: boolean;
  includes_labor?: boolean;
  includes_travel?: boolean;
  max_interventions?: number | null;
  manager_id?: number | null;
  notes?: string | null;
}

export interface ContractUpdate {
  name?: string | null;
  description?: string | null;
  status?: ContractStatus | null;
  vendor_contact?: string | null;
  vendor_phone?: string | null;
  vendor_email?: string | null;
  renewal_date?: string | null;
  auto_renewal?: boolean | null;
  covered_assets?: number[] | null;
  coverage_description?: string | null;
  response_time_hours?: number | null;
  annual_cost?: string | null;
  manager_id?: number | null;
  notes?: string | null;
}

export interface ContractList {
  items: Contract[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// DASHBOARD
// ============================================================================

export interface MaintenanceDashboard {
  // Assets
  assets_total: number;
  assets_active: number;
  assets_in_maintenance: number;
  assets_by_category: Record<string, number>;
  // Work orders
  wo_total: number;
  wo_open: number;
  wo_overdue: number;
  wo_completed_this_month: number;
  wo_by_priority: Record<string, number>;
  wo_by_status: Record<string, number>;
  // Failures
  failures_this_month: number;
  failures_by_type: Record<string, number>;
  mtbf_global?: string | null;
  mttr_global?: string | null;
  // Plans
  plans_active: number;
  plans_due_soon: number;
  // Costs
  total_cost_this_month?: string | null;
  labor_cost_this_month?: string | null;
  parts_cost_this_month?: string | null;
  // Indicators
  availability_rate?: string | null;
  preventive_ratio?: string | null;
  schedule_compliance?: string | null;
  // Contracts
  contracts_active: number;
  contracts_expiring_soon: number;
  // Spare parts
  parts_below_min_stock: number;
  pending_part_requests: number;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/maintenance';

function buildQueryString(
  params: Record<string, string | number | boolean | undefined | null>
): string {
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

export const maintenanceApi = {
  // ==========================================================================
  // Assets
  // ==========================================================================

  createAsset: (data: AssetCreate) =>
    api.post<Asset>(`${BASE_PATH}/assets`, data),

  listAssets: (params?: {
    skip?: number;
    limit?: number;
    category?: AssetCategory;
    status?: AssetStatus;
    criticality?: AssetCriticality;
    search?: string;
  }) =>
    api.get<AssetList>(`${BASE_PATH}/assets${buildQueryString(params || {})}`),

  getAsset: (assetId: number) =>
    api.get<Asset>(`${BASE_PATH}/assets/${assetId}`),

  updateAsset: (assetId: number, data: AssetUpdate) =>
    api.put<Asset>(`${BASE_PATH}/assets/${assetId}`, data),

  deleteAsset: (assetId: number) =>
    api.delete(`${BASE_PATH}/assets/${assetId}`),

  // ==========================================================================
  // Meters
  // ==========================================================================

  createMeter: (assetId: number, data: MeterCreate) =>
    api.post<Meter>(`${BASE_PATH}/assets/${assetId}/meters`, data),

  recordMeterReading: (meterId: number, data: MeterReadingCreate) =>
    api.post<MeterReading>(`${BASE_PATH}/meters/${meterId}/readings`, data),

  // ==========================================================================
  // Maintenance Plans
  // ==========================================================================

  createMaintenancePlan: (data: MaintenancePlanCreate) =>
    api.post<MaintenancePlan>(`${BASE_PATH}/plans`, data),

  listMaintenancePlans: (params?: {
    skip?: number;
    limit?: number;
    asset_id?: number;
    is_active?: boolean;
  }) =>
    api.get<MaintenancePlanList>(
      `${BASE_PATH}/plans${buildQueryString(params || {})}`
    ),

  getMaintenancePlan: (planId: number) =>
    api.get<MaintenancePlan>(`${BASE_PATH}/plans/${planId}`),

  updateMaintenancePlan: (planId: number, data: MaintenancePlanUpdate) =>
    api.put<MaintenancePlan>(`${BASE_PATH}/plans/${planId}`, data),

  // ==========================================================================
  // Work Orders
  // ==========================================================================

  createWorkOrder: (data: WorkOrderCreate) =>
    api.post<WorkOrder>(`${BASE_PATH}/work-orders`, data),

  listWorkOrders: (params?: {
    skip?: number;
    limit?: number;
    asset_id?: number;
    status?: WorkOrderStatus;
    priority?: WorkOrderPriority;
    assigned_to_id?: number;
  }) =>
    api.get<WorkOrderList>(
      `${BASE_PATH}/work-orders${buildQueryString(params || {})}`
    ),

  getWorkOrder: (woId: number) =>
    api.get<WorkOrder>(`${BASE_PATH}/work-orders/${woId}`),

  updateWorkOrder: (woId: number, data: WorkOrderUpdate) =>
    api.put<WorkOrder>(`${BASE_PATH}/work-orders/${woId}`, data),

  startWorkOrder: (woId: number) =>
    api.post<WorkOrder>(`${BASE_PATH}/work-orders/${woId}/start`, {}),

  completeWorkOrder: (woId: number, data: WorkOrderComplete) =>
    api.post<WorkOrder>(`${BASE_PATH}/work-orders/${woId}/complete`, data),

  addLaborEntry: (woId: number, data: WorkOrderLaborCreate) =>
    api.post<WorkOrderLabor>(`${BASE_PATH}/work-orders/${woId}/labor`, data),

  addPartUsed: (woId: number, data: WorkOrderPartCreate) =>
    api.post<WorkOrderPart>(`${BASE_PATH}/work-orders/${woId}/parts`, data),

  // ==========================================================================
  // Failures
  // ==========================================================================

  createFailure: (data: FailureCreate) =>
    api.post<Failure>(`${BASE_PATH}/failures`, data),

  listFailures: (params?: {
    skip?: number;
    limit?: number;
    asset_id?: number;
    status?: string;
  }) =>
    api.get<FailureList>(`${BASE_PATH}/failures${buildQueryString(params || {})}`),

  getFailure: (failureId: number) =>
    api.get<Failure>(`${BASE_PATH}/failures/${failureId}`),

  updateFailure: (failureId: number, data: FailureUpdate) =>
    api.put<Failure>(`${BASE_PATH}/failures/${failureId}`, data),

  // ==========================================================================
  // Spare Parts
  // ==========================================================================

  createSparePart: (data: SparePartCreate) =>
    api.post<SparePart>(`${BASE_PATH}/spare-parts`, data),

  listSpareParts: (params?: {
    skip?: number;
    limit?: number;
    category?: string;
    search?: string;
  }) =>
    api.get<SparePartList>(
      `${BASE_PATH}/spare-parts${buildQueryString(params || {})}`
    ),

  getSparePart: (partId: number) =>
    api.get<SparePart>(`${BASE_PATH}/spare-parts/${partId}`),

  updateSparePart: (partId: number, data: SparePartUpdate) =>
    api.put<SparePart>(`${BASE_PATH}/spare-parts/${partId}`, data),

  // ==========================================================================
  // Part Requests
  // ==========================================================================

  createPartRequest: (data: PartRequestCreate) =>
    api.post<PartRequest>(`${BASE_PATH}/part-requests`, data),

  listPartRequests: (params?: {
    skip?: number;
    limit?: number;
    status?: PartRequestStatus;
    work_order_id?: number;
  }) =>
    api.get<PartRequestList>(
      `${BASE_PATH}/part-requests${buildQueryString(params || {})}`
    ),

  // ==========================================================================
  // Contracts
  // ==========================================================================

  createContract: (data: ContractCreate) =>
    api.post<Contract>(`${BASE_PATH}/contracts`, data),

  listContracts: (params?: {
    skip?: number;
    limit?: number;
    status?: ContractStatus;
  }) =>
    api.get<ContractList>(
      `${BASE_PATH}/contracts${buildQueryString(params || {})}`
    ),

  getContract: (contractId: number) =>
    api.get<Contract>(`${BASE_PATH}/contracts/${contractId}`),

  updateContract: (contractId: number, data: ContractUpdate) =>
    api.put<Contract>(`${BASE_PATH}/contracts/${contractId}`, data),

  // ==========================================================================
  // Dashboard
  // ==========================================================================

  getDashboard: () =>
    api.get<MaintenanceDashboard>(`${BASE_PATH}/dashboard`),
};

export default maintenanceApi;
