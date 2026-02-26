/**
 * AZALSCORE - Stripe Integration API
 * ====================================
 * Complete typed API client for Stripe payment integration.
 * Covers: Customers, Payments, Checkout, Refunds, Disputes, Connect, Webhooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const stripeKeys = {
  all: ['stripe'] as const,
  config: () => [...stripeKeys.all, 'config'] as const,
  dashboard: () => [...stripeKeys.all, 'dashboard'] as const,
  analytics: (period?: string) => [...stripeKeys.all, 'analytics', period] as const,

  // Customers
  customers: () => [...stripeKeys.all, 'customers'] as const,
  customer: (id: string) => [...stripeKeys.customers(), id] as const,
  customerPaymentMethods: (customerId: string) => [...stripeKeys.customer(customerId), 'payment-methods'] as const,

  // Payment Intents
  paymentIntents: () => [...stripeKeys.all, 'payment-intents'] as const,
  paymentIntent: (id: string) => [...stripeKeys.paymentIntents(), id] as const,

  // Checkout Sessions
  checkoutSessions: () => [...stripeKeys.all, 'checkout-sessions'] as const,
  checkoutSession: (id: string) => [...stripeKeys.checkoutSessions(), id] as const,

  // Refunds
  refunds: () => [...stripeKeys.all, 'refunds'] as const,
  refund: (id: string) => [...stripeKeys.refunds(), id] as const,

  // Disputes
  disputes: () => [...stripeKeys.all, 'disputes'] as const,
  dispute: (id: string) => [...stripeKeys.disputes(), id] as const,

  // Products & Prices
  products: () => [...stripeKeys.all, 'products'] as const,
  product: (id: string) => [...stripeKeys.products(), id] as const,
  prices: (productId?: string) => [...stripeKeys.all, 'prices', productId] as const,

  // Connect
  connectAccounts: () => [...stripeKeys.all, 'connect-accounts'] as const,
  connectAccount: (id: string) => [...stripeKeys.connectAccounts(), id] as const,
  payouts: (accountId?: string) => [...stripeKeys.all, 'payouts', accountId] as const,

  // Webhooks
  webhookEvents: () => [...stripeKeys.all, 'webhook-events'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type PaymentIntentStatus =
  | 'requires_payment_method'
  | 'requires_confirmation'
  | 'requires_action'
  | 'processing'
  | 'requires_capture'
  | 'canceled'
  | 'succeeded';

export type RefundStatus = 'pending' | 'succeeded' | 'failed' | 'canceled';
export type DisputeStatus = 'warning_needs_response' | 'warning_under_review' | 'warning_closed' | 'needs_response' | 'under_review' | 'charge_refunded' | 'won' | 'lost';
export type StripeAccountStatus = 'pending' | 'active' | 'restricted' | 'disabled';
export type WebhookStatus = 'pending' | 'processed' | 'failed' | 'skipped';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface StripeConfig {
  id: number;
  tenant_id: string;
  is_live_mode: boolean;
  default_currency: string;
  default_payment_methods: string[];
  statement_descriptor?: string | null;
  auto_capture: boolean;
  send_receipts: boolean;
  connect_enabled: boolean;
  platform_fee_percent: number;
  has_live_key: boolean;
  has_test_key: boolean;
  created_at: string;
}

export interface StripeCustomer {
  id: number;
  tenant_id: string;
  stripe_customer_id: string;
  customer_id: number;
  email?: string | null;
  name?: string | null;
  phone?: string | null;
  default_payment_method_id?: string | null;
  balance: number;
  currency?: string | null;
  delinquent: boolean;
  is_synced: boolean;
  created_at: string;
}

export interface PaymentMethod {
  id: number;
  stripe_payment_method_id: string;
  method_type: string;
  card_brand?: string | null;
  card_last4?: string | null;
  card_exp_month?: number | null;
  card_exp_year?: number | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
}

export interface PaymentIntent {
  id: number;
  stripe_payment_intent_id: string;
  amount: number;
  amount_received: number;
  currency: string;
  status: PaymentIntentStatus;
  client_secret?: string | null;
  payment_method_id?: string | null;
  capture_method: string;
  invoice_id?: number | null;
  order_id?: number | null;
  description?: string | null;
  stripe_fee?: number | null;
  net_amount?: number | null;
  created_at: string;
}

export interface CheckoutSession {
  id: number;
  stripe_session_id: string;
  url: string;
  mode: string;
  payment_status?: string | null;
  status: string;
  amount_total?: number | null;
  currency: string;
  customer_email?: string | null;
  expires_at?: string | null;
  created_at: string;
}

export interface Refund {
  id: number;
  stripe_refund_id: string;
  payment_intent_id: number;
  amount: number;
  currency: string;
  status: RefundStatus;
  reason?: string | null;
  description?: string | null;
  created_at: string;
}

export interface Dispute {
  id: number;
  stripe_dispute_id: string;
  stripe_charge_id?: string | null;
  amount: number;
  currency: string;
  status: DisputeStatus;
  reason?: string | null;
  evidence_due_by?: string | null;
  created_at: string;
}

export interface StripeProduct {
  id: number;
  stripe_product_id: string;
  name: string;
  description?: string | null;
  product_id?: number | null;
  plan_id?: number | null;
  active: boolean;
  created_at: string;
}

export interface StripePrice {
  id: number;
  stripe_price_id: string;
  unit_amount: number;
  currency: string;
  recurring_interval?: string | null;
  recurring_interval_count: number;
  active: boolean;
  nickname?: string | null;
  created_at: string;
}

export interface ConnectAccount {
  id: number;
  stripe_account_id: string;
  vendor_id?: number | null;
  email?: string | null;
  account_type: string;
  status: StripeAccountStatus;
  charges_enabled: boolean;
  payouts_enabled: boolean;
  details_submitted: boolean;
  onboarding_url?: string | null;
  created_at: string;
}

export interface Payout {
  id: number;
  stripe_payout_id: string;
  amount: number;
  currency: string;
  status: string;
  arrival_date?: string | null;
  description?: string | null;
  created_at: string;
}

export interface WebhookEvent {
  id: number;
  stripe_event_id: string;
  event_type: string;
  object_type?: string | null;
  object_id?: string | null;
  status: WebhookStatus;
  processed_at?: string | null;
  processing_error?: string | null;
  created_at: string;
}

export interface StripeDashboard {
  total_volume_30d: number;
  successful_payments_30d: number;
  failed_payments_30d: number;
  refunds_30d: number;
  success_rate: number;
  average_transaction: number;
  open_disputes: number;
  disputed_amount: number;
  available_balance: number;
  pending_balance: number;
  recent_payments: PaymentIntent[];
  recent_refunds: Refund[];
}

export interface PaymentAnalytics {
  period: string;
  start_date: string;
  end_date: string;
  total_volume: number;
  total_count: number;
  average_amount: number;
  by_method: Record<string, number>;
  by_status: Record<string, number>;
  by_currency: Record<string, number>;
  chart_data: Array<{ date: string; amount: number; count: number }>;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface StripeCustomerCreate {
  customer_id: number;
  email?: string;
  name?: string;
  phone?: string;
  description?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  tax_exempt?: string;
  metadata?: Record<string, string>;
}

export interface StripeCustomerUpdate {
  email?: string;
  name?: string;
  phone?: string;
  description?: string;
  address_line1?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  default_payment_method_id?: string;
  metadata?: Record<string, string>;
}

export interface PaymentMethodCreate {
  stripe_customer_id: string;
  method_type?: string;
  token?: string;
  set_as_default?: boolean;
}

export interface SetupIntentCreate {
  customer_id: number;
  payment_method_types?: string[];
  usage?: string;
}

export interface SetupIntentResponse {
  setup_intent_id: string;
  client_secret: string;
  status: string;
  payment_method_types: string[];
}

export interface PaymentIntentCreate {
  customer_id?: number;
  amount: number;
  currency?: string;
  payment_method_types?: string[];
  capture_method?: string;
  confirm?: boolean;
  payment_method_id?: string;
  receipt_email?: string;
  description?: string;
  metadata?: Record<string, string>;
  invoice_id?: number;
  order_id?: number;
  subscription_id?: number;
}

export interface PaymentIntentUpdate {
  amount?: number;
  description?: string;
  metadata?: Record<string, string>;
  receipt_email?: string;
}

export interface PaymentIntentConfirm {
  payment_method_id?: string;
  return_url?: string;
}

export interface PaymentIntentCapture {
  amount_to_capture?: number;
}

export interface CheckoutLineItem {
  name: string;
  description?: string;
  amount: number;
  currency?: string;
  quantity?: number;
  images?: string[];
}

export interface CheckoutSessionCreate {
  customer_id?: number;
  customer_email?: string;
  mode?: string;
  success_url: string;
  cancel_url: string;
  line_items?: CheckoutLineItem[];
  price_id?: string;
  quantity?: number;
  trial_period_days?: number;
  allow_promotion_codes?: boolean;
  collect_shipping_address?: boolean;
  payment_method_types?: string[];
  invoice_id?: number;
  order_id?: number;
  subscription_id?: number;
  metadata?: Record<string, string>;
}

export interface RefundCreate {
  payment_intent_id: number;
  amount?: number;
  reason?: string;
  description?: string;
  metadata?: Record<string, string>;
}

export interface DisputeEvidenceSubmit {
  customer_name?: string;
  customer_email?: string;
  product_description?: string;
  shipping_documentation?: string;
  receipt?: string;
  uncategorized_text?: string;
}

export interface StripeProductCreate {
  name: string;
  description?: string;
  product_id?: number;
  plan_id?: number;
  images?: string[];
  metadata?: Record<string, string>;
}

export interface StripePriceCreate {
  product_id: number;
  unit_amount: number;
  currency?: string;
  recurring_interval?: string;
  recurring_interval_count?: number;
  nickname?: string;
  metadata?: Record<string, string>;
}

export interface ConnectAccountCreate {
  vendor_id: number;
  email: string;
  country?: string;
  account_type?: string;
  business_type?: string;
  return_url: string;
  refresh_url: string;
}

export interface TransferCreate {
  destination_account_id: string;
  amount: number;
  currency?: string;
  description?: string;
  source_transaction?: string;
  metadata?: Record<string, string>;
}

export interface StripeConfigCreate {
  api_key_live?: string;
  api_key_test?: string;
  webhook_secret_live?: string;
  webhook_secret_test?: string;
  is_live_mode?: boolean;
  default_currency?: string;
  default_payment_methods?: string[];
  statement_descriptor?: string;
  auto_capture?: boolean;
  send_receipts?: boolean;
}

export interface StripeConfigUpdate {
  api_key_live?: string;
  api_key_test?: string;
  webhook_secret_live?: string;
  webhook_secret_test?: string;
  is_live_mode?: boolean;
  default_currency?: string;
  statement_descriptor?: string;
  auto_capture?: boolean;
  send_receipts?: boolean;
  connect_enabled?: boolean;
  platform_fee_percent?: number;
}

// ============================================================================
// HOOKS - CONFIGURATION
// ============================================================================

export function useStripeConfig() {
  return useQuery({
    queryKey: stripeKeys.config(),
    queryFn: async () => {
      const response = await api.get<StripeConfig>('/stripe/config');
      return response;
    },
  });
}

export function useUpdateStripeConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: StripeConfigUpdate) => {
      return api.put<StripeConfig>('/stripe/config', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.config() });
    },
  });
}

export function useCreateStripeConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: StripeConfigCreate) => {
      return api.post<StripeConfig>('/stripe/config', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.config() });
    },
  });
}

// ============================================================================
// HOOKS - DASHBOARD & ANALYTICS
// ============================================================================

export function useStripeDashboard() {
  return useQuery({
    queryKey: stripeKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<StripeDashboard>('/stripe/dashboard');
      return response;
    },
  });
}

export function usePaymentAnalytics(period: string = 'monthly') {
  return useQuery({
    queryKey: stripeKeys.analytics(period),
    queryFn: async () => {
      const response = await api.get<PaymentAnalytics>(`/stripe/analytics?period=${period}`);
      return response;
    },
  });
}

// ============================================================================
// HOOKS - CUSTOMERS
// ============================================================================

export function useStripeCustomers(filters?: {
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...stripeKeys.customers(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: StripeCustomer[]; total: number }>(
        `/stripe/customers${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useStripeCustomer(id: string) {
  return useQuery({
    queryKey: stripeKeys.customer(id),
    queryFn: async () => {
      const response = await api.get<StripeCustomer>(`/stripe/customers/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateStripeCustomer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: StripeCustomerCreate) => {
      return api.post<StripeCustomer>('/stripe/customers', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.customers() });
    },
  });
}

export function useUpdateStripeCustomer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: StripeCustomerUpdate }) => {
      return api.put<StripeCustomer>(`/stripe/customers/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.customers() });
      queryClient.invalidateQueries({ queryKey: stripeKeys.customer(id) });
    },
  });
}

export function useSyncStripeCustomer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<StripeCustomer>(`/stripe/customers/${id}/sync`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.customer(id) });
    },
  });
}

// ============================================================================
// HOOKS - PAYMENT METHODS
// ============================================================================

export function useCustomerPaymentMethods(customerId: string) {
  return useQuery({
    queryKey: stripeKeys.customerPaymentMethods(customerId),
    queryFn: async () => {
      const response = await api.get<{ items: PaymentMethod[] }>(
        `/stripe/customers/${customerId}/payment-methods`
      );
      return response;
    },
    enabled: !!customerId,
  });
}

export function useAddPaymentMethod() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: PaymentMethodCreate) => {
      return api.post<PaymentMethod>('/stripe/payment-methods', data);
    },
    onSuccess: (_, { stripe_customer_id }) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.customerPaymentMethods(stripe_customer_id) });
    },
  });
}

export function useSetDefaultPaymentMethod() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ customerId, paymentMethodId }: { customerId: string; paymentMethodId: string }) => {
      return api.post(`/stripe/customers/${customerId}/payment-methods/${paymentMethodId}/set-default`);
    },
    onSuccess: (_, { customerId }) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.customerPaymentMethods(customerId) });
      queryClient.invalidateQueries({ queryKey: stripeKeys.customer(customerId) });
    },
  });
}

export function useDeletePaymentMethod() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ customerId, paymentMethodId }: { customerId: string; paymentMethodId: string }) => {
      return api.delete(`/stripe/payment-methods/${paymentMethodId}`);
    },
    onSuccess: (_, { customerId }) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.customerPaymentMethods(customerId) });
    },
  });
}

export function useCreateSetupIntent() {
  return useMutation({
    mutationFn: async (data: SetupIntentCreate) => {
      return api.post<SetupIntentResponse>('/stripe/setup-intents', data);
    },
  });
}

// ============================================================================
// HOOKS - PAYMENT INTENTS
// ============================================================================

export function usePaymentIntents(filters?: {
  status?: PaymentIntentStatus;
  customer_id?: number;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...stripeKeys.paymentIntents(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.customer_id) params.append('customer_id', String(filters.customer_id));
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: PaymentIntent[]; total: number }>(
        `/stripe/payment-intents${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function usePaymentIntent(id: string) {
  return useQuery({
    queryKey: stripeKeys.paymentIntent(id),
    queryFn: async () => {
      const response = await api.get<PaymentIntent>(`/stripe/payment-intents/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreatePaymentIntent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: PaymentIntentCreate) => {
      return api.post<PaymentIntent>('/stripe/payment-intents', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.paymentIntents() });
      queryClient.invalidateQueries({ queryKey: stripeKeys.dashboard() });
    },
  });
}

export function useUpdatePaymentIntent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PaymentIntentUpdate }) => {
      return api.put<PaymentIntent>(`/stripe/payment-intents/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.paymentIntent(id) });
    },
  });
}

export function useConfirmPaymentIntent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PaymentIntentConfirm }) => {
      return api.post<PaymentIntent>(`/stripe/payment-intents/${id}/confirm`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.paymentIntent(id) });
      queryClient.invalidateQueries({ queryKey: stripeKeys.paymentIntents() });
      queryClient.invalidateQueries({ queryKey: stripeKeys.dashboard() });
    },
  });
}

export function useCapturePaymentIntent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data?: PaymentIntentCapture }) => {
      return api.post<PaymentIntent>(`/stripe/payment-intents/${id}/capture`, data || {});
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.paymentIntent(id) });
      queryClient.invalidateQueries({ queryKey: stripeKeys.paymentIntents() });
      queryClient.invalidateQueries({ queryKey: stripeKeys.dashboard() });
    },
  });
}

export function useCancelPaymentIntent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<PaymentIntent>(`/stripe/payment-intents/${id}/cancel`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.paymentIntent(id) });
      queryClient.invalidateQueries({ queryKey: stripeKeys.paymentIntents() });
    },
  });
}

// ============================================================================
// HOOKS - CHECKOUT SESSIONS
// ============================================================================

export function useCheckoutSessions(filters?: {
  status?: string;
  mode?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...stripeKeys.checkoutSessions(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.mode) params.append('mode', filters.mode);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: CheckoutSession[]; total: number }>(
        `/stripe/checkout-sessions${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCheckoutSession(id: string) {
  return useQuery({
    queryKey: stripeKeys.checkoutSession(id),
    queryFn: async () => {
      const response = await api.get<CheckoutSession>(`/stripe/checkout-sessions/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateCheckoutSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CheckoutSessionCreate) => {
      return api.post<CheckoutSession>('/stripe/checkout-sessions', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.checkoutSessions() });
    },
  });
}

export function useExpireCheckoutSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<CheckoutSession>(`/stripe/checkout-sessions/${id}/expire`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.checkoutSession(id) });
      queryClient.invalidateQueries({ queryKey: stripeKeys.checkoutSessions() });
    },
  });
}

// ============================================================================
// HOOKS - REFUNDS
// ============================================================================

export function useRefunds(filters?: {
  payment_intent_id?: number;
  status?: RefundStatus;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...stripeKeys.refunds(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.payment_intent_id) params.append('payment_intent_id', String(filters.payment_intent_id));
      if (filters?.status) params.append('status', filters.status);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Refund[]; total: number }>(
        `/stripe/refunds${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useRefund(id: string) {
  return useQuery({
    queryKey: stripeKeys.refund(id),
    queryFn: async () => {
      const response = await api.get<Refund>(`/stripe/refunds/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateRefund() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RefundCreate) => {
      return api.post<Refund>('/stripe/refunds', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.refunds() });
      queryClient.invalidateQueries({ queryKey: stripeKeys.paymentIntents() });
      queryClient.invalidateQueries({ queryKey: stripeKeys.dashboard() });
    },
  });
}

// ============================================================================
// HOOKS - DISPUTES
// ============================================================================

export function useDisputes(filters?: {
  status?: DisputeStatus;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...stripeKeys.disputes(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Dispute[]; total: number }>(
        `/stripe/disputes${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useDispute(id: string) {
  return useQuery({
    queryKey: stripeKeys.dispute(id),
    queryFn: async () => {
      const response = await api.get<Dispute>(`/stripe/disputes/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useSubmitDisputeEvidence() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: DisputeEvidenceSubmit }) => {
      return api.post(`/stripe/disputes/${id}/evidence`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.dispute(id) });
      queryClient.invalidateQueries({ queryKey: stripeKeys.disputes() });
    },
  });
}

export function useCloseDispute() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/stripe/disputes/${id}/close`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.dispute(id) });
      queryClient.invalidateQueries({ queryKey: stripeKeys.disputes() });
      queryClient.invalidateQueries({ queryKey: stripeKeys.dashboard() });
    },
  });
}

// ============================================================================
// HOOKS - PRODUCTS & PRICES
// ============================================================================

export function useStripeProducts(filters?: {
  active?: boolean;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...stripeKeys.products(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.active !== undefined) params.append('active', String(filters.active));
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: StripeProduct[]; total: number }>(
        `/stripe/products${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useStripeProduct(id: string) {
  return useQuery({
    queryKey: stripeKeys.product(id),
    queryFn: async () => {
      const response = await api.get<StripeProduct>(`/stripe/products/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateStripeProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: StripeProductCreate) => {
      return api.post<StripeProduct>('/stripe/products', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.products() });
    },
  });
}

export function useStripePrices(productId?: string) {
  return useQuery({
    queryKey: stripeKeys.prices(productId),
    queryFn: async () => {
      const url = productId ? `/stripe/products/${productId}/prices` : '/stripe/prices';
      const response = await api.get<{ items: StripePrice[] }>(url);
      return response;
    },
  });
}

export function useCreateStripePrice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: StripePriceCreate) => {
      return api.post<StripePrice>('/stripe/prices', data);
    },
    onSuccess: (_, { product_id }) => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.prices(String(product_id)) });
      queryClient.invalidateQueries({ queryKey: stripeKeys.prices() });
    },
  });
}

// ============================================================================
// HOOKS - CONNECT (MARKETPLACE)
// ============================================================================

export function useConnectAccounts(filters?: {
  status?: StripeAccountStatus;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...stripeKeys.connectAccounts(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ConnectAccount[]; total: number }>(
        `/stripe/connect/accounts${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useConnectAccount(id: string) {
  return useQuery({
    queryKey: stripeKeys.connectAccount(id),
    queryFn: async () => {
      const response = await api.get<ConnectAccount>(`/stripe/connect/accounts/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateConnectAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ConnectAccountCreate) => {
      return api.post<ConnectAccount>('/stripe/connect/accounts', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.connectAccounts() });
    },
  });
}

export function useGenerateOnboardingLink() {
  return useMutation({
    mutationFn: async ({ accountId, returnUrl, refreshUrl }: {
      accountId: string;
      returnUrl: string;
      refreshUrl: string;
    }) => {
      return api.post<{ url: string; expires_at: string }>(
        `/stripe/connect/accounts/${accountId}/onboarding-link`,
        { return_url: returnUrl, refresh_url: refreshUrl }
      );
    },
  });
}

export function useGenerateLoginLink() {
  return useMutation({
    mutationFn: async (accountId: string) => {
      return api.post<{ url: string }>(`/stripe/connect/accounts/${accountId}/login-link`);
    },
  });
}

export function useConnectPayouts(accountId?: string) {
  return useQuery({
    queryKey: stripeKeys.payouts(accountId),
    queryFn: async () => {
      const url = accountId
        ? `/stripe/connect/accounts/${accountId}/payouts`
        : '/stripe/payouts';
      const response = await api.get<{ items: Payout[] }>(url);
      return response;
    },
  });
}

export function useCreateTransfer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TransferCreate) => {
      return api.post('/stripe/transfers', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.payouts() });
    },
  });
}

// ============================================================================
// HOOKS - WEBHOOKS
// ============================================================================

export function useWebhookEvents(filters?: {
  event_type?: string;
  status?: WebhookStatus;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...stripeKeys.webhookEvents(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.event_type) params.append('event_type', filters.event_type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: WebhookEvent[]; total: number }>(
        `/stripe/webhook-events${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useRetryWebhookEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (eventId: string) => {
      return api.post(`/stripe/webhook-events/${eventId}/retry`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: stripeKeys.webhookEvents() });
    },
  });
}
