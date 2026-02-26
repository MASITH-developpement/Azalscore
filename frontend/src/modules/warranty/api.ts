/**
 * AZALSCORE - Warranty API
 * ========================
 * Complete typed API client for Warranty Management module.
 * Covers: Warranties, Claims, Extensions, Repairs, Provisions
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const warrantyKeys = {
  all: ['warranty'] as const,
  warranties: () => [...warrantyKeys.all, 'warranties'] as const,
  warranty: (id: string) => [...warrantyKeys.warranties(), id] as const,
  claims: () => [...warrantyKeys.all, 'claims'] as const,
  claim: (id: string) => [...warrantyKeys.claims(), id] as const,
  extensions: () => [...warrantyKeys.all, 'extensions'] as const,
  provisions: () => [...warrantyKeys.all, 'provisions'] as const,
  stats: () => [...warrantyKeys.all, 'stats'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type WarrantyType =
  | 'legal_conformity'      // Garantie légale de conformité (2 ans)
  | 'hidden_defects'        // Garantie vices cachés
  | 'commercial'            // Garantie commerciale constructeur
  | 'extended'              // Extension de garantie
  | 'parts_only'            // Pièces uniquement
  | 'labor_only'            // Main d'oeuvre uniquement
  | 'full_coverage';        // Couverture complète

export type WarrantyStatus =
  | 'active' | 'expired' | 'voided' | 'transferred' | 'pending';

export type ClaimStatus =
  | 'draft' | 'submitted' | 'under_review' | 'approved'
  | 'in_repair' | 'awaiting_parts' | 'repaired' | 'replaced'
  | 'refunded' | 'rejected' | 'closed' | 'cancelled';

export type ClaimResolution =
  | 'repair' | 'replacement' | 'refund' | 'credit_note'
  | 'partial_refund' | 'exchange' | 'no_action' | 'rejected';

export type DefectType =
  | 'manufacturing' | 'material' | 'workmanship' | 'design'
  | 'shipping_damage' | 'wear_and_tear' | 'misuse' | 'unknown';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface WarrantyTerms {
  duration_months: number;
  coverage_type: WarrantyType;
  parts_covered: boolean;
  labor_covered: boolean;
  on_site_service: boolean;
  pickup_service: boolean;
  international_coverage: boolean;
  transferable: boolean;
  deductible_amount?: number | null;
  max_claim_value?: number | null;
  exclusions: string[];
}

export interface Warranty {
  id: string;
  tenant_id: string;
  reference: string;
  product_id: string;
  product_name: string;
  product_serial?: string | null;
  customer_id: string;
  customer_name: string;
  warranty_type: WarrantyType;
  status: WarrantyStatus;
  purchase_date: string;
  start_date: string;
  end_date: string;
  invoice_number?: string | null;
  invoice_amount?: number | null;
  terms: WarrantyTerms;
  extended_warranty_id?: string | null;
  claims_count: number;
  total_claim_value: number;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClaimDocument {
  id: string;
  claim_id: string;
  name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  document_type: 'photo' | 'video' | 'invoice' | 'report' | 'other';
  uploaded_at: string;
}

export interface RepairDetail {
  id: string;
  claim_id: string;
  description: string;
  repair_type: 'in_house' | 'external' | 'manufacturer';
  technician?: string | null;
  service_center?: string | null;
  parts_used: Array<{ name: string; quantity: number; cost: number }>;
  labor_hours: number;
  labor_cost: number;
  parts_cost: number;
  total_cost: number;
  started_at?: string | null;
  completed_at?: string | null;
  notes?: string | null;
}

export interface WarrantyClaim {
  id: string;
  tenant_id: string;
  reference: string;
  warranty_id: string;
  warranty_reference: string;
  product_name: string;
  customer_id: string;
  customer_name: string;
  status: ClaimStatus;
  defect_type: DefectType;
  defect_description: string;
  reported_date: string;
  resolution?: ClaimResolution | null;
  resolution_date?: string | null;
  resolution_notes?: string | null;
  estimated_cost?: number | null;
  actual_cost?: number | null;
  refund_amount?: number | null;
  replacement_product_id?: string | null;
  assigned_to?: string | null;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  documents: ClaimDocument[];
  repair_details?: RepairDetail | null;
  created_at: string;
  updated_at: string;
}

export interface WarrantyExtension {
  id: string;
  tenant_id: string;
  warranty_id: string;
  original_end_date: string;
  new_end_date: string;
  extension_months: number;
  extension_type: WarrantyType;
  price: number;
  purchase_date: string;
  provider?: string | null;
  policy_number?: string | null;
  terms: WarrantyTerms;
  is_active: boolean;
  created_at: string;
}

export interface WarrantyProvision {
  id: string;
  tenant_id: string;
  fiscal_year: number;
  fiscal_month: number;
  provision_type: 'legal' | 'commercial' | 'extended';
  opening_balance: number;
  additions: number;
  utilizations: number;
  reversals: number;
  closing_balance: number;
  calculation_basis: string;
  calculation_rate: number;
  notes?: string | null;
  posted: boolean;
  posted_at?: string | null;
  accounting_entry_id?: string | null;
  created_at: string;
}

export interface WarrantyStats {
  total_active_warranties: number;
  expiring_this_month: number;
  expiring_next_30_days: number;
  total_claims: number;
  open_claims: number;
  avg_resolution_days: number;
  claim_approval_rate: number;
  total_claim_cost: number;
  by_warranty_type: Record<WarrantyType, number>;
  by_claim_status: Record<ClaimStatus, number>;
  by_defect_type: Record<DefectType, number>;
  provision_balance: number;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface WarrantyCreate {
  product_id: string;
  product_serial?: string;
  customer_id: string;
  warranty_type: WarrantyType;
  purchase_date: string;
  start_date?: string;
  invoice_number?: string;
  invoice_amount?: number;
  terms?: Partial<WarrantyTerms>;
  notes?: string;
}

export interface WarrantyUpdate {
  status?: WarrantyStatus;
  end_date?: string;
  notes?: string;
}

export interface ClaimCreate {
  warranty_id: string;
  defect_type: DefectType;
  defect_description: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

export interface ClaimUpdate {
  status?: ClaimStatus;
  defect_type?: DefectType;
  defect_description?: string;
  resolution?: ClaimResolution;
  resolution_notes?: string;
  assigned_to?: string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

export interface ExtensionCreate {
  warranty_id: string;
  extension_months: number;
  extension_type?: WarrantyType;
  price: number;
  provider?: string;
  policy_number?: string;
  terms?: Partial<WarrantyTerms>;
}

// ============================================================================
// HOOKS - WARRANTIES
// ============================================================================

export function useWarranties(filters?: {
  status?: WarrantyStatus;
  warranty_type?: WarrantyType;
  customer_id?: string;
  product_id?: string;
  expiring_before?: string;
  expiring_after?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...warrantyKeys.warranties(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.warranty_type) params.append('warranty_type', filters.warranty_type);
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      if (filters?.product_id) params.append('product_id', filters.product_id);
      if (filters?.expiring_before) params.append('expiring_before', filters.expiring_before);
      if (filters?.expiring_after) params.append('expiring_after', filters.expiring_after);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Warranty[]; total: number }>(
        `/warranty/warranties${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useWarranty(id: string) {
  return useQuery({
    queryKey: warrantyKeys.warranty(id),
    queryFn: async () => {
      const response = await api.get<Warranty>(`/warranty/warranties/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useWarrantyByProduct(productId: string) {
  return useQuery({
    queryKey: [...warrantyKeys.warranties(), 'product', productId],
    queryFn: async () => {
      const response = await api.get<{ items: Warranty[] }>(
        `/warranty/warranties/product/${productId}`
      );
      return response;
    },
    enabled: !!productId,
  });
}

export function useCreateWarranty() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: WarrantyCreate) => {
      return api.post<Warranty>('/warranty/warranties', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.warranties() });
    },
  });
}

export function useUpdateWarranty() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: WarrantyUpdate }) => {
      return api.put<Warranty>(`/warranty/warranties/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.warranties() });
      queryClient.invalidateQueries({ queryKey: warrantyKeys.warranty(id) });
    },
  });
}

export function useTransferWarranty() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, newCustomerId }: { id: string; newCustomerId: string }) => {
      return api.post<Warranty>(`/warranty/warranties/${id}/transfer`, {
        new_customer_id: newCustomerId,
      });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.warranties() });
      queryClient.invalidateQueries({ queryKey: warrantyKeys.warranty(id) });
    },
  });
}

export function useCheckWarrantyValidity() {
  return useMutation({
    mutationFn: async (data: { product_serial: string; purchase_date?: string }) => {
      return api.post<{
        valid: boolean;
        warranty?: Warranty | null;
        days_remaining?: number;
        message: string;
      }>('/warranty/check', data);
    },
  });
}

// ============================================================================
// HOOKS - CLAIMS
// ============================================================================

export function useWarrantyClaims(filters?: {
  status?: ClaimStatus;
  warranty_id?: string;
  customer_id?: string;
  defect_type?: DefectType;
  priority?: string;
  assigned_to?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...warrantyKeys.claims(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.warranty_id) params.append('warranty_id', filters.warranty_id);
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      if (filters?.defect_type) params.append('defect_type', filters.defect_type);
      if (filters?.priority) params.append('priority', filters.priority);
      if (filters?.assigned_to) params.append('assigned_to', filters.assigned_to);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: WarrantyClaim[]; total: number }>(
        `/warranty/claims${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useWarrantyClaim(id: string) {
  return useQuery({
    queryKey: warrantyKeys.claim(id),
    queryFn: async () => {
      const response = await api.get<WarrantyClaim>(`/warranty/claims/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateClaim() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ClaimCreate) => {
      return api.post<WarrantyClaim>('/warranty/claims', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.claims() });
      queryClient.invalidateQueries({ queryKey: warrantyKeys.warranties() });
    },
  });
}

export function useUpdateClaim() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ClaimUpdate }) => {
      return api.put<WarrantyClaim>(`/warranty/claims/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.claims() });
      queryClient.invalidateQueries({ queryKey: warrantyKeys.claim(id) });
    },
  });
}

export function useApproveClaim() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, resolution, notes }: { id: string; resolution: ClaimResolution; notes?: string }) => {
      return api.post(`/warranty/claims/${id}/approve`, { resolution, notes });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.claims() });
      queryClient.invalidateQueries({ queryKey: warrantyKeys.claim(id) });
    },
  });
}

export function useRejectClaim() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.post(`/warranty/claims/${id}/reject`, { reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.claims() });
      queryClient.invalidateQueries({ queryKey: warrantyKeys.claim(id) });
    },
  });
}

export function useUploadClaimDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      claimId,
      file,
      documentType,
    }: {
      claimId: string;
      file: File;
      documentType: 'photo' | 'video' | 'invoice' | 'report' | 'other';
    }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_type', documentType);
      return api.post<ClaimDocument>(`/warranty/claims/${claimId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: (_, { claimId }) => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.claim(claimId) });
    },
  });
}

export function useAddRepairDetails() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      claimId,
      data,
    }: {
      claimId: string;
      data: Omit<RepairDetail, 'id' | 'claim_id' | 'total_cost'>;
    }) => {
      return api.post<RepairDetail>(`/warranty/claims/${claimId}/repair`, data);
    },
    onSuccess: (_, { claimId }) => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.claim(claimId) });
    },
  });
}

// ============================================================================
// HOOKS - EXTENSIONS
// ============================================================================

export function useWarrantyExtensions(warrantyId?: string) {
  return useQuery({
    queryKey: [...warrantyKeys.extensions(), warrantyId],
    queryFn: async () => {
      const params = warrantyId ? `?warranty_id=${warrantyId}` : '';
      const response = await api.get<{ items: WarrantyExtension[] }>(
        `/warranty/extensions${params}`
      );
      return response;
    },
  });
}

export function useCreateExtension() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ExtensionCreate) => {
      return api.post<WarrantyExtension>('/warranty/extensions', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.extensions() });
      queryClient.invalidateQueries({ queryKey: warrantyKeys.warranties() });
    },
  });
}

export function useCancelExtension() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/warranty/extensions/${id}/cancel`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.extensions() });
      queryClient.invalidateQueries({ queryKey: warrantyKeys.warranties() });
    },
  });
}

// ============================================================================
// HOOKS - PROVISIONS
// ============================================================================

export function useWarrantyProvisions(filters?: { fiscal_year?: number; provision_type?: string }) {
  return useQuery({
    queryKey: [...warrantyKeys.provisions(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.fiscal_year) params.append('fiscal_year', String(filters.fiscal_year));
      if (filters?.provision_type) params.append('provision_type', filters.provision_type);
      const queryString = params.toString();
      const response = await api.get<{ items: WarrantyProvision[] }>(
        `/warranty/provisions${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCalculateProvisions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { fiscal_year: number; fiscal_month: number }) => {
      return api.post<WarrantyProvision[]>('/warranty/provisions/calculate', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.provisions() });
    },
  });
}

export function usePostProvision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/warranty/provisions/${id}/post`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: warrantyKeys.provisions() });
    },
  });
}

// ============================================================================
// HOOKS - STATS
// ============================================================================

export function useWarrantyStats() {
  return useQuery({
    queryKey: warrantyKeys.stats(),
    queryFn: async () => {
      const response = await api.get<WarrantyStats>('/warranty/stats');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - EXPIRATION ALERTS
// ============================================================================

export function useExpiringWarranties(days: number = 30) {
  return useQuery({
    queryKey: [...warrantyKeys.warranties(), 'expiring', days],
    queryFn: async () => {
      const response = await api.get<{ items: Warranty[] }>(
        `/warranty/warranties/expiring?days=${days}`
      );
      return response;
    },
  });
}

export function useSendExpirationReminders() {
  return useMutation({
    mutationFn: async (days: number = 30) => {
      return api.post<{ sent_count: number }>('/warranty/reminders/send', { days_before: days });
    },
  });
}
