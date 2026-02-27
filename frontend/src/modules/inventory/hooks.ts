/**
 * AZALSCORE - Inventory Module Hooks
 * ===================================
 * React Query hooks pour le module Inventaire
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { inventoryApi } from './api';
import type {
  Category, Warehouse, Location, Product,
  Movement, InventoryCount, Picking, InventoryDashboard,
  ProductSuggestion
} from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const inventoryKeys = {
  all: ['inventory'] as const,

  // Dashboard
  dashboard: () => [...inventoryKeys.all, 'dashboard'] as const,

  // Categories
  categories: () => [...inventoryKeys.all, 'categories'] as const,

  // Warehouses
  warehouses: () => [...inventoryKeys.all, 'warehouses'] as const,

  // Locations
  locations: () => [...inventoryKeys.all, 'locations'] as const,
  locationsByWarehouse: (warehouseId?: string) =>
    [...inventoryKeys.locations(), warehouseId] as const,

  // Products
  products: () => [...inventoryKeys.all, 'products'] as const,
  productDetail: (id: string) => [...inventoryKeys.products(), id] as const,
  productSearch: (query: string, categoryId?: string) =>
    [...inventoryKeys.products(), 'search', query, categoryId] as const,

  // Movements
  movements: () => [...inventoryKeys.all, 'movements'] as const,

  // Pickings
  pickings: () => [...inventoryKeys.all, 'pickings'] as const,

  // Inventory counts
  counts: () => [...inventoryKeys.all, 'counts'] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export const useInventoryDashboard = () => {
  return useQuery({
    queryKey: inventoryKeys.dashboard(),
    queryFn: async () => {
      return api.get<InventoryDashboard>('/inventory/dashboard').then(r => r.data);
    }
  });
};

// ============================================================================
// CATEGORY HOOKS
// ============================================================================

export const useCategories = () => {
  return useQuery({
    queryKey: inventoryKeys.categories(),
    queryFn: async () => {
      const response = await api.get<{ items: Category[] }>('/inventory/categories').then(r => r.data);
      return response?.items || [];
    }
  });
};

// ============================================================================
// WAREHOUSE HOOKS
// ============================================================================

export const useWarehouses = () => {
  return useQuery({
    queryKey: inventoryKeys.warehouses(),
    queryFn: async () => {
      const response = await api.get<{ items: Warehouse[] }>('/inventory/warehouses').then(r => r.data);
      return response?.items || [];
    }
  });
};

// ============================================================================
// LOCATION HOOKS
// ============================================================================

export const useLocations = (warehouseId?: string) => {
  return useQuery({
    queryKey: inventoryKeys.locationsByWarehouse(warehouseId),
    queryFn: async () => {
      const url = warehouseId
        ? `/inventory/locations?warehouse_id=${encodeURIComponent(warehouseId)}`
        : '/inventory/locations';
      const response = await api.get<{ items: Location[] }>(url).then(r => r.data);
      return response?.items || [];
    }
  });
};

// ============================================================================
// PRODUCT HOOKS
// ============================================================================

export const useProducts = () => {
  return useQuery({
    queryKey: inventoryKeys.products(),
    queryFn: async () => {
      const response = await api.get<{ items: Product[] }>('/inventory/products').then(r => r.data);
      return response?.items || [];
    }
  });
};

export const useProduct = (id: string) => {
  return useQuery({
    queryKey: inventoryKeys.productDetail(id),
    queryFn: async () => {
      return api.get<Product>(`/inventory/products/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export function useProductSearch(
  query: string,
  limit = 10,
  categoryId?: string,
  enabled = true
) {
  return useQuery<ProductSuggestion[]>({
    queryKey: inventoryKeys.productSearch(query, categoryId),
    queryFn: () => inventoryApi.searchProducts(query, limit, categoryId),
    enabled: enabled && query.length >= 2,
    staleTime: 30 * 1000,
  });
}

export const useCreateProduct = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Product>) => {
      return api.post('/inventory/products', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: inventoryKeys.products() })
  });
};

export const useUpdateProduct = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Product> }) => {
      return api.put(`/inventory/products/${id}`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: inventoryKeys.products() })
  });
};

// ============================================================================
// MOVEMENT HOOKS
// ============================================================================

export const useMovements = () => {
  return useQuery({
    queryKey: inventoryKeys.movements(),
    queryFn: async () => {
      const response = await api.get<{ items: Movement[] }>('/inventory/movements').then(r => r.data);
      return response?.items || [];
    }
  });
};

export const useCreateMovement = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Movement>) => {
      return api.post('/inventory/movements', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: inventoryKeys.all })
  });
};

export const useValidateMovement = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/inventory/movements/${id}/validate`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: inventoryKeys.all })
  });
};

// ============================================================================
// PICKING HOOKS
// ============================================================================

export const usePickings = () => {
  return useQuery({
    queryKey: inventoryKeys.pickings(),
    queryFn: async () => {
      const response = await api.get<{ items: Picking[] }>('/inventory/pickings').then(r => r.data);
      return response?.items || [];
    }
  });
};

// ============================================================================
// INVENTORY COUNT HOOKS
// ============================================================================

export const useInventoryCounts = () => {
  return useQuery({
    queryKey: inventoryKeys.counts(),
    queryFn: async () => {
      const response = await api.get<{ items: InventoryCount[] }>('/inventory/counts').then(r => r.data);
      return response?.items || [];
    }
  });
};

export const useCreateInventoryCount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<InventoryCount>) => {
      return api.post('/inventory/counts', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: inventoryKeys.counts() })
  });
};
