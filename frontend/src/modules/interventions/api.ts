/**
 * AZALSCORE Module - INTERVENTIONS API (AZA-FE-003)
 * ==================================================
 *
 * Couche API du module Interventions.
 * Tous les hooks React Query et appels API sont centralisés ici.
 *
 * Contrat module : page.tsx + api.ts + index.ts
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import type { Intervention, DonneurOrdre, InterventionStats, AnalyseIA } from './types';

// ============================================================================
// QUERY KEYS (centralised for cache management)
// ============================================================================

export const interventionKeys = {
  all: ['interventions'] as const,
  lists: () => [...interventionKeys.all, 'list'] as const,
  list: (filters?: Record<string, string | undefined>) => [...interventionKeys.lists(), filters] as const,
  details: () => [...interventionKeys.all, 'detail'] as const,
  detail: (id: string) => [...interventionKeys.details(), id] as const,
  analyseIA: (id: string) => [...interventionKeys.details(), id, 'analyse-ia'] as const,
  stats: () => [...interventionKeys.all, 'stats'] as const,
  donneursOrdre: () => [...interventionKeys.all, 'donneurs-ordre'] as const,
  clients: () => ['clients'] as const,
  intervenants: () => ['intervenants'] as const,
};

// ============================================================================
// HOOKS - STATISTIQUES
// ============================================================================

export const useInterventionStats = () => {
  return useQuery({
    queryKey: interventionKeys.stats(),
    queryFn: async () => {
      const response = await api.get<InterventionStats>('/v2/interventions/stats');
      return response as unknown as InterventionStats;
    },
  });
};

// ============================================================================
// HOOKS - INTERVENTIONS
// ============================================================================

export const useInterventions = (filters?: {
  statut?: string;
  type_intervention?: string;
  priorite?: string;
  client_id?: string;
}) => {
  return useQuery({
    queryKey: interventionKeys.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.statut) params.append('statut', filters.statut);
      if (filters?.type_intervention) params.append('type_intervention', filters.type_intervention);
      if (filters?.priorite) params.append('priorite', filters.priorite);
      if (filters?.client_id) params.append('client_id', filters.client_id);
      const queryString = params.toString();
      const url = `/v2/interventions${queryString ? `?${queryString}` : ''}`;
      const response = await api.get<{ items: Intervention[]; total: number }>(url);
      return (response as any)?.items || [];
    },
  });
};

export const useCreateIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Intervention>) => {
      return api.post('/v2/interventions', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: interventionKeys.all });
    },
  });
};

export const useUpdateIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Intervention> }) => {
      return api.put(`/v2/interventions/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: interventionKeys.all });
    },
  });
};

export const useDeleteIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/v2/interventions/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: interventionKeys.all });
    },
  });
};

// ============================================================================
// HOOKS - DONNEURS D'ORDRE
// ============================================================================

export const useDonneursOrdre = () => {
  return useQuery({
    queryKey: interventionKeys.donneursOrdre(),
    queryFn: async () => {
      const response = await api.get<DonneurOrdre[]>('/v2/interventions/donneurs-ordre');
      return response as unknown as DonneurOrdre[];
    },
  });
};

export const useUpdateDonneurOrdre = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<DonneurOrdre> }) => {
      return api.put(`/v2/interventions/donneurs-ordre/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: interventionKeys.donneursOrdre() });
    },
  });
};

export const useDeleteDonneurOrdre = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/v2/interventions/donneurs-ordre/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: interventionKeys.donneursOrdre() });
    },
  });
};

// ============================================================================
// HOOKS - ENTITÉS EXTERNES (via API, pas d'accès direct)
// ============================================================================

export const useClients = () => {
  return useQuery({
    queryKey: interventionKeys.clients(),
    queryFn: async () => {
      const response = await api.get<{ items: { id: string; name: string; code?: string }[] }>('/v1/commercial/customers');
      return (response as any)?.items || [];
    },
  });
};

export const useIntervenants = () => {
  return useQuery({
    queryKey: interventionKeys.intervenants(),
    queryFn: async () => {
      const response = await api.get<{ items: { id: string; first_name: string; last_name: string }[] }>('/v1/hr/employees');
      return (response as any)?.items || [];
    },
  });
};

// ============================================================================
// HOOKS - ANALYSE IA
// ============================================================================

export const useAnalyseIA = (interventionId: string | undefined) => {
  return useQuery({
    queryKey: interventionKeys.analyseIA(interventionId!),
    queryFn: async () => {
      const response = await api.get<AnalyseIA>(`/v2/interventions/${interventionId}/analyse-ia`);
      return response as unknown as AnalyseIA;
    },
    enabled: !!interventionId,
  });
};
