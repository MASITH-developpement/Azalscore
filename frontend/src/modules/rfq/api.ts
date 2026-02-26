/**
 * AZALSCORE - RFQ (Request for Quote) API
 * =========================================
 * Complete typed API client for Request for Quote module.
 * Covers: RFQs, Quotations, Suppliers, Comparison, Award
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const rfqKeys = {
  all: ['rfq'] as const,
  list: () => [...rfqKeys.all, 'list'] as const,
  detail: (id: string) => [...rfqKeys.all, id] as const,
  quotations: (rfqId: string) => [...rfqKeys.detail(rfqId), 'quotations'] as const,
  quotation: (id: string) => [...rfqKeys.all, 'quotation', id] as const,
  comparison: (rfqId: string) => [...rfqKeys.detail(rfqId), 'comparison'] as const,
  suppliers: () => [...rfqKeys.all, 'suppliers'] as const,
  templates: () => [...rfqKeys.all, 'templates'] as const,
  dashboard: () => [...rfqKeys.all, 'dashboard'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type RFQStatus = 'DRAFT' | 'SENT' | 'OPEN' | 'CLOSED' | 'EVALUATING' | 'AWARDED' | 'CANCELLED';
export type QuotationStatus = 'PENDING' | 'RECEIVED' | 'REJECTED' | 'SELECTED' | 'AWARDED';
export type RFQType = 'STANDARD' | 'URGENT' | 'FRAMEWORK' | 'SEALED_BID';
export type AwardCriteria = 'LOWEST_PRICE' | 'BEST_VALUE' | 'WEIGHTED_SCORE' | 'TECHNICAL_EVALUATION';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface RFQLineItem {
  id: string;
  product_id?: number | null;
  product_code?: string | null;
  description: string;
  quantity: number;
  unit: string;
  specifications?: string | null;
  required_date?: string | null;
  is_required: boolean;
}

export interface RFQ {
  id: string;
  tenant_id: string;
  reference: string;
  title: string;
  description?: string | null;
  rfq_type: RFQType;
  status: RFQStatus;

  // Dates
  issue_date: string;
  closing_date: string;
  delivery_date?: string | null;

  // Details
  line_items: RFQLineItem[];
  terms_and_conditions?: string | null;
  payment_terms?: string | null;
  delivery_address?: string | null;

  // Award
  award_criteria: AwardCriteria;
  evaluation_criteria?: Record<string, number> | null;

  // Statistics
  suppliers_invited: number;
  quotations_received: number;

  // Workflow
  sent_at?: string | null;
  closed_at?: string | null;
  awarded_at?: string | null;
  awarded_supplier_id?: string | null;

  created_by?: number | null;
  created_at: string;
  updated_at: string;
}

export interface Quotation {
  id: string;
  tenant_id: string;
  rfq_id: string;
  supplier_id: string;
  supplier_name: string;
  reference?: string | null;
  status: QuotationStatus;

  // Pricing
  line_items: QuotationLineItem[];
  subtotal: number;
  discount_amount: number;
  tax_amount: number;
  total_amount: number;
  currency: string;

  // Terms
  validity_days: number;
  delivery_days?: number | null;
  payment_terms?: string | null;
  notes?: string | null;

  // Evaluation
  technical_score?: number | null;
  price_score?: number | null;
  overall_score?: number | null;
  evaluator_notes?: string | null;

  // Dates
  received_at?: string | null;
  evaluated_at?: string | null;

  created_at: string;
  updated_at: string;
}

export interface QuotationLineItem {
  rfq_line_id: string;
  description: string;
  quantity: number;
  unit: string;
  unit_price: number;
  total_price: number;
  lead_time_days?: number | null;
  notes?: string | null;
}

export interface Supplier {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  contact_name?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  categories: string[];
  rating?: number | null;
  is_approved: boolean;
  is_active: boolean;
  total_rfqs: number;
  total_awarded: number;
  created_at: string;
}

export interface RFQComparison {
  rfq: RFQ;
  quotations: Quotation[];
  comparison_matrix: Array<{
    line_item_id: string;
    description: string;
    quantity: number;
    unit: string;
    prices: Array<{
      supplier_id: string;
      supplier_name: string;
      unit_price: number;
      total_price: number;
      lead_time_days?: number | null;
    }>;
    lowest_price: number;
    average_price: number;
  }>;
  summary: {
    total_quotations: number;
    lowest_total: number;
    highest_total: number;
    average_total: number;
    recommended_supplier_id?: string | null;
    recommendation_reason?: string | null;
  };
}

export interface RFQTemplate {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  rfq_type: RFQType;
  award_criteria: AwardCriteria;
  evaluation_criteria?: Record<string, number> | null;
  terms_and_conditions?: string | null;
  payment_terms?: string | null;
  default_validity_days: number;
  is_active: boolean;
  created_at: string;
}

export interface RFQDashboard {
  total_rfqs: number;
  open_rfqs: number;
  pending_evaluation: number;
  awarded_this_month: number;
  total_quotations_received: number;
  average_response_rate: number;
  average_savings_pct: number;
  recent_rfqs: RFQ[];
  top_suppliers: Array<{
    supplier_id: string;
    supplier_name: string;
    total_awarded: number;
    total_value: number;
  }>;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface RFQCreate {
  title: string;
  description?: string;
  rfq_type?: RFQType;
  closing_date: string;
  delivery_date?: string;
  line_items: Omit<RFQLineItem, 'id'>[];
  terms_and_conditions?: string;
  payment_terms?: string;
  delivery_address?: string;
  award_criteria?: AwardCriteria;
  evaluation_criteria?: Record<string, number>;
  supplier_ids: string[];
}

export interface RFQUpdate {
  title?: string;
  description?: string;
  closing_date?: string;
  delivery_date?: string;
  line_items?: Omit<RFQLineItem, 'id'>[];
  terms_and_conditions?: string;
  payment_terms?: string;
  delivery_address?: string;
  award_criteria?: AwardCriteria;
  evaluation_criteria?: Record<string, number>;
}

export interface QuotationCreate {
  rfq_id: string;
  supplier_id: string;
  reference?: string;
  line_items: Omit<QuotationLineItem, 'rfq_line_id'>[];
  discount_amount?: number;
  currency?: string;
  validity_days?: number;
  delivery_days?: number;
  payment_terms?: string;
  notes?: string;
}

export interface QuotationUpdate {
  line_items?: Omit<QuotationLineItem, 'rfq_line_id'>[];
  discount_amount?: number;
  validity_days?: number;
  delivery_days?: number;
  payment_terms?: string;
  notes?: string;
}

export interface QuotationEvaluation {
  technical_score?: number;
  price_score?: number;
  evaluator_notes?: string;
}

export interface SupplierCreate {
  code: string;
  name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  categories?: string[];
  is_approved?: boolean;
}

export interface SupplierUpdate {
  name?: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  categories?: string[];
  rating?: number;
  is_approved?: boolean;
  is_active?: boolean;
}

export interface RFQTemplateCreate {
  name: string;
  description?: string;
  rfq_type?: RFQType;
  award_criteria?: AwardCriteria;
  evaluation_criteria?: Record<string, number>;
  terms_and_conditions?: string;
  payment_terms?: string;
  default_validity_days?: number;
}

// ============================================================================
// HOOKS - RFQs
// ============================================================================

export function useRFQs(filters?: {
  status?: RFQStatus;
  rfq_type?: RFQType;
  from_date?: string;
  to_date?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...rfqKeys.list(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.rfq_type) params.append('rfq_type', filters.rfq_type);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: RFQ[]; total: number }>(
        `/rfq${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useRFQ(id: string) {
  return useQuery({
    queryKey: rfqKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<RFQ>(`/rfq/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateRFQ() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RFQCreate) => {
      return api.post<RFQ>('/rfq', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.list() });
      queryClient.invalidateQueries({ queryKey: rfqKeys.dashboard() });
    },
  });
}

export function useUpdateRFQ() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: RFQUpdate }) => {
      return api.put<RFQ>(`/rfq/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.list() });
      queryClient.invalidateQueries({ queryKey: rfqKeys.detail(id) });
    },
  });
}

export function useDeleteRFQ() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/rfq/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.list() });
      queryClient.invalidateQueries({ queryKey: rfqKeys.dashboard() });
    },
  });
}

export function useSendRFQ() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<RFQ>(`/rfq/${id}/send`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: rfqKeys.list() });
      queryClient.invalidateQueries({ queryKey: rfqKeys.dashboard() });
    },
  });
}

export function useCloseRFQ() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<RFQ>(`/rfq/${id}/close`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: rfqKeys.list() });
    },
  });
}

export function useCancelRFQ() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      return api.post<RFQ>(`/rfq/${id}/cancel`, { reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: rfqKeys.list() });
      queryClient.invalidateQueries({ queryKey: rfqKeys.dashboard() });
    },
  });
}

export function useExtendRFQ() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, newClosingDate }: { id: string; newClosingDate: string }) => {
      return api.post<RFQ>(`/rfq/${id}/extend`, { closing_date: newClosingDate });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: rfqKeys.list() });
    },
  });
}

export function useAddSuppliersToRFQ() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, supplierIds }: { id: string; supplierIds: string[] }) => {
      return api.post<RFQ>(`/rfq/${id}/suppliers`, { supplier_ids: supplierIds });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.detail(id) });
    },
  });
}

export function useResendToSupplier() {
  return useMutation({
    mutationFn: async ({ rfqId, supplierId }: { rfqId: string; supplierId: string }) => {
      return api.post(`/rfq/${rfqId}/resend/${supplierId}`);
    },
  });
}

// ============================================================================
// HOOKS - QUOTATIONS
// ============================================================================

export function useRFQQuotations(rfqId: string) {
  return useQuery({
    queryKey: rfqKeys.quotations(rfqId),
    queryFn: async () => {
      const response = await api.get<{ items: Quotation[] }>(`/rfq/${rfqId}/quotations`);
      return response;
    },
    enabled: !!rfqId,
  });
}

export function useQuotation(id: string) {
  return useQuery({
    queryKey: rfqKeys.quotation(id),
    queryFn: async () => {
      const response = await api.get<Quotation>(`/rfq/quotations/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateQuotation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: QuotationCreate) => {
      return api.post<Quotation>('/rfq/quotations', data);
    },
    onSuccess: (_, { rfq_id }) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.quotations(rfq_id) });
      queryClient.invalidateQueries({ queryKey: rfqKeys.detail(rfq_id) });
      queryClient.invalidateQueries({ queryKey: rfqKeys.comparison(rfq_id) });
    },
  });
}

export function useUpdateQuotation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: QuotationUpdate }) => {
      return api.put<Quotation>(`/rfq/quotations/${id}`, data);
    },
    onSuccess: (result, { id }) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.quotation(id) });
      if (result.data?.rfq_id) {
        queryClient.invalidateQueries({ queryKey: rfqKeys.quotations(result.data.rfq_id) });
        queryClient.invalidateQueries({ queryKey: rfqKeys.comparison(result.data.rfq_id) });
      }
    },
  });
}

export function useEvaluateQuotation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: QuotationEvaluation }) => {
      return api.post<Quotation>(`/rfq/quotations/${id}/evaluate`, data);
    },
    onSuccess: (result, { id }) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.quotation(id) });
      if (result.data?.rfq_id) {
        queryClient.invalidateQueries({ queryKey: rfqKeys.quotations(result.data.rfq_id) });
        queryClient.invalidateQueries({ queryKey: rfqKeys.comparison(result.data.rfq_id) });
      }
    },
  });
}

export function useSelectQuotation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Quotation>(`/rfq/quotations/${id}/select`);
    },
    onSuccess: (result, id) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.quotation(id) });
      if (result.data?.rfq_id) {
        queryClient.invalidateQueries({ queryKey: rfqKeys.quotations(result.data.rfq_id) });
        queryClient.invalidateQueries({ queryKey: rfqKeys.detail(result.data.rfq_id) });
      }
    },
  });
}

export function useRejectQuotation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      return api.post<Quotation>(`/rfq/quotations/${id}/reject`, { reason });
    },
    onSuccess: (result, { id }) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.quotation(id) });
      if (result.data?.rfq_id) {
        queryClient.invalidateQueries({ queryKey: rfqKeys.quotations(result.data.rfq_id) });
      }
    },
  });
}

// ============================================================================
// HOOKS - COMPARISON & AWARD
// ============================================================================

export function useRFQComparison(rfqId: string) {
  return useQuery({
    queryKey: rfqKeys.comparison(rfqId),
    queryFn: async () => {
      const response = await api.get<RFQComparison>(`/rfq/${rfqId}/comparison`);
      return response;
    },
    enabled: !!rfqId,
  });
}

export function useAwardRFQ() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ rfqId, quotationId, notes }: {
      rfqId: string;
      quotationId: string;
      notes?: string;
    }) => {
      return api.post<RFQ>(`/rfq/${rfqId}/award`, { quotation_id: quotationId, notes });
    },
    onSuccess: (_, { rfqId }) => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.detail(rfqId) });
      queryClient.invalidateQueries({ queryKey: rfqKeys.quotations(rfqId) });
      queryClient.invalidateQueries({ queryKey: rfqKeys.list() });
      queryClient.invalidateQueries({ queryKey: rfqKeys.dashboard() });
    },
  });
}

export function useCreatePurchaseOrderFromRFQ() {
  return useMutation({
    mutationFn: async (rfqId: string) => {
      return api.post<{ purchase_order_id: string }>(`/rfq/${rfqId}/create-po`);
    },
  });
}

// ============================================================================
// HOOKS - SUPPLIERS
// ============================================================================

export function useRFQSuppliers(filters?: {
  categories?: string[];
  is_approved?: boolean;
  is_active?: boolean;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...rfqKeys.suppliers(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.categories?.length) params.append('categories', filters.categories.join(','));
      if (filters?.is_approved !== undefined) params.append('is_approved', String(filters.is_approved));
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Supplier[]; total: number }>(
        `/rfq/suppliers${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCreateRFQSupplier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SupplierCreate) => {
      return api.post<Supplier>('/rfq/suppliers', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.suppliers() });
    },
  });
}

export function useUpdateRFQSupplier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: SupplierUpdate }) => {
      return api.put<Supplier>(`/rfq/suppliers/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.suppliers() });
    },
  });
}

// ============================================================================
// HOOKS - TEMPLATES
// ============================================================================

export function useRFQTemplates() {
  return useQuery({
    queryKey: rfqKeys.templates(),
    queryFn: async () => {
      const response = await api.get<{ items: RFQTemplate[] }>('/rfq/templates');
      return response;
    },
  });
}

export function useCreateRFQTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RFQTemplateCreate) => {
      return api.post<RFQTemplate>('/rfq/templates', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.templates() });
    },
  });
}

export function useCreateRFQFromTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ templateId, data }: { templateId: string; data: Partial<RFQCreate> }) => {
      return api.post<RFQ>(`/rfq/templates/${templateId}/create-rfq`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: rfqKeys.list() });
    },
  });
}

// ============================================================================
// HOOKS - DASHBOARD
// ============================================================================

export function useRFQDashboard() {
  return useQuery({
    queryKey: rfqKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<RFQDashboard>('/rfq/dashboard');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - EXPORT
// ============================================================================

export function useExportRFQReport() {
  return useMutation({
    mutationFn: async ({ rfqId, format }: { rfqId: string; format: 'pdf' | 'excel' }) => {
      return api.post<{ download_url: string; expires_at: string }>(
        `/rfq/${rfqId}/export`,
        { format }
      );
    },
  });
}

export function useExportComparisonReport() {
  return useMutation({
    mutationFn: async ({ rfqId, format }: { rfqId: string; format: 'pdf' | 'excel' }) => {
      return api.post<{ download_url: string; expires_at: string }>(
        `/rfq/${rfqId}/comparison/export`,
        { format }
      );
    },
  });
}
