/**
 * AZALSCORE - Ecommerce React Query Hooks
 * ========================================
 * Hooks pour le module E-commerce
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { Product, Order, Category, Shipping } from './types';

// ============================================================================
// TYPES
// ============================================================================

interface EcommerceStats {
  total_products: number;
  active_products: number;
  pending_orders: number;
  orders_today: number;
  orders_this_month: number;
  revenue_today: number;
  revenue_this_month: number;
  low_stock_count: number;
}

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const ecommerceKeys = {
  all: ['ecommerce'] as const,

  // Stats
  stats: () => [...ecommerceKeys.all, 'stats'] as const,

  // Products
  products: () => [...ecommerceKeys.all, 'products'] as const,
  productsList: (filters?: { status?: string; category_id?: string }) =>
    [...ecommerceKeys.products(), serializeFilters(filters)] as const,
  productDetail: (id: string) => [...ecommerceKeys.all, 'product', id] as const,

  // Orders
  orders: () => [...ecommerceKeys.all, 'orders'] as const,
  ordersList: (filters?: { status?: string; payment_status?: string }) =>
    [...ecommerceKeys.orders(), serializeFilters(filters)] as const,
  orderDetail: (id: string) => [...ecommerceKeys.all, 'order', id] as const,

  // Categories
  categories: () => [...ecommerceKeys.all, 'categories'] as const,

  // Shippings
  shippings: () => [...ecommerceKeys.all, 'shippings'] as const,
  shippingsList: (filters?: { status?: string }) =>
    [...ecommerceKeys.shippings(), serializeFilters(filters)] as const,
};

// ============================================================================
// STATS HOOKS
// ============================================================================

export const useEcommerceStats = () => {
  return useQuery({
    queryKey: ecommerceKeys.stats(),
    queryFn: async () => {
      const response = await api.get<EcommerceStats>('/ecommerce/summary');
      return response.data;
    },
  });
};

// ============================================================================
// PRODUCTS HOOKS
// ============================================================================

export const useProducts = (filters?: { status?: string; category_id?: string }) => {
  return useQuery({
    queryKey: ecommerceKeys.productsList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.category_id) params.append('category_id', filters.category_id);
      const response = await api.get<{ items: Product[] } | Product[]>(`/ecommerce/products?${params}`);
      const data = response.data;
      return Array.isArray(data) ? data : data.items || [];
    },
  });
};

export const useProduct = (id: string) => {
  return useQuery({
    queryKey: ecommerceKeys.productDetail(id),
    queryFn: async () => {
      const response = await api.get<Product>(`/ecommerce/products/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

// ============================================================================
// ORDERS HOOKS
// ============================================================================

export const useOrders = (filters?: { status?: string; payment_status?: string }) => {
  return useQuery({
    queryKey: ecommerceKeys.ordersList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.payment_status) params.append('payment_status', filters.payment_status);
      const response = await api.get<{ items: Order[] } | Order[]>(`/ecommerce/orders?${params}`);
      const data = response.data;
      return Array.isArray(data) ? data : data.items || [];
    },
  });
};

export const useOrder = (id: string) => {
  return useQuery({
    queryKey: ecommerceKeys.orderDetail(id),
    queryFn: async () => {
      const response = await api.get<Order>(`/ecommerce/orders/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useUpdateOrderStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/ecommerce/orders/${id}/status`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ecommerceKeys.orders() });
      queryClient.invalidateQueries({ queryKey: ecommerceKeys.stats() });
    },
  });
};

// ============================================================================
// CATEGORIES HOOKS
// ============================================================================

export const useCategories = () => {
  return useQuery({
    queryKey: ecommerceKeys.categories(),
    queryFn: async () => {
      const response = await api.get<Category[]>('/ecommerce/categories');
      return response.data;
    },
  });
};

// ============================================================================
// SHIPPINGS HOOKS
// ============================================================================

export const useShippings = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: ecommerceKeys.shippingsList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const response = await api.get<Shipping[]>(`/ecommerce/shippings?${params}`);
      return response.data;
    },
  });
};
