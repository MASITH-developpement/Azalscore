/**
 * AZALSCORE - Marketplace API
 * ===========================
 * Complete typed API client for marketplace module.
 * Covers: Plans, Checkout, Orders, Discount Codes, Provisioning
 */

import { api } from '@/core/api-client';

// ============================================================================
// ENUMS
// ============================================================================

export type PlanType = 'FREE' | 'STARTER' | 'PROFESSIONAL' | 'ENTERPRISE' | 'CUSTOM';

export type BillingCycle = 'MONTHLY' | 'ANNUAL';

export type PaymentMethod = 'CARD' | 'SEPA' | 'TRANSFER' | 'PAYPAL';

export type OrderStatus =
  | 'PENDING'
  | 'PAYMENT_PENDING'
  | 'PAID'
  | 'PROVISIONING'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'REFUNDED'
  | 'FAILED';

// ============================================================================
// PLANS
// ============================================================================

export interface PlanFeature {
  name: string;
  included: boolean;
  description?: string | null;
}

export interface CommercialPlan {
  id: string;
  code: string;
  name: string;
  plan_type: PlanType;
  description?: string | null;
  price_monthly: string;
  price_annual: string;
  currency: string;
  max_users: number;
  max_storage_gb: number;
  max_documents_month: number;
  modules_included: string[];
  features: string[];
  trial_days: number;
  setup_fee: string;
  is_featured: boolean;
}

export interface PlanComparison {
  plans: CommercialPlan[];
  features: Array<Record<string, unknown>>;
}

// ============================================================================
// CHECKOUT
// ============================================================================

export interface CheckoutRequest {
  plan_code: string;
  billing_cycle: BillingCycle;
  customer_email: string;
  customer_name: string;
  company_name?: string | null;
  company_siret?: string | null;
  phone?: string | null;
  billing_address_line1: string;
  billing_address_line2?: string | null;
  billing_city: string;
  billing_postal_code: string;
  billing_country?: string;
  payment_method: PaymentMethod;
  discount_code?: string | null;
  accept_terms: boolean;
  accept_privacy: boolean;
}

export interface CheckoutResponse {
  order_id: string;
  order_number: string;
  status: OrderStatus;
  subtotal: string;
  tax_amount: string;
  discount_amount: string;
  total: string;
  currency: string;
  payment_intent_client_secret?: string | null;
  checkout_url?: string | null;
  instructions?: string | null;
}

// ============================================================================
// ORDERS
// ============================================================================

export interface Order {
  id: string;
  order_number: string;
  status: OrderStatus;
  plan_code: string;
  billing_cycle: BillingCycle;
  customer_email: string;
  customer_name?: string | null;
  company_name?: string | null;
  subtotal: string;
  tax_amount: string;
  discount_amount: string;
  total: string;
  currency: string;
  payment_method?: PaymentMethod | null;
  paid_at?: string | null;
  tenant_id?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface OrderDetail extends Order {
  company_siret?: string | null;
  phone?: string | null;
  billing_address_line1?: string | null;
  billing_address_line2?: string | null;
  billing_city?: string | null;
  billing_postal_code?: string | null;
  billing_country?: string | null;
  payment_intent_id?: string | null;
  payment_status?: string | null;
  tenant_created_at?: string | null;
  notes?: string | null;
}

// ============================================================================
// DISCOUNT CODES
// ============================================================================

export interface DiscountCodeValidate {
  code: string;
  plan_code: string;
  order_amount: string;
}

export interface DiscountCodeResponse {
  code: string;
  valid: boolean;
  discount_type?: string | null;
  discount_value?: string | null;
  final_discount?: string | null;
  message: string;
}

// ============================================================================
// PROVISIONING
// ============================================================================

export interface TenantProvisionRequest {
  order_id: string;
}

export interface TenantProvisionResponse {
  tenant_id: string;
  admin_email: string;
  login_url: string;
  temporary_password?: string | null;
  welcome_email_sent: boolean;
}

// ============================================================================
// DASHBOARD / STATS
// ============================================================================

export interface MarketplaceStats {
  total_orders: number;
  total_revenue: string;
  orders_today: number;
  revenue_today: string;
  orders_month: number;
  revenue_month: string;
  conversion_rate: number;
  avg_order_value: string;
  by_plan: Record<string, number>;
  by_billing_cycle: Record<string, number>;
}

export interface MarketplaceDashboard {
  stats: MarketplaceStats;
  recent_orders: Order[];
  popular_plans: CommercialPlan[];
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/marketplace';

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

export const marketplaceApi = {
  // ==========================================================================
  // Plans (Public)
  // ==========================================================================

  listPlans: () =>
    api.get<CommercialPlan[]>(`${BASE_PATH}/plans`),

  getPlan: (planCode: string) =>
    api.get<CommercialPlan>(`${BASE_PATH}/plans/${planCode}`),

  seedPlans: () =>
    api.post<{ status: string }>(`${BASE_PATH}/plans/seed`, {}),

  // ==========================================================================
  // Checkout (Public)
  // ==========================================================================

  createCheckout: (data: CheckoutRequest) =>
    api.post<CheckoutResponse>(`${BASE_PATH}/checkout`, data),

  validateDiscountCode: (data: DiscountCodeValidate) =>
    api.post<DiscountCodeResponse>(`${BASE_PATH}/discount/validate`, data),

  // ==========================================================================
  // Orders
  // ==========================================================================

  listOrders: (params?: {
    status?: OrderStatus;
    skip?: number;
    limit?: number;
  }) =>
    api.get<Order[]>(`${BASE_PATH}/orders${buildQueryString(params || {})}`),

  getOrder: (orderId: string) =>
    api.get<OrderDetail>(`${BASE_PATH}/orders/${orderId}`),

  getOrderByNumber: (orderNumber: string) =>
    api.get<Order>(`${BASE_PATH}/orders/number/${orderNumber}`),

  // ==========================================================================
  // Provisioning
  // ==========================================================================

  provisionTenant: (data: TenantProvisionRequest) =>
    api.post<TenantProvisionResponse>(`${BASE_PATH}/provision`, data),

  // ==========================================================================
  // Dashboard
  // ==========================================================================

  getDashboard: () =>
    api.get<MarketplaceDashboard>(`${BASE_PATH}/dashboard`),
};

export default marketplaceApi;
