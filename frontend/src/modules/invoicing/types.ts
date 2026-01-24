/**
 * AZALSCORE Module - Invoicing Types
 * Types, constantes et utilitaires pour la facturation
 */

// ============================================================================
// TYPES
// ============================================================================

export type DocumentType = 'QUOTE' | 'ORDER' | 'INVOICE';
export type DocumentStatus = 'DRAFT' | 'VALIDATED' | 'SENT' | 'PAID' | 'CANCELLED';

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
  date: string;
  due_date?: string;
  validity_date?: string;
  subtotal: number;
  discount_percent: number;
  discount_amount: number;
  tax_amount: number;
  total: number;
  currency: string;
  notes?: string;
  internal_notes?: string;
  payment_terms?: string;
  payment_method?: string;
  reference?: string;
  parent_id?: string;
  parent_number?: string;
  children?: DocumentChild[];
  validated_by?: string;
  validated_by_name?: string;
  validated_at?: string;
  sent_at?: string;
  paid_at?: string;
  cancelled_at?: string;
  cancelled_reason?: string;
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
  color: 'gray' | 'blue' | 'green' | 'orange' | 'red' | 'purple';
  description: string;
}> = {
  DRAFT: {
    label: 'Brouillon',
    color: 'gray',
    description: 'Document en cours de redaction'
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
  color: 'blue' | 'orange' | 'green';
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
  }
};

export const TRANSFORM_WORKFLOW: Partial<Record<DocumentType, {
  target: DocumentType;
  label: string;
}>> = {
  QUOTE: { target: 'ORDER', label: 'Transformer en commande' },
  ORDER: { target: 'INVOICE', label: 'Transformer en facture' }
};

export const TVA_RATES = [
  { value: 0, label: '0%' },
  { value: 5.5, label: '5,5%' },
  { value: 10, label: '10%' },
  { value: 20, label: '20%' }
];

export const PAYMENT_TERMS = [
  { value: 'immediate', label: 'Comptant' },
  { value: 'net15', label: 'Net 15 jours' },
  { value: 'net30', label: 'Net 30 jours' },
  { value: 'net45', label: 'Net 45 jours' },
  { value: 'net60', label: 'Net 60 jours' },
  { value: 'end_of_month', label: 'Fin de mois' }
];

export const PAYMENT_METHODS = [
  { value: 'bank_transfer', label: 'Virement bancaire' },
  { value: 'check', label: 'Cheque' },
  { value: 'card', label: 'Carte bancaire' },
  { value: 'cash', label: 'Especes' },
  { value: 'direct_debit', label: 'Prelevement' }
];

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export function formatCurrency(amount: number, currency = 'EUR'): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency
  }).format(amount);
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('fr-FR');
}

export function formatDateTime(dateStr: string): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('fr-FR', {
    dateStyle: 'short',
    timeStyle: 'short'
  });
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

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
