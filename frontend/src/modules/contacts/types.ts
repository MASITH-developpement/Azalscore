/**
 * AZALS MODULE - Contacts Unifiés - Types TypeScript
 * ===================================================
 *
 * Types pour la gestion unifiée des contacts (Clients et Fournisseurs).
 */

// ============================================================================
// ENUMS
// ============================================================================

export enum EntityType {
  INDIVIDUAL = 'INDIVIDUAL',
  COMPANY = 'COMPANY',
}

export enum RelationType {
  CUSTOMER = 'CUSTOMER',
  SUPPLIER = 'SUPPLIER',
}

export enum AddressType {
  BILLING = 'BILLING',
  SHIPPING = 'SHIPPING',
  SITE = 'SITE',
  HEAD_OFFICE = 'HEAD_OFFICE',
  OTHER = 'OTHER',
}

export enum ContactPersonRole {
  MANAGER = 'MANAGER',
  COMMERCIAL = 'COMMERCIAL',
  ACCOUNTING = 'ACCOUNTING',
  BUYER = 'BUYER',
  TECHNICAL = 'TECHNICAL',
  ADMINISTRATIVE = 'ADMINISTRATIVE',
  LOGISTICS = 'LOGISTICS',
  OTHER = 'OTHER',
}

export enum CustomerType {
  PROSPECT = 'PROSPECT',
  LEAD = 'LEAD',
  CUSTOMER = 'CUSTOMER',
  VIP = 'VIP',
  PARTNER = 'PARTNER',
  CHURNED = 'CHURNED',
}

export enum SupplierStatus {
  PROSPECT = 'PROSPECT',
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  BLOCKED = 'BLOCKED',
  INACTIVE = 'INACTIVE',
}

export enum SupplierType {
  GOODS = 'GOODS',
  SERVICES = 'SERVICES',
  BOTH = 'BOTH',
  RAW_MATERIALS = 'RAW_MATERIALS',
  EQUIPMENT = 'EQUIPMENT',
}

// ============================================================================
// LABELS (pour l'affichage)
// ============================================================================

export const EntityTypeLabels: Record<EntityType, string> = {
  [EntityType.INDIVIDUAL]: 'Particulier',
  [EntityType.COMPANY]: 'Société',
};

export const RelationTypeLabels: Record<RelationType, string> = {
  [RelationType.CUSTOMER]: 'Client',
  [RelationType.SUPPLIER]: 'Fournisseur',
};

export const AddressTypeLabels: Record<AddressType, string> = {
  [AddressType.BILLING]: 'Facturation',
  [AddressType.SHIPPING]: 'Livraison',
  [AddressType.SITE]: 'Chantier',
  [AddressType.HEAD_OFFICE]: 'Siège social',
  [AddressType.OTHER]: 'Autre',
};

export const ContactPersonRoleLabels: Record<ContactPersonRole, string> = {
  [ContactPersonRole.MANAGER]: 'Dirigeant',
  [ContactPersonRole.COMMERCIAL]: 'Commercial',
  [ContactPersonRole.ACCOUNTING]: 'Comptabilité',
  [ContactPersonRole.BUYER]: 'Acheteur',
  [ContactPersonRole.TECHNICAL]: 'Technique',
  [ContactPersonRole.ADMINISTRATIVE]: 'Administratif',
  [ContactPersonRole.LOGISTICS]: 'Logistique',
  [ContactPersonRole.OTHER]: 'Autre',
};

export const CustomerTypeLabels: Record<CustomerType, string> = {
  [CustomerType.PROSPECT]: 'Prospect',
  [CustomerType.LEAD]: 'Lead',
  [CustomerType.CUSTOMER]: 'Client',
  [CustomerType.VIP]: 'VIP',
  [CustomerType.PARTNER]: 'Partenaire',
  [CustomerType.CHURNED]: 'Perdu',
};

export const SupplierStatusLabels: Record<SupplierStatus, string> = {
  [SupplierStatus.PROSPECT]: 'Prospect',
  [SupplierStatus.PENDING]: 'En attente',
  [SupplierStatus.APPROVED]: 'Approuvé',
  [SupplierStatus.BLOCKED]: 'Bloqué',
  [SupplierStatus.INACTIVE]: 'Inactif',
};

export const SupplierTypeLabels: Record<SupplierType, string> = {
  [SupplierType.GOODS]: 'Marchandises',
  [SupplierType.SERVICES]: 'Services',
  [SupplierType.BOTH]: 'Les deux',
  [SupplierType.RAW_MATERIALS]: 'Matières premières',
  [SupplierType.EQUIPMENT]: 'Équipements',
};

// ============================================================================
// INTERFACES - PERSONNE DE CONTACT
// ============================================================================

export interface ContactPerson {
  id: string;
  tenant_id: string;
  contact_id: string;
  role: ContactPersonRole;
  custom_role?: string;
  first_name: string;
  last_name: string;
  job_title?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  is_primary: boolean;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
  // Computed
  full_name: string;
  display_role: string;
}

export interface ContactPersonCreate {
  role?: ContactPersonRole;
  custom_role?: string;
  first_name: string;
  last_name: string;
  job_title?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  is_primary?: boolean;
  notes?: string;
}

export interface ContactPersonUpdate {
  role?: ContactPersonRole;
  custom_role?: string;
  first_name?: string;
  last_name?: string;
  job_title?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  is_primary?: boolean;
  is_active?: boolean;
  notes?: string;
}

// ============================================================================
// INTERFACES - ADRESSE
// ============================================================================

