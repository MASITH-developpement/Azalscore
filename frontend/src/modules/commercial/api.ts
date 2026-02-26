/**
 * AZALSCORE - Commercial API
 * ==========================
 * Complete typed API client for Commercial/CRM module.
 * Covers: Customers, Contacts, Opportunities, Documents, Products, Pipeline
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const commercialKeys = {
  all: ['commercial'] as const,
  // Customers
  customers: () => [...commercialKeys.all, 'customers'] as const,
  customer: (id: string) => [...commercialKeys.customers(), id] as const,
  // Contacts
  contacts: () => [...commercialKeys.all, 'contacts'] as const,
  contact: (id: string) => [...commercialKeys.contacts(), id] as const,
  // Opportunities
  opportunities: () => [...commercialKeys.all, 'opportunities'] as const,
  opportunity: (id: string) => [...commercialKeys.opportunities(), id] as const,
  // Documents (Quotes, Invoices, Credit Notes)
  documents: () => [...commercialKeys.all, 'documents'] as const,
  document: (id: string) => [...commercialKeys.documents(), id] as const,
  quotes: () => [...commercialKeys.documents(), 'quotes'] as const,
  invoices: () => [...commercialKeys.documents(), 'invoices'] as const,
  // Products
  products: () => [...commercialKeys.all, 'products'] as const,
  product: (id: string) => [...commercialKeys.products(), id] as const,
  // Pipeline
  pipeline: () => [...commercialKeys.all, 'pipeline'] as const,
  // Dashboard
  dashboard: () => [...commercialKeys.all, 'dashboard'] as const,
};

// ============================================================================
// TYPES - CUSTOMERS
// ============================================================================

export type CustomerType = 'PROSPECT' | 'CLIENT' | 'ANCIEN_CLIENT' | 'FOURNISSEUR';

export interface Customer {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  type: CustomerType;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  postal_code?: string | null;
  country?: string | null;
  siret?: string | null;
  vat_number?: string | null;
  payment_terms?: number | null;
  credit_limit?: number | null;
  assigned_to?: string | null;
  tags?: string[] | null;
  notes?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreate {
  code: string;
  name: string;
  type?: CustomerType;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  postal_code?: string | null;
  country?: string | null;
  siret?: string | null;
  vat_number?: string | null;
  payment_terms?: number | null;
  assigned_to?: string | null;
  tags?: string[] | null;
  notes?: string | null;
}

export interface CustomerUpdate {
  name?: string | null;
  type?: CustomerType | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  city?: string | null;
  postal_code?: string | null;
  country?: string | null;
  payment_terms?: number | null;
  credit_limit?: number | null;
  is_active?: boolean | null;
  tags?: string[] | null;
  notes?: string | null;
}

export interface CustomerList {
  total: number;
  page: number;
  per_page: number;
  items: Customer[];
}

// ============================================================================
// TYPES - CONTACTS
// ============================================================================

export interface Contact {
  id: string;
  tenant_id: string;
  customer_id?: string | null;
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  job_title?: string | null;
  is_primary: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ContactCreate {
  customer_id?: string | null;
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  job_title?: string | null;
  is_primary?: boolean;
}

export interface ContactUpdate {
  first_name?: string | null;
  last_name?: string | null;
  email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  job_title?: string | null;
  is_primary?: boolean | null;
  is_active?: boolean | null;
}

// ============================================================================
// TYPES - OPPORTUNITIES
// ============================================================================

export type OpportunityStatus = 'NEW' | 'QUALIFIED' | 'PROPOSAL' | 'NEGOTIATION' | 'WON' | 'LOST';

export interface Opportunity {
  id: string;
  tenant_id: string;
  name: string;
  customer_id: string;
  customer_name?: string;
  contact_id?: string | null;
  status: OpportunityStatus;
  stage_id?: string | null;
  amount: number;
  probability: number;
  expected_close_date?: string | null;
  assigned_to?: string | null;
  source?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OpportunityCreate {
  name: string;
  customer_id: string;
  contact_id?: string | null;
  status?: OpportunityStatus;
  stage_id?: string | null;
  amount: number;
  probability?: number;
  expected_close_date?: string | null;
  assigned_to?: string | null;
  source?: string | null;
  notes?: string | null;
}

export interface OpportunityUpdate {
  name?: string | null;
  status?: OpportunityStatus | null;
  stage_id?: string | null;
  amount?: number | null;
  probability?: number | null;
  expected_close_date?: string | null;
  assigned_to?: string | null;
  notes?: string | null;
}

export interface OpportunityList {
  total: number;
  page: number;
  per_page: number;
  items: Opportunity[];
}

// ============================================================================
// TYPES - DOCUMENTS (Quotes, Invoices, Credit Notes)
// ============================================================================

export type DocumentType = 'QUOTE' | 'ORDER' | 'DELIVERY' | 'INVOICE' | 'CREDIT_NOTE';
export type DocumentStatus = 'DRAFT' | 'SENT' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED' | 'PAID';

export interface DocumentLine {
  id: string;
  document_id: string;
  product_id?: string | null;
  description: string;
  quantity: number;
  unit_price: number;
  discount_percent?: number | null;
  tax_rate: number;
  line_total: number;
  position: number;
}

export interface Document {
  id: string;
  tenant_id: string;
  document_type: DocumentType;
  document_number: string;
  customer_id: string;
  customer_name?: string;
  contact_id?: string | null;
  status: DocumentStatus;
  date: string;
  due_date?: string | null;
  validity_date?: string | null;
  subtotal: number;
  tax_amount: number;
  total: number;
  currency: string;
  notes?: string | null;
  terms?: string | null;
  lines: DocumentLine[];
  created_at: string;
  updated_at: string;
}

export interface DocumentLineCreate {
  product_id?: string | null;
  description: string;
  quantity: number;
  unit_price: number;
  discount_percent?: number | null;
  tax_rate?: number;
}

export interface DocumentCreate {
  document_type: DocumentType;
  customer_id: string;
  contact_id?: string | null;
  date?: string | null;
  due_date?: string | null;
  validity_date?: string | null;
  currency?: string;
  notes?: string | null;
  terms?: string | null;
  lines: DocumentLineCreate[];
}

export interface DocumentUpdate {
  status?: DocumentStatus | null;
  due_date?: string | null;
  notes?: string | null;
  terms?: string | null;
}

export interface DocumentList {
  total: number;
  page: number;
  per_page: number;
  items: Document[];
}

// ============================================================================
// TYPES - PRODUCTS
// ============================================================================

export type ProductType = 'PRODUCT' | 'SERVICE';

export interface Product {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  type: ProductType;
  description?: string | null;
  unit_price: number;
  cost_price?: number | null;
  tax_rate: number;
  unit?: string | null;
  category?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  code: string;
  name: string;
  type?: ProductType;
  description?: string | null;
  unit_price: number;
  cost_price?: number | null;
  tax_rate?: number;
  unit?: string | null;
  category?: string | null;
}

export interface ProductUpdate {
  name?: string | null;
  description?: string | null;
  unit_price?: number | null;
  cost_price?: number | null;
  tax_rate?: number | null;
  unit?: string | null;
  category?: string | null;
  is_active?: boolean | null;
}

export interface ProductList {
  total: number;
  page: number;
  per_page: number;
  items: Product[];
}

// ============================================================================
// TYPES - PIPELINE
// ============================================================================

export interface PipelineStage {
  id: string;
  name: string;
  position: number;
  probability: number;
  color?: string | null;
}

export interface PipelineStats {
  total_opportunities: number;
  total_value: number;
  weighted_value: number;
  by_stage: {
    stage_id: string;
    stage_name: string;
    count: number;
    value: number;
  }[];
  conversion_rate: number;
  avg_deal_size: number;
}

// ============================================================================
// TYPES - DASHBOARD
// ============================================================================

export interface SalesDashboard {
  revenue_mtd: number;
  revenue_ytd: number;
  quotes_pending: number;
  invoices_overdue: number;
  opportunities_open: number;
  pipeline_value: number;
  top_customers: { id: string; name: string; revenue: number }[];
  recent_activities: unknown[];
}

// ============================================================================
// HOOKS - CUSTOMERS
// ============================================================================

export function useCustomers(filters?: {
  type?: CustomerType;
  search?: string;
  is_active?: boolean;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...commercialKeys.customers(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<CustomerList>(`/commercial/customers${queryString ? `?${queryString}` : ''}`);
      return response;
    },
  });
}

export function useCustomer(id: string) {
  return useQuery({
    queryKey: commercialKeys.customer(id),
    queryFn: async () => {
      const response = await api.get<Customer>(`/commercial/customers/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateCustomer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CustomerCreate) => {
      return api.post<Customer>('/commercial/customers', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.customers() });
    },
  });
}

export function useUpdateCustomer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: CustomerUpdate }) => {
      return api.put<Customer>(`/commercial/customers/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.customers() });
      queryClient.invalidateQueries({ queryKey: commercialKeys.customer(id) });
    },
  });
}

export function useDeleteCustomer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/commercial/customers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.customers() });
    },
  });
}

// ============================================================================
// HOOKS - CONTACTS
// ============================================================================

export function useContacts(customerId?: string) {
  return useQuery({
    queryKey: [...commercialKeys.contacts(), customerId],
    queryFn: async () => {
      const url = customerId
        ? `/commercial/contacts?customer_id=${customerId}`
        : '/commercial/contacts';
      const response = await api.get<{ items: Contact[]; total: number }>(url);
      return response;
    },
  });
}

export function useCreateContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ContactCreate) => {
      return api.post<Contact>('/commercial/contacts', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.contacts() });
    },
  });
}

export function useUpdateContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ContactUpdate }) => {
      return api.put<Contact>(`/commercial/contacts/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.contacts() });
    },
  });
}

// ============================================================================
// HOOKS - OPPORTUNITIES
// ============================================================================

export function useOpportunities(filters?: {
  status?: OpportunityStatus;
  customer_id?: string;
  assigned_to?: string;
}) {
  return useQuery({
    queryKey: [...commercialKeys.opportunities(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      if (filters?.assigned_to) params.append('assigned_to', filters.assigned_to);
      const queryString = params.toString();
      const response = await api.get<OpportunityList>(
        `/commercial/opportunities${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useOpportunity(id: string) {
  return useQuery({
    queryKey: commercialKeys.opportunity(id),
    queryFn: async () => {
      const response = await api.get<Opportunity>(`/commercial/opportunities/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateOpportunity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: OpportunityCreate) => {
      return api.post<Opportunity>('/commercial/opportunities', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.opportunities() });
      queryClient.invalidateQueries({ queryKey: commercialKeys.pipeline() });
    },
  });
}

export function useUpdateOpportunity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: OpportunityUpdate }) => {
      return api.put<Opportunity>(`/commercial/opportunities/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.opportunities() });
      queryClient.invalidateQueries({ queryKey: commercialKeys.opportunity(id) });
      queryClient.invalidateQueries({ queryKey: commercialKeys.pipeline() });
    },
  });
}

// ============================================================================
// HOOKS - DOCUMENTS
// ============================================================================

export function useDocuments(filters?: {
  document_type?: DocumentType;
  status?: DocumentStatus;
  customer_id?: string;
}) {
  return useQuery({
    queryKey: [...commercialKeys.documents(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.document_type) params.append('document_type', filters.document_type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      const queryString = params.toString();
      const response = await api.get<DocumentList>(
        `/commercial/documents${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: commercialKeys.document(id),
    queryFn: async () => {
      const response = await api.get<Document>(`/commercial/documents/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: DocumentCreate) => {
      return api.post<Document>('/commercial/documents', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.documents() });
    },
  });
}

export function useUpdateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: DocumentUpdate }) => {
      return api.put<Document>(`/commercial/documents/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.documents() });
      queryClient.invalidateQueries({ queryKey: commercialKeys.document(id) });
    },
  });
}

export function useSendDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, email }: { id: string; email?: string }) => {
      return api.post(`/commercial/documents/${id}/send`, { email });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.documents() });
    },
  });
}

export function useConvertDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, targetType }: { id: string; targetType: DocumentType }) => {
      return api.post<Document>(`/commercial/documents/${id}/convert`, { target_type: targetType });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.documents() });
    },
  });
}

// ============================================================================
// HOOKS - PRODUCTS
// ============================================================================

export function useProducts(filters?: {
  type?: ProductType;
  category?: string;
  search?: string;
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: [...commercialKeys.products(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.category) params.append('category', filters.category);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<ProductList>(
        `/commercial/products${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: commercialKeys.product(id),
    queryFn: async () => {
      const response = await api.get<Product>(`/commercial/products/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ProductCreate) => {
      return api.post<Product>('/commercial/products', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.products() });
    },
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ProductUpdate }) => {
      return api.put<Product>(`/commercial/products/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: commercialKeys.products() });
      queryClient.invalidateQueries({ queryKey: commercialKeys.product(id) });
    },
  });
}

// ============================================================================
// HOOKS - PIPELINE
// ============================================================================

export function usePipelineStages() {
  return useQuery({
    queryKey: [...commercialKeys.pipeline(), 'stages'],
    queryFn: async () => {
      const response = await api.get<{ stages: PipelineStage[] }>('/commercial/pipeline/stages');
      return response;
    },
  });
}

export function usePipelineStats() {
  return useQuery({
    queryKey: [...commercialKeys.pipeline(), 'stats'],
    queryFn: async () => {
      const response = await api.get<PipelineStats>('/commercial/pipeline/stats');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - DASHBOARD
// ============================================================================

export function useSalesDashboard() {
  return useQuery({
    queryKey: commercialKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<SalesDashboard>('/commercial/dashboard');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - ACTIVITIES
// ============================================================================

export function useActivities(filters?: { customer_id?: string; opportunity_id?: string }) {
  return useQuery({
    queryKey: [...commercialKeys.all, 'activities', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      if (filters?.opportunity_id) params.append('opportunity_id', filters.opportunity_id);
      const queryString = params.toString();
      const response = await api.get<{ items: unknown[]; total: number }>(
        `/commercial/activities${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCreateActivity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { type: string; description: string; customer_id?: string; opportunity_id?: string }) => {
      return api.post('/commercial/activities', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [...commercialKeys.all, 'activities'] });
    },
  });
}
