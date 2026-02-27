/**
 * AZALSCORE - Profile React Query Hooks
 * ======================================
 * Hooks pour le module Profil Utilisateur
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// TYPES
// ============================================================================

export interface UserProfile {
  id?: string;
  name: string;
  email: string;
  phone?: string;
  photo?: string;
  api_token?: string;
  role: string;
}

export interface UpdateProfileData {
  name?: string;
  email?: string;
  phone?: string;
  photo?: string;
}

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const profileKeys = {
  all: ['profile'] as const,
  detail: () => [...profileKeys.all, 'detail'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

export const useProfile = () => {
  return useQuery({
    queryKey: profileKeys.detail(),
    queryFn: async () => {
      const response = await api.get<UserProfile>('/web/profile');
      return response as unknown as UserProfile;
    },
  });
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

export const useUpdateProfile = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: UpdateProfileData) => {
      await api.put('/web/profile', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.detail() });
    },
  });
};

export const useGenerateApiToken = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const response = await api.post<{ api_token: string }>('/web/profile/generate-token');
      return response as unknown as { api_token: string };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: profileKeys.detail() });
    },
  });
};
