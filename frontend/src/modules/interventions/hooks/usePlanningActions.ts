/**
 * AZALSCORE - Hooks Planning Interventions
 * Mutations pour planifier, modifier et annuler la planification.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../../core/api-client';

interface PlanificationData {
  date_prevue_debut: string;
  date_prevue_fin: string;
  intervenant_id: string;
}

export const usePlanifierIntervention = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PlanificationData }) => {
      return api.post(`/interventions/${id}/planifier`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const useModifierPlanification = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PlanificationData }) => {
      return api.put(`/interventions/${id}/planification`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const useAnnulerPlanification = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/interventions/${id}/planification`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interventions'] });
    },
  });
};

export const buildPlanificationData = (
  targetDate: Date,
  intervenantId: string,
  dureePrevueMinutes?: number
): PlanificationData => {
  const debut = new Date(targetDate);
  debut.setHours(8, 0, 0, 0);

  const fin = new Date(targetDate);
  if (dureePrevueMinutes && dureePrevueMinutes > 0) {
    fin.setHours(8, 0, 0, 0);
    fin.setMinutes(fin.getMinutes() + dureePrevueMinutes);
  } else {
    fin.setHours(17, 0, 0, 0);
  }

  return {
    date_prevue_debut: debut.toISOString(),
    date_prevue_fin: fin.toISOString(),
    intervenant_id: intervenantId,
  };
};
