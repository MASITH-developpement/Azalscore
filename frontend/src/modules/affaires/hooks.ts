/**
 * AZALSCORE - Affaires React Query Hooks
 * =======================================
 * Hooks pour le module Affaires (projets simplifiés)
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { unwrapApiResponse } from '@/types';

// ============================================================================
// TYPES
// ============================================================================

type Status = 'draft' | 'planning' | 'in_progress' | 'on_hold' | 'completed' | 'cancelled';
type Priority = 'low' | 'medium' | 'high' | 'critical';

interface Affaire {
  id: string;
  reference?: string;
  code?: string;
  name: string;
  description?: string;
  customer_id?: string;
  customer_name?: string;
  status: Status;
  priority: Priority;
  progress_percent?: number;
  planned_budget?: number;
  actual_cost?: number;
  planned_start_date?: string;
  planned_end_date?: string;
}

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const affairesKeys = {
  all: ['affaires'] as const,
  list: (search?: string) => [...affairesKeys.all, { search }] as const,
  detail: (id: string) => [...affairesKeys.all, 'detail', id] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

export const useAffaires = (search?: string) => {
  return useQuery({
    queryKey: affairesKeys.list(search),
    queryFn: async () => {
      const params = search ? `?search=${search}&limit=100` : '?limit=100';
      const res = await api.get<{ items: Affaire[] }>(`/projects${params}`);
      const data = unwrapApiResponse<{ items: Affaire[] }>(res);
      return data?.items || [];
    },
  });
};

export const useAffaire = (id?: string) => {
  return useQuery({
    queryKey: affairesKeys.detail(id || ''),
    queryFn: async () => {
      const res = await api.get<Affaire>(`/projects/${id}`);
      return unwrapApiResponse<Affaire>(res);
    },
    enabled: !!id,
  });
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

export const useSaveAffaire = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id?: string; data: Partial<Affaire> }): Promise<Affaire> => {
      const payload = id ? data : {
        ...data,
        code: data.code || `AFF-${Date.now().toString(36).toUpperCase()}`,
      };
      const res = id
        ? await api.put<Affaire>(`/projects/${id}`, payload)
        : await api.post<Affaire>('/projects', payload);
      const result = unwrapApiResponse<Affaire>(res);
      if (!result) throw new Error('No data returned from API');
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: affairesKeys.all });
    },
  });
};

export const useDeleteAffaire = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/projects/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: affairesKeys.all });
    },
  });
};
