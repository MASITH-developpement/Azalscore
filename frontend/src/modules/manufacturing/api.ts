/**
 * AZALSCORE Module - Manufacturing API
 * Client API pour le module GPAO/Production
 */

import { api } from '@core/api-client';
import type {
  BOM, BOMCreate, BOMUpdate, BOMListResponse, BOMFilters,
  WorkOrder, WorkOrderCreate, WorkOrderUpdate, WorkOrderListResponse, WorkOrderFilters,
  Workcenter, WorkcenterCreate, WorkcenterUpdate, WorkcenterListResponse, WorkcenterFilters,
  Routing, RoutingCreate, RoutingListResponse,
  QualityCheck, QualityCheckCreate, QualityCheckListResponse,
  ManufacturingStats, ManufacturingDashboard,
  BOMLine, BOMLineCreate, BOMLineUpdate,
} from './types';

const BASE_URL = '/manufacturing';

// ============================================================================
// BOM API
// ============================================================================

export const bomApi = {
  list: async (filters?: BOMFilters): Promise<BOMListResponse> => {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.bom_type) params.set('bom_type', filters.bom_type);
    if (filters?.product_id) params.set('product_id', filters.product_id);
    if (filters?.search) params.set('search', filters.search);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    const response = await api.get<BOMListResponse>(`${BASE_URL}/boms?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<BOM> => {
    const response = await api.get<BOM>(`${BASE_URL}/boms/${id}`);
    return response.data;
  },

  create: async (data: BOMCreate): Promise<BOM> => {
    const response = await api.post<BOM>(`${BASE_URL}/boms`, data);
    return response.data;
  },

  update: async (id: string, data: BOMUpdate): Promise<BOM> => {
    const response = await api.put<BOM>(`${BASE_URL}/boms/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/boms/${id}`);
  },

  activate: async (id: string): Promise<BOM> => {
    const response = await api.post<BOM>(`${BASE_URL}/boms/${id}/activate`);
    return response.data;
  },

  duplicate: async (id: string): Promise<BOM> => {
    const response = await api.post<BOM>(`${BASE_URL}/boms/${id}/duplicate`);
    return response.data;
  },

  // BOM Lines
  addLine: async (bomId: string, data: BOMLineCreate): Promise<BOMLine> => {
    const response = await api.post<BOMLine>(`${BASE_URL}/boms/${bomId}/lines`, data);
    return response.data;
  },

  updateLine: async (bomId: string, lineId: string, data: BOMLineUpdate): Promise<BOMLine> => {
    const response = await api.put<BOMLine>(`${BASE_URL}/boms/${bomId}/lines/${lineId}`, data);
    return response.data;
  },

  deleteLine: async (bomId: string, lineId: string): Promise<void> => {
    await api.delete(`${BASE_URL}/boms/${bomId}/lines/${lineId}`);
  },

  // Cost calculation
  calculateCost: async (id: string): Promise<{ material_cost: number; labor_cost: number; overhead_cost: number; total_cost: number }> => {
    const response = await api.get<{ material_cost: number; labor_cost: number; overhead_cost: number; total_cost: number }>(`${BASE_URL}/boms/${id}/cost`);
    return response.data;
  },
};

// ============================================================================
// WORK ORDER API
// ============================================================================

export const workOrderApi = {
  list: async (filters?: WorkOrderFilters): Promise<WorkOrderListResponse> => {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.product_id) params.set('product_id', filters.product_id);
    if (filters?.customer_id) params.set('customer_id', filters.customer_id);
    if (filters?.assigned_to_id) params.set('assigned_to_id', filters.assigned_to_id);
    if (filters?.from_date) params.set('from_date', filters.from_date);
    if (filters?.to_date) params.set('to_date', filters.to_date);
    if (filters?.search) params.set('search', filters.search);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    const response = await api.get<WorkOrderListResponse>(`${BASE_URL}/work-orders?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<WorkOrder> => {
    const response = await api.get<WorkOrder>(`${BASE_URL}/work-orders/${id}`);
    return response.data;
  },

  create: async (data: WorkOrderCreate): Promise<WorkOrder> => {
    const response = await api.post<WorkOrder>(`${BASE_URL}/work-orders`, data);
    return response.data;
  },

  update: async (id: string, data: WorkOrderUpdate): Promise<WorkOrder> => {
    const response = await api.put<WorkOrder>(`${BASE_URL}/work-orders/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/work-orders/${id}`);
  },

  // Status transitions
  confirm: async (id: string): Promise<WorkOrder> => {
    const response = await api.post<WorkOrder>(`${BASE_URL}/work-orders/${id}/confirm`);
    return response.data;
  },

  start: async (id: string): Promise<WorkOrder> => {
    const response = await api.post<WorkOrder>(`${BASE_URL}/work-orders/${id}/start`);
    return response.data;
  },

  pause: async (id: string, reason?: string): Promise<WorkOrder> => {
    const response = await api.post<WorkOrder>(`${BASE_URL}/work-orders/${id}/pause`, { reason });
    return response.data;
  },

  resume: async (id: string): Promise<WorkOrder> => {
    const response = await api.post<WorkOrder>(`${BASE_URL}/work-orders/${id}/resume`);
    return response.data;
  },

  complete: async (id: string, data?: { quantity_produced: number; quantity_scrapped?: number }): Promise<WorkOrder> => {
    const response = await api.post<WorkOrder>(`${BASE_URL}/work-orders/${id}/complete`, data);
    return response.data;
  },

  cancel: async (id: string, reason?: string): Promise<WorkOrder> => {
    const response = await api.post<WorkOrder>(`${BASE_URL}/work-orders/${id}/cancel`, { reason });
    return response.data;
  },

  // Operations
  startOperation: async (workOrderId: string, operationId: string): Promise<void> => {
    await api.post(`${BASE_URL}/work-orders/${workOrderId}/operations/${operationId}/start`);
  },

  completeOperation: async (workOrderId: string, operationId: string, data?: { actual_duration_minutes?: number; notes?: string }): Promise<void> => {
    await api.post(`${BASE_URL}/work-orders/${workOrderId}/operations/${operationId}/complete`, data);
  },

  // Material consumption
  consumeMaterial: async (workOrderId: string, data: { component_id: string; quantity: number; lot_number?: string }): Promise<void> => {
    await api.post(`${BASE_URL}/work-orders/${workOrderId}/consume`, data);
  },

  getConsumption: async (workOrderId: string): Promise<{ items: unknown[]; total: number }> => {
    const response = await api.get<{ items: unknown[]; total: number }>(`${BASE_URL}/work-orders/${workOrderId}/consumption`);
    return response.data;
  },
};

// ============================================================================
// WORKCENTER API
// ============================================================================

export const workcenterApi = {
  list: async (filters?: WorkcenterFilters): Promise<WorkcenterListResponse> => {
    const params = new URLSearchParams();
    if (filters?.workcenter_type) params.set('workcenter_type', filters.workcenter_type);
    if (filters?.state) params.set('state', filters.state);
    if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active));
    if (filters?.search) params.set('search', filters.search);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    const response = await api.get<WorkcenterListResponse>(`${BASE_URL}/workcenters?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<Workcenter> => {
    const response = await api.get<Workcenter>(`${BASE_URL}/workcenters/${id}`);
    return response.data;
  },

  create: async (data: WorkcenterCreate): Promise<Workcenter> => {
    const response = await api.post<Workcenter>(`${BASE_URL}/workcenters`, data);
    return response.data;
  },

  update: async (id: string, data: WorkcenterUpdate): Promise<Workcenter> => {
    const response = await api.put<Workcenter>(`${BASE_URL}/workcenters/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/workcenters/${id}`);
  },

  // State management
  setAvailable: async (id: string): Promise<Workcenter> => {
    const response = await api.post<Workcenter>(`${BASE_URL}/workcenters/${id}/available`);
    return response.data;
  },

  setMaintenance: async (id: string, data?: { reason?: string; expected_end?: string }): Promise<Workcenter> => {
    const response = await api.post<Workcenter>(`${BASE_URL}/workcenters/${id}/maintenance`, data);
    return response.data;
  },

  setOffline: async (id: string, reason?: string): Promise<Workcenter> => {
    const response = await api.post<Workcenter>(`${BASE_URL}/workcenters/${id}/offline`, { reason });
    return response.data;
  },

  // Capacity planning
  getSchedule: async (id: string, from: string, to: string): Promise<{ slots: unknown[] }> => {
    const response = await api.get<{ slots: unknown[] }>(`${BASE_URL}/workcenters/${id}/schedule?from=${from}&to=${to}`);
    return response.data;
  },
};

// ============================================================================
// ROUTING API
// ============================================================================

export const routingApi = {
  list: async (filters?: { product_id?: string; is_active?: boolean; search?: string; page?: number; page_size?: number }): Promise<RoutingListResponse> => {
    const params = new URLSearchParams();
    if (filters?.product_id) params.set('product_id', filters.product_id);
    if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active));
    if (filters?.search) params.set('search', filters.search);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    const response = await api.get<RoutingListResponse>(`${BASE_URL}/routings?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<Routing> => {
    const response = await api.get<Routing>(`${BASE_URL}/routings/${id}`);
    return response.data;
  },

  create: async (data: RoutingCreate): Promise<Routing> => {
    const response = await api.post<Routing>(`${BASE_URL}/routings`, data);
    return response.data;
  },

  update: async (id: string, data: Partial<RoutingCreate>): Promise<Routing> => {
    const response = await api.put<Routing>(`${BASE_URL}/routings/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/routings/${id}`);
  },
};

// ============================================================================
// QUALITY API
// ============================================================================

export const qualityApi = {
  list: async (filters?: { check_type?: string; result?: string; work_order_id?: string; from_date?: string; to_date?: string; page?: number; page_size?: number }): Promise<QualityCheckListResponse> => {
    const params = new URLSearchParams();
    if (filters?.check_type) params.set('check_type', filters.check_type);
    if (filters?.result) params.set('result', filters.result);
    if (filters?.work_order_id) params.set('work_order_id', filters.work_order_id);
    if (filters?.from_date) params.set('from_date', filters.from_date);
    if (filters?.to_date) params.set('to_date', filters.to_date);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    const response = await api.get<QualityCheckListResponse>(`${BASE_URL}/quality-checks?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<QualityCheck> => {
    const response = await api.get<QualityCheck>(`${BASE_URL}/quality-checks/${id}`);
    return response.data;
  },

  create: async (data: QualityCheckCreate): Promise<QualityCheck> => {
    const response = await api.post<QualityCheck>(`${BASE_URL}/quality-checks`, data);
    return response.data;
  },
};

// ============================================================================
// STATS & DASHBOARD API
// ============================================================================

export const statsApi = {
  getStats: async (): Promise<ManufacturingStats> => {
    const response = await api.get<ManufacturingStats>(`${BASE_URL}/stats`);
    return response.data;
  },

  getDashboard: async (): Promise<ManufacturingDashboard> => {
    const response = await api.get<ManufacturingDashboard>(`${BASE_URL}/dashboard`);
    return response.data;
  },

  getOEE: async (workcenter_id?: string, from?: string, to?: string): Promise<{ oee: number; availability: number; performance: number; quality: number }> => {
    const params = new URLSearchParams();
    if (workcenter_id) params.set('workcenter_id', workcenter_id);
    if (from) params.set('from', from);
    if (to) params.set('to', to);
    const response = await api.get<{ oee: number; availability: number; performance: number; quality: number }>(`${BASE_URL}/stats/oee?${params}`);
    return response.data;
  },

  getProductionReport: async (from: string, to: string): Promise<{ total_produced: number; total_scrapped: number; by_product: unknown[]; by_workcenter: unknown[] }> => {
    const response = await api.get<{ total_produced: number; total_scrapped: number; by_product: unknown[]; by_workcenter: unknown[] }>(`${BASE_URL}/reports/production?from=${from}&to=${to}`);
    return response.data;
  },
};

// ============================================================================
// PLANNING API
// ============================================================================

export const planningApi = {
  getGantt: async (from: string, to: string): Promise<{ work_orders: unknown[]; operations: unknown[] }> => {
    const response = await api.get<{ work_orders: unknown[]; operations: unknown[] }>(`${BASE_URL}/planning/gantt?from=${from}&to=${to}`);
    return response.data;
  },

  autoSchedule: async (work_order_ids: string[]): Promise<{ scheduled: number; conflicts: unknown[] }> => {
    const response = await api.post<{ scheduled: number; conflicts: unknown[] }>(`${BASE_URL}/planning/auto-schedule`, { work_order_ids });
    return response.data;
  },

  checkCapacity: async (product_id: string, quantity: number, desired_date: string): Promise<{ can_produce: boolean; earliest_date: string; constraints: string[] }> => {
    const response = await api.post<{ can_produce: boolean; earliest_date: string; constraints: string[] }>(`${BASE_URL}/planning/capacity-check`, { product_id, quantity, desired_date });
    return response.data;
  },
};
