/**
 * AZALSCORE Module - Automated Accounting (M2A) Types
 * Types TypeScript pour la comptabilite automatisee
 */

// ============================================================================
// ENUMS
// ============================================================================

export type DocumentType =
  | 'INVOICE_RECEIVED'
  | 'INVOICE_SENT'
  | 'EXPENSE_NOTE'
  | 'CREDIT_NOTE_RECEIVED'
  | 'CREDIT_NOTE_SENT'
  | 'QUOTE'
  | 'PURCHASE_ORDER'
  | 'DELIVERY_NOTE'
  | 'BANK_STATEMENT'
  | 'OTHER';

export type DocumentStatus =
  | 'RECEIVED'
  | 'PROCESSING'
  | 'ANALYZED'
  | 'PENDING_VALIDATION'
  | 'VALIDATED'
  | 'ACCOUNTED'
  | 'REJECTED'
  | 'ERROR';

export type DocumentSource =
  | 'EMAIL'
  | 'UPLOAD'
  | 'MOBILE_SCAN'
  | 'API'
  | 'BANK_SYNC'
  | 'INTERNAL';

export type ConfidenceLevel =
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'VERY_LOW';

export type PaymentStatus =
  | 'UNPAID'
  | 'PARTIALLY_PAID'
  | 'PAID'
  | 'OVERPAID'
  | 'CANCELLED';

export type BankConnectionStatus =
  | 'ACTIVE'
  | 'EXPIRED'
  | 'REQUIRES_ACTION'
  | 'ERROR'
  | 'DISCONNECTED';

export type ReconciliationStatus =
  | 'PENDING'
  | 'MATCHED'
  | 'PARTIAL'
  | 'MANUAL'
  | 'UNMATCHED';

export type AlertType =
  | 'DOCUMENT_UNREADABLE'
  | 'MISSING_INFO'
  | 'LOW_CONFIDENCE'
  | 'DUPLICATE_SUSPECTED'
  | 'AMOUNT_MISMATCH'
  | 'TAX_ERROR'
  | 'OVERDUE_PAYMENT'
  | 'CASH_FLOW_WARNING'
  | 'RECONCILIATION_ISSUE';

export type AlertSeverity =
  | 'INFO'
  | 'WARNING'
  | 'ERROR'
  | 'CRITICAL';

export type ViewType =
  | 'DIRIGEANT'
  | 'ASSISTANTE'
  | 'EXPERT_COMPTABLE';

export type SyncType =
  | 'MANUAL'
  | 'SCHEDULED'
  | 'ON_DEMAND';

export type SyncStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'FAILED';

export type EmailInboxType =
  | 'INVOICES'
  | 'EXPENSE_NOTES'
  | 'GENERAL';

// ============================================================================
// DOCUMENT
// ============================================================================

export interface ExtractedData {
  vendor_name?: string;
  vendor_vat?: string;
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
  total_ht?: number;
  total_tva?: number;
  total_ttc?: number;
  currency?: string;
  lines?: ExtractedLine[];
  [key: string]: unknown;
}

export interface ExtractedLine {
  description?: string;
  quantity?: number;
  unit_price?: number;
  amount?: number;
  tva_rate?: number;
}

