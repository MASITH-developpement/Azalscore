/**
 * AZALSCORE - Tenants API
 * =======================
 * Complete typed API client for Tenants Management module.
 * Covers: Tenants, Subscriptions, Modules, Usage, Billing
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const tenantsKeys = {
  all: ['tenants'] as const,
  list: () => [...tenantsKeys.all, 'list'] as const,
  detail: (id: string) => [...tenantsKeys.all, id] as const,
  modules: (id: string) => [...tenantsKeys.all, id, 'modules'] as const,
  usage: (id: string) => [...tenantsKeys.all, id, 'usage'] as const,
  billing: (id: string) => [...tenantsKeys.all, id, 'billing'] as const,
  current: () => [...tenantsKeys.all, 'current'] as const,
  stats: () => [...tenantsKeys.all, 'stats'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type TenantStatus = 'PENDING' | 'ACTIVE' | 'SUSPENDED' | 'CANCELLED' | 'TRIAL';
export type SubscriptionPlan = 'STARTER' | 'PROFESSIONAL' | 'ENTERPRISE' | 'CUSTOM';
export type BillingCycle = 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
export type ModuleStatus = 'ACTIVE' | 'DISABLED' | 'PENDING';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface Tenant {
  id: string;
  tenant_id: string;
  name: string;
  legal_name?: string | null;
  siret?: string | null;
  vat_number?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  city?: string | null;
  postal_code?: string | null;
  country: string;
  email: string;
  phone?: string | null;
  website?: string | null;
  status: TenantStatus;
  plan: SubscriptionPlan;
  billing_cycle: BillingCycle;
  timezone: string;
  language: string;
  currency: string;
  max_users: number;
  current_users: number;
  max_storage_gb: number;
  used_storage_gb: number;
  logo_url?: string | null;
  primary_color: string;
  secondary_color: string;
  features: Record<string, boolean>;
  trial_ends_at?: string | null;
  subscription_ends_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TenantModule {
  id: string;
  tenant_id: string;
  module_code: string;
  module_name: string;
  status: ModuleStatus;
  enabled_at?: string | null;
  disabled_at?: string | null;
  config?: Record<string, unknown> | null;
  usage_limit?: number | null;
  usage_current?: number | null;
}

export interface TenantUsage {
  tenant_id: string;
  period_start: string;
  period_end: string;
  users_count: number;
  storage_used_gb: number;
  api_calls: number;
  documents_created: number;
  emails_sent: number;
  by_module: Record<string, {
    api_calls: number;
    records_created: number;
    storage_used_mb: number;
  }>;
}

export interface TenantBilling {
  tenant_id: string;
  current_plan: SubscriptionPlan;
  billing_cycle: BillingCycle;
  base_price: number;
  additional_users_price: number;
  additional_storage_price: number;
  total_monthly: number;
  next_billing_date: string;
  payment_method?: {
    type: 'card' | 'sepa' | 'invoice';
    last4?: string;
    brand?: string;
  } | null;
  invoices: Array<{
    id: string;
    number: string;
    date: string;
    amount: number;
    status: 'paid' | 'pending' | 'overdue';
    pdf_url?: string;
  }>;
}

export interface TenantStats {
  total_tenants: number;
  active_tenants: number;
  trial_tenants: number;
  suspended_tenants: number;
  by_plan: Record<SubscriptionPlan, number>;
  total_mrr: number;
  total_arr: number;
  churn_rate: number;
  avg_users_per_tenant: number;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface TenantCreate {
  tenant_id: string;
  name: string;
  legal_name?: string;
  siret?: string;
  vat_number?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  email: string;
  phone?: string;
  website?: string;
  plan?: SubscriptionPlan;
  timezone?: string;
  language?: string;
  currency?: string;
  max_users?: number;
  max_storage_gb?: number;
  logo_url?: string;
  primary_color?: string;
  secondary_color?: string;
  features?: Record<string, boolean>;
}

export interface TenantUpdate {
  name?: string;
  legal_name?: string;
  siret?: string;
  vat_number?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  email?: string;
  phone?: string;
  website?: string;
  timezone?: string;
  language?: string;
  currency?: string;
  max_users?: number;
  max_storage_gb?: number;
  logo_url?: string;
  primary_color?: string;
  secondary_color?: string;
  features?: Record<string, boolean>;
}

// ============================================================================
// HOOKS - TENANTS (Admin)
// ============================================================================

export function useTenants(filters?: {
  status?: TenantStatus;
  plan?: SubscriptionPlan;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...tenantsKeys.list(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.plan) params.append('plan', filters.plan);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Tenant[]; total: number }>(
        `/tenants${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useTenant(id: string) {
  return useQuery({
    queryKey: tenantsKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Tenant>(`/tenants/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCurrentTenant() {
  return useQuery({
    queryKey: tenantsKeys.current(),
    queryFn: async () => {
      const response = await api.get<Tenant>('/tenants/current');
      return response;
    },
  });
}

export function useCreateTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TenantCreate) => {
      return api.post<Tenant>('/tenants', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.list() });
      queryClient.invalidateQueries({ queryKey: tenantsKeys.stats() });
    },
  });
}

export function useUpdateTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TenantUpdate }) => {
      return api.put<Tenant>(`/tenants/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.list() });
      queryClient.invalidateQueries({ queryKey: tenantsKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: tenantsKeys.current() });
    },
  });
}

export function useDeleteTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/tenants/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.list() });
      queryClient.invalidateQueries({ queryKey: tenantsKeys.stats() });
    },
  });
}

// ============================================================================
// HOOKS - STATUS TRANSITIONS
// ============================================================================

export function useActivateTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/tenants/${id}/activate`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.list() });
      queryClient.invalidateQueries({ queryKey: tenantsKeys.detail(id) });
    },
  });
}

export function useSuspendTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.post(`/tenants/${id}/suspend`, { reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.list() });
      queryClient.invalidateQueries({ queryKey: tenantsKeys.detail(id) });
    },
  });
}

export function useCancelTenant() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason, feedback }: { id: string; reason: string; feedback?: string }) => {
      return api.post(`/tenants/${id}/cancel`, { reason, feedback });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.list() });
      queryClient.invalidateQueries({ queryKey: tenantsKeys.detail(id) });
    },
  });
}

// ============================================================================
// HOOKS - MODULES
// ============================================================================

export function useTenantModules(tenantId: string) {
  return useQuery({
    queryKey: tenantsKeys.modules(tenantId),
    queryFn: async () => {
      const response = await api.get<{ items: TenantModule[] }>(`/tenants/${tenantId}/modules`);
      return response;
    },
    enabled: !!tenantId,
  });
}

export function useEnableModule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      tenantId,
      moduleCode,
      config,
    }: {
      tenantId: string;
      moduleCode: string;
      config?: Record<string, unknown>;
    }) => {
      return api.post(`/tenants/${tenantId}/modules/${moduleCode}/enable`, { config });
    },
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.modules(tenantId) });
    },
  });
}

export function useDisableModule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ tenantId, moduleCode }: { tenantId: string; moduleCode: string }) => {
      return api.post(`/tenants/${tenantId}/modules/${moduleCode}/disable`);
    },
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.modules(tenantId) });
    },
  });
}

// ============================================================================
// HOOKS - USAGE
// ============================================================================

export function useTenantUsage(tenantId: string, period?: { from?: string; to?: string }) {
  return useQuery({
    queryKey: [...tenantsKeys.usage(tenantId), period],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (period?.from) params.append('from', period.from);
      if (period?.to) params.append('to', period.to);
      const queryString = params.toString();
      const response = await api.get<TenantUsage>(
        `/tenants/${tenantId}/usage${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!tenantId,
  });
}

// ============================================================================
// HOOKS - BILLING
// ============================================================================

export function useTenantBilling(tenantId: string) {
  return useQuery({
    queryKey: tenantsKeys.billing(tenantId),
    queryFn: async () => {
      const response = await api.get<TenantBilling>(`/tenants/${tenantId}/billing`);
      return response;
    },
    enabled: !!tenantId,
  });
}

export function useChangePlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      tenantId,
      plan,
      billingCycle,
    }: {
      tenantId: string;
      plan: SubscriptionPlan;
      billingCycle?: BillingCycle;
    }) => {
      return api.post(`/tenants/${tenantId}/change-plan`, {
        plan,
        billing_cycle: billingCycle,
      });
    },
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.detail(tenantId) });
      queryClient.invalidateQueries({ queryKey: tenantsKeys.billing(tenantId) });
    },
  });
}

export function useUpdatePaymentMethod() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      tenantId,
      paymentMethodId,
    }: {
      tenantId: string;
      paymentMethodId: string;
    }) => {
      return api.post(`/tenants/${tenantId}/payment-method`, {
        payment_method_id: paymentMethodId,
      });
    },
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.billing(tenantId) });
    },
  });
}

// ============================================================================
// HOOKS - STATS (Admin)
// ============================================================================

export function useTenantStats() {
  return useQuery({
    queryKey: tenantsKeys.stats(),
    queryFn: async () => {
      const response = await api.get<TenantStats>('/tenants/stats');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - EXPORT & BACKUP
// ============================================================================

export function useExportTenantData() {
  return useMutation({
    mutationFn: async (tenantId: string) => {
      return api.post<{ job_id: string; estimated_size_mb: number }>(
        `/tenants/${tenantId}/export`
      );
    },
  });
}

export function useImportTenantData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ tenantId, file }: { tenantId: string; file: File }) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post<{ job_id: string }>(`/tenants/${tenantId}/import`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({ queryKey: tenantsKeys.detail(tenantId) });
    },
  });
}
