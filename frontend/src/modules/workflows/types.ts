/**
 * AZALSCORE Module - Workflows (BPM) Types
 * Types TypeScript pour le module de workflows
 */

// ============================================================================
// ENUMS
// ============================================================================

export type WorkflowStatus =
  | 'draft'
  | 'active'
  | 'suspended'
  | 'archived';

export type InstanceStatus =
  | 'pending'
  | 'running'
  | 'waiting'
  | 'completed'
  | 'cancelled'
  | 'failed'
  | 'suspended';

export type StepType =
  | 'start'
  | 'end'
  | 'task'
  | 'approval'
  | 'decision'
  | 'parallel_split'
  | 'parallel_join'
  | 'inclusive_join'
  | 'timer'
  | 'subprocess'
  | 'script'
  | 'notification'
  | 'integration';

export type TaskStatus =
  | 'pending'
  | 'assigned'
  | 'in_progress'
  | 'completed'
  | 'rejected'
  | 'cancelled'
  | 'delegated'
  | 'escalated';

export type ApprovalType =
  | 'single'
  | 'sequential'
  | 'parallel'
  | 'quorum'
  | 'first_response';

export type ConditionOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'contains'
  | 'in_list'
  | 'is_true'
  | 'is_false'
  | 'is_null'
  | 'is_not_null';

// ============================================================================
// CONDITION & TRANSITION
// ============================================================================

export interface Condition {
  field: string;
  operator: ConditionOperator;
  value: unknown;
  logic?: 'and' | 'or';
}

export interface Transition {
  transition_id: string;
  from_step_id: string;
  to_step_id: string;
  name?: string;
  conditions: Condition[];
  is_default: boolean;
  priority: number;
}

// ============================================================================
// ASSIGNMENT & ESCALATION
// ============================================================================

export interface AssignmentRule {
  rule_type: 'user' | 'role' | 'group' | 'expression' | 'supervisor';
  value: string;
  fallback?: string;
}

export interface EscalationRule {
  after_hours: number;
  escalate_to: AssignmentRule;
  notification_template?: string;
  max_escalations: number;
}

// ============================================================================
// STEP
// ============================================================================

export interface Step {
  step_id: string;
  name: string;
  step_type: StepType;
  description?: string;
  assignment_rules: AssignmentRule[];
  approval_type?: ApprovalType;
  approvers: string[];
  quorum_percent?: number;
  allow_delegation: boolean;
  allow_rejection: boolean;
  due_hours?: number;
  reminder_hours?: number;
  escalation_rules: EscalationRule[];
  on_enter_actions: Record<string, unknown>[];
  on_exit_actions: Record<string, unknown>[];
  on_complete_actions: Record<string, unknown>[];
  script_code?: string;
  script_language?: string;
  timer_duration_hours?: number;
  timer_expression?: string;
  subprocess_workflow_id?: string;
  form_definition?: Record<string, unknown>;
  instructions?: string;
  metadata: Record<string, unknown>;
}

// ============================================================================
// WORKFLOW DEFINITION
// ============================================================================

export interface WorkflowDefinition {
  workflow_id: string;
  tenant_id: string;
  name: string;
  description: string;
  version: number;
  status: WorkflowStatus;
  steps: Step[];
  transitions: Transition[];
  start_step_id?: string;
  end_step_ids: string[];
  variables: Record<string, unknown>;
  input_schema?: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
  triggers: Record<string, unknown>[];
  sla_hours?: number;
  created_at: string;
  created_by?: string;
  updated_at?: string;
  category: string;
  tags: string[];
}

export interface WorkflowCreate {
  name: string;
  description: string;
  category?: string;
  sla_hours?: number;
  input_schema?: Record<string, unknown>;
  tags?: string[];
}

export interface WorkflowUpdate {
  name?: string;
  description?: string;
  category?: string;
  sla_hours?: number;
  tags?: string[];
}

// ============================================================================
// TASK INSTANCE
// ============================================================================

export interface TaskInstance {
  task_id: string;
  instance_id: string;
  step_id: string;
  status: TaskStatus;
  assigned_to?: string;
  assigned_role?: string;
  assigned_at?: string;
  delegated_by?: string;
  delegated_at?: string;
  original_assignee?: string;
  due_at?: string;
  reminded_at?: string;
  escalation_level: number;
  outcome?: string;
  decision_data: Record<string, unknown>;
  comments?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  completed_by?: string;
  metadata: Record<string, unknown>;
}

// ============================================================================
// STEP EXECUTION
// ============================================================================

export interface StepExecution {
  execution_id: string;
  instance_id: string;
  step_id: string;
  step_name: string;
  step_type: StepType;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'waiting';
  tasks: TaskInstance[];
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  is_parallel_branch: boolean;
  parallel_branch_id?: string;
}

