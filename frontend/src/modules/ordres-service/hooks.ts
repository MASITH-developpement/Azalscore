/**
 * AZALSCORE Module - ORDRES DE SERVICE - Hooks
 * React Query hooks pour l'API Interventions
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { PaginatedResponse } from '@/types';
import type { Intervention, DonneurOrdre, InterventionStats } from './types';

// ============================================================
// TYPES LOCAUX
// ============================================================

interface Client {
  id: string;
  code: string;
  name: string;
}

interface Intervenant {
  id: string;
  first_name: string;
  last_name: string;
}

// ============================================================
// QUERY HOOKS
// ============================================================

export const useInterventionsList = (page = 1, pageSize = 25, filters?: { statut?: string; priorite?: string; search?: string }) => {
  return useQuery({
    queryKey: ['interventions', page, pageSize, serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
      if (filters?.statut) params.append('statut', filters.statut);
      if (filters?.priorite) params.append('priorite', filters.priorite);
      if (filters?.search) params.append('search', filters.search);
      const response = await api.get<PaginatedResponse<Intervention>>(`/interventions?${params}`);
      return response.data;
    },
  });
};

export const useIntervention = (id: string) => {
  return useQuery({
    queryKey: ['interventions', id],
    queryFn: async () => {
      const response = await api.get<Intervention>(`/interventions/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useInterventionStats = () => {
  return useQuery({
    queryKey: ['interventions', 'stats'],
    queryFn: async () => {
      const response = await api.get<InterventionStats>('/interventions/stats');
      return response.data;
    },
  });
};

export const useDonneursOrdre = () => {
  return useQuery({
    queryKey: ['interventions', 'donneurs-ordre'],
    queryFn: async () => {
      const response = await api.get<DonneurOrdre[]>('/interventions/donneurs-ordre');
      return response.data;
    },
  });
};

export const useClients = () => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await api.get<Client[] | { items: Client[] }>('/crm/customers');
      const data = response.data;
      return Array.isArray(data) ? data : (data?.items || []);
    },
  });
};

export const useIntervenants = () => {
  return useQuery({
    queryKey: ['intervenants'],
    queryFn: async () => {
      const response = await api.get<Intervenant[] | { items: Intervenant[] }>('/hr/employees');
      const data = response.data;
      return Array.isArray(data) ? data : (data?.items || []);
    },
  });
};

// ============================================================
// MUTATIONS - DONNEURS D'ORDRE
// ============================================================

export const useCreateDonneurOrdre = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<DonneurOrdre>) => {
      const response = await api.post<DonneurOrdre>('/interventions/donneurs-ordre', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions', 'donneurs-ordre'] });
    },
  });
};

export const useUpdateDonneurOrdre = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<DonneurOrdre> }) => {
      const response = await api.put<DonneurOrdre>(`/interventions/donneurs-ordre/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions', 'donneurs-ordre'] });
    },
  });
};

export const useDeleteDonneurOrdre = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/interventions/donneurs-ordre/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions', 'donneurs-ordre'] });
    },
  });
};

// ============================================================
// MUTATIONS - INTERVENTIONS
// ============================================================

export const useDeleteIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/interventions/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const useCreateIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Intervention>) => {
      const response = await api.post<Intervention>('/interventions', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const useUpdateIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Intervention> }) => {
      const response = await api.put<Intervention>(`/interventions/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const useDemarrerIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Intervention>(`/interventions/${id}/demarrer`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const useTerminerIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { commentaire_cloture?: string; montant_reel?: number } }) => {
      const response = await api.post<Intervention>(`/interventions/${id}/terminer`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};
