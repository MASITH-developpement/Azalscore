/**
 * AZALSCORE - Module Documents Unifié
 * Types et interfaces partagés
 */

// ============================================================
// TYPES DE DOCUMENTS
// ============================================================

/**
 * Types de documents commerciaux
 */
export type DocumentType =
  | 'QUOTE'            // Devis client
  | 'INVOICE'          // Facture client
  | 'CREDIT_NOTE'      // Avoir client
  | 'PURCHASE_ORDER'   // Commande fournisseur
  | 'PURCHASE_INVOICE'; // Facture fournisseur

/**
 * Catégorie de document (ventes ou achats)
 */
export type DocumentCategory = 'SALES' | 'PURCHASES';

/**
 * Statuts des documents de vente
 */
export type SalesDocumentStatus = 'DRAFT' | 'VALIDATED' | 'SENT' | 'PAID' | 'CANCELLED';

/**
 * Statuts des commandes fournisseur
 */
export type PurchaseOrderStatus =
  | 'DRAFT'
  | 'SENT'
  | 'CONFIRMED'
  | 'PARTIAL'
  | 'RECEIVED'
  | 'INVOICED'
  | 'CANCELLED';

/**
 * Statuts des factures fournisseur
 */
export type PurchaseInvoiceStatus =
  | 'DRAFT'
  | 'VALIDATED'
  | 'PAID'
  | 'PARTIAL'
  | 'CANCELLED';

/**
 * Statut générique de document
 */
export type DocumentStatus = SalesDocumentStatus | PurchaseOrderStatus | PurchaseInvoiceStatus;

// ============================================================
// INTERFACES - LIGNES DE DOCUMENT
// ============================================================

/**
 * Ligne de document (commune à tous les types)
 */
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

/**
 * Données de formulaire pour une ligne
 */
export interface LineFormData {
  id?: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount_percent: number;
  tax_rate: number;
}

// ============================================================
// INTERFACES - DOCUMENTS
// ============================================================

/**
 * Document de base (commun à tous les types)
 */
export interface BaseDocument {
  id: string;
  number: string;
  type: DocumentType;
  status: DocumentStatus;
  date: string;
  subtotal: number;
  discount_percent: number;
  discount_amount: number;
  tax_amount: number;
  total: number;
  currency: string;
  notes?: string;
  internal_notes?: string;
  validated_by?: string;
  validated_at?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  lines: DocumentLine[];
}

/**
 * Document de vente (devis, facture, avoir)
 */
export interface SalesDocument extends BaseDocument {
  type: 'QUOTE' | 'INVOICE' | 'CREDIT_NOTE';
  status: SalesDocumentStatus;
  customer_id: string;
  customer_name?: string;
  customer_code?: string;
  due_date?: string;
  validity_date?: string;
  parent_id?: string; // Pour les conversions (devis → facture)
}

/**
 * Commande fournisseur
 */
export interface PurchaseOrder extends BaseDocument {
  type: 'PURCHASE_ORDER';
  status: PurchaseOrderStatus;
  supplier_id: string;
  supplier_name?: string;
  supplier_code?: string;
  expected_date?: string;
  reference?: string;
}

/**
 * Facture fournisseur
 */
export interface PurchaseInvoice extends BaseDocument {
  type: 'PURCHASE_INVOICE';
  status: PurchaseInvoiceStatus;
  supplier_id: string;
  supplier_name?: string;
  supplier_code?: string;
  due_date?: string;
  supplier_reference?: string;
  order_id?: string;
  order_number?: string;
}

/**
 * Union de tous les types de documents
 */
export type UnifiedDocument = SalesDocument | PurchaseOrder | PurchaseInvoice;

// ============================================================
// INTERFACES - PARTENAIRES
// ============================================================

/**
 * Type de partenaire
 */
export type PartnerType = 'CUSTOMER' | 'SUPPLIER';

/**
 * Statut de partenaire
 */
export type PartnerStatus = 'PROSPECT' | 'PENDING' | 'APPROVED' | 'ACTIVE' | 'BLOCKED' | 'INACTIVE';

/**
 * Partenaire (client ou fournisseur)
 */
export interface Partner {
  id: string;
  code: string;
  name: string;
  type: PartnerType;
  status: PartnerStatus;
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
  created_at: string;
  updated_at: string;
}

/**
 * Client (alias pour clarté)
 */
export interface Customer extends Omit<Partner, 'type'> {
  type: 'CUSTOMER';
}

/**
 * Fournisseur (alias pour clarté)
 */
export interface Supplier extends Omit<Partner, 'type'> {
  type: 'SUPPLIER';
}

/**
 * Données de création de partenaire
 */
export interface PartnerCreateData {
  name: string;
  type: PartnerType;
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

// ============================================================
// INTERFACES - FILTRES
// ============================================================

/**
 * Filtres pour la liste de documents
 */
export interface DocumentFilters {
  search?: string;
  status?: DocumentStatus;
  partner_id?: string;
  date_from?: string;
  date_to?: string;
}

/**
 * Filtres pour la liste de partenaires
 */
export interface PartnerFilters {
  search?: string;
  status?: PartnerStatus;
  type?: PartnerType;
}

// ============================================================
// INTERFACES - FORMULAIRES
// ============================================================

/**
 * Données de création de document de vente
 */
export interface SalesDocumentCreateData {
  type: 'QUOTE' | 'INVOICE' | 'CREDIT_NOTE';
  customer_id: string;
  date: string;
  due_date?: string;
  validity_date?: string;
  notes?: string;
  lines: Omit<LineFormData, 'id'>[];
}

/**
 * Données de création de commande fournisseur
 */
export interface PurchaseOrderCreateData {
  supplier_id: string;
  date: string;
  expected_date?: string;
  reference?: string;
  notes?: string;
  lines: Omit<LineFormData, 'id'>[];
}

/**
 * Données de création de facture fournisseur
 */
export interface PurchaseInvoiceCreateData {
  supplier_id: string;
  order_id?: string;
  date: string;
  due_date?: string;
  supplier_reference?: string;
  notes?: string;
  lines: Omit<LineFormData, 'id'>[];
}

/**
 * Union des données de création
 */
export type DocumentCreateData =
  | SalesDocumentCreateData
  | PurchaseOrderCreateData
  | PurchaseInvoiceCreateData;

// ============================================================
// INTERFACES - API
// ============================================================

/**
 * Réponse paginée générique
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/**
 * Résumé pour le dashboard
 */
export interface DocumentsSummary {
  // Ventes
  draft_quotes: number;
  draft_invoices: number;
  pending_amount: number;
  // Achats
  pending_orders: number;
  pending_orders_value: number;
  draft_purchase_invoices: number;
  // Partenaires
  active_customers: number;
  active_suppliers: number;
}
