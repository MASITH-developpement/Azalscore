/**
 * AZALSCORE - Module Documents Unifié
 * Constantes et configurations
 */

import type {
  DocumentType,
  DocumentCategory,
  DocumentStatus,
  PartnerStatus,
} from './types';

// ============================================================
// CONFIGURATION DES TYPES DE DOCUMENTS
// ============================================================

export interface DocumentTypeConfig {
  type: DocumentType;
  category: DocumentCategory;
  labelKey: string;
  labelPluralKey: string;
  prefix: string;
  partnerType: 'customer' | 'supplier';
  hasValidityDate?: boolean;
  hasDueDate?: boolean;
  hasExpectedDate?: boolean;
  hasSupplierReference?: boolean;
  canConvertTo?: DocumentType;
}

export const DOCUMENT_TYPE_CONFIG: Record<DocumentType, DocumentTypeConfig> = {
  QUOTE: {
    type: 'QUOTE',
    category: 'SALES',
    labelKey: 'documents.types.quote',
    labelPluralKey: 'documents.types.quotes',
    prefix: 'DEV',
    partnerType: 'customer',
    hasValidityDate: true,
    canConvertTo: 'INVOICE',
  },
  INVOICE: {
    type: 'INVOICE',
    category: 'SALES',
    labelKey: 'documents.types.invoice',
    labelPluralKey: 'documents.types.invoices',
    prefix: 'FAC',
    partnerType: 'customer',
    hasDueDate: true,
  },
  CREDIT_NOTE: {
    type: 'CREDIT_NOTE',
    category: 'SALES',
    labelKey: 'documents.types.creditNote',
    labelPluralKey: 'documents.types.creditNotes',
    prefix: 'AVO',
    partnerType: 'customer',
  },
  PURCHASE_ORDER: {
    type: 'PURCHASE_ORDER',
    category: 'PURCHASES',
    labelKey: 'documents.types.purchaseOrder',
    labelPluralKey: 'documents.types.purchaseOrders',
    prefix: 'CF',
    partnerType: 'supplier',
    hasExpectedDate: true,
    canConvertTo: 'PURCHASE_INVOICE',
  },
  PURCHASE_INVOICE: {
    type: 'PURCHASE_INVOICE',
    category: 'PURCHASES',
    labelKey: 'documents.types.purchaseInvoice',
    labelPluralKey: 'documents.types.purchaseInvoices',
    prefix: 'FF',
    partnerType: 'supplier',
    hasDueDate: true,
    hasSupplierReference: true,
  },
};

// ============================================================
// CONFIGURATION DES STATUTS
// ============================================================

export interface StatusConfig {
  labelKey: string;
  color: string;
}

export const STATUS_CONFIG: Record<DocumentStatus, StatusConfig> = {
  // Statuts communs
  DRAFT: { labelKey: 'documents.status.draft', color: 'gray' },
  VALIDATED: { labelKey: 'documents.status.validated', color: 'green' },
  SENT: { labelKey: 'documents.status.sent', color: 'blue' },
  PAID: { labelKey: 'documents.status.paid', color: 'green' },
  CANCELLED: { labelKey: 'documents.status.cancelled', color: 'red' },
  // Statuts commandes
  CONFIRMED: { labelKey: 'documents.status.confirmed', color: 'orange' },
  PARTIAL: { labelKey: 'documents.status.partial', color: 'yellow' },
  RECEIVED: { labelKey: 'documents.status.received', color: 'green' },
  INVOICED: { labelKey: 'documents.status.invoiced', color: 'purple' },
};

export const PARTNER_STATUS_CONFIG: Record<PartnerStatus, StatusConfig> = {
  PROSPECT: { labelKey: 'partners.status.prospect', color: 'gray' },
  PENDING: { labelKey: 'partners.status.pending', color: 'yellow' },
  APPROVED: { labelKey: 'partners.status.approved', color: 'green' },
  ACTIVE: { labelKey: 'partners.status.active', color: 'green' },
  BLOCKED: { labelKey: 'partners.status.blocked', color: 'red' },
  INACTIVE: { labelKey: 'partners.status.inactive', color: 'gray' },
};

// ============================================================
// STATUTS PAR TYPE DE DOCUMENT
// ============================================================

export const SALES_DOCUMENT_STATUSES: DocumentStatus[] = [
  'DRAFT',
  'VALIDATED',
  'SENT',
  'PAID',
  'CANCELLED',
];

