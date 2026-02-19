/**
 * AZALSCORE - Comptabilite API
 * ============================
 * API client pour le module Comptabilité
 * Couvre: Plan comptable, Journaux, Écritures, Banque
 */

import { api } from '@/core/api-client';
import type { Entry } from './types';

// ============================================================================
// RE-EXPORTS
// ============================================================================

export type { Entry };

// ============================================================================
// TYPES
// ============================================================================

export type AccountType = 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE';
export type JournalType = 'GENERAL' | 'SALES' | 'PURCHASES' | 'CASH' | 'BANK';
export type EntryStatus = 'DRAFT' | 'VALIDATED' | 'POSTED' | 'CANCELLED';

export interface Account {
  id: string;
  code: string;
  name: string;
  type: AccountType;
  parent_id?: string;
  parent_code?: string;
  balance: number;
  is_reconcilable: boolean;
  is_active: boolean;
  created_at: string;
}

export interface Journal {
  id: string;
  code: string;
  name: string;
  type: JournalType;
  default_debit_account_id?: string;
  default_credit_account_id?: string;
  is_active: boolean;
}

export interface EntryLine {
  id: string;
  account_id: string;
  account_code?: string;
  account_name?: string;
  debit: number;
  credit: number;
  label?: string;
  analytic_account_id?: string;
}

export interface EntryFull {
  id: string;
  number: string;
  journal_id: string;
  journal_code?: string;
  journal_name?: string;
  date: string;
  reference?: string;
  description: string;
  status: EntryStatus;
  lines: EntryLine[];
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
  validated_at?: string;
  validated_by?: string;
  posted_at?: string;
  created_at: string;
  created_by?: string;
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
}

export interface BankTransaction {
  id: string;
  bank_account_id: string;
  date: string;
  amount: number;
  type: 'CREDIT' | 'DEBIT';
  reference?: string;
  description?: string;
  is_reconciled: boolean;
  entry_id?: string;
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
}

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface AccountFilters {
  type?: AccountType;
  parent_id?: string;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface EntryFilters {
  journal_id?: string;
  status?: EntryStatus;
  date_from?: string;
  date_to?: string;
  account_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface BankTransactionFilters {
  bank_account_id?: string;
  is_reconciled?: boolean;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface AccountCreate {
  code: string;
  name: string;
  type: AccountType;
  parent_id?: string;
  is_reconcilable?: boolean;
}

export interface EntryLineCreate {
  account_id: string;
  debit?: number;
  credit?: number;
  label?: string;
  analytic_account_id?: string;
}

export interface EntryCreate {
  journal_id: string;
  date: string;
  reference?: string;
  description: string;
  lines: EntryLineCreate[];
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/finance';

function buildQueryString<T extends object>(params: T): string {
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

export const comptabiliteApi = {
  // ==========================================================================
  // Dashboard
  // ==========================================================================

  /**
   * Récupère le tableau de bord financier
   */
  getDashboard: () =>
    api.get<FinanceDashboard>(`${BASE_PATH}/dashboard`),

  // ==========================================================================
  // Accounts (Plan comptable)
  // ==========================================================================

  /**
   * Liste les comptes
   */
  listAccounts: (filters?: AccountFilters) =>
    api.get<PaginatedResponse<Account>>(
      `${BASE_PATH}/accounts${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère un compte par son ID
   */
  getAccount: (id: string) =>
    api.get<Account>(`${BASE_PATH}/accounts/${id}`),

  /**
   * Crée un nouveau compte
   */
  createAccount: (data: AccountCreate) =>
    api.post<Account>(`${BASE_PATH}/accounts`, data),

  /**
   * Met à jour un compte
   */
  updateAccount: (id: string, data: Partial<AccountCreate>) =>
    api.put<Account>(`${BASE_PATH}/accounts/${id}`, data),

  /**
   * Désactive un compte
   */
  deactivateAccount: (id: string) =>
    api.post<Account>(`${BASE_PATH}/accounts/${id}/deactivate`, {}),

  // ==========================================================================
  // Journals
  // ==========================================================================

  /**
   * Liste les journaux
   */
  listJournals: () =>
    api.get<Journal[]>(`${BASE_PATH}/journals`),

  /**
   * Récupère un journal par son ID
   */
  getJournal: (id: string) =>
    api.get<Journal>(`${BASE_PATH}/journals/${id}`),

  // ==========================================================================
  // Entries (Écritures)
  // ==========================================================================

  /**
   * Liste les écritures
   */
  listEntries: (filters?: EntryFilters) =>
    api.get<PaginatedResponse<EntryFull>>(
      `${BASE_PATH}/entries${buildQueryString(filters || {})}`
    ),

  /**
   * Récupère une écriture par son ID
   */
  getEntry: (id: string) =>
    api.get<EntryFull>(`${BASE_PATH}/entries/${id}`),

  /**
   * Crée une nouvelle écriture
   */
  createEntry: (data: EntryCreate) =>
    api.post<EntryFull>(`${BASE_PATH}/entries`, data),

  /**
   * Met à jour une écriture (brouillon uniquement)
   */
  updateEntry: (id: string, data: Partial<EntryCreate>) =>
    api.put<EntryFull>(`${BASE_PATH}/entries/${id}`, data),

  /**
   * Supprime une écriture (brouillon uniquement)
   */
  deleteEntry: (id: string) =>
    api.delete(`${BASE_PATH}/entries/${id}`),

  /**
   * Valide une écriture
   */
  validateEntry: (id: string) =>
    api.post<EntryFull>(`${BASE_PATH}/entries/${id}/validate`, {}),

  /**
   * Comptabilise une écriture
   */
  postEntry: (id: string) =>
    api.post<EntryFull>(`${BASE_PATH}/entries/${id}/post`, {}),

  /**
   * Annule une écriture
   */
  cancelEntry: (id: string) =>
    api.post<EntryFull>(`${BASE_PATH}/entries/${id}/cancel`, {}),

  // ==========================================================================
  // Bank
  // ==========================================================================

  /**
   * Liste les comptes bancaires
   */
  listBankAccounts: () =>
    api.get<BankAccount[]>(`${BASE_PATH}/bank/accounts`),

  /**
   * Récupère un compte bancaire par son ID
   */
  getBankAccount: (id: string) =>
    api.get<BankAccount>(`${BASE_PATH}/bank/accounts/${id}`),

  /**
   * Liste les transactions bancaires
   */
  listBankTransactions: (filters?: BankTransactionFilters) =>
    api.get<PaginatedResponse<BankTransaction>>(
      `${BASE_PATH}/bank/transactions${buildQueryString(filters || {})}`
    ),

  /**
   * Rapproche une transaction bancaire
   */
  reconcileTransaction: (transactionId: string, entryId: string) =>
    api.post<BankTransaction>(`${BASE_PATH}/bank/transactions/${transactionId}/reconcile`, {
      entry_id: entryId,
    }),

  /**
   * Annule le rapprochement d'une transaction
   */
  unreconcileTransaction: (transactionId: string) =>
    api.post<BankTransaction>(`${BASE_PATH}/bank/transactions/${transactionId}/unreconcile`, {}),
};

export default comptabiliteApi;
