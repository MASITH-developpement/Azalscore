/**
 * AZALSCORE Module - Automated Accounting (M2A) API
 * Client REST pour la comptabilite automatisee
 */

import { api } from '@core/api-client';
import type {
  Document,
  DocumentUpdate,
  DocumentFilters,
  DocumentListResponse,
  BankConnection,
  BankConnectionCreate,
  BankTransaction,
  BankTransactionFilters,
  BankTransactionListResponse,
  Alert,
  AlertFilters,
  AlertListResponse,
  AccountingRule,
  AccountingRuleCreate,
  EmailInbox,
  EmailInboxCreate,
  SyncLog,
  M2ADashboard,
  ReconciliationAction,
  ReconciliationSuggestion,
  DocumentType,
} from './types';

const BASE_URL = '/accounting';

// ============================================================================
// DASHBOARDS
// ============================================================================

export const dashboardApi = {
  getDirigeant: (syncBank = true) =>
    api.get<{
      treasury_current: number;
      treasury_forecast_30d: number;
      invoices_to_pay: number;
      invoices_to_pay_amount: number;
      invoices_to_receive: number;
      invoices_to_receive_amount: number;
      result_estimated: number;
      alerts_critical: Alert[];
    }>(`${BASE_URL}/dirigeant/dashboard?sync_bank=${syncBank}`),

  getAssistante: () =>
    api.get<{
      documents_received_today: number;
      documents_pending: number;
      documents_error: number;
      recent_documents: Document[];
      alerts: Alert[];
    }>(`${BASE_URL}/assistante/dashboard`),

  getExpert: () =>
    api.get<{
      documents_to_validate: number;
      reconciliations_pending: number;
      alerts_unresolved: number;
      confidence_average: number;
      recent_entries: unknown[];
      pending_validations: Document[];
    }>(`${BASE_URL}/expert/dashboard`),

  getGeneral: () => api.get<M2ADashboard>(`${BASE_URL}/dashboard`),
};

// ============================================================================
// DOCUMENTS
// ============================================================================

