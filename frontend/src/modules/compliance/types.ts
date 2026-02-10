/**
 * AZALSCORE Module - Compliance - Types
 * Types, constantes et helpers pour le module conformite
 */

// ============================================================================
// TYPES PRINCIPAUX
// ============================================================================

export interface Policy {
  id: string;
  code: string;
  name: string;
  description?: string;
  type: PolicyType;
  version: string;
  status: PolicyStatus;
  effective_date?: string;
  review_date?: string;
  content?: string;
  is_mandatory: boolean;
  owner?: string;
  approver?: string;
  approved_at?: string;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
}

export type PolicyType = 'SECURITY' | 'PRIVACY' | 'DATA_RETENTION' | 'ACCESS_CONTROL' | 'OTHER';
export type PolicyStatus = 'DRAFT' | 'ACTIVE' | 'ARCHIVED';

export interface Audit {
  id: string;
  code: string;
  name: string;
  description?: string;
  type: AuditType;
  status: AuditStatus;
  scope?: string;
  objectives?: string;
  auditor?: string;
  auditor_company?: string;
  lead_auditor?: string;
  audit_team?: string[];
  planned_date?: string;
  start_date?: string;
  end_date?: string;
  completed_date?: string;
  findings_count: number;
  critical_findings: number;
  major_findings?: number;
  minor_findings?: number;
  observations?: number;
  score?: number;
  report_url?: string;
  report_date?: string;
  next_audit_date?: string;
  action_plan_status?: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED';
  action_plan_progress?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
  created_by_name?: string;
  findings?: AuditFinding[];
  documents?: AuditDocument[];
  history?: AuditHistoryEntry[];
}

export type AuditType = 'INTERNAL' | 'EXTERNAL' | 'REGULATORY';
export type AuditStatus = 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export interface AuditFinding {
  id: string;
  audit_id: string;
  code: string;
  title: string;
  description: string;
  severity: FindingSeverity;
  category?: string;
  affected_area?: string;
  root_cause?: string;
  recommendation?: string;
  status: FindingStatus;
  due_date?: string;
  closed_date?: string;
  assigned_to?: string;
  evidence?: string;
  created_at: string;
}

export type FindingSeverity = 'CRITICAL' | 'MAJOR' | 'MINOR' | 'OBSERVATION';
export type FindingStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED' | 'ACCEPTED';

export interface AuditDocument {
  id: string;
  name: string;
  type: string;
  size: number;
  url?: string;
  uploaded_at: string;
  uploaded_by?: string;
}

export interface AuditHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_name?: string;
  details?: string;
  old_status?: string;
  new_status?: string;
}

export interface GDPRRequest {
  id: string;
  reference: string;
  type: GDPRRequestType;
  requester_name: string;
  requester_email: string;
  requester_phone?: string;
  status: GDPRRequestStatus;
  request_date: string;
  due_date: string;
  completed_date?: string;
  assigned_to?: string;
  notes?: string;
  data_categories?: string[];
  response_sent?: boolean;
  response_date?: string;
  created_at: string;
  updated_at: string;
}

export type GDPRRequestType = 'ACCESS' | 'RECTIFICATION' | 'ERASURE' | 'PORTABILITY' | 'OBJECTION' | 'RESTRICTION';
export type GDPRRequestStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED';

export interface Consent {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  consent_type: ConsentType;
  status: boolean;
  given_at?: string;
  withdrawn_at?: string;
  source: string;
  version: string;
  ip_address?: string;
}

export type ConsentType = 'MARKETING' | 'ANALYTICS' | 'THIRD_PARTY' | 'NEWSLETTER' | 'TERMS';

export interface ComplianceStats {
  active_policies: number;
  pending_reviews: number;
  audits_year: number;
  open_findings: number;
  gdpr_requests_pending: number;
  gdpr_requests_completed: number;
  compliance_score: number;
  consent_rate: number;
}

// ============================================================================
// CONFIGURATIONS DE STATUT
// ============================================================================

export const POLICY_TYPE_CONFIG: Record<PolicyType, { label: string; color: string }> = {
  SECURITY: { label: 'Securite', color: 'red' },
  PRIVACY: { label: 'Confidentialite', color: 'purple' },
  DATA_RETENTION: { label: 'Conservation donnees', color: 'blue' },
  ACCESS_CONTROL: { label: 'Controle d\'acces', color: 'orange' },
  OTHER: { label: 'Autre', color: 'gray' }
};

export const POLICY_STATUS_CONFIG: Record<PolicyStatus, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  ACTIVE: { label: 'Active', color: 'green' },
  ARCHIVED: { label: 'Archivee', color: 'gray' }
};

