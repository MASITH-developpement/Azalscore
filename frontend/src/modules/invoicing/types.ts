/**
 * AZALSCORE Module - Invoicing Types
 * Types, constantes et utilitaires pour la facturation
 */

// ============================================================================
// TYPES
// ============================================================================

export type DocumentType = 'QUOTE' | 'ORDER' | 'INVOICE' | 'CREDIT_NOTE' | 'PROFORMA' | 'DELIVERY';
export type DocumentStatus = 'DRAFT' | 'PENDING' | 'VALIDATED' | 'SENT' | 'ACCEPTED' | 'REJECTED' | 'DELIVERED' | 'INVOICED' | 'PAID' | 'CANCELLED';
export type PaymentMethod = 'BANK_TRANSFER' | 'CHECK' | 'CREDIT_CARD' | 'CASH' | 'DIRECT_DEBIT' | 'PAYPAL' | 'OTHER';
export type PaymentTerms = 'IMMEDIATE' | 'NET_15' | 'NET_30' | 'NET_45' | 'NET_60' | 'NET_90' | 'END_OF_MONTH' | 'CUSTOM';

export interface DocumentLine {
  id: string;
  document_id: string;
  line_number: number;
  product_id?: string;
  product_code?: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount_percent: number;
  tax_rate: number;
  discount_amount: number;
  subtotal: number;
  tax_amount: number;
  total: number;
  notes?: string;
  created_at: string;
}

export interface Document {
  id: string;
  number: string;
  type: DocumentType;
  status: DocumentStatus;
  customer_id: string;
  customer_name?: string;
  customer_email?: string;
  customer_code?: string;
  customer_siret?: string;
  customer_siren?: string;
  customer_vat_number?: string;
  customer_legal_form?: string;
  opportunity_id?: string;
  date: string;
  due_date?: string;
  validity_date?: string;
  delivery_date?: string;
  subtotal: number;
  discount_percent: number;
  discount_amount: number;
  tax_amount: number;
  total: number;
  currency: string;
  paid_amount?: number;
  remaining_amount?: number;
  // Addresses
  billing_address?: AddressData;
  shipping_address?: AddressData;
  // Shipping
  shipping_method?: string;
  shipping_cost?: number;
  tracking_number?: string;
  // Terms
  notes?: string;
  internal_notes?: string;
  terms?: string;
  payment_terms?: PaymentTerms;
  payment_method?: PaymentMethod;
  reference?: string;
  // Relations
  parent_id?: string;
  parent_number?: string;
  invoice_id?: string;
  children?: DocumentChild[];
  // Workflow
  assigned_to?: string;
  validated_by?: string;
  validated_by_name?: string;
  validated_at?: string;
  sent_at?: string;
  paid_at?: string;
  cancelled_at?: string;
  cancelled_reason?: string;
  pdf_url?: string;
  // Meta
  created_by: string;
  created_by_name?: string;
  created_at: string;
  updated_at: string;
  lines: DocumentLine[];
  // Computed
  lines_count?: number;
  is_overdue?: boolean;
  days_until_due?: number;
  // Stats
  stats?: DocumentStats;
  history?: DocumentHistoryEntry[];
  related_documents?: RelatedDocument[];
}

export interface AddressData {
  line1?: string;
  line2?: string;
  city?: string;
  postal_code?: string;
  state?: string;
  country?: string;
}

export interface DocumentChild {
  id: string;
  number: string;
  type: DocumentType;
  date: string;
  total: number;
}

export interface DocumentStats {
  margin_percent?: number;
  margin_amount?: number;
  cost_total?: number;
  payment_received?: number;
  payment_pending?: number;
}

export interface DocumentHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

export interface RelatedDocument {
  id: string;
  number: string;
  type: DocumentType;
  status: DocumentStatus;
  date: string;
  total: number;
  relation: 'parent' | 'child' | 'linked';
}

export interface Customer {
  id: string;
  code: string;
  name: string;
  email?: string;
  phone?: string;
}

export interface LineFormData {
  id?: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount_percent: number;
  tax_rate: number;
}

// ============================================================================
// CONSTANTS
// ============================================================================

export const DOCUMENT_STATUS_CONFIG: Record<DocumentStatus, {
  label: string;
  color: 'gray' | 'blue' | 'green' | 'orange' | 'red' | 'purple' | 'cyan' | 'yellow';
  description: string;
}> = {
  DRAFT: {
    label: 'Brouillon',
    color: 'gray',
    description: 'Document en cours de redaction'
  },
  PENDING: {
    label: 'En attente',
    color: 'yellow',
    description: 'Document en attente de validation'
  },
  VALIDATED: {
    label: 'Valide',
    color: 'blue',
    description: 'Document valide et pret a etre envoye'
  },
  SENT: {
    label: 'Envoye',
    color: 'purple',
    description: 'Document envoye au client'
  },
  ACCEPTED: {
    label: 'Accepte',
    color: 'cyan',
    description: 'Document accepte par le client'
  },
  REJECTED: {
    label: 'Rejete',
    color: 'red',
    description: 'Document rejete par le client'
  },
  DELIVERED: {
    label: 'Livre',
    color: 'blue',
    description: 'Marchandises livrees'
  },
  INVOICED: {
    label: 'Facture',
    color: 'orange',
    description: 'Facture generee'
  },
  PAID: {
    label: 'Paye',
    color: 'green',
    description: 'Paiement recu'
  },
  CANCELLED: {
    label: 'Annule',
    color: 'red',
    description: 'Document annule'
  }
};

