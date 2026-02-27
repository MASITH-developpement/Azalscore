/**
 * AZALSCORE Module - Subscriptions Types
 * Types, constantes et utilitaires pour la gestion des abonnements
 * Aligne avec l'API backend
 */

// ============================================================================
// TYPES (alignes avec l'API)
// ============================================================================

export type PlanInterval = 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
export type SubscriptionInterval = PlanInterval; // Alias pour compatibilite

export type SubscriptionStatus =
  | 'TRIALING'
  | 'ACTIVE'
  | 'PAST_DUE'
  | 'PAUSED'
  | 'CANCELED'
  | 'UNPAID'
  | 'INCOMPLETE'
  | 'INCOMPLETE_EXPIRED'
  | 'TRIAL'       // Alias pour compatibilite UI
  | 'CANCELLED'   // Alias pour compatibilite UI
  | 'EXPIRED';    // Alias pour compatibilite UI

export type InvoiceStatus = 'DRAFT' | 'OPEN' | 'PAID' | 'VOID' | 'UNCOLLECTIBLE';

// Helper pour convertir string en number
const toNum = (val: string | number | null | undefined): number => {
  if (val === null || val === undefined) return 0;
  if (typeof val === 'number') return val;
  const parsed = parseFloat(val);
  return isNaN(parsed) ? 0 : parsed;
};

export interface Plan {
  id: string | number;
  code: string;
  name: string;
  description?: string | null;
  // API renvoie base_price comme string, on accepte les deux
  base_price?: string;
  price?: number;  // Pour compatibilite UI (converti depuis base_price)
  currency: string;
  interval: PlanInterval;
  interval_count?: number;
  features?: string[] | Record<string, unknown> | null;
  trial_days: number;
  is_active: boolean;
  is_public?: boolean;
  subscribers_count?: number;  // Optionnel (pas dans l'API)
  per_user_price?: string;
  included_users?: number;
  setup_fee?: string;
  sort_order?: number;
  created_at: string;
  updated_at?: string;
}

export interface Subscription {
  id: string | number;
  subscription_number?: string;
  plan_id: string | number;
  plan_name?: string;  // Optionnel - peut etre joint depuis Plan
  plan_code?: string;
  customer_id: string | number;
  customer_name?: string | null;
  customer_email?: string | null;
  status: SubscriptionStatus;
  quantity?: number;
  current_users?: number;
  // Dates - API utilise started_at, UI peut utiliser start_date
  started_at?: string;
  start_date?: string;  // Alias pour started_at
  ended_at?: string | null;
  trial_start?: string | null;
  trial_end?: string | null;
  current_period_start?: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  canceled_at?: string | null;
  cancelled_at?: string | null;  // Alias
  paused_at?: string | null;
  resume_at?: string | null;
  // Montants - API renvoie mrr/arr comme string
  mrr?: string;
  arr?: string;
  amount?: number;  // Pour compatibilite UI
  currency?: string;
  discount_percent?: string;
  discount_end_date?: string | null;
  items?: SubscriptionItem[];
  created_at: string;
  updated_at?: string;
  // Champs additionnels pour detail
  metadata?: Record<string, unknown>;
  invoices?: SubscriptionInvoice[];
  payment_method_id?: string;
  payment_method_last_four?: string;
  history?: SubscriptionHistoryEntry[];
  total_paid?: number;
  lifetime_value?: number;
}

export interface SubscriptionItem {
  id: number;
  add_on_code?: string | null;
  name: string;
  description?: string | null;
  unit_price: string;
  quantity: number;
  usage_type?: string;
  metered_usage?: string;
  is_active: boolean;
}

export interface SubscriptionInvoice {
  id: string | number;
  subscription_id: string | number;
  invoice_number?: string;
  number?: string;  // Alias pour invoice_number
  customer_id?: string | number;
  customer_name?: string | null;
  customer_email?: string | null;
  status: InvoiceStatus;
  period_start: string;
  period_end: string;
  due_date?: string | null;
  paid_at?: string | null;
  finalized_at?: string | null;
  // Montants
  subtotal?: string;
  discount_amount?: string;
  tax_rate?: string;
  tax_amount?: string;
  total?: string;
  amount?: number;  // Pour compatibilite UI (converti depuis total)
  amount_paid?: string;
  amount_remaining?: string;
  currency: string;
  lines?: InvoiceLine[];
  created_at: string;
}

export interface InvoiceLine {
  id: number;
  description: string;
  item_type?: string | null;
  period_start?: string | null;
  period_end?: string | null;
  quantity: string;
  unit_price: string;
  discount_amount?: string;
  amount: string;
  tax_rate?: string;
  tax_amount?: string;
  proration?: boolean;
}

