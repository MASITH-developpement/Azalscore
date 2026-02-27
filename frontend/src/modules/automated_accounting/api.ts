/**
 * AZALSCORE Module - Automated Accounting (M2A) API
 * Client REST pour la comptabilite automatisee
 */

import { api } from '@/core/api-client';
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
  AlertUpdate,
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
  /**
   * Dashboard simplifie pour le dirigeant
   */
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
    }>(`${BASE_URL}/dirigeant/dashboard`, { params: { sync_bank: syncBank } }),

  /**
   * Dashboard documentaire pour l'assistante
   */
  getAssistante: () =>
    api.get<{
      documents_received_today: number;
      documents_pending: number;
      documents_error: number;
      recent_documents: Document[];
      alerts: Alert[];
    }>(`${BASE_URL}/assistante/dashboard`),

  /**
   * Dashboard complet pour l'expert-comptable
   */
  getExpert: () =>
    api.get<{
      documents_to_validate: number;
      reconciliations_pending: number;
      alerts_unresolved: number;
      confidence_average: number;
      recent_entries: unknown[];
      pending_validations: Document[];
    }>(`${BASE_URL}/expert/dashboard`),

  /**
   * Dashboard general M2A
   */
  getGeneral: () => api.get<M2ADashboard>(`${BASE_URL}/dashboard`),
};

// ============================================================================
// DOCUMENTS
// ============================================================================

export const documentApi = {
  /**
   * Liste des documents
   */
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

    return api.get<DocumentListResponse>(`${BASE_URL}/documents?${params.toString()}`);
  },

  /**
   * Detail d'un document
   */
  get: (id: string) => api.get<Document>(`${BASE_URL}/documents/${id}`),

  /**
   * Upload d'un document
   */
  upload: (file: File, documentType: DocumentType = 'INVOICE_RECEIVED') => {
    const formData = new FormData();
    formData.append('file', file);
    return api.postForm<Document>(
      `${BASE_URL}/assistante/documents/upload?document_type=${documentType}`,
      formData
    );
  },

  /**
   * Mise a jour d'un document
   */
  update: (id: string, data: DocumentUpdate) =>
    api.put<Document>(`${BASE_URL}/documents/${id}`, data),

  /**
   * Valider un document
   */
  validate: (id: string, data?: { corrections?: DocumentUpdate }) =>
    api.post<Document>(`${BASE_URL}/documents/${id}/validate`, data),

  /**
   * Rejeter un document
   */
  reject: (id: string, reason?: string) =>
    api.post<Document>(`${BASE_URL}/documents/${id}/reject`, { reason }),

  /**
   * Relancer le traitement OCR/IA
   */
  reprocess: (id: string) =>
    api.post<Document>(`${BASE_URL}/documents/${id}/reprocess`),

  /**
   * Comptabiliser un document
   */
  account: (id: string) =>
    api.post<{ entry_id: string }>(`${BASE_URL}/documents/${id}/account`),

  /**
   * Validation en masse
   */
  bulkValidate: (documentIds: string[]) =>
    api.post<{ validated: number; errors: string[] }>(
      `${BASE_URL}/expert/bulk-validate`,
      { document_ids: documentIds }
    ),

  /**
   * Telecharger le fichier original
   */
  download: (id: string) =>
    api.get<Blob>(`${BASE_URL}/documents/${id}/download`, { responseType: 'blob' }),
};

// ============================================================================
// BANK CONNECTIONS
// ============================================================================

export const bankConnectionApi = {
  /**
   * Liste des connexions bancaires
   */
  list: () => api.get<BankConnection[]>(`${BASE_URL}/bank/connections`),

  /**
   * Detail d'une connexion
   */
  get: (id: string) => api.get<BankConnection>(`${BASE_URL}/bank/connections/${id}`),

  /**
   * Initier une connexion bancaire
   */
  create: (data: BankConnectionCreate) =>
    api.post<{ connection_id: string; redirect_url: string }>(
      `${BASE_URL}/bank/connections`,
      data
    ),

  /**
   * Deconnecter une banque
   */
  delete: (id: string) => api.delete(`${BASE_URL}/bank/connections/${id}`),

  /**
   * Declencher une synchronisation
   */
  sync: (id: string) =>
    api.post<SyncLog>(`${BASE_URL}/bank/connections/${id}/sync`),

  /**
   * Synchroniser toutes les connexions
   */
  syncAll: () => api.post<SyncLog[]>(`${BASE_URL}/bank/sync-all`),
};

// ============================================================================
// BANK TRANSACTIONS
// ============================================================================

export const bankTransactionApi = {
  /**
   * Liste des transactions bancaires
   */
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

    return api.get<BankTransactionListResponse>(`${BASE_URL}/bank/transactions?${params.toString()}`);
  },

  /**
   * Detail d'une transaction
   */
  get: (id: string) => api.get<BankTransaction>(`${BASE_URL}/bank/transactions/${id}`),
};