export const documentApi = {
  list: (filters?: DocumentFilters) => {
    const params = new URLSearchParams();
    if (filters?.document_type) params.append('document_type', filters.document_type);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.source) params.append('source', filters.source);
    if (filters?.vendor_id) params.append('vendor_id', filters.vendor_id);
    if (filters?.from_date) params.append('from_date', filters.from_date);
    if (filters?.to_date) params.append('to_date', filters.to_date);
    if (filters?.payment_status) params.append('payment_status', filters.payment_status);
    if (filters?.search) params.append('search', filters.search);
    if (filters?.page) params.append('page', String(filters.page));
    if (filters?.page_size) params.append('page_size', String(filters.page_size));

    const queryString = params.toString();
    return api.get<DocumentListResponse>(`${BASE_URL}/documents${queryString ? `?${queryString}` : ''}`);
  },

  get: (id: string) => api.get<Document>(`${BASE_URL}/documents/${id}`),

  upload: async (file: File, documentType: DocumentType = 'INVOICE_RECEIVED') => {
    // For file upload, we need to use FormData
    const formData = new FormData();
    formData.append('file', file);
    // Using post with headers for multipart
    return api.post<Document>(
      `${BASE_URL}/assistante/documents/upload?document_type=${documentType}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  },

  update: (id: string, data: DocumentUpdate) =>
    api.put<Document>(`${BASE_URL}/documents/${id}`, data),

  validate: (id: string, data?: { corrections?: DocumentUpdate }) =>
    api.post<Document>(`${BASE_URL}/documents/${id}/validate`, data),

  reject: (id: string, reason?: string) =>
    api.post<Document>(`${BASE_URL}/documents/${id}/reject`, { reason }),

  reprocess: (id: string) =>
    api.post<Document>(`${BASE_URL}/documents/${id}/reprocess`),

  account: (id: string) =>
    api.post<{ entry_id: string }>(`${BASE_URL}/documents/${id}/account`),

  bulkValidate: (documentIds: string[]) =>
    api.post<{ validated: number; errors: string[] }>(
      `${BASE_URL}/expert/bulk-validate`,
      { document_ids: documentIds }
    ),

  download: (id: string) =>
    api.get<Blob>(`${BASE_URL}/documents/${id}/download`, { responseType: 'blob' }),
};

// ============================================================================
// BANK CONNECTIONS
// ============================================================================

export const bankConnectionApi = {
  list: () => api.get<BankConnection[]>(`${BASE_URL}/bank/connections`),

  get: (id: string) => api.get<BankConnection>(`${BASE_URL}/bank/connections/${id}`),

  create: (data: BankConnectionCreate) =>
    api.post<{ connection_id: string; redirect_url: string }>(
      `${BASE_URL}/bank/connections`,
      data
    ),

  delete: (id: string) => api.delete(`${BASE_URL}/bank/connections/${id}`),

  sync: (id: string) =>
    api.post<SyncLog>(`${BASE_URL}/bank/connections/${id}/sync`),

  syncAll: () => api.post<SyncLog[]>(`${BASE_URL}/bank/sync-all`),
};

// ============================================================================
// BANK TRANSACTIONS
// ============================================================================

export const bankTransactionApi = {
  list: (filters?: BankTransactionFilters) => {
    const params = new URLSearchParams();
    if (filters?.connection_id) params.append('connection_id', filters.connection_id);
    if (filters?.reconciliation_status) params.append('reconciliation_status', filters.reconciliation_status);
    if (filters?.from_date) params.append('from_date', filters.from_date);
    if (filters?.to_date) params.append('to_date', filters.to_date);
    if (filters?.min_amount) params.append('min_amount', String(filters.min_amount));
    if (filters?.max_amount) params.append('max_amount', String(filters.max_amount));
    if (filters?.search) params.append('search', filters.search);
    if (filters?.page) params.append('page', String(filters.page));
    if (filters?.page_size) params.append('page_size', String(filters.page_size));

    const queryString = params.toString();
    return api.get<BankTransactionListResponse>(`${BASE_URL}/bank/transactions${queryString ? `?${queryString}` : ''}`);
  },

  get: (id: string) => api.get<BankTransaction>(`${BASE_URL}/bank/transactions/${id}`),
};

// ============================================================================
// RECONCILIATION
// ============================================================================

export const reconciliationApi = {
  getSuggestions: (transactionId?: string) => {
    const params = transactionId ? `?transaction_id=${transactionId}` : '';
    return api.get<ReconciliationSuggestion[]>(`${BASE_URL}/reconciliation/suggestions${params}`);
  },

  reconcile: (action: ReconciliationAction) =>
    api.post<BankTransaction>(`${BASE_URL}/reconciliation/manual`, action),

  unreconcile: (transactionId: string) =>
    api.post<BankTransaction>(`${BASE_URL}/reconciliation/unreconcile`, {
      transaction_id: transactionId,
    }),

  autoReconcile: () =>
    api.post<{ matched: number; unmatched: number }>(`${BASE_URL}/reconciliation/auto`),
};

// ============================================================================
// ALERTS
// ============================================================================

export const alertApi = {
  list: (filters?: AlertFilters) => {
    const params = new URLSearchParams();
    if (filters?.alert_type) params.append('alert_type', filters.alert_type);
    if (filters?.severity) params.append('severity', filters.severity);
    if (filters?.is_read !== undefined) params.append('is_read', String(filters.is_read));
    if (filters?.is_resolved !== undefined) params.append('is_resolved', String(filters.is_resolved));
    if (filters?.page) params.append('page', String(filters.page));
    if (filters?.page_size) params.append('page_size', String(filters.page_size));

    const queryString = params.toString();
    return api.get<AlertListResponse>(`${BASE_URL}/alerts${queryString ? `?${queryString}` : ''}`);
  },

  get: (id: string) => api.get<Alert>(`${BASE_URL}/alerts/${id}`),

  markRead: (id: string) =>
    api.put<Alert>(`${BASE_URL}/alerts/${id}`, { is_read: true }),

  resolve: (id: string, note?: string) =>
    api.put<Alert>(`${BASE_URL}/alerts/${id}`, {
      is_resolved: true,
      resolution_note: note,
    }),

  markAllRead: () => api.post(`${BASE_URL}/alerts/mark-all-read`),
};

// ============================================================================
// ACCOUNTING RULES
// ============================================================================

export const accountingRuleApi = {
  list: () => api.get<AccountingRule[]>(`${BASE_URL}/rules`),

  get: (id: string) => api.get<AccountingRule>(`${BASE_URL}/rules/${id}`),

  create: (data: AccountingRuleCreate) =>
    api.post<AccountingRule>(`${BASE_URL}/rules`, data),

  update: (id: string, data: Partial<AccountingRuleCreate>) =>
    api.put<AccountingRule>(`${BASE_URL}/rules/${id}`, data),

  delete: (id: string) => api.delete(`${BASE_URL}/rules/${id}`),

  toggle: (id: string, isActive: boolean) =>
    api.put<AccountingRule>(`${BASE_URL}/rules/${id}`, { is_active: isActive }),
};

// ============================================================================
// EMAIL INBOXES
// ============================================================================

export const emailInboxApi = {
  list: () => api.get<EmailInbox[]>(`${BASE_URL}/email-inboxes`),

  get: (id: string) => api.get<EmailInbox>(`${BASE_URL}/email-inboxes/${id}`),

  create: (data: EmailInboxCreate) =>
    api.post<EmailInbox>(`${BASE_URL}/email-inboxes`, data),

  delete: (id: string) => api.delete(`${BASE_URL}/email-inboxes/${id}`),

  check: (id: string) =>
    api.post<{ documents_received: number }>(`${BASE_URL}/email-inboxes/${id}/check`),
};

// ============================================================================
// SYNC LOGS
// ============================================================================

export const syncLogApi = {
  list: (connectionId?: string) => {
    const params = connectionId ? `?connection_id=${connectionId}` : '';
    return api.get<SyncLog[]>(`${BASE_URL}/bank/sync-logs${params}`);
  },
};
