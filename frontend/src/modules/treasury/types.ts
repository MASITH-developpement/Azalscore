/**
 * AZALSCORE Module - Treasury - Types
 * Types, constantes et helpers pour le module tresorerie
 */

// ============================================================================
// TYPES PRINCIPAUX
// ============================================================================

export interface BankAccount {
  id: string;
  code?: string;
  name: string;
  bank_name: string;
  iban: string;
  bic: string;
  account_number?: string;
  balance: number;
  available_balance?: number;
  currency: string;
  is_default: boolean;
  is_active: boolean;
  account_type?: AccountType;
  opening_date?: string;
  last_sync?: string;
  last_statement_date?: string;
  pending_in?: number;
  pending_out?: number;
  transactions_count?: number;
  unreconciled_count?: number;
  contact_name?: string;
  contact_phone?: string;
  contact_email?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
  transactions?: Transaction[];
  history?: AccountHistoryEntry[];
}

export type AccountType = 'CURRENT' | 'SAVINGS' | 'TERM_DEPOSIT' | 'CREDIT_LINE';

export interface Transaction {
  id: string;
  account_id: string;
  account_name?: string;
  date: string;
  value_date: string;
  description: string;
  reference?: string;
  amount: number;
  currency: string;
  type: TransactionType;
  category?: string;
  reconciled: boolean;
  reconciled_at?: string;
  reconciled_by?: string;
  linked_document?: LinkedDocument;
  bank_reference?: string;
  notes?: string;
  created_at: string;
}

export type TransactionType = 'credit' | 'debit';

export interface LinkedDocument {
  type: string;
  id: string;
  number: string;
}

export interface TreasurySummary {
  total_balance: number;
  total_pending_in: number;
  total_pending_out: number;
  forecast_7d: number;
  forecast_30d: number;
  accounts: BankAccount[];
}

export interface ForecastData {
  date: string;
  projected_balance: number;
  pending_in: number;
  pending_out: number;
}

export interface AccountHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_balance?: number;
  new_balance?: number;
}

// ============================================================================
// CONFIGURATIONS DE STATUT
// ============================================================================

export const ACCOUNT_TYPE_CONFIG: Record<AccountType, { label: string; color: string }> = {
  CURRENT: { label: 'Courant', color: 'blue' },
  SAVINGS: { label: 'Epargne', color: 'green' },
  TERM_DEPOSIT: { label: 'Depot a terme', color: 'purple' },
  CREDIT_LINE: { label: 'Ligne de credit', color: 'orange' }
};

export const ACCOUNT_STATUS_CONFIG = {
  active: { label: 'Actif', color: 'green' },
  inactive: { label: 'Inactif', color: 'gray' }
};

// ============================================================================
// HELPERS METIER
// ============================================================================

export const isAccountActive = (account: BankAccount): boolean => {
  return account.is_active;
};

export const isAccountDefault = (account: BankAccount): boolean => {
  return account.is_default;
};

export const hasLowBalance = (account: BankAccount, threshold = 1000): boolean => {
  return account.balance < threshold;
};

export const hasNegativeBalance = (account: BankAccount): boolean => {
  return account.balance < 0;
};

export const hasUnreconciledTransactions = (account: BankAccount): boolean => {
  return (account.unreconciled_count || 0) > 0;
};

export const getAccountBalance = (account: BankAccount): number => {
  return account.balance;
};

export const getAvailableBalance = (account: BankAccount): number => {
  return account.available_balance ?? account.balance;
};

export const getProjectedBalance = (account: BankAccount): number => {
  const pendingIn = account.pending_in || 0;
  const pendingOut = account.pending_out || 0;
  return account.balance + pendingIn - pendingOut;
};

export const isTransactionReconciled = (transaction: Transaction): boolean => {
  return transaction.reconciled;
};

export const isCredit = (transaction: Transaction): boolean => {
  return transaction.type === 'credit';
};

export const isDebit = (transaction: Transaction): boolean => {
  return transaction.type === 'debit';
};

export const getTransactionAmount = (transaction: Transaction): number => {
  return transaction.type === 'credit' ? transaction.amount : -transaction.amount;
};
