/**
 * AZALSCORE Module - POS - Types
 * Types, configurations et helpers pour Point de Vente
 */

// ============================================================================
// TYPES PRINCIPAUX
// ============================================================================

/**
 * Magasin POS
 */
export interface POSStore {
  id: string;
  code: string;
  name: string;
  address?: string;
  city?: string;
  postal_code?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
  manager_id?: string;
  manager_name?: string;
  terminals_count?: number;
  created_at: string;
  updated_at: string;
}

/**
 * Terminal POS
 */
export interface POSTerminal {
  id: string;
  code: string;
  name: string;
  store_id: string;
  store_name?: string;
  status: 'OFFLINE' | 'ONLINE' | 'IN_USE' | 'MAINTENANCE';
  model?: string;
  serial_number?: string;
  last_activity?: string;
  current_session_id?: string;
  ip_address?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Session de caisse
 */
export interface POSSession {
  id: string;
  code: string;
  terminal_id: string;
  terminal_code?: string;
  terminal_name?: string;
  store_id?: string;
  store_code?: string;
  store_name?: string;
  cashier_id: string;
  cashier_name?: string;
  opened_at: string;
  closed_at?: string;
  status: 'OPEN' | 'CLOSED' | 'SUSPENDED';
  opening_balance: number;
  closing_balance?: number;
  expected_balance?: number;
  cash_difference?: number;
  total_sales: number;
  total_returns: number;
  net_sales: number;
  total_transactions: number;
  total_items_sold: number;
  average_basket: number;
  cash_payments: number;
  card_payments: number;
  other_payments: number;
  discounts_given: number;
  notes?: string;
  transactions?: POSTransaction[];
  cash_movements?: CashMovement[];
  history?: SessionHistoryEntry[];
  created_at: string;
  updated_at: string;
}

/**
 * Transaction POS
 */
export interface POSTransaction {
  id: string;
  number: string;
  session_id: string;
  type: 'SALE' | 'RETURN' | 'EXCHANGE' | 'VOID';
  customer_id?: string;
  customer_name?: string;
  customer_email?: string;
  items: POSTransactionItem[];
  subtotal: number;
  discount: number;
  discount_reason?: string;
  tax: number;
  total: number;
  payment_method: 'CASH' | 'CARD' | 'CHECK' | 'VOUCHER' | 'MIXED' | 'CREDIT';
  payments?: PaymentDetail[];
  amount_paid: number;
  change: number;
  status: 'COMPLETED' | 'VOIDED' | 'REFUNDED' | 'PENDING';
  receipt_number?: string;
  cashier_name?: string;
  created_at: string;
}

/**
 * Article d'une transaction
 */
export interface POSTransactionItem {
  id: string;
  product_id: string;
  product_code?: string;
  product_name?: string;
  barcode?: string;
  quantity: number;
  unit_price: number;
  discount: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
}

/**
 * Detail de paiement
 */
export interface PaymentDetail {
  id: string;
  method: 'CASH' | 'CARD' | 'CHECK' | 'VOUCHER' | 'CREDIT';
  amount: number;
  reference?: string;
  card_type?: string;
  card_last_digits?: string;
}

/**
 * Mouvement de caisse
 */
export interface CashMovement {
  id: string;
  session_id: string;
  type: 'DEPOSIT' | 'WITHDRAWAL' | 'ADJUSTMENT';
  amount: number;
  reason: string;
  performed_by?: string;
  performed_at: string;
  approved_by?: string;
}

/**
 * Entree historique session
 */
export interface SessionHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_status?: string;
  new_status?: string;
}

// ============================================================================
// CONFIGURATIONS DE STATUTS
// ============================================================================

export const SESSION_STATUS_CONFIG: Record<POSSession['status'], { label: string; color: string }> = {
  OPEN: { label: 'Ouverte', color: 'green' },
  CLOSED: { label: 'Fermee', color: 'gray' },
  SUSPENDED: { label: 'Suspendue', color: 'orange' }
};

export const TERMINAL_STATUS_CONFIG: Record<POSTerminal['status'], { label: string; color: string }> = {
  OFFLINE: { label: 'Hors ligne', color: 'gray' },
  ONLINE: { label: 'En ligne', color: 'green' },
  IN_USE: { label: 'En cours', color: 'blue' },
  MAINTENANCE: { label: 'Maintenance', color: 'orange' }
};

export const TRANSACTION_TYPE_CONFIG: Record<POSTransaction['type'], { label: string; color: string }> = {
  SALE: { label: 'Vente', color: 'green' },
  RETURN: { label: 'Retour', color: 'red' },
  EXCHANGE: { label: 'Echange', color: 'blue' },
  VOID: { label: 'Annulation', color: 'gray' }
};

