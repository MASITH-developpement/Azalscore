/**
 * AZALSCORE Module - Accounting Types
 * Types TypeScript alignes avec le backend Python
 */

// ============================================================================
// ENUMS
// ============================================================================

export type AccountType =
  | 'ASSET'
  | 'LIABILITY'
  | 'EQUITY'
  | 'INCOME'
  | 'EXPENSE';

export type EntryStatus =
  | 'DRAFT'
  | 'VALIDATED'
  | 'POSTED'
  | 'CANCELLED';

export type FiscalYearStatus =
  | 'OPEN'
  | 'CLOSED'
  | 'LOCKED';

export type JournalType =
  | 'GENERAL'
  | 'SALES'
  | 'PURCHASES'
  | 'CASH'
  | 'BANK'
  | 'MISC';

// ============================================================================
// FISCAL YEAR
// ============================================================================

export interface FiscalYear {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  start_date: string;
  end_date: string;
  status: FiscalYearStatus;
  is_active: boolean;
  notes?: string | null;
  closed_at?: string | null;
  closed_by?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FiscalYearCreate {
  name: string;
  code: string;
  start_date: string;
  end_date: string;
  notes?: string;
}

export interface FiscalYearUpdate {
  name?: string;
  notes?: string;
}

// ============================================================================
// CHART OF ACCOUNTS
// ============================================================================

export interface ChartOfAccounts {
  id: string;
  tenant_id: string;
  account_number: string;
  account_label: string;
  account_type: AccountType;
  account_class: string;
  parent_account?: string | null;
  is_auxiliary: boolean;
  requires_analytics: boolean;
  opening_balance_debit: number | string;
  opening_balance_credit: number | string;
  is_active: boolean;
  notes?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChartOfAccountsCreate {
  account_number: string;
  account_label: string;
  account_type: AccountType;
  parent_account?: string;
  is_auxiliary?: boolean;
  requires_analytics?: boolean;
  opening_balance_debit?: number;
  opening_balance_credit?: number;
  notes?: string;
}

export interface ChartOfAccountsUpdate {
  account_label?: string;
  is_auxiliary?: boolean;
  requires_analytics?: boolean;
  notes?: string;
}

// ============================================================================
// JOURNAL
// ============================================================================

export interface Journal {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  journal_type: JournalType;
  default_account?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface JournalCreate {
  code: string;
  name: string;
  journal_type: JournalType;
  default_account?: string;
}

// ============================================================================
// JOURNAL ENTRY
// ============================================================================

export interface JournalEntryLine {
  id: string;
  tenant_id: string;
  entry_id: string;
  line_number: number;
  account_number: string;
  account_label: string;
  label?: string | null;
  debit: number | string;
  credit: number | string;
  currency: string;
  analytics_code?: string | null;
  analytics_label?: string | null;
  auxiliary_code?: string | null;
  notes?: string | null;
}

export interface JournalEntryLineCreate {
  account_number: string;
  account_label: string;
  label?: string;
  debit?: number;
  credit?: number;
  analytics_code?: string;
  analytics_label?: string;
  auxiliary_code?: string;
  notes?: string;
}

export interface JournalEntry {
  id: string;
  tenant_id: string;
  fiscal_year_id: string;
  journal_id: string;
  journal_code: string;
  entry_number: string;
  entry_date: string;
  accounting_date: string;
  reference?: string | null;
  label: string;
  status: EntryStatus;
  total_debit: number | string;
  total_credit: number | string;
  currency: string;
  source_type?: string | null;
  source_id?: string | null;
  lines: JournalEntryLine[];
  is_balanced: boolean;
  validated_at?: string | null;
  validated_by?: string | null;
  posted_at?: string | null;
  posted_by?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JournalEntryCreate {
  fiscal_year_id: string;
  journal_id: string;
  entry_date: string;
  accounting_date?: string;
  reference?: string;
  label: string;
  lines: JournalEntryLineCreate[];
  source_type?: string;
  source_id?: string;
}

export interface JournalEntryUpdate {
  reference?: string;
  label?: string;
  lines?: JournalEntryLineCreate[];
}

// ============================================================================
// ANALYTICS
// ============================================================================

export interface AnalyticsCode {
  id: string;
  tenant_id: string;
  code: string;
  label: string;
  parent_code?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// BALANCES & REPORTS
// ============================================================================

export interface AccountBalance {
  account_number: string;
  account_label: string;
  account_type: AccountType;
  opening_debit: number;
  opening_credit: number;
  period_debit: number;
  period_credit: number;
  closing_debit: number;
  closing_credit: number;
  balance: number;
}

export interface TrialBalance {
  fiscal_year_id: string;
  as_of_date: string;
  accounts: AccountBalance[];
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
}

export interface GeneralLedgerEntry {
  entry_id: string;
  entry_number: string;
  entry_date: string;
  journal_code: string;
  account_number: string;
  label: string;
  debit: number;
  credit: number;
  balance: number;
  reference?: string;
}

export interface GeneralLedger {
  account_number: string;
  account_label: string;
  opening_balance: number;
  entries: GeneralLedgerEntry[];
  closing_balance: number;
}

// ============================================================================
// STATS & DASHBOARD
// ============================================================================

export interface AccountingStats {
  fiscal_year: string;
  total_entries: number;
  draft_entries: number;
  posted_entries: number;
  total_debit: number;
  total_credit: number;
  accounts_count: number;
  journals_count: number;
  last_entry_date?: string;
}

// ============================================================================
// LIST RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export type FiscalYearListResponse = PaginatedResponse<FiscalYear>;
export type ChartOfAccountsListResponse = PaginatedResponse<ChartOfAccounts>;
export type JournalListResponse = PaginatedResponse<Journal>;
export type JournalEntryListResponse = PaginatedResponse<JournalEntry>;

// ============================================================================
// FILTERS
// ============================================================================

export interface JournalEntryFilters {
  fiscal_year_id?: string;
  journal_id?: string;
  status?: EntryStatus;
  from_date?: string;
  to_date?: string;
  account_number?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface ChartOfAccountsFilters {
  account_type?: AccountType;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}