export const AUDIT_TYPE_CONFIG: Record<AuditType, { label: string; color: string }> = {
  INTERNAL: { label: 'Interne', color: 'blue' },
  EXTERNAL: { label: 'Externe', color: 'purple' },
  REGULATORY: { label: 'Reglementaire', color: 'red' }
};

export const AUDIT_STATUS_CONFIG: Record<AuditStatus, { label: string; color: string }> = {
  PLANNED: { label: 'Planifie', color: 'blue' },
  IN_PROGRESS: { label: 'En cours', color: 'orange' },
  COMPLETED: { label: 'Termine', color: 'green' },
  CANCELLED: { label: 'Annule', color: 'red' }
};

export const FINDING_SEVERITY_CONFIG: Record<FindingSeverity, { label: string; color: string }> = {
  CRITICAL: { label: 'Critique', color: 'red' },
  MAJOR: { label: 'Majeur', color: 'orange' },
  MINOR: { label: 'Mineur', color: 'yellow' },
  OBSERVATION: { label: 'Observation', color: 'blue' }
};

export const FINDING_STATUS_CONFIG: Record<FindingStatus, { label: string; color: string }> = {
  OPEN: { label: 'Ouvert', color: 'red' },
  IN_PROGRESS: { label: 'En cours', color: 'orange' },
  RESOLVED: { label: 'Resolu', color: 'blue' },
  CLOSED: { label: 'Cloture', color: 'green' },
  ACCEPTED: { label: 'Accepte', color: 'gray' }
};

export const GDPR_TYPE_CONFIG: Record<GDPRRequestType, { label: string; color: string }> = {
  ACCESS: { label: 'Acces', color: 'blue' },
  RECTIFICATION: { label: 'Rectification', color: 'orange' },
  ERASURE: { label: 'Effacement', color: 'red' },
  PORTABILITY: { label: 'Portabilite', color: 'purple' },
  OBJECTION: { label: 'Opposition', color: 'yellow' },
  RESTRICTION: { label: 'Limitation', color: 'gray' }
};

export const GDPR_STATUS_CONFIG: Record<GDPRRequestStatus, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'orange' },
  IN_PROGRESS: { label: 'En cours', color: 'blue' },
  COMPLETED: { label: 'Traitee', color: 'green' },
  REJECTED: { label: 'Rejetee', color: 'red' }
};

export const CONSENT_TYPE_CONFIG: Record<ConsentType, { label: string; color: string }> = {
  MARKETING: { label: 'Marketing', color: 'purple' },
  ANALYTICS: { label: 'Analytics', color: 'blue' },
  THIRD_PARTY: { label: 'Tiers', color: 'orange' },
  NEWSLETTER: { label: 'Newsletter', color: 'green' },
  TERMS: { label: 'CGU', color: 'gray' }
};

// ============================================================================
// HELPERS DE FORMATAGE
// ============================================================================

export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
};

// ============================================================================
// HELPERS METIER
// ============================================================================

export const isAuditCompleted = (audit: Audit): boolean => {
  return audit.status === 'COMPLETED';
};

export const isAuditInProgress = (audit: Audit): boolean => {
  return audit.status === 'IN_PROGRESS';
};

export const isAuditPlanned = (audit: Audit): boolean => {
  return audit.status === 'PLANNED';
};

export const hasOpenFindings = (audit: Audit): boolean => {
  return (audit.critical_findings || 0) > 0 ||
         (audit.major_findings || 0) > 0 ||
         (audit.minor_findings || 0) > 0;
};

export const hasCriticalFindings = (audit: Audit): boolean => {
  return (audit.critical_findings || 0) > 0;
};

export const getAuditScoreColor = (score: number): string => {
  if (score >= 80) return 'green';
  if (score >= 60) return 'orange';
  return 'red';
};

export const getNextAuditStatus = (status: AuditStatus): AuditStatus | null => {
  switch (status) {
    case 'PLANNED':
      return 'IN_PROGRESS';
    case 'IN_PROGRESS':
      return 'COMPLETED';
    default:
      return null;
  }
};

export const isFindingOpen = (finding: AuditFinding): boolean => {
  return finding.status === 'OPEN' || finding.status === 'IN_PROGRESS';
};

export const isFindingCritical = (finding: AuditFinding): boolean => {
  return finding.severity === 'CRITICAL';
};

export const isGDPRRequestOverdue = (request: GDPRRequest): boolean => {
  return new Date(request.due_date) < new Date() &&
         request.status !== 'COMPLETED' &&
         request.status !== 'REJECTED';
};
