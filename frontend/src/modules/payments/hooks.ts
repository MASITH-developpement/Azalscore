/**
 * AZALSCORE - Payments React Query Hooks
 * =======================================
 * Hooks pour le module Paiements
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { serializeFilters } from '@core/query-keys';
import { paymentsApi, type RefundCreate } from './api';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const paymentsKeys = {
  all: ['payments'] as const,

  // Stats
  stats: () => [...paymentsKeys.all, 'stats'] as const,

  // Payments
  payments: () => [...paymentsKeys.all, 'list'] as const,
  paymentsList: (filters?: { status?: string; method?: string; date_from?: string; date_to?: string }) =>
    [...paymentsKeys.payments(), serializeFilters(filters)] as const,
  paymentDetail: (id: string) => [...paymentsKeys.all, 'detail', id] as const,

  // Refunds
  refunds: () => [...paymentsKeys.all, 'refunds'] as const,
  refundsList: (filters?: { status?: string }) =>
    [...paymentsKeys.refunds(), serializeFilters(filters)] as const,

  // Payment Methods
  methods: () => [...paymentsKeys.all, 'methods'] as const,
  methodsList: (filters?: { customer_id?: string }) =>
    [...paymentsKeys.methods(), serializeFilters(filters)] as const,
};

// ============================================================================
// STATS HOOKS
// ============================================================================

export const usePaymentStats = () => {
  return useQuery({
    queryKey: paymentsKeys.stats(),
    queryFn: async () => {
      const response = await paymentsApi.getSummary();
      return response.data;
    },
  });
};

// ============================================================================
// PAYMENT HOOKS
// ============================================================================

export const usePayments = (filters?: { status?: string; method?: string; date_from?: string; date_to?: string }) => {
  return useQuery({
    queryKey: paymentsKeys.paymentsList(filters),
    queryFn: async () => {
      const response = await paymentsApi.listPayments(filters as Parameters<typeof paymentsApi.listPayments>[0]);
      return response.data?.items || [];
    },
  });
};

export const usePayment = (id: string) => {
  return useQuery({
    queryKey: paymentsKeys.paymentDetail(id),
    queryFn: async () => {
      const response = await paymentsApi.getPayment(id);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useRetryPayment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (paymentId: string) => {
      const response = await paymentsApi.retryPayment(paymentId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: paymentsKeys.all });
    },
  });
};

// ============================================================================
// REFUND HOOKS
// ============================================================================

export const useRefunds = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: paymentsKeys.refundsList(filters),
    queryFn: async () => {
      const response = await paymentsApi.listRefunds(filters as Parameters<typeof paymentsApi.listRefunds>[0]);
      return response.data;
    },
  });
};

export const useCreateRefund = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RefundCreate) => {
      const response = await paymentsApi.createRefund(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: paymentsKeys.all });
    },
  });
};

// ============================================================================
// PAYMENT METHODS HOOKS
// ============================================================================

export const usePaymentMethods = (filters?: { customer_id?: string }) => {
  return useQuery({
    queryKey: paymentsKeys.methodsList(filters),
    queryFn: async () => {
      const response = await paymentsApi.listPaymentMethods(filters);
      return response.data;
    },
  });
};
