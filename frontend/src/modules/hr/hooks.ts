/**
 * AZALSCORE Module - HR - Hooks
 * React Query hooks pour le module Ressources Humaines
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type {
  Department, Position, Employee, LeaveRequest, TimeEntry, HRDashboard
} from './types';

// ============================================================================
// HELPERS
// ============================================================================

const buildUrlWithParams = (baseUrl: string, params?: Record<string, string | undefined>): string => {
  if (!params) return baseUrl;
  const filteredParams = Object.entries(params).filter(([_, v]) => v !== undefined);
  if (filteredParams.length === 0) return baseUrl;
  const queryString = filteredParams.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v!)}`).join('&');
  return `${baseUrl}?${queryString}`;
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

/**
 * Hook pour le dashboard RH
 */
export const useHRDashboard = () => {
  return useQuery<HRDashboard | null, Error>({
    queryKey: ['hr', 'dashboard'],
    queryFn: async (): Promise<HRDashboard | null> => {
      const response = await api.get<HRDashboard | { data: HRDashboard }>('/hr/dashboard');
      const res = response as HRDashboard | { data?: HRDashboard; pending_leave_requests?: number };
      if ('pending_leave_requests' in res && res.pending_leave_requests !== undefined) {
        return res as HRDashboard;
      }
      if ('data' in res && res.data?.pending_leave_requests !== undefined) {
        return res.data as HRDashboard;
      }
      return res as HRDashboard || null;
    }
  });
};

/**
 * Hook pour la liste des departements
 */
export const useDepartments = () => {
  return useQuery({
    queryKey: ['hr', 'departments'],
    queryFn: async () => {
      const response = await api.get<{ data: Department[] } | Department[]>('/hr/departments');
      if (Array.isArray(response)) {
        return response;
      }
      if (response && typeof response === 'object' && 'data' in response) {
        return Array.isArray(response.data) ? response.data : [];
      }
      return [];
    }
  });
};

/**
 * Hook pour la liste des postes
 */
export const usePositions = () => {
  return useQuery({
    queryKey: ['hr', 'positions'],
    queryFn: async () => {
      const response = await api.get<{ data: Position[] } | Position[]>('/hr/positions');
      if (Array.isArray(response)) {
        return response;
      }
      if (response && typeof response === 'object' && 'data' in response) {
        return Array.isArray(response.data) ? response.data : [];
      }
      return [];
    }
  });
};

/**
 * Hook pour la liste des employes
 */
export const useEmployees = (filters?: { department_id?: string; status?: string; contract_type?: string }) => {
  return useQuery<Employee[], Error>({
    queryKey: ['hr', 'employees', serializeFilters(filters)],
    queryFn: async (): Promise<Employee[]> => {
      const url = buildUrlWithParams('/hr/employees', filters);
      const response = await api.get<{ items?: Employee[]; data?: { items?: Employee[] } }>(url);
      const res = response as { items?: Employee[]; data?: { items?: Employee[] } };
      if (res?.items) {
        return res.items;
      }
      if (res?.data?.items) {
        return res.data.items;
      }
      return [];
    }
  });
};

/**
 * Hook pour un employe specifique
 */
export const useEmployee = (id: string) => {
  return useQuery<Employee | null, Error>({
    queryKey: ['hr', 'employee', id],
    queryFn: async (): Promise<Employee | null> => {
      const response = await api.get<Employee | { data: Employee }>(`/hr/employees/${id}`);
      const res = response as Employee | { data?: Employee; id?: string };
      if ('data' in res && res.data) {
        return res.data;
      }
      if ('id' in res && res.id) {
        return res as Employee;
      }
      return null;
    },
    enabled: !!id
  });
};

/**
 * Hook pour les demandes de conges
 */
export const useLeaveRequests = (filters?: { status?: string; type?: string }) => {
  return useQuery<LeaveRequest[], Error>({
    queryKey: ['hr', 'leave-requests', serializeFilters(filters)],
    queryFn: async (): Promise<LeaveRequest[]> => {
      const url = buildUrlWithParams('/hr/leave-requests', filters);
      const response = await api.get<{ items?: LeaveRequest[]; data?: { items?: LeaveRequest[] } }>(url);
      const res = response as { items?: LeaveRequest[]; data?: { items?: LeaveRequest[] } };
      if (res?.items) {
        return res.items;
      }
      if (res?.data?.items) {
        return res.data.items;
      }
      return [];
    }
  });
};

/**
 * Hook pour les entrees de temps
 */
