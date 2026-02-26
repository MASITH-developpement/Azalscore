/**
 * AZALSCORE - Production Management API
 * ======================================
 * Complete typed API client for production module.
 * Covers: Work Centers, BOMs, Routings, Manufacturing Orders, Work Orders, Consumption, Scraps, Planning, Maintenance
 */

import { api } from '@/core/api-client';

// ============================================================================
// ENUMS
// ============================================================================

export type WorkCenterType = 'MACHINE' | 'WORKSTATION' | 'LINE' | 'CELL' | 'MANUAL';

export type WorkCenterStatus = 'AVAILABLE' | 'BUSY' | 'MAINTENANCE' | 'OFFLINE' | 'SETUP';

export type BOMType = 'MANUFACTURING' | 'ASSEMBLY' | 'KIT' | 'PHANTOM' | 'SUBCONTRACTING';

export type BOMStatus = 'DRAFT' | 'ACTIVE' | 'OBSOLETE';

export type ConsumptionType = 'MANUAL' | 'AUTO_ON_START' | 'AUTO_ON_COMPLETE' | 'BACKFLUSH';

export type OperationType =
  | 'PRODUCTION'
  | 'ASSEMBLY'
  | 'INSPECTION'
  | 'PACKAGING'
  | 'TRANSPORT'
  | 'SUBCONTRACTING'
  | 'SETUP'
  | 'CLEANUP';

export type MOStatus =
  | 'DRAFT'
  | 'CONFIRMED'
  | 'PLANNED'
  | 'IN_PROGRESS'
  | 'DONE'
  | 'CANCELLED'
  | 'ON_HOLD';

export type MOPriority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

export type WorkOrderStatus =
  | 'PENDING'
  | 'READY'
  | 'IN_PROGRESS'
  | 'PAUSED'
  | 'DONE'
  | 'CANCELLED';

export type ScrapReason =
  | 'DEFECT'
  | 'DAMAGE'
  | 'WRONG_MATERIAL'
  | 'MACHINE_ERROR'
  | 'OPERATOR_ERROR'
  | 'QUALITY_REJECT'
  | 'EXPIRED'
  | 'OTHER';

// ============================================================================
// WORK CENTERS
// ============================================================================

