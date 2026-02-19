/**
 * AZALSCORE - Treasury API
 * ========================
 * Complete typed API client for treasury module.
 * Covers: Bank Accounts, Transactions, Reconciliation, Forecast
 */

import { api } from '@/core/api-client';

// ============================================================================
// ENUMS
// ============================================================================

export type AccountType = 'CURRENT' | 'SAVINGS' | 'DEPOSIT' | 'CREDIT' | 'CASH';

export type TransactionType = 'CREDIT' | 'DEBIT';

// ============================================================================
// BANK ACCOUNTS
// ============================================================================

export interface BankAccount {
  id: string;
  tenant_id: string;
  code?: string | null;
  name: string;
  bank_name: string;
  iban: string;
  bic?: string | null;
  account_number?: string | null;
  account_type: AccountType;
  is_default: boolean;
  is_active: boolean;
  balance: string;
  available_balance?: string | null;
  pending_in: string;
  pending_out: string;
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
  created_at: string;
  updated_at: string;
}

export interface BankAccountCreate {
  code?: string | null;
  name: string;
  bank_name: string;
  iban: string;
  bic?: string | null;
  account_number?: string | null;
  account_type?: AccountType;
  is_default?: boolean;
  balance?: string;
  currency?: string;
  opening_date?: string | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  notes?: string | null;
}

export interface BankAccountUpdate {
  name?: string | null;
  bank_name?: string | null;
  is_default?: boolean | null;
  is_active?: boolean | null;
  contact_name?: string | null;
  contact_phone?: string | null;
  contact_email?: string | null;
  notes?: string | null;
}

export interface BankAccountList {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: BankAccount[];
}

// ============================================================================
// TRANSACTIONS
// ============================================================================

export interface BankTransaction {
  id: string;
  tenant_id: string;
  account_id: string;
  account_name?: string | null;
  date: string;
  value_date: string;
  description: string;
  reference?: string | null;
  bank_reference?: string | null;
  amount: string;
  currency: string;
  type: TransactionType;
  category?: string | null;
  reconciled: boolean;
  reconciled_at?: string | null;
  reconciled_by?: string | null;
  linked_document?: Record<string, unknown> | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BankTransactionCreate {
  account_id: string;
  date: string;
  value_date: string;
  description: string;
  reference?: string | null;
  bank_reference?: string | null;
  amount: string;
  currency?: string;
  type: TransactionType;
  category?: string | null;
  notes?: string | null;
}

export interface BankTransactionUpdate {
  description?: string | null;
  category?: string | null;
  notes?: string | null;
}

export interface BankTransactionList {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: BankTransaction[];
}

// ============================================================================
// RECONCILIATION
// ============================================================================

export interface ReconciliationRequest {
  document_type: string;
  document_id: string;
}

// ============================================================================
// SUMMARY / FORECAST
// ============================================================================

export interface TreasurySummary {
  total_balance: string;
  total_pending_in: string;
  total_pending_out: string;
  forecast_7d: string;
  forecast_30d: string;
  accounts: BankAccount[];
}

export interface ForecastData {
  date: string;
  projected_balance: string;
  pending_in: string;
  pending_out: string;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/treasury';

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

export const treasuryApi = {
  // ==========================================================================
  // Summary / Dashboard
  // ==========================================================================

  getSummary: () =>
    api.get<TreasurySummary>(`${BASE_PATH}/summary`),

  getForecast: (days = 30) =>
    api.get<ForecastData[]>(`${BASE_PATH}/forecast${buildQueryString({ days })}`),

  // ==========================================================================
  // Bank Accounts
  // ==========================================================================

  createAccount: (data: BankAccountCreate) =>
    api.post<BankAccount>(`${BASE_PATH}/accounts`, data),

  listAccounts: (params?: {
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }) =>
    api.get<BankAccountList>(
      `${BASE_PATH}/accounts${buildQueryString(params || {})}`
    ),

  getAccount: (accountId: string) =>
    api.get<BankAccount>(`${BASE_PATH}/accounts/${accountId}`),

  updateAccount: (accountId: string, data: BankAccountUpdate) =>
    api.put<BankAccount>(`${BASE_PATH}/accounts/${accountId}`, data),

  deleteAccount: (accountId: string) =>
    api.delete(`${BASE_PATH}/accounts/${accountId}`),

  // ==========================================================================
  // Transactions
  // ==========================================================================

  createTransaction: (data: BankTransactionCreate) =>
    api.post<BankTransaction>(`${BASE_PATH}/transactions`, data),

  listTransactions: (params?: {
    account_id?: string;
    type?: TransactionType;
    reconciled?: boolean;
    page?: number;
    page_size?: number;
  }) =>
    api.get<BankTransactionList>(
      `${BASE_PATH}/transactions${buildQueryString(params || {})}`
    ),

  listAccountTransactions: (accountId: string, params?: {
    page?: number;
    page_size?: number;
  }) =>
    api.get<BankTransactionList>(
      `${BASE_PATH}/accounts/${accountId}/transactions${buildQueryString(params || {})}`
    ),

  getTransaction: (transactionId: string) =>
    api.get<BankTransaction>(`${BASE_PATH}/transactions/${transactionId}`),

  updateTransaction: (transactionId: string, data: BankTransactionUpdate) =>
    api.put<BankTransaction>(`${BASE_PATH}/transactions/${transactionId}`, data),

  // ==========================================================================
  // Reconciliation
  // ==========================================================================

  reconcileTransaction: (transactionId: string, data: ReconciliationRequest) =>
    api.post<BankTransaction>(
      `${BASE_PATH}/transactions/${transactionId}/reconcile`,
      data
    ),

  unreconcileTransaction: (transactionId: string) =>
    api.post<BankTransaction>(
      `${BASE_PATH}/transactions/${transactionId}/unreconcile`,
      {}
    ),
};

export default treasuryApi;
