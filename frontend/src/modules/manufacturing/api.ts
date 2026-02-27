/**
 * AZALSCORE Module - Manufacturing API
 * Client API pour le module GPAO/Production
 */

import { api } from '@/core/api-client';
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
    return api.get(`${BASE_URL}/boms?${params}`);
  },

  get: async (id: string): Promise<BOM> => {
    return api.get(`${BASE_URL}/boms/${id}`);
  },

  create: async (data: BOMCreate): Promise<BOM> => {
    return api.post(`${BASE_URL}/boms`, data);
  },

  update: async (id: string, data: BOMUpdate): Promise<BOM> => {
    return api.put(`${BASE_URL}/boms/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/boms/${id}`);
  },

  activate: async (id: string): Promise<BOM> => {
    return api.post(`${BASE_URL}/boms/${id}/activate`);
  },

  duplicate: async (id: string): Promise<BOM> => {
    return api.post(`${BASE_URL}/boms/${id}/duplicate`);
  },

  // BOM Lines
  addLine: async (bomId: string, data: BOMLineCreate): Promise<BOMLine> => {
    return api.post(`${BASE_URL}/boms/${bomId}/lines`, data);
  },

  updateLine: async (bomId: string, lineId: string, data: BOMLineUpdate): Promise<BOMLine> => {
    return api.put(`${BASE_URL}/boms/${bomId}/lines/${lineId}`, data);
  },

  deleteLine: async (bomId: string, lineId: string): Promise<void> => {
    return api.delete(`${BASE_URL}/boms/${bomId}/lines/${lineId}`);
  },

  // Cost calculation
  calculateCost: async (id: string): Promise<{ material_cost: number; labor_cost: number; overhead_cost: number; total_cost: number }> => {
    return api.get(`${BASE_URL}/boms/${id}/cost`);
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
    return api.get(`${BASE_URL}/work-orders?${params}`);
  },

  get: async (id: string): Promise<WorkOrder> => {
    return api.get(`${BASE_URL}/work-orders/${id}`);
  },

  create: async (data: WorkOrderCreate): Promise<WorkOrder> => {
    return api.post(`${BASE_URL}/work-orders`, data);
  },

  update: async (id: string, data: WorkOrderUpdate): Promise<WorkOrder> => {
    return api.put(`${BASE_URL}/work-orders/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/work-orders/${id}`);
  },

  // Status transitions
  confirm: async (id: string): Promise<WorkOrder> => {
    return api.post(`${BASE_URL}/work-orders/${id}/confirm`);
  },

  start: async (id: string): Promise<WorkOrder> => {
    return api.post(`${BASE_URL}/work-orders/${id}/start`);
  },

  pause: async (id: string, reason?: string): Promise<WorkOrder> => {
    return api.post(`${BASE_URL}/work-orders/${id}/pause`, { reason });
  },

  resume: async (id: string): Promise<WorkOrder> => {
    return api.post(`${BASE_URL}/work-orders/${id}/resume`);
  },

  complete: async (id: string, data?: { quantity_produced: number; quantity_scrapped?: number }): Promise<WorkOrder> => {
    return api.post(`${BASE_URL}/work-orders/${id}/complete`, data);
  },

  cancel: async (id: string, reason?: string): Promise<WorkOrder> => {
    return api.post(`${BASE_URL}/work-orders/${id}/cancel`, { reason });
  },

  // Operations
  startOperation: async (workOrderId: string, operationId: string): Promise<void> => {
    return api.post(`${BASE_URL}/work-orders/${workOrderId}/operations/${operationId}/start`);
  },

  completeOperation: async (workOrderId: string, operationId: string, data?: { actual_duration_minutes?: number; notes?: string }): Promise<void> => {
    return api.post(`${BASE_URL}/work-orders/${workOrderId}/operations/${operationId}/complete`, data);
  },

  // Material consumption
  consumeMaterial: async (workOrderId: string, data: { component_id: string; quantity: number; lot_number?: string }): Promise<void> => {
    return api.post(`${BASE_URL}/work-orders/${workOrderId}/consume`, data);
  },

  getConsumption: async (workOrderId: string): Promise<{ items: unknown[]; total: number }> => {
    return api.get(`${BASE_URL}/work-orders/${workOrderId}/consumption`);
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
    return api.get(`${BASE_URL}/workcenters?${params}`);
  },

  get: async (id: string): Promise<Workcenter> => {
    return api.get(`${BASE_URL}/workcenters/${id}`);
  },

  create: async (data: WorkcenterCreate): Promise<Workcenter> => {
    return api.post(`${BASE_URL}/workcenters`, data);
  },

  update: async (id: string, data: WorkcenterUpdate): Promise<Workcenter> => {
    return api.put(`${BASE_URL}/workcenters/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/workcenters/${id}`);
  },

  // State management
  setAvailable: async (id: string): Promise<Workcenter> => {
    return api.post(`${BASE_URL}/workcenters/${id}/available`);
  },

  setMaintenance: async (id: string, data?: { reason?: string; expected_end?: string }): Promise<Workcenter> => {
    return api.post(`${BASE_URL}/workcenters/${id}/maintenance`, data);
  },

  setOffline: async (id: string, reason?: string): Promise<Workcenter> => {
    return api.post(`${BASE_URL}/workcenters/${id}/offline`, { reason });
  },

  // Capacity planning
  getSchedule: async (id: string, from: string, to: string): Promise<{ slots: unknown[] }> => {
    return api.get(`${BASE_URL}/workcenters/${id}/schedule?from=${from}&to=${to}`);
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
    return api.get(`${BASE_URL}/routings?${params}`);
  },

  get: async (id: string): Promise<Routing> => {
    return api.get(`${BASE_URL}/routings/${id}`);
  },

  create: async (data: RoutingCreate): Promise<Routing> => {
    return api.post(`${BASE_URL}/routings`, data);
  },

  update: async (id: string, data: Partial<RoutingCreate>): Promise<Routing> => {
    return api.put(`${BASE_URL}/routings/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/routings/${id}`);
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
    return api.get(`${BASE_URL}/quality-checks?${params}`);
  },

  get: async (id: string): Promise<QualityCheck> => {
    return api.get(`${BASE_URL}/quality-checks/${id}`);
  },

  create: async (data: QualityCheckCreate): Promise<QualityCheck> => {
    return api.post(`${BASE_URL}/quality-checks`, data);
  },
};

