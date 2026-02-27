/**
 * AZALSCORE Module - Factures - React Query Hooks
 * Hooks pour la gestion de la facturation clients
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { PaginatedResponse } from '@/types';
import type {
  Facture, FactureFormData, Customer, FactureType,
  Payment, PaymentFormData
} from './types';

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const factureKeys = {
  all: ['commercial', 'documents'] as const,

  // Lists
  lists: () => [...factureKeys.all, 'factures'] as const,
  list: (page: number, pageSize: number, filters?: { type?: FactureType; status?: string; search?: string }) =>
    [...factureKeys.lists(), page, pageSize, serializeFilters(filters)] as const,

  // Details
  details: () => [...factureKeys.all, 'detail'] as const,
  detail: (id: string) => [...factureKeys.all, id] as const,

  // Payments
  payments: (documentId: string) => [...factureKeys.all, documentId, 'payments'] as const,

  // Customers
  customers: () => ['commercial', 'customers'] as const,
  customerSearch: (search?: string) => [...factureKeys.customers(), 'search', search] as const,
};

// ============================================================================
// LIST & DETAIL HOOKS
// ============================================================================

export const useFacturesList = (
  page = 1,
  pageSize = 25,
  filters?: { type?: FactureType; status?: string; search?: string }
) => {
  return useQuery({
    queryKey: factureKeys.list(page, pageSize, filters),
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (filters?.type) {
        params.append('type', filters.type);
      } else {
        params.append('type', 'INVOICE');
      }
      if (filters?.status) params.append('status', filters.status);
      if (filters?.search) params.append('search', filters.search);
      const response = await api.get<PaginatedResponse<Facture>>(`/commercial/documents?${params}`);
      return response.data;
    },
  });
};

export const useFacture = (id: string) => {
  return useQuery({
    queryKey: factureKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Facture>(`/commercial/documents/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

export const useFacturePayments = (documentId: string) => {
  return useQuery({
    queryKey: factureKeys.payments(documentId),
    queryFn: async () => {
      const response = await api.get<Payment[]>(`/commercial/documents/${documentId}/payments`);
      return response.data;
    },
    enabled: !!documentId,
  });
};

export const useCustomers = (search?: string) => {
  return useQuery({
    queryKey: factureKeys.customerSearch(search),
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

export const useCreateFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: FactureFormData) => {
      const response = await api.post<Facture>('/commercial/documents', data);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: factureKeys.all }),
  });
};

export const useUpdateFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<FactureFormData> }) => {
      const response = await api.put<Facture>(`/commercial/documents/${id}`, data);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: factureKeys.all }),
  });
};

export const useValidateFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Facture>(`/commercial/documents/${id}/validate`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: factureKeys.all }),
  });
};

export const useSendFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Facture>(`/commercial/documents/${id}/send`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: factureKeys.all }),
  });
};

export const useCancelFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Facture>(`/commercial/documents/${id}/cancel`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: factureKeys.all }),
  });
};

// ============================================================================
// PAYMENT HOOKS
// ============================================================================

export const useCreatePayment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, data }: { documentId: string; data: PaymentFormData }) => {
      const response = await api.post<Payment>('/commercial/payments', {
        document_id: documentId,
        ...data,
      });
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: factureKeys.all }),
  });
};

export const useDeletePayment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (paymentId: string) => {
      await api.delete(`/commercial/payments/${paymentId}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: factureKeys.all }),
  });
};

// ============================================================================
// AVOIR (CREDIT NOTE) HOOKS
// ============================================================================

export const useCreateAvoir = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (factureId: string) => {
      const response = await api.post<Facture>(`/commercial/documents/${factureId}/credit-note`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: factureKeys.all }),
  });
};
