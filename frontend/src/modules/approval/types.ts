/**
 * AZALSCORE Module - APPROVAL - Types
 * ====================================
 * Types TypeScript pour les workflows d'approbation
 */

// ============================================================================
// ENUMS
// ============================================================================

export type ApprovalType =
  | 'PURCHASE_ORDER'
  | 'EXPENSE_REPORT'
  | 'LEAVE_REQUEST'
  | 'TIMESHEET'
  | 'INVOICE'
  | 'CONTRACT'
  | 'BUDGET'
  | 'REQUISITION'
  | 'DOCUMENT'
  | 'CUSTOM';

export type WorkflowStatus = 'ACTIVE' | 'INACTIVE' | 'DRAFT' | 'ARCHIVED';

export type RequestStatus =
  | 'DRAFT'
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'APPROVED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'EXPIRED';

export type StepType = 'SINGLE' | 'ANY' | 'ALL' | 'MAJORITY' | 'SEQUENCE';

export type ApproverType = 'USER' | 'ROLE' | 'MANAGER' | 'DEPARTMENT_HEAD' | 'DYNAMIC';

export type ActionType = 'APPROVE' | 'REJECT' | 'DELEGATE' | 'ESCALATE' | 'REQUEST_INFO' | 'RETURN';

// ============================================================================
// INTERFACES
// ============================================================================

export interface Approver {
  approver_type: ApproverType;
  approver_id: string;
  approver_name: string;
  order: number;
  is_required: boolean;
  can_delegate: boolean;
}

export interface WorkflowStep {
  id: string;
  name: string;
  description?: string;
  step_type: StepType;
  order: number;
  approvers: Approver[];
  timeout_hours?: number;
  auto_approve_on_timeout: boolean;
  conditions?: Record<string, unknown>[];
}

export interface ApprovalWorkflow {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  approval_type: ApprovalType;
  status: WorkflowStatus;
  version: number;
  steps: WorkflowStep[];
  conditions?: Record<string, unknown>[];
  is_default: boolean;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface ApprovalRequest {
  id: string;
  tenant_id: string;
  workflow_id: string;
  workflow_name: string;
  approval_type: ApprovalType;
  status: RequestStatus;
  reference_type: string;
  reference_id: string;
  reference_name: string;
  requester_id: string;
  requester_name: string;
  amount?: number;
  currency?: string;
  current_step: number;
  total_steps: number;
  due_date?: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  notes?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface ApprovalAction {
  id: string;
  request_id: string;
  step_id: string;
  action_type: ActionType;
  actor_id: string;
  actor_name: string;
  comment?: string;
  delegated_to_id?: string;
  delegated_to_name?: string;
  created_at: string;
}

export interface PendingApproval {
  request: ApprovalRequest;
  step: WorkflowStep;
  can_approve: boolean;
  can_delegate: boolean;
  deadline?: string;
}

export interface ApprovalStats {
  pending_count: number;
  approved_today: number;
  rejected_today: number;
  avg_approval_time_hours: number;
  overdue_count: number;
}

// ============================================================================
// CONFIGURATION
// ============================================================================

export const APPROVAL_TYPE_CONFIG: Record<ApprovalType, { label: string; color: string; icon: string }> = {
  PURCHASE_ORDER: { label: 'Commande achat', color: 'blue', icon: 'shopping-cart' },
  EXPENSE_REPORT: { label: 'Note de frais', color: 'green', icon: 'receipt' },
  LEAVE_REQUEST: { label: 'Demande conge', color: 'purple', icon: 'calendar' },
  TIMESHEET: { label: 'Feuille de temps', color: 'cyan', icon: 'clock' },
  INVOICE: { label: 'Facture', color: 'orange', icon: 'file-text' },
  CONTRACT: { label: 'Contrat', color: 'red', icon: 'file-signature' },
  BUDGET: { label: 'Budget', color: 'yellow', icon: 'wallet' },
  REQUISITION: { label: 'Demande achat', color: 'indigo', icon: 'clipboard-list' },
  DOCUMENT: { label: 'Document', color: 'gray', icon: 'file' },
  CUSTOM: { label: 'Personnalise', color: 'pink', icon: 'settings' },
};

export const REQUEST_STATUS_CONFIG: Record<RequestStatus, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  PENDING: { label: 'En attente', color: 'orange' },
  IN_PROGRESS: { label: 'En cours', color: 'blue' },
  APPROVED: { label: 'Approuve', color: 'green' },
  REJECTED: { label: 'Rejete', color: 'red' },
  CANCELLED: { label: 'Annule', color: 'gray' },
  EXPIRED: { label: 'Expire', color: 'purple' },
};

export const WORKFLOW_STATUS_CONFIG: Record<WorkflowStatus, { label: string; color: string }> = {
  ACTIVE: { label: 'Actif', color: 'green' },
  INACTIVE: { label: 'Inactif', color: 'gray' },
  DRAFT: { label: 'Brouillon', color: 'orange' },
  ARCHIVED: { label: 'Archive', color: 'purple' },
};

export const STEP_TYPE_CONFIG: Record<StepType, { label: string; description: string }> = {
  SINGLE: { label: 'Unique', description: 'Un seul approbateur requis' },
  ANY: { label: 'Un parmi', description: 'Au moins un approbateur' },
  ALL: { label: 'Tous', description: 'Tous les approbateurs requis' },
  MAJORITY: { label: 'Majorite', description: 'Majorite des approbateurs' },
  SEQUENCE: { label: 'Sequence', description: 'Approbation en sequence' },
};
