/**
 * AZALSCORE - Accounting Module Hooks
 * ====================================
 * React Query hooks pour la comptabilite
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountingApi } from './api';
import type {
  FiscalYear, FiscalYearCreate, FiscalYearUpdate, FiscalYearStatus,
  Account, AccountCreate, AccountUpdate, AccountType,
  JournalEntry, JournalEntryCreate, JournalEntryUpdate, EntryStatus,
} from './api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const accountingKeys = {
  all: ['accounting'] as const,
  summary: (fiscalYearId?: string) => [...accountingKeys.all, 'summary', fiscalYearId] as const,
  status: () => [...accountingKeys.all, 'status'] as const,
  // Fiscal Years
  fiscalYears: () => [...accountingKeys.all, 'fiscal-years'] as const,
  fiscalYearsList: (filters?: Record<string, unknown>) => [...accountingKeys.fiscalYears(), 'list', filters] as const,
  fiscalYear: (id: string) => [...accountingKeys.fiscalYears(), id] as const,
  // Chart of Accounts
  accounts: () => [...accountingKeys.all, 'accounts'] as const,
  accountsList: (filters?: Record<string, unknown>) => [...accountingKeys.accounts(), 'list', filters] as const,
  account: (number: string) => [...accountingKeys.accounts(), number] as const,
  // Journal
  journal: () => [...accountingKeys.all, 'journal'] as const,
  journalList: (filters?: Record<string, unknown>) => [...accountingKeys.journal(), 'list', filters] as const,
  journalEntry: (id: string) => [...accountingKeys.journal(), id] as const,
  // Ledger
  ledger: (filters?: Record<string, unknown>) => [...accountingKeys.all, 'ledger', filters] as const,
  ledgerAccount: (accountNumber: string, fiscalYearId?: string) => 
    [...accountingKeys.all, 'ledger', accountNumber, fiscalYearId] as const,
  // Balance
  balance: (filters?: Record<string, unknown>) => [...accountingKeys.all, 'balance', filters] as const,
};

// ============================================================================
// SUMMARY / STATUS HOOKS
// ============================================================================

export function useAccountingSummary(fiscalYearId?: string) {
  return useQuery({
    queryKey: accountingKeys.summary(fiscalYearId),
    queryFn: async () => {
      const response = await accountingApi.getSummary(fiscalYearId);
      return response.data;
    },
  });
}

export function useAccountingStatus() {
  return useQuery({
    queryKey: accountingKeys.status(),
    queryFn: async () => {
      const response = await accountingApi.getStatus();
      return response.data;
    },
  });
}

// ============================================================================
// FISCAL YEARS HOOKS
// ============================================================================

export function useFiscalYears(params?: {
  status?: FiscalYearStatus;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: accountingKeys.fiscalYearsList(params),
    queryFn: async () => {
      const response = await accountingApi.listFiscalYears(params);
      return response.data;
    },
  });
}

export function useFiscalYear(fiscalYearId: string) {
  return useQuery({
    queryKey: accountingKeys.fiscalYear(fiscalYearId),
    queryFn: async () => {
      const response = await accountingApi.getFiscalYear(fiscalYearId);
      return response.data;
    },
    enabled: !!fiscalYearId,
  });
}

export function useCreateFiscalYear() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: FiscalYearCreate) => {
      const response = await accountingApi.createFiscalYear(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.fiscalYears() });
    },
  });
}

export function useUpdateFiscalYear() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ fiscalYearId, data }: { fiscalYearId: string; data: FiscalYearUpdate }) => {
      const response = await accountingApi.updateFiscalYear(fiscalYearId, data);
      return response.data;
    },
    onSuccess: (_data, { fiscalYearId }) => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.fiscalYear(fiscalYearId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.fiscalYears() });
    },
  });
}

export function useCloseFiscalYear() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (fiscalYearId: string) => {
      const response = await accountingApi.closeFiscalYear(fiscalYearId);
      return response.data;
    },
    onSuccess: (_data, fiscalYearId) => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.fiscalYear(fiscalYearId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.fiscalYears() });
      queryClient.invalidateQueries({ queryKey: accountingKeys.status() });
    },
  });
}

// ============================================================================
// CHART OF ACCOUNTS HOOKS
// ============================================================================

export function useChartOfAccounts(params?: {
  type?: AccountType;
  class?: string;
  search?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: accountingKeys.accountsList(params),
    queryFn: async () => {
      const response = await accountingApi.listAccounts(params);
      return response.data;
    },
  });
}

export function useAccount(accountNumber: string) {
  return useQuery({
    queryKey: accountingKeys.account(accountNumber),
    queryFn: async () => {
      const response = await accountingApi.getAccount(accountNumber);
      return response.data;
    },
    enabled: !!accountNumber,
  });
}

export function useCreateAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: AccountCreate) => {
      const response = await accountingApi.createAccount(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts() });
    },
  });
}

export function useUpdateAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ accountNumber, data }: { accountNumber: string; data: AccountUpdate }) => {
      const response = await accountingApi.updateAccount(accountNumber, data);
      return response.data;
    },
    onSuccess: (_data, { accountNumber }) => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.account(accountNumber) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.accounts() });
    },
  });
}

// ============================================================================
// JOURNAL ENTRIES HOOKS
// ============================================================================

export function useJournalEntries(params?: {
  fiscal_year_id?: string;
  journal_code?: string;
  status?: EntryStatus;
  period?: string;
  search?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: accountingKeys.journalList(params),
    queryFn: async () => {
      const response = await accountingApi.listJournalEntries(params);
      return response.data;
    },
  });
}

export function useJournalEntry(entryId: string) {
  return useQuery({
    queryKey: accountingKeys.journalEntry(entryId),
    queryFn: async () => {
      const response = await accountingApi.getJournalEntry(entryId);
      return response.data;
    },
    enabled: !!entryId,
  });
}

export function useCreateJournalEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: JournalEntryCreate) => {
      const response = await accountingApi.createJournalEntry(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journal() });
      queryClient.invalidateQueries({ queryKey: accountingKeys.summary() });
      queryClient.invalidateQueries({ queryKey: accountingKeys.status() });
    },
  });
}

export function useUpdateJournalEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ entryId, data }: { entryId: string; data: JournalEntryUpdate }) => {
      const response = await accountingApi.updateJournalEntry(entryId, data);
      return response.data;
    },
    onSuccess: (_data, { entryId }) => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntry(entryId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.journal() });
    },
  });
}

export function usePostJournalEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (entryId: string) => {
      const response = await accountingApi.postJournalEntry(entryId);
      return response.data;
    },
    onSuccess: (_data, entryId) => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntry(entryId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.journal() });
      queryClient.invalidateQueries({ queryKey: accountingKeys.status() });
      queryClient.invalidateQueries({ queryKey: accountingKeys.ledger() });
      queryClient.invalidateQueries({ queryKey: accountingKeys.balance() });
    },
  });
}

export function useValidateJournalEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (entryId: string) => {
      const response = await accountingApi.validateJournalEntry(entryId);
      return response.data;
    },
    onSuccess: (_data, entryId) => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntry(entryId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.journal() });
    },
  });
}

export function useCancelJournalEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (entryId: string) => {
      const response = await accountingApi.cancelJournalEntry(entryId);
      return response.data;
    },
    onSuccess: (_data, entryId) => {
      queryClient.invalidateQueries({ queryKey: accountingKeys.journalEntry(entryId) });
      queryClient.invalidateQueries({ queryKey: accountingKeys.journal() });
      queryClient.invalidateQueries({ queryKey: accountingKeys.status() });
      queryClient.invalidateQueries({ queryKey: accountingKeys.summary() });
    },
  });
}

// ============================================================================
// LEDGER HOOKS
// ============================================================================

export function useLedger(params?: {
  fiscal_year_id?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: accountingKeys.ledger(params),
    queryFn: async () => {
      const response = await accountingApi.getLedger(params);
      return response.data;
    },
  });
}

export function useLedgerByAccount(accountNumber: string, fiscalYearId?: string) {
  return useQuery({
    queryKey: accountingKeys.ledgerAccount(accountNumber, fiscalYearId),
    queryFn: async () => {
      const response = await accountingApi.getLedgerByAccount(accountNumber, fiscalYearId);
      return response.data;
    },
    enabled: !!accountNumber,
  });
}

// ============================================================================
// BALANCE HOOKS
// ============================================================================

export function useBalance(params?: {
  fiscal_year_id?: string;
  period?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: accountingKeys.balance(params),
    queryFn: async () => {
      const response = await accountingApi.getBalance(params);
      return response.data;
    },
  });
}