export interface ContactAddress {
  id: string;
  tenant_id: string;
  contact_id: string;
  address_type: AddressType;
  label?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  state?: string;
  country_code: string;
  latitude?: number;
  longitude?: number;
  contact_name?: string;
  contact_phone?: string;
  is_default: boolean;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
  // Computed
  full_address: string;
  display_label: string;
}

export interface ContactAddressCreate {
  address_type?: AddressType;
  label?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  state?: string;
  country_code?: string;
  latitude?: number;
  longitude?: number;
  contact_name?: string;
  contact_phone?: string;
  is_default?: boolean;
  notes?: string;
}

export interface ContactAddressUpdate {
  address_type?: AddressType;
  label?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  state?: string;
  country_code?: string;
  latitude?: number;
  longitude?: number;
  contact_name?: string;
  contact_phone?: string;
  is_default?: boolean;
  is_active?: boolean;
  notes?: string;
}

// ============================================================================
// INTERFACES - CONTACT PRINCIPAL
// ============================================================================

export interface Contact {
  id: string;
  tenant_id: string;
  code: string;
  entity_type: EntityType;
  relation_types: RelationType[];
  // Identification
  name: string;
  legal_name?: string;
  first_name?: string;
  last_name?: string;
  // Coordonnées
  email?: string;
  phone?: string;
  mobile?: string;
  website?: string;
  // Informations légales
  tax_id?: string;
  registration_number?: string;
  legal_form?: string;
  // Logo
  logo_url?: string;
  // Tags
  tags: string[];
  // Notes
  notes?: string;
  internal_notes?: string;
  // Client
  customer_type?: CustomerType;
  customer_payment_terms?: string;
  customer_payment_method?: string;
  customer_credit_limit?: number;
  customer_discount_rate?: number;
  customer_currency: string;
  assigned_to?: string;
  industry?: string;
  source?: string;
  segment?: string;
  lead_score: number;
  health_score: number;
  customer_total_revenue: number;
  customer_order_count: number;
  customer_last_order_date?: string;
  customer_first_order_date?: string;
  // Fournisseur
  supplier_status?: SupplierStatus;
  supplier_type?: SupplierType;
  supplier_payment_terms?: string;
  supplier_currency: string;
  supplier_credit_limit?: number;
  supplier_category?: string;
  supplier_total_purchases: number;
  supplier_order_count: number;
  supplier_last_order_date?: string;
  // Métadonnées
  is_active: boolean;
  deleted_at?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
  // Computed
  is_customer: boolean;
  is_supplier: boolean;
  display_name: string;
  // Relations
  persons: ContactPerson[];
  addresses: ContactAddress[];
}

export interface ContactCreate {
  code?: string;
  entity_type?: EntityType;
  relation_types: RelationType[];
  name: string;
  legal_name?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  website?: string;
  tax_id?: string;
  registration_number?: string;
  legal_form?: string;
  logo_url?: string;
  tags?: string[];
  notes?: string;
  internal_notes?: string;
  // Client
  customer_type?: CustomerType;
  customer_payment_terms?: string;
  customer_payment_method?: string;
  customer_credit_limit?: number;
  customer_discount_rate?: number;
  customer_currency?: string;
  assigned_to?: string;
  industry?: string;
  source?: string;
  segment?: string;
  // Fournisseur
  supplier_status?: SupplierStatus;
  supplier_type?: SupplierType;
  supplier_payment_terms?: string;
  supplier_currency?: string;
  supplier_credit_limit?: number;
  supplier_category?: string;
  // Relations inline
  persons?: ContactPersonCreate[];
  addresses?: ContactAddressCreate[];
}

export interface ContactUpdate {
  entity_type?: EntityType;
  relation_types?: RelationType[];
  name?: string;
  legal_name?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  website?: string;
  tax_id?: string;
  registration_number?: string;
  legal_form?: string;
  logo_url?: string;
  tags?: string[];
  notes?: string;
  internal_notes?: string;
  // Client
  customer_type?: CustomerType;
  customer_payment_terms?: string;
  customer_payment_method?: string;
  customer_credit_limit?: number;
  customer_discount_rate?: number;
  customer_currency?: string;
  assigned_to?: string;
  industry?: string;
  source?: string;
  segment?: string;
  // Fournisseur
  supplier_status?: SupplierStatus;
  supplier_type?: SupplierType;
  supplier_payment_terms?: string;
  supplier_currency?: string;
  supplier_credit_limit?: number;
  supplier_category?: string;
  // Statut
  is_active?: boolean;
}

// ============================================================================
// INTERFACES - LISTES ET LOOKUPS
// ============================================================================

export interface ContactSummary {
  id: string;
  code: string;
  name: string;
  entity_type: EntityType;
  relation_types: RelationType[];
  email?: string;
  phone?: string;
  logo_url?: string;
  is_customer: boolean;
  is_supplier: boolean;
  is_active: boolean;
}

export interface ContactList {
  items: ContactSummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ContactLookup {
  id: string;
  code: string;
  name: string;
  entity_type: EntityType;
  is_customer: boolean;
  is_supplier: boolean;
  logo_url?: string;
}

export interface ContactLookupList {
  items: ContactLookup[];
  total: number;
}

// ============================================================================
// INTERFACES - FILTRES ET REQUÊTES
// ============================================================================

export interface ContactFilters {
  entity_type?: EntityType;
  relation_type?: RelationType;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface ContactStats {
  contact_id: string;
  is_customer: boolean;
  is_supplier: boolean;
  customer_stats?: {
    total_revenue: number;
    order_count: number;
    last_order_date?: string;
    first_order_date?: string;
    health_score: number;
    lead_score: number;
  };
  supplier_stats?: {
    total_purchases: number;
    order_count: number;
    last_order_date?: string;
  };
}
