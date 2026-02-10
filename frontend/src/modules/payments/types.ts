/**
 * AZALSCORE Module - Payments Types
 * Types, constantes et utilitaires pour les paiements
 */

// ============================================================================
// TYPES
// ============================================================================

export type PaymentMethod = 'CARD' | 'BANK_TRANSFER' | 'TAP_TO_PAY' | 'CASH' | 'CHECK' | 'OTHER';
export type PaymentStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'REFUNDED' | 'CANCELLED';
export type RefundStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
export type SavedMethodType = 'CARD' | 'BANK_ACCOUNT' | 'SEPA';

export interface Payment {
  id: string;
  reference: string;
  amount: number;
  currency: string;
  method: PaymentMethod;
  status: PaymentStatus;
  customer_id?: string;
  customer_name?: string;
  customer_email?: string;
  invoice_id?: string;
  invoice_number?: string;
  description?: string;
  metadata?: Record<string, any>;
  error_message?: string;
  processed_at?: string;
  created_at: string;
  updated_at?: string;
  // Champs additionnels pour detail
  transaction_id?: string;
  authorization_code?: string;
  card_last_four?: string;
  card_brand?: string;
  bank_name?: string;
  fees?: number;
  net_amount?: number;
  refunds?: Refund[];
  history?: PaymentHistoryEntry[];
}

export interface Refund {
  id: string;
  payment_id: string;
  payment_reference: string;
  amount: number;
  currency: string;
  reason: string;
  status: RefundStatus;
  processed_at?: string;
  created_at: string;
  processed_by?: string;
  notes?: string;
}

export interface SavedPaymentMethod {
  id: string;
  customer_id: string;
  customer_name: string;
  type: SavedMethodType;
  last_four?: string;
  brand?: string;
  expiry_month?: number;
  expiry_year?: number;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
}

export interface PaymentStats {
  total_today: number;
  transactions_today: number;
  total_this_week: number;
  transactions_this_week: number;
  total_this_month: number;
  transactions_this_month: number;
  pending_count: number;
  failed_count: number;
  refunded_amount_month: number;
  average_transaction: number;
}

export interface PaymentHistoryEntry {
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

export const PAYMENT_METHODS: Array<{ value: PaymentMethod; label: string; icon: string }> = [
  { value: 'CARD', label: 'Carte bancaire', icon: '💳' },
  { value: 'BANK_TRANSFER', label: 'Virement', icon: '🏦' },
  { value: 'TAP_TO_PAY', label: 'Tap-to-Pay', icon: '📱' },
  { value: 'CASH', label: 'Especes', icon: '💵' },
  { value: 'CHECK', label: 'Cheque', icon: '📄' },
  { value: 'OTHER', label: 'Autre', icon: '💰' }
];

export const PAYMENT_STATUS: Array<{ value: PaymentStatus; label: string }> = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'PROCESSING', label: 'En cours' },
  { value: 'COMPLETED', label: 'Complete' },
  { value: 'FAILED', label: 'Echoue' },
  { value: 'REFUNDED', label: 'Rembourse' },
  { value: 'CANCELLED', label: 'Annule' }
];

export const REFUND_STATUS: Array<{ value: RefundStatus; label: string }> = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'PROCESSING', label: 'En cours' },
  { value: 'COMPLETED', label: 'Effectue' },
  { value: 'FAILED', label: 'Echoue' }
];

export const PAYMENT_STATUS_CONFIG: Record<PaymentStatus, {
  label: string;
  color: 'green' | 'orange' | 'red' | 'blue' | 'gray';
  description: string;
}> = {
  PENDING: {
    label: 'En attente',
    color: 'orange',
    description: 'Le paiement est en attente de traitement'
  },
  PROCESSING: {
    label: 'En cours',
    color: 'blue',
    description: 'Le paiement est en cours de traitement'
  },
  COMPLETED: {
    label: 'Complete',
    color: 'green',
    description: 'Le paiement a ete effectue avec succes'
  },
  FAILED: {
    label: 'Echoue',
    color: 'red',
    description: 'Le paiement a echoue'
  },
  REFUNDED: {
    label: 'Rembourse',
    color: 'gray',
    description: 'Le paiement a ete rembourse'
  },
  CANCELLED: {
    label: 'Annule',
    color: 'red',
    description: 'Le paiement a ete annule'
  }
};

