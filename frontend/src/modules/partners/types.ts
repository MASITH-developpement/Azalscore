/**
 * AZALSCORE Module - Partners Types
 * Types, constantes et utilitaires pour la gestion des partenaires
 */

// ============================================================================
// TYPES
// ============================================================================

export type PartnerType = 'client' | 'supplier' | 'contact';
export type ClientType = 'PROSPECT' | 'LEAD' | 'CUSTOMER' | 'VIP' | 'PARTNER' | 'CHURNED';

export interface Partner {
  id: string;
  type: PartnerType;
  code?: string;
  name: string;
  email?: string;
  phone?: string;
  mobile?: string;
  address?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  country_code?: string;
  vat_number?: string;
  tax_id?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  // Champs additionnels pour detail
  notes?: string;
  website?: string;
  industry?: string;
  company_size?: string;
  source?: string;
  assigned_to?: string;
  assigned_to_name?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  history?: PartnerHistoryEntry[];
  contacts?: Contact[];
  documents?: PartnerDocument[];
  stats?: PartnerStats;
}

export interface Client extends Partner {
  type: 'client';
  client_type: ClientType;
  payment_terms?: number;
  credit_limit?: number;
  currency?: string;
  discount_rate?: number;
  loyalty_points?: number;
  total_orders?: number;
  total_revenue?: number;
  last_order_date?: string;
  first_order_date?: string;
}

export interface Supplier extends Partner {
  type: 'supplier';
  supplier_code?: string;
  payment_terms?: number;
  lead_time_days?: number;
  min_order_amount?: number;
  total_purchases?: number;
  last_purchase_date?: string;
  rating?: number;
  certifications?: string[];
}

export interface Contact {
  id: string;
  customer_id?: string;
  supplier_id?: string;
  partner_name?: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  mobile?: string;
  job_title?: string;
  department?: string;
  is_primary?: boolean;
  is_active: boolean;
  created_at: string;
  notes?: string;
}

export interface PartnerHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

export interface PartnerDocument {
  id: string;
  name: string;
  type: string;
  size?: number;
  url?: string;
  uploaded_at: string;
  uploaded_by?: string;
}

export interface PartnerStats {
  total_orders?: number;
  total_revenue?: number;
  average_order_value?: number;
  last_activity_date?: string;
  open_invoices?: number;
  overdue_invoices?: number;
  total_paid?: number;
  total_outstanding?: number;
}

// ============================================================================
// CONSTANTES & CONFIGURATIONS
// ============================================================================

export const PARTNER_TYPES: Array<{ value: PartnerType; label: string; icon: string }> = [
  { value: 'client', label: 'Client', icon: '👤' },
  { value: 'supplier', label: 'Fournisseur', icon: '🏢' },
  { value: 'contact', label: 'Contact', icon: '📇' }
];

export const CLIENT_TYPES: Array<{ value: ClientType; label: string }> = [
  { value: 'PROSPECT', label: 'Prospect' },
  { value: 'LEAD', label: 'Lead' },
  { value: 'CUSTOMER', label: 'Client' },
  { value: 'VIP', label: 'VIP' },
  { value: 'PARTNER', label: 'Partenaire' },
  { value: 'CHURNED', label: 'Perdu' }
];

export const PARTNER_TYPE_CONFIG: Record<PartnerType, {
  label: string;
  color: 'green' | 'blue' | 'purple' | 'gray';
}> = {
  client: { label: 'Client', color: 'green' },
  supplier: { label: 'Fournisseur', color: 'blue' },
  contact: { label: 'Contact', color: 'purple' }
};

export const CLIENT_TYPE_CONFIG: Record<ClientType, {
  label: string;
  color: 'green' | 'orange' | 'red' | 'blue' | 'gray' | 'purple';
  description: string;
}> = {
  PROSPECT: {
    label: 'Prospect',
    color: 'blue',
    description: 'Contact interesse non qualifie'
  },
  LEAD: {
    label: 'Lead',
    color: 'orange',
    description: 'Prospect qualifie en cours de conversion'
  },
  CUSTOMER: {
    label: 'Client',
    color: 'green',
    description: 'Client actif'
  },
  VIP: {
    label: 'VIP',
    color: 'purple',
    description: 'Client prioritaire a forte valeur'
  },
  PARTNER: {
    label: 'Partenaire',
    color: 'blue',
    description: 'Partenaire commercial'
  },
  CHURNED: {
    label: 'Perdu',
    color: 'gray',
    description: 'Client inactif ou perdu'
  }
};

export const STATUS_CONFIG = {
  active: { label: 'Actif', color: 'green' },
  inactive: { label: 'Inactif', color: 'gray' }
};

// ============================================================================
// HELPERS
// ============================================================================

export const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

export const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

export const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);
};

export const getPartnerAge = (partner: Partner): string => {
  const created = new Date(partner.created_at);
  const now = new Date();
  const diffMs = now.getTime() - created.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffMonths / 12);

  if (diffYears > 0) return `${diffYears} an${diffYears > 1 ? 's' : ''}`;
  if (diffMonths > 0) return `${diffMonths} mois`;
  return `${diffDays} jour${diffDays > 1 ? 's' : ''}`;
};

export const getPartnerAgeDays = (partner: Partner): number => {
  const created = new Date(partner.created_at);
  const now = new Date();
  return Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24));
};

export const getFullName = (contact: Contact): string => {
  return `${contact.first_name || ''} ${contact.last_name || ''}`.trim() || 'Sans nom';
};

export const getFullAddress = (partner: Partner): string => {
  const parts = [
    partner.address_line1 || partner.address,
    partner.address_line2,
    [partner.postal_code, partner.city].filter(Boolean).join(' '),
    partner.country || partner.country_code
  ].filter(Boolean);
  return parts.join(', ');
};

export const isActivePartner = (partner: Partner): boolean => {
  return partner.is_active;
};

export const hasContacts = (partner: Partner): boolean => {
  return (partner.contacts?.length || 0) > 0;
};

export const hasDocuments = (partner: Partner): boolean => {
  return (partner.documents?.length || 0) > 0;
};

export const getClientTypeLabel = (type: ClientType): string => {
  return CLIENT_TYPE_CONFIG[type]?.label || type;
};

export const getClientTypeColor = (type: ClientType): string => {
  return CLIENT_TYPE_CONFIG[type]?.color || 'gray';
};

export const getPrimaryContact = (partner: Partner): Contact | undefined => {
  return partner.contacts?.find(c => c.is_primary) || partner.contacts?.[0];
};

export const getContactsCount = (partner: Partner): number => {
  return partner.contacts?.length || 0;
};

export const getDocumentsCount = (partner: Partner): number => {
  return partner.documents?.length || 0;
};