export const PURCHASE_ORDER_STATUSES: DocumentStatus[] = [
  'DRAFT',
  'SENT',
  'CONFIRMED',
  'PARTIAL',
  'RECEIVED',
  'INVOICED',
  'CANCELLED',
];

export const PURCHASE_INVOICE_STATUSES: DocumentStatus[] = [
  'DRAFT',
  'VALIDATED',
  'PAID',
  'PARTIAL',
  'CANCELLED',
];

export const getStatusesForType = (type: DocumentType): DocumentStatus[] => {
  switch (type) {
    case 'QUOTE':
    case 'INVOICE':
    case 'CREDIT_NOTE':
      return SALES_DOCUMENT_STATUSES;
    case 'PURCHASE_ORDER':
      return PURCHASE_ORDER_STATUSES;
    case 'PURCHASE_INVOICE':
      return PURCHASE_INVOICE_STATUSES;
    default:
      return SALES_DOCUMENT_STATUSES;
  }
};

// ============================================================
// TAUX DE TVA
// ============================================================

export const TVA_RATES = [
  { value: 0, labelKey: 'tax.rate0' },
  { value: 5.5, labelKey: 'tax.rate5_5' },
  { value: 10, labelKey: 'tax.rate10' },
  { value: 20, labelKey: 'tax.rate20' },
] as const;

export const DEFAULT_TVA_RATE = 20;

// ============================================================
// CONDITIONS DE PAIEMENT
// ============================================================

export const PAYMENT_TERMS = [
  { value: 'IMMEDIATE', labelKey: 'partners.paymentTerms.immediate' },
  { value: 'NET15', labelKey: 'partners.paymentTerms.net15' },
  { value: 'NET30', labelKey: 'partners.paymentTerms.net30' },
  { value: 'NET45', labelKey: 'partners.paymentTerms.net45' },
  { value: 'NET60', labelKey: 'partners.paymentTerms.net60' },
  { value: 'EOM', labelKey: 'partners.paymentTerms.eom' },
  { value: 'EOM30', labelKey: 'partners.paymentTerms.eom30' },
] as const;

export const DEFAULT_PAYMENT_TERMS = 'NET30';

// ============================================================
// PARAMÈTRES DE CACHE REACT QUERY
// ============================================================

export const QUERY_CONFIG: {
  staleTime: number;
  cacheTime: number;
  partnerLookupLimit: number;
  defaultPageSize: number;
} = {
  // Temps avant que les données soient considérées périmées (5 minutes)
  staleTime: 5 * 60 * 1000,
  // Temps de cache (10 minutes)
  cacheTime: 10 * 60 * 1000,
  // Nombre max de partenaires à charger pour les sélecteurs
  partnerLookupLimit: 50,
  // Taille de page par défaut
  defaultPageSize: 25,
};

// ============================================================
// HELPERS
// ============================================================

/**
 * Formate un montant en devise
 */
export const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
  }).format(amount);
};

/**
 * Formate une date en format français
 */
export const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

/**
 * Calcule les totaux d'une ligne
 */
export const calculateLineTotal = (
  quantity: number,
  unitPrice: number,
  discountPercent: number,
  taxRate: number
): { subtotal: number; taxAmount: number; total: number } => {
  const baseAmount = quantity * unitPrice;
  const discountAmount = baseAmount * (discountPercent / 100);
  const subtotal = baseAmount - discountAmount;
  const taxAmount = subtotal * (taxRate / 100);
  const total = subtotal + taxAmount;

  return { subtotal, taxAmount, total };
};

/**
 * Détermine la catégorie d'un type de document
 */
export const getDocumentCategory = (type: DocumentType): DocumentCategory => {
  return DOCUMENT_TYPE_CONFIG[type].category;
};

/**
 * Vérifie si un document peut être modifié
 */
export const canEditDocument = (status: DocumentStatus): boolean => {
  return status === 'DRAFT';
};

/**
 * Vérifie si un document peut être validé
 */
export const canValidateDocument = (status: DocumentStatus): boolean => {
  return status === 'DRAFT';
};

/**
 * Vérifie si un document peut être converti
 */
export const canConvertDocument = (type: DocumentType, status: DocumentStatus): boolean => {
  const config = DOCUMENT_TYPE_CONFIG[type];
  if (!config.canConvertTo) return false;

  // Seuls les documents validés peuvent être convertis
  if (type === 'QUOTE') return status === 'VALIDATED';
  if (type === 'PURCHASE_ORDER') return status === 'SENT' || status === 'CONFIRMED';

  return false;
};
