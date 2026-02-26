/**
 * AZALSCORE - Contracts API
 * =========================
 * Complete typed API client for Contracts module.
 * Covers: Contracts, Parties, Amendments, Obligations, Milestones
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const contractsKeys = {
  all: ['contracts'] as const,
  list: () => [...contractsKeys.all, 'list'] as const,
  detail: (id: string) => [...contractsKeys.all, id] as const,
  parties: (id: string) => [...contractsKeys.all, id, 'parties'] as const,
  amendments: (id: string) => [...contractsKeys.all, id, 'amendments'] as const,
  obligations: (id: string) => [...contractsKeys.all, id, 'obligations'] as const,
  documents: (id: string) => [...contractsKeys.all, id, 'documents'] as const,
  templates: () => [...contractsKeys.all, 'templates'] as const,
  calendar: () => [...contractsKeys.all, 'calendar'] as const,
  stats: () => [...contractsKeys.all, 'stats'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type ContractType =
  | 'sales' | 'purchase' | 'service' | 'subscription' | 'license'
  | 'distribution' | 'franchise' | 'agency' | 'reseller' | 'partnership'
  | 'joint_venture' | 'consortium' | 'affiliate' | 'nda' | 'non_compete'
  | 'non_solicitation' | 'lease' | 'sublease' | 'real_estate' | 'employment'
  | 'consulting' | 'internship' | 'freelance' | 'maintenance' | 'sla'
  | 'support' | 'warranty' | 'rental' | 'leasing' | 'framework' | 'master' | 'other';

export type ContractStatus =
  | 'draft' | 'in_review' | 'in_negotiation' | 'pending_approval'
  | 'approved' | 'pending_signature' | 'partially_signed' | 'active'
  | 'suspended' | 'on_hold' | 'expired' | 'terminated'
  | 'renewed' | 'cancelled' | 'archived';

export type PartyRole =
  | 'contractor' | 'client' | 'supplier' | 'partner'
  | 'employer' | 'employee' | 'licensor' | 'licensee'
  | 'landlord' | 'tenant' | 'guarantor' | 'beneficiary'
  | 'agent' | 'principal';

export type PartyType = 'company' | 'individual' | 'government' | 'nonprofit';

export type RenewalType = 'manual' | 'automatic' | 'negotiated' | 'evergreen' | 'none';

export type BillingFrequency =
  | 'one_time' | 'daily' | 'weekly' | 'biweekly' | 'monthly'
  | 'bimonthly' | 'quarterly' | 'semi_annual' | 'annual' | 'custom';

export type AmendmentType =
  | 'extension' | 'modification' | 'pricing' | 'scope'
  | 'parties' | 'termination' | 'renewal' | 'addendum' | 'assignment' | 'other';

export type ObligationType =
  | 'payment' | 'delivery' | 'performance' | 'reporting'
  | 'compliance' | 'audit' | 'renewal_notice' | 'termination_notice'
  | 'confidentiality' | 'insurance' | 'warranty' | 'milestone' | 'review' | 'other';

export type ObligationStatus = 'pending' | 'in_progress' | 'completed' | 'overdue' | 'waived';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface Contract {
  id: string;
  tenant_id: string;
  reference: string;
  title: string;
  description?: string | null;
  contract_type: ContractType;
  status: ContractStatus;
  start_date: string;
  end_date?: string | null;
  signed_date?: string | null;
  total_value?: number | null;
  currency: string;
  billing_frequency?: BillingFrequency | null;
  payment_terms?: string | null;
  renewal_type: RenewalType;
  auto_renew_days?: number | null;
  notice_period_days?: number | null;
  termination_clause?: string | null;
  governing_law?: string | null;
  jurisdiction?: string | null;
  confidential: boolean;
  parent_contract_id?: string | null;
  template_id?: string | null;
  owner_id?: string | null;
  notes?: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ContractParty {
  id: string;
  contract_id: string;
  party_type: PartyType;
  party_role: PartyRole;
  entity_id?: string | null;
  company_name?: string | null;
  contact_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  address?: string | null;
  is_primary: boolean;
  signed: boolean;
  signed_at?: string | null;
  signed_by?: string | null;
}

export interface ContractAmendment {
  id: string;
  contract_id: string;
  reference: string;
  amendment_type: AmendmentType;
  title: string;
  description?: string | null;
  effective_date: string;
  changes: Record<string, unknown>;
  approved: boolean;
  approved_by?: string | null;
  approved_at?: string | null;
  created_at: string;
}

export interface ContractObligation {
  id: string;
  contract_id: string;
  obligation_type: ObligationType;
  title: string;
  description?: string | null;
  responsible_party?: string | null;
  due_date?: string | null;
  recurrence?: string | null;
  status: ObligationStatus;
  completed_at?: string | null;
  completed_by?: string | null;
  notes?: string | null;
}

export interface ContractDocument {
  id: string;
  contract_id: string;
  name: string;
  file_path: string;
  file_type: string;
  file_size: number;
  version: number;
  is_signed: boolean;
  uploaded_by?: string | null;
  uploaded_at: string;
}

export interface ContractTemplate {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  contract_type: ContractType;
  content: string;
  variables: string[];
  is_active: boolean;
  created_at: string;
}

export interface ContractCalendarEvent {
  id: string;
  contract_id: string;
  contract_title: string;
  event_type: 'start' | 'end' | 'renewal' | 'obligation' | 'milestone';
  event_date: string;
  title: string;
  description?: string | null;
}

export interface ContractStats {
  total_contracts: number;
  active_contracts: number;
  total_value: number;
  by_status: Record<ContractStatus, number>;
  by_type: Record<ContractType, number>;
  expiring_soon: number;
  pending_renewal: number;
  obligations_overdue: number;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface ContractCreate {
  title: string;
  description?: string;
  contract_type: ContractType;
  start_date: string;
  end_date?: string;
  total_value?: number;
  currency?: string;
  billing_frequency?: BillingFrequency;
  payment_terms?: string;
  renewal_type?: RenewalType;
  auto_renew_days?: number;
  notice_period_days?: number;
  termination_clause?: string;
  governing_law?: string;
  jurisdiction?: string;
  confidential?: boolean;
  parent_contract_id?: string;
  template_id?: string;
  notes?: string;
  tags?: string[];
}

export interface ContractUpdate {
  title?: string;
  description?: string;
  status?: ContractStatus;
  end_date?: string;
  total_value?: number;
  payment_terms?: string;
  renewal_type?: RenewalType;
  notice_period_days?: number;
  owner_id?: string;
  notes?: string;
  tags?: string[];
}

export interface PartyCreate {
  party_type: PartyType;
  party_role: PartyRole;
  entity_id?: string;
  company_name?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  is_primary?: boolean;
}

export interface ObligationCreate {
  obligation_type: ObligationType;
  title: string;
  description?: string;
  responsible_party?: string;
  due_date?: string;
  recurrence?: string;
}

// ============================================================================
// HOOKS - CONTRACTS
// ============================================================================

export function useContracts(filters?: {
  status?: ContractStatus;
  contract_type?: ContractType;
  party_id?: string;
  expiring_before?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...contractsKeys.list(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.contract_type) params.append('contract_type', filters.contract_type);
      if (filters?.party_id) params.append('party_id', filters.party_id);
      if (filters?.expiring_before) params.append('expiring_before', filters.expiring_before);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Contract[]; total: number }>(
        `/contracts${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useContract(id: string) {
  return useQuery({
    queryKey: contractsKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Contract>(`/contracts/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ContractCreate) => {
      return api.post<Contract>('/contracts', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.list() });
    },
  });
}

export function useUpdateContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ContractUpdate }) => {
      return api.put<Contract>(`/contracts/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.list() });
      queryClient.invalidateQueries({ queryKey: contractsKeys.detail(id) });
    },
  });
}

export function useDeleteContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/contracts/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.list() });
    },
  });
}

export function useTerminateContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.post(`/contracts/${id}/terminate`, { reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.list() });
      queryClient.invalidateQueries({ queryKey: contractsKeys.detail(id) });
    },
  });
}

export function useRenewContract() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { new_end_date: string; notes?: string } }) => {
      return api.post<Contract>(`/contracts/${id}/renew`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.list() });
      queryClient.invalidateQueries({ queryKey: contractsKeys.detail(id) });
    },
  });
}

// ============================================================================
// HOOKS - PARTIES
// ============================================================================

export function useContractParties(contractId: string) {
  return useQuery({
    queryKey: contractsKeys.parties(contractId),
    queryFn: async () => {
      const response = await api.get<{ items: ContractParty[] }>(`/contracts/${contractId}/parties`);
      return response;
    },
    enabled: !!contractId,
  });
}

export function useAddContractParty() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ contractId, data }: { contractId: string; data: PartyCreate }) => {
      return api.post<ContractParty>(`/contracts/${contractId}/parties`, data);
    },
    onSuccess: (_, { contractId }) => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.parties(contractId) });
    },
  });
}

export function useRemoveContractParty() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ contractId, partyId }: { contractId: string; partyId: string }) => {
      return api.delete(`/contracts/${contractId}/parties/${partyId}`);
    },
    onSuccess: (_, { contractId }) => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.parties(contractId) });
    },
  });
}

// ============================================================================
// HOOKS - AMENDMENTS
// ============================================================================

export function useContractAmendments(contractId: string) {
  return useQuery({
    queryKey: contractsKeys.amendments(contractId),
    queryFn: async () => {
      const response = await api.get<{ items: ContractAmendment[] }>(
        `/contracts/${contractId}/amendments`
      );
      return response;
    },
    enabled: !!contractId,
  });
}

export function useCreateAmendment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      contractId,
      data,
    }: {
      contractId: string;
      data: {
        amendment_type: AmendmentType;
        title: string;
        description?: string;
        effective_date: string;
        changes: Record<string, unknown>;
      };
    }) => {
      return api.post<ContractAmendment>(`/contracts/${contractId}/amendments`, data);
    },
    onSuccess: (_, { contractId }) => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.amendments(contractId) });
      queryClient.invalidateQueries({ queryKey: contractsKeys.detail(contractId) });
    },
  });
}

export function useApproveAmendment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ contractId, amendmentId }: { contractId: string; amendmentId: string }) => {
      return api.post(`/contracts/${contractId}/amendments/${amendmentId}/approve`);
    },
    onSuccess: (_, { contractId }) => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.amendments(contractId) });
    },
  });
}

// ============================================================================
// HOOKS - OBLIGATIONS
// ============================================================================

export function useContractObligations(contractId: string) {
  return useQuery({
    queryKey: contractsKeys.obligations(contractId),
    queryFn: async () => {
      const response = await api.get<{ items: ContractObligation[] }>(
        `/contracts/${contractId}/obligations`
      );
      return response;
    },
    enabled: !!contractId,
  });
}

export function useCreateObligation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ contractId, data }: { contractId: string; data: ObligationCreate }) => {
      return api.post<ContractObligation>(`/contracts/${contractId}/obligations`, data);
    },
    onSuccess: (_, { contractId }) => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.obligations(contractId) });
    },
  });
}

export function useCompleteObligation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      contractId,
      obligationId,
      notes,
    }: {
      contractId: string;
      obligationId: string;
      notes?: string;
    }) => {
      return api.post(`/contracts/${contractId}/obligations/${obligationId}/complete`, { notes });
    },
    onSuccess: (_, { contractId }) => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.obligations(contractId) });
    },
  });
}

// ============================================================================
// HOOKS - DOCUMENTS
// ============================================================================

export function useContractDocuments(contractId: string) {
  return useQuery({
    queryKey: contractsKeys.documents(contractId),
    queryFn: async () => {
      const response = await api.get<{ items: ContractDocument[] }>(
        `/contracts/${contractId}/documents`
      );
      return response;
    },
    enabled: !!contractId,
  });
}

export function useUploadContractDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ contractId, file }: { contractId: string; file: File }) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post<ContractDocument>(`/contracts/${contractId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: (_, { contractId }) => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.documents(contractId) });
    },
  });
}

// ============================================================================
// HOOKS - TEMPLATES
// ============================================================================

export function useContractTemplates(contractType?: ContractType) {
  return useQuery({
    queryKey: [...contractsKeys.templates(), contractType],
    queryFn: async () => {
      const params = contractType ? `?contract_type=${contractType}` : '';
      const response = await api.get<{ items: ContractTemplate[] }>(`/contracts/templates${params}`);
      return response;
    },
  });
}

export function useGenerateFromTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { template_id: string; variables: Record<string, unknown> }) => {
      return api.post<Contract>('/contracts/generate', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contractsKeys.list() });
    },
  });
}

// ============================================================================
// HOOKS - CALENDAR & STATS
// ============================================================================

export function useContractCalendar(filters?: { from_date?: string; to_date?: string }) {
  return useQuery({
    queryKey: [...contractsKeys.calendar(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const response = await api.get<{ items: ContractCalendarEvent[] }>(
        `/contracts/calendar${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useContractStats() {
  return useQuery({
    queryKey: contractsKeys.stats(),
    queryFn: async () => {
      const response = await api.get<ContractStats>('/contracts/stats');
      return response;
    },
  });
}
