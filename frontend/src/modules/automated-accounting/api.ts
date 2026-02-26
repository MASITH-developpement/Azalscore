/**
 * AZALSCORE - Automated Accounting API
 * ====================================
 * API client pour le module Comptabilite Automatisee
 * Couvre: Documents, Rapprochement bancaire, Dashboard par vue
 */

import { api } from '@/core/api-client';

// ============================================================================
// TYPES
// ============================================================================

export type DocumentStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'VALIDATED'
  | 'REJECTED'
  | 'ERROR';

export type DocumentType =
  | 'INVOICE_RECEIVED'
  | 'INVOICE_SENT'
  | 'RECEIPT'
  | 'BANK_STATEMENT'
  | 'EXPENSE_REPORT'
  | 'OTHER';

export type ReconciliationStatus =
  | 'PENDING'
  | 'MATCHED'
  | 'PARTIAL'
  | 'UNMATCHED';

export interface AccountingDocument {
  id: string;
  type: DocumentType;
  status: DocumentStatus;
  reference?: string;
  supplier_name?: string;
  customer_name?: string;
  amount?: number;
  tax_amount?: number;
  date?: string;
  due_date?: string;
  file_url?: string;
  ocr_data?: Record<string, unknown>;
  accounting_entry_id?: string;
  created_at: string;
  processed_at?: string;
  validated_at?: string;
  validated_by?: string;
}

export interface BankTransaction {
  id: string;
  bank_account_id: string;
  date: string;
  amount: number;
  type: 'CREDIT' | 'DEBIT';
  reference?: string;
  description?: string;
  status: ReconciliationStatus;
  matched_document_id?: string;
  matched_entry_id?: string;
  created_at: string;
}

export interface BankConnection {
  id: string;
  bank_name: string;
  account_name: string;
  account_number_masked: string;
  iban_masked?: string;
  is_active: boolean;
  last_sync_at?: string;
  balance?: number;
  sync_status: 'OK' | 'ERROR' | 'PENDING';
  error_message?: string;
}

export interface DirigeantDashboard {
  total_revenue: number;
  total_expenses: number;
  net_result: number;
  cash_position: number;
  pending_receivables: number;
  pending_payables: number;
  cash_flow_trend: Array<{ date: string; value: number }>;
}

export interface AssistanteDashboard {
  documents_to_process: number;
  documents_pending_validation: number;
  documents_with_errors: number;
  recent_documents: AccountingDocument[];
}

export interface ExpertDashboard {
  entries_to_validate: number;
  reconciliation_pending: number;
  anomalies_detected: number;
  validation_rate: number;
  entries_by_journal: Array<{ journal: string; count: number }>;
}

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface DocumentFilters {
  type?: DocumentType;
  status?: DocumentStatus;
  date_from?: string;
  date_to?: string;
  supplier_name?: string;
  page?: number;
  page_size?: number;
}

