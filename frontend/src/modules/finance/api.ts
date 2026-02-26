/**
 * AZALSCORE - Finance API
 * =======================
 * Complete typed API client for Finance module.
 * Covers: Banking, Reconciliation, Cash Forecast, Virtual Cards, Providers
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const financeKeys = {
  all: ['finance'] as const,
  // Banking
  bankAccounts: () => [...financeKeys.all, 'bank-accounts'] as const,
  bankAccount: (id: string) => [...financeKeys.bankAccounts(), id] as const,
  bankStatements: (accountId: string) => [...financeKeys.all, 'bank-statements', accountId] as const,
  transactions: (accountId: string) => [...financeKeys.all, 'transactions', accountId] as const,
  // Reconciliation
  reconciliation: () => [...financeKeys.all, 'reconciliation'] as const,
  suggestions: (accountId: string) => [...financeKeys.reconciliation(), 'suggestions', accountId] as const,
  // Cash Forecast
  forecast: () => [...financeKeys.all, 'forecast'] as const,
  forecastPeriods: () => [...financeKeys.forecast(), 'periods'] as const,
  // Virtual Cards
  virtualCards: () => [...financeKeys.all, 'virtual-cards'] as const,
  virtualCard: (id: string) => [...financeKeys.virtualCards(), id] as const,
  // Providers
  providers: () => [...financeKeys.all, 'providers'] as const,
  // Dashboard
  dashboard: () => [...financeKeys.all, 'dashboard'] as const,
};

// ============================================================================
// TYPES - BANK ACCOUNTS
// ============================================================================

export interface BankAccount {
  id: string;
  tenant_id: string;
  name: string;
  bank_name: string;
  account_number: string;
  iban?: string | null;
  bic?: string | null;
  currency: string;
  balance: number;
  last_sync_at?: string | null;
  is_active: boolean;
  provider?: string | null;
  provider_account_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BankAccountCreate {
  name: string;
  bank_name: string;
  account_number: string;
  iban?: string | null;
  bic?: string | null;
  currency?: string;
}

export interface BankAccountUpdate {
  name?: string | null;
  bank_name?: string | null;
  is_active?: boolean | null;
}

// ============================================================================
// TYPES - BANK TRANSACTIONS
// ============================================================================

export type TransactionType = 'CREDIT' | 'DEBIT';
export type TransactionStatus = 'PENDING' | 'RECONCILED' | 'IGNORED';

export interface BankTransaction {
  id: string;
  tenant_id: string;
  bank_account_id: string;
  transaction_date: string;
  value_date?: string | null;
  amount: number;
  currency: string;
  description: string;
  reference?: string | null;
  transaction_type: TransactionType;
  status: TransactionStatus;
  category?: string | null;
  reconciled_entry_id?: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - RECONCILIATION
// ============================================================================

export interface ReconciliationSuggestion {
  transaction_id: string;
  entry_id: string;
  confidence: number;
  match_type: 'exact' | 'fuzzy' | 'partial';
  amount_match: boolean;
  date_match: boolean;
  description_similarity: number;
}

export interface ReconciliationResult {
  reconciled_count: number;
  total_amount: number;
  entries: string[];
}

// ============================================================================
// TYPES - CASH FORECAST
// ============================================================================

export interface CashForecastEntry {
  id: string;
  date: string;
  amount: number;
  type: 'INFLOW' | 'OUTFLOW';
  category: string;
  description: string;
  probability: number;
  is_recurring: boolean;
}

export interface CashForecastPeriod {
  start_date: string;
  end_date: string;
  opening_balance: number;
  closing_balance: number;
  total_inflows: number;
  total_outflows: number;
  entries: CashForecastEntry[];
}

export interface CashForecastAlert {
  id: string;
  alert_type: 'LOW_BALANCE' | 'NEGATIVE_BALANCE' | 'LARGE_OUTFLOW';
  threshold: number;
  current_value: number;
  date: string;
  message: string;
}

// ============================================================================
// TYPES - VIRTUAL CARDS
// ============================================================================

export type CardStatus = 'ACTIVE' | 'BLOCKED' | 'EXPIRED' | 'CANCELLED';

export interface VirtualCard {
  id: string;
  tenant_id: string;
  name: string;
  card_number_last4: string;
  expiry_month: number;
  expiry_year: number;
  status: CardStatus;
  spending_limit: number;
  spent_amount: number;
  currency: string;
  assigned_to?: string | null;
  department?: string | null;
  created_at: string;
  updated_at: string;
}

export interface VirtualCardCreate {
  name: string;
  spending_limit: number;
  currency?: string;
  assigned_to?: string | null;
  department?: string | null;
}

// ============================================================================
// TYPES - PROVIDERS
// ============================================================================

export type ProviderType = 'SWAN' | 'NMI' | 'DEFACTO' | 'SOLARIS';

export interface ProviderConfig {
  id: string;
  tenant_id: string;
  provider_type: ProviderType;
  is_active: boolean;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - DASHBOARD
// ============================================================================

export interface FinanceDashboard {
  total_balance: number;
  accounts_count: number;
  pending_reconciliations: number;
  forecast_30_days: number;
  active_cards: number;
  recent_transactions: BankTransaction[];
  alerts: CashForecastAlert[];
}

// ============================================================================
// HOOKS - BANK ACCOUNTS
// ============================================================================

export function useBankAccounts() {
  return useQuery({
    queryKey: financeKeys.bankAccounts(),
    queryFn: async () => {
      const response = await api.get<{ items: BankAccount[]; total: number }>('/finance/bank-accounts');
      return response;
    },
  });
}

export function useBankAccount(id: string) {
  return useQuery({
    queryKey: financeKeys.bankAccount(id),
    queryFn: async () => {
      const response = await api.get<BankAccount>(`/finance/bank-accounts/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateBankAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BankAccountCreate) => {
      return api.post<BankAccount>('/finance/bank-accounts', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.bankAccounts() });
    },
  });
}

export function useUpdateBankAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: BankAccountUpdate }) => {
      return api.put<BankAccount>(`/finance/bank-accounts/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.bankAccounts() });
    },
  });
}

// ============================================================================
// HOOKS - TRANSACTIONS
// ============================================================================

export function useBankTransactions(accountId: string, filters?: {
  status?: TransactionStatus;
  from_date?: string;
  to_date?: string;
}) {
  return useQuery({
    queryKey: financeKeys.transactions(accountId),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      const queryString = params.toString();
      const url = `/finance/bank-accounts/${accountId}/transactions${queryString ? `?${queryString}` : ''}`;
      const response = await api.get<{ items: BankTransaction[]; total: number }>(url);
      return response;
    },
    enabled: !!accountId,
  });
}

// ============================================================================
// HOOKS - RECONCILIATION
// ============================================================================

export function useReconciliationSuggestions(accountId: string) {
  return useQuery({
    queryKey: financeKeys.suggestions(accountId),
    queryFn: async () => {
      const response = await api.get<{ suggestions: ReconciliationSuggestion[] }>(
        `/finance/reconciliation/${accountId}/suggestions`
      );
      return response;
    },
    enabled: !!accountId,
  });
}

export function useAutoReconcile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ accountId, minConfidence }: { accountId: string; minConfidence?: number }) => {
      return api.post<ReconciliationResult>(`/finance/reconciliation/${accountId}/auto`, {
        min_confidence: minConfidence ?? 0.9,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.reconciliation() });
      queryClient.invalidateQueries({ queryKey: financeKeys.bankAccounts() });
    },
  });
}

export function useManualReconcile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ transactionId, entryId }: { transactionId: string; entryId: string }) => {
      return api.post('/finance/reconciliation/manual', {
        transaction_id: transactionId,
        entry_id: entryId,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.reconciliation() });
    },
  });
}

// ============================================================================
// HOOKS - CASH FORECAST
// ============================================================================

export function useCashForecast(days: number = 30) {
  return useQuery({
    queryKey: [...financeKeys.forecast(), days],
    queryFn: async () => {
      const response = await api.get<CashForecastPeriod>(`/finance/cash-forecast?days=${days}`);
      return response;
    },
  });
}

export function useCashForecastAlerts() {
  return useQuery({
    queryKey: [...financeKeys.forecast(), 'alerts'],
    queryFn: async () => {
      const response = await api.get<{ alerts: CashForecastAlert[] }>('/finance/cash-forecast/alerts');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - VIRTUAL CARDS
// ============================================================================

export function useVirtualCards() {
  return useQuery({
    queryKey: financeKeys.virtualCards(),
    queryFn: async () => {
      const response = await api.get<{ items: VirtualCard[]; total: number }>('/finance/virtual-cards');
      return response;
    },
  });
}

export function useVirtualCard(id: string) {
  return useQuery({
    queryKey: financeKeys.virtualCard(id),
    queryFn: async () => {
      const response = await api.get<VirtualCard>(`/finance/virtual-cards/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateVirtualCard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: VirtualCardCreate) => {
      return api.post<VirtualCard>('/finance/virtual-cards', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.virtualCards() });
    },
  });
}

export function useBlockVirtualCard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      return api.post(`/finance/virtual-cards/${id}/block`, { reason });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.virtualCards() });
    },
  });
}

// ============================================================================
// HOOKS - PROVIDERS
// ============================================================================

export function useFinanceProviders() {
  return useQuery({
    queryKey: financeKeys.providers(),
    queryFn: async () => {
      const response = await api.get<{ providers: ProviderConfig[] }>('/finance/providers');
      return response;
    },
  });
}

export function useProviderStatus(providerType: ProviderType) {
  return useQuery({
    queryKey: [...financeKeys.providers(), providerType, 'status'],
    queryFn: async () => {
      const response = await api.get<{ status: string; last_sync: string }>(
        `/finance/providers/${providerType.toLowerCase()}/status`
      );
      return response;
    },
  });
}

// ============================================================================
// HOOKS - DASHBOARD
// ============================================================================

export function useFinanceDashboard() {
  return useQuery({
    queryKey: financeKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<FinanceDashboard>('/finance/suite/dashboard');
      return response;
    },
  });
}

// ============================================================================
// HOOKS - CURRENCY
// ============================================================================

export function useExchangeRates(baseCurrency: string = 'EUR') {
  return useQuery({
    queryKey: [...financeKeys.all, 'exchange-rates', baseCurrency],
    queryFn: async () => {
      const response = await api.get<{ rates: Record<string, number>; base: string; date: string }>(
        `/finance/currency/rates?base=${baseCurrency}`
      );
      return response;
    },
  });
}

export function useConvertCurrency() {
  return useMutation({
    mutationFn: async ({ amount, from, to }: { amount: number; from: string; to: string }) => {
      const response = await api.post<{ converted_amount: number; rate: number }>(
        '/finance/currency/convert',
        { amount, from_currency: from, to_currency: to }
      );
      return response;
    },
  });
}

// ============================================================================
// HOOKS - DUNNING (Relances)
// ============================================================================

export function useDunningCampaigns() {
  return useQuery({
    queryKey: [...financeKeys.all, 'dunning', 'campaigns'],
    queryFn: async () => {
      const response = await api.get<{ items: unknown[]; total: number }>('/finance/dunning/campaigns');
      return response;
    },
  });
}

export function useOverdueInvoices() {
  return useQuery({
    queryKey: [...financeKeys.all, 'dunning', 'overdue'],
    queryFn: async () => {
      const response = await api.get<{ invoices: unknown[]; total_amount: number }>(
        '/finance/dunning/overdue'
      );
      return response;
    },
  });
}

// ============================================================================
// HOOKS - OCR
// ============================================================================

export function useExtractInvoice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post('/finance/invoice-ocr/extract', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: financeKeys.all });
    },
  });
}
