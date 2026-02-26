/**
 * AZALSCORE - Procurement Management API
 * =======================================
 * Complete typed API client for procurement module.
 * Covers: Suppliers, Requisitions, Purchase Orders, Receipts, Invoices, Payments, Evaluations
 */

import { api } from '@/core/api-client';

// ============================================================================
// ENUMS
// ============================================================================

export type SupplierType =
  | 'MANUFACTURER'
  | 'DISTRIBUTOR'
  | 'RETAILER'
  | 'WHOLESALER'
  | 'SERVICE'
  | 'SUBCONTRACTOR'
  | 'BROKER'
  | 'OTHER';

export type SupplierStatus = 'PROSPECT' | 'PENDING_APPROVAL' | 'APPROVED' | 'SUSPENDED' | 'BLOCKED';

export type RequisitionStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'ORDERED' | 'CLOSED';

export type QuotationStatus = 'REQUESTED' | 'RECEIVED' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED';

export type PurchaseOrderStatus =
  | 'DRAFT'
  | 'VALIDATED'
  | 'SENT'
  | 'CONFIRMED'
  | 'PARTIAL_RECEIPT'
  | 'RECEIVED'
  | 'INVOICED'
  | 'COMPLETE'
  | 'CANCELLED';

export type ReceivingStatus = 'PENDING' | 'VALIDATED' | 'CANCELLED';

export type PurchaseInvoiceStatus = 'DRAFT' | 'VALIDATED' | 'PARTIAL_PAID' | 'PAID' | 'CANCELLED';

// ============================================================================
// SUPPLIERS
// ============================================================================

