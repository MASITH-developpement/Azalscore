/**
 * AZALSCORE Module - Devis - React Query Hooks
 * Hooks pour la gestion des devis clients
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { PaginatedResponse } from '@/types';
import type { Devis, DevisFormData, Customer, DocumentLine } from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const devisKeys = {
  all: ['commercial', 'documents'] as const,
  lists: () => [...devisKeys.all, 'QUOTE'] as const,
  list: (page: number, pageSize: number, filters?: Record<string, unknown>) =>
    [...devisKeys.lists(), page, pageSize, serializeFilters(filters)] as const,
  details: () => [...devisKeys.all, 'detail'] as const,
  detail: (id: string) => [...devisKeys.all, id] as const,
  customers: () => ['commercial', 'customers'] as const,
  customerSearch: (search?: string) => [...devisKeys.customers(), 'search', search] as const,
};

// ============================================================================
// LIST & DETAIL HOOKS
// ============================================================================

export const useDevisList = (
  page = 1,
  pageSize = 25,
  filters?: { status?: string; customer_id?: string; search?: string }
) => {
  return useQuery({
    queryKey: devisKeys.list(page, pageSize, filters),
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        type: 'QUOTE',
      });
      if (filters?.status) params.append('status', filters.status);
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      if (filters?.search) params.append('search', filters.search);
      const response = await api.get<PaginatedResponse<Devis>>(`/commercial/documents?${params}`);
      return response.data;
    },
  });
};

export const useDevis = (id: string) => {
  return useQuery({
    queryKey: devisKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Devis>(`/commercial/documents/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useCustomers = (search?: string) => {
  return useQuery({
    queryKey: devisKeys.customerSearch(search),
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

export const useCreateDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: DevisFormData) => {
      const response = await api.post<Devis>('/commercial/documents', { ...data, type: 'QUOTE' });
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};

export const useUpdateDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<DevisFormData> }) => {
      const response = await api.put<Devis>(`/commercial/documents/${id}`, data);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};

export const useValidateDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Devis>(`/commercial/documents/${id}/validate`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};

export const useSendDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Devis>(`/commercial/documents/${id}/send`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};

export const useAcceptDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Devis>(`/commercial/documents/${id}/accept`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};

export const useRejectDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      const response = await api.post<Devis>(`/commercial/documents/${id}/reject`, { reason });
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};

export const useConvertToOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (quoteId: string) => {
      const response = await api.post<Devis>(`/commercial/quotes/${quoteId}/convert`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};

export const useCancelDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Devis>(`/commercial/documents/${id}/cancel`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};

// ============================================================================
// LINE HOOKS
// ============================================================================

export const useAddLine = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, data }: { documentId: string; data: Partial<DocumentLine> }) => {
      const response = await api.post<DocumentLine>(`/commercial/documents/${documentId}/lines`, data);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};

export const useUpdateLine = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, lineId, data }: { documentId: string; lineId: string; data: Partial<DocumentLine> }) => {
      const response = await api.put<DocumentLine>(`/commercial/documents/${documentId}/lines/${lineId}`, data);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};

export const useDeleteLine = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, lineId }: { documentId: string; lineId: string }) => {
      await api.delete(`/commercial/documents/${documentId}/lines/${lineId}`);
      return lineId;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: devisKeys.all }),
  });
};
