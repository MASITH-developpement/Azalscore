/**
 * AZALSCORE Module - Comptabilite Types
 * Types, constantes et utilitaires pour la comptabilite
 */

// ============================================================================
// TYPES
// ============================================================================

export type AccountType = 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE';
export type JournalType = 'GENERAL' | 'SALES' | 'PURCHASES' | 'CASH' | 'BANK';
export type EntryStatus = 'DRAFT' | 'VALIDATED' | 'POSTED' | 'CANCELLED';
export type TransactionType = 'CREDIT' | 'DEBIT';
export type ForecastType = 'INCOME' | 'EXPENSE';

export interface Account {
  id: string;
  code: string;
  name: string;
  type: AccountType;
  parent_id?: string;
  parent_code?: string;
  parent_name?: string;
  balance: number;
  debit_total?: number;
  credit_total?: number;
  is_active: boolean;
  description?: string;
  created_at: string;
  updated_at?: string;
}

export interface Journal {
  id: string;
  code: string;
  name: string;
  type: JournalType;
  default_debit_account_id?: string;
  default_credit_account_id?: string;
  default_debit_account_code?: string;
  default_credit_account_code?: string;
  is_active: boolean;
  description?: string;
  entry_count?: number;
  created_at: string;
}

export interface EntryLine {
  id: string;
  entry_id?: string;
  account_id: string;
  account_code?: string;
  account_name?: string;
  debit: number;
  credit: number;
  label?: string;
  reference?: string;
  cost_center?: string;
  analytic_account?: string;
}

export interface Entry {
  id: string;
  number: string;
  journal_id: string;
  journal_code?: string;
  journal_name?: string;
  date: string;
  period?: string;
  fiscal_year?: string;
  reference?: string;
  description: string;
  status: EntryStatus;
  lines: EntryLine[];
  total_debit: number;
  total_credit: number;
  is_balanced?: boolean;
  source_document_id?: string;
  source_document_type?: string;
  source_document_number?: string;
  validated_by?: string;
  validated_by_name?: string;
  validated_at?: string;
  posted_by?: string;
  posted_by_name?: string;
  posted_at?: string;
  cancelled_by?: string;
  cancelled_reason?: string;
  cancelled_at?: string;
  created_by?: string;
  created_by_name?: string;
  created_at: string;
  updated_at?: string;
  // Computed
  history?: EntryHistoryEntry[];
  related_entries?: RelatedEntry[];
}

export interface EntryHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

export interface RelatedEntry {
  id: string;
  number: string;
  date: string;
  description: string;
  total_debit: number;
  relation: 'reversal' | 'adjustment' | 'linked';
}

export interface BankAccount {
  id: string;
  name: string;
  bank_name: string;
  iban?: string;
  bic?: string;
  account_id?: string;
  account_code?: string;
  balance: number;
  is_active: boolean;
  currency?: string;
  created_at: string;
}

export interface BankTransaction {
  id: string;
  bank_account_id: string;
  bank_account_name?: string;
  date: string;
  value_date?: string;
  amount: number;
  type: TransactionType;
  reference?: string;
  description?: string;
  counterparty?: string;
  is_reconciled: boolean;
  reconciled_at?: string;
  entry_id?: string;
  entry_number?: string;
  created_at: string;
}

export interface CashForecast {
  id: string;
  date: string;
  type: ForecastType;
  amount: number;
  description: string;
  category?: string;
  is_realized: boolean;
  realized_at?: string;
  realized_amount?: number;
  source_document_id?: string;
  source_document_type?: string;
  created_at: string;
}

export interface FinanceDashboard {
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
  total_revenue: number;
  total_expenses: number;
  net_income: number;
  bank_balance: number;
  pending_entries: number;
  draft_entries?: number;
  validated_entries?: number;
  unreconciled_transactions?: number;
}

// ============================================================================
// CONSTANTS
// ============================================================================

export const ACCOUNT_TYPE_CONFIG: Record<AccountType, {
  label: string;
  color: 'blue' | 'red' | 'purple' | 'green' | 'orange';
  description: string;
  normalBalance: 'debit' | 'credit';
}> = {
  ASSET: {
    label: 'Actif',
    color: 'blue',
    description: 'Biens et creances de l\'entreprise',
    normalBalance: 'debit'
  },
  LIABILITY: {
    label: 'Passif',
    color: 'red',
    description: 'Dettes et obligations',
    normalBalance: 'credit'
  },
  EQUITY: {
    label: 'Capitaux propres',
    color: 'purple',
    description: 'Fonds propres et reserves',
    normalBalance: 'credit'
  },
  REVENUE: {
    label: 'Produits',
    color: 'green',
    description: 'Revenus et recettes',
    normalBalance: 'credit'
  },
  EXPENSE: {
    label: 'Charges',
    color: 'orange',
    description: 'Depenses et couts',
    normalBalance: 'debit'
  }
};

