/**
 * AZALSCORE Module - HR Vault - Types
 * =====================================
 * Types et constantes pour le module Coffre-fort RH
 */

// ============================================================================
// ENUMS
// ============================================================================

export type VaultDocumentType =
  | 'PAYSLIP'
  | 'PAYSLIP_SUMMARY'
  | 'TAX_STATEMENT'
  | 'CONTRACT'
  | 'AMENDMENT'
  | 'TEMPORARY_CONTRACT'
  | 'APPRENTICESHIP'
  | 'INTERNSHIP'
  | 'EMPLOYMENT_CERTIFICATE'
  | 'SALARY_CERTIFICATE'
  | 'TRAINING_CERTIFICATE'
  | 'FRANCE_TRAVAIL'
  | 'TERMINATION_LETTER'
  | 'STC'
  | 'WORK_CERTIFICATE'
  | 'PORTABILITY_NOTICE'
  | 'MEDICAL_APTITUDE'
  | 'ACCIDENT_DECLARATION'
  | 'ID_DOCUMENT'
  | 'DIPLOMA'
  | 'DEGREE'
  | 'CERTIFICATION'
  | 'RIB'
  | 'VITALE_CARD'
  | 'DRIVING_LICENSE'
  | 'EVALUATION'
  | 'WARNING'
  | 'PROMOTION_LETTER'
  | 'BONUS_LETTER'
  | 'OTHER';

export type VaultDocumentStatus =
  | 'DRAFT'
  | 'PENDING_SIGNATURE'
  | 'PENDING_VALIDATION'
  | 'ACTIVE'
  | 'ARCHIVED'
  | 'DELETED';

export type SignatureStatus =
  | 'NOT_REQUIRED'
  | 'PENDING'
  | 'SIGNED_EMPLOYEE'
  | 'SIGNED_EMPLOYER'
  | 'FULLY_SIGNED'
  | 'REJECTED'
  | 'EXPIRED';

export type RetentionPeriod =
  | '5_YEARS'
  | '10_YEARS'
  | '30_YEARS'
  | '50_YEARS'
  | 'LIFETIME_PLUS_5'
  | 'PERMANENT';

export type VaultAccessType =
  | 'VIEW'
  | 'DOWNLOAD'
  | 'PRINT'
  | 'SHARE'
  | 'EDIT'
  | 'DELETE'
  | 'SIGN';

export type VaultAccessRole =
  | 'EMPLOYEE'
  | 'MANAGER'
  | 'HR_ADMIN'
  | 'HR_DIRECTOR'
  | 'LEGAL'
  | 'ACCOUNTANT'
  | 'SYSTEM';

export type GDPRRequestType =
  | 'ACCESS'
  | 'RECTIFICATION'
  | 'ERASURE'
  | 'PORTABILITY'
  | 'RESTRICTION'
  | 'OBJECTION';

export type GDPRRequestStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'REJECTED'
  | 'EXPIRED';

export type AlertType =
  | 'EXPIRATION'
  | 'MISSING_DOCUMENT'
  | 'SIGNATURE_PENDING'
  | 'RETENTION_END'
  | 'GDPR_REQUEST'
  | 'ACCESS_ANOMALY';

// ============================================================================
// INTERFACES - CATEGORY
// ============================================================================

export interface VaultCategory {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  default_retention: RetentionPeriod;
  requires_signature: boolean;
  is_confidential: boolean;
  visible_to_employee: boolean;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  documents_count: number;
}

export interface VaultCategoryCreate {
  code: string;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  default_retention?: RetentionPeriod;
  requires_signature?: boolean;
  is_confidential?: boolean;
  visible_to_employee?: boolean;
  sort_order?: number;
}

// ============================================================================
// INTERFACES - DOCUMENT
// ============================================================================

