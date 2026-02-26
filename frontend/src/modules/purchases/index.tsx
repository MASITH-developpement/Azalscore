/**
 * AZALSCORE Module - Achats
 * ==========================
 * Module de gestion des achats: Fournisseurs, Commandes, Factures fournisseurs
 *
 * Structure modulaire refactorisee depuis le fichier monolithique (2,962 lignes)
 * vers une architecture avec separation des responsabilites.
 *
 * @module purchases
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';

// ============================================================================
// Pages
// ============================================================================

import {
  PurchasesDashboard,
  SuppliersListPage,
  SupplierFormPage,
  SupplierDetailView,
  OrdersListPage,
  OrderFormPage,
  OrderDetailView,
  InvoicesListPage,
  InvoiceFormPage,
  InvoiceDetailView,
} from './pages';

// ============================================================================
// RE-EXPORTS
// ============================================================================

// Types
export type {
  Supplier,
  SupplierStatus,
  SupplierCreate,
  PurchaseOrder,
  PurchaseOrderStatus,
  PurchaseOrderLine,
  PurchaseInvoice,
  PurchaseInvoiceStatus,
  PurchaseSummary,
  PurchaseHistoryEntry,
  LineCalculation,
  VATBreakdown,
} from './types';

// Constants & Helpers
export {
  SUPPLIER_STATUS_CONFIG,
  ORDER_STATUS_CONFIG,
  INVOICE_STATUS_CONFIG,
  PAYMENT_TERMS_OPTIONS,
  TVA_RATES,
  calculateLineTotal,
  calculateLinesTotals,
  calculateVATBreakdown,
  canEditOrder,
  canValidateOrder,
  canCancelOrder,
  canCreateInvoiceFromOrder,
  canEditInvoice,
  canValidateInvoice,
  canPayInvoice,
  canCancelInvoice,
  getPaymentTermsLabel,
  isOverdue,
  getDaysUntilDue,
} from './types';

// API
export { purchasesApi } from './api';
export type {
  PaginatedResponse,
  SupplierFilters,
  OrderFilters,
  InvoiceFilters,
  OrderLineCreate,
  OrderCreate,
  InvoiceCreate,
} from './api';

// Hooks
export {
  purchasesKeys,
  usePurchaseSummary,
  useSuppliers,
  useSupplier,
  useSuppliersLookup,
  useCreateSupplier,
  useUpdateSupplier,
  useDeleteSupplier,
  useApproveSupplier,
  useBlockSupplier,
  usePurchaseOrders,
  usePurchaseOrder,
  useCreatePurchaseOrder,
  useUpdatePurchaseOrder,
  useDeletePurchaseOrder,
  useValidatePurchaseOrder,
  useConfirmPurchaseOrder,
  useReceivePurchaseOrder,
  useCancelPurchaseOrder,
  useCreateInvoiceFromOrder,
  usePurchaseInvoices,
  usePurchaseInvoice,
  useCreatePurchaseInvoice,
  useUpdatePurchaseInvoice,
  useDeletePurchaseInvoice,
  useValidatePurchaseInvoice,
  useCancelPurchaseInvoice,
} from './hooks';

// Components
export {
  OrderStatusBadge,
  InvoiceStatusBadge,
  SupplierStatusBadge,
  LineEditor,
  FilterBar,
  type LineFormData,
  type FilterState,
} from './components';

// Pages
export {
  PurchasesDashboard,
  SuppliersListPage,
  SupplierFormPage,
  SupplierDetailView,
  OrdersListPage,
  OrderFormPage,
  OrderDetailView,
  InvoicesListPage,
  InvoiceFormPage,
  InvoiceDetailView,
} from './pages';

// ============================================================================
// ROUTES
// ============================================================================

export const PurchasesRoutes: React.FC = () => (
  <Routes>
    <Route index element={<PurchasesDashboard />} />
    {/* Suppliers */}
    <Route path="suppliers" element={<SuppliersListPage />} />
    <Route path="suppliers/new" element={<SupplierFormPage />} />
    <Route path="suppliers/:id" element={<SupplierDetailView />} />
    <Route path="suppliers/:id/edit" element={<SupplierFormPage />} />
    {/* Orders */}
    <Route path="orders" element={<OrdersListPage />} />
    <Route path="orders/new" element={<OrderFormPage />} />
    <Route path="orders/:id" element={<OrderDetailView />} />
    <Route path="orders/:id/edit" element={<OrderFormPage />} />
    {/* Invoices */}
    <Route path="invoices" element={<InvoicesListPage />} />
    <Route path="invoices/new" element={<InvoiceFormPage />} />
    <Route path="invoices/:id" element={<InvoiceDetailView />} />
    <Route path="invoices/:id/edit" element={<InvoiceFormPage />} />
  </Routes>
);

export default PurchasesRoutes;