export const useTimeEntries = (filters?: { employee_id?: string; from_date?: string; to_date?: string }) => {
  return useQuery({
    queryKey: ['hr', 'time-entries', serializeFilters(filters)],
    queryFn: async () => {
      const url = buildUrlWithParams('/hr/time-entries', filters);
      const response = await api.get<TimeEntry[] | { items: TimeEntry[] }>(url).then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

// Alias pour compatibilite
export const useTimesheets = useTimeEntries;

// ============================================================================
// MUTATION HOOKS - EMPLOYEES
// ============================================================================

/**
 * Hook pour creer un employe
 */
export const useCreateEmployee = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Employee>) => {
      return api.post<Employee>('/hr/employees', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

/**
 * Hook pour modifier un employe
 */
export const useUpdateEmployee = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Employee> }) => {
      const response = await api.put<Employee | { data: Employee }>(`/hr/employees/${id}`, data);
      const res = response as Employee | { data?: Employee };
      return ('data' in res && res.data) ? res.data : res;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

/**
 * Hook pour supprimer un employe
 */
export const useDeleteEmployee = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/hr/employees/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

// ============================================================================
// MUTATION HOOKS - DEPARTMENTS
// ============================================================================

/**
 * Hook pour creer un departement
 */
export const useCreateDepartment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Department>) => {
      return api.post<Department>('/hr/departments', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'departments'] })
  });
};

/**
 * Hook pour modifier un departement
 */
export const useUpdateDepartment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Department> }) => {
      const response = await api.put<Department | { data: Department }>(`/hr/departments/${id}`, data);
      const res = response as Department | { data?: Department };
      return ('data' in res && res.data) ? res.data : res;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'departments'] })
  });
};

/**
 * Hook pour supprimer un departement
 */
export const useDeleteDepartment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/hr/departments/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'departments'] })
  });
};

// ============================================================================
// MUTATION HOOKS - POSITIONS
// ============================================================================

/**
 * Hook pour creer un poste
 */
export const useCreatePosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Position>) => {
      return api.post<Position>('/hr/positions', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'positions'] })
  });
};

/**
 * Hook pour modifier un poste
 */
export const useUpdatePosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Position> }) => {
      const response = await api.put<Position | { data: Position }>(`/hr/positions/${id}`, data);
      const res = response as Position | { data?: Position };
      return ('data' in res && res.data) ? res.data : res;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'positions'] })
  });
};

/**
 * Hook pour supprimer un poste
 */
export const useDeletePosition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/hr/positions/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'positions'] })
  });
};

// ============================================================================
// MUTATION HOOKS - LEAVE REQUESTS
// ============================================================================

export interface LeaveRequestCreateData {
  employee_id: string;
  type: string;
  start_date: string;
  end_date: string;
  reason?: string;
}

export interface LeaveRequestUpdateData {
  type?: string;
  start_date?: string;
  end_date?: string;
  half_day_start?: boolean;
  half_day_end?: boolean;
  reason?: string;
  resubmit?: boolean;
}

/**
 * Hook pour creer une demande de conge
 */
export const useCreateLeaveRequest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: LeaveRequestCreateData) => {
      const response = await api.post<LeaveRequest>('/hr/leave-requests', data);
      return (response as { data?: LeaveRequest }).data || response;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'leave-requests'] })
  });
};

/**
 * Hook pour modifier une demande de conge
 */
export const useUpdateLeaveRequest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: LeaveRequestUpdateData }) => {
      const response = await api.put<LeaveRequest | { data: LeaveRequest }>(`/hr/leave-requests/${id}`, data);
      const res = response as LeaveRequest | { data?: LeaveRequest };
      return ('data' in res && res.data) ? res.data : res;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

/**
 * Hook pour approuver une demande de conge
 */
export const useApproveLeave = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<LeaveRequest | { data: LeaveRequest }>(`/hr/leave-requests/${id}/approve`);
      const res = response as LeaveRequest | { data?: LeaveRequest };
      return ('data' in res && res.data) ? res.data : res;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

/**
 * Hook pour refuser une demande de conge
 */
export const useRejectLeave = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      const response = await api.post<LeaveRequest | { data: LeaveRequest }>(`/hr/leave-requests/${id}/reject?rejection_reason=${encodeURIComponent(reason)}`);
      const res = response as LeaveRequest | { data?: LeaveRequest };
      return ('data' in res && res.data) ? res.data : res;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr'] })
  });
};

// ============================================================================
// MUTATION HOOKS - TIME ENTRIES
// ============================================================================

export interface TimeEntryCreateData {
  date: string;
  start_time?: string;
  end_time?: string;
  break_duration?: number;
  worked_hours: number;
  overtime_hours?: number;
  project_id?: string;
  task_description?: string;
}

/**
 * Hook pour creer une entree de temps
 */
export const useCreateTimeEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ employee_id, data }: { employee_id: string; data: TimeEntryCreateData }) => {
      return api.post<TimeEntry>(`/hr/employees/${employee_id}/time-entries`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['hr', 'time-entries'] })
  });
};
