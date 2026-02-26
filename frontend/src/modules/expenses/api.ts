/**
 * AZALSCORE - Expenses API
 * ========================
 * Complete typed API client for Expenses module.
 * Covers: Expense Reports, Lines, Receipts, Mileage, Policies
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const expensesKeys = {
  all: ['expenses'] as const,
  reports: () => [...expensesKeys.all, 'reports'] as const,
  report: (id: string) => [...expensesKeys.reports(), id] as const,
  lines: (reportId: string) => [...expensesKeys.report(reportId), 'lines'] as const,
  receipts: () => [...expensesKeys.all, 'receipts'] as const,
  policies: () => [...expensesKeys.all, 'policies'] as const,
  mileageRates: () => [...expensesKeys.all, 'mileage-rates'] as const,
  stats: () => [...expensesKeys.all, 'stats'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type ExpenseCategory =
  | 'mileage' | 'public_transport' | 'taxi' | 'parking' | 'toll'
  | 'rental_car' | 'fuel' | 'hotel' | 'airbnb' | 'restaurant'
  | 'meal_solo' | 'meal_business' | 'meal_team' | 'flight' | 'train'
  | 'visa' | 'travel_insurance' | 'phone' | 'internet' | 'office_supplies'
  | 'it_equipment' | 'books' | 'representation' | 'subscription' | 'other';

export type ExpenseStatus =
  | 'draft' | 'submitted' | 'pending_approval'
  | 'approved' | 'rejected' | 'paid' | 'cancelled';

export type PaymentMethod =
  | 'personal_card' | 'company_card' | 'cash' | 'company_account' | 'mileage';

export type VehicleType =
  | 'car_3cv' | 'car_4cv' | 'car_5cv' | 'car_6cv' | 'car_7cv_plus'
  | 'moto_50cc' | 'moto_125cc' | 'moto_3_5cv' | 'moto_5cv_plus'
  | 'bicycle' | 'electric_bicycle';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface ExpenseLine {
  id: string;
  tenant_id: string;
  report_id: string;
  category: ExpenseCategory;
  description: string;
  expense_date: string;
  amount: number;
  currency: string;
  vat_rate?: number | null;
  vat_amount?: number | null;
  amount_excl_vat?: number | null;
  payment_method: PaymentMethod;
  receipt_required: boolean;
  receipt_id?: string | null;
  receipt_file_path?: string | null;
  project_id?: string | null;
  client_id?: string | null;
  billable: boolean;
  accounting_code?: string | null;
  cost_center?: string | null;
  mileage_departure?: string | null;
  mileage_arrival?: string | null;
  mileage_distance_km?: number | null;
  mileage_is_round_trip: boolean;
  vehicle_type?: VehicleType | null;
  mileage_rate?: number | null;
  mileage_purpose?: string | null;
  guests: string[];
  guest_count: number;
  is_policy_compliant: boolean;
  policy_violation_reason?: string | null;
  ocr_processed: boolean;
  created_at: string;
}

export interface ExpenseReport {
  id: string;
  tenant_id: string;
  user_id: string;
  title: string;
  description?: string | null;
  status: ExpenseStatus;
  period_start?: string | null;
  period_end?: string | null;
  total_amount: number;
  currency: string;
  lines_count: number;
  submitted_at?: string | null;
  approved_at?: string | null;
  approved_by?: string | null;
  paid_at?: string | null;
  rejection_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExpensePolicy {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  category: ExpenseCategory;
  max_amount?: number | null;
  requires_receipt_above?: number | null;
  requires_justification: boolean;
  requires_approval_above?: number | null;
  is_active: boolean;
}

export interface MileageRate {
  vehicle_type: VehicleType;
  rate_per_km: number;
  year: number;
  source: string;
}

export interface ExpenseStats {
  total_reports: number;
  total_amount: number;
  pending_approval_count: number;
  pending_approval_amount: number;
  by_category: Record<ExpenseCategory, number>;
  by_status: Record<ExpenseStatus, number>;
  avg_processing_time_days: number;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface ExpenseReportCreate {
  title: string;
  description?: string;
  period_start?: string;
  period_end?: string;
}

export interface ExpenseReportUpdate {
  title?: string;
  description?: string;
  period_start?: string;
  period_end?: string;
}

export interface ExpenseLineCreate {
  category: ExpenseCategory;
  description: string;
  expense_date: string;
  amount: number;
  currency?: string;
  vat_rate?: number;
  payment_method?: PaymentMethod;
  receipt_required?: boolean;
  project_id?: string;
  client_id?: string;
  billable?: boolean;
  accounting_code?: string;
  cost_center?: string;
  mileage_departure?: string;
  mileage_arrival?: string;
  mileage_distance_km?: number;
  mileage_is_round_trip?: boolean;
  vehicle_type?: VehicleType;
  mileage_purpose?: string;
  guests?: string[];
}

export interface ExpenseLineUpdate {
  category?: ExpenseCategory;
  description?: string;
  expense_date?: string;
  amount?: number;
  vat_rate?: number;
  payment_method?: PaymentMethod;
  project_id?: string;
  client_id?: string;
  billable?: boolean;
  guests?: string[];
}

// ============================================================================
// HOOKS - EXPENSE REPORTS
// ============================================================================

export function useExpenseReports(filters?: {
  status?: ExpenseStatus;
  user_id?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...expensesKeys.reports(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ExpenseReport[]; total: number }>(
        `/expenses/reports${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useExpenseReport(id: string) {
  return useQuery({
    queryKey: expensesKeys.report(id),
    queryFn: async () => {
      const response = await api.get<ExpenseReport>(`/expenses/reports/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateExpenseReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ExpenseReportCreate) => {
      return api.post<ExpenseReport>('/expenses/reports', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: expensesKeys.reports() });
    },
  });
}

export function useUpdateExpenseReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ExpenseReportUpdate }) => {
      return api.put<ExpenseReport>(`/expenses/reports/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: expensesKeys.reports() });
      queryClient.invalidateQueries({ queryKey: expensesKeys.report(id) });
    },
  });
}

export function useDeleteExpenseReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/expenses/reports/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: expensesKeys.reports() });
    },
  });
}

export function useSubmitExpenseReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/expenses/reports/${id}/submit`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: expensesKeys.reports() });
      queryClient.invalidateQueries({ queryKey: expensesKeys.report(id) });
    },
  });
}

export function useApproveExpenseReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes?: string }) => {
      return api.post(`/expenses/reports/${id}/approve`, { notes });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: expensesKeys.reports() });
      queryClient.invalidateQueries({ queryKey: expensesKeys.report(id) });
    },
  });
}

export function useRejectExpenseReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.post(`/expenses/reports/${id}/reject`, { reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: expensesKeys.reports() });
      queryClient.invalidateQueries({ queryKey: expensesKeys.report(id) });
    },
  });
}

// ============================================================================
// HOOKS - EXPENSE LINES
// ============================================================================

export function useExpenseLines(reportId: string) {
  return useQuery({
    queryKey: expensesKeys.lines(reportId),
    queryFn: async () => {
      const response = await api.get<{ items: ExpenseLine[] }>(
        `/expenses/reports/${reportId}/lines`
      );
      return response;
    },
    enabled: !!reportId,
  });
}

export function useCreateExpenseLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ reportId, data }: { reportId: string; data: ExpenseLineCreate }) => {
      return api.post<ExpenseLine>(`/expenses/reports/${reportId}/lines`, data);
    },
    onSuccess: (_, { reportId }) => {
      queryClient.invalidateQueries({ queryKey: expensesKeys.lines(reportId) });
      queryClient.invalidateQueries({ queryKey: expensesKeys.report(reportId) });
    },
  });
}

export function useUpdateExpenseLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      reportId,
      lineId,
      data,
    }: {
      reportId: string;
      lineId: string;
      data: ExpenseLineUpdate;
    }) => {
      return api.put<ExpenseLine>(`/expenses/reports/${reportId}/lines/${lineId}`, data);
    },
    onSuccess: (_, { reportId }) => {
      queryClient.invalidateQueries({ queryKey: expensesKeys.lines(reportId) });
      queryClient.invalidateQueries({ queryKey: expensesKeys.report(reportId) });
    },
  });
}

export function useDeleteExpenseLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ reportId, lineId }: { reportId: string; lineId: string }) => {
      return api.delete(`/expenses/reports/${reportId}/lines/${lineId}`);
    },
    onSuccess: (_, { reportId }) => {
      queryClient.invalidateQueries({ queryKey: expensesKeys.lines(reportId) });
      queryClient.invalidateQueries({ queryKey: expensesKeys.report(reportId) });
    },
  });
}

// ============================================================================
// HOOKS - RECEIPTS
// ============================================================================

export function useUploadReceipt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      reportId,
      lineId,
      file,
    }: {
      reportId: string;
      lineId: string;
      file: File;
    }) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post<{ receipt_id: string; file_path: string; ocr_result?: Record<string, unknown> }>(
        `/expenses/reports/${reportId}/lines/${lineId}/receipt`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
    },
    onSuccess: (_, { reportId }) => {
      queryClient.invalidateQueries({ queryKey: expensesKeys.lines(reportId) });
    },
  });
}

export function useOcrReceipt() {
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post<{
        vendor?: string;
        amount?: number;
        date?: string;
        category?: ExpenseCategory;
        vat_rate?: number;
        confidence: number;
      }>('/expenses/ocr/receipt', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
  });
}

// ============================================================================
// HOOKS - MILEAGE
// ============================================================================

export function useMileageRates(year?: number) {
  return useQuery({
    queryKey: [...expensesKeys.mileageRates(), year],
    queryFn: async () => {
      const params = year ? `?year=${year}` : '';
      const response = await api.get<{ items: MileageRate[] }>(`/expenses/mileage/rates${params}`);
      return response;
    },
  });
}

export function useCalculateMileage() {
  return useMutation({
    mutationFn: async (data: {
      departure: string;
      arrival: string;
      vehicle_type: VehicleType;
      is_round_trip?: boolean;
    }) => {
      return api.post<{
        distance_km: number;
        rate_per_km: number;
        total_amount: number;
        route_details?: Record<string, unknown>;
      }>('/expenses/mileage/calculate', data);
    },
  });
}

// ============================================================================
// HOOKS - POLICIES
// ============================================================================

export function useExpensePolicies() {
  return useQuery({
    queryKey: expensesKeys.policies(),
    queryFn: async () => {
      const response = await api.get<{ items: ExpensePolicy[] }>('/expenses/policies');
      return response;
    },
  });
}

export function useCheckPolicyCompliance() {
  return useMutation({
    mutationFn: async (data: {
      category: ExpenseCategory;
      amount: number;
      has_receipt: boolean;
    }) => {
      return api.post<{
        compliant: boolean;
        violations: string[];
        requires_approval: boolean;
      }>('/expenses/policies/check', data);
    },
  });
}

// ============================================================================
// HOOKS - STATS
// ============================================================================

export function useExpenseStats(filters?: { from_date?: string; to_date?: string }) {
  return useQuery({
    queryKey: [...expensesKeys.stats(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const response = await api.get<ExpenseStats>(
        `/expenses/stats${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}
