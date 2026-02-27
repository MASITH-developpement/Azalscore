/**
 * AZALSCORE Module - Manufacturing (GPAO) Types
 * Types TypeScript pour la gestion de production
 */

// ============================================================================
// ENUMS
// ============================================================================

export type BOMType =
  | 'manufacturing'
  | 'assembly'
  | 'subcontracting'
  | 'phantom'
  | 'kit';

export type BOMStatus =
  | 'draft'
  | 'active'
  | 'obsolete';

export type WorkcenterType =
  | 'machine'
  | 'manual'
  | 'assembly'
  | 'quality'
  | 'packaging';

export type WorkcenterState =
  | 'available'
  | 'busy'
  | 'maintenance'
  | 'offline';

export type WorkOrderStatus =
  | 'draft'
  | 'confirmed'
  | 'planned'
  | 'in_progress'
  | 'paused'
  | 'completed'
  | 'cancelled';

export type OperationStatus =
  | 'pending'
  | 'ready'
  | 'in_progress'
  | 'completed'
  | 'blocked';

export type QualityCheckType =
  | 'incoming'
  | 'in_process'
  | 'final';

export type QualityResult =
  | 'pass'
  | 'fail'
  | 'conditional';

// ============================================================================
// BOM LINE
// ============================================================================

export interface BOMLine {
  id: string;
  tenant_id: string;
  bom_id: string;
  component_id: string;
  component_code: string;
  component_name: string;
  quantity: number | string;
  unit: string;
  unit_cost: number | string;
  total_cost: number | string;
  is_optional: boolean;
  scrap_rate: number | string;
  sequence: number;
  operation_id?: string;
  substitute_ids: string[];
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface BOMLineCreate {
  component_id: string;
  component_code: string;
  component_name: string;
  quantity?: number;
  unit?: string;
  unit_cost?: number;
  is_optional?: boolean;
  scrap_rate?: number;
  sequence?: number;
  operation_id?: string;
  notes?: string;
}

export interface BOMLineUpdate {
  component_id?: string;
  component_code?: string;
  component_name?: string;
  quantity?: number;
  unit?: string;
  unit_cost?: number;
  is_optional?: boolean;
  scrap_rate?: number;
  sequence?: number;
  operation_id?: string;
  notes?: string;
}

// ============================================================================
// BOM (Bill of Materials)
// ============================================================================

export interface BOM {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  bom_type: BOMType;
  status: BOMStatus;
  product_id: string;
  product_code: string;
  product_name: string;
  quantity: number | string;
  unit: string;
  yield_rate: number | string;
  material_cost: number | string;
  labor_cost: number | string;
  overhead_cost: number | string;
  total_cost: number | string;
  bom_version: number;
  is_current: boolean;
  valid_from?: string;
  valid_until?: string;
  routing_id?: string;
  lines: BOMLine[];
  tags: string[];
  extra_data: Record<string, unknown>;
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export interface BOMCreate {
  code: string;
  name: string;
  description?: string;
  bom_type?: BOMType;
  product_id: string;
  product_code: string;
  product_name: string;
  quantity?: number;
  unit?: string;
  yield_rate?: number;
  valid_from?: string;
  valid_until?: string;
  routing_id?: string;
  lines?: BOMLineCreate[];
  tags?: string[];
  extra_data?: Record<string, unknown>;
}

export interface BOMUpdate {
  name?: string;
  description?: string;
  bom_type?: BOMType;
  status?: BOMStatus;
  product_id?: string;
  product_code?: string;
  product_name?: string;
  quantity?: number;
  unit?: string;
  yield_rate?: number;
  valid_from?: string;
  valid_until?: string;
  routing_id?: string;
  labor_cost?: number;
  overhead_cost?: number;
  tags?: string[];
  extra_data?: Record<string, unknown>;
}

// ============================================================================
// WORKCENTER
// ============================================================================

export interface Workcenter {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  workcenter_type: WorkcenterType;
  state: WorkcenterState;
  capacity: number;
  efficiency: number | string;
  hourly_cost: number | string;
  setup_time_minutes: number;
  cleanup_time_minutes: number;
  location?: string;
  is_active: boolean;
  current_operator_id?: string;
  current_operator_name?: string;
  last_maintenance_at?: string;
  next_maintenance_at?: string;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface WorkcenterCreate {
  code: string;
  name: string;
  description?: string;
  workcenter_type?: WorkcenterType;
  capacity?: number;
  efficiency?: number;
  hourly_cost?: number;
  setup_time_minutes?: number;
  cleanup_time_minutes?: number;
  location?: string;
  notes?: string;
}

export interface WorkcenterUpdate {
  name?: string;
  description?: string;
  workcenter_type?: WorkcenterType;
  state?: WorkcenterState;
  capacity?: number;
  efficiency?: number;
  hourly_cost?: number;
  setup_time_minutes?: number;
  cleanup_time_minutes?: number;
  location?: string;
  is_active?: boolean;
  notes?: string;
}

// ============================================================================
// ROUTING & OPERATIONS
// ============================================================================

export interface RoutingOperation {
  id: string;
  tenant_id: string;
  routing_id: string;
  sequence: number;
  name: string;
  description?: string;
  workcenter_id: string;
  workcenter_name?: string;
  duration_minutes: number;
  setup_minutes: number;
  teardown_minutes: number;
  is_quality_checkpoint: boolean;
  instructions?: string;
  created_at: string;
  updated_at?: string;
}

export interface Routing {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  product_id?: string;
  product_name?: string;
  is_active: boolean;
  total_duration_minutes: number;
  operations: RoutingOperation[];
  created_at: string;
  updated_at?: string;
}

export interface RoutingCreate {
  code: string;
  name: string;
  description?: string;
  product_id?: string;
  operations?: Omit<RoutingOperation, 'id' | 'tenant_id' | 'routing_id' | 'created_at' | 'updated_at'>[];
}

// ============================================================================
// WORK ORDER
// ============================================================================

export interface WorkOrderOperation {
  id: string;
  work_order_id: string;
  routing_operation_id?: string;
  sequence: number;
  name: string;
  workcenter_id: string;
  workcenter_name?: string;
  status: OperationStatus;
  planned_duration_minutes: number;
  actual_duration_minutes?: number;
  operator_id?: string;
  operator_name?: string;
  started_at?: string;
  completed_at?: string;
  notes?: string;
}

export interface WorkOrder {
  id: string;
  tenant_id: string;
  work_order_number: string;
  name: string;
  description?: string;
  status: WorkOrderStatus;
  priority: number;
  bom_id: string;
  bom_code?: string;
  product_id: string;
  product_code: string;
  product_name: string;
  quantity_planned: number | string;
  quantity_produced: number | string;
  quantity_scrapped: number | string;
  unit: string;
  planned_start: string;
  planned_end: string;
  actual_start?: string;
  actual_end?: string;
  routing_id?: string;
  operations: WorkOrderOperation[];
  sale_order_id?: string;
  sale_order_number?: string;
  customer_id?: string;
  customer_name?: string;
  assigned_to_id?: string;
  assigned_to_name?: string;
  notes?: string;
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export interface WorkOrderCreate {
  name: string;
  description?: string;
  priority?: number;
  bom_id: string;
  product_id: string;
  product_code: string;
  product_name: string;
  quantity_planned: number;
  unit?: string;
  planned_start: string;
  planned_end: string;
  routing_id?: string;
  sale_order_id?: string;
  customer_id?: string;
  assigned_to_id?: string;
  notes?: string;
}

export interface WorkOrderUpdate {
  name?: string;
  description?: string;
  status?: WorkOrderStatus;
  priority?: number;
  quantity_planned?: number;
  planned_start?: string;
  planned_end?: string;
  assigned_to_id?: string;
  notes?: string;
}

// ============================================================================
// QUALITY CHECK
// ============================================================================

export interface QualityCheck {
  id: string;
  tenant_id: string;
  check_number: string;
  check_type: QualityCheckType;
  result: QualityResult;
  work_order_id?: string;
  work_order_number?: string;
  operation_id?: string;
  product_id: string;
  product_code: string;
  product_name: string;
  quantity_checked: number;
  quantity_passed: number;
  quantity_failed: number;
  inspector_id?: string;
  inspector_name?: string;
  criteria: QualityCriterion[];
  notes?: string;
  checked_at: string;
  created_at: string;
}

export interface QualityCriterion {
  name: string;
  expected_value: string;
  actual_value: string;
  is_passed: boolean;
  notes?: string;
}

export interface QualityCheckCreate {
  check_type: QualityCheckType;
  work_order_id?: string;
  operation_id?: string;
  product_id: string;
  product_code: string;
  product_name: string;
  quantity_checked: number;
  criteria: Omit<QualityCriterion, 'is_passed'>[];
  notes?: string;
}

// ============================================================================
// MATERIAL CONSUMPTION
// ============================================================================

export interface MaterialConsumption {
  id: string;
  tenant_id: string;
  work_order_id: string;
  bom_line_id?: string;
  component_id: string;
  component_code: string;
  component_name: string;
  planned_quantity: number | string;
  consumed_quantity: number | string;
  unit: string;
  warehouse_id?: string;
  lot_number?: string;
  consumed_at: string;
  consumed_by?: string;
}

// ============================================================================
// STATS & DASHBOARD
// ============================================================================

export interface ManufacturingStats {
  active_work_orders: number;
  completed_today: number;
  in_progress: number;
  delayed: number;
  total_boms: number;
  active_boms: number;
  workcenters_available: number;
  workcenters_busy: number;
  workcenters_maintenance: number;
  oee_today: number; // Overall Equipment Effectiveness
  production_rate: number;
  scrap_rate: number;
  quality_pass_rate: number;
}

export interface ManufacturingDashboard {
  stats: ManufacturingStats;
  recent_work_orders: WorkOrder[];
  pending_quality_checks: QualityCheck[];
  workcenter_status: Workcenter[];
  upcoming_maintenance: Workcenter[];
}

// ============================================================================
// LIST RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export type BOMListResponse = PaginatedResponse<BOM>;
export type WorkOrderListResponse = PaginatedResponse<WorkOrder>;
export type WorkcenterListResponse = PaginatedResponse<Workcenter>;
export type RoutingListResponse = PaginatedResponse<Routing>;
export type QualityCheckListResponse = PaginatedResponse<QualityCheck>;

// ============================================================================
// FILTERS
// ============================================================================

export interface BOMFilters {
  status?: BOMStatus;
  bom_type?: BOMType;
  product_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface WorkOrderFilters {
  status?: WorkOrderStatus;
  product_id?: string;
  customer_id?: string;
  assigned_to_id?: string;
  from_date?: string;
  to_date?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface WorkcenterFilters {
  workcenter_type?: WorkcenterType;
  state?: WorkcenterState;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

// ============================================================================
// CONFIG CONSTANTS
// ============================================================================

export const BOM_TYPE_CONFIG: Record<BOMType, { label: string; color: string }> = {
  manufacturing: { label: 'Fabrication', color: 'blue' },
  assembly: { label: 'Assemblage', color: 'green' },
  subcontracting: { label: 'Sous-traitance', color: 'purple' },
  phantom: { label: 'Fantome', color: 'gray' },
  kit: { label: 'Kit', color: 'orange' },
};

export const BOM_STATUS_CONFIG: Record<BOMStatus, { label: string; color: string }> = {
  draft: { label: 'Brouillon', color: 'gray' },
  active: { label: 'Actif', color: 'green' },
  obsolete: { label: 'Obsolete', color: 'red' },
};

export const WORK_ORDER_STATUS_CONFIG: Record<WorkOrderStatus, { label: string; color: string }> = {
  draft: { label: 'Brouillon', color: 'gray' },
  confirmed: { label: 'Confirme', color: 'blue' },
  planned: { label: 'Planifie', color: 'purple' },
  in_progress: { label: 'En cours', color: 'orange' },
  paused: { label: 'En pause', color: 'yellow' },
  completed: { label: 'Termine', color: 'green' },
  cancelled: { label: 'Annule', color: 'red' },
};

export const WORKCENTER_STATE_CONFIG: Record<WorkcenterState, { label: string; color: string }> = {
  available: { label: 'Disponible', color: 'green' },
  busy: { label: 'Occupe', color: 'orange' },
  maintenance: { label: 'Maintenance', color: 'yellow' },
  offline: { label: 'Hors ligne', color: 'red' },
};
