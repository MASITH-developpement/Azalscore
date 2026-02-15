/**
 * AZALSCORE - Hooks Workflow Interventions
 * Mutations pour valider, demarrer, terminer, bloquer, debloquer et annuler.
 *
 * Page : /interventions
 * State machine 7 états : DRAFT → A_PLANIFIER → PLANIFIEE → EN_COURS → TERMINEE
 *                                                              ↓
 *                                                          BLOQUEE
 *                         Tout état actif → ANNULEE
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../core/api-client';

export const useValiderIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/v3/interventions/${id}/valider`, {});
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
      return api.post(`/v3/interventions/${id}/arrivee`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const useTerminerIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/v3/interventions/${id}/terminer`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const useBloquerIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, motif }: { id: string; motif: string }) => {
      return api.post(`/v3/interventions/${id}/bloquer`, { motif });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const useDebloquerIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/v3/interventions/${id}/debloquer`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const useAnnulerIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/v3/interventions/${id}/annuler`, {});
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};
