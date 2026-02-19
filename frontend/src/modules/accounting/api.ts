/**
 * AZALSCORE - Accounting API
 * ==========================
 * Complete typed API client for accounting module.
 * Covers: Fiscal Years, Chart of Accounts, Journal Entries, Ledger, Balance
 */

import { api } from '@/core/api-client';

// ============================================================================
// ENUMS
// ============================================================================

export type AccountType =
  | 'ASSET'
  | 'LIABILITY'
  | 'EQUITY'
  | 'INCOME'
  | 'EXPENSE'
  | 'COST_OF_GOODS_SOLD';

export type FiscalYearStatus = 'OPEN' | 'CLOSED' | 'DRAFT';

export type EntryStatus = 'DRAFT' | 'POSTED' | 'VALIDATED' | 'CANCELLED';

// ============================================================================
// FISCAL YEARS
// ============================================================================

export interface FiscalYear {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  start_date: string;
  end_date: string;
  status: FiscalYearStatus;
  closed_at?: string | null;
  closed_by?: string | null;
  is_active: boolean;
  notes?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FiscalYearCreate {
  name: string;
  code: string;
  start_date: string;
  end_date: string;
  notes?: string | null;
}

export interface FiscalYearUpdate {
  name?: string | null;
  notes?: string | null;
}

export interface FiscalYearList {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: FiscalYear[];
}

// ============================================================================
// CHART OF ACCOUNTS
// ============================================================================

export interface Account {
  id: string;
  tenant_id: string;
  account_number: string;
  account_label: string;
  account_type: AccountType;
  account_class: string;
  parent_account?: string | null;
  is_auxiliary: boolean;
  requires_analytics: boolean;
  opening_balance_debit: string;
  opening_balance_credit: string;
  is_active: boolean;
  notes?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AccountCreate {
  account_number: string;
  account_label: string;
  account_type: AccountType;
  parent_account?: string | null;
  is_auxiliary?: boolean;
  requires_analytics?: boolean;
  opening_balance_debit?: string;
  opening_balance_credit?: string;
  notes?: string | null;
}

export interface AccountUpdate {
  account_label?: string | null;
  is_auxiliary?: boolean | null;
  requires_analytics?: boolean | null;
  notes?: string | null;
}

export interface AccountList {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: Account[];
}

// ============================================================================
// JOURNAL ENTRIES
// ============================================================================

export interface JournalEntryLine {
  id: string;
  tenant_id: string;
  entry_id: string;
  line_number: number;
  account_number: string;
  account_label: string;
  label?: string | null;
  debit: string;
  credit: string;
  currency: string;
  analytics_code?: string | null;
  analytics_label?: string | null;
  auxiliary_code?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JournalEntryLineCreate {
  account_number: string;
  account_label: string;
  label?: string | null;
  debit?: string;
  credit?: string;
  analytics_code?: string | null;
  analytics_label?: string | null;
  auxiliary_code?: string | null;
  notes?: string | null;
}

export interface JournalEntry {
  id: string;
  tenant_id: string;
  entry_number: string;
  fiscal_year_id: string;
  period: string;
  piece_number: string;
  journal_code: string;
  journal_label?: string | null;
  entry_date: string;
  label: string;
  document_type?: string | null;
  document_id?: string | null;
  currency: string;
  status: EntryStatus;
  total_debit: string;
  total_credit: string;
  is_balanced: boolean;
  posted_at?: string | null;
  posted_by?: string | null;
  validated_at?: string | null;
  validated_by?: string | null;
  notes?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
  lines: JournalEntryLine[];
}

export interface JournalEntryCreate {
  fiscal_year_id: string;
  piece_number: string;
  journal_code: string;
  journal_label?: string | null;
  entry_date: string;
  label: string;
  document_type?: string | null;
  document_id?: string | null;
  currency?: string;
  notes?: string | null;
  lines: JournalEntryLineCreate[];
}

export interface JournalEntryUpdate {
  piece_number?: string | null;
  journal_label?: string | null;
  entry_date?: string | null;
  label?: string | null;
  notes?: string | null;
  lines?: JournalEntryLineCreate[] | null;
}

export interface JournalEntryList {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: JournalEntry[];
}

// ============================================================================
// LEDGER
// ============================================================================

export interface LedgerAccount {
  account_number: string;
  account_label: string;
  debit_total: string;
  credit_total: string;
  balance: string;
  currency: string;
}

export interface LedgerList {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: LedgerAccount[];
}

// ============================================================================
// BALANCE
// ============================================================================

export interface BalanceEntry {
  account_number: string;
  account_label: string;
  opening_debit: string;
  opening_credit: string;
  period_debit: string;
  period_credit: string;
  closing_debit: string;
  closing_credit: string;
}

export interface BalanceList {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: BalanceEntry[];
}

// ============================================================================
// SUMMARY / STATUS
// ============================================================================

export interface AccountingSummary {
  total_assets: string;
  total_liabilities: string;
  total_equity: string;
  revenue: string;
  expenses: string;
  net_income: string;
  currency: string;
}

export interface AccountingStatus {
  status: string;
  entries_up_to_date: boolean;
  last_closure_date?: string | null;
  pending_entries_count: number;
  days_since_closure?: number | null;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/accounting';

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

export const accountingApi = {
  // ==========================================================================
  // Summary / Dashboard
  // ==========================================================================

  getSummary: (fiscalYearId?: string) =>
    api.get<AccountingSummary>(
      `${BASE_PATH}/summary${buildQueryString({ fiscal_year_id: fiscalYearId })}`
    ),

  getStatus: () =>
    api.get<AccountingStatus>(`${BASE_PATH}/status`),

  // ==========================================================================
  // Fiscal Years
  // ==========================================================================

  createFiscalYear: (data: FiscalYearCreate) =>
    api.post<FiscalYear>(`${BASE_PATH}/fiscal-years`, data),

  listFiscalYears: (params?: {
    status?: FiscalYearStatus;
    page?: number;
    page_size?: number;
  }) =>
    api.get<FiscalYearList>(
      `${BASE_PATH}/fiscal-years${buildQueryString(params || {})}`
    ),

  getFiscalYear: (fiscalYearId: string) =>
    api.get<FiscalYear>(`${BASE_PATH}/fiscal-years/${fiscalYearId}`),

  updateFiscalYear: (fiscalYearId: string, data: FiscalYearUpdate) =>
    api.put<FiscalYear>(`${BASE_PATH}/fiscal-years/${fiscalYearId}`, data),

  closeFiscalYear: (fiscalYearId: string) =>
    api.post<FiscalYear>(`${BASE_PATH}/fiscal-years/${fiscalYearId}/close`, {}),

  // ==========================================================================
  // Chart of Accounts
  // ==========================================================================

  createAccount: (data: AccountCreate) =>
    api.post<Account>(`${BASE_PATH}/chart-of-accounts`, data),

  listAccounts: (params?: {
    type?: AccountType;
    class?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }) =>
    api.get<AccountList>(
      `${BASE_PATH}/chart-of-accounts${buildQueryString(params || {})}`
    ),

  getAccount: (accountNumber: string) =>
    api.get<Account>(`${BASE_PATH}/chart-of-accounts/${accountNumber}`),

  updateAccount: (accountNumber: string, data: AccountUpdate) =>
    api.put<Account>(`${BASE_PATH}/chart-of-accounts/${accountNumber}`, data),

  // ==========================================================================
  // Journal Entries
  // ==========================================================================

  createJournalEntry: (data: JournalEntryCreate) =>
    api.post<JournalEntry>(`${BASE_PATH}/journal`, data),

  listJournalEntries: (params?: {
    fiscal_year_id?: string;
    journal_code?: string;
    status?: EntryStatus;
    period?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }) =>
    api.get<JournalEntryList>(
      `${BASE_PATH}/journal${buildQueryString(params || {})}`
    ),

  getJournalEntry: (entryId: string) =>
    api.get<JournalEntry>(`${BASE_PATH}/journal/${entryId}`),

  updateJournalEntry: (entryId: string, data: JournalEntryUpdate) =>
    api.put<JournalEntry>(`${BASE_PATH}/journal/${entryId}`, data),

  postJournalEntry: (entryId: string) =>
    api.post<JournalEntry>(`${BASE_PATH}/journal/${entryId}/post`, {}),

  validateJournalEntry: (entryId: string) =>
    api.post<JournalEntry>(`${BASE_PATH}/journal/${entryId}/validate`, {}),

  cancelJournalEntry: (entryId: string) =>
    api.post<JournalEntry>(`${BASE_PATH}/journal/${entryId}/cancel`, {}),

  // ==========================================================================
  // Ledger (Grand Livre)
  // ==========================================================================

  getLedger: (params?: {
    fiscal_year_id?: string;
    page?: number;
    page_size?: number;
  }) =>
    api.get<LedgerList>(`${BASE_PATH}/ledger${buildQueryString(params || {})}`),

  getLedgerByAccount: (accountNumber: string, fiscalYearId?: string) =>
    api.get<LedgerList>(
      `${BASE_PATH}/ledger/${accountNumber}${buildQueryString({ fiscal_year_id: fiscalYearId })}`
    ),

  // ==========================================================================
  // Balance
  // ==========================================================================

  getBalance: (params?: {
    fiscal_year_id?: string;
    period?: string;
    page?: number;
    page_size?: number;
  }) =>
    api.get<BalanceList>(`${BASE_PATH}/balance${buildQueryString(params || {})}`),
};

export default accountingApi;
