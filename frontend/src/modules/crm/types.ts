/**
 * AZALSCORE Module - CRM - Types et Helpers
 * Types partagés pour la gestion de la relation client
 */

// ============================================================================
// TYPES - Entités principales
// ============================================================================

export type CustomerType = 'PROSPECT' | 'LEAD' | 'CUSTOMER' | 'VIP' | 'PARTNER' | 'CHURNED';
export type OpportunityStatus = 'NEW' | 'QUALIFIED' | 'PROPOSAL' | 'NEGOTIATION' | 'WON' | 'LOST';
export type ActivityType = 'CALL' | 'EMAIL' | 'MEETING' | 'TASK' | 'NOTE';
export type ActivityStatus = 'PLANNED' | 'DONE' | 'CANCELLED';

export interface Customer {
  id: string;
  code: string;
  name: string;
  legal_name?: string;
  type: CustomerType;
  email?: string;
  phone?: string;
  mobile?: string;
  fax?: string;
  website?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  country_code?: string;
  tax_id?: string;
  registration_number?: string;
  assigned_to?: string;
  assigned_to_name?: string;
  industry?: string;
  source?: string;
  lead_score?: number;
  total_revenue?: number;
  order_count?: number;
  quote_count?: number;
  invoice_count?: number;
  last_order_date?: string;
  last_contact_date?: string;
  notes?: string;
  tags?: string[];
  custom_fields?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
  // Relations
  contacts?: Contact[];
  opportunities?: Opportunity[];
  activities?: Activity[];
  documents?: CustomerDocument[];
  history?: CustomerHistoryEntry[];
}

export interface Contact {
  id: string;
  customer_id: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  job_title?: string;
  department?: string;
  email?: string;
  phone?: string;
  mobile?: string;
  is_primary: boolean;
  is_active: boolean;
  notes?: string;
  created_at: string;
}

export interface Opportunity {
  id: string;
  code: string;
  name: string;
  description?: string;
  customer_id: string;
  customer_name?: string;
  contact_id?: string;
  contact_name?: string;
  status: OpportunityStatus;
  probability: number;
  amount: number;
  currency: string;
  expected_close_date?: string;
  actual_close_date?: string;
  assigned_to?: string;
  assigned_to_name?: string;
  source?: string;
  win_reason?: string;
  loss_reason?: string;
  competitor?: string;
  notes?: string;
  quote_id?: string;
  quote_number?: string;
  created_at: string;
  updated_at?: string;
}

export interface Activity {
  id: string;
  customer_id: string;
  contact_id?: string;
  opportunity_id?: string;
  type: ActivityType;
  status: ActivityStatus;
  subject: string;
  description?: string;
  due_date?: string;
  completed_date?: string;
  assigned_to?: string;
  assigned_to_name?: string;
  created_at: string;
  created_by?: string;
}

// ============================================================================
// TYPES - Dashboard et Stats
// ============================================================================

export interface PipelineStats {
  total_opportunities: number;
  total_value: number;
  weighted_value: number;
  won_count: number;
  won_value: number;
  lost_count: number;
  lost_value: number;
  conversion_rate: number;
  avg_deal_size: number;
  avg_sales_cycle_days: number;
  by_stage: PipelineStage[];
}

export interface PipelineStage {
  stage: OpportunityStatus;
  label: string;
  count: number;
  value: number;
  weighted_value: number;
}

export interface SalesDashboard {
  revenue_mtd: number;
  revenue_ytd: number;
  revenue_growth: number;
  orders_mtd: number;
  orders_ytd: number;
  new_customers_mtd: number;
  new_customers_ytd: number;
  pipeline_value: number;
  weighted_pipeline: number;
  pending_quotes: number;
  pending_quotes_value: number;
  pending_invoices: number;
  overdue_invoices: number;
  overdue_invoices_value: number;
}

export interface CustomerStats {
  total_revenue: number;
  total_orders: number;
  total_quotes: number;
  total_invoices: number;
  avg_order_value: number;
  open_opportunities: number;
  open_opportunities_value: number;
  won_opportunities: number;
  won_opportunities_value: number;
  activities_count: number;
  last_activity_date?: string;
}

// ============================================================================
// TYPES - Historique et Documents
// ============================================================================

export interface CustomerHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
  field?: string;
}

export interface CustomerDocument {
  id: string;
  name: string;
  type: 'pdf' | 'image' | 'contract' | 'other';
  category?: string;
  url?: string;
  size?: number;
  created_at: string;
  created_by?: string;
}

// ============================================================================
// CONSTANTES - Configurations
// ============================================================================

