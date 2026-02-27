/**
 * AZALSCORE Module - Maintenance - React Query Hooks
 * Hooks pour la gestion de la maintenance et des equipements
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { Asset, MaintenanceOrder, MaintenancePlan, MaintenanceDashboard } from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const maintenanceKeys = {
  all: ['maintenance'] as const,

  // Dashboard
  dashboard: () => [...maintenanceKeys.all, 'dashboard'] as const,

  // Assets
  assets: () => [...maintenanceKeys.all, 'assets'] as const,
  assetsList: (filters?: { type?: string; status?: string; criticality?: string }) =>
    [...maintenanceKeys.assets(), serializeFilters(filters)] as const,
  assetDetail: (id: string) => [...maintenanceKeys.all, 'asset', id] as const,

  // Orders
  orders: () => [...maintenanceKeys.all, 'orders'] as const,
  ordersList: (filters?: { type?: string; status?: string; priority?: string }) =>
    [...maintenanceKeys.orders(), serializeFilters(filters)] as const,
  orderDetail: (id: string) => [...maintenanceKeys.orders(), id] as const,

  // Plans
  plans: () => [...maintenanceKeys.all, 'plans'] as const,
  planDetail: (id: string) => [...maintenanceKeys.plans(), id] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export const useMaintenanceDashboard = () => {
  return useQuery({
    queryKey: maintenanceKeys.dashboard(),
    queryFn: async () => {
      return api.get<MaintenanceDashboard>('/maintenance/dashboard').then(r => r.data);
    }
  });
};

// ============================================================================
// ASSET HOOKS
// ============================================================================

export const useAssets = (filters?: { type?: string; status?: string; criticality?: string }) => {
  return useQuery({
    queryKey: maintenanceKeys.assetsList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.criticality) params.append('criticality', filters.criticality);
      const queryString = params.toString();
      const url = `/maintenance/assets${queryString ? `?${queryString}` : ''}`;
      return api.get<Asset[]>(url).then(r => r.data);
    }
  });
};

export const useAsset = (id: string) => {
  return useQuery({
    queryKey: maintenanceKeys.assetDetail(id),
    queryFn: async () => {
      return api.get<Asset>(`/maintenance/assets/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreateAsset = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Asset>) => {
      return api.post('/maintenance/assets', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.assets() })
  });
};

export const useUpdateAsset = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Asset> }) => {
      return api.put(`/maintenance/assets/${id}`, data).then(r => r.data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: maintenanceKeys.assets() });
      queryClient.invalidateQueries({ queryKey: maintenanceKeys.assetDetail(id) });
    }
  });
};

export const useDeleteAsset = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/maintenance/assets/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.assets() })
  });
};

// ============================================================================
// MAINTENANCE ORDER HOOKS
// ============================================================================

export const useMaintenanceOrders = (filters?: { type?: string; status?: string; priority?: string }) => {
  return useQuery({
    queryKey: maintenanceKeys.ordersList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.priority) params.append('priority', filters.priority);
      const queryString = params.toString();
      const url = `/maintenance/orders${queryString ? `?${queryString}` : ''}`;
      return api.get<MaintenanceOrder[]>(url).then(r => r.data);
    }
  });
};

export const useMaintenanceOrder = (id: string) => {
  return useQuery({
    queryKey: maintenanceKeys.orderDetail(id),
    queryFn: async () => {
      return api.get<MaintenanceOrder>(`/maintenance/orders/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreateMaintenanceOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<MaintenanceOrder>) => {
      return api.post('/maintenance/orders', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.all })
  });
};

export const useUpdateMaintenanceOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<MaintenanceOrder> }) => {
      return api.put(`/maintenance/orders/${id}`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.all })
  });
};

export const useUpdateOrderStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/maintenance/orders/${id}`, { status }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.all })
  });
};

export const useCompleteMaintenanceOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, resolution }: { id: string; resolution?: string }) => {
      return api.post(`/maintenance/orders/${id}/complete`, { resolution }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.all })
  });
};

export const useCancelMaintenanceOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      return api.post(`/maintenance/orders/${id}/cancel`, { reason }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.all })
  });
};

// ============================================================================
// MAINTENANCE PLAN HOOKS
// ============================================================================

export const useMaintenancePlans = () => {
  return useQuery({
    queryKey: maintenanceKeys.plans(),
    queryFn: async () => {
      return api.get<MaintenancePlan[]>('/maintenance/plans').then(r => r.data);
    }
  });
};

export const useMaintenancePlan = (id: string) => {
  return useQuery({
    queryKey: maintenanceKeys.planDetail(id),
    queryFn: async () => {
      return api.get<MaintenancePlan>(`/maintenance/plans/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreateMaintenancePlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<MaintenancePlan>) => {
      return api.post('/maintenance/plans', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.plans() })
  });
};

export const useUpdateMaintenancePlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<MaintenancePlan> }) => {
      return api.put(`/maintenance/plans/${id}`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.plans() })
  });
};

export const useTogglePlanActive = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, isActive }: { id: string; isActive: boolean }) => {
      return api.patch(`/maintenance/plans/${id}`, { is_active: isActive }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.plans() })
  });
};

export const useExecutePlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (planId: string) => {
      return api.post(`/maintenance/plans/${planId}/execute`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: maintenanceKeys.all })
  });
};
