/**
 * AZALSCORE - Subscriptions Management API
 * =========================================
 * Complete typed API client for subscriptions module.
 * Covers: Plans, Add-ons, Subscriptions, Invoices, Payments, Usage, Coupons, Metrics
 */

import { api } from '@/core/api-client';

// ============================================================================
// ENUMS
// ============================================================================

export type PlanInterval = 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'YEARLY';

export type SubscriptionStatus =
  | 'TRIALING'
  | 'ACTIVE'
  | 'PAST_DUE'
  | 'PAUSED'
  | 'CANCELED'
  | 'UNPAID'
  | 'INCOMPLETE'
  | 'INCOMPLETE_EXPIRED';

export type InvoiceStatus = 'DRAFT' | 'OPEN' | 'PAID' | 'VOID' | 'UNCOLLECTIBLE';

export type PaymentStatus = 'PENDING' | 'SUCCEEDED' | 'FAILED' | 'CANCELED' | 'REFUNDED';

export type UsageType = 'LICENSED' | 'METERED' | 'TIERED';

// ============================================================================
// PLANS
// ============================================================================

export interface Plan {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  base_price: string;
  currency: string;
  interval: PlanInterval;
  interval_count: number;
  trial_days: number;
  trial_once: boolean;
  max_users?: number | null;
  max_storage_gb?: string | null;
  max_api_calls?: number | null;
  features?: Record<string, unknown> | null;
  modules_included?: string[] | null;
  per_user_price: string;
  included_users: number;
  setup_fee: string;
  is_public: boolean;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PlanCreate {
  code: string;
  name: string;
  description?: string | null;
  base_price: string;
  currency?: string;
  interval?: PlanInterval;
  interval_count?: number;
  trial_days?: number;
  trial_once?: boolean;
  max_users?: number | null;
  max_storage_gb?: string | null;
  max_api_calls?: number | null;
  features?: Record<string, unknown> | null;
  modules_included?: string[] | null;
  per_user_price?: string;
  included_users?: number;
  setup_fee?: string;
  is_public?: boolean;
  sort_order?: number;
}

export interface PlanUpdate {
  name?: string | null;
  description?: string | null;
  base_price?: string | null;
  trial_days?: number | null;
  max_users?: number | null;
  max_storage_gb?: string | null;
  max_api_calls?: number | null;
  features?: Record<string, unknown> | null;
  modules_included?: string[] | null;
  per_user_price?: string | null;
  setup_fee?: string | null;
  is_public?: boolean | null;
  is_active?: boolean | null;
  sort_order?: number | null;
}

export interface PlanList {
  items: Plan[];
  total: number;
}

// ============================================================================
// ADD-ONS
// ============================================================================

export interface AddOn {
  id: number;
  tenant_id: string;
  plan_id: number;
  code: string;
  name: string;
  description?: string | null;
  price: string;
  usage_type: UsageType;
  unit_name?: string | null;
  min_quantity: number;
  max_quantity?: number | null;
  is_active: boolean;
  created_at: string;
}

export interface AddOnCreate {
  plan_id: number;
  code: string;
  name: string;
  description?: string | null;
  price: string;
  usage_type?: UsageType;
  unit_name?: string | null;
  min_quantity?: number;
  max_quantity?: number | null;
}

export interface AddOnUpdate {
  name?: string | null;
  description?: string | null;
  price?: string | null;
  unit_name?: string | null;
  min_quantity?: number | null;
  max_quantity?: number | null;
  is_active?: boolean | null;
}

// ============================================================================
// SUBSCRIPTIONS
// ============================================================================

export interface SubscriptionItem {
  id: number;
  add_on_code?: string | null;
  name: string;
  description?: string | null;
  unit_price: string;
  quantity: number;
  usage_type: UsageType;
  metered_usage: string;
  is_active: boolean;
}

export interface SubscriptionItemCreate {
  add_on_code?: string | null;
  name: string;
  description?: string | null;
  unit_price: string;
  quantity?: number;
  usage_type?: UsageType;
}

export interface Subscription {
  id: number;
  tenant_id: string;
  subscription_number: string;
  external_id?: string | null;
  plan_id: number;
  customer_id: number;
  customer_name?: string | null;
  customer_email?: string | null;
  status: SubscriptionStatus;
  quantity: number;
  current_users: number;
  trial_start?: string | null;
  trial_end?: string | null;
  current_period_start: string;
  current_period_end: string;
  started_at: string;
  ended_at?: string | null;
  cancel_at_period_end: boolean;
  canceled_at?: string | null;
  paused_at?: string | null;
  resume_at?: string | null;
  billing_cycle_anchor: number;
  discount_percent: string;
  discount_end_date?: string | null;
  mrr: string;
  arr: string;
  items: SubscriptionItem[];
  created_at: string;
  updated_at: string;
}

export interface SubscriptionCreate {
  plan_id: number;
  customer_id: number;
  customer_name?: string | null;
  customer_email?: string | null;
  quantity?: number;
  start_date?: string | null;
  trial_end?: string | null;
  billing_cycle_anchor?: number | null;
  discount_percent?: string | null;
  discount_end_date?: string | null;
  coupon_code?: string | null;
  collection_method?: string;
  default_payment_method_id?: string | null;
  items?: SubscriptionItemCreate[] | null;
  extra_data?: Record<string, unknown> | null;
  notes?: string | null;
}

export interface SubscriptionUpdate {
  quantity?: number | null;
  discount_percent?: string | null;
  discount_end_date?: string | null;
  default_payment_method_id?: string | null;
  extra_data?: Record<string, unknown> | null;
  notes?: string | null;
}

export interface SubscriptionList {
  items: Subscription[];
  total: number;
  page: number;
  page_size: number;
}

export interface SubscriptionChangePlanRequest {
  new_plan_id: number;
  new_quantity?: number | null;
  prorate?: boolean;
  effective_date?: string | null;
  reason?: string | null;
}

export interface SubscriptionCancelRequest {
  cancel_at_period_end?: boolean;
  reason?: string | null;
  feedback?: string | null;
}

export interface SubscriptionPauseRequest {
  resume_at?: string | null;
  reason?: string | null;
}

// ============================================================================
// INVOICES
// ============================================================================

export interface InvoiceLine {
  id: number;
  description: string;
  item_type?: string | null;
  period_start?: string | null;
  period_end?: string | null;
  quantity: string;
  unit_price: string;
  discount_amount: string;
  amount: string;
  tax_rate: string;
  tax_amount: string;
  proration: boolean;
}

export interface InvoiceLineCreate {
  description: string;
  item_type?: string | null;
  period_start?: string | null;
  period_end?: string | null;
  quantity?: string;
  unit_price: string;
  discount_amount?: string;
  tax_rate?: string;
}

export interface Invoice {
  id: number;
  tenant_id: string;
  subscription_id: number;
  invoice_number: string;
  external_id?: string | null;
  customer_id: number;
  customer_name?: string | null;
  customer_email?: string | null;
  status: InvoiceStatus;
  period_start: string;
  period_end: string;
  due_date?: string | null;
  finalized_at?: string | null;
  paid_at?: string | null;
  subtotal: string;
  discount_amount: string;
  tax_rate: string;
  tax_amount: string;
  total: string;
  amount_paid: string;
  amount_remaining: string;
  currency: string;
  collection_method: string;
  attempt_count: number;
  hosted_invoice_url?: string | null;
  pdf_url?: string | null;
  lines: InvoiceLine[];
  created_at: string;
}

export interface InvoiceCreate {
  subscription_id: number;
  customer_id: number;
  customer_name?: string | null;
  customer_email?: string | null;
  billing_address?: Record<string, unknown> | null;
  period_start: string;
  period_end: string;
  due_date?: string | null;
  collection_method?: string;
  lines: InvoiceLineCreate[];
  notes?: string | null;
  footer?: string | null;
}

export interface InvoiceList {
  items: Invoice[];
  total: number;
  page: number;
  page_size: number;
}

// ============================================================================
// PAYMENTS
// ============================================================================

export interface Payment {
  id: number;
  tenant_id: string;
  invoice_id?: number | null;
  payment_number: string;
  external_id?: string | null;
  customer_id: number;
  amount: string;
  currency: string;
  fee_amount: string;
  status: PaymentStatus;
  payment_method_type?: string | null;
  payment_method_details?: Record<string, unknown> | null;
  created_at: string;
  processed_at?: string | null;
  failure_code?: string | null;
  failure_message?: string | null;
  refunded_amount: string;
}

export interface PaymentCreate {
  invoice_id: number;
  amount: string;
  currency?: string;
  payment_method_type?: string | null;
  payment_method_id?: string | null;
}

export interface RefundRequest {
  amount?: string | null;
  reason?: string | null;
}

// ============================================================================
// USAGE
// ============================================================================

export interface UsageRecord {
  id: number;
  subscription_id: number;
  subscription_item_id?: number | null;
  quantity: string;
  unit?: string | null;
  action: string;
  timestamp: string;
  idempotency_key?: string | null;
  created_at: string;
}

export interface UsageRecordCreate {
  subscription_item_id: number;
  quantity: string;
  unit?: string | null;
  action?: string;
  timestamp?: string | null;
  idempotency_key?: string | null;
  extra_data?: Record<string, unknown> | null;
}

export interface UsageSummary {
  subscription_id: number;
  item_id: number;
  item_name: string;
  period_start: string;
  period_end: string;
  total_usage: string;
  unit?: string | null;
  estimated_amount: string;
}

// ============================================================================
// COUPONS
// ============================================================================

export interface Coupon {
  id: number;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  discount_type: string;
  discount_value: string;
  currency?: string | null;
  duration: string;
  duration_months?: number | null;
  max_redemptions?: number | null;
  times_redeemed: number;
  applies_to_plans?: number[] | null;
  first_time_only: boolean;
  valid_from?: string | null;
  valid_until?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface CouponCreate {
  code: string;
  name: string;
  description?: string | null;
  discount_type?: string;
  discount_value: string;
  currency?: string | null;
  duration?: string;
  duration_months?: number | null;
  max_redemptions?: number | null;
  applies_to_plans?: number[] | null;
  min_amount?: string | null;
  first_time_only?: boolean;
  valid_from?: string | null;
  valid_until?: string | null;
}

export interface CouponUpdate {
  name?: string | null;
  description?: string | null;
  max_redemptions?: number | null;
  valid_until?: string | null;
  is_active?: boolean | null;
}

export interface CouponValidateRequest {
  code: string;
  plan_id?: number | null;
  customer_id?: number | null;
  amount?: string | null;
}

export interface CouponValidateResponse {
  valid: boolean;
  coupon?: Coupon | null;
  discount_amount?: string | null;
  error_message?: string | null;
}

// ============================================================================
// METRICS
// ============================================================================

export interface MetricsSnapshot {
  metric_date: string;
  mrr: string;
  arr: string;
  new_mrr: string;
  expansion_mrr: string;
  contraction_mrr: string;
  churned_mrr: string;
  total_subscriptions: number;
  active_subscriptions: number;
  trialing_subscriptions: number;
  canceled_subscriptions: number;
  new_subscriptions: number;
  churned_subscriptions: number;
  total_customers: number;
  new_customers: number;
  churned_customers: number;
  churn_rate: string;
  trial_conversion_rate: string;
  arpu: string;
  average_ltv: string;
}

// ============================================================================
// DASHBOARD / STATS
// ============================================================================

export interface SubscriptionStats {
  total_plans: number;
  active_subscriptions: number;
  trial_subscriptions: number;
  mrr: string;
  arr: string;
  churn_rate: string;
  new_subscribers_month: number;
  revenue_this_month: string;
}

export interface SubscriptionDashboard {
  // Revenue
  mrr: string;
  mrr_growth: string;
  arr: string;
  // Counters
  total_active: number;
  trialing: number;
  past_due: number;
  canceled_this_month: number;
  // MRR movements
  new_mrr: string;
  expansion_mrr: string;
  contraction_mrr: string;
  churned_mrr: string;
  net_mrr_change: string;
  // Rates
  churn_rate: string;
  trial_conversion_rate: string;
  // ARPU & LTV
  arpu: string;
  average_ltv: string;
  // Top plans
  top_plans: Array<Record<string, unknown>>;
  // Upcoming renewals
  upcoming_renewals: Array<Record<string, unknown>>;
  // Pending invoices
  pending_invoices_count: number;
  pending_invoices_amount: string;
}

// ============================================================================
// WEBHOOKS
// ============================================================================

export interface WebhookEvent {
  event_type: string;
  source: string;
  payload: Record<string, unknown>;
  related_object_type?: string | null;
  related_object_id?: string | null;
}

export interface WebhookResponse {
  received: boolean;
  webhook_id: number;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/subscriptions';

function buildQueryString(
  params: Record<string, string | number | boolean | undefined | null>
): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// API CLIENT
// ============================================================================

export const subscriptionsApi = {
  // ==========================================================================
  // Plans
  // ==========================================================================

  createPlan: (data: PlanCreate) =>
    api.post<Plan>(`${BASE_PATH}/plans`, data),

  listPlans: (params?: {
    is_active?: boolean;
    is_public?: boolean;
    skip?: number;
    limit?: number;
  }) =>
    api.get<PlanList>(`${BASE_PATH}/plans${buildQueryString(params || {})}`),

  getPlan: (planId: number) =>
    api.get<Plan>(`${BASE_PATH}/plans/${planId}`),

  updatePlan: (planId: number, data: PlanUpdate) =>
    api.patch<Plan>(`${BASE_PATH}/plans/${planId}`, data),

  deletePlan: (planId: number) =>
    api.delete(`${BASE_PATH}/plans/${planId}`),

  // ==========================================================================
  // Add-ons
  // ==========================================================================

  createAddOn: (data: AddOnCreate) =>
    api.post<AddOn>(`${BASE_PATH}/addons`, data),

  listAddOns: (planId: number) =>
    api.get<AddOn[]>(`${BASE_PATH}/plans/${planId}/addons`),

  updateAddOn: (addonId: number, data: AddOnUpdate) =>
    api.patch<AddOn>(`${BASE_PATH}/addons/${addonId}`, data),

  // ==========================================================================
  // Subscriptions
  // ==========================================================================

  createSubscription: (data: SubscriptionCreate) =>
    api.post<Subscription>(`${BASE_PATH}`, data),

  listSubscriptions: (params?: {
    customer_id?: number;
    plan_id?: number;
    status?: SubscriptionStatus;
    skip?: number;
    limit?: number;
  }) =>
    api.get<SubscriptionList>(`${BASE_PATH}${buildQueryString(params || {})}`),

  getSubscription: (subscriptionId: number) =>
    api.get<Subscription>(`${BASE_PATH}/${subscriptionId}`),

  updateSubscription: (subscriptionId: number, data: SubscriptionUpdate) =>
    api.patch<Subscription>(`${BASE_PATH}/${subscriptionId}`, data),

  changeSubscriptionPlan: (subscriptionId: number, data: SubscriptionChangePlanRequest) =>
    api.post<Subscription>(`${BASE_PATH}/${subscriptionId}/change-plan`, data),

  cancelSubscription: (subscriptionId: number, data: SubscriptionCancelRequest) =>
    api.post<Subscription>(`${BASE_PATH}/${subscriptionId}/cancel`, data),

  pauseSubscription: (subscriptionId: number, data: SubscriptionPauseRequest) =>
    api.post<Subscription>(`${BASE_PATH}/${subscriptionId}/pause`, data),

  resumeSubscription: (subscriptionId: number) =>
    api.post<Subscription>(`${BASE_PATH}/${subscriptionId}/resume`, {}),

  // ==========================================================================
  // Invoices
  // ==========================================================================

  createInvoice: (data: InvoiceCreate) =>
    api.post<Invoice>(`${BASE_PATH}/invoices`, data),

  listInvoices: (params?: {
    subscription_id?: number;
    customer_id?: number;
    status?: InvoiceStatus;
    skip?: number;
    limit?: number;
  }) =>
    api.get<InvoiceList>(`${BASE_PATH}/invoices${buildQueryString(params || {})}`),

  getInvoice: (invoiceId: number) =>
    api.get<Invoice>(`${BASE_PATH}/invoices/${invoiceId}`),

  finalizeInvoice: (invoiceId: number) =>
    api.post<Invoice>(`${BASE_PATH}/invoices/${invoiceId}/finalize`, {}),

  voidInvoice: (invoiceId: number) =>
    api.post<Invoice>(`${BASE_PATH}/invoices/${invoiceId}/void`, {}),

  payInvoice: (invoiceId: number, amount?: number) =>
    api.post<Invoice>(
      `${BASE_PATH}/invoices/${invoiceId}/pay${buildQueryString({ amount })}`,
      {}
    ),

  // ==========================================================================
  // Payments
  // ==========================================================================

  createPayment: (data: PaymentCreate) =>
    api.post<Payment>(`${BASE_PATH}/payments`, data),

  refundPayment: (paymentId: number, data: RefundRequest) =>
    api.post<Payment>(`${BASE_PATH}/payments/${paymentId}/refund`, data),

  // ==========================================================================
  // Usage
  // ==========================================================================

  createUsageRecord: (data: UsageRecordCreate) =>
    api.post<UsageRecord>(`${BASE_PATH}/usage`, data),

  getUsageSummary: (subscriptionId: number, periodStart?: string, periodEnd?: string) =>
    api.get<UsageSummary[]>(
      `${BASE_PATH}/${subscriptionId}/usage${buildQueryString({
        period_start: periodStart,
        period_end: periodEnd,
      })}`
    ),

  // ==========================================================================
  // Coupons
  // ==========================================================================

  createCoupon: (data: CouponCreate) =>
    api.post<Coupon>(`${BASE_PATH}/coupons`, data),

  listCoupons: (params?: {
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }) =>
    api.get<Coupon[]>(`${BASE_PATH}/coupons${buildQueryString(params || {})}`),

  getCoupon: (couponId: number) =>
    api.get<Coupon>(`${BASE_PATH}/coupons/${couponId}`),

  updateCoupon: (couponId: number, data: CouponUpdate) =>
    api.patch<Coupon>(`${BASE_PATH}/coupons/${couponId}`, data),

  validateCoupon: (data: CouponValidateRequest) =>
    api.post<CouponValidateResponse>(`${BASE_PATH}/coupons/validate`, data),

  // ==========================================================================
  // Metrics
  // ==========================================================================

  calculateMetrics: (metricDate?: string) =>
    api.post<MetricsSnapshot>(
      `${BASE_PATH}/metrics/calculate${buildQueryString({ metric_date: metricDate })}`,
      {}
    ),

  getMetrics: (metricDate: string) =>
    api.get<MetricsSnapshot>(`${BASE_PATH}/metrics/${metricDate}`),

  getMetricsTrend: (startDate: string, endDate: string) =>
    api.get<MetricsSnapshot[]>(
      `${BASE_PATH}/metrics/trend${buildQueryString({
        start_date: startDate,
        end_date: endDate,
      })}`
    ),

  // ==========================================================================
  // Stats & Dashboard
  // ==========================================================================

  getStats: () =>
    api.get<SubscriptionStats>(`${BASE_PATH}/stats`),

  getDashboard: () =>
    api.get<SubscriptionDashboard>(`${BASE_PATH}/dashboard`),

  // ==========================================================================
  // Webhooks
  // ==========================================================================

  receiveWebhook: (event: WebhookEvent) =>
    api.post<WebhookResponse>(`${BASE_PATH}/webhooks`, event),
};

export default subscriptionsApi;
