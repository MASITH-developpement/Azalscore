/**
 * AZALSCORE - Break-Glass React Query Hooks
 * ==========================================
 * Hooks pour le module Break-Glass Souverain
 *
 * IMPORTANT: Ce module est réservé aux situations d'urgence absolue.
 * Toutes les actions sont journalisées de manière inviolable.
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import {
  breakGlassApi,
  type BreakGlassScope,
  type BreakGlassRequest,
} from './api';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const breakGlassKeys = {
  all: ['break-glass'] as const,
  tenants: () => [...breakGlassKeys.all, 'tenants'] as const,
  modules: () => [...breakGlassKeys.all, 'modules'] as const,
};

// ============================================================================
// CHALLENGE & EXECUTION HOOKS
// ============================================================================

export const useBreakGlassChallenge = () => {
  return useMutation({
    mutationFn: async (scope: BreakGlassScope) => {
      const response = await breakGlassApi.requestChallenge(scope);
      return response.data;
    },
  });
};

export const useExecuteBreakGlass = () => {
  return useMutation({
    mutationFn: async (request: BreakGlassRequest) => {
      await breakGlassApi.execute(request);
    },
  });
};

// ============================================================================
// TENANTS & MODULES HOOKS
// ============================================================================

export const useTenantsList = () => {
  return useQuery({
    queryKey: breakGlassKeys.tenants(),
    queryFn: async () => {
      const response = await breakGlassApi.listTenants();
      return response.data.items;
    },
  });
};

export const useModulesList = () => {
  return useQuery({
    queryKey: breakGlassKeys.modules(),
    queryFn: async () => {
      const response = await breakGlassApi.listModules();
      return response.data.items;
    },
  });
};
