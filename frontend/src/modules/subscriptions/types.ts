/**
 * AZALSCORE Module - Subscriptions Types
 * Types, constantes et utilitaires pour la gestion des abonnements
 */

// ============================================================================
// TYPES
// ============================================================================

export type SubscriptionInterval = 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
export type SubscriptionStatus = 'ACTIVE' | 'TRIAL' | 'PAST_DUE' | 'CANCELLED' | 'EXPIRED';
export type InvoiceStatus = 'DRAFT' | 'OPEN' | 'PAID' | 'VOID' | 'UNCOLLECTIBLE';

export interface Plan {
  id: string;
  code: string;
  name: string;
  description?: string;
  price: number;
  currency: string;
  interval: SubscriptionInterval;
  features: string[];
  trial_days: number;
  is_active: boolean;
  subscribers_count: number;
  created_at: string;
  updated_at?: string;
}

export interface Subscription {
  id: string;
  plan_id: string;
  plan_name: string;
  plan_code?: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  status: SubscriptionStatus;
  start_date: string;
  current_period_start?: string;
  current_period_end: string;
  trial_start?: string;
  trial_end?: string;
  cancel_at_period_end: boolean;
  cancelled_at?: string;
  amount: number;
  currency: string;
  created_at: string;
  updated_at?: string;
  // Champs additionnels pour detail
  metadata?: Record<string, any>;
  invoices?: SubscriptionInvoice[];
  payment_method_id?: string;
  payment_method_last_four?: string;
  history?: SubscriptionHistoryEntry[];
  total_paid?: number;
  lifetime_value?: number;
}

export interface SubscriptionInvoice {
  id: string;
  subscription_id: string;
  customer_name: string;
  number: string;
  status: InvoiceStatus;
  amount: number;
  currency: string;
  period_start: string;
  period_end: string;
  due_date: string;
  paid_at?: string;
  created_at: string;
}

export interface SubscriptionStats {
  total_plans: number;
  active_subscriptions: number;
  trial_subscriptions: number;
  mrr: number;
  arr: number;
  churn_rate: number;
  new_subscribers_month: number;
  revenue_this_month: number;
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

export const INTERVALS: Array<{ value: SubscriptionInterval; label: string; months: number }> = [
  { value: 'MONTHLY', label: 'Mensuel', months: 1 },
  { value: 'QUARTERLY', label: 'Trimestriel', months: 3 },
  { value: 'YEARLY', label: 'Annuel', months: 12 }
];

export const SUBSCRIPTION_STATUS: Array<{ value: SubscriptionStatus; label: string }> = [
  { value: 'ACTIVE', label: 'Actif' },
  { value: 'TRIAL', label: 'Essai' },
  { value: 'PAST_DUE', label: 'En retard' },
  { value: 'CANCELLED', label: 'Annule' },
  { value: 'EXPIRED', label: 'Expire' }
];

export const INVOICE_STATUS: Array<{ value: InvoiceStatus; label: string }> = [
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'OPEN', label: 'Ouverte' },
  { value: 'PAID', label: 'Payee' },
  { value: 'VOID', label: 'Annulee' },
  { value: 'UNCOLLECTIBLE', label: 'Irrecouvrable' }
];

export const SUBSCRIPTION_STATUS_CONFIG: Record<SubscriptionStatus, {
  label: string;
  color: 'green' | 'orange' | 'red' | 'blue' | 'gray';
  description: string;
}> = {
  ACTIVE: {
    label: 'Actif',
    color: 'green',
    description: 'L\'abonnement est actif et en cours'
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
  CANCELLED: {
    label: 'Annule',
    color: 'red',
    description: 'L\'abonnement a ete annule'
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

export const INTERVAL_CONFIG: Record<SubscriptionInterval, {
  label: string;
  shortLabel: string;
  months: number;
}> = {
  MONTHLY: { label: 'Mensuel', shortLabel: '/mois', months: 1 },
  QUARTERLY: { label: 'Trimestriel', shortLabel: '/trim.', months: 3 },
  YEARLY: { label: 'Annuel', shortLabel: '/an', months: 12 }
};

// ============================================================================
// HELPERS
// ============================================================================

export const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);
};

export const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

export const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

export const formatPercent = (value: number): string => {
  return `${value.toFixed(1)}%`;
};

export const getSubscriptionAge = (subscription: Subscription): string => {
  const start = new Date(subscription.start_date);
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
  const start = new Date(subscription.start_date);
  const now = new Date();
  return Math.floor((now.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
};

export const getDaysUntilRenewal = (subscription: Subscription): number => {
  const end = new Date(subscription.current_period_end);
  const now = new Date();
  return Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
};

export const isInTrial = (subscription: Subscription): boolean => {
  return subscription.status === 'TRIAL';
};

export const isActive = (subscription: Subscription): boolean => {
  return subscription.status === 'ACTIVE' || subscription.status === 'TRIAL';
};

export const isPastDue = (subscription: Subscription): boolean => {
  return subscription.status === 'PAST_DUE';
};

export const isCancelled = (subscription: Subscription): boolean => {
  return subscription.status === 'CANCELLED' || subscription.status === 'EXPIRED';
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

export const getMonthlyEquivalent = (amount: number, interval: SubscriptionInterval): number => {
  const config = INTERVAL_CONFIG[interval];
  return amount / config.months;
};

export const getYearlyEquivalent = (amount: number, interval: SubscriptionInterval): number => {
  const config = INTERVAL_CONFIG[interval];
  return (amount / config.months) * 12;
};

export const getIntervalLabel = (interval: SubscriptionInterval): string => {
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
    .reduce((sum, inv) => sum + inv.amount, 0);
};