export interface SubscriptionStats {
  total_plans: number;
  active_subscriptions: number;
  trial_subscriptions: number;
  mrr: number | string;
  arr: number | string;
  churn_rate: number | string;
  new_subscribers_month: number;
  revenue_this_month: number | string;
}

export interface SubscriptionHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

// ============================================================================
// CONSTANTES & CONFIGURATIONS
// ============================================================================

export const INTERVALS: Array<{ value: PlanInterval; label: string; months: number }> = [
  { value: 'DAILY', label: 'Quotidien', months: 0 },
  { value: 'WEEKLY', label: 'Hebdomadaire', months: 0 },
  { value: 'MONTHLY', label: 'Mensuel', months: 1 },
  { value: 'QUARTERLY', label: 'Trimestriel', months: 3 },
  { value: 'YEARLY', label: 'Annuel', months: 12 }
];

export const SUBSCRIPTION_STATUS: Array<{ value: SubscriptionStatus; label: string }> = [
  { value: 'ACTIVE', label: 'Actif' },
  { value: 'TRIALING', label: 'Essai' },
  { value: 'PAST_DUE', label: 'En retard' },
  { value: 'PAUSED', label: 'En pause' },
  { value: 'CANCELED', label: 'Annule' },
  { value: 'UNPAID', label: 'Impaye' }
];

export const INVOICE_STATUS: Array<{ value: InvoiceStatus; label: string }> = [
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'OPEN', label: 'Ouverte' },
  { value: 'PAID', label: 'Payee' },
  { value: 'VOID', label: 'Annulee' },
  { value: 'UNCOLLECTIBLE', label: 'Irrecouvrable' }
];

export const SUBSCRIPTION_STATUS_CONFIG: Record<string, {
  label: string;
  color: 'green' | 'orange' | 'red' | 'blue' | 'gray' | 'purple';
  description: string;
}> = {
  ACTIVE: {
    label: 'Actif',
    color: 'green',
    description: 'L\'abonnement est actif et en cours'
  },
  TRIALING: {
    label: 'Essai',
    color: 'blue',
    description: 'L\'abonnement est en periode d\'essai'
  },
  TRIAL: {
    label: 'Essai',
    color: 'blue',
    description: 'L\'abonnement est en periode d\'essai'
  },
  PAST_DUE: {
    label: 'En retard',
    color: 'orange',
    description: 'Le paiement est en retard'
  },
  PAUSED: {
    label: 'En pause',
    color: 'gray',
    description: 'L\'abonnement est en pause'
  },
  CANCELED: {
    label: 'Annule',
    color: 'red',
    description: 'L\'abonnement a ete annule'
  },
  CANCELLED: {
    label: 'Annule',
    color: 'red',
    description: 'L\'abonnement a ete annule'
  },
  UNPAID: {
    label: 'Impaye',
    color: 'red',
    description: 'L\'abonnement est impaye'
  },
  INCOMPLETE: {
    label: 'Incomplet',
    color: 'orange',
    description: 'La souscription est incomplete'
  },
  INCOMPLETE_EXPIRED: {
    label: 'Expire (incomplet)',
    color: 'gray',
    description: 'La souscription incomplete a expire'
  },
  EXPIRED: {
    label: 'Expire',
    color: 'gray',
    description: 'L\'abonnement a expire'
  }
};

export const INVOICE_STATUS_CONFIG: Record<InvoiceStatus, {
  label: string;
  color: 'green' | 'orange' | 'red' | 'blue' | 'gray';
  description: string;
}> = {
  DRAFT: {
    label: 'Brouillon',
    color: 'gray',
    description: 'Facture en preparation'
  },
  OPEN: {
    label: 'Ouverte',
    color: 'blue',
    description: 'Facture emise, en attente de paiement'
  },
  PAID: {
    label: 'Payee',
    color: 'green',
    description: 'Facture reglee'
  },
  VOID: {
    label: 'Annulee',
    color: 'red',
    description: 'Facture annulee'
  },
  UNCOLLECTIBLE: {
    label: 'Irrecouvrable',
    color: 'red',
    description: 'Facture irrecouvrable'
  }
};

export const INTERVAL_CONFIG: Record<PlanInterval, {
  label: string;
  shortLabel: string;
  months: number;
}> = {
  DAILY: { label: 'Quotidien', shortLabel: '/jour', months: 0 },
  WEEKLY: { label: 'Hebdomadaire', shortLabel: '/sem.', months: 0 },
  MONTHLY: { label: 'Mensuel', shortLabel: '/mois', months: 1 },
  QUARTERLY: { label: 'Trimestriel', shortLabel: '/trim.', months: 3 },
  YEARLY: { label: 'Annuel', shortLabel: '/an', months: 12 }
};

