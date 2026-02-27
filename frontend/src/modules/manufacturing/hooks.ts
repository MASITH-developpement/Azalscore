/**
 * AZALSCORE Module - Manufacturing Hooks
 * React Query hooks pour le module GPAO/Production
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bomApi, workOrderApi, workcenterApi, routingApi, qualityApi, statsApi, planningApi } from './api';
import type {
  BOMCreate, BOMUpdate, BOMFilters, BOMLineCreate, BOMLineUpdate,
  WorkOrderCreate, WorkOrderUpdate, WorkOrderFilters,
  WorkcenterCreate, WorkcenterUpdate, WorkcenterFilters,
  RoutingCreate,
  QualityCheckCreate,
} from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const manufacturingKeys = {
  all: ['manufacturing'] as const,

  // BOM
  boms: () => [...manufacturingKeys.all, 'boms'] as const,
  bomList: (filters?: BOMFilters) => [...manufacturingKeys.boms(), 'list', filters] as const,
  bomDetail: (id: string) => [...manufacturingKeys.boms(), 'detail', id] as const,
  bomCost: (id: string) => [...manufacturingKeys.boms(), 'cost', id] as const,

  // Work Orders
  workOrders: () => [...manufacturingKeys.all, 'work-orders'] as const,
  workOrderList: (filters?: WorkOrderFilters) => [...manufacturingKeys.workOrders(), 'list', filters] as const,
  workOrderDetail: (id: string) => [...manufacturingKeys.workOrders(), 'detail', id] as const,
  workOrderConsumption: (id: string) => [...manufacturingKeys.workOrders(), 'consumption', id] as const,

  // Workcenters
  workcenters: () => [...manufacturingKeys.all, 'workcenters'] as const,
  workcenterList: (filters?: WorkcenterFilters) => [...manufacturingKeys.workcenters(), 'list', filters] as const,
  workcenterDetail: (id: string) => [...manufacturingKeys.workcenters(), 'detail', id] as const,
  workcenterSchedule: (id: string, from: string, to: string) => [...manufacturingKeys.workcenters(), 'schedule', id, from, to] as const,

  // Routings
  routings: () => [...manufacturingKeys.all, 'routings'] as const,
  routingList: (filters?: { product_id?: string; is_active?: boolean; search?: string }) => [...manufacturingKeys.routings(), 'list', filters] as const,
  routingDetail: (id: string) => [...manufacturingKeys.routings(), 'detail', id] as const,

  // Quality
  quality: () => [...manufacturingKeys.all, 'quality'] as const,
  qualityList: (filters?: { check_type?: string; result?: string; work_order_id?: string }) => [...manufacturingKeys.quality(), 'list', filters] as const,
  qualityDetail: (id: string) => [...manufacturingKeys.quality(), 'detail', id] as const,

  // Stats & Planning
  stats: () => [...manufacturingKeys.all, 'stats'] as const,
  dashboard: () => [...manufacturingKeys.all, 'dashboard'] as const,
  oee: (workcenter_id?: string, from?: string, to?: string) => [...manufacturingKeys.all, 'oee', workcenter_id, from, to] as const,
  gantt: (from: string, to: string) => [...manufacturingKeys.all, 'gantt', from, to] as const,
};

// ============================================================================
// BOM HOOKS
// ============================================================================

export function useBOMList(filters?: BOMFilters) {
  return useQuery({
    queryKey: manufacturingKeys.bomList(filters),
    queryFn: () => bomApi.list(filters),
  });
}

export function useBOM(id: string) {
  return useQuery({
    queryKey: manufacturingKeys.bomDetail(id),
    queryFn: () => bomApi.get(id),
    enabled: !!id,
  });
}

export function useBOMCost(id: string) {
  return useQuery({
    queryKey: manufacturingKeys.bomCost(id),
    queryFn: () => bomApi.calculateCost(id),
    enabled: !!id,
  });
}

export function useCreateBOM() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BOMCreate) => bomApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.boms() });
    },
  });
}

export function useUpdateBOM() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: BOMUpdate }) => bomApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.bomDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.boms() });
    },
  });
}

export function useDeleteBOM() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => bomApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.boms() });
    },
  });
}

export function useActivateBOM() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => bomApi.activate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.bomDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.boms() });
    },
  });
}

export function useDuplicateBOM() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => bomApi.duplicate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.boms() });
    },
  });
}

export function useAddBOMLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ bomId, data }: { bomId: string; data: BOMLineCreate }) => bomApi.addLine(bomId, data),
    onSuccess: (_, { bomId }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.bomDetail(bomId) });
    },
  });
}

export function useUpdateBOMLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ bomId, lineId, data }: { bomId: string; lineId: string; data: BOMLineUpdate }) =>
      bomApi.updateLine(bomId, lineId, data),
    onSuccess: (_, { bomId }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.bomDetail(bomId) });
    },
  });
}

export function useDeleteBOMLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ bomId, lineId }: { bomId: string; lineId: string }) => bomApi.deleteLine(bomId, lineId),
    onSuccess: (_, { bomId }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.bomDetail(bomId) });
    },
  });
}

// ============================================================================
// WORK ORDER HOOKS
// ============================================================================

export function useWorkOrderList(filters?: WorkOrderFilters) {
  return useQuery({
    queryKey: manufacturingKeys.workOrderList(filters),
    queryFn: () => workOrderApi.list(filters),
  });
}

export function useWorkOrder(id: string) {
  return useQuery({
    queryKey: manufacturingKeys.workOrderDetail(id),
    queryFn: () => workOrderApi.get(id),
    enabled: !!id,
  });
}

export function useWorkOrderConsumption(id: string) {
  return useQuery({
    queryKey: manufacturingKeys.workOrderConsumption(id),
    queryFn: () => workOrderApi.getConsumption(id),
    enabled: !!id,
  });
}

export function useCreateWorkOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WorkOrderCreate) => workOrderApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrders() });
    },
  });
}

export function useUpdateWorkOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkOrderUpdate }) => workOrderApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrderDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrders() });
    },
  });
}

export function useDeleteWorkOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workOrderApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrders() });
    },
  });
}

// Work Order Status Transitions
export function useConfirmWorkOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workOrderApi.confirm(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrderDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrders() });
    },
  });
}

export function useStartWorkOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workOrderApi.start(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrderDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrders() });
    },
  });
}

export function usePauseWorkOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => workOrderApi.pause(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrderDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrders() });
    },
  });
}

export function useResumeWorkOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workOrderApi.resume(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrderDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrders() });
    },
  });
}

export function useCompleteWorkOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: { quantity_produced: number; quantity_scrapped?: number } }) =>
      workOrderApi.complete(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrderDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrders() });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.stats() });
    },
  });
}

export function useCancelWorkOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => workOrderApi.cancel(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrderDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrders() });
    },
  });
}

// Work Order Operations
export function useStartOperation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workOrderId, operationId }: { workOrderId: string; operationId: string }) =>
      workOrderApi.startOperation(workOrderId, operationId),
    onSuccess: (_, { workOrderId }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrderDetail(workOrderId) });
    },
  });
}

export function useCompleteOperation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workOrderId, operationId, data }: { workOrderId: string; operationId: string; data?: { actual_duration_minutes?: number; notes?: string } }) =>
      workOrderApi.completeOperation(workOrderId, operationId, data),
    onSuccess: (_, { workOrderId }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrderDetail(workOrderId) });
    },
  });
}

export function useConsumeMaterial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ workOrderId, data }: { workOrderId: string; data: { component_id: string; quantity: number; lot_number?: string } }) =>
      workOrderApi.consumeMaterial(workOrderId, data),
    onSuccess: (_, { workOrderId }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrderConsumption(workOrderId) });
    },
  });
}

// ============================================================================
// WORKCENTER HOOKS
// ============================================================================

export function useWorkcenterList(filters?: WorkcenterFilters) {
  return useQuery({
    queryKey: manufacturingKeys.workcenterList(filters),
    queryFn: () => workcenterApi.list(filters),
  });
}

export function useWorkcenter(id: string) {
  return useQuery({
    queryKey: manufacturingKeys.workcenterDetail(id),
    queryFn: () => workcenterApi.get(id),
    enabled: !!id,
  });
}

export function useWorkcenterSchedule(id: string, from: string, to: string) {
  return useQuery({
    queryKey: manufacturingKeys.workcenterSchedule(id, from, to),
    queryFn: () => workcenterApi.getSchedule(id, from, to),
    enabled: !!id && !!from && !!to,
  });
}

export function useCreateWorkcenter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WorkcenterCreate) => workcenterApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workcenters() });
    },
  });
}

export function useUpdateWorkcenter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkcenterUpdate }) => workcenterApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workcenterDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workcenters() });
    },
  });
}

export function useDeleteWorkcenter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workcenterApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workcenters() });
    },
  });
}

// Workcenter State
export function useSetWorkcenterAvailable() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workcenterApi.setAvailable(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workcenterDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workcenters() });
    },
  });
}

export function useSetWorkcenterMaintenance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: { reason?: string; expected_end?: string } }) =>
      workcenterApi.setMaintenance(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workcenterDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workcenters() });
    },
  });
}

export function useSetWorkcenterOffline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => workcenterApi.setOffline(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workcenterDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workcenters() });
    },
  });
}

// ============================================================================
// ROUTING HOOKS
// ============================================================================

export function useRoutingList(filters?: { product_id?: string; is_active?: boolean; search?: string; page?: number; page_size?: number }) {
  return useQuery({
    queryKey: manufacturingKeys.routingList(filters),
    queryFn: () => routingApi.list(filters),
  });
}

export function useRouting(id: string) {
  return useQuery({
    queryKey: manufacturingKeys.routingDetail(id),
    queryFn: () => routingApi.get(id),
    enabled: !!id,
  });
}

export function useCreateRouting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: RoutingCreate) => routingApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.routings() });
    },
  });
}

export function useUpdateRouting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<RoutingCreate> }) => routingApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.routingDetail(id) });
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.routings() });
    },
  });
}

export function useDeleteRouting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => routingApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.routings() });
    },
  });
}

// ============================================================================
// QUALITY HOOKS
// ============================================================================

export function useQualityCheckList(filters?: { check_type?: string; result?: string; work_order_id?: string; from_date?: string; to_date?: string; page?: number; page_size?: number }) {
  return useQuery({
    queryKey: manufacturingKeys.qualityList(filters),
    queryFn: () => qualityApi.list(filters),
  });
}

export function useQualityCheck(id: string) {
  return useQuery({
    queryKey: manufacturingKeys.qualityDetail(id),
    queryFn: () => qualityApi.get(id),
    enabled: !!id,
  });
}

export function useCreateQualityCheck() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: QualityCheckCreate) => qualityApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.quality() });
    },
  });
}

// ============================================================================
// STATS & DASHBOARD HOOKS
// ============================================================================

export function useManufacturingStats() {
  return useQuery({
    queryKey: manufacturingKeys.stats(),
    queryFn: () => statsApi.getStats(),
  });
}

export function useManufacturingDashboard() {
  return useQuery({
    queryKey: manufacturingKeys.dashboard(),
    queryFn: () => statsApi.getDashboard(),
  });
}

export function useOEE(workcenter_id?: string, from?: string, to?: string) {
  return useQuery({
    queryKey: manufacturingKeys.oee(workcenter_id, from, to),
    queryFn: () => statsApi.getOEE(workcenter_id, from, to),
  });
}

export function useProductionReport(from: string, to: string) {
  return useQuery({
    queryKey: ['manufacturing', 'report', from, to],
    queryFn: () => statsApi.getProductionReport(from, to),
    enabled: !!from && !!to,
  });
}

// ============================================================================
// PLANNING HOOKS
// ============================================================================

export function useGantt(from: string, to: string) {
  return useQuery({
    queryKey: manufacturingKeys.gantt(from, to),
    queryFn: () => planningApi.getGantt(from, to),
    enabled: !!from && !!to,
  });
}

export function useAutoSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (work_order_ids: string[]) => planningApi.autoSchedule(work_order_ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: manufacturingKeys.workOrders() });
    },
  });
}

export function useCapacityCheck() {
  return useMutation({
    mutationFn: ({ product_id, quantity, desired_date }: { product_id: string; quantity: number; desired_date: string }) =>
      planningApi.checkCapacity(product_id, quantity, desired_date),
  });
}
