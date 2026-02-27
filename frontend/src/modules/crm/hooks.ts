/**
 * AZALSCORE Module - CRM - React Query Hooks
 * Hooks pour la gestion de la relation client
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { serializeFilters } from '@core/query-keys';
import { crmApi } from './api';
import type { Customer, Opportunity, PipelineStats, SalesDashboard, CustomerStats } from './types';
import type { CustomerFilters, OpportunityFilters, CustomerCreate, OpportunityCreate } from './api';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const crmKeys = {
  all: ['commercial'] as const,

  // Dashboard
  dashboard: () => [...crmKeys.all, 'dashboard'] as const,
  pipeline: () => [...crmKeys.all, 'pipeline', 'stats'] as const,

  // Customers
  customers: () => [...crmKeys.all, 'customers'] as const,
  customersList: (page: number, pageSize: number, filters?: Partial<CustomerFilters>) =>
    [...crmKeys.customers(), page, pageSize, serializeFilters(filters)] as const,
  customerDetail: (id: string) => [...crmKeys.customers(), id] as const,
  customerStats: (id: string) => [...crmKeys.customers(), id, 'stats'] as const,

  // Opportunities
  opportunities: () => [...crmKeys.all, 'opportunities'] as const,
  opportunitiesList: (page: number, pageSize: number, filters?: Partial<OpportunityFilters>) =>
    [...crmKeys.opportunities(), page, pageSize, serializeFilters(filters)] as const,
  opportunityDetail: (id: string) => [...crmKeys.opportunities(), id] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export const useSalesDashboard = () => {
  return useQuery({
    queryKey: crmKeys.dashboard(),
    queryFn: async () => {
      const response = await crmApi.getDashboard();
      return response.data as SalesDashboard;
    },
  });
};

export const usePipelineStats = () => {
  return useQuery({
    queryKey: crmKeys.pipeline(),
    queryFn: async () => {
      const response = await crmApi.getPipelineStats();
      return response.data as PipelineStats;
    },
  });
};

// ============================================================================
// CUSTOMER HOOKS
// ============================================================================

export const useCustomers = (
  page = 1,
  pageSize = 25,
  filters?: Partial<CustomerFilters>
) => {
  return useQuery({
    queryKey: crmKeys.customersList(page, pageSize, filters),
    queryFn: async () => {
      const response = await crmApi.listCustomers({
        page,
        page_size: pageSize,
        ...filters,
      } as CustomerFilters);
      return response.data;
    },
  });
};

export const useCustomer = (id: string) => {
  return useQuery({
    queryKey: crmKeys.customerDetail(id),
    queryFn: async () => {
      const response = await crmApi.getCustomer(id);
      return response.data as Customer;
    },
    enabled: !!id,
  });
};

export const useCustomerStats = (customerId: string) => {
  return useQuery({
    queryKey: crmKeys.customerStats(customerId),
    queryFn: async () => {
      const response = await crmApi.getCustomerStats(customerId);
      return response.data as CustomerStats;
    },
    enabled: !!customerId,
  });
};

export const useCreateCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CustomerCreate) => {
      const response = await crmApi.createCustomer(data);
      return response.data as Customer;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: crmKeys.customers() });
    },
  });
};

export const useUpdateCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<CustomerCreate> }) => {
      const response = await crmApi.updateCustomer(id, data);
      return response.data as Customer;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: crmKeys.customers() });
      queryClient.invalidateQueries({ queryKey: crmKeys.customerDetail(id) });
    },
  });
};

export const useDeleteCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await crmApi.deleteCustomer(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: crmKeys.customers() });
    },
  });
};

export const useConvertProspect = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (customerId: string) => {
      const response = await crmApi.convertProspect(customerId);
      return response.data as Customer;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: crmKeys.customers() });
    },
  });
};

// ============================================================================
// OPPORTUNITY HOOKS
// ============================================================================

export const useOpportunities = (
  page = 1,
  pageSize = 25,
  filters?: Partial<OpportunityFilters>
) => {
  return useQuery({
    queryKey: crmKeys.opportunitiesList(page, pageSize, filters),
    queryFn: async () => {
      const response = await crmApi.listOpportunities({
        page,
        page_size: pageSize,
        ...filters,
      } as OpportunityFilters);
      return response.data;
    },
  });
};

export const useOpportunity = (id: string) => {
  return useQuery({
    queryKey: crmKeys.opportunityDetail(id),
    queryFn: async () => {
      const response = await crmApi.getOpportunity(id);
      return response.data as Opportunity;
    },
    enabled: !!id,
  });
};

export const useCreateOpportunity = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OpportunityCreate) => {
      const response = await crmApi.createOpportunity(data);
      return response.data as Opportunity;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: crmKeys.opportunities() });
    },
  });
};

export const useUpdateOpportunity = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<OpportunityCreate> }) => {
      const response = await crmApi.updateOpportunity(id, data);
      return response.data as Opportunity;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: crmKeys.opportunities() });
      queryClient.invalidateQueries({ queryKey: crmKeys.opportunityDetail(id) });
    },
  });
};

export const useWinOpportunity = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, winReason }: { id: string; winReason?: string }) => {
      const response = await crmApi.winOpportunity(id, winReason);
      return response.data as Opportunity;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: crmKeys.opportunities() });
      queryClient.invalidateQueries({ queryKey: crmKeys.pipeline() });
    },
  });
};

export const useLoseOpportunity = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, lossReason }: { id: string; lossReason?: string }) => {
      const response = await crmApi.loseOpportunity(id, lossReason);
      return response.data as Opportunity;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: crmKeys.opportunities() });
      queryClient.invalidateQueries({ queryKey: crmKeys.pipeline() });
    },
  });
};

export const useCreateQuoteFromOpportunity = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (opportunityId: string) => {
      const response = await crmApi.createQuoteFromOpportunity(opportunityId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: crmKeys.opportunities() });
    },
  });
};