// ============================================================================
// HELPERS
// ============================================================================

// Obtenir start_date avec fallback sur started_at
const getStartDate = (subscription: Subscription): string => {
  return subscription.start_date || subscription.started_at || subscription.created_at;
};

// Obtenir amount avec fallback sur mrr
const getAmount = (subscription: Subscription): number => {
  if (subscription.amount !== undefined) return subscription.amount;
  return toNum(subscription.mrr);
};

// Obtenir currency avec fallback
const getCurrency = (subscription: Subscription): string => {
  return subscription.currency || 'EUR';
};

export const getSubscriptionAge = (subscription: Subscription): string => {
  const start = new Date(getStartDate(subscription));
  const now = new Date();
  const diffMs = now.getTime() - start.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffMonths / 12);

  if (diffYears > 0) return `${diffYears} an${diffYears > 1 ? 's' : ''}`;
  if (diffMonths > 0) return `${diffMonths} mois`;
  return `${diffDays} jour${diffDays > 1 ? 's' : ''}`;
};

export const getSubscriptionAgeDays = (subscription: Subscription): number => {
  const start = new Date(getStartDate(subscription));
  const now = new Date();
  return Math.floor((now.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
};

export const getDaysUntilRenewal = (subscription: Subscription): number => {
  const end = new Date(subscription.current_period_end);
  const now = new Date();
  return Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
};

export const isInTrial = (subscription: Subscription): boolean => {
  return subscription.status === 'TRIAL' || subscription.status === 'TRIALING';
};

export const isActive = (subscription: Subscription): boolean => {
  return subscription.status === 'ACTIVE' || subscription.status === 'TRIALING' || subscription.status === 'TRIAL';
};

export const isPastDue = (subscription: Subscription): boolean => {
  return subscription.status === 'PAST_DUE';
};

export const isCancelled = (subscription: Subscription): boolean => {
  return subscription.status === 'CANCELLED' || subscription.status === 'CANCELED' || subscription.status === 'EXPIRED';
};

export const willCancel = (subscription: Subscription): boolean => {
  return subscription.cancel_at_period_end && !isCancelled(subscription);
};

export const getTrialDaysRemaining = (subscription: Subscription): number | null => {
  if (!subscription.trial_end) return null;
  const end = new Date(subscription.trial_end);
  const now = new Date();
  const days = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
  return days > 0 ? days : 0;
};

export const getMonthlyEquivalent = (amount: number | string, interval: PlanInterval): number => {
  const config = INTERVAL_CONFIG[interval];
  if (!config || config.months === 0) return toNum(amount);
  return toNum(amount) / config.months;
};

export const getYearlyEquivalent = (amount: number | string, interval: PlanInterval): number => {
  const config = INTERVAL_CONFIG[interval];
  if (!config || config.months === 0) return toNum(amount) * 12;
  return (toNum(amount) / config.months) * 12;
};

export const getIntervalLabel = (interval: PlanInterval): string => {
  return INTERVAL_CONFIG[interval]?.label || interval;
};

export const getStatusLabel = (status: SubscriptionStatus): string => {
  return SUBSCRIPTION_STATUS_CONFIG[status]?.label || status;
};

export const getStatusColor = (status: SubscriptionStatus): string => {
  return SUBSCRIPTION_STATUS_CONFIG[status]?.color || 'gray';
};

export const getPaidInvoicesCount = (subscription: Subscription): number => {
  if (!subscription.invoices) return 0;
  return subscription.invoices.filter(inv => inv.status === 'PAID').length;
};

export const getTotalPaid = (subscription: Subscription): number => {
  if (subscription.total_paid !== undefined) return subscription.total_paid;
  if (!subscription.invoices) return 0;
  return subscription.invoices
    .filter(inv => inv.status === 'PAID')
    .reduce((sum, inv) => sum + toNum(inv.total || inv.amount), 0);
};

// Obtenir le prix du plan
export const getPlanPrice = (plan: Plan): number => {
  if (plan.price !== undefined) return plan.price;
  return toNum(plan.base_price);
};

// Obtenir le numero de facture
export const getInvoiceNumber = (invoice: SubscriptionInvoice): string => {
  return invoice.number || invoice.invoice_number || String(invoice.id);
};

// Obtenir le montant de la facture
export const getInvoiceAmount = (invoice: SubscriptionInvoice): number => {
  if (invoice.amount !== undefined) return invoice.amount;
  return toNum(invoice.total);
};