export interface Document {
  id: string;
  tenant_id: string;
  document_type: DocumentType;
  source: DocumentSource;
  status: DocumentStatus;
  original_filename?: string;
  file_path?: string;
  file_size?: number;
  mime_type?: string;
  ocr_text?: string;
  extracted_data?: ExtractedData;
  confidence_score?: number;
  confidence_level?: ConfidenceLevel;
  vendor_id?: string;
  vendor_name?: string;
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
  total_ht?: number | string;
  total_tva?: number | string;
  total_ttc?: number | string;
  currency?: string;
  payment_status?: PaymentStatus;
  accounting_entry_id?: string;
  is_duplicate?: boolean;
  duplicate_of_id?: string;
  validated_by?: string;
  validated_at?: string;
  accounted_at?: string;
  error_message?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface DocumentCreate {
  document_type: DocumentType;
  source?: DocumentSource;
  file?: File;
}

export interface DocumentUpdate {
  document_type?: DocumentType;
  vendor_id?: string;
  vendor_name?: string;
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
  total_ht?: number;
  total_tva?: number;
  total_ttc?: number;
  currency?: string;
  extracted_data?: ExtractedData;
}

// ============================================================================
// BANK CONNECTION
// ============================================================================

export interface BankConnection {
  id: string;
  tenant_id: string;
  provider: string;
  bank_name: string;
  account_name?: string;
  account_number_masked?: string;
  iban_masked?: string;
  status: BankConnectionStatus;
  last_sync_at?: string;
  next_sync_at?: string;
  sync_frequency?: string;
  error_message?: string;
  requires_action?: boolean;
  action_url?: string;
  created_at: string;
  updated_at: string;
}

export interface BankConnectionCreate {
  provider: string;
  redirect_url?: string;
}

// ============================================================================
// BANK TRANSACTION
// ============================================================================

export interface BankTransaction {
  id: string;
  tenant_id: string;
  connection_id: string;
  transaction_id: string;
  booking_date: string;
  value_date?: string;
  amount: number | string;
  currency: string;
  description?: string;
  counterparty_name?: string;
  counterparty_iban?: string;
  reference?: string;
  category?: string;
  reconciliation_status: ReconciliationStatus;
  reconciled_document_id?: string;
  reconciled_entry_id?: string;
  is_internal_transfer?: boolean;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// RECONCILIATION
// ============================================================================

export interface ReconciliationSuggestion {
  transaction_id: string;
  document_id: string;
  confidence: number;
  match_reasons: string[];
  amount_match: boolean;
  date_match: boolean;
  reference_match: boolean;
}

export interface ReconciliationAction {
  transaction_id: string;
  document_id?: string;
  action: 'match' | 'unmatch' | 'ignore';
}

// ============================================================================
// ALERT
// ============================================================================

export interface Alert {
  id: string;
  tenant_id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  document_id?: string;
  transaction_id?: string;
  is_read: boolean;
  is_resolved: boolean;
  resolved_by?: string;
  resolved_at?: string;
  resolution_note?: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface AlertUpdate {
  is_read?: boolean;
  is_resolved?: boolean;
  resolution_note?: string;
}

// ============================================================================
// EMAIL INBOX
// ============================================================================

export interface EmailInbox {
  id: string;
  tenant_id: string;
  email_address: string;
  inbox_type: EmailInboxType;
  provider?: string;
  is_active: boolean;
  last_check_at?: string;
  documents_received: number;
  created_at: string;
  updated_at: string;
}

export interface EmailInboxCreate {
  email_address: string;
  inbox_type: EmailInboxType;
  provider?: string;
}

// ============================================================================
// ACCOUNTING RULE
// ============================================================================

export interface AccountingRule {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  document_type?: DocumentType;
  vendor_pattern?: string;
  amount_min?: number;
  amount_max?: number;
  debit_account: string;
  credit_account: string;
  analytics_code?: string;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountingRuleCreate {
  name: string;
  description?: string;
  document_type?: DocumentType;
  vendor_pattern?: string;
  amount_min?: number;
  amount_max?: number;
  debit_account: string;
  credit_account: string;
  analytics_code?: string;
  priority?: number;
}

// ============================================================================
// SYNC LOG
// ============================================================================

export interface SyncLog {
  id: string;
  tenant_id: string;
  connection_id?: string;
  sync_type: SyncType;
  status: SyncStatus;
  started_at: string;
  completed_at?: string;
  transactions_fetched: number;
  transactions_created: number;
  transactions_updated: number;
  error_message?: string;
}

// ============================================================================
// STATS & DASHBOARD
// ============================================================================

export interface M2AStats {
  documents_total: number;
  documents_pending: number;
  documents_processed: number;
  documents_error: number;
  bank_connections: number;
  unreconciled_transactions: number;
  alerts_unread: number;
  alerts_critical: number;
  processing_rate: number;
  confidence_average: number;
}

export interface M2ADashboard {
  stats: M2AStats;
  recent_documents: Document[];
  recent_transactions: BankTransaction[];
  pending_alerts: Alert[];
  reconciliation_suggestions: ReconciliationSuggestion[];
}

// ============================================================================
// LIST RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export type DocumentListResponse = PaginatedResponse<Document>;
export type BankTransactionListResponse = PaginatedResponse<BankTransaction>;
export type AlertListResponse = PaginatedResponse<Alert>;

// ============================================================================
// FILTERS
// ============================================================================

export interface DocumentFilters {
  document_type?: DocumentType;
  status?: DocumentStatus;
  source?: DocumentSource;
  vendor_id?: string;
  from_date?: string;
  to_date?: string;
  payment_status?: PaymentStatus;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface BankTransactionFilters {
  connection_id?: string;
  reconciliation_status?: ReconciliationStatus;
  from_date?: string;
  to_date?: string;
  min_amount?: number;
  max_amount?: number;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface AlertFilters {
  alert_type?: AlertType;
  severity?: AlertSeverity;
  is_read?: boolean;
  is_resolved?: boolean;
  page?: number;
  page_size?: number;
}
