/**
 * AZALSCORE - Module Documents Unifié
 * Hooks API optimisés avec React Query
 *
 * Optimisations:
 * - staleTime: 5 minutes pour réduire les requêtes
 * - Pagination des partenaires (50 max au lieu de 500)
 * - Invalidation ciblée du cache
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { QUERY_CONFIG, DOCUMENT_TYPE_CONFIG } from './constants';
import type {
  DocumentType,
  DocumentFilters,
  PartnerFilters,
  UnifiedDocument,
  SalesDocument,
  PurchaseOrder,
  PurchaseInvoice,
  Partner,
  Customer,
  Supplier,
  PaginatedResponse,
  SalesDocumentCreateData,
  PurchaseOrderCreateData,
  PurchaseInvoiceCreateData,
  LineFormData,
  DocumentsSummary,
} from './types';

// ============================================================
// HELPERS
// ============================================================

const buildQueryParams = (params: Record<string, string | number | undefined>): string => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  return searchParams.toString();
};

// ============================================================
// HOOKS - DOCUMENTS DE VENTE (Devis, Factures, Avoirs)
// ============================================================

/**
 * Liste des documents de vente
 */
export const useSalesDocuments = (
  type: 'QUOTE' | 'INVOICE' | 'CREDIT_NOTE',
  page = 1,
  pageSize = QUERY_CONFIG.defaultPageSize,
  filters: DocumentFilters = {}
) => {
  const queryParams = buildQueryParams({
    page,
    page_size: pageSize,
    type,
    status: filters.status,
    search: filters.search,
    customer_id: filters.partner_id,
    date_from: filters.date_from,
    date_to: filters.date_to,
  });

  return useQuery({
    queryKey: ['documents', 'sales', type, page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<SalesDocument>>(
        `/v1/commercial/documents?${queryParams}`
      );
      return response as unknown as PaginatedResponse<SalesDocument>;
    },
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Document de vente par ID
 */
export const useSalesDocument = (id: string) => {
  return useQuery({
    queryKey: ['documents', 'sales', 'detail', id],
    queryFn: async () => {
      const response = await api.get<SalesDocument>(`/v1/commercial/documents/${id}`);
      return response as unknown as SalesDocument;
    },
    enabled: !!id && id !== 'new',
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Créer un document de vente
 */
export const useCreateSalesDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: SalesDocumentCreateData) => {
      const response = await api.post<SalesDocument>('/v1/commercial/documents', data);
      return response as unknown as SalesDocument;
    },
    onSuccess: (data) => {
      // Invalidation ciblée
      queryClient.invalidateQueries({ queryKey: ['documents', 'sales', data.type] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

/**
 * Mettre à jour un document de vente
 */
export const useUpdateSalesDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<SalesDocumentCreateData> & { lines?: LineFormData[] };
    }) => {
      const response = await api.put<SalesDocument>(`/v1/commercial/documents/${id}`, data);
      return response as unknown as SalesDocument;
    },
    onSuccess: (data) => {
      // Invalidation ciblée
      queryClient.invalidateQueries({ queryKey: ['documents', 'sales', data.type] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'sales', 'detail', data.id] });
    },
  });
};

/**
 * Supprimer un document de vente
 */
export const useDeleteSalesDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, type }: { id: string; type: 'QUOTE' | 'INVOICE' | 'CREDIT_NOTE' }) => {
      await api.delete(`/v1/commercial/documents/${id}`);
      return { id, type };
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'sales', variables.type] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

/**
 * Valider un document de vente
 */
export const useValidateSalesDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id }: { id: string }) => {
      const response = await api.post<SalesDocument>(`/v1/commercial/documents/${id}/validate`);
      return response as unknown as SalesDocument;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'sales', data.type] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'sales', 'detail', data.id] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

/**
 * Convertir un devis en facture
 */
