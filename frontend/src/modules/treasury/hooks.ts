/**
 * AZALSCORE - Treasury Module Hooks
 * ==================================
 * React Query hooks pour la gestion de tresorerie
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { treasuryApi } from './api';
import type {
  BankAccount, BankAccountCreate, BankAccountUpdate,
  BankTransaction, BankTransactionCreate, BankTransactionUpdate,
  TransactionType, ReconciliationRequest,
} from './api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const treasuryKeys = {
  all: ['treasury'] as const,
  summary: () => [...treasuryKeys.all, 'summary'] as const,
  forecast: (days?: number) => [...treasuryKeys.all, 'forecast', days] as const,
  accounts: () => [...treasuryKeys.all, 'accounts'] as const,
  accountsList: (filters?: Record<string, unknown>) => [...treasuryKeys.accounts(), 'list', filters] as const,
  account: (id: string) => [...treasuryKeys.accounts(), id] as const,
  transactions: () => [...treasuryKeys.all, 'transactions'] as const,
  transactionsList: (filters?: Record<string, unknown>) => [...treasuryKeys.transactions(), 'list', filters] as const,
  accountTransactions: (accountId: string, filters?: Record<string, unknown>) => 
    [...treasuryKeys.account(accountId), 'transactions', filters] as const,
  transaction: (id: string) => [...treasuryKeys.transactions(), id] as const,
};

// ============================================================================
// SUMMARY / DASHBOARD HOOKS
// ============================================================================

export function useTreasurySummary() {
  return useQuery({
    queryKey: treasuryKeys.summary(),
    queryFn: async () => {
      const response = await treasuryApi.getSummary();
      return response.data;
    },
  });
}

export function useForecast(days = 30) {
  return useQuery({
    queryKey: treasuryKeys.forecast(days),
    queryFn: async () => {
      const response = await treasuryApi.getForecast(days);
      return response.data;
    },
  });
}

// ============================================================================
// BANK ACCOUNTS HOOKS
// ============================================================================

export function useBankAccounts(params?: {
  is_active?: boolean;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: treasuryKeys.accountsList(params),
    queryFn: async () => {
      const response = await treasuryApi.listAccounts(params);
      return response.data;
    },
  });
}

export function useBankAccount(accountId: string) {
  return useQuery({
    queryKey: treasuryKeys.account(accountId),
    queryFn: async () => {
      const response = await treasuryApi.getAccount(accountId);
      return response.data;
    },
    enabled: !!accountId,
  });
}

export function useCreateBankAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BankAccountCreate) => {
      const response = await treasuryApi.createAccount(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: treasuryKeys.accounts() });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.summary() });
    },
  });
}

export function useUpdateBankAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ accountId, data }: { accountId: string; data: BankAccountUpdate }) => {
      const response = await treasuryApi.updateAccount(accountId, data);
      return response.data;
    },
    onSuccess: (_data, { accountId }) => {
      queryClient.invalidateQueries({ queryKey: treasuryKeys.account(accountId) });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.accounts() });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.summary() });
    },
  });
}

export function useDeleteBankAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (accountId: string) => {
      await treasuryApi.deleteAccount(accountId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: treasuryKeys.accounts() });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.summary() });
    },
  });
}

// ============================================================================
// TRANSACTIONS HOOKS
// ============================================================================

export function useBankTransactions(params?: {
  account_id?: string;
  type?: TransactionType;
  reconciled?: boolean;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: treasuryKeys.transactionsList(params),
    queryFn: async () => {
      const response = await treasuryApi.listTransactions(params);
      return response.data;
    },
  });
}

export function useAccountTransactions(accountId: string, params?: {
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: treasuryKeys.accountTransactions(accountId, params),
    queryFn: async () => {
      const response = await treasuryApi.listAccountTransactions(accountId, params);
      return response.data;
    },
    enabled: !!accountId,
  });
}

export function useBankTransaction(transactionId: string) {
  return useQuery({
    queryKey: treasuryKeys.transaction(transactionId),
    queryFn: async () => {
      const response = await treasuryApi.getTransaction(transactionId);
      return response.data;
    },
    enabled: !!transactionId,
  });
}

export function useCreateBankTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BankTransactionCreate) => {
      const response = await treasuryApi.createTransaction(data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: treasuryKeys.transactions() });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.account(data.account_id) });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.summary() });
    },
  });
}

export function useUpdateBankTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ transactionId, data }: { transactionId: string; data: BankTransactionUpdate }) => {
      const response = await treasuryApi.updateTransaction(transactionId, data);
      return response.data;
    },
    onSuccess: (_data, { transactionId }) => {
      queryClient.invalidateQueries({ queryKey: treasuryKeys.transaction(transactionId) });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.transactions() });
    },
  });
}

// ============================================================================
// RECONCILIATION HOOKS
// ============================================================================

export function useReconcileTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ transactionId, data }: { transactionId: string; data: ReconciliationRequest }) => {
      const response = await treasuryApi.reconcileTransaction(transactionId, data);
      return response.data;
    },
    onSuccess: (_data, { transactionId }) => {
      queryClient.invalidateQueries({ queryKey: treasuryKeys.transaction(transactionId) });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.transactions() });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.summary() });
    },
  });
}

export function useUnreconcileTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (transactionId: string) => {
      const response = await treasuryApi.unreconcileTransaction(transactionId);
      return response.data;
    },
    onSuccess: (_data, transactionId) => {
      queryClient.invalidateQueries({ queryKey: treasuryKeys.transaction(transactionId) });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.transactions() });
      queryClient.invalidateQueries({ queryKey: treasuryKeys.summary() });
    },
  });
}
