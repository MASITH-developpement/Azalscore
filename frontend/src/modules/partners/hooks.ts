/**
 * AZALSCORE Module - Partners - React Query Hooks
 * API hooks pour clients, fournisseurs et contacts
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { unwrapApiResponse } from '@/types';
import type { PaginatedResponse } from '@/types';
import type { Partner, Client, Contact, ClientFormData, PartnerLegacy } from './types';

// ============================================================================
// QUERY KEYS FACTORY
// ============================================================================

export const partnersKeys = {
  all: ['partners'] as const,
  lists: () => [...partnersKeys.all, 'list'] as const,
  list: (type: string, page?: number, pageSize?: number) =>
    [...partnersKeys.lists(), type, page, pageSize] as const,
  details: () => [...partnersKeys.all, 'detail'] as const,
  detail: (type: string, id: string) => [...partnersKeys.details(), type, id] as const,
  clientsForSelect: () => [...partnersKeys.all, 'clients-for-select'] as const,
};

// ============================================================================
// LIST HOOKS
// ============================================================================

/**
 * Hook générique pour récupérer une liste de partenaires
 */
export const usePartners = (
  type: 'client' | 'supplier' | 'contact',
  page = 1,
  pageSize = 25
) => {
  return useQuery({
    queryKey: partnersKeys.list(type, page, pageSize),
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PartnerLegacy>>(
        `/partners/${type}s?page=${page}&page_size=${pageSize}`
      );
      return response as unknown as PaginatedResponse<PartnerLegacy>;
    },
  });
};

/**
 * Hook pour récupérer les clients (avec pagination)
 */
export const useClients = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: partnersKeys.list('clients', page, pageSize),
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PartnerLegacy>>(
        `/partners/clients?page=${page}&page_size=${pageSize}`
      );
      return response as unknown as PaginatedResponse<PartnerLegacy>;
    },
  });
};

/**
 * Hook pour récupérer les contacts (avec pagination)
 */
export const useContacts = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: partnersKeys.list('contacts', page, pageSize),
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Contact>>(
        `/partners/contacts?page=${page}&page_size=${pageSize}`
      );
      return response as unknown as PaginatedResponse<Contact>;
    },
  });
};

/**
 * Hook pour récupérer les clients actifs (pour select)
 */
export const useClientsForSelect = () => {
  return useQuery({
    queryKey: partnersKeys.clientsForSelect(),
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PartnerLegacy>>(
        '/partners/clients?page=1&page_size=100&is_active=true'
      );
      return response as unknown as PaginatedResponse<PartnerLegacy>;
    },
  });
};

// ============================================================================
// DETAIL HOOKS
// ============================================================================

/**
 * Hook générique pour récupérer un partenaire par ID
 */
export const usePartner = (
  type: 'client' | 'supplier' | 'contact',
  id: string | undefined
) => {
  return useQuery({
    queryKey: partnersKeys.detail(type, id || ''),
    queryFn: async () => {
      const response = await api.get<Partner>(`/partners/${type}s/${id}`);
      return response as unknown as Partner;
    },
    enabled: !!id,
  });
};

/**
 * Hook pour récupérer un client par ID (avec unwrap)
 */
export const useClient = (id: string) => {
  return useQuery({
    queryKey: partnersKeys.detail('clients', id),
    queryFn: async () => {
      const response = await api.get<Client>(`/partners/clients/${id}`);
      return unwrapApiResponse<Client>(response);
    },
    enabled: !!id && id !== 'new',
  });
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

/**
 * Hook générique pour créer un partenaire
 */
export const useCreatePartner = (type: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<PartnerLegacy>) => {
      const response = await api.post<PartnerLegacy>(`/partners/${type}s`, data);
      return response as unknown as PartnerLegacy;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: partnersKeys.lists() });
    },
  });
};

/**
 * Hook pour créer un client
 */
export const useCreateClient = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<ClientFormData>) => {
      const response = await api.post<Client>('/partners/clients', data);
      return unwrapApiResponse<Client>(response);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: partnersKeys.lists() });
    },
  });
};

/**
 * Hook pour mettre à jour un client
 */
export const useUpdateClient = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<ClientFormData> }) => {
      const response = await api.put<Client>(`/partners/clients/${id}`, data);
      return unwrapApiResponse<Client>(response);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: partnersKeys.lists() });
      queryClient.invalidateQueries({ queryKey: partnersKeys.detail('clients', id) });
    },
  });
};

/**
 * Hook pour créer un contact
 */
export const useCreateContact = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Contact>) => {
      const response = await api.post<Contact>('/partners/contacts', data);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: partnersKeys.lists() });
    },
  });
};