export const JOURNAL_TYPE_CONFIG: Record<JournalType, {
  label: string;
  color: 'blue' | 'green' | 'orange' | 'purple' | 'gray';
  description: string;
}> = {
  GENERAL: {
    label: 'General',
    color: 'gray',
    description: 'Journal des operations diverses'
  },
  SALES: {
    label: 'Ventes',
    color: 'green',
    description: 'Journal des ventes et factures clients'
  },
  PURCHASES: {
    label: 'Achats',
    color: 'orange',
    description: 'Journal des achats et factures fournisseurs'
  },
  CASH: {
    label: 'Caisse',
    color: 'purple',
    description: 'Journal des operations de caisse'
  },
  BANK: {
    label: 'Banque',
    color: 'blue',
    description: 'Journal des operations bancaires'
  }
};

export const ENTRY_STATUS_CONFIG: Record<EntryStatus, {
  label: string;
  color: 'gray' | 'blue' | 'green' | 'red';
  description: string;
}> = {
  DRAFT: {
    label: 'Brouillon',
    color: 'gray',
    description: 'Ecriture en cours de saisie'
  },
  VALIDATED: {
    label: 'Valide',
    color: 'blue',
    description: 'Ecriture validee, prete a comptabiliser'
  },
  POSTED: {
    label: 'Comptabilise',
    color: 'green',
    description: 'Ecriture definitivement enregistree'
  },
  CANCELLED: {
    label: 'Annule',
    color: 'red',
    description: 'Ecriture annulee'
  }
};

export const TRANSACTION_TYPE_CONFIG: Record<TransactionType, {
  label: string;
  color: 'green' | 'red';
}> = {
  CREDIT: { label: 'Credit', color: 'green' },
  DEBIT: { label: 'Debit', color: 'red' }
};

export const FORECAST_TYPE_CONFIG: Record<ForecastType, {
  label: string;
  color: 'green' | 'red';
}> = {
  INCOME: { label: 'Encaissement', color: 'green' },
  EXPENSE: { label: 'Decaissement', color: 'red' }
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export function formatCurrency(amount: number, currency = 'EUR'): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency
  }).format(amount);
}

export function formatDate(dateStr: string): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('fr-FR');
}

export function formatDateTime(dateStr: string): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('fr-FR', {
    dateStyle: 'short',
    timeStyle: 'short'
  });
}

export function formatAccountCode(code: string): string {
  // Format: XXX.XXX.XXX
  if (!code) return '-';
  const parts = code.match(/.{1,3}/g);
  return parts ? parts.join('.') : code;
}

export function getAccountTypeLabel(type: AccountType): string {
  return ACCOUNT_TYPE_CONFIG[type]?.label || type;
}

export function getAccountTypeColor(type: AccountType): string {
  return ACCOUNT_TYPE_CONFIG[type]?.color || 'gray';
}

export function getJournalTypeLabel(type: JournalType): string {
  return JOURNAL_TYPE_CONFIG[type]?.label || type;
}

export function getJournalTypeColor(type: JournalType): string {
  return JOURNAL_TYPE_CONFIG[type]?.color || 'gray';
}

export function getEntryStatusLabel(status: EntryStatus): string {
  return ENTRY_STATUS_CONFIG[status]?.label || status;
}

export function getEntryStatusColor(status: EntryStatus): string {
  return ENTRY_STATUS_CONFIG[status]?.color || 'gray';
}

export function isEntryBalanced(entry: Entry): boolean {
  if (entry.is_balanced !== undefined) return entry.is_balanced;
  return Math.abs(entry.total_debit - entry.total_credit) < 0.01;
}

export function canEditEntry(entry: Entry): boolean {
  return entry.status === 'DRAFT';
}

export function canValidateEntry(entry: Entry): boolean {
  return entry.status === 'DRAFT' && isEntryBalanced(entry) && entry.lines.length > 0;
}

export function canPostEntry(entry: Entry): boolean {
  return entry.status === 'VALIDATED';
}

export function canCancelEntry(entry: Entry): boolean {
  return entry.status !== 'CANCELLED';
}

export function calculateLineTotals(lines: EntryLine[]): { debit: number; credit: number } {
  return lines.reduce(
    (acc, line) => ({
      debit: acc.debit + (line.debit || 0),
      credit: acc.credit + (line.credit || 0)
    }),
    { debit: 0, credit: 0 }
  );
}

export function getEntryAgeDays(entry: Entry): number {
  const created = new Date(entry.created_at);
  const now = new Date();
  return Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24));
}