export interface TransactionFilters {
  bank_account_id?: string;
  status?: ReconciliationStatus;
  date_from?: string;
  date_to?: string;
  type?: 'CREDIT' | 'DEBIT';
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/automated-accounting';

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

export const automatedAccountingApi = {
  // ==========================================================================
  // Dashboards par Vue
  // ==========================================================================

  /**
   * Dashboard Dirigeant (zero jargon comptable)
   */
  getDirigeantDashboard: () =>
    api.get<DirigeantDashboard>(`${BASE_PATH}/dashboard/dirigeant`),

  /**
   * Dashboard Assistante (centralisation documents)
   */
  getAssistanteDashboard: () =>
    api.get<AssistanteDashboard>(`${BASE_PATH}/dashboard/assistante`),

  /**
   * Dashboard Expert-comptable (validation et controle)
   */
  getExpertDashboard: () =>
    api.get<ExpertDashboard>(`${BASE_PATH}/dashboard/expert`),

  // ==========================================================================
  // Documents
  // ==========================================================================

  /**
   * Liste les documents comptables
   */
  listDocuments: (filters?: DocumentFilters) =>
    api.get<PaginatedResponse<AccountingDocument>>(
      `${BASE_PATH}/documents${buildQueryString(filters || {})}`
    ),

  /**
   * Recupere un document par son ID
   */
  getDocument: (id: string) =>
    api.get<AccountingDocument>(`${BASE_PATH}/documents/${id}`),

  /**
   * Upload un nouveau document
   */
  uploadDocument: (file: File, type?: DocumentType) => {
    const formData = new FormData();
    formData.append('file', file);
    if (type) formData.append('type', type);
    return api.post<AccountingDocument>(`${BASE_PATH}/documents`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /**
   * Valide un document
   */
  validateDocument: (id: string) =>
    api.post<AccountingDocument>(`${BASE_PATH}/documents/${id}/validate`, {}),

  /**
   * Rejette un document
   */
  rejectDocument: (id: string, reason?: string) =>
    api.post<AccountingDocument>(`${BASE_PATH}/documents/${id}/reject`, { reason }),

  /**
   * Relance le traitement OCR
   */
  reprocessDocument: (id: string) =>
    api.post<AccountingDocument>(`${BASE_PATH}/documents/${id}/reprocess`, {}),

  /**
   * Met a jour les donnees extraites
   */
  updateDocumentData: (id: string, data: Partial<AccountingDocument>) =>
    api.patch<AccountingDocument>(`${BASE_PATH}/documents/${id}`, data),

  // ==========================================================================
  // Bank Connections
  // ==========================================================================

  /**
   * Liste les connexions bancaires
   */
  listBankConnections: () =>
    api.get<BankConnection[]>(`${BASE_PATH}/bank/connections`),

  /**
   * Ajoute une connexion bancaire
   */
  addBankConnection: (data: { bank_id: string; credentials: Record<string, string> }) =>
    api.post<BankConnection>(`${BASE_PATH}/bank/connections`, data),

  /**
   * Supprime une connexion bancaire
   */
  removeBankConnection: (id: string) =>
    api.delete(`${BASE_PATH}/bank/connections/${id}`),

  /**
   * Synchronise une connexion bancaire
   */
  syncBankConnection: (id: string) =>
    api.post<BankConnection>(`${BASE_PATH}/bank/connections/${id}/sync`, {}),

  /**
   * Synchronise toutes les connexions
   */
  syncAllBankConnections: () =>
    api.post(`${BASE_PATH}/bank/sync-all`, {}),

  // ==========================================================================
  // Bank Transactions
  // ==========================================================================

  /**
   * Liste les transactions bancaires
   */
  listTransactions: (filters?: TransactionFilters) =>
    api.get<PaginatedResponse<BankTransaction>>(
      `${BASE_PATH}/bank/transactions${buildQueryString(filters || {})}`
    ),

  /**
   * Recupere une transaction par son ID
   */
  getTransaction: (id: string) =>
    api.get<BankTransaction>(`${BASE_PATH}/bank/transactions/${id}`),

  // ==========================================================================
  // Reconciliation
  // ==========================================================================

  /**
   * Obtient les suggestions de rapprochement pour une transaction
   */
  getReconciliationSuggestions: (transactionId: string) =>
    api.get<Array<{ document_id: string; score: number; reason: string }>>(
      `${BASE_PATH}/reconciliation/${transactionId}/suggestions`
    ),

  /**
   * Rapproche une transaction avec un document
   */
  reconcile: (transactionId: string, documentId: string) =>
    api.post<BankTransaction>(`${BASE_PATH}/reconciliation`, {
      transaction_id: transactionId,
      document_id: documentId,
    }),

  /**
   * Annule un rapprochement
   */
  unreconcile: (transactionId: string) =>
    api.post<BankTransaction>(`${BASE_PATH}/reconciliation/${transactionId}/undo`, {}),

  /**
   * Rapprochement automatique
   */
  autoReconcile: () =>
    api.post<{ matched: number; unmatched: number }>(`${BASE_PATH}/reconciliation/auto`, {}),
};

export default automatedAccountingApi;