// ============================================================================
// WORKFLOW INSTANCE
// ============================================================================

export interface WorkflowInstance {
  instance_id: string;
  tenant_id: string;
  workflow_id: string;
  workflow_name: string;
  version: number;
  status: InstanceStatus;
  context: Record<string, unknown>;
  variables: Record<string, unknown>;
  current_step_ids: string[];
  step_executions: StepExecution[];
  reference_type?: string;
  reference_id?: string;
  reference_name?: string;
  initiated_by: string;
  initiated_at: string;
  due_at?: string;
  sla_breached: boolean;
  completed_at?: string;
  outcome?: string;
  metadata: Record<string, unknown>;
  tags: string[];
}

export interface InstanceCreate {
  workflow_id: string;
  context: Record<string, unknown>;
  reference_type?: string;
  reference_id?: string;
  reference_name?: string;
  tags?: string[];
}

// ============================================================================
// WORKFLOW HISTORY
// ============================================================================

export interface WorkflowHistory {
  history_id: string;
  instance_id: string;
  event_type: string;
  step_id?: string;
  task_id?: string;
  actor?: string;
  details: Record<string, unknown>;
  timestamp: string;
}

// ============================================================================
// TASK ACTIONS
// ============================================================================

export interface TaskCompleteData {
  outcome: string;
  decision_data?: Record<string, unknown>;
  comments?: string;
}

export interface TaskDelegateData {
  delegate_to: string;
  comments?: string;
}

// ============================================================================
// STATS
// ============================================================================

export interface WorkflowStats {
  total_workflows: number;
  active_workflows: number;
  total_instances: number;
  running_instances: number;
  waiting_instances: number;
  completed_today: number;
  failed_today: number;
  avg_completion_time_hours: number;
  sla_breach_rate: number;
  pending_tasks: number;
}

// ============================================================================
// LIST RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export type WorkflowListResponse = PaginatedResponse<WorkflowDefinition>;
export type InstanceListResponse = PaginatedResponse<WorkflowInstance>;
export type TaskListResponse = PaginatedResponse<TaskInstance>;

// ============================================================================
// FILTERS
// ============================================================================

export interface WorkflowFilters {
  status?: WorkflowStatus;
  category?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface InstanceFilters {
  workflow_id?: string;
  status?: InstanceStatus;
  initiated_by?: string;
  reference_type?: string;
  reference_id?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
}

export interface TaskFilters {
  status?: TaskStatus;
  assigned_to?: string;
  workflow_id?: string;
  page?: number;
  page_size?: number;
}

// ============================================================================
// CONFIG CONSTANTS
// ============================================================================

export const WORKFLOW_STATUS_CONFIG: Record<WorkflowStatus, { label: string; color: string }> = {
  draft: { label: 'Brouillon', color: 'gray' },
  active: { label: 'Actif', color: 'green' },
  suspended: { label: 'Suspendu', color: 'yellow' },
  archived: { label: 'Archive', color: 'red' },
};

export const INSTANCE_STATUS_CONFIG: Record<InstanceStatus, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'gray' },
  running: { label: 'En cours', color: 'blue' },
  waiting: { label: 'En attente action', color: 'yellow' },
  completed: { label: 'Termine', color: 'green' },
  cancelled: { label: 'Annule', color: 'red' },
  failed: { label: 'Echoue', color: 'red' },
  suspended: { label: 'Suspendu', color: 'orange' },
};

export const TASK_STATUS_CONFIG: Record<TaskStatus, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'gray' },
  assigned: { label: 'Assigne', color: 'blue' },
  in_progress: { label: 'En cours', color: 'orange' },
  completed: { label: 'Termine', color: 'green' },
  rejected: { label: 'Rejete', color: 'red' },
  cancelled: { label: 'Annule', color: 'gray' },
  delegated: { label: 'Delegue', color: 'purple' },
  escalated: { label: 'Escalade', color: 'red' },
};

export const STEP_TYPE_CONFIG: Record<StepType, { label: string; icon: string }> = {
  start: { label: 'Debut', icon: 'Play' },
  end: { label: 'Fin', icon: 'Square' },
  task: { label: 'Tache', icon: 'CheckSquare' },
  approval: { label: 'Approbation', icon: 'UserCheck' },
  decision: { label: 'Decision', icon: 'GitBranch' },
  parallel_split: { label: 'Fork', icon: 'GitFork' },
  parallel_join: { label: 'Join AND', icon: 'GitMerge' },
  inclusive_join: { label: 'Join OR', icon: 'GitMerge' },
  timer: { label: 'Timer', icon: 'Clock' },
  subprocess: { label: 'Sous-processus', icon: 'Workflow' },
  script: { label: 'Script', icon: 'Code' },
  notification: { label: 'Notification', icon: 'Bell' },
  integration: { label: 'Integration', icon: 'Plug' },
};
