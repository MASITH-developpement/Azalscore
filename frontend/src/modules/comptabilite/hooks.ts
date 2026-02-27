/**
 * AZALSCORE Module - Comptabilite - React Query Hooks
 * Hooks pour la gestion comptable et financiere
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import type {
  Account, Journal, Entry, BankAccount, BankTransaction,
  CashForecast, FinanceDashboard
} from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const financeKeys = {
  all: ['finance'] as const,

  // Dashboard
  dashboard: () => [...financeKeys.all, 'dashboard'] as const,

  // Accounts
  accounts: () => [...financeKeys.all, 'accounts'] as const,
  accountDetail: (id: string) => [...financeKeys.accounts(), id] as const,

  // Journals
  journals: () => [...financeKeys.all, 'journals'] as const,
  journalDetail: (id: string) => [...financeKeys.journals(), id] as const,

  // Entries
  entries: () => [...financeKeys.all, 'entries'] as const,
  entriesList: (params?: { journal_id?: string; status?: string }) =>
    [...financeKeys.entries(), params] as const,
  entryDetail: (id: string) => [...financeKeys.entries(), id] as const,

  // Bank
  bankAccounts: () => [...financeKeys.all, 'bank-accounts'] as const,
  bankTransactions: (bankAccountId?: string) =>
    [...financeKeys.all, 'bank-transactions', bankAccountId] as const,

  // Cash forecasts
  cashForecasts: () => [...financeKeys.all, 'cash-forecasts'] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export const useFinanceDashboard = () => {
  return useQuery({
    queryKey: financeKeys.dashboard(),
    queryFn: async () => {
      return api.get<FinanceDashboard>('/finance/dashboard').then(r => r.data);
    }
  });
};

// ============================================================================
// ACCOUNT HOOKS
// ============================================================================

export const useAccounts = () => {
  return useQuery({
    queryKey: financeKeys.accounts(),
    queryFn: async () => {
      const response = await api.get<Account[] | { items: Account[] }>('/finance/accounts').then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

export const useAccount = (id: string) => {
  return useQuery({
    queryKey: financeKeys.accountDetail(id),
    queryFn: async () => {
      return api.get<Account>(`/finance/accounts/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreateAccount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Account>) => {
      return api.post('/finance/accounts', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: financeKeys.accounts() })
  });
};

export const useUpdateAccount = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Account> }) => {
      return api.put(`/finance/accounts/${id}`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: financeKeys.accounts() })
  });
};

// ============================================================================
// JOURNAL HOOKS
// ============================================================================

export const useJournals = () => {
  return useQuery({
    queryKey: financeKeys.journals(),
    queryFn: async () => {
      const response = await api.get<Journal[] | { items: Journal[] }>('/finance/journals').then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

export const useJournal = (id: string) => {
  return useQuery({
    queryKey: financeKeys.journalDetail(id),
    queryFn: async () => {
      return api.get<Journal>(`/finance/journals/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreateJournal = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Journal>) => {
      return api.post('/finance/journals', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: financeKeys.journals() })
  });
};

// ============================================================================
// ENTRY HOOKS
// ============================================================================

export const useEntries = (params?: { journal_id?: string; status?: string }) => {
  return useQuery({
    queryKey: financeKeys.entriesList(params),
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      if (params?.journal_id) queryParams.append('journal_id', params.journal_id);
      if (params?.status) queryParams.append('status', params.status);
      const queryString = queryParams.toString();
      const url = queryString ? `/finance/entries?${queryString}` : '/finance/entries';
      const response = await api.get<Entry[] | { items: Entry[] }>(url).then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

export const useEntry = (id: string) => {
  return useQuery({
    queryKey: financeKeys.entryDetail(id),
    queryFn: async () => {
      return api.get<Entry>(`/finance/entries/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

export const useCreateEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Entry>) => {
      return api.post('/finance/entries', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: financeKeys.entries() })
  });
};

export const useUpdateEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Entry> }) => {
      return api.put(`/finance/entries/${id}`, data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: financeKeys.entries() })
  });
};

export const useValidateEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/finance/entries/${id}/validate`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: financeKeys.entries() })
  });
};

export const usePostEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/finance/entries/${id}/post`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: financeKeys.all })
  });
};

export const useCancelEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      return api.post(`/finance/entries/${id}/cancel`, { reason }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: financeKeys.entries() })
  });
};

// ============================================================================
// BANK HOOKS
// ============================================================================

export const useBankAccounts = () => {
  return useQuery({
    queryKey: financeKeys.bankAccounts(),
    queryFn: async () => {
      const response = await api.get<BankAccount[] | { items: BankAccount[] }>('/finance/bank-accounts').then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

export const useBankTransactions = (bankAccountId?: string) => {
  return useQuery({
    queryKey: financeKeys.bankTransactions(bankAccountId),
    queryFn: async () => {
      const url = bankAccountId
        ? `/finance/bank-transactions?bank_account_id=${encodeURIComponent(bankAccountId)}`
        : '/finance/bank-transactions';
      const response = await api.get<BankTransaction[] | { items: BankTransaction[] }>(url).then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    },
    enabled: !!bankAccountId
  });
};

export const useReconcileTransaction = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, entryId }: { id: string; entryId: string }) => {
      return api.post(`/finance/bank-transactions/${id}/reconcile`, { entry_id: entryId }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.bankAccounts() });
      queryClient.invalidateQueries({ queryKey: ['finance', 'bank-transactions'] });
    }
  });
};

// ============================================================================
// CASH FORECAST HOOKS
// ============================================================================

export const useCashForecasts = () => {
  return useQuery({
    queryKey: financeKeys.cashForecasts(),
    queryFn: async () => {
      const response = await api.get<CashForecast[] | { items: CashForecast[] }>('/finance/cash-forecasts').then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

export const useCreateCashForecast = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<CashForecast>) => {
      return api.post('/finance/cash-forecasts', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: financeKeys.cashForecasts() })
  });
};
