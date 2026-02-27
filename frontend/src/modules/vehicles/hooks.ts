/**
 * AZALSCORE Module - Vehicules - React Query Hooks
 * Hooks pour la gestion de la flotte de vehicules
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import type { PaginatedResponse } from '@/types';
import type { Vehicule } from './types';
import { isDemoMode } from '../../utils/demoMode';
import { DEMO_VEHICLES } from './demoData';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const vehicleKeys = {
  all: ['vehicles'] as const,
  lists: () => [...vehicleKeys.all, 'list'] as const,
  list: (page: number, pageSize: number) => [...vehicleKeys.lists(), page, pageSize] as const,
  details: () => [...vehicleKeys.all, 'detail'] as const,
  detail: (id: string) => [...vehicleKeys.details(), id] as const,
};

// ============================================================================
// HOOKS
// ============================================================================

export const useVehicules = (page = 1, pageSize = 25) => {
  const demoMode = isDemoMode();

  return useQuery({
    queryKey: vehicleKeys.list(page, pageSize),
    queryFn: async () => {
      if (demoMode) {
        const start = (page - 1) * pageSize;
        const items = DEMO_VEHICLES.slice(start, start + pageSize);
        return { items, total: DEMO_VEHICLES.length };
      }

      try {
        const response = await api.get<PaginatedResponse<Vehicule>>(
          `/fleet/vehicles?page=${page}&page_size=${pageSize}`
        );
        return (response as unknown as PaginatedResponse<Vehicule>) || { items: [], total: 0 };
      } catch {
        const start = (page - 1) * pageSize;
        const items = DEMO_VEHICLES.slice(start, start + pageSize);
        return { items, total: DEMO_VEHICLES.length };
      }
    },
  });
};

export const useVehicule = (id: string) => {
  const demoMode = isDemoMode();

  return useQuery({
    queryKey: vehicleKeys.detail(id),
    queryFn: async () => {
      if (demoMode) {
        const vehicule = DEMO_VEHICLES.find(v => v.id === id);
        if (!vehicule) throw new Error('Vehicule non trouve');
        return vehicule;
      }

      try {
        const response = await api.get<Vehicule>(`/fleet/vehicles/${id}`);
        return response as unknown as Vehicule;
      } catch (error) {
        const vehicule = DEMO_VEHICLES.find(v => v.id === id);
        if (vehicule) return vehicule;
        throw error;
      }
    },
    enabled: !!id && id !== 'new',
  });
};

export const useDeleteVehicule = () => {
  const queryClient = useQueryClient();
  const demoMode = isDemoMode();

  return useMutation({
    mutationFn: async (id: string) => {
      if (demoMode) {
        const index = DEMO_VEHICLES.findIndex(v => v.id === id);
        if (index >= 0) {
          DEMO_VEHICLES.splice(index, 1);
        }
        return id;
      }
      await api.delete(`/fleet/vehicles/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
    },
  });
};

export const useCreateVehicule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<Vehicule>) => {
      const response = await api.post<Vehicule>('/fleet/vehicles', data);
      return response as unknown as Vehicule;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: vehicleKeys.all });
    },
  });
};

export const useUpdateVehicule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Vehicule> }) => {
      const response = await api.put<Vehicule>(`/fleet/vehicles/${id}`, data);
      return response as unknown as Vehicule;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: vehicleKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: vehicleKeys.lists() });
    },
  });
};
