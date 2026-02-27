/**
 * AZALSCORE Module - Production - React Query Hooks
 * Hooks pour la gestion de la production et fabrication
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type {
  WorkCenter, BillOfMaterials, ProductionOrder, WorkOrder, ProductionDashboard
} from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const productionKeys = {
  all: ['production'] as const,

  // Dashboard
  dashboard: () => [...productionKeys.all, 'dashboard'] as const,

  // Work Centers
  workCenters: () => [...productionKeys.all, 'work-centers'] as const,
  workCenterDetail: (id: string) => [...productionKeys.workCenters(), id] as const,

  // BOMs
  boms: () => [...productionKeys.all, 'boms'] as const,
  bomDetail: (id: string) => [...productionKeys.boms(), id] as const,

  // Production Orders
  orders: () => [...productionKeys.all, 'orders'] as const,
  ordersList: (filters?: { status?: string; priority?: string }) =>
    [...productionKeys.orders(), serializeFilters(filters)] as const,
  orderDetail: (id: string) => [...productionKeys.all, 'order', id] as const,

  // Work Orders
  workOrders: () => [...productionKeys.all, 'work-orders'] as const,
  workOrdersList: (productionOrderId?: string) =>
    [...productionKeys.workOrders(), productionOrderId] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export const useProductionDashboard = () => {
  return useQuery({
    queryKey: productionKeys.dashboard(),
    queryFn: async () => {
      return api.get<ProductionDashboard>('/production/dashboard').then(r => r.data);
    }
  });
};

// ============================================================================
// WORK CENTER HOOKS
// ============================================================================

export const useWorkCenters = () => {
  return useQuery({
    queryKey: productionKeys.workCenters(),
    queryFn: async () => {
      const response = await api.get<WorkCenter[] | { items: WorkCenter[] }>('/production/work-centers').then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

export const useWorkCenter = (id: string) => {
  return useQuery({
    queryKey: productionKeys.workCenterDetail(id),
    queryFn: async () => {
      return api.get<WorkCenter>(`/production/work-centers/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreateWorkCenter = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<WorkCenter>) => {
      return api.post('/production/work-centers', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.workCenters() })
  });
};

export const useUpdateWorkCenter = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<WorkCenter> }) => {
      return api.put(`/production/work-centers/${id}`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.workCenters() })
  });
};

// ============================================================================
// BOM HOOKS
// ============================================================================

export const useBOMs = () => {
  return useQuery({
    queryKey: productionKeys.boms(),
    queryFn: async () => {
      const response = await api.get<BillOfMaterials[] | { items: BillOfMaterials[] }>('/production/boms').then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

export const useBOM = (id: string) => {
  return useQuery({
    queryKey: productionKeys.bomDetail(id),
    queryFn: async () => {
      return api.get<BillOfMaterials>(`/production/boms/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreateBOM = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<BillOfMaterials>) => {
      return api.post('/production/boms', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.boms() })
  });
};

export const useUpdateBOM = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<BillOfMaterials> }) => {
      return api.put(`/production/boms/${id}`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.boms() })
  });
};

// ============================================================================
// PRODUCTION ORDER HOOKS
// ============================================================================

export const useProductionOrders = (filters?: { status?: string; priority?: string }) => {
  return useQuery({
    queryKey: productionKeys.ordersList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.priority) params.append('priority', filters.priority);
      const queryString = params.toString();
      const url = queryString ? `/production/orders?${queryString}` : '/production/orders';
      const response = await api.get<ProductionOrder[] | { items: ProductionOrder[] }>(url).then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

export const useProductionOrder = (id: string) => {
  return useQuery({
    queryKey: productionKeys.orderDetail(id),
    queryFn: async () => {
      return api.get<ProductionOrder>(`/production/orders/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreateProductionOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<ProductionOrder>) => {
      return api.post('/production/orders', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.all })
  });
};

export const useUpdateProductionOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<ProductionOrder> }) => {
      return api.put(`/production/orders/${id}`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.all })
  });
};

export const useConfirmOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/production/orders/${id}/confirm`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.all })
  });
};

export const useStartOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/production/orders/${id}/start`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.all })
  });
};

export const useCompleteOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/production/orders/${id}/complete`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.all })
  });
};

export const useCancelOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/production/orders/${id}/cancel`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.all })
  });
};

// ============================================================================
// WORK ORDER HOOKS
// ============================================================================

export const useWorkOrders = (productionOrderId?: string) => {
  return useQuery({
    queryKey: productionKeys.workOrdersList(productionOrderId),
    queryFn: async () => {
      const url = productionOrderId
        ? `/production/work-orders?production_order_id=${encodeURIComponent(productionOrderId)}`
        : '/production/work-orders';
      const response = await api.get<WorkOrder[] | { items: WorkOrder[] }>(url).then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

export const useStartWorkOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/production/work-orders/${id}/start`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.all })
  });
};

export const useCompleteWorkOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, duration }: { id: string; duration?: number }) => {
      return api.post(`/production/work-orders/${id}/complete`, { duration_actual: duration }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: productionKeys.all })
  });
};