export interface VaultDocument {
  id: string;
  tenant_id: string;
  employee_id: string;
  category_id?: string;
  document_type: VaultDocumentType;
  title: string;
  description?: string;
  reference?: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  is_encrypted: boolean;
  file_hash: string;
  status: VaultDocumentStatus;
  document_date?: string;
  period_start?: string;
  period_end?: string;
  effective_date?: string;
  expiry_date?: string;
  pay_period?: string;
  gross_salary?: number;
  net_salary?: number;
  signature_status: SignatureStatus;
  signed_at?: string;
  retention_period: RetentionPeriod;
  retention_end_date?: string;
  is_confidential: boolean;
  confidentiality_level: number;
  visible_to_employee: boolean;
  employee_notified: boolean;
  notification_sent_at?: string;
  employee_viewed: boolean;
  first_viewed_at?: string;
  tags: string[];
  custom_fields: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  created_by?: string;
  updated_at: string;
  version: number;
  category_name?: string;
  employee_name?: string;
}

export interface VaultDocumentUpload {
  employee_id: string;
  document_type: VaultDocumentType;
  title: string;
  category_id?: string;
  description?: string;
  reference?: string;
  document_date?: string;
  period_start?: string;
  period_end?: string;
  pay_period?: string;
  gross_salary?: number;
  net_salary?: number;
  notify_employee?: boolean;
  requires_signature?: boolean;
  tags?: string[];
}

export interface VaultDocumentUpdate {
  title?: string;
  description?: string;
  reference?: string;
  category_id?: string;
  document_date?: string;
  period_start?: string;
  period_end?: string;
  effective_date?: string;
  expiry_date?: string;
  is_confidential?: boolean;
  confidentiality_level?: number;
  visible_to_employee?: boolean;
  tags?: string[];
  custom_fields?: Record<string, unknown>;
}

export interface VaultDocumentFilters {
  employee_id?: string;
  document_type?: VaultDocumentType;
  category_id?: string;
  status?: VaultDocumentStatus;
  signature_status?: SignatureStatus;
  date_from?: string;
  date_to?: string;
  pay_period?: string;
  search?: string;
  tags?: string[];
}

