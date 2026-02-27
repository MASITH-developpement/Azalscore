/**
 * AZALSCORE Module - Commandes - React Query Hooks
 * Hooks pour la gestion des commandes clients
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { PaginatedResponse } from '@/types';
import type { Commande, CommandeFormData, Customer, DocumentLine } from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const commandeKeys = {
  all: ['commercial', 'documents'] as const,
  lists: () => [...commandeKeys.all, 'ORDER'] as const,
  list: (page: number, pageSize: number, filters?: Record<string, unknown>) =>
    [...commandeKeys.lists(), page, pageSize, serializeFilters(filters)] as const,
  details: () => [...commandeKeys.all, 'detail'] as const,
  detail: (id: string) => [...commandeKeys.all, id] as const,
  customers: () => ['commercial', 'customers'] as const,
  customerSearch: (search?: string) => [...commandeKeys.customers(), 'search', search] as const,
};

// ============================================================================
// LIST & DETAIL HOOKS
// ============================================================================

export const useCommandesList = (
  page = 1,
  pageSize = 25,
  filters?: { status?: string; customer_id?: string; search?: string }
) => {
  return useQuery({
    queryKey: commandeKeys.list(page, pageSize, filters),
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        type: 'ORDER',
      });
      if (filters?.status) params.append('status', filters.status);
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      if (filters?.search) params.append('search', filters.search);
      const response = await api.get<PaginatedResponse<Commande>>(`/commercial/documents?${params}`);
      return response.data;
    },
  });
};

export const useCommande = (id: string) => {
  return useQuery({
    queryKey: commandeKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Commande>(`/commercial/documents/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCustomers = (search?: string) => {
  return useQuery({
    queryKey: commandeKeys.customerSearch(search),
    queryFn: async () => {
      const params = new URLSearchParams({ page: '1', page_size: '50' });
      if (search) params.append('search', search);
      const response = await api.get<PaginatedResponse<Customer>>(`/commercial/customers?${params}`);
      return response.data.items;
    },
  });
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

export const useCreateCommande = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CommandeFormData) => {
      const response = await api.post<Commande>('/commercial/documents', { ...data, type: 'ORDER' });
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: commandeKeys.all }),
  });
};

export const useUpdateCommande = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<CommandeFormData> }) => {
      const response = await api.put<Commande>(`/commercial/documents/${id}`, data);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: commandeKeys.all }),
  });
};

export const useValidateCommande = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Commande>(`/commercial/documents/${id}/validate`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: commandeKeys.all }),
  });
};

export const useMarkDelivered = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Commande>(`/commercial/documents/${id}/deliver`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: commandeKeys.all }),
  });
};

export const useCreateInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (orderId: string) => {
      const response = await api.post<{ id: string; number: string }>(`/commercial/orders/${orderId}/invoice`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: commandeKeys.all }),
  });
};

export const useCreateAffaire = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (orderId: string) => {
      const response = await api.post<{ id: string; reference: string }>(`/commercial/orders/${orderId}/affaire`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: commandeKeys.all });
      queryClient.invalidateQueries({ queryKey: ['affaires'] });
    },
  });
};

export const useAddLine = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, data }: { documentId: string; data: Partial<DocumentLine> }) => {
      const response = await api.post<DocumentLine>(`/commercial/documents/${documentId}/lines`, data);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: commandeKeys.all }),
  });
};

export const useDeleteLine = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, lineId }: { documentId: string; lineId: string }) => {
      await api.delete(`/commercial/documents/${documentId}/lines/${lineId}`);
      return lineId;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: commandeKeys.all }),
  });
};

export const useCancelCommande = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Commande>(`/commercial/documents/${id}/cancel`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: commandeKeys.all }),
  });
};
