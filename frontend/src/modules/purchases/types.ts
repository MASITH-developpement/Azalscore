/**
 * AZALSCORE Module - Purchases - Types
 * Types, constants and helpers for the purchases module
 */

// ============================================================================
// TYPES - Supplier
// ============================================================================

export type SupplierStatus = 'PROSPECT' | 'PENDING' | 'APPROVED' | 'BLOCKED' | 'INACTIVE';

export interface Supplier {
  id: string;
  code: string;
  name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  tax_id?: string;
  payment_terms?: string;
  notes?: string;
  status: SupplierStatus;
  // Computed fields
  total_orders?: number;
  total_invoices?: number;
  total_spent?: number;
  last_order_date?: string;
  // Metadata
  created_at: string;
  updated_at: string;
  created_by_name?: string;
}

export interface SupplierCreate {
  name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  tax_id?: string;
  payment_terms?: string;
  notes?: string;
}

// ============================================================================
// TYPES - Purchase Order
// ============================================================================

export type PurchaseOrderStatus = 'DRAFT' | 'SENT' | 'CONFIRMED' | 'PARTIAL' | 'RECEIVED' | 'INVOICED' | 'CANCELLED';

export interface PurchaseOrderLine {
  id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  discount_percent: number;
  // Computed
  subtotal?: number;
  tax_amount?: number;
  total?: number;
}

export interface PurchaseOrder {
  id: string;
  number: string;
  supplier_id: string;
  supplier_name: string;
  supplier_code: string;
  date: string;
  expected_date?: string;
  status: PurchaseOrderStatus;
  reference?: string;
  notes?: string;
  lines: PurchaseOrderLine[];
  total_ht: number;
  total_tax: number;
  total_ttc: number;
  currency: string;
  // Workflow
  validated_at?: string;
  validated_by?: string;
  validated_by_name?: string;
  sent_at?: string;
  confirmed_at?: string;
  received_at?: string;
  // Related
  invoice_ids?: string[];
  reception_ids?: string[];
  // History
  history?: PurchaseHistoryEntry[];
  // Metadata
  created_at: string;
  updated_at: string;
  created_by_name?: string;
}

// ============================================================================
// TYPES - Purchase Invoice
// ============================================================================

export type PurchaseInvoiceStatus = 'DRAFT' | 'VALIDATED' | 'PAID' | 'PARTIAL' | 'CANCELLED';

export interface PurchaseInvoice {
  id: string;
  number: string;
  supplier_id: string;
  supplier_name: string;
  supplier_code: string;
  order_id?: string;
  order_number?: string;
  date: string;
  due_date?: string;
  status: PurchaseInvoiceStatus;
  supplier_reference?: string;
  notes?: string;
  lines: PurchaseOrderLine[];
  total_ht: number;
  total_tax: number;
  total_ttc: number;
  currency: string;
  // Payment
  amount_paid?: number;
  amount_remaining?: number;
  payment_ids?: string[];
  // Workflow
  validated_at?: string;
  validated_by?: string;
  validated_by_name?: string;
  paid_at?: string;
  // History
  history?: PurchaseHistoryEntry[];
  // Metadata
  created_at: string;
  updated_at: string;
  created_by_name?: string;
}

// ============================================================================
// TYPES - History
// ============================================================================

export interface PurchaseHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

// ============================================================================
// TYPES - Summary
// ============================================================================

export interface PurchaseSummary {
  pending_orders: number;
  pending_value: number;
  validated_this_month: number;
  pending_invoices: number;
  total_suppliers: number;
  active_suppliers: number;
}

// ============================================================================
// CONSTANTS - Status Configs
// ============================================================================

export const SUPPLIER_STATUS_CONFIG: Record<SupplierStatus, { label: string; color: 'gray' | 'yellow' | 'green' | 'red' }> = {
  PROSPECT: { label: 'Prospect', color: 'gray' },
  PENDING: { label: 'En attente', color: 'yellow' },
  APPROVED: { label: 'Approuve', color: 'green' },
  BLOCKED: { label: 'Bloque', color: 'red' },
  INACTIVE: { label: 'Inactif', color: 'gray' },
};

export const ORDER_STATUS_CONFIG: Record<PurchaseOrderStatus, { label: string; color: 'gray' | 'blue' | 'orange' | 'yellow' | 'green' | 'purple' | 'red' }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  SENT: { label: 'Envoyee', color: 'blue' },
  CONFIRMED: { label: 'Confirmee', color: 'orange' },
  PARTIAL: { label: 'Partielle', color: 'yellow' },
  RECEIVED: { label: 'Recue', color: 'green' },
  INVOICED: { label: 'Facturee', color: 'purple' },
  CANCELLED: { label: 'Annulee', color: 'red' },
};