export const REFUND_STATUS_CONFIG: Record<RefundStatus, {
  label: string;
  color: 'green' | 'orange' | 'red' | 'blue' | 'gray';
  description: string;
}> = {
  PENDING: {
    label: 'En attente',
    color: 'orange',
    description: 'Le remboursement est en attente'
  },
  PROCESSING: {
    label: 'En cours',
    color: 'blue',
    description: 'Le remboursement est en cours de traitement'
  },
  COMPLETED: {
    label: 'Effectue',
    color: 'green',
    description: 'Le remboursement a ete effectue'
  },
  FAILED: {
    label: 'Echoue',
    color: 'red',
    description: 'Le remboursement a echoue'
  }
};

export const METHOD_CONFIG: Record<PaymentMethod, {
  label: string;
  icon: string;
  color: string;
}> = {
  CARD: { label: 'Carte bancaire', icon: '💳', color: 'blue' },
  BANK_TRANSFER: { label: 'Virement', icon: '🏦', color: 'green' },
  TAP_TO_PAY: { label: 'Tap-to-Pay', icon: '📱', color: 'purple' },
  CASH: { label: 'Especes', icon: '💵', color: 'green' },
  CHECK: { label: 'Cheque', icon: '📄', color: 'gray' },
  OTHER: { label: 'Autre', icon: '💰', color: 'gray' }
};

export const SAVED_METHOD_TYPE_CONFIG: Record<SavedMethodType, {
  label: string;
  icon: string;
}> = {
  CARD: { label: 'Carte', icon: '💳' },
  BANK_ACCOUNT: { label: 'Compte bancaire', icon: '🏦' },
  SEPA: { label: 'SEPA', icon: '🇪🇺' }
};

// ============================================================================
// HELPERS
// ============================================================================

export const getPaymentAge = (payment: Payment): string => {
  const created = new Date(payment.created_at);
  const now = new Date();
  const diffMs = now.getTime() - created.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor(diffMs / (1000 * 60));

  if (diffDays > 0) return `${diffDays}j`;
  if (diffHours > 0) return `${diffHours}h`;
  return `${diffMinutes}min`;
};

export const getPaymentAgeDays = (payment: Payment): number => {
  const created = new Date(payment.created_at);
  const now = new Date();
  return Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24));
};

export const isPaymentPending = (payment: Payment): boolean => {
  return payment.status === 'PENDING' || payment.status === 'PROCESSING';
};

export const isPaymentCompleted = (payment: Payment): boolean => {
  return payment.status === 'COMPLETED';
};

export const isPaymentFailed = (payment: Payment): boolean => {
  return payment.status === 'FAILED' || payment.status === 'CANCELLED';
};

export const canRefund = (payment: Payment): boolean => {
  return payment.status === 'COMPLETED';
};

export const canRetry = (payment: Payment): boolean => {
  return payment.status === 'FAILED';
};

export const getRefundTotal = (payment: Payment): number => {
  if (!payment.refunds) return 0;
  return payment.refunds
    .filter(r => r.status === 'COMPLETED')
    .reduce((sum, r) => sum + r.amount, 0);
};

export const getNetAmount = (payment: Payment): number => {
  const refundTotal = getRefundTotal(payment);
  return payment.amount - refundTotal;
};

export const hasPartialRefund = (payment: Payment): boolean => {
  const refundTotal = getRefundTotal(payment);
  return refundTotal > 0 && refundTotal < payment.amount;
};

export const hasFullRefund = (payment: Payment): boolean => {
  const refundTotal = getRefundTotal(payment);
  return refundTotal >= payment.amount;
};

export const getMethodLabel = (method: PaymentMethod): string => {
  return METHOD_CONFIG[method]?.label || method;
};

export const getMethodIcon = (method: PaymentMethod): string => {
  return METHOD_CONFIG[method]?.icon || '💰';
};

export const getStatusLabel = (status: PaymentStatus): string => {
  return PAYMENT_STATUS_CONFIG[status]?.label || status;
};

export const getStatusColor = (status: PaymentStatus): string => {
  return PAYMENT_STATUS_CONFIG[status]?.color || 'gray';
};
