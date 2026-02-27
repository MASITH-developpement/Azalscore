/**
 * AZALSCORE Module - Automated Accounting (M2A) Hooks
 * React Query hooks pour la comptabilite automatisee
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  dashboardApi,
  documentApi,
  bankConnectionApi,
  bankTransactionApi,
  reconciliationApi,
  alertApi,
  accountingRuleApi,
  emailInboxApi,
  syncLogApi,
} from './api';
import type {
  DocumentUpdate,
  DocumentFilters,
  BankConnectionCreate,
  BankTransactionFilters,
  AlertFilters,
  AlertUpdate,
  AccountingRuleCreate,
  EmailInboxCreate,
  ReconciliationAction,
  DocumentType,
} from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const m2aKeys = {
  all: ['m2a'] as const,

  // Dashboards
  dashboardDirigeant: () => [...m2aKeys.all, 'dashboard', 'dirigeant'] as const,
  dashboardAssistante: () => [...m2aKeys.all, 'dashboard', 'assistante'] as const,
  dashboardExpert: () => [...m2aKeys.all, 'dashboard', 'expert'] as const,
  dashboardGeneral: () => [...m2aKeys.all, 'dashboard', 'general'] as const,

  // Documents
  documents: () => [...m2aKeys.all, 'documents'] as const,
  documentList: (filters?: DocumentFilters) => [...m2aKeys.documents(), 'list', filters] as const,
  documentDetail: (id: string) => [...m2aKeys.documents(), 'detail', id] as const,

  // Bank Connections
  bankConnections: () => [...m2aKeys.all, 'bank-connections'] as const,
  bankConnectionDetail: (id: string) => [...m2aKeys.bankConnections(), 'detail', id] as const,

  // Bank Transactions
  bankTransactions: () => [...m2aKeys.all, 'bank-transactions'] as const,
  bankTransactionList: (filters?: BankTransactionFilters) =>
    [...m2aKeys.bankTransactions(), 'list', filters] as const,
  bankTransactionDetail: (id: string) => [...m2aKeys.bankTransactions(), 'detail', id] as const,

  // Reconciliation
  reconciliationSuggestions: (transactionId?: string) =>
    [...m2aKeys.all, 'reconciliation', 'suggestions', transactionId] as const,

  // Alerts
  alerts: () => [...m2aKeys.all, 'alerts'] as const,
  alertList: (filters?: AlertFilters) => [...m2aKeys.alerts(), 'list', filters] as const,
  alertDetail: (id: string) => [...m2aKeys.alerts(), 'detail', id] as const,

  // Accounting Rules
  rules: () => [...m2aKeys.all, 'rules'] as const,
  ruleDetail: (id: string) => [...m2aKeys.rules(), 'detail', id] as const,

  // Email Inboxes
  emailInboxes: () => [...m2aKeys.all, 'email-inboxes'] as const,
  emailInboxDetail: (id: string) => [...m2aKeys.emailInboxes(), 'detail', id] as const,

  // Sync Logs
  syncLogs: (connectionId?: string) => [...m2aKeys.all, 'sync-logs', connectionId] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export function useDirigeantDashboard(syncBank = true) {
  return useQuery({
    queryKey: m2aKeys.dashboardDirigeant(),
    queryFn: () => dashboardApi.getDirigeant(syncBank),
  });
}

export function useAssistanteDashboard() {
  return useQuery({
    queryKey: m2aKeys.dashboardAssistante(),
    queryFn: () => dashboardApi.getAssistante(),
  });
}

export function useExpertDashboard() {
  return useQuery({
    queryKey: m2aKeys.dashboardExpert(),
    queryFn: () => dashboardApi.getExpert(),
  });
}

export function useM2ADashboard() {
  return useQuery({
    queryKey: m2aKeys.dashboardGeneral(),
    queryFn: () => dashboardApi.getGeneral(),
  });
}

// ============================================================================
// DOCUMENT HOOKS
// ============================================================================

export function useDocumentList(filters?: DocumentFilters) {
  return useQuery({
    queryKey: m2aKeys.documentList(filters),
    queryFn: () => documentApi.list(filters),
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: m2aKeys.documentDetail(id),
    queryFn: () => documentApi.get(id),
    enabled: !!id,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, documentType }: { file: File; documentType?: DocumentType }) =>
      documentApi.upload(file, documentType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.documents() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.dashboardAssistante() });
    },
  });
}

export function useUpdateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DocumentUpdate }) =>
      documentApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.documentDetail(id) });
      queryClient.invalidateQueries({ queryKey: m2aKeys.documents() });
    },
  });
}

export function useValidateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, corrections }: { id: string; corrections?: DocumentUpdate }) =>
      documentApi.validate(id, { corrections }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.documentDetail(id) });
      queryClient.invalidateQueries({ queryKey: m2aKeys.documents() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.dashboardExpert() });
    },
  });
}

export function useRejectDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      documentApi.reject(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.documentDetail(id) });
      queryClient.invalidateQueries({ queryKey: m2aKeys.documents() });
    },
  });
}

export function useReprocessDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentApi.reprocess(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.documentDetail(id) });
      queryClient.invalidateQueries({ queryKey: m2aKeys.documents() });
    },
  });
}

export function useAccountDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentApi.account(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.documentDetail(id) });
      queryClient.invalidateQueries({ queryKey: m2aKeys.documents() });
    },
  });
}

export function useBulkValidateDocuments() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (documentIds: string[]) => documentApi.bulkValidate(documentIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.documents() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.dashboardExpert() });
    },
  });
}

// ============================================================================
// BANK CONNECTION HOOKS
// ============================================================================

export function useBankConnections() {
  return useQuery({
    queryKey: m2aKeys.bankConnections(),
    queryFn: () => bankConnectionApi.list(),
  });
}

export function useBankConnection(id: string) {
  return useQuery({
    queryKey: m2aKeys.bankConnectionDetail(id),
    queryFn: () => bankConnectionApi.get(id),
    enabled: !!id,
  });
}

export function useCreateBankConnection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: BankConnectionCreate) => bankConnectionApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.bankConnections() });
    },
  });
}

export function useDeleteBankConnection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => bankConnectionApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.bankConnections() });
    },
  });
}

export function useSyncBankConnection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => bankConnectionApi.sync(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.bankConnections() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.bankTransactions() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.dashboardDirigeant() });
    },
  });
}

export function useSyncAllBanks() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => bankConnectionApi.syncAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.bankConnections() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.bankTransactions() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.dashboardDirigeant() });
    },
  });
}

// ============================================================================
// BANK TRANSACTION HOOKS
// ============================================================================

export function useBankTransactionList(filters?: BankTransactionFilters) {
  return useQuery({
    queryKey: m2aKeys.bankTransactionList(filters),
    queryFn: () => bankTransactionApi.list(filters),
  });
}

export function useBankTransaction(id: string) {
  return useQuery({
    queryKey: m2aKeys.bankTransactionDetail(id),
    queryFn: () => bankTransactionApi.get(id),
    enabled: !!id,
  });
}

// ============================================================================
// RECONCILIATION HOOKS
// ============================================================================

export function useReconciliationSuggestions(transactionId?: string) {
  return useQuery({
    queryKey: m2aKeys.reconciliationSuggestions(transactionId),
    queryFn: () => reconciliationApi.getSuggestions(transactionId),
  });
}

export function useReconcile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (action: ReconciliationAction) => reconciliationApi.reconcile(action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.bankTransactions() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.reconciliationSuggestions() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.documents() });
    },
  });
}

export function useUnreconcile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (transactionId: string) => reconciliationApi.unreconcile(transactionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.bankTransactions() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.reconciliationSuggestions() });
    },
  });
}

export function useAutoReconcile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => reconciliationApi.autoReconcile(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.bankTransactions() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.reconciliationSuggestions() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.documents() });
    },
  });
}

// ============================================================================
// ALERT HOOKS
// ============================================================================

export function useAlertList(filters?: AlertFilters) {
  return useQuery({
    queryKey: m2aKeys.alertList(filters),
    queryFn: () => alertApi.list(filters),
  });
}

export function useAlert(id: string) {
  return useQuery({
    queryKey: m2aKeys.alertDetail(id),
    queryFn: () => alertApi.get(id),
    enabled: !!id,
  });
}

export function useMarkAlertRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => alertApi.markRead(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.alertDetail(id) });
      queryClient.invalidateQueries({ queryKey: m2aKeys.alerts() });
    },
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string }) => alertApi.resolve(id, note),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.alertDetail(id) });
      queryClient.invalidateQueries({ queryKey: m2aKeys.alerts() });
    },
  });
}

export function useMarkAllAlertsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => alertApi.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.alerts() });
    },
  });
}

// ============================================================================
// ACCOUNTING RULE HOOKS
// ============================================================================

export function useAccountingRules() {
  return useQuery({
    queryKey: m2aKeys.rules(),
    queryFn: () => accountingRuleApi.list(),
  });
}

export function useAccountingRule(id: string) {
  return useQuery({
    queryKey: m2aKeys.ruleDetail(id),
    queryFn: () => accountingRuleApi.get(id),
    enabled: !!id,
  });
}

export function useCreateAccountingRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AccountingRuleCreate) => accountingRuleApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.rules() });
    },
  });
}

export function useUpdateAccountingRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<AccountingRuleCreate> }) =>
      accountingRuleApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.ruleDetail(id) });
      queryClient.invalidateQueries({ queryKey: m2aKeys.rules() });
    },
  });
}

export function useDeleteAccountingRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => accountingRuleApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.rules() });
    },
  });
}

export function useToggleAccountingRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      accountingRuleApi.toggle(id, isActive),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.ruleDetail(id) });
      queryClient.invalidateQueries({ queryKey: m2aKeys.rules() });
    },
  });
}

// ============================================================================
// EMAIL INBOX HOOKS
// ============================================================================

export function useEmailInboxes() {
  return useQuery({
    queryKey: m2aKeys.emailInboxes(),
    queryFn: () => emailInboxApi.list(),
  });
}

export function useEmailInbox(id: string) {
  return useQuery({
    queryKey: m2aKeys.emailInboxDetail(id),
    queryFn: () => emailInboxApi.get(id),
    enabled: !!id,
  });
}

export function useCreateEmailInbox() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EmailInboxCreate) => emailInboxApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.emailInboxes() });
    },
  });
}

export function useDeleteEmailInbox() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => emailInboxApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.emailInboxes() });
    },
  });
}

export function useCheckEmailInbox() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => emailInboxApi.check(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: m2aKeys.emailInboxes() });
      queryClient.invalidateQueries({ queryKey: m2aKeys.documents() });
    },
  });
}

// ============================================================================
// SYNC LOG HOOKS
// ============================================================================

export function useSyncLogs(connectionId?: string) {
  return useQuery({
    queryKey: m2aKeys.syncLogs(connectionId),
    queryFn: () => syncLogApi.list(connectionId),
  });
}