export const INVOICE_STATUS_CONFIG: Record<PurchaseInvoiceStatus, { label: string; color: 'gray' | 'blue' | 'green' | 'yellow' | 'red' }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  VALIDATED: { label: 'Validee', color: 'blue' },
  PAID: { label: 'Payee', color: 'green' },
  PARTIAL: { label: 'Partielle', color: 'yellow' },
  CANCELLED: { label: 'Annulee', color: 'red' },
};

// ============================================================================
// CONSTANTS - Options
// ============================================================================

export const PAYMENT_TERMS_OPTIONS = [
  { value: 'IMMEDIATE', label: 'Paiement immediat' },
  { value: 'NET15', label: 'Net 15 jours' },
  { value: 'NET30', label: 'Net 30 jours' },
  { value: 'NET45', label: 'Net 45 jours' },
  { value: 'NET60', label: 'Net 60 jours' },
  { value: 'EOM', label: 'Fin de mois' },
  { value: 'EOM30', label: 'Fin de mois + 30' },
];

export const TVA_RATES = [
  { value: 0, label: '0%' },
  { value: 5.5, label: '5.5%' },
  { value: 10, label: '10%' },
  { value: 20, label: '20%' },
];

// ============================================================================
// HELPERS - Line Calculations
// ============================================================================

export interface LineCalculation {
  subtotal: number;
  taxAmount: number;
  total: number;
}

export const calculateLineTotal = (line: PurchaseOrderLine): LineCalculation => {
  const baseAmount = line.quantity * line.unit_price;
  const discountAmount = baseAmount * (line.discount_percent / 100);
  const subtotal = baseAmount - discountAmount;
  const taxAmount = subtotal * (line.tax_rate / 100);
  const total = subtotal + taxAmount;

  return { subtotal, taxAmount, total };
};

export const calculateLinesTotals = (lines: PurchaseOrderLine[]): { total_ht: number; total_tax: number; total_ttc: number } => {
  return lines.reduce(
    (acc, line) => {
      const calc = calculateLineTotal(line);
      return {
        total_ht: acc.total_ht + calc.subtotal,
        total_tax: acc.total_tax + calc.taxAmount,
        total_ttc: acc.total_ttc + calc.total,
      };
    },
    { total_ht: 0, total_tax: 0, total_ttc: 0 }
  );
};

// ============================================================================
// HELPERS - VAT Breakdown
// ============================================================================

export interface VATBreakdown {
  rate: number;
  base: number;
  amount: number;
}

export const calculateVATBreakdown = (lines: PurchaseOrderLine[]): VATBreakdown[] => {
  const breakdown: Record<number, { base: number; amount: number }> = {};

  lines.forEach((line) => {
    const calc = calculateLineTotal(line);
    if (!breakdown[line.tax_rate]) {
      breakdown[line.tax_rate] = { base: 0, amount: 0 };
    }
    breakdown[line.tax_rate].base += calc.subtotal;
    breakdown[line.tax_rate].amount += calc.taxAmount;
  });

  return Object.entries(breakdown)
    .map(([rate, data]) => ({
      rate: parseFloat(rate),
      base: data.base,
      amount: data.amount,
    }))
    .sort((a, b) => a.rate - b.rate);
};

// ============================================================================
// HELPERS - Status Checks
// ============================================================================

export const canEditOrder = (order: PurchaseOrder): boolean => {
  return order.status === 'DRAFT';
};

export const canValidateOrder = (order: PurchaseOrder): boolean => {
  return order.status === 'DRAFT' && order.lines.length > 0;
};

export const canCancelOrder = (order: PurchaseOrder): boolean => {
  return order.status === 'DRAFT' || order.status === 'SENT';
};

export const canCreateInvoiceFromOrder = (order: PurchaseOrder): boolean => {
  return order.status === 'SENT' || order.status === 'CONFIRMED' || order.status === 'RECEIVED';
};

export const canEditInvoice = (invoice: PurchaseInvoice): boolean => {
  return invoice.status === 'DRAFT';
};

export const canValidateInvoice = (invoice: PurchaseInvoice): boolean => {
  return invoice.status === 'DRAFT' && invoice.lines.length > 0;
};

export const canPayInvoice = (invoice: PurchaseInvoice): boolean => {
  return invoice.status === 'VALIDATED' || invoice.status === 'PARTIAL';
};

export const canCancelInvoice = (invoice: PurchaseInvoice): boolean => {
  return invoice.status === 'DRAFT';
};

// ============================================================================
// HELPERS - Payment Terms
// ============================================================================

export const getPaymentTermsLabel = (value?: string): string => {
  if (!value) return '-';
  const option = PAYMENT_TERMS_OPTIONS.find((o) => o.value === value);
  return option?.label || value;
};

// ============================================================================
// HELPERS - Due Date
// ============================================================================

export const isOverdue = (dueDate?: string): boolean => {
  if (!dueDate) return false;
  return new Date(dueDate) < new Date();
};

export const getDaysUntilDue = (dueDate?: string): number | null => {
  if (!dueDate) return null;
  const due = new Date(dueDate);
  const now = new Date();
  const diffTime = due.getTime() - now.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};