export const DOCUMENT_TYPE_CONFIG: Record<DocumentType, {
  label: string;
  labelPlural: string;
  prefix: string;
  color: 'blue' | 'orange' | 'green' | 'purple' | 'cyan' | 'red';
}> = {
  QUOTE: {
    label: 'Devis',
    labelPlural: 'Devis',
    prefix: 'DEV',
    color: 'blue'
  },
  ORDER: {
    label: 'Commande',
    labelPlural: 'Commandes',
    prefix: 'CMD',
    color: 'orange'
  },
  INVOICE: {
    label: 'Facture',
    labelPlural: 'Factures',
    prefix: 'FAC',
    color: 'green'
  },
  CREDIT_NOTE: {
    label: 'Avoir',
    labelPlural: 'Avoirs',
    prefix: 'AVO',
    color: 'red'
  },
  PROFORMA: {
    label: 'Proforma',
    labelPlural: 'Proformas',
    prefix: 'PRO',
    color: 'purple'
  },
  DELIVERY: {
    label: 'Bon de livraison',
    labelPlural: 'Bons de livraison',
    prefix: 'BL',
    color: 'cyan'
  }
};

export const TRANSFORM_WORKFLOW: Partial<Record<DocumentType, {
  target: DocumentType;
  label: string;
}>> = {
  QUOTE: { target: 'ORDER', label: 'Transformer en commande' },
  PROFORMA: { target: 'ORDER', label: 'Transformer en commande' },
  ORDER: { target: 'INVOICE', label: 'Transformer en facture' },
  DELIVERY: { target: 'INVOICE', label: 'Transformer en facture' }
};

export const TVA_RATES = [
  { value: 0, label: '0%' },
  { value: 5.5, label: '5,5%' },
  { value: 10, label: '10%' },
  { value: 20, label: '20%' }
];

export const PAYMENT_TERMS_OPTIONS: { value: PaymentTerms; label: string }[] = [
  { value: 'IMMEDIATE', label: 'Comptant' },
  { value: 'NET_15', label: 'Net 15 jours' },
  { value: 'NET_30', label: 'Net 30 jours' },
  { value: 'NET_45', label: 'Net 45 jours' },
  { value: 'NET_60', label: 'Net 60 jours' },
  { value: 'NET_90', label: 'Net 90 jours' },
  { value: 'END_OF_MONTH', label: 'Fin de mois' },
  { value: 'CUSTOM', label: 'Personnalise' }
];

export const PAYMENT_METHODS_OPTIONS: { value: PaymentMethod; label: string }[] = [
  { value: 'BANK_TRANSFER', label: 'Virement bancaire' },
  { value: 'CHECK', label: 'Cheque' },
  { value: 'CREDIT_CARD', label: 'Carte bancaire' },
  { value: 'CASH', label: 'Especes' },
  { value: 'DIRECT_DEBIT', label: 'Prelevement' },
  { value: 'PAYPAL', label: 'PayPal' },
  { value: 'OTHER', label: 'Autre' }
];

// Legacy exports for compatibility
export const PAYMENT_TERMS = PAYMENT_TERMS_OPTIONS;
export const PAYMENT_METHODS = PAYMENT_METHODS_OPTIONS;

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export function calculateLineTotal(line: LineFormData): {
  subtotal: number;
  taxAmount: number;
  total: number;
  discountAmount: number;
} {
  const baseAmount = line.quantity * line.unit_price;
  const discountAmount = baseAmount * (line.discount_percent / 100);
  const subtotal = baseAmount - discountAmount;
  const taxAmount = subtotal * (line.tax_rate / 100);
  const total = subtotal + taxAmount;

  return { subtotal, taxAmount, total, discountAmount };
}

export function calculateDocumentTotals(lines: LineFormData[]): {
  subtotal: number;
  taxAmount: number;
  total: number;
  discountAmount: number;
} {
  return lines.reduce(
    (acc, line) => {
      const calc = calculateLineTotal(line);
      return {
        subtotal: acc.subtotal + calc.subtotal,
        taxAmount: acc.taxAmount + calc.taxAmount,
        total: acc.total + calc.total,
        discountAmount: acc.discountAmount + calc.discountAmount
      };
    },
    { subtotal: 0, taxAmount: 0, total: 0, discountAmount: 0 }
  );
}

export function getDocumentAgeDays(doc: Document): number {
  const created = new Date(doc.created_at);
  const now = new Date();
  return Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24));
}

export function getDaysUntilDue(doc: Document): number | null {
  if (!doc.due_date) return null;
  const due = new Date(doc.due_date);
  const now = new Date();
  return Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

export function isDocumentOverdue(doc: Document): boolean {
  if (doc.status === 'PAID' || doc.status === 'CANCELLED') return false;
  const days = getDaysUntilDue(doc);
  return days !== null && days < 0;
}

export function getStatusLabel(status: DocumentStatus): string {
  return DOCUMENT_STATUS_CONFIG[status]?.label || status;
}

export function getStatusColor(status: DocumentStatus): string {
  return DOCUMENT_STATUS_CONFIG[status]?.color || 'gray';
}

export function getTypeLabel(type: DocumentType): string {
  return DOCUMENT_TYPE_CONFIG[type]?.label || type;
}

export function getTypeColor(type: DocumentType): string {
  return DOCUMENT_TYPE_CONFIG[type]?.color || 'blue';
}

export function canEditDocument(doc: Document): boolean {
  return doc.status === 'DRAFT';
}

export function canValidateDocument(doc: Document): boolean {
  return doc.status === 'DRAFT' && doc.lines.length > 0;
}

export function canTransformDocument(doc: Document): boolean {
  return doc.status === 'VALIDATED' && !!TRANSFORM_WORKFLOW[doc.type];
}

export function canCancelDocument(doc: Document): boolean {
  return doc.status !== 'CANCELLED' && doc.status !== 'PAID';
}

export function getNextTransformType(type: DocumentType): DocumentType | null {
  return TRANSFORM_WORKFLOW[type]?.target || null;
}