// ============================================================================
// STATS & DASHBOARD API
// ============================================================================

export const statsApi = {
  getStats: async (): Promise<ManufacturingStats> => {
    return api.get(`${BASE_URL}/stats`);
  },

  getDashboard: async (): Promise<ManufacturingDashboard> => {
    return api.get(`${BASE_URL}/dashboard`);
  },

  getOEE: async (workcenter_id?: string, from?: string, to?: string): Promise<{ oee: number; availability: number; performance: number; quality: number }> => {
    const params = new URLSearchParams();
    if (workcenter_id) params.set('workcenter_id', workcenter_id);
    if (from) params.set('from', from);
    if (to) params.set('to', to);
    return api.get(`${BASE_URL}/stats/oee?${params}`);
  },

  getProductionReport: async (from: string, to: string): Promise<{ total_produced: number; total_scrapped: number; by_product: unknown[]; by_workcenter: unknown[] }> => {
    return api.get(`${BASE_URL}/reports/production?from=${from}&to=${to}`);
  },
};

// ============================================================================
// PLANNING API
// ============================================================================

export const planningApi = {
  getGantt: async (from: string, to: string): Promise<{ work_orders: unknown[]; operations: unknown[] }> => {
    return api.get(`${BASE_URL}/planning/gantt?from=${from}&to=${to}`);
  },

  autoSchedule: async (work_order_ids: string[]): Promise<{ scheduled: number; conflicts: unknown[] }> => {
    return api.post(`${BASE_URL}/planning/auto-schedule`, { work_order_ids });
  },

  checkCapacity: async (product_id: string, quantity: number, desired_date: string): Promise<{ can_produce: boolean; earliest_date: string; constraints: string[] }> => {
    return api.post(`${BASE_URL}/planning/capacity-check`, { product_id, quantity, desired_date });
  },
};