export const useConvertQuoteToInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ quoteId }: { quoteId: string }) => {
      const response = await api.post<SalesDocument>(`/v1/commercial/quotes/${quoteId}/convert`);
      return response as unknown as SalesDocument;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'sales', 'QUOTE'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'sales', 'INVOICE'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

// ============================================================
// HOOKS - COMMANDES FOURNISSEURS
// ============================================================

/**
 * Liste des commandes fournisseurs
 */
export const usePurchaseOrders = (
  page = 1,
  pageSize = QUERY_CONFIG.defaultPageSize,
  filters: DocumentFilters = {}
) => {
  const queryParams = buildQueryParams({
    page,
    page_size: pageSize,
    status: filters.status,
    search: filters.search,
    supplier_id: filters.partner_id,
    date_from: filters.date_from,
    date_to: filters.date_to,
  });

  return useQuery({
    queryKey: ['documents', 'purchases', 'orders', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PurchaseOrder>>(
        `/v1/purchases/orders?${queryParams}`
      );
      return response.data;
    },
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Commande fournisseur par ID
 */
export const usePurchaseOrder = (id: string) => {
  return useQuery({
    queryKey: ['documents', 'purchases', 'orders', 'detail', id],
    queryFn: async () => {
      const response = await api.get<PurchaseOrder>(`/v1/purchases/orders/${id}`);
      return response.data;
    },
    enabled: !!id && id !== 'new',
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Créer une commande fournisseur
 */
export const useCreatePurchaseOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: PurchaseOrderCreateData) => {
      const response = await api.post<PurchaseOrder>('/v1/purchases/orders', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

/**
 * Mettre à jour une commande fournisseur
 */
export const useUpdatePurchaseOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<PurchaseOrderCreateData> & { lines?: LineFormData[] };
    }) => {
      const response = await api.put<PurchaseOrder>(`/v1/purchases/orders/${id}`, data);
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'orders', 'detail', id] });
    },
  });
};

/**
 * Supprimer une commande fournisseur
 */
export const useDeletePurchaseOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v1/purchases/orders/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

/**
 * Valider une commande fournisseur
 */
export const useValidatePurchaseOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<PurchaseOrder>(`/v1/purchases/orders/${id}/validate`);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'orders', 'detail', id] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

// ============================================================
// HOOKS - FACTURES FOURNISSEURS
// ============================================================

/**
 * Liste des factures fournisseurs
 */
export const usePurchaseInvoices = (
  page = 1,
  pageSize = QUERY_CONFIG.defaultPageSize,
  filters: DocumentFilters = {}
) => {
  const queryParams = buildQueryParams({
    page,
    page_size: pageSize,
    status: filters.status,
    search: filters.search,
    supplier_id: filters.partner_id,
    date_from: filters.date_from,
    date_to: filters.date_to,
  });

  return useQuery({
    queryKey: ['documents', 'purchases', 'invoices', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PurchaseInvoice>>(
        `/v1/purchases/invoices?${queryParams}`
      );
      return response.data;
    },
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Facture fournisseur par ID
 */
export const usePurchaseInvoice = (id: string) => {
  return useQuery({
    queryKey: ['documents', 'purchases', 'invoices', 'detail', id],
    queryFn: async () => {
      const response = await api.get<PurchaseInvoice>(`/v1/purchases/invoices/${id}`);
      return response.data;
    },
    enabled: !!id && id !== 'new',
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Créer une facture fournisseur
 */
export const useCreatePurchaseInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: PurchaseInvoiceCreateData) => {
      const response = await api.post<PurchaseInvoice>('/v1/purchases/invoices', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

/**
 * Mettre à jour une facture fournisseur
 */
export const useUpdatePurchaseInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<PurchaseInvoiceCreateData> & { lines?: LineFormData[] };
    }) => {
      const response = await api.put<PurchaseInvoice>(`/v1/purchases/invoices/${id}`, data);
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'invoices', 'detail', id] });
    },
  });
};

/**
 * Supprimer une facture fournisseur
 */
export const useDeletePurchaseInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v1/purchases/invoices/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

/**
 * Valider une facture fournisseur
 */
export const useValidatePurchaseInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<PurchaseInvoice>(`/v1/purchases/invoices/${id}/validate`);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'invoices', 'detail', id] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

