/**
 * AZALSCORE - Timesheet API
 * =========================
 * Complete typed API client for Timesheet (Time & Activity Management) module.
 * Covers: Time Entries, Timesheets, Absences, Overtime, Timers, Leave Balances
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const timesheetKeys = {
  all: ['timesheet'] as const,
  entries: () => [...timesheetKeys.all, 'entries'] as const,
  entry: (id: string) => [...timesheetKeys.entries(), id] as const,
  timesheets: () => [...timesheetKeys.all, 'timesheets'] as const,
  timesheet: (id: string) => [...timesheetKeys.timesheets(), id] as const,
  absences: () => [...timesheetKeys.all, 'absences'] as const,
  timers: () => [...timesheetKeys.all, 'timers'] as const,
  leaveBalances: () => [...timesheetKeys.all, 'leave-balances'] as const,
  overtime: () => [...timesheetKeys.all, 'overtime'] as const,
  schedules: () => [...timesheetKeys.all, 'schedules'] as const,
  stats: () => [...timesheetKeys.all, 'stats'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type TimeEntryType =
  | 'work' | 'break' | 'meeting' | 'training'
  | 'travel' | 'remote' | 'on_call' | 'overtime';

export type AbsenceType =
  | 'vacation' | 'sick_leave' | 'family_leave' | 'maternity' | 'paternity'
  | 'bereavement' | 'unpaid_leave' | 'compensatory' | 'training'
  | 'public_holiday' | 'rtt' | 'other';

export type TimesheetStatus =
  | 'draft' | 'submitted' | 'pending_approval'
  | 'approved' | 'rejected' | 'locked';

export type WorkScheduleType =
  | 'full_time_35h' | 'full_time_39h' | 'part_time'
  | 'shift' | 'flexible' | 'compressed' | 'custom';

export type OvertimeType =
  | 'standard' | 'night' | 'weekend' | 'holiday' | 'on_call';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface TimeEntry {
  id: string;
  tenant_id: string;
  user_id: string;
  date: string;
  start_time: string;
  end_time?: string | null;
  duration_minutes?: number | null;
  entry_type: TimeEntryType;
  project_id?: string | null;
  project_name?: string | null;
  task_id?: string | null;
  task_name?: string | null;
  client_id?: string | null;
  client_name?: string | null;
  description?: string | null;
  billable: boolean;
  billed: boolean;
  hourly_rate?: number | null;
  is_overtime: boolean;
  overtime_type?: OvertimeType | null;
  overtime_multiplier?: number | null;
  location?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Timesheet {
  id: string;
  tenant_id: string;
  user_id: string;
  user_name: string;
  period_start: string;
  period_end: string;
  period_type: 'weekly' | 'biweekly' | 'monthly';
  status: TimesheetStatus;
  total_hours: number;
  regular_hours: number;
  overtime_hours: number;
  billable_hours: number;
  absence_hours: number;
  submitted_at?: string | null;
  approved_at?: string | null;
  approved_by?: string | null;
  rejection_reason?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AbsenceEntry {
  id: string;
  tenant_id: string;
  user_id: string;
  absence_type: AbsenceType;
  start_date: string;
  end_date: string;
  start_half_day: boolean;
  end_half_day: boolean;
  total_days: number;
  reason?: string | null;
  status: 'pending' | 'approved' | 'rejected' | 'cancelled';
  approved_by?: string | null;
  approved_at?: string | null;
  certificate_required: boolean;
  certificate_uploaded: boolean;
  certificate_path?: string | null;
  created_at: string;
}

export interface Timer {
  id: string;
  tenant_id: string;
  user_id: string;
  project_id?: string | null;
  task_id?: string | null;
  description?: string | null;
  started_at: string;
  paused_at?: string | null;
  total_paused_seconds: number;
  is_running: boolean;
  entry_type: TimeEntryType;
  billable: boolean;
}

export interface LeaveBalance {
  user_id: string;
  year: number;
  vacation_total: number;
  vacation_used: number;
  vacation_pending: number;
  vacation_remaining: number;
  sick_leave_used: number;
  rtt_total: number;
  rtt_used: number;
  rtt_remaining: number;
  compensatory_balance: number;
  carry_over: number;
  expiring_soon: number;
  expiry_date?: string | null;
}

export interface WorkSchedule {
  id: string;
  tenant_id: string;
  user_id: string;
  schedule_type: WorkScheduleType;
  weekly_hours: number;
  monday_hours: number;
  tuesday_hours: number;
  wednesday_hours: number;
  thursday_hours: number;
  friday_hours: number;
  saturday_hours: number;
  sunday_hours: number;
  start_date: string;
  end_date?: string | null;
  is_active: boolean;
}

export interface OvertimeCalculation {
  user_id: string;
  period_start: string;
  period_end: string;
  regular_hours: number;
  overtime_hours: number;
  overtime_breakdown: {
    standard: number;
    night: number;
    weekend: number;
    holiday: number;
  };
  compensatory_earned: number;
  overtime_pay: number;
}

export interface TimesheetStats {
  total_hours_this_week: number;
  total_hours_this_month: number;
  billable_hours_this_month: number;
  overtime_hours_this_month: number;
  average_daily_hours: number;
  by_project: Array<{ project_id: string; project_name: string; hours: number }>;
  by_client: Array<{ client_id: string; client_name: string; hours: number }>;
  pending_approval_count: number;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface TimeEntryCreate {
  date: string;
  start_time: string;
  end_time?: string;
  duration_minutes?: number;
  entry_type?: TimeEntryType;
  project_id?: string;
  task_id?: string;
  client_id?: string;
  description?: string;
  billable?: boolean;
  hourly_rate?: number;
  location?: string;
}

export interface TimeEntryUpdate {
  date?: string;
  start_time?: string;
  end_time?: string;
  duration_minutes?: number;
  entry_type?: TimeEntryType;
  project_id?: string;
  task_id?: string;
  description?: string;
  billable?: boolean;
}

export interface AbsenceCreate {
  absence_type: AbsenceType;
  start_date: string;
  end_date: string;
  start_half_day?: boolean;
  end_half_day?: boolean;
  reason?: string;
}

export interface TimesheetSubmit {
  notes?: string;
}

// ============================================================================
// HOOKS - TIME ENTRIES
// ============================================================================

export function useTimeEntries(filters?: {
  user_id?: string;
  date?: string;
  from_date?: string;
  to_date?: string;
  project_id?: string;
  client_id?: string;
  entry_type?: TimeEntryType;
  billable?: boolean;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...timesheetKeys.entries(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.date) params.append('date', filters.date);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.project_id) params.append('project_id', filters.project_id);
      if (filters?.client_id) params.append('client_id', filters.client_id);
      if (filters?.entry_type) params.append('entry_type', filters.entry_type);
      if (filters?.billable !== undefined) params.append('billable', String(filters.billable));
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: TimeEntry[]; total: number }>(
        `/timesheet/entries${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useTimeEntry(id: string) {
  return useQuery({
    queryKey: timesheetKeys.entry(id),
    queryFn: async () => {
      const response = await api.get<TimeEntry>(`/timesheet/entries/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateTimeEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TimeEntryCreate) => {
      return api.post<TimeEntry>('/timesheet/entries', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.entries() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.stats() });
    },
  });
}

export function useUpdateTimeEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TimeEntryUpdate }) => {
      return api.put<TimeEntry>(`/timesheet/entries/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.entries() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.entry(id) });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.stats() });
    },
  });
}

export function useDeleteTimeEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/timesheet/entries/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.entries() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.stats() });
    },
  });
}

// ============================================================================
// HOOKS - TIMESHEETS
// ============================================================================

export function useTimesheets(filters?: {
  user_id?: string;
  status?: TimesheetStatus;
  period_type?: 'weekly' | 'biweekly' | 'monthly';
  from_date?: string;
  to_date?: string;
}) {
  return useQuery({
    queryKey: [...timesheetKeys.timesheets(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.period_type) params.append('period_type', filters.period_type);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const response = await api.get<{ items: Timesheet[] }>(
        `/timesheet/timesheets${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useTimesheet(id: string) {
  return useQuery({
    queryKey: timesheetKeys.timesheet(id),
    queryFn: async () => {
      const response = await api.get<Timesheet>(`/timesheet/timesheets/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCurrentTimesheet() {
  return useQuery({
    queryKey: [...timesheetKeys.timesheets(), 'current'],
    queryFn: async () => {
      const response = await api.get<Timesheet>('/timesheet/timesheets/current');
      return response;
    },
  });
}

export function useSubmitTimesheet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data?: TimesheetSubmit }) => {
      return api.post(`/timesheet/timesheets/${id}/submit`, data ?? {});
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timesheets() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timesheet(id) });
    },
  });
}

export function useApproveTimesheet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes?: string }) => {
      return api.post(`/timesheet/timesheets/${id}/approve`, { notes });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timesheets() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timesheet(id) });
    },
  });
}

export function useRejectTimesheet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.post(`/timesheet/timesheets/${id}/reject`, { reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timesheets() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timesheet(id) });
    },
  });
}

// ============================================================================
// HOOKS - ABSENCES
// ============================================================================

export function useAbsences(filters?: {
  user_id?: string;
  absence_type?: AbsenceType;
  status?: string;
  from_date?: string;
  to_date?: string;
}) {
  return useQuery({
    queryKey: [...timesheetKeys.absences(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.absence_type) params.append('absence_type', filters.absence_type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const response = await api.get<{ items: AbsenceEntry[] }>(
        `/timesheet/absences${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCreateAbsence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: AbsenceCreate) => {
      return api.post<AbsenceEntry>('/timesheet/absences', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.absences() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.leaveBalances() });
    },
  });
}

export function useCancelAbsence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/timesheet/absences/${id}/cancel`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.absences() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.leaveBalances() });
    },
  });
}

export function useApproveAbsence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/timesheet/absences/${id}/approve`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.absences() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.leaveBalances() });
    },
  });
}

export function useRejectAbsence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.post(`/timesheet/absences/${id}/reject`, { reason });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.absences() });
    },
  });
}

// ============================================================================
// HOOKS - TIMERS
// ============================================================================

export function useActiveTimer() {
  return useQuery({
    queryKey: [...timesheetKeys.timers(), 'active'],
    queryFn: async () => {
      const response = await api.get<Timer | null>('/timesheet/timers/active');
      return response;
    },
  });
}

export function useStartTimer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      project_id?: string;
      task_id?: string;
      description?: string;
      entry_type?: TimeEntryType;
      billable?: boolean;
    }) => {
      return api.post<Timer>('/timesheet/timers/start', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timers() });
    },
  });
}

export function usePauseTimer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Timer>(`/timesheet/timers/${id}/pause`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timers() });
    },
  });
}

export function useResumeTimer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Timer>(`/timesheet/timers/${id}/resume`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timers() });
    },
  });
}

export function useStopTimer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<TimeEntry>(`/timesheet/timers/${id}/stop`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timers() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.entries() });
      queryClient.invalidateQueries({ queryKey: timesheetKeys.stats() });
    },
  });
}

export function useDiscardTimer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/timesheet/timers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: timesheetKeys.timers() });
    },
  });
}

// ============================================================================
// HOOKS - LEAVE BALANCES
// ============================================================================

export function useLeaveBalances(userId?: string, year?: number) {
  return useQuery({
    queryKey: [...timesheetKeys.leaveBalances(), userId, year],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      if (year) params.append('year', String(year));
      const queryString = params.toString();
      const response = await api.get<LeaveBalance>(
        `/timesheet/leave-balances${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

// ============================================================================
// HOOKS - OVERTIME
// ============================================================================

export function useOvertimeCalculation(filters: {
  user_id?: string;
  period_start: string;
  period_end: string;
}) {
  return useQuery({
    queryKey: [...timesheetKeys.overtime(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.user_id) params.append('user_id', filters.user_id);
      params.append('period_start', filters.period_start);
      params.append('period_end', filters.period_end);
      const response = await api.get<OvertimeCalculation>(
        `/timesheet/overtime?${params.toString()}`
      );
      return response;
    },
    enabled: !!filters.period_start && !!filters.period_end,
  });
}

// ============================================================================
// HOOKS - WORK SCHEDULES
// ============================================================================

export function useWorkSchedule(userId?: string) {
  return useQuery({
    queryKey: [...timesheetKeys.schedules(), userId],
    queryFn: async () => {
      const params = userId ? `?user_id=${userId}` : '';
      const response = await api.get<WorkSchedule>(`/timesheet/schedules${params}`);
      return response;
    },
  });
}

// ============================================================================
// HOOKS - STATS
// ============================================================================

export function useTimesheetStats(filters?: { user_id?: string; from_date?: string; to_date?: string }) {
  return useQuery({
    queryKey: [...timesheetKeys.stats(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const response = await api.get<TimesheetStats>(
        `/timesheet/stats${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

// ============================================================================
// HOOKS - EXPORT
// ============================================================================

export function useExportTimesheet() {
  return useMutation({
    mutationFn: async (data: {
      timesheet_id?: string;
      user_id?: string;
      from_date: string;
      to_date: string;
      format: 'csv' | 'excel' | 'pdf';
    }) => {
      return api.post<Blob>('/timesheet/export', data, { responseType: 'blob' });
    },
  });
}