export interface VaultDocumentListResponse {
  items: VaultDocument[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// ============================================================================
// INTERFACES - ACCESS LOG
// ============================================================================

export interface VaultAccessLog {
  id: string;
  document_id: string;
  employee_id: string;
  accessed_by: string;
  access_role: VaultAccessRole;
  access_type: VaultAccessType;
  access_date: string;
  ip_address?: string;
  device_type?: string;
  success: boolean;
  error_message?: string;
  document_title?: string;
  accessed_by_name?: string;
}

// ============================================================================
// INTERFACES - RGPD
// ============================================================================

export interface VaultGDPRRequest {
  id: string;
  tenant_id: string;
  employee_id: string;
  request_code: string;
  request_type: GDPRRequestType;
  status: GDPRRequestStatus;
  request_description?: string;
  document_types: VaultDocumentType[];
  period_start?: string;
  period_end?: string;
  requested_at: string;
  due_date: string;
  processed_at?: string;
  processed_by?: string;
  response_details?: string;
  download_count: number;
  employee_name?: string;
  processed_by_name?: string;
}

export interface VaultGDPRRequestCreate {
  employee_id: string;
  request_type: GDPRRequestType;
  request_description?: string;
  document_types?: VaultDocumentType[];
  period_start?: string;
  period_end?: string;
}

// ============================================================================
// INTERFACES - ALERT
// ============================================================================

export interface VaultAlert {
  id: string;
  tenant_id: string;
  employee_id?: string;
  document_id?: string;
  alert_type: AlertType;
  title: string;
  description?: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  is_read: boolean;
  read_at?: string;
  is_dismissed: boolean;
  action_url?: string;
  due_date?: string;
  created_at: string;
  document_title?: string;
  employee_name?: string;
}

// ============================================================================
// INTERFACES - STATS
// ============================================================================

export interface VaultDashboardStats {
  total_employees: number;
  active_vaults: number;
  total_documents: number;
  documents_this_month: number;
  total_storage_bytes: number;
  average_docs_per_employee: number;
  pending_signatures: number;
  expiring_documents_30d: number;
  gdpr_requests_pending: number;
  documents_by_type: Record<string, number>;
  recent_activity: Array<{
    id: string;
    type: string;
    description: string;
    date: string;
  }>;
}

export interface VaultEmployeeStats {
  employee_id: string;
  employee_name: string;
  vault_activated: boolean;
  activated_at?: string;
  total_documents: number;
  documents_by_type: Record<string, number>;
  total_storage_bytes: number;
  last_document_date?: string;
  last_access_date?: string;
  pending_signatures: number;
  unread_documents: number;
}

// ============================================================================
// CONFIGURATIONS
// ============================================================================

export const DOCUMENT_TYPE_CONFIG: Record<VaultDocumentType, { label: string; color: string; icon: string }> = {
  PAYSLIP: { label: 'Bulletin de paie', color: 'green', icon: 'receipt' },
  PAYSLIP_SUMMARY: { label: 'Recapitulatif annuel', color: 'green', icon: 'file-text' },
  TAX_STATEMENT: { label: 'Declaration fiscale', color: 'blue', icon: 'file-text' },
  CONTRACT: { label: 'Contrat de travail', color: 'purple', icon: 'file-signature' },
  AMENDMENT: { label: 'Avenant', color: 'purple', icon: 'file-plus' },
  TEMPORARY_CONTRACT: { label: 'CDD', color: 'purple', icon: 'clock' },
  APPRENTICESHIP: { label: 'Contrat apprentissage', color: 'purple', icon: 'graduation-cap' },
  INTERNSHIP: { label: 'Convention de stage', color: 'purple', icon: 'book-open' },
  EMPLOYMENT_CERTIFICATE: { label: 'Attestation employeur', color: 'blue', icon: 'award' },
  SALARY_CERTIFICATE: { label: 'Attestation salaire', color: 'blue', icon: 'file-check' },
  TRAINING_CERTIFICATE: { label: 'Attestation formation', color: 'blue', icon: 'award' },
  FRANCE_TRAVAIL: { label: 'Attestation France Travail', color: 'blue', icon: 'briefcase' },
  TERMINATION_LETTER: { label: 'Lettre de rupture', color: 'red', icon: 'file-x' },
  STC: { label: 'Solde de tout compte', color: 'red', icon: 'calculator' },
  WORK_CERTIFICATE: { label: 'Certificat de travail', color: 'red', icon: 'file-check' },
  PORTABILITY_NOTICE: { label: 'Notice portabilite', color: 'red', icon: 'shield' },
  MEDICAL_APTITUDE: { label: 'Aptitude medicale', color: 'orange', icon: 'heart-pulse' },
  ACCIDENT_DECLARATION: { label: 'Declaration AT', color: 'orange', icon: 'alert-triangle' },
  ID_DOCUMENT: { label: 'Piece d\'identite', color: 'gray', icon: 'id-card' },
  DIPLOMA: { label: 'Diplome', color: 'yellow', icon: 'graduation-cap' },
  DEGREE: { label: 'Titre universitaire', color: 'yellow', icon: 'award' },
  CERTIFICATION: { label: 'Certification', color: 'yellow', icon: 'badge-check' },
  RIB: { label: 'RIB', color: 'gray', icon: 'landmark' },
  VITALE_CARD: { label: 'Carte Vitale', color: 'gray', icon: 'credit-card' },
  DRIVING_LICENSE: { label: 'Permis de conduire', color: 'gray', icon: 'car' },
  EVALUATION: { label: 'Evaluation', color: 'blue', icon: 'clipboard-list' },
  WARNING: { label: 'Avertissement', color: 'red', icon: 'alert-circle' },
  PROMOTION_LETTER: { label: 'Promotion', color: 'green', icon: 'trending-up' },
  BONUS_LETTER: { label: 'Prime', color: 'green', icon: 'gift' },
  OTHER: { label: 'Autre', color: 'gray', icon: 'file' },
};

export const DOCUMENT_STATUS_CONFIG: Record<VaultDocumentStatus, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  PENDING_SIGNATURE: { label: 'En attente signature', color: 'orange' },
  PENDING_VALIDATION: { label: 'En attente validation', color: 'blue' },
  ACTIVE: { label: 'Actif', color: 'green' },
  ARCHIVED: { label: 'Archive', color: 'gray' },
  DELETED: { label: 'Supprime', color: 'red' },
};

export const SIGNATURE_STATUS_CONFIG: Record<SignatureStatus, { label: string; color: string }> = {
  NOT_REQUIRED: { label: 'Non requis', color: 'gray' },
  PENDING: { label: 'En attente', color: 'orange' },
  SIGNED_EMPLOYEE: { label: 'Signe employe', color: 'blue' },
  SIGNED_EMPLOYER: { label: 'Signe employeur', color: 'blue' },
  FULLY_SIGNED: { label: 'Signe', color: 'green' },
  REJECTED: { label: 'Refuse', color: 'red' },
  EXPIRED: { label: 'Expire', color: 'red' },
};

export const RETENTION_CONFIG: Record<RetentionPeriod, { label: string; years: number }> = {
  '5_YEARS': { label: '5 ans', years: 5 },
  '10_YEARS': { label: '10 ans', years: 10 },
  '30_YEARS': { label: '30 ans', years: 30 },
  '50_YEARS': { label: '50 ans', years: 50 },
  'LIFETIME_PLUS_5': { label: 'Vie + 5 ans', years: 70 },
  'PERMANENT': { label: 'Permanent', years: 999 },
};

export const GDPR_TYPE_CONFIG: Record<GDPRRequestType, { label: string; color: string }> = {
  ACCESS: { label: 'Acces', color: 'blue' },
  RECTIFICATION: { label: 'Rectification', color: 'orange' },
  ERASURE: { label: 'Effacement', color: 'red' },
  PORTABILITY: { label: 'Portabilite', color: 'purple' },
  RESTRICTION: { label: 'Limitation', color: 'yellow' },
  OBJECTION: { label: 'Opposition', color: 'gray' },
};

export const GDPR_STATUS_CONFIG: Record<GDPRRequestStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'orange' },
  PROCESSING: { label: 'En cours', color: 'blue' },
  COMPLETED: { label: 'Traite', color: 'green' },
  REJECTED: { label: 'Rejete', color: 'red' },
  EXPIRED: { label: 'Expire', color: 'gray' },
};

