/**
 * AZALSCORE - Marketplace React Query Hooks
 * ==========================================
 * Hooks pour le module Marketplace (vendeurs, produits, commandes)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { Seller, MarketplaceProduct, MarketplaceOrder, Payout, MarketplaceStats } from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const marketplaceKeys = {
  all: ['marketplace'] as const,

  // Stats
  stats: () => [...marketplaceKeys.all, 'stats'] as const,

  // Sellers
  sellers: () => [...marketplaceKeys.all, 'sellers'] as const,
  sellersList: (filters?: { status?: string }) =>
    [...marketplaceKeys.sellers(), serializeFilters(filters)] as const,
  sellerDetail: (id: string) => [...marketplaceKeys.sellers(), id] as const,

  // Products
  products: () => [...marketplaceKeys.all, 'products'] as const,
  productsList: (filters?: { status?: string; seller_id?: string }) =>
    [...marketplaceKeys.products(), serializeFilters(filters)] as const,

  // Orders
  orders: () => [...marketplaceKeys.all, 'orders'] as const,
  ordersList: (filters?: { status?: string; seller_id?: string }) =>
    [...marketplaceKeys.orders(), serializeFilters(filters)] as const,

  // Payouts
  payouts: () => [...marketplaceKeys.all, 'payouts'] as const,
  payoutsList: (filters?: { status?: string; seller_id?: string }) =>
    [...marketplaceKeys.payouts(), serializeFilters(filters)] as const,
};

// ============================================================================
// STATS HOOKS
// ============================================================================

export const useMarketplaceStats = () => {
  return useQuery({
    queryKey: marketplaceKeys.stats(),
    queryFn: async () => {
      return api.get<MarketplaceStats>('/marketplace/stats').then(r => r.data);
    },
  });
};

// ============================================================================
// SELLER HOOKS
// ============================================================================

export const useSellers = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: marketplaceKeys.sellersList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/marketplace/sellers?${queryString}` : '/marketplace/sellers';
      return api.get<Seller[]>(url).then(r => r.data);
    },
  });
};

export const useSeller = (id: string) => {
  return useQuery({
    queryKey: marketplaceKeys.sellerDetail(id),
    queryFn: async () => {
      return api.get<Seller>(`/marketplace/sellers/${id}`).then(r => r.data);
    },
    enabled: !!id,
  });
};

export const useUpdateSellerStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/marketplace/sellers/${id}/status`, { status }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.sellers() });
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.stats() });
    },
  });
};

// ============================================================================
// PRODUCT HOOKS
// ============================================================================

export const useMarketplaceProducts = (filters?: { status?: string; seller_id?: string }) => {
  return useQuery({
    queryKey: marketplaceKeys.productsList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.seller_id) params.append('seller_id', filters.seller_id);
      const queryString = params.toString();
      const url = queryString ? `/marketplace/products?${queryString}` : '/marketplace/products';
      return api.get<MarketplaceProduct[]>(url).then(r => r.data);
    },
  });
};

export const useApproveProduct = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, approved }: { id: string; approved: boolean }) => {
      return api.patch(`/marketplace/products/${id}/review`, { approved }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.products() });
      queryClient.invalidateQueries({ queryKey: marketplaceKeys.stats() });
    },
  });
};

// ============================================================================
// ORDER HOOKS
// ============================================================================

export const useMarketplaceOrders = (filters?: { status?: string; seller_id?: string }) => {
  return useQuery({
    queryKey: marketplaceKeys.ordersList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.seller_id) params.append('seller_id', filters.seller_id);
      const queryString = params.toString();
      const url = queryString ? `/marketplace/orders?${queryString}` : '/marketplace/orders';
      return api.get<MarketplaceOrder[]>(url).then(r => r.data);
    },
  });
};

// ============================================================================
// PAYOUT HOOKS
// ============================================================================

export const usePayouts = (filters?: { status?: string; seller_id?: string }) => {
  return useQuery({
    queryKey: marketplaceKeys.payoutsList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.seller_id) params.append('seller_id', filters.seller_id);
      const queryString = params.toString();
      const url = queryString ? `/marketplace/payouts?${queryString}` : '/marketplace/payouts';
      return api.get<Payout[]>(url).then(r => r.data);
    },
  });
};
