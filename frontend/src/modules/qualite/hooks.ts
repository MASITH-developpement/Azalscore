/**
 * AZALSCORE - Qualite React Query Hooks
 * ======================================
 * Hooks pour le module Qualite (NC, regles QC, inspections)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { NonConformance, QCRule, QCInspection, QualityDashboard } from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const qualityKeys = {
  all: ['quality'] as const,

  // Dashboard
  dashboard: () => [...qualityKeys.all, 'dashboard'] as const,

  // Non-conformances
  ncs: () => [...qualityKeys.all, 'non-conformances'] as const,
  ncsList: (filters?: { type?: string; status?: string; severity?: string }) =>
    [...qualityKeys.ncs(), serializeFilters(filters)] as const,
  ncDetail: (id: string) => [...qualityKeys.ncs(), id] as const,

  // QC Rules
  rules: () => ['qc', 'rules'] as const,
  rulesList: (filters?: { type?: string }) =>
    [...qualityKeys.rules(), serializeFilters(filters)] as const,

  // Inspections
  inspections: () => ['qc', 'inspections'] as const,
  inspectionsList: (filters?: { type?: string; status?: string }) =>
    [...qualityKeys.inspections(), serializeFilters(filters)] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export const useQualityDashboard = () => {
  return useQuery({
    queryKey: qualityKeys.dashboard(),
    queryFn: async () => {
      return api.get<QualityDashboard>('/quality/dashboard').then(r => r.data);
    },
  });
};

// ============================================================================
// NON-CONFORMANCE HOOKS
// ============================================================================

export const useNonConformances = (filters?: { type?: string; status?: string; severity?: string }) => {
  return useQuery({
    queryKey: qualityKeys.ncsList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.severity) params.append('severity', filters.severity);
      const query = params.toString();
      return api.get<NonConformance[]>(`/quality/non-conformances${query ? `?${query}` : ''}`).then(r => r.data);
    },
  });
};

export const useNonConformance = (id: string) => {
  return useQuery({
    queryKey: qualityKeys.ncDetail(id),
    queryFn: async () => {
      return api.get<NonConformance>(`/quality/non-conformances/${id}`).then(r => r.data);
    },
    enabled: !!id,
  });
};

export const useCreateNonConformance = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<NonConformance>) => {
      return api.post<NonConformance>('/quality/non-conformances', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: qualityKeys.all }),
  });
};

export const useUpdateNCStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/quality/non-conformances/${id}`, { status }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: qualityKeys.all }),
  });
};

export const useCloseNC = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/quality/non-conformances/${id}/close`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: qualityKeys.all }),
  });
};

// ============================================================================
// QC RULES HOOKS
// ============================================================================

export const useQCRules = (filters?: { type?: string }) => {
  return useQuery({
    queryKey: qualityKeys.rulesList(filters),
    queryFn: async () => {
      const query = filters?.type ? `?type=${encodeURIComponent(filters.type)}` : '';
      return api.get<QCRule[]>(`/qc/rules${query}`).then(r => r.data);
    },
  });
};

// ============================================================================
// INSPECTION HOOKS
// ============================================================================

export const useQCInspections = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: qualityKeys.inspectionsList(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const query = params.toString();
      return api.get<QCInspection[]>(`/qc/inspections${query ? `?${query}` : ''}`).then(r => r.data);
    },
  });
};