// ============================================================================
// RECONCILIATION
// ============================================================================

export const reconciliationApi = {
  /**
   * Obtenir les suggestions de rapprochement
   */
  getSuggestions: (transactionId?: string) => {
    const params = transactionId ? `?transaction_id=${transactionId}` : '';
    return api.get<ReconciliationSuggestion[]>(`${BASE_URL}/reconciliation/suggestions${params}`);
  },

  /**
   * Rapprocher manuellement
   */
  reconcile: (action: ReconciliationAction) =>
    api.post<BankTransaction>(`${BASE_URL}/reconciliation/manual`, action),

  /**
   * Annuler un rapprochement
   */
  unreconcile: (transactionId: string) =>
    api.post<BankTransaction>(`${BASE_URL}/reconciliation/unreconcile`, {
      transaction_id: transactionId,
    }),

  /**
   * Lancer le rapprochement automatique
   */
  autoReconcile: () =>
    api.post<{ matched: number; unmatched: number }>(`${BASE_URL}/reconciliation/auto`),
};

// ============================================================================
// ALERTS
// ============================================================================

export const alertApi = {
  /**
   * Liste des alertes
   */
  list: (filters?: AlertFilters) => {
    const params = new URLSearchParams();
    if (filters?.alert_type) params.append('alert_type', filters.alert_type);
    if (filters?.severity) params.append('severity', filters.severity);
    if (filters?.is_read !== undefined) params.append('is_read', String(filters.is_read));
    if (filters?.is_resolved !== undefined) params.append('is_resolved', String(filters.is_resolved));
    if (filters?.page) params.append('page', String(filters.page));
    if (filters?.page_size) params.append('page_size', String(filters.page_size));

    return api.get<AlertListResponse>(`${BASE_URL}/alerts?${params.toString()}`);
  },

  /**
   * Detail d'une alerte
   */
  get: (id: string) => api.get<Alert>(`${BASE_URL}/alerts/${id}`),

  /**
   * Marquer comme lu
   */
  markRead: (id: string) =>
    api.put<Alert>(`${BASE_URL}/alerts/${id}`, { is_read: true }),

  /**
   * Resoudre une alerte
   */
  resolve: (id: string, note?: string) =>
    api.put<Alert>(`${BASE_URL}/alerts/${id}`, {
      is_resolved: true,
      resolution_note: note,
    }),

  /**
   * Marquer toutes comme lues
   */
  markAllRead: () => api.post(`${BASE_URL}/alerts/mark-all-read`),
};

// ============================================================================
// ACCOUNTING RULES
// ============================================================================

export const accountingRuleApi = {
  /**
   * Liste des regles comptables
   */
  list: () => api.get<AccountingRule[]>(`${BASE_URL}/rules`),

  /**
   * Detail d'une regle
   */
  get: (id: string) => api.get<AccountingRule>(`${BASE_URL}/rules/${id}`),

  /**
   * Creer une regle
   */
  create: (data: AccountingRuleCreate) =>
    api.post<AccountingRule>(`${BASE_URL}/rules`, data),

  /**
   * Mettre a jour une regle
   */
  update: (id: string, data: Partial<AccountingRuleCreate>) =>
    api.put<AccountingRule>(`${BASE_URL}/rules/${id}`, data),

  /**
   * Supprimer une regle
   */
  delete: (id: string) => api.delete(`${BASE_URL}/rules/${id}`),

  /**
   * Activer/Desactiver une regle
   */
  toggle: (id: string, isActive: boolean) =>
    api.put<AccountingRule>(`${BASE_URL}/rules/${id}`, { is_active: isActive }),
};

// ============================================================================
// EMAIL INBOXES
// ============================================================================

export const emailInboxApi = {
  /**
   * Liste des boites email
   */
  list: () => api.get<EmailInbox[]>(`${BASE_URL}/email-inboxes`),

  /**
   * Detail d'une boite
   */
  get: (id: string) => api.get<EmailInbox>(`${BASE_URL}/email-inboxes/${id}`),

  /**
   * Configurer une boite email
   */
  create: (data: EmailInboxCreate) =>
    api.post<EmailInbox>(`${BASE_URL}/email-inboxes`, data),

  /**
   * Supprimer une boite email
   */
  delete: (id: string) => api.delete(`${BASE_URL}/email-inboxes/${id}`),

  /**
   * Verifier manuellement une boite
   */
  check: (id: string) =>
    api.post<{ documents_received: number }>(`${BASE_URL}/email-inboxes/${id}/check`),
};

// ============================================================================
// SYNC LOGS
// ============================================================================

export const syncLogApi = {
  /**
   * Liste des logs de synchronisation
   */
  list: (connectionId?: string) => {
    const params = connectionId ? `?connection_id=${connectionId}` : '';
    return api.get<SyncLog[]>(`${BASE_URL}/bank/sync-logs${params}`);
  },
};