export interface WorkCenter {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  type: WorkCenterType;
  status: WorkCenterStatus;
  warehouse_id?: string | null;
  location?: string | null;
  capacity: string;
  efficiency: string;
  oee_target: string;
  cost_per_hour: string;
  cost_per_cycle: string;
  currency: string;
  working_hours_per_day: string;
  working_days_per_week: number;
  manager_id?: string | null;
  operator_ids?: string[] | null;
  requires_approval: boolean;
  allow_parallel: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkCenterCreate {
  code: string;
  name: string;
  description?: string | null;
  type?: WorkCenterType;
  warehouse_id?: string | null;
  location?: string | null;
  capacity?: string;
  efficiency?: string;
  oee_target?: string;
  time_start?: string;
  time_stop?: string;
  time_before?: string;
  time_after?: string;
  cost_per_hour?: string;
  cost_per_cycle?: string;
  currency?: string;
  working_hours_per_day?: string;
  working_days_per_week?: number;
  manager_id?: string | null;
  operator_ids?: string[] | null;
  requires_approval?: boolean;
  allow_parallel?: boolean;
  notes?: string | null;
}

export interface WorkCenterUpdate {
  name?: string | null;
  description?: string | null;
  type?: WorkCenterType | null;
  status?: WorkCenterStatus | null;
  warehouse_id?: string | null;
  location?: string | null;
  capacity?: string | null;
  efficiency?: string | null;
  oee_target?: string | null;
  cost_per_hour?: string | null;
  cost_per_cycle?: string | null;
  working_hours_per_day?: string | null;
  working_days_per_week?: number | null;
  manager_id?: string | null;
  operator_ids?: string[] | null;
  requires_approval?: boolean | null;
  allow_parallel?: boolean | null;
  notes?: string | null;
  is_active?: boolean | null;
}

export interface WorkCenterCapacity {
  id: string;
  work_center_id: string;
  date: string;
  shift: string;
  available_hours: string;
  planned_hours: string;
  actual_hours: string;
  notes?: string | null;
  created_at: string;
}

export interface WorkCenterCapacityCreate {
  work_center_id: string;
  date: string;
  shift?: string;
  available_hours: string;
  notes?: string | null;
}

// ============================================================================
// BOMs (Bills of Materials)
// ============================================================================

export interface BOMLine {
  id: string;
  bom_id: string;
  line_number: number;
  product_id: string;
  quantity: string;
  unit: string;
  operation_id?: string | null;
  scrap_rate: string;
  is_critical: boolean;
  alternative_group?: string | null;
  consumption_type?: ConsumptionType | null;
  notes?: string | null;
  created_at: string;
}

export interface BOMLineCreate {
  product_id: string;
  quantity: string;
  unit?: string;
  operation_id?: string | null;
  scrap_rate?: string;
  is_critical?: boolean;
  alternative_group?: string | null;
  consumption_type?: ConsumptionType | null;
  notes?: string | null;
}

export interface BOM {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  version: string;
  product_id: string;
  quantity: string;
  unit: string;
  type: BOMType;
  status: BOMStatus;
  routing_id?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  material_cost: string;
  labor_cost: string;
  overhead_cost: string;
  total_cost: string;
  currency: string;
  is_default: boolean;
  allow_alternatives: boolean;
  consumption_type: ConsumptionType;
  is_active: boolean;
  lines: BOMLine[];
  created_at: string;
  updated_at: string;
}

export interface BOMCreate {
  code: string;
  name: string;
  description?: string | null;
  version?: string;
  product_id: string;
  quantity?: string;
  unit?: string;
  type?: BOMType;
  routing_id?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  is_default?: boolean;
  allow_alternatives?: boolean;
  consumption_type?: ConsumptionType;
  notes?: string | null;
  lines?: BOMLineCreate[];
}

export interface BOMUpdate {
  name?: string | null;
  description?: string | null;
  status?: BOMStatus | null;
  routing_id?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  is_default?: boolean | null;
  allow_alternatives?: boolean | null;
  consumption_type?: ConsumptionType | null;
  notes?: string | null;
  is_active?: boolean | null;
}

export interface BOMList {
  items: BOM[];
  total: number;
}

// ============================================================================
// ROUTINGS
// ============================================================================

export interface RoutingOperation {
  id: string;
  routing_id: string;
  sequence: number;
  code: string;
  name: string;
  description?: string | null;
  type: OperationType;
  work_center_id?: string | null;
  setup_time: string;
  operation_time: string;
  cleanup_time: string;
  wait_time: string;
  batch_size: string;
  labor_cost_per_hour: string;
  machine_cost_per_hour: string;
  is_subcontracted: boolean;
  subcontractor_id?: string | null;
  requires_quality_check: boolean;
  skill_required?: string | null;
  created_at: string;
}

export interface RoutingOperationCreate {
  sequence: number;
  code: string;
  name: string;
  description?: string | null;
  type?: OperationType;
  work_center_id?: string | null;
  setup_time?: string;
  operation_time?: string;
  cleanup_time?: string;
  wait_time?: string;
  batch_size?: string;
  labor_cost_per_hour?: string;
  machine_cost_per_hour?: string;
  is_subcontracted?: boolean;
  subcontractor_id?: string | null;
  requires_quality_check?: boolean;
  skill_required?: string | null;
  notes?: string | null;
}

export interface Routing {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  version: string;
  product_id?: string | null;
  status: BOMStatus;
  total_setup_time: string;
  total_operation_time: string;
  total_time: string;
  total_labor_cost: string;
  total_machine_cost: string;
  currency: string;
  is_active: boolean;
  operations: RoutingOperation[];
  created_at: string;
  updated_at: string;
}

export interface RoutingCreate {
  code: string;
  name: string;
  description?: string | null;
  version?: string;
  product_id?: string | null;
  notes?: string | null;
  operations?: RoutingOperationCreate[];
}

export interface RoutingUpdate {
  name?: string | null;
  description?: string | null;
  status?: BOMStatus | null;
  product_id?: string | null;
  notes?: string | null;
  is_active?: boolean | null;
}

// ============================================================================
// MANUFACTURING ORDERS
// ============================================================================

export interface Consumption {
  id: string;
  mo_id: string;
  product_id: string;
  bom_line_id?: string | null;
  work_order_id?: string | null;
  quantity_planned: string;
  quantity_consumed: string;
  quantity_returned: string;
  unit: string;
  lot_id?: string | null;
  serial_id?: string | null;
  warehouse_id?: string | null;
  location_id?: string | null;
  unit_cost: string;
  total_cost: string;
  consumed_at?: string | null;
  consumed_by?: string | null;
  created_at: string;
}

export interface WorkOrder {
  id: string;
  mo_id: string;
  sequence: number;
  name: string;
  description?: string | null;
  operation_id?: string | null;
  work_center_id?: string | null;
  status: WorkOrderStatus;
  quantity_planned: string;
  quantity_done: string;
  quantity_scrapped: string;
  setup_time_planned: string;
  operation_time_planned: string;
  setup_time_actual: string;
  operation_time_actual: string;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  actual_start?: string | null;
  actual_end?: string | null;
  operator_id?: string | null;
  labor_cost: string;
  machine_cost: string;
  created_at: string;
  updated_at: string;
}

export interface ManufacturingOrder {
  id: string;
  number: string;
  name?: string | null;
  product_id: string;
  bom_id?: string | null;
  routing_id?: string | null;
  quantity_planned: string;
  quantity_produced: string;
  quantity_scrapped: string;
  unit: string;
  status: MOStatus;
  priority: MOPriority;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  actual_start?: string | null;
  actual_end?: string | null;
  deadline?: string | null;
  warehouse_id?: string | null;
  location_id?: string | null;
  origin_type?: string | null;
  origin_id?: string | null;
  origin_number?: string | null;
  planned_cost: string;
  actual_cost: string;
  material_cost: string;
  labor_cost: string;
  overhead_cost: string;
  currency: string;
  responsible_id?: string | null;
  progress_percent: string;
  work_orders: WorkOrder[];
  consumptions: Consumption[];
  created_at: string;
  updated_at: string;
}

export interface ManufacturingOrderCreate {
  name?: string | null;
  product_id: string;
  bom_id?: string | null;
  routing_id?: string | null;
  quantity_planned: string;
  unit?: string;
  priority?: MOPriority;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  deadline?: string | null;
  warehouse_id?: string | null;
  location_id?: string | null;
  origin_type?: string | null;
  origin_id?: string | null;
  origin_number?: string | null;
  responsible_id?: string | null;
  notes?: string | null;
}

export interface ManufacturingOrderUpdate {
  name?: string | null;
  priority?: MOPriority | null;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  deadline?: string | null;
  warehouse_id?: string | null;
  location_id?: string | null;
  responsible_id?: string | null;
  notes?: string | null;
}

export interface ManufacturingOrderList {
  items: ManufacturingOrder[];
  total: number;
}

// ============================================================================
// WORK ORDER REQUESTS
// ============================================================================

export interface WorkOrderUpdate {
  work_center_id?: string | null;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  operator_id?: string | null;
  notes?: string | null;
}

export interface StartWorkOrderRequest {
  operator_id?: string | null;
}

export interface CompleteWorkOrderRequest {
  quantity_done: string;
  quantity_scrapped?: string;
  scrap_reason?: ScrapReason | null;
  notes?: string | null;
}

// ============================================================================
// CONSUMPTION / PRODUCTION
// ============================================================================

export interface ConsumeRequest {
  product_id: string;
  quantity: string;
  lot_id?: string | null;
  serial_id?: string | null;
  warehouse_id?: string | null;
  location_id?: string | null;
  work_order_id?: string | null;
  notes?: string | null;
}

export interface ReturnRequest {
  consumption_id: string;
  quantity: string;
  notes?: string | null;
}

export interface ProduceRequest {
  quantity: string;
  lot_id?: string | null;
  serial_ids?: string[] | null;
  warehouse_id?: string | null;
  location_id?: string | null;
  work_order_id?: string | null;
  is_quality_passed?: boolean;
  quality_notes?: string | null;
  notes?: string | null;
}

export interface ProductionOutput {
  id: string;
  mo_id: string;
  work_order_id?: string | null;
  product_id: string;
  quantity: string;
  unit: string;
  lot_id?: string | null;
  serial_ids?: string[] | null;
  warehouse_id?: string | null;
  location_id?: string | null;
  is_quality_passed: boolean;
  quality_notes?: string | null;
  unit_cost: string;
  total_cost: string;
  produced_at: string;
  produced_by?: string | null;
  created_at: string;
}

// ============================================================================
// SCRAPS
// ============================================================================

export interface Scrap {
  id: string;
  mo_id?: string | null;
  work_order_id?: string | null;
  product_id: string;
  quantity: string;
  unit: string;
  lot_id?: string | null;
  serial_id?: string | null;
  reason: ScrapReason;
  reason_detail?: string | null;
  work_center_id?: string | null;
  unit_cost: string;
  total_cost: string;
  scrapped_at: string;
  scrapped_by?: string | null;
  created_at: string;
}

export interface ScrapCreate {
  mo_id?: string | null;
  work_order_id?: string | null;
  product_id: string;
  quantity: string;
  unit?: string;
  lot_id?: string | null;
  serial_id?: string | null;
  reason?: ScrapReason;
  reason_detail?: string | null;
  work_center_id?: string | null;
  notes?: string | null;
}

// ============================================================================
// PLANNING
// ============================================================================

export interface PlanLine {
  id: string;
  plan_id: string;
  product_id: string;
  bom_id?: string | null;
  quantity_demanded: string;
  quantity_available: string;
  quantity_to_produce: string;
  required_date?: string | null;
  planned_start?: string | null;
  planned_end?: string | null;
  mo_id?: string | null;
  priority: MOPriority;
  notes?: string | null;
  created_at: string;
}

export interface PlanLineCreate {
  product_id: string;
  bom_id?: string | null;
  quantity_demanded: string;
  required_date?: string | null;
  priority?: MOPriority;
  notes?: string | null;
}

export interface ProductionPlan {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  start_date: string;
  end_date: string;
  planning_horizon_days: number;
  status: string;
  planning_method: string;
  total_orders: number;
  total_quantity: string;
  total_hours: string;
  generated_at?: string | null;
  approved_at?: string | null;
  approved_by?: string | null;
  lines: PlanLine[];
  created_at: string;
  updated_at: string;
}

export interface ProductionPlanCreate {
  code: string;
  name: string;
  description?: string | null;
  start_date: string;
  end_date: string;
  planning_horizon_days?: number;
  planning_method?: string;
  notes?: string | null;
  lines?: PlanLineCreate[];
}

// ============================================================================
// MAINTENANCE
// ============================================================================

export interface MaintenanceSchedule {
  id: string;
  work_center_id: string;
  name: string;
  description?: string | null;
  frequency_type: string;
  frequency_value: number;
  duration_hours: string;
  last_maintenance?: string | null;
  next_maintenance?: string | null;
  cycles_since_last: number;
  hours_since_last: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface MaintenanceScheduleCreate {
  work_center_id: string;
  name: string;
  description?: string | null;
  frequency_type: string;
  frequency_value?: number;
  duration_hours?: string;
  notes?: string | null;
}

// ============================================================================
// DASHBOARD
// ============================================================================

export interface ProductionDashboard {
  // Manufacturing orders
  total_orders: number;
  orders_draft: number;
  orders_confirmed: number;
  orders_in_progress: number;
  orders_done_today: number;
  orders_done_this_week: number;
  orders_late: number;
  // Production
  quantity_produced_today: string;
  quantity_produced_this_week: string;
  quantity_scrapped_today: string;
  scrap_rate: string;
  // Work centers
  total_work_centers: number;
  work_centers_available: number;
  work_centers_busy: number;
  work_centers_maintenance: number;
  average_oee: string;
  // Costs
  total_cost_this_month: string;
  material_cost_this_month: string;
  labor_cost_this_month: string;
  // Alerts
  low_material_alerts: number;
  maintenance_due: number;
  quality_issues: number;
  // Top products
  top_products_produced: Array<Record<string, unknown>>;
  // Urgent orders
  urgent_orders: Array<Record<string, unknown>>;
}

// ============================================================================
// TIME ENTRIES
// ============================================================================

export interface TimeEntry {
  id: string;
  work_order_id: string;
  entry_type: string;
  operator_id: string;
  start_time: string;
  end_time?: string | null;
  duration_minutes?: string | null;
  quantity_produced: string;
  quantity_scrapped: string;
  scrap_reason?: ScrapReason | null;
  notes?: string | null;
  created_at: string;
}

export interface TimeEntryCreate {
  work_order_id: string;
  entry_type?: string;
  operator_id: string;
  start_time: string;
  end_time?: string | null;
  quantity_produced?: string;
  quantity_scrapped?: string;
  scrap_reason?: ScrapReason | null;
  notes?: string | null;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/production';

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

export const productionApi = {
  // ==========================================================================
  // Work Centers
  // ==========================================================================

  createWorkCenter: (data: WorkCenterCreate) =>
    api.post<WorkCenter>(`${BASE_PATH}/work-centers`, data),

  listWorkCenters: (params?: {
    status?: WorkCenterStatus;
    type?: WorkCenterType;
    skip?: number;
    limit?: number;
  }) =>
    api.get<WorkCenter[]>(`${BASE_PATH}/work-centers${buildQueryString(params || {})}`),

  getWorkCenter: (wcId: string) =>
    api.get<WorkCenter>(`${BASE_PATH}/work-centers/${wcId}`),

  updateWorkCenter: (wcId: string, data: WorkCenterUpdate) =>
    api.put<WorkCenter>(`${BASE_PATH}/work-centers/${wcId}`, data),

  setWorkCenterStatus: (wcId: string, status: WorkCenterStatus) =>
    api.post<WorkCenter>(`${BASE_PATH}/work-centers/${wcId}/status/${status}`, {}),

  listWorkOrdersForWorkCenter: (wcId: string, status?: WorkOrderStatus) =>
    api.get<WorkOrder[]>(
      `${BASE_PATH}/work-centers/${wcId}/work-orders${buildQueryString({ status })}`
    ),

  // ==========================================================================
  // BOMs
  // ==========================================================================

  createBom: (data: BOMCreate) =>
    api.post<BOM>(`${BASE_PATH}/bom`, data),

  listBoms: (params?: {
    product_id?: string;
    status?: BOMStatus;
    skip?: number;
    limit?: number;
  }) =>
    api.get<BOMList>(`${BASE_PATH}/bom${buildQueryString(params || {})}`),

  getBom: (bomId: string) =>
    api.get<BOM>(`${BASE_PATH}/bom/${bomId}`),

  getBomForProduct: (productId: string) =>
    api.get<BOM>(`${BASE_PATH}/bom/product/${productId}`),

  updateBom: (bomId: string, data: BOMUpdate) =>
    api.put<BOM>(`${BASE_PATH}/bom/${bomId}`, data),

  activateBom: (bomId: string) =>
    api.post<BOM>(`${BASE_PATH}/bom/${bomId}/activate`, {}),

  addBomLine: (bomId: string, data: BOMLineCreate) =>
    api.post<BOMLine>(`${BASE_PATH}/bom/${bomId}/lines`, data),

  // ==========================================================================
  // Routings
  // ==========================================================================

  createRouting: (data: RoutingCreate) =>
    api.post<Routing>(`${BASE_PATH}/routings`, data),

  listRoutings: (params?: {
    product_id?: string;
    skip?: number;
    limit?: number;
  }) =>
    api.get<Routing[]>(`${BASE_PATH}/routings${buildQueryString(params || {})}`),

  getRouting: (routingId: string) =>
    api.get<Routing>(`${BASE_PATH}/routings/${routingId}`),

  // ==========================================================================
  // Manufacturing Orders
  // ==========================================================================

  createManufacturingOrder: (data: ManufacturingOrderCreate) =>
    api.post<ManufacturingOrder>(`${BASE_PATH}/orders`, data),

  listManufacturingOrders: (params?: {
    status?: MOStatus;
    priority?: MOPriority;
    product_id?: string;
    date_from?: string;
    date_to?: string;
    skip?: number;
    limit?: number;
  }) =>
    api.get<ManufacturingOrderList>(`${BASE_PATH}/orders${buildQueryString(params || {})}`),

  getManufacturingOrder: (moId: string) =>
    api.get<ManufacturingOrder>(`${BASE_PATH}/orders/${moId}`),

  updateManufacturingOrder: (moId: string, data: ManufacturingOrderUpdate) =>
    api.put<ManufacturingOrder>(`${BASE_PATH}/orders/${moId}`, data),

  confirmManufacturingOrder: (moId: string) =>
    api.post<ManufacturingOrder>(`${BASE_PATH}/orders/${moId}/confirm`, {}),

  startManufacturingOrder: (moId: string) =>
    api.post<ManufacturingOrder>(`${BASE_PATH}/orders/${moId}/start`, {}),

  completeManufacturingOrder: (moId: string) =>
    api.post<ManufacturingOrder>(`${BASE_PATH}/orders/${moId}/complete`, {}),

  cancelManufacturingOrder: (moId: string) =>
    api.post<ManufacturingOrder>(`${BASE_PATH}/orders/${moId}/cancel`, {}),

  // ==========================================================================
  // Work Orders
  // ==========================================================================

  getWorkOrder: (woId: string) =>
    api.get<WorkOrder>(`${BASE_PATH}/work-orders/${woId}`),

  startWorkOrder: (woId: string, data?: StartWorkOrderRequest) =>
    api.post<WorkOrder>(`${BASE_PATH}/work-orders/${woId}/start`, data || {}),

  completeWorkOrder: (woId: string, data: CompleteWorkOrderRequest) =>
    api.post<WorkOrder>(`${BASE_PATH}/work-orders/${woId}/complete`, data),

  pauseWorkOrder: (woId: string) =>
    api.post<WorkOrder>(`${BASE_PATH}/work-orders/${woId}/pause`, {}),

  resumeWorkOrder: (woId: string) =>
    api.post<WorkOrder>(`${BASE_PATH}/work-orders/${woId}/resume`, {}),

  // ==========================================================================
  // Consumption
  // ==========================================================================

  consumeMaterial: (moId: string, data: ConsumeRequest) =>
    api.post<Consumption>(`${BASE_PATH}/orders/${moId}/consume`, data),

  returnMaterial: (data: ReturnRequest) =>
    api.post<Consumption>(`${BASE_PATH}/consumptions/return`, data),

  // ==========================================================================
  // Production Output
  // ==========================================================================

  produce: (moId: string, data: ProduceRequest) =>
    api.post<ProductionOutput>(`${BASE_PATH}/orders/${moId}/produce`, data),

  // ==========================================================================
  // Scraps
  // ==========================================================================

  createScrap: (data: ScrapCreate) =>
    api.post<Scrap>(`${BASE_PATH}/scraps`, data),

  listScraps: (params?: {
    mo_id?: string;
    product_id?: string;
    date_from?: string;
    date_to?: string;
    skip?: number;
    limit?: number;
  }) =>
    api.get<Scrap[]>(`${BASE_PATH}/scraps${buildQueryString(params || {})}`),

  // ==========================================================================
  // Planning
  // ==========================================================================

  createProductionPlan: (data: ProductionPlanCreate) =>
    api.post<ProductionPlan>(`${BASE_PATH}/plans`, data),

  getProductionPlan: (planId: string) =>
    api.get<ProductionPlan>(`${BASE_PATH}/plans/${planId}`),

  // ==========================================================================
  // Maintenance
  // ==========================================================================

  createMaintenanceSchedule: (data: MaintenanceScheduleCreate) =>
    api.post<MaintenanceSchedule>(`${BASE_PATH}/maintenance`, data),

  listMaintenanceSchedules: (workCenterId?: string) =>
    api.get<MaintenanceSchedule[]>(
      `${BASE_PATH}/maintenance${buildQueryString({ work_center_id: workCenterId })}`
    ),

  getDueMaintenance: () =>
    api.get<MaintenanceSchedule[]>(`${BASE_PATH}/maintenance/due`),

  // ==========================================================================
  // Dashboard
  // ==========================================================================

  getDashboard: () =>
    api.get<ProductionDashboard>(`${BASE_PATH}/dashboard`),
};

export default productionApi;
