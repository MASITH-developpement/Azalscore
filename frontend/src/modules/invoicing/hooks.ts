/**
 * AZALSCORE Module - Invoicing - Hooks
 * React Query hooks pour le module Facturation
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type { PaginatedResponse } from '@/types';
import type { Document, DocumentType, DocumentStatus, Customer, LineFormData } from './types';

// ============================================================================
// TYPES
// ============================================================================

export interface DocumentFilters {
  status?: DocumentStatus;
  search?: string;
  date_from?: string;
  date_to?: string;
}

// ============================================================================
// QUERY HOOKS
// ============================================================================

/**
 * Hook pour lister les documents d'un type
 */
export const useDocuments = (
  type: DocumentType,
  page = 1,
  pageSize = 25,
  filters: DocumentFilters = {}
) => {
  const queryParams = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    type: type,
    ...(filters.status && { status: filters.status }),
    ...(filters.search && { search: filters.search }),
    ...(filters.date_from && { date_from: filters.date_from }),
    ...(filters.date_to && { date_to: filters.date_to }),
  });

  return useQuery({
    queryKey: ['documents', type, page, pageSize, serializeFilters(filters)],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Document>>(
        `/commercial/documents?${queryParams}`
      );
      return response as unknown as PaginatedResponse<Document>;
    },
  });
};

/**
 * Hook pour un document specifique
 */
export const useDocument = (id: string) => {
  return useQuery({
    queryKey: ['document', id],
    queryFn: async () => {
      const response = await api.get<Document>(`/commercial/documents/${id}`);
      return response as unknown as Document;
    },
    enabled: !!id && id !== 'new',
  });
};

/**
 * Hook pour la liste des clients
 */
export const useCustomers = () => {
  return useQuery({
    queryKey: ['customers', 'list'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Customer>>(
        '/partners/clients?page_size=500&is_active=true'
      );
      return (response as unknown as PaginatedResponse<Customer>).items;
    },
  });
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

/**
 * Hook pour creer un document
 */
export const useCreateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: {
      type: DocumentType;
      customer_id: string;
      date: string;
      due_date?: string;
      validity_date?: string;
      notes?: string;
      lines: Omit<LineFormData, 'id'>[];
    }) => {
      const response = await api.post<Document>('/commercial/documents', data);
      return response as unknown as Document;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
    },
  });
};

/**
 * Hook pour modifier un document
 */
export const useUpdateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: {
      id: string;
      data: Omit<Partial<Document>, 'lines'> & { lines?: LineFormData[] };
    }) => {
      const response = await api.put<Document>(`/commercial/documents/${id}`, data);
      return response as unknown as Document;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
      queryClient.invalidateQueries({ queryKey: ['document', data.id] });
    },
  });
};

/**
 * Hook pour supprimer un document
 */
export const useDeleteDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, type }: { id: string; type: DocumentType }) => {
      await api.delete(`/commercial/documents/${id}`);
      return { id, type };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents', variables.type] });
    },
  });
};

/**
 * Hook pour valider un document
 */
export const useValidateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id }: { id: string }) => {
      const response = await api.post<Document>(`/commercial/documents/${id}/validate`);
      return response as unknown as Document;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
      queryClient.invalidateQueries({ queryKey: ['document', data.id] });
    },
  });
};

/**
 * Hook pour convertir un devis en facture (legacy)
 */
export const useConvertQuoteToInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ quoteId }: { quoteId: string }) => {
      const response = await api.post<Document>(`/commercial/quotes/${quoteId}/convert`);
      return response as unknown as Document;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'QUOTE'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'INVOICE'] });
    },
  });
};

/**
 * Hook pour dupliquer un document
 */
export const useDuplicateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ document }: { document: Document }) => {
      const payload = {
        type: document.type,
        customer_id: document.customer_id,
        date: new Date().toISOString().split('T')[0],
        due_date: document.due_date,
        validity_date: document.validity_date,
        notes: document.notes ? `(Copie) ${document.notes}` : '(Copie)',
        lines: document.lines.map(l => ({
          description: l.description,
          quantity: l.quantity,
          unit: l.unit,
          unit_price: l.unit_price,
          discount_percent: l.discount_percent,
          tax_rate: l.tax_rate,
        })),
      };
      const response = await api.post<Document>('/commercial/documents', payload);
      return response as unknown as Document;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
    },
  });
};

/**
 * Hook pour transformer un document (Devis -> Commande ou Commande -> Facture)
 */
export const useTransformDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ document, targetType }: { document: Document; targetType: DocumentType }) => {
      const payload = {
        type: targetType,
        customer_id: document.customer_id,
        date: new Date().toISOString().split('T')[0],
        parent_id: document.id,
        notes: document.notes,
        lines: document.lines.map(l => ({
          description: l.description,
          quantity: l.quantity,
          unit: l.unit,
          unit_price: l.unit_price,
          discount_percent: l.discount_percent,
          tax_rate: l.tax_rate,
        })),
      };
      const response = await api.post<Document>('/commercial/documents', payload);
      return response as unknown as Document;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents', variables.document.type] });
      queryClient.invalidateQueries({ queryKey: ['documents', data.type] });
    },
  });
};

/**
 * Hook pour exporter les documents
 */
export const useExportDocuments = () => {
  return useMutation({
    mutationFn: async ({ type, filters }: { type: DocumentType; filters: DocumentFilters }) => {
      const queryParams = new URLSearchParams({
        type: type,
        format: 'csv',
        ...(filters.status && { status: filters.status }),
        ...(filters.search && { search: filters.search }),
      });

      const response = await api.get<Blob>(
        `/commercial/documents/export?${queryParams}`,
        { responseType: 'blob' }
      );
      return response as unknown as Blob;
    },
  });
};
