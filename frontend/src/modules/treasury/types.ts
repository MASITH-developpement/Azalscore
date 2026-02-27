/**
 * AZALSCORE Module - Treasury - Types
 * Types, constantes et helpers pour le module tresorerie
 */

// ============================================================================
// TYPES PRINCIPAUX (alignes avec l'API)
// ============================================================================

export type AccountType = 'CURRENT' | 'SAVINGS' | 'DEPOSIT' | 'CREDIT' | 'CASH' | 'TERM_DEPOSIT' | 'CREDIT_LINE';

export type TransactionType = 'CREDIT' | 'DEBIT' | 'credit' | 'debit';

export interface BankAccount {
  id: string;
  tenant_id?: string;
  code?: string | null;
  name: string;
  bank_name: string;
  iban: string;
  bic?: string | null;
  account_number?: string | null;
  account_type?: AccountType;
  is_default: boolean;
  is_active: boolean;
  balance: string | number;
  available_balance?: string | number | null;
  pending_in?: string | number;
  pending_out?: string | number;
  currency: string;
  opening_date?: string | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  last_sync?: string | null;
  last_statement_date?: string | null;
  transactions_count?: number | null;
  unreconciled_count?: number | null;
  notes?: string | null;
  created_by?: string | null;
  created_by_name?: string | null;
  created_at: string;
  updated_at: string;
  transactions?: Transaction[];
  history?: AccountHistoryEntry[];
}

export interface Transaction {
  id: string;
  tenant_id?: string;
  account_id: string;
  account_name?: string | null;
  date: string;
  value_date: string;
  description: string;
  reference?: string | null;
  bank_reference?: string | null;
  amount: string | number;
  currency: string;
  type: TransactionType;
  category?: string | null;
  reconciled: boolean;
  reconciled_at?: string | null;
  reconciled_by?: string | null;
  linked_document?: LinkedDocument | Record<string, unknown> | null;
  notes?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface LinkedDocument {
  type: string;
  id: string;
  number: string;
}

export interface TreasurySummary {
  total_balance: string | number;
  total_pending_in: string | number;
  total_pending_out: string | number;
  forecast_7d: string | number;
  forecast_30d: string | number;
  accounts: BankAccount[];
}

export interface ForecastData {
  date: string;
  projected_balance: string | number;
  pending_in: string | number;
  pending_out: string | number;
}

export interface AccountHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string | null;
  details?: string | null;
  old_balance?: string | number | null;
  new_balance?: string | number | null;
}

// ============================================================================
// CONFIGURATIONS DE STATUT
// ============================================================================

export const ACCOUNT_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  CURRENT: { label: 'Courant', color: 'blue' },
  SAVINGS: { label: 'Epargne', color: 'green' },
  DEPOSIT: { label: 'Depot', color: 'green' },
  TERM_DEPOSIT: { label: 'Depot a terme', color: 'purple' },
  CREDIT: { label: 'Credit', color: 'orange' },
  CREDIT_LINE: { label: 'Ligne de credit', color: 'orange' },
  CASH: { label: 'Caisse', color: 'gray' }
};

export const ACCOUNT_STATUS_CONFIG = {
  active: { label: 'Actif', color: 'green' },
  inactive: { label: 'Inactif', color: 'gray' }
};

// ============================================================================
// HELPERS METIER
// ============================================================================

export const toNumber = (value: string | number | null | undefined): number => {
  if (value === null || value === undefined) return 0;
  if (typeof value === 'number') return value;
  const parsed = parseFloat(value);
  return isNaN(parsed) ? 0 : parsed;
};

export const isAccountActive = (account: BankAccount): boolean => {
  return account.is_active;
};

export const isAccountDefault = (account: BankAccount): boolean => {
  return account.is_default;
};

export const hasLowBalance = (account: BankAccount, threshold = 1000): boolean => {
  return toNumber(account.balance) < threshold;
};

export const hasNegativeBalance = (account: BankAccount): boolean => {
  return toNumber(account.balance) < 0;
};

export const hasUnreconciledTransactions = (account: BankAccount): boolean => {
  return (account.unreconciled_count || 0) > 0;
};

export const getAccountBalance = (account: BankAccount): number => {
  return toNumber(account.balance);
};

export const getAvailableBalance = (account: BankAccount): number => {
  return account.available_balance !== null && account.available_balance !== undefined
    ? toNumber(account.available_balance)
    : toNumber(account.balance);
};

export const getProjectedBalance = (account: BankAccount): number => {
  const pendingIn = toNumber(account.pending_in);
  const pendingOut = toNumber(account.pending_out);
  return toNumber(account.balance) + pendingIn - pendingOut;
};

export const isTransactionReconciled = (transaction: Transaction): boolean => {
  return transaction.reconciled;
};

export const isCredit = (transaction: Transaction): boolean => {
  return transaction.type === 'credit' || transaction.type === 'CREDIT';
};

export const isDebit = (transaction: Transaction): boolean => {
  return transaction.type === 'debit' || transaction.type === 'DEBIT';
};

export const getTransactionAmount = (transaction: Transaction): number => {
  const amount = toNumber(transaction.amount);
  return isCredit(transaction) ? amount : -amount;
};