/**
 * Créer une facture depuis une commande
 */
export const useCreateInvoiceFromOrder = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (orderId: string) => {
      const response = await api.post<PurchaseInvoice>(
        `/v1/purchases/orders/${orderId}/create-invoice`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'purchases', 'invoices'] });
      queryClient.invalidateQueries({ queryKey: ['documents', 'summary'] });
    },
  });
};

// ============================================================
// HOOKS - PARTENAIRES (Clients & Fournisseurs)
// ============================================================

/**
 * Liste des clients avec pagination
 * OPTIMISÉ: Charge seulement 50 clients au lieu de 500
 */
export const useCustomers = (
  page = 1,
  pageSize = QUERY_CONFIG.defaultPageSize,
  filters: PartnerFilters = {}
) => {
  const queryParams = buildQueryParams({
    page,
    page_size: pageSize,
    search: filters.search,
    status: filters.status,
    is_active: 'true',
  });

  return useQuery({
    queryKey: ['partners', 'customers', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Customer>>(
        `/v1/partners/clients?${queryParams}`
      );
      return response as unknown as PaginatedResponse<Customer>;
    },
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Lookup clients (pour les sélecteurs)
 * OPTIMISÉ: Limite à 50 résultats avec recherche
 */
export const useCustomersLookup = (search = '') => {
  const queryParams = buildQueryParams({
    page_size: QUERY_CONFIG.partnerLookupLimit,
    is_active: 'true',
    search: search || undefined,
  });

  return useQuery({
    queryKey: ['partners', 'customers', 'lookup', search],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Customer>>(
        `/v1/partners/clients?${queryParams}`
      );
      return (response as unknown as PaginatedResponse<Customer>).items;
    },
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Client par ID
 */
export const useCustomer = (id: string) => {
  return useQuery({
    queryKey: ['partners', 'customers', 'detail', id],
    queryFn: async () => {
      const response = await api.get<Customer>(`/v1/partners/clients/${id}`);
      return response as unknown as Customer;
    },
    enabled: !!id && id !== 'new',
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Liste des fournisseurs avec pagination
 */
export const useSuppliers = (
  page = 1,
  pageSize = QUERY_CONFIG.defaultPageSize,
  filters: PartnerFilters = {}
) => {
  const queryParams = buildQueryParams({
    page,
    page_size: pageSize,
    search: filters.search,
    status: filters.status,
  });

  return useQuery({
    queryKey: ['partners', 'suppliers', page, pageSize, filters],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Supplier>>(
        `/v1/purchases/suppliers?${queryParams}`
      );
      return response.data;
    },
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Lookup fournisseurs (pour les sélecteurs)
 * OPTIMISÉ: Limite à 50 résultats avec recherche
 */
export const useSuppliersLookup = (search = '') => {
  const queryParams = buildQueryParams({
    page_size: QUERY_CONFIG.partnerLookupLimit,
    status: 'APPROVED',
    search: search || undefined,
  });

  return useQuery({
    queryKey: ['partners', 'suppliers', 'lookup', search],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Supplier>>(
        `/v1/purchases/suppliers?${queryParams}`
      );
      return response.data.items;
    },
    staleTime: QUERY_CONFIG.staleTime,
  });
};

/**
 * Fournisseur par ID
 */
export const useSupplier = (id: string) => {
  return useQuery({
    queryKey: ['partners', 'suppliers', 'detail', id],
    queryFn: async () => {
      const response = await api.get<Supplier>(`/v1/purchases/suppliers/${id}`);
      return response.data;
    },
    enabled: !!id && id !== 'new',
    staleTime: QUERY_CONFIG.staleTime,
  });
};

// ============================================================
// HOOKS - MUTATIONS PARTENAIRES
// ============================================================

/**
 * Créer un client
 */
export const useCreateCustomer = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Omit<Customer, 'id' | 'code' | 'type' | 'created_at' | 'updated_at'>) => {
      const response = await api.post<Customer>('/v1/partners/clients', data);
      return response as unknown as Customer;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners', 'customers'] });
    },
  });
};

/**
 * Mettre à jour un client
 */
export const useUpdateCustomer = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<Omit<Customer, 'id' | 'code' | 'type' | 'created_at' | 'updated_at'>>;
    }) => {
      const response = await api.put<Customer>(`/v1/partners/clients/${id}`, data);
      return response as unknown as Customer;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['partners', 'customers'] });
      queryClient.invalidateQueries({ queryKey: ['partners', 'customers', 'detail', id] });
    },
  });
};

