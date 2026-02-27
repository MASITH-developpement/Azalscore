/**
 * AZALSCORE - Subscriptions React Query Hooks
 * ============================================
 * Hooks pour le module Abonnements / SaaS
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { serializeFilters } from '@core/query-keys';
import { subscriptionsApi } from './api';
import type { SubscriptionStatus } from './api';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const subscriptionsKeys = {
  all: ['subscriptions'] as const,

  // Stats
  stats: () => [...subscriptionsKeys.all, 'stats'] as const,
  dashboard: () => [...subscriptionsKeys.all, 'dashboard'] as const,

  // Plans
  plans: () => [...subscriptionsKeys.all, 'plans'] as const,
  plansList: (filters?: { is_active?: boolean }) =>
    [...subscriptionsKeys.plans(), serializeFilters(filters)] as const,
  planDetail: (id: number) => [...subscriptionsKeys.plans(), id] as const,

  // Subscriptions
  subscriptions: () => [...subscriptionsKeys.all, 'list'] as const,
  subscriptionsList: (filters?: { status?: string; plan_id?: string }) =>
    [...subscriptionsKeys.subscriptions(), serializeFilters(filters)] as const,
  subscriptionDetail: (id: string) => [...subscriptionsKeys.all, 'detail', id] as const,

  // Invoices
  invoices: () => [...subscriptionsKeys.all, 'invoices'] as const,
  invoicesList: (filters?: { status?: string }) =>
    [...subscriptionsKeys.invoices(), serializeFilters(filters)] as const,
  invoiceDetail: (id: number) => [...subscriptionsKeys.invoices(), id] as const,

  // Metrics
  metrics: () => [...subscriptionsKeys.all, 'metrics'] as const,
  metricsTrend: (startDate: string, endDate: string) =>
    [...subscriptionsKeys.metrics(), 'trend', startDate, endDate] as const,

  // Coupons
  coupons: () => [...subscriptionsKeys.all, 'coupons'] as const,
  couponsList: (filters?: { is_active?: boolean }) =>
    [...subscriptionsKeys.coupons(), serializeFilters(filters)] as const,
};

// ============================================================================
// STATS HOOKS
// ============================================================================

export const useSubscriptionStats = () => {
  return useQuery({
    queryKey: subscriptionsKeys.stats(),
    queryFn: async () => {
      const response = await subscriptionsApi.getStats();
      return response.data;
    },
  });
};

export const useSubscriptionDashboard = () => {
  return useQuery({
    queryKey: subscriptionsKeys.dashboard(),
    queryFn: async () => {
      const response = await subscriptionsApi.getDashboard();
      return response.data;
    },
  });
};

// ============================================================================
// PLANS HOOKS
// ============================================================================

export const usePlans = (filters?: { is_active?: boolean }) => {
  return useQuery({
    queryKey: subscriptionsKeys.plansList(filters),
    queryFn: async () => {
      const response = await subscriptionsApi.listPlans(filters);
      return response.data?.items || [];
    },
  });
};

export const usePlan = (planId: number) => {
  return useQuery({
    queryKey: subscriptionsKeys.planDetail(planId),
    queryFn: async () => {
      const response = await subscriptionsApi.getPlan(planId);
      return response.data;
    },
    enabled: !!planId,
  });
};

// ============================================================================
// SUBSCRIPTIONS HOOKS
// ============================================================================

export const useSubscriptions = (filters?: { status?: string; plan_id?: string }) => {
  return useQuery({
    queryKey: subscriptionsKeys.subscriptionsList(filters),
    queryFn: async () => {
      const params: Parameters<typeof subscriptionsApi.listSubscriptions>[0] = {};
      if (filters?.status) params.status = filters.status as SubscriptionStatus;
      if (filters?.plan_id) params.plan_id = Number(filters.plan_id);
      const response = await subscriptionsApi.listSubscriptions(params);
      return response.data?.items || [];
    },
  });
};

export const useSubscription = (id: string) => {
  return useQuery({
    queryKey: subscriptionsKeys.subscriptionDetail(id),
    queryFn: async () => {
      const response = await subscriptionsApi.getSubscription(Number(id));
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCancelSubscription = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, immediately }: { id: string; immediately?: boolean }) => {
      const response = await subscriptionsApi.cancelSubscription(Number(id), {
        cancel_at_period_end: !immediately,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: subscriptionsKeys.all });
    },
  });
};

export const useChangeSubscriptionPlan = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      subscriptionId,
      newPlanId,
      quantity,
    }: {
      subscriptionId: number;
      newPlanId: number;
      quantity?: number;
    }) => {
      const response = await subscriptionsApi.changeSubscriptionPlan(subscriptionId, {
        new_plan_id: newPlanId,
        new_quantity: quantity,
        prorate: true,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: subscriptionsKeys.all });
    },
  });
};

// ============================================================================
// INVOICES HOOKS
// ============================================================================

export const useInvoices = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: subscriptionsKeys.invoicesList(filters),
    queryFn: async () => {
      const params: Parameters<typeof subscriptionsApi.listInvoices>[0] = {};
      if (filters?.status) params.status = filters.status as any;
      const response = await subscriptionsApi.listInvoices(params);
      return response.data?.items || [];
    },
  });
};

export const useInvoice = (invoiceId: number) => {
  return useQuery({
    queryKey: subscriptionsKeys.invoiceDetail(invoiceId),
    queryFn: async () => {
      const response = await subscriptionsApi.getInvoice(invoiceId);
      return response.data;
    },
    enabled: !!invoiceId,
  });
};

export const useFinalizeInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (invoiceId: number) => {
      const response = await subscriptionsApi.finalizeInvoice(invoiceId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: subscriptionsKeys.invoices() });
    },
  });
};

// ============================================================================
// METRICS HOOKS
// ============================================================================

export const useMetricsTrend = (startDate: string, endDate: string) => {
  return useQuery({
    queryKey: subscriptionsKeys.metricsTrend(startDate, endDate),
    queryFn: async () => {
      const response = await subscriptionsApi.getMetricsTrend(startDate, endDate);
      return response.data;
    },
    enabled: !!startDate && !!endDate,
  });
};

// ============================================================================
// COUPONS HOOKS
// ============================================================================

export const useCoupons = (filters?: { is_active?: boolean }) => {
  return useQuery({
    queryKey: subscriptionsKeys.couponsList(filters),
    queryFn: async () => {
      const response = await subscriptionsApi.listCoupons(filters);
      return response.data;
    },
  });
};

export const useValidateCoupon = () => {
  return useMutation({
    mutationFn: async (data: {
      code: string;
      plan_id?: number;
      customer_id?: number;
      amount?: string;
    }) => {
      const response = await subscriptionsApi.validateCoupon(data);
      return response.data;
    },
  });
};
