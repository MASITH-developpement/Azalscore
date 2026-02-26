/**
 * AZALSCORE Module - Purchases - React Query Hooks
 * =================================================
 * Hooks React Query pour le module Achats
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { purchasesApi } from '../api';
import type {
  SupplierFilters,
  OrderFilters,
  InvoiceFilters,
  SupplierCreate,
  OrderCreate,
  InvoiceCreate,
} from '../api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const purchasesKeys = {
  all: ['purchases'] as const,
  summary: () => [...purchasesKeys.all, 'summary'] as const,
  // Suppliers
  suppliers: () => [...purchasesKeys.all, 'suppliers'] as const,
  suppliersList: (filters?: SupplierFilters) => [...purchasesKeys.suppliers(), 'list', filters] as const,
  suppliersLookup: () => [...purchasesKeys.suppliers(), 'lookup'] as const,
  supplier: (id: string) => [...purchasesKeys.suppliers(), id] as const,
  // Orders
  orders: () => [...purchasesKeys.all, 'orders'] as const,
  ordersList: (filters?: OrderFilters) => [...purchasesKeys.orders(), 'list', filters] as const,
  order: (id: string) => [...purchasesKeys.orders(), id] as const,
  // Invoices
  invoices: () => [...purchasesKeys.all, 'invoices'] as const,
  invoicesList: (filters?: InvoiceFilters) => [...purchasesKeys.invoices(), 'list', filters] as const,
  invoice: (id: string) => [...purchasesKeys.invoices(), id] as const,
};

// ============================================================================
// SUMMARY
// ============================================================================

export function usePurchaseSummary() {
  return useQuery({
    queryKey: purchasesKeys.summary(),
    queryFn: async () => {
      const response = await purchasesApi.getSummary();
      return response.data;
    },
  });
}

// ============================================================================
// SUPPLIERS - Queries
// ============================================================================

export function useSuppliers(filters?: SupplierFilters) {
  return useQuery({
    queryKey: purchasesKeys.suppliersList(filters),
    queryFn: async () => {
      const response = await purchasesApi.listSuppliers(filters);
      return response.data ?? { items: [], total: 0, page: 1, pages: 0 };
    },
  });
}

export function useSupplier(id: string) {
  return useQuery({
    queryKey: purchasesKeys.supplier(id),
    queryFn: async () => {
      const response = await purchasesApi.getSupplier(id);
      return response.data;
    },
    enabled: !!id && id !== 'new',
  });
}

export function useSuppliersLookup() {
  return useQuery({
    queryKey: purchasesKeys.suppliersLookup(),
    queryFn: async () => {
      const response = await purchasesApi.listSuppliers({ status: 'APPROVED', page_size: 500 });
      return response.data?.items ?? [];
    },
  });
}

// ============================================================================
// SUPPLIERS - Mutations
// ============================================================================

export function useCreateSupplier() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: SupplierCreate) => {
      const response = await purchasesApi.createSupplier(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.suppliers() });
    },
  });
}

export function useUpdateSupplier() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<SupplierCreate> }) => {
      const response = await purchasesApi.updateSupplier(id, data);
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.suppliers() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.supplier(id) });
    },
  });
}

export function useDeleteSupplier() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await purchasesApi.deleteSupplier(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.suppliers() });
    },
    onError: (error: Error & { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || error.message || 'Erreur lors de la suppression';
      alert(`Erreur: ${message}`);
      console.error('[DELETE_SUPPLIER] Erreur:', error);
    },
  });
}

export function useApproveSupplier() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await purchasesApi.approveSupplier(id);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.suppliers() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.supplier(id) });
    },
  });
}

export function useBlockSupplier() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await purchasesApi.blockSupplier(id);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.suppliers() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.supplier(id) });
    },
  });
}

// ============================================================================
// ORDERS - Queries
// ============================================================================

export function usePurchaseOrders(filters?: OrderFilters) {
  return useQuery({
    queryKey: purchasesKeys.ordersList(filters),
    queryFn: async () => {
      const response = await purchasesApi.listOrders(filters);
      return response.data ?? { items: [], total: 0, page: 1, pages: 0 };
    },
  });
}

export function usePurchaseOrder(id: string) {
  return useQuery({
    queryKey: purchasesKeys.order(id),
    queryFn: async () => {
      const response = await purchasesApi.getOrder(id);
      return response.data;
    },
    enabled: !!id && id !== 'new',
  });
}

// ============================================================================
// ORDERS - Mutations
// ============================================================================

export function useCreatePurchaseOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: OrderCreate) => {
      const response = await purchasesApi.createOrder(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.orders() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.summary() });
    },
  });
}

export function useUpdatePurchaseOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<OrderCreate> }) => {
      const response = await purchasesApi.updateOrder(id, data);
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.orders() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.order(id) });
    },
  });
}

export function useDeletePurchaseOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await purchasesApi.deleteOrder(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.orders() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.summary() });
    },
  });
}

export function useValidatePurchaseOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await purchasesApi.validateOrder(id);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.orders() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.order(id) });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.summary() });
    },
  });
}

export function useConfirmPurchaseOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await purchasesApi.confirmOrder(id);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.orders() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.order(id) });
    },
  });
}

export function useReceivePurchaseOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes?: string }) => {
      const response = await purchasesApi.receiveOrder(id, { notes });
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.orders() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.order(id) });
    },
  });
}

export function useCancelPurchaseOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await purchasesApi.cancelOrder(id);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.orders() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.order(id) });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.summary() });
    },
  });
}

export function useCreateInvoiceFromOrder() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (orderId: string) => {
      const response = await purchasesApi.createInvoiceFromOrder(orderId);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.orders() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.invoices() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.summary() });
    },
  });
}

// ============================================================================
// INVOICES - Queries
// ============================================================================

export function usePurchaseInvoices(filters?: InvoiceFilters) {
  return useQuery({
    queryKey: purchasesKeys.invoicesList(filters),
    queryFn: async () => {
      const response = await purchasesApi.listInvoices(filters);
      return response.data ?? { items: [], total: 0, page: 1, pages: 0 };
    },
  });
}

export function usePurchaseInvoice(id: string) {
  return useQuery({
    queryKey: purchasesKeys.invoice(id),
    queryFn: async () => {
      const response = await purchasesApi.getInvoice(id);
      return response.data;
    },
    enabled: !!id && id !== 'new',
  });
}

// ============================================================================
// INVOICES - Mutations
// ============================================================================

export function useCreatePurchaseInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: InvoiceCreate) => {
      const response = await purchasesApi.createInvoice(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.invoices() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.summary() });
    },
  });
}

export function useUpdatePurchaseInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<InvoiceCreate> }) => {
      const response = await purchasesApi.updateInvoice(id, data);
      return response.data;
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.invoices() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.invoice(id) });
    },
  });
}

export function useDeletePurchaseInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await purchasesApi.deleteInvoice(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.invoices() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.summary() });
    },
  });
}

export function useValidatePurchaseInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await purchasesApi.validateInvoice(id);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.invoices() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.invoice(id) });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.summary() });
    },
  });
}

export function useCancelPurchaseInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await purchasesApi.cancelInvoice(id);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: purchasesKeys.invoices() });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.invoice(id) });
      queryClient.invalidateQueries({ queryKey: purchasesKeys.summary() });
    },
  });
}