export const CUSTOMER_TYPE_CONFIG: Record<CustomerType, { label: string; color: string; description: string }> = {
  PROSPECT: { label: 'Prospect', color: 'gray', description: 'Contact non qualifié' },
  LEAD: { label: 'Lead', color: 'blue', description: 'Contact qualifié, opportunité identifiée' },
  CUSTOMER: { label: 'Client', color: 'green', description: 'Client actif' },
  VIP: { label: 'VIP', color: 'yellow', description: 'Client stratégique' },
  PARTNER: { label: 'Partenaire', color: 'purple', description: 'Partenaire commercial' },
  CHURNED: { label: 'Perdu', color: 'red', description: 'Client perdu' },
};

export const OPPORTUNITY_STATUS_CONFIG: Record<OpportunityStatus, { label: string; color: string; probability: number; order: number }> = {
  NEW: { label: 'Nouveau', color: 'blue', probability: 10, order: 1 },
  QUALIFIED: { label: 'Qualifié', color: 'cyan', probability: 30, order: 2 },
  PROPOSAL: { label: 'Proposition', color: 'orange', probability: 50, order: 3 },
  NEGOTIATION: { label: 'Négociation', color: 'purple', probability: 70, order: 4 },
  WON: { label: 'Gagné', color: 'green', probability: 100, order: 5 },
  LOST: { label: 'Perdu', color: 'red', probability: 0, order: 6 },
};

export const ACTIVITY_TYPE_CONFIG: Record<ActivityType, { label: string; color: string; icon: string }> = {
  CALL: { label: 'Appel', color: 'blue', icon: 'phone' },
  EMAIL: { label: 'Email', color: 'cyan', icon: 'mail' },
  MEETING: { label: 'Réunion', color: 'purple', icon: 'calendar' },
  TASK: { label: 'Tâche', color: 'orange', icon: 'check-square' },
  NOTE: { label: 'Note', color: 'gray', icon: 'file-text' },
};

export const ACTIVITY_STATUS_CONFIG: Record<ActivityStatus, { label: string; color: string }> = {
  PLANNED: { label: 'Planifié', color: 'blue' },
  DONE: { label: 'Terminé', color: 'green' },
  CANCELLED: { label: 'Annulé', color: 'gray' },
};

// ============================================================================
// HELPERS - Calculs et vérifications
// ============================================================================

export const isProspect = (customer: Customer): boolean => {
  return customer.type === 'PROSPECT' || customer.type === 'LEAD';
};

export const isActiveCustomer = (customer: Customer): boolean => {
  return customer.type === 'CUSTOMER' || customer.type === 'VIP' || customer.type === 'PARTNER';
};

export const isChurned = (customer: Customer): boolean => {
  return customer.type === 'CHURNED';
};

export const canConvert = (customer: Customer): boolean => {
  return isProspect(customer) && customer.is_active;
};

export const getCustomerValue = (customer: Customer): 'high' | 'medium' | 'low' => {
  const revenue = customer.total_revenue || 0;
  if (revenue >= 100000) return 'high';
  if (revenue >= 10000) return 'medium';
  return 'low';
};

export const getLeadScore = (customer: Customer): number => {
  return customer.lead_score || 0;
};

export const getLeadScoreLevel = (score: number): 'hot' | 'warm' | 'cold' => {
  if (score >= 80) return 'hot';
  if (score >= 50) return 'warm';
  return 'cold';
};

export const isOpportunityOpen = (opportunity: Opportunity): boolean => {
  return !['WON', 'LOST'].includes(opportunity.status);
};

export const isOpportunityWon = (opportunity: Opportunity): boolean => {
  return opportunity.status === 'WON';
};

export const isOpportunityLost = (opportunity: Opportunity): boolean => {
  return opportunity.status === 'LOST';
};

export const getWeightedValue = (opportunity: Opportunity): number => {
  return opportunity.amount * (opportunity.probability / 100);
};

export const getDaysToClose = (opportunity: Opportunity): number | null => {
  if (!opportunity.expected_close_date) return null;
  const now = new Date();
  const closeDate = new Date(opportunity.expected_close_date);
  const diffTime = closeDate.getTime() - now.getTime();
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};

export const isOverdue = (opportunity: Opportunity): boolean => {
  if (!isOpportunityOpen(opportunity)) return false;
  const days = getDaysToClose(opportunity);
  return days !== null && days < 0;
};

export const getContactFullName = (contact: Contact): string => {
  return contact.full_name || `${contact.first_name} ${contact.last_name}`.trim();
};

// ============================================================================
// HELPERS - Navigation
// ============================================================================

export const navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

export const navigateToDevis = (customerId: string) => {
  navigateTo('devis', { customerId, action: 'new' });
};

export const navigateToCommande = (customerId: string) => {
  navigateTo('commandes', { customerId, action: 'new' });
};