export interface Supplier {
  id: string;
  code: string;
  name: string;
  legal_name?: string | null;
  type: SupplierType;
  status: SupplierStatus;
  tax_id?: string | null;
  vat_number?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  postal_code?: string | null;
  city?: string | null;
  country: string;
  payment_terms: string;
  currency: string;
  category?: string | null;
  credit_limit?: string | null;
  discount_rate: string;
  bank_name?: string | null;
  iban?: string | null;
  bic?: string | null;
  rating?: string | null;
  last_evaluation_date?: string | null;
  notes?: string | null;
  tags: string[];
  is_active: boolean;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupplierCreate {
  code: string;
  name: string;
  legal_name?: string | null;
  type?: SupplierType;
  tax_id?: string | null;
  vat_number?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  postal_code?: string | null;
  city?: string | null;
  country?: string;
  payment_terms?: string;
  currency?: string;
  category?: string | null;
  credit_limit?: string | null;
  discount_rate?: string;
  bank_name?: string | null;
  iban?: string | null;
  bic?: string | null;
  notes?: string | null;
  tags?: string[];
}

export interface SupplierUpdate {
  name?: string | null;
  legal_name?: string | null;
  type?: SupplierType | null;
  status?: SupplierStatus | null;
  tax_id?: string | null;
  vat_number?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  postal_code?: string | null;
  city?: string | null;
  country?: string | null;
  payment_terms?: string | null;
  currency?: string | null;
  credit_limit?: string | null;
  discount_rate?: string | null;
  category?: string | null;
  bank_name?: string | null;
  iban?: string | null;
  bic?: string | null;
  notes?: string | null;
  tags?: string[] | null;
  is_active?: boolean | null;
}

export interface SupplierList {
  items: Supplier[];
  total: number;
}

// ============================================================================
// SUPPLIER CONTACTS
// ============================================================================

export interface SupplierContact {
  id: string;
  supplier_id: string;
  first_name: string;
  last_name: string;
  job_title?: string | null;
  department?: string | null;
  email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  is_primary: boolean;
  notes?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupplierContactCreate {
  first_name: string;
  last_name: string;
  job_title?: string | null;
  department?: string | null;
  email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  is_primary?: boolean;
  notes?: string | null;
}

// ============================================================================
// REQUISITIONS
// ============================================================================

export interface RequisitionLine {
  id: string;
  requisition_id: string;
  line_number: number;
  product_id?: string | null;
  product_code?: string | null;
  description: string;
  quantity: string;
  unit: string;
  estimated_price?: string | null;
  total?: string | null;
  preferred_supplier_id?: string | null;
  required_date?: string | null;
  ordered_quantity: string;
  purchase_order_id?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface RequisitionLineCreate {
  product_id?: string | null;
  product_code?: string | null;
  description: string;
  quantity: string;
  unit?: string;
  estimated_price?: string | null;
  preferred_supplier_id?: string | null;
  required_date?: string | null;
  notes?: string | null;
}

export interface Requisition {
  id: string;
  number: string;
  status: RequisitionStatus;
  priority: string;
  title: string;
  description?: string | null;
  justification?: string | null;
  requester_id: string;
  department_id?: string | null;
  requested_date: string;
  required_date?: string | null;
  estimated_total: string;
  currency: string;
  budget_code?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  rejection_reason?: string | null;
  notes?: string | null;
  lines: RequisitionLine[];
  created_at: string;
  updated_at: string;
}

export interface RequisitionCreate {
  title: string;
  description?: string | null;
  justification?: string | null;
  priority?: string;
  requested_date: string;
  required_date?: string | null;
  budget_code?: string | null;
  department_id?: string | null;
  notes?: string | null;
  lines?: RequisitionLineCreate[];
}

export interface RequisitionList {
  items: Requisition[];
  total: number;
}

// ============================================================================
// PURCHASE ORDERS
// ============================================================================

export interface OrderLine {
  id: string;
  order_id: string;
  line_number: number;
  product_id?: string | null;
  product_code?: string | null;
  description: string;
  quantity: string;
  unit: string;
  unit_price: string;
  discount_percent: string;
  tax_rate: string;
  total: string;
  expected_date?: string | null;
  requisition_line_id?: string | null;
  received_quantity: string;
  invoiced_quantity: string;
  notes?: string | null;
  created_at: string;
}

export interface OrderLineCreate {
  product_id?: string | null;
  product_code?: string | null;
  description: string;
  quantity: string;
  unit?: string;
  unit_price: string;
  discount_percent?: string;
  tax_rate?: string;
  expected_date?: string | null;
  requisition_line_id?: string | null;
  notes?: string | null;
}

export interface PurchaseOrder {
  id: string;
  number: string;
  supplier_id: string;
  requisition_id?: string | null;
  quotation_id?: string | null;
  status: PurchaseOrderStatus;
  order_date: string;
  expected_date?: string | null;
  confirmed_date?: string | null;
  delivery_address?: string | null;
  delivery_contact?: string | null;
  currency: string;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  shipping_cost: string;
  total: string;
  payment_terms?: string | null;
  incoterms?: string | null;
  received_amount: string;
  invoiced_amount: string;
  supplier_reference?: string | null;
  notes?: string | null;
  lines: OrderLine[];
  sent_at?: string | null;
  confirmed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PurchaseOrderCreate {
  supplier_id: string;
  requisition_id?: string | null;
  quotation_id?: string | null;
  order_date: string;
  expected_date?: string | null;
  delivery_address?: string | null;
  delivery_contact?: string | null;
  currency?: string;
  payment_terms?: string | null;
  incoterms?: string | null;
  shipping_cost?: string;
  notes?: string | null;
  internal_notes?: string | null;
  lines?: OrderLineCreate[];
}

export interface PurchaseOrderList {
  items: PurchaseOrder[];
  total: number;
}

// ============================================================================
// GOODS RECEIPTS
// ============================================================================

export interface ReceiptLine {
  id: string;
  receipt_id: string;
  line_number: number;
  order_line_id: string;
  product_id?: string | null;
  product_code?: string | null;
  description: string;
  ordered_quantity: string;
  received_quantity: string;
  rejected_quantity: string;
  unit: string;
  rejection_reason?: string | null;
  lot_number?: string | null;
  expiry_date?: string | null;
  serial_numbers: string[];
  notes?: string | null;
  created_at: string;
}

export interface ReceiptLineCreate {
  order_line_id: string;
  product_id?: string | null;
  product_code?: string | null;
  description: string;
  ordered_quantity: string;
  received_quantity: string;
  rejected_quantity?: string;
  unit?: string;
  rejection_reason?: string | null;
  lot_number?: string | null;
  expiry_date?: string | null;
  notes?: string | null;
}

export interface GoodsReceipt {
  id: string;
  number: string;
  order_id: string;
  supplier_id: string;
  status: ReceivingStatus;
  receipt_date: string;
  delivery_note?: string | null;
  carrier?: string | null;
  tracking_number?: string | null;
  warehouse_id?: string | null;
  location?: string | null;
  notes?: string | null;
  lines: ReceiptLine[];
  received_by?: string | null;
  validated_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface GoodsReceiptCreate {
  order_id: string;
  receipt_date: string;
  delivery_note?: string | null;
  carrier?: string | null;
  tracking_number?: string | null;
  warehouse_id?: string | null;
  location?: string | null;
  notes?: string | null;
  lines?: ReceiptLineCreate[];
}

export interface GoodsReceiptList {
  items: GoodsReceipt[];
  total: number;
}

// ============================================================================
// PURCHASE INVOICES
// ============================================================================

export interface InvoiceLine {
  id: string;
  invoice_id: string;
  line_number: number;
  order_line_id?: string | null;
  product_id?: string | null;
  product_code?: string | null;
  description: string;
  quantity: string;
  unit: string;
  unit_price: string;
  discount_percent: string;
  tax_rate: string;
  tax_amount: string;
  total: string;
  account_id?: string | null;
  analytic_code?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface InvoiceLineCreate {
  order_line_id?: string | null;
  product_id?: string | null;
  product_code?: string | null;
  description: string;
  quantity: string;
  unit?: string;
  unit_price: string;
  discount_percent?: string;
  tax_rate?: string;
  account_id?: string | null;
  analytic_code?: string | null;
  notes?: string | null;
}

export interface PurchaseInvoice {
  id: string;
  number: string;
  supplier_id: string;
  order_id?: string | null;
  status: PurchaseInvoiceStatus;
  invoice_date: string;
  due_date?: string | null;
  supplier_invoice_number?: string | null;
  supplier_invoice_date?: string | null;
  currency: string;
  subtotal: string;
  discount_amount: string;
  tax_amount: string;
  total: string;
  paid_amount: string;
  remaining_amount: string;
  payment_terms?: string | null;
  payment_method?: string | null;
  notes?: string | null;
  lines: InvoiceLine[];
  validated_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PurchaseInvoiceCreate {
  supplier_id: string;
  order_id?: string | null;
  invoice_date: string;
  due_date?: string | null;
  supplier_invoice_number?: string | null;
  supplier_invoice_date?: string | null;
  currency?: string;
  payment_terms?: string | null;
  payment_method?: string | null;
  notes?: string | null;
  lines?: InvoiceLineCreate[];
}

export interface PurchaseInvoiceList {
  items: PurchaseInvoice[];
  total: number;
}

// ============================================================================
// SUPPLIER PAYMENTS
// ============================================================================

export interface PaymentAllocation {
  invoice_id: string;
  amount: string;
}

export interface SupplierPayment {
  id: string;
  number: string;
  supplier_id: string;
  payment_date: string;
  amount: string;
  currency: string;
  payment_method: string;
  reference?: string | null;
  bank_account_id?: string | null;
  journal_entry_id?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface SupplierPaymentCreate {
  supplier_id: string;
  payment_date: string;
  amount: string;
  currency?: string;
  payment_method: string;
  reference?: string | null;
  bank_account_id?: string | null;
  notes?: string | null;
  allocations?: PaymentAllocation[];
}

// ============================================================================
// SUPPLIER EVALUATIONS
// ============================================================================

export interface SupplierEvaluation {
  id: string;
  supplier_id: string;
  evaluation_date: string;
  period_start: string;
  period_end: string;
  quality_score?: string | null;
  price_score?: string | null;
  delivery_score?: string | null;
  service_score?: string | null;
  reliability_score?: string | null;
  overall_score?: string | null;
  total_orders: number;
  total_amount: string;
  on_time_delivery_rate?: string | null;
  quality_rejection_rate?: string | null;
  comments?: string | null;
  recommendations?: string | null;
  evaluated_by?: string | null;
  created_at: string;
}

export interface SupplierEvaluationCreate {
  supplier_id: string;
  evaluation_date: string;
  period_start: string;
  period_end: string;
  quality_score?: string | null;
  price_score?: string | null;
  delivery_score?: string | null;
  service_score?: string | null;
  reliability_score?: string | null;
  comments?: string | null;
  recommendations?: string | null;
}

// ============================================================================
// DASHBOARD
// ============================================================================

export interface ProcurementDashboard {
  // Suppliers
  total_suppliers: number;
  active_suppliers: number;
  pending_approvals: number;
  // Requisitions
  pending_requisitions: number;
  requisitions_this_month: number;
  // Orders
  draft_orders: number;
  pending_orders: number;
  orders_this_month: number;
  orders_amount_this_month: string;
  // Receipts
  pending_receipts: number;
  // Invoices
  pending_invoices: number;
  overdue_invoices: number;
  invoices_this_month: number;
  invoices_amount_this_month: string;
  // Payments
  unpaid_amount: string;
  payments_due_this_week: string;
  // Top suppliers
  top_suppliers_by_amount: Array<Record<string, unknown>>;
  top_suppliers_by_orders: Array<Record<string, unknown>>;
  // By category
  by_category: Record<string, string>;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/procurement';

function buildQueryString(
  params: Record<string, string | number | boolean | undefined | null>
): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// API CLIENT
// ============================================================================

export const procurementApi = {
  // ==========================================================================
  // Suppliers
  // ==========================================================================

  createSupplier: (data: SupplierCreate) =>
    api.post<Supplier>(`${BASE_PATH}/suppliers`, data),

  listSuppliers: (params?: {
    status?: SupplierStatus;
    supplier_type?: SupplierType;
    category?: string;
    search?: string;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }) =>
    api.get<SupplierList>(`${BASE_PATH}/suppliers${buildQueryString(params || {})}`),

  getSupplier: (supplierId: string) =>
    api.get<Supplier>(`${BASE_PATH}/suppliers/${supplierId}`),

  updateSupplier: (supplierId: string, data: SupplierUpdate) =>
    api.put<Supplier>(`${BASE_PATH}/suppliers/${supplierId}`, data),

  approveSupplier: (supplierId: string) =>
    api.post<Supplier>(`${BASE_PATH}/suppliers/${supplierId}/approve`, {}),

  addSupplierContact: (supplierId: string, data: SupplierContactCreate) =>
    api.post<SupplierContact>(`${BASE_PATH}/suppliers/${supplierId}/contacts`, data),

  getSupplierContacts: (supplierId: string) =>
    api.get<SupplierContact[]>(`${BASE_PATH}/suppliers/${supplierId}/contacts`),

  // ==========================================================================
  // Requisitions
  // ==========================================================================

  createRequisition: (data: RequisitionCreate) =>
    api.post<Requisition>(`${BASE_PATH}/requisitions`, data),

  listRequisitions: (params?: {
    requisition_status?: RequisitionStatus;
    requester_id?: string;
    skip?: number;
    limit?: number;
  }) =>
    api.get<RequisitionList>(
      `${BASE_PATH}/requisitions${buildQueryString(params || {})}`
    ),

  getRequisition: (requisitionId: string) =>
    api.get<Requisition>(`${BASE_PATH}/requisitions/${requisitionId}`),

  submitRequisition: (requisitionId: string) =>
    api.post<Requisition>(`${BASE_PATH}/requisitions/${requisitionId}/submit`, {}),

  approveRequisition: (requisitionId: string) =>
    api.post<Requisition>(`${BASE_PATH}/requisitions/${requisitionId}/approve`, {}),

  rejectRequisition: (requisitionId: string, reason: string) =>
    api.post<Requisition>(
      `${BASE_PATH}/requisitions/${requisitionId}/reject${buildQueryString({ reason })}`,
      {}
    ),

  // ==========================================================================
  // Purchase Orders
  // ==========================================================================

  createPurchaseOrder: (data: PurchaseOrderCreate) =>
    api.post<PurchaseOrder>(`${BASE_PATH}/orders`, data),

  listPurchaseOrders: (params?: {
    supplier_id?: string;
    order_status?: PurchaseOrderStatus;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }) =>
    api.get<PurchaseOrderList>(`${BASE_PATH}/orders${buildQueryString(params || {})}`),

  getPurchaseOrder: (orderId: string) =>
    api.get<PurchaseOrder>(`${BASE_PATH}/orders/${orderId}`),

  updatePurchaseOrder: (orderId: string, data: PurchaseOrderCreate) =>
    api.put<PurchaseOrder>(`${BASE_PATH}/orders/${orderId}`, data),

  deletePurchaseOrder: (orderId: string) =>
    api.delete(`${BASE_PATH}/orders/${orderId}`),

  sendPurchaseOrder: (orderId: string) =>
    api.post<PurchaseOrder>(`${BASE_PATH}/orders/${orderId}/send`, {}),

  confirmPurchaseOrder: (
    orderId: string,
    supplierReference?: string,
    confirmedDate?: string
  ) =>
    api.post<PurchaseOrder>(
      `${BASE_PATH}/orders/${orderId}/confirm${buildQueryString({
        supplier_reference: supplierReference,
        confirmed_date: confirmedDate,
      })}`,
      {}
    ),

  validatePurchaseOrder: (orderId: string) =>
    api.post<PurchaseOrder>(`${BASE_PATH}/orders/${orderId}/validate`, {}),

  createInvoiceFromOrder: (
    orderId: string,
    invoiceDate?: string,
    supplierInvoiceNumber?: string
  ) =>
    api.post<PurchaseInvoice>(
      `${BASE_PATH}/orders/${orderId}/create-invoice${buildQueryString({
        invoice_date: invoiceDate,
        supplier_invoice_number: supplierInvoiceNumber,
      })}`,
      {}
    ),

  exportOrdersCsv: (params?: {
    supplier_id?: string;
    order_status?: PurchaseOrderStatus;
    start_date?: string;
    end_date?: string;
  }) =>
    api.get<Blob>(`${BASE_PATH}/orders/export/csv${buildQueryString(params || {})}`),

  // ==========================================================================
  // Goods Receipts
  // ==========================================================================

  listGoodsReceipts: (params?: {
    supplier_id?: string;
    order_id?: string;
    skip?: number;
    limit?: number;
  }) =>
    api.get<GoodsReceiptList>(`${BASE_PATH}/receipts${buildQueryString(params || {})}`),

  createGoodsReceipt: (data: GoodsReceiptCreate) =>
    api.post<GoodsReceipt>(`${BASE_PATH}/receipts`, data),

  validateGoodsReceipt: (receiptId: string) =>
    api.post<GoodsReceipt>(`${BASE_PATH}/receipts/${receiptId}/validate`, {}),

  // ==========================================================================
  // Purchase Invoices
  // ==========================================================================

  createPurchaseInvoice: (data: PurchaseInvoiceCreate) =>
    api.post<PurchaseInvoice>(`${BASE_PATH}/invoices`, data),

  listPurchaseInvoices: (params?: {
    supplier_id?: string;
    invoice_status?: PurchaseInvoiceStatus;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }) =>
    api.get<PurchaseInvoiceList>(
      `${BASE_PATH}/invoices${buildQueryString(params || {})}`
    ),

  getPurchaseInvoice: (invoiceId: string) =>
    api.get<PurchaseInvoice>(`${BASE_PATH}/invoices/${invoiceId}`),

  updatePurchaseInvoice: (invoiceId: string, data: PurchaseInvoiceCreate) =>
    api.put<PurchaseInvoice>(`${BASE_PATH}/invoices/${invoiceId}`, data),

  deletePurchaseInvoice: (invoiceId: string) =>
    api.delete(`${BASE_PATH}/invoices/${invoiceId}`),

  validatePurchaseInvoice: (invoiceId: string) =>
    api.post<PurchaseInvoice>(`${BASE_PATH}/invoices/${invoiceId}/validate`, {}),

  exportInvoicesCsv: (params?: {
    supplier_id?: string;
    invoice_status?: PurchaseInvoiceStatus;
    start_date?: string;
    end_date?: string;
  }) =>
    api.get<Blob>(`${BASE_PATH}/invoices/export/csv${buildQueryString(params || {})}`),

  // ==========================================================================
  // Supplier Payments
  // ==========================================================================

  createSupplierPayment: (data: SupplierPaymentCreate) =>
    api.post<SupplierPayment>(`${BASE_PATH}/payments`, data),

  // ==========================================================================
  // Supplier Evaluations
  // ==========================================================================

  createSupplierEvaluation: (data: SupplierEvaluationCreate) =>
    api.post<SupplierEvaluation>(`${BASE_PATH}/evaluations`, data),

  // ==========================================================================
  // Dashboard
  // ==========================================================================

  getDashboard: () =>
    api.get<ProcurementDashboard>(`${BASE_PATH}/dashboard`),
};

export default procurementApi;