export const ALERT_TYPE_CONFIG: Record<AlertType, { label: string; color: string; icon: string }> = {
  EXPIRATION: { label: 'Expiration', color: 'orange', icon: 'clock' },
  MISSING_DOCUMENT: { label: 'Document manquant', color: 'red', icon: 'file-x' },
  SIGNATURE_PENDING: { label: 'Signature en attente', color: 'blue', icon: 'pen-tool' },
  RETENTION_END: { label: 'Fin conservation', color: 'yellow', icon: 'archive' },
  GDPR_REQUEST: { label: 'Demande RGPD', color: 'purple', icon: 'shield' },
  ACCESS_ANOMALY: { label: 'Anomalie acces', color: 'red', icon: 'alert-triangle' },
};

// ============================================================================
// HELPERS
// ============================================================================

export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} Go`;
};

export const isDocumentExpiring = (doc: VaultDocument, days: number = 30): boolean => {
  if (!doc.expiry_date) return false;
  const expiryDate = new Date(doc.expiry_date);
  const now = new Date();
  const diffTime = expiryDate.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays > 0 && diffDays <= days;
};

export const isDocumentExpired = (doc: VaultDocument): boolean => {
  if (!doc.expiry_date) return false;
  return new Date(doc.expiry_date) < new Date();
};

export const needsSignature = (doc: VaultDocument): boolean => {
  return doc.signature_status === 'PENDING' ||
         doc.signature_status === 'SIGNED_EMPLOYEE' ||
         doc.signature_status === 'SIGNED_EMPLOYER';
};

export const getDocumentTypeLabel = (type: VaultDocumentType): string => {
  return DOCUMENT_TYPE_CONFIG[type]?.label || type;
};

export const getDocumentStatusColor = (status: VaultDocumentStatus): string => {
  return DOCUMENT_STATUS_CONFIG[status]?.color || 'gray';
};
