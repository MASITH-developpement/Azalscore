/**
 * AZALSCORE - Complaints API
 * ==========================
 * Complete typed API client for Complaints Management module.
 * Covers: Complaints, Categories, SLA Policies, Actions, Resolution
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const complaintsKeys = {
  all: ['complaints'] as const,
  list: () => [...complaintsKeys.all, 'list'] as const,
  detail: (id: string) => [...complaintsKeys.all, id] as const,
  actions: (id: string) => [...complaintsKeys.all, id, 'actions'] as const,
  categories: () => [...complaintsKeys.all, 'categories'] as const,
  slaPolicies: () => [...complaintsKeys.all, 'sla-policies'] as const,
  stats: () => [...complaintsKeys.all, 'stats'] as const,
  dashboard: () => [...complaintsKeys.all, 'dashboard'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type ComplaintStatus =
  | 'new' | 'acknowledged' | 'investigating' | 'pending_customer'
  | 'pending_supplier' | 'escalated' | 'resolved' | 'closed' | 'reopened';

export type ComplaintPriority = 'low' | 'medium' | 'high' | 'urgent' | 'critical';

export type ComplaintChannel =
  | 'email' | 'phone' | 'chat' | 'web_form' | 'social_media'
  | 'in_person' | 'letter' | 'third_party';

export type ComplaintCategory =
  | 'product_quality' | 'delivery' | 'billing' | 'customer_service'
  | 'warranty' | 'technical' | 'safety' | 'legal' | 'other';

export type ResolutionType =
  | 'refund' | 'replacement' | 'repair' | 'credit_note'
  | 'compensation' | 'apology' | 'process_change' | 'no_action' | 'other';

export type ActionType =
  | 'note' | 'email_sent' | 'call_made' | 'escalation'
  | 'status_change' | 'assignment' | 'resolution' | 'reopen';

export type EscalationLevel = 'L1' | 'L2' | 'L3' | 'management' | 'executive';

export type SatisfactionRating = 1 | 2 | 3 | 4 | 5;

export type RootCauseCategory =
  | 'manufacturing_defect' | 'design_flaw' | 'handling_damage'
  | 'supplier_issue' | 'human_error' | 'process_failure'
  | 'communication_breakdown' | 'system_error' | 'unknown';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface Complaint {
  id: string;
  tenant_id: string;
  reference: string;
  title: string;
  description: string;
  channel: ComplaintChannel;
  category_id?: string | null;
  category_name?: string | null;
  status: ComplaintStatus;
  priority: ComplaintPriority;
  customer_id: string;
  customer_name: string;
  customer_email?: string | null;
  customer_phone?: string | null;
  order_id?: string | null;
  order_reference?: string | null;
  product_id?: string | null;
  product_name?: string | null;
  invoice_id?: string | null;
  invoice_reference?: string | null;
  assigned_to?: string | null;
  assigned_team?: string | null;
  escalation_level: EscalationLevel;
  sla_policy_id?: string | null;
  response_due_at?: string | null;
  resolution_due_at?: string | null;
  first_response_at?: string | null;
  resolved_at?: string | null;
  closed_at?: string | null;
  resolution_type?: ResolutionType | null;
  resolution_summary?: string | null;
  root_cause_category?: RootCauseCategory | null;
  root_cause_description?: string | null;
  compensation_amount?: number | null;
  satisfaction_rating?: SatisfactionRating | null;
  satisfaction_feedback?: string | null;
  is_repeat: boolean;
  previous_complaint_id?: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ComplaintAction {
  id: string;
  complaint_id: string;
  action_type: ActionType;
  description: string;
  performed_by: string;
  performed_by_name: string;
  metadata?: Record<string, unknown> | null;
  is_public: boolean;
  created_at: string;
}

export interface CategoryConfig {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  icon?: string | null;
  parent_id?: string | null;
  default_priority: ComplaintPriority;
  default_team_id?: string | null;
  sla_policy_id?: string | null;
  require_order: boolean;
  require_product: boolean;
  require_invoice: boolean;
  auto_assign: boolean;
  is_public: boolean;
  is_active: boolean;
  sort_order: number;
  created_at: string;
}

export interface SLAPolicy {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  priority: ComplaintPriority;
  first_response_hours: number;
  resolution_hours: number;
  escalation_hours: number;
  business_hours_only: boolean;
  is_active: boolean;
  created_at: string;
}

export interface ComplaintStats {
  total: number;
  open: number;
  resolved_this_month: number;
  average_resolution_hours: number;
  sla_compliance_rate: number;
  satisfaction_average: number;
  by_status: Record<ComplaintStatus, number>;
  by_priority: Record<ComplaintPriority, number>;
  by_category: Record<string, number>;
  by_channel: Record<ComplaintChannel, number>;
}

export interface ComplaintDashboard {
  stats: ComplaintStats;
  recent_complaints: Complaint[];
  sla_breaches: Complaint[];
  my_assigned: Complaint[];
  trending_issues: Array<{ category: string; count: number; trend: number }>;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface ComplaintCreate {
  title: string;
  description: string;
  channel: ComplaintChannel;
  category_id?: string;
  priority?: ComplaintPriority;
  customer_id: string;
  order_id?: string;
  product_id?: string;
  invoice_id?: string;
  assigned_to?: string;
  tags?: string[];
}

export interface ComplaintUpdate {
  title?: string;
  description?: string;
  category_id?: string;
  priority?: ComplaintPriority;
  assigned_to?: string;
  assigned_team?: string;
  tags?: string[];
}

export interface ComplaintResolution {
  resolution_type: ResolutionType;
  resolution_summary: string;
  root_cause_category?: RootCauseCategory;
  root_cause_description?: string;
  compensation_amount?: number;
}

export interface ActionCreate {
  action_type: ActionType;
  description: string;
  is_public?: boolean;
  metadata?: Record<string, unknown>;
}

// ============================================================================
// HOOKS - COMPLAINTS
// ============================================================================

export function useComplaints(filters?: {
  status?: ComplaintStatus;
  priority?: ComplaintPriority;
  category_id?: string;
  channel?: ComplaintChannel;
  assigned_to?: string;
  customer_id?: string;
  search?: string;
  sla_breached?: boolean;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...complaintsKeys.list(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.priority) params.append('priority', filters.priority);
      if (filters?.category_id) params.append('category_id', filters.category_id);
      if (filters?.channel) params.append('channel', filters.channel);
      if (filters?.assigned_to) params.append('assigned_to', filters.assigned_to);
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.sla_breached !== undefined) params.append('sla_breached', String(filters.sla_breached));
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Complaint[]; total: number }>(
        `/complaints${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useComplaint(id: string) {
  return useQuery({
    queryKey: complaintsKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Complaint>(`/complaints/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateComplaint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ComplaintCreate) => {
      return api.post<Complaint>('/complaints', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.list() });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.stats() });
    },
  });
}

export function useUpdateComplaint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ComplaintUpdate }) => {
      return api.put<Complaint>(`/complaints/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.list() });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.detail(id) });
    },
  });
}

export function useDeleteComplaint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/complaints/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.list() });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.stats() });
    },
  });
}

// ============================================================================
// HOOKS - STATUS TRANSITIONS
// ============================================================================

export function useAcknowledgeComplaint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, message }: { id: string; message?: string }) => {
      return api.post(`/complaints/${id}/acknowledge`, { message });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.list() });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.detail(id) });
    },
  });
}

export function useEscalateComplaint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      level,
      reason,
      assignTo,
    }: {
      id: string;
      level: EscalationLevel;
      reason: string;
      assignTo?: string;
    }) => {
      return api.post(`/complaints/${id}/escalate`, { level, reason, assign_to: assignTo });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.list() });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.detail(id) });
    },
  });
}

export function useResolveComplaint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ComplaintResolution }) => {
      return api.post(`/complaints/${id}/resolve`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.list() });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.stats() });
    },
  });
}

export function useCloseComplaint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes?: string }) => {
      return api.post(`/complaints/${id}/close`, { notes });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.list() });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.stats() });
    },
  });
}

export function useReopenComplaint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.post(`/complaints/${id}/reopen`, { reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.list() });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.detail(id) });
    },
  });
}

// ============================================================================
// HOOKS - ACTIONS
// ============================================================================

export function useComplaintActions(complaintId: string) {
  return useQuery({
    queryKey: complaintsKeys.actions(complaintId),
    queryFn: async () => {
      const response = await api.get<{ items: ComplaintAction[] }>(
        `/complaints/${complaintId}/actions`
      );
      return response;
    },
    enabled: !!complaintId,
  });
}

export function useAddComplaintAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ complaintId, data }: { complaintId: string; data: ActionCreate }) => {
      return api.post<ComplaintAction>(`/complaints/${complaintId}/actions`, data);
    },
    onSuccess: (_, { complaintId }) => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.actions(complaintId) });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.detail(complaintId) });
    },
  });
}

// ============================================================================
// HOOKS - ASSIGNMENT
// ============================================================================

export function useAssignComplaint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      userId,
      teamId,
    }: {
      id: string;
      userId?: string;
      teamId?: string;
    }) => {
      return api.post(`/complaints/${id}/assign`, { user_id: userId, team_id: teamId });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.list() });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.detail(id) });
    },
  });
}

// ============================================================================
// HOOKS - SATISFACTION
// ============================================================================

export function useSubmitSatisfaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      rating,
      feedback,
    }: {
      id: string;
      rating: SatisfactionRating;
      feedback?: string;
    }) => {
      return api.post(`/complaints/${id}/satisfaction`, { rating, feedback });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: complaintsKeys.stats() });
    },
  });
}

// ============================================================================
// HOOKS - CATEGORIES
// ============================================================================

export function useComplaintCategories(filters?: { is_active?: boolean }) {
  return useQuery({
    queryKey: [...complaintsKeys.categories(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: CategoryConfig[] }>(
        `/complaints/categories${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCreateComplaintCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Omit<CategoryConfig, 'id' | 'tenant_id' | 'is_active' | 'created_at'>) => {
      return api.post<CategoryConfig>('/complaints/categories', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.categories() });
    },
  });
}

// ============================================================================
// HOOKS - SLA POLICIES
// ============================================================================

export function useSLAPolicies() {
  return useQuery({
    queryKey: complaintsKeys.slaPolicies(),
    queryFn: async () => {
      const response = await api.get<{ items: SLAPolicy[] }>('/complaints/sla-policies');
      return response;
    },
  });
}

export function useCreateSLAPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Omit<SLAPolicy, 'id' | 'tenant_id' | 'is_active' | 'created_at'>) => {
      return api.post<SLAPolicy>('/complaints/sla-policies', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: complaintsKeys.slaPolicies() });
    },
  });
}

// ============================================================================
// HOOKS - STATS & DASHBOARD
// ============================================================================

export function useComplaintStats(filters?: { from_date?: string; to_date?: string }) {
  return useQuery({
    queryKey: [...complaintsKeys.stats(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const response = await api.get<ComplaintStats>(
        `/complaints/stats${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useComplaintDashboard() {
  return useQuery({
    queryKey: complaintsKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<ComplaintDashboard>('/complaints/dashboard');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - EXPORT
// ============================================================================

export function useExportComplaints() {
  return useMutation({
    mutationFn: async (data: {
      format: 'csv' | 'excel' | 'pdf';
      filters?: Record<string, unknown>;
    }) => {
      return api.post<Blob>('/complaints/export', data, { responseType: 'blob' });
    },
  });
}