/**
 * Supprimer un client
 */
export const useDeleteCustomer = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v1/partners/clients/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners', 'customers'] });
    },
  });
};

/**
 * Créer un fournisseur
 */
export const useCreateSupplier = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Omit<Supplier, 'id' | 'code' | 'type' | 'status' | 'created_at' | 'updated_at'>) => {
      const response = await api.post<Supplier>('/v1/purchases/suppliers', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners', 'suppliers'] });
    },
  });
};

/**
 * Mettre à jour un fournisseur
 */
export const useUpdateSupplier = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: Partial<Omit<Supplier, 'id' | 'code' | 'type' | 'created_at' | 'updated_at'>>;
    }) => {
      const response = await api.put<Supplier>(`/v1/purchases/suppliers/${id}`, data);
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['partners', 'suppliers'] });
      queryClient.invalidateQueries({ queryKey: ['partners', 'suppliers', 'detail', id] });
    },
  });
};

/**
 * Supprimer un fournisseur
 */
export const useDeleteSupplier = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v1/purchases/suppliers/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners', 'suppliers'] });
    },
  });
};

// ============================================================
// HOOKS - SUMMARY
// ============================================================

/**
 * Résumé pour le dashboard
 */
export const useDocumentsSummary = () => {
  return useQuery({
    queryKey: ['documents', 'summary'],
    queryFn: async () => {
      // Appel parallèle pour récupérer les résumés
      const [salesSummary, purchasesSummary] = await Promise.all([
        api.get('/v1/commercial/summary').catch(() => ({ data: {} })),
        api.get('/v1/purchases/summary').catch(() => ({ data: {} })),
      ]);

      return {
        // Ventes
        draft_quotes: (salesSummary as any).data?.draft_quotes || 0,
        draft_invoices: (salesSummary as any).data?.draft_invoices || 0,
        pending_amount: (salesSummary as any).data?.pending_amount || 0,
        // Achats
        pending_orders: (purchasesSummary as any).data?.pending_orders || 0,
        pending_orders_value: (purchasesSummary as any).data?.pending_value || 0,
        draft_purchase_invoices: (purchasesSummary as any).data?.pending_invoices || 0,
        // Partenaires
        active_customers: (salesSummary as any).data?.active_customers || 0,
        active_suppliers: (purchasesSummary as any).data?.active_suppliers || 0,
      } as DocumentsSummary;
    },
    staleTime: QUERY_CONFIG.staleTime,
  });
};

// ============================================================
// HOOKS - EXPORT
// ============================================================

/**
 * Export CSV des documents
 */
export const useExportDocuments = () => {
  return useMutation({
    mutationFn: async ({
      type,
      filters,
    }: {
      type: DocumentType;
      filters: DocumentFilters;
    }) => {
      const config = DOCUMENT_TYPE_CONFIG[type];
      const issPurchase = config.category === 'PURCHASES';

      let endpoint = '';
      if (type === 'PURCHASE_ORDER') {
        endpoint = '/v1/purchases/orders/export';
      } else if (type === 'PURCHASE_INVOICE') {
        endpoint = '/v1/purchases/invoices/export';
      } else {
        endpoint = '/v1/commercial/documents/export';
      }

      const queryParams = buildQueryParams({
        type: issPurchase ? undefined : type,
        format: 'csv',
        status: filters.status,
        search: filters.search,
      });

      const response = await api.get<Blob>(`${endpoint}?${queryParams}`, {
        responseType: 'blob',
      } as any);

      return response as unknown as Blob;
    },
  });
};