export const TRANSACTION_STATUS_CONFIG: Record<POSTransaction['status'], { label: string; color: string }> = {
  COMPLETED: { label: 'Terminee', color: 'green' },
  VOIDED: { label: 'Annulee', color: 'gray' },
  REFUNDED: { label: 'Remboursee', color: 'orange' },
  PENDING: { label: 'En attente', color: 'blue' }
};

export const PAYMENT_METHOD_CONFIG: Record<POSTransaction['payment_method'], { label: string; color: string }> = {
  CASH: { label: 'Especes', color: 'green' },
  CARD: { label: 'Carte', color: 'blue' },
  CHECK: { label: 'Cheque', color: 'purple' },
  VOUCHER: { label: 'Bon', color: 'orange' },
  MIXED: { label: 'Mixte', color: 'cyan' },
  CREDIT: { label: 'Credit', color: 'yellow' }
};

export const CASH_MOVEMENT_TYPE_CONFIG: Record<CashMovement['type'], { label: string; color: string }> = {
  DEPOSIT: { label: 'Depot', color: 'green' },
  WITHDRAWAL: { label: 'Retrait', color: 'red' },
  ADJUSTMENT: { label: 'Ajustement', color: 'blue' }
};

// ============================================================================
// FONCTIONS DE FORMATAGE
// ============================================================================

/**
 * Formater un nombre
 */
export const formatNumber = (value: number): string => {
  return new Intl.NumberFormat('fr-FR').format(value);
};

/**
 * Calculer la duree d'une session
 */
export const formatSessionDuration = (session: POSSession): string => {
  const start = new Date(session.opened_at);
  const end = session.closed_at ? new Date(session.closed_at) : new Date();
  const diffMs = end.getTime() - start.getTime();
  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
  return `${hours}h ${minutes}min`;
};

// ============================================================================
// FONCTIONS METIER
// ============================================================================

/**
 * Verifier si une session est ouverte
 */
export const isSessionOpen = (session: POSSession): boolean => {
  return session.status === 'OPEN';
};

/**
 * Verifier si une session est fermee
 */
export const isSessionClosed = (session: POSSession): boolean => {
  return session.status === 'CLOSED';
};

/**
 * Verifier si une session est suspendue
 */
export const isSessionSuspended = (session: POSSession): boolean => {
  return session.status === 'SUSPENDED';
};

/**
 * Verifier s'il y a un ecart de caisse
 */
export const hasCashDifference = (session: POSSession): boolean => {
  return session.cash_difference !== undefined && session.cash_difference !== 0;
};

/**
 * Verifier si l'ecart est significatif (> 1 EUR)
 */
export const hasSignificantDifference = (session: POSSession): boolean => {
  return session.cash_difference !== undefined && Math.abs(session.cash_difference) > 1;
};

/**
 * Verifier si une session a des transactions
 */
export const hasTransactions = (session: POSSession): boolean => {
  return session.total_transactions > 0;
};

/**
 * Verifier si une session a des retours
 */
export const hasReturns = (session: POSSession): boolean => {
  return session.total_returns > 0;
};

/**
 * Calculer le pourcentage de ventes en especes
 */
export const getCashPaymentPercentage = (session: POSSession): number => {
  if (session.total_sales === 0) return 0;
  return (session.cash_payments / session.total_sales) * 100;
};

/**
 * Calculer le pourcentage de ventes par carte
 */
export const getCardPaymentPercentage = (session: POSSession): number => {
  if (session.total_sales === 0) return 0;
  return (session.card_payments / session.total_sales) * 100;
};

/**
 * Obtenir la couleur du statut de session
 */
export const getSessionStatusColor = (status: POSSession['status']): string => {
  return SESSION_STATUS_CONFIG[status]?.color || 'gray';
};

/**
 * Verifier si une transaction est une vente
 */
export const isSaleTransaction = (transaction: POSTransaction): boolean => {
  return transaction.type === 'SALE';
};

/**
 * Verifier si une transaction est un retour
 */
export const isReturnTransaction = (transaction: POSTransaction): boolean => {
  return transaction.type === 'RETURN';
};

/**
 * Verifier si une transaction est annulee
 */
export const isVoidedTransaction = (transaction: POSTransaction): boolean => {
  return transaction.status === 'VOIDED' || transaction.type === 'VOID';
};

/**
 * Calculer le montant total des articles
 */
export const calculateItemsTotal = (items: POSTransactionItem[]): number => {
  return items.reduce((sum, item) => sum + item.total, 0);
};
