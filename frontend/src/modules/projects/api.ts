/**
 * AZALSCORE - Projects API
 * ========================
 * Client API typé pour la gestion de projets
 */

import { api } from '@core/api-client';

// ============================================================================
// HELPERS
// ============================================================================

function buildQueryString(params: Record<string, string | number | boolean | undefined | null>): string {
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
// ENUMS
// ============================================================================

export type ProjectStatus = 'DRAFT' | 'PLANNING' | 'ACTIVE' | 'ON_HOLD' | 'COMPLETED' | 'CANCELLED' | 'ARCHIVED';
export type ProjectPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'REVIEW' | 'BLOCKED' | 'DONE' | 'CANCELLED';
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
export type MilestoneStatus = 'PENDING' | 'IN_PROGRESS' | 'ACHIEVED' | 'MISSED' | 'CANCELLED';
export type RiskStatus = 'IDENTIFIED' | 'ANALYZING' | 'MITIGATING' | 'MONITORING' | 'OCCURRED' | 'CLOSED';
export type RiskProbability = 'RARE' | 'UNLIKELY' | 'POSSIBLE' | 'LIKELY' | 'ALMOST_CERTAIN';
export type RiskImpact = 'NEGLIGIBLE' | 'MINOR' | 'MODERATE' | 'MAJOR' | 'SEVERE';
export type IssueStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED' | 'DEFERRED';
export type IssuePriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type TimeEntryStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'INVOICED';
export type ExpenseStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'PAID';
export type TeamMemberRole = 'OWNER' | 'MANAGER' | 'LEAD' | 'MEMBER' | 'CONTRIBUTOR' | 'VIEWER';
export type BudgetType = 'FIXED' | 'TIME_AND_MATERIALS' | 'MIXED';

// ============================================================================
// TYPES - PROJETS
// ============================================================================

export interface ProjectCreate {
  code: string;
  name: string;
  description?: string | null;
  category?: string | null;
  tags?: string[];
  priority?: ProjectPriority;
  planned_start_date?: string | null;
  planned_end_date?: string | null;
  project_manager_id?: string | null;
  sponsor_id?: string | null;
  customer_id?: string | null;
  budget_type?: BudgetType | null;
  planned_budget?: number;
  currency?: string;
  planned_hours?: number;
  is_billable?: boolean;
  billing_rate?: number | null;
  parent_project_id?: string | null;
  template_id?: string | null;
  settings?: Record<string, unknown>;
}

export interface ProjectUpdate {
  name?: string;
  description?: string | null;
  category?: string | null;
  tags?: string[];
  status?: ProjectStatus;
  priority?: ProjectPriority;
  planned_start_date?: string | null;
  planned_end_date?: string | null;
  actual_start_date?: string | null;
  actual_end_date?: string | null;
  project_manager_id?: string | null;
  sponsor_id?: string | null;
  customer_id?: string | null;
  planned_budget?: number | null;
  planned_hours?: number | null;
  progress_percent?: number | null;
  health_status?: string | null;
  is_billable?: boolean;
  billing_rate?: number | null;
  settings?: Record<string, unknown>;
  is_active?: boolean;
}

export interface Project {
  id: string;
  code: string;
  name: string;
  description: string | null;
  category: string | null;
  tags: string[];
  status: ProjectStatus;
  priority: ProjectPriority;
  planned_start_date: string | null;
  planned_end_date: string | null;
  actual_start_date: string | null;
  actual_end_date: string | null;
  project_manager_id: string | null;
  sponsor_id: string | null;
  customer_id: string | null;
  budget_type: BudgetType | null;
  planned_budget: number;
  actual_cost: number;
  currency: string;
  planned_hours: number;
  actual_hours: number;
  progress_percent: number;
  health_status: string | null;
  parent_project_id: string | null;
  is_billable: boolean;
  billing_rate: number | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface ProjectList {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProjectStats {
  tasks_total: number;
  tasks_completed: number;
  tasks_in_progress: number;
  tasks_blocked: number;
  tasks_overdue: number;
  milestones_total: number;
  milestones_achieved: number;
  milestones_overdue: number;
  risks_total: number;
  risks_open: number;
  risks_high: number;
  issues_total: number;
  issues_open: number;
  issues_critical: number;
  team_size: number;
  hours_planned: number;
  hours_actual: number;
  hours_remaining: number;
  budget_planned: number;
  budget_actual: number;
  budget_remaining: number;
}

// ============================================================================
// TYPES - PHASES
// ============================================================================

export interface PhaseCreate {
  name: string;
  description?: string | null;
  order?: number;
  color?: string | null;
  planned_start_date?: string | null;
  planned_end_date?: string | null;
  planned_hours?: number;
  planned_budget?: number;
}

export interface PhaseUpdate {
  name?: string;
  description?: string | null;
  order?: number;
  color?: string | null;
  planned_start_date?: string | null;
  planned_end_date?: string | null;
  actual_start_date?: string | null;
  actual_end_date?: string | null;
  status?: TaskStatus;
  progress_percent?: number;
}

export interface Phase {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  order: number;
  color: string | null;
  planned_start_date: string | null;
  planned_end_date: string | null;
  actual_start_date: string | null;
  actual_end_date: string | null;
  progress_percent: number;
  status: TaskStatus;
  planned_hours: number;
  actual_hours: number;
  planned_budget: number;
  actual_cost: number;
  created_at: string;
}

// ============================================================================
// TYPES - TÂCHES
// ============================================================================

export interface TaskDependencyCreate {
  predecessor_id: string;
  dependency_type?: string;
  lag_days?: number;
}

export interface TaskCreate {
  name: string;
  description?: string | null;
  task_type?: string | null;
  tags?: string[];
  phase_id?: string | null;
  parent_task_id?: string | null;
  code?: string | null;
  priority?: TaskPriority;
  planned_start_date?: string | null;
  planned_end_date?: string | null;
  due_date?: string | null;
  assignee_id?: string | null;
  estimated_hours?: number;
  order?: number;
  wbs_code?: string | null;
  is_milestone?: boolean;
  is_critical?: boolean;
  is_billable?: boolean;
  dependencies?: TaskDependencyCreate[];
}

export interface TaskUpdate {
  name?: string;
  description?: string | null;
  phase_id?: string | null;
  parent_task_id?: string | null;
  task_type?: string | null;
  tags?: string[];
  status?: TaskStatus;
  priority?: TaskPriority;
  planned_start_date?: string | null;
  planned_end_date?: string | null;
  due_date?: string | null;
  assignee_id?: string | null;
  estimated_hours?: number;
  remaining_hours?: number;
  progress_percent?: number;
  order?: number;
  is_critical?: boolean;
  is_billable?: boolean;
}

export interface Task {
  id: string;
  project_id: string;
  phase_id: string | null;
  parent_task_id: string | null;
  code: string | null;
  name: string;
  description: string | null;
  task_type: string | null;
  tags: string[];
  status: TaskStatus;
  priority: TaskPriority;
  planned_start_date: string | null;
  planned_end_date: string | null;
  actual_start_date: string | null;
  actual_end_date: string | null;
  due_date: string | null;
  assignee_id: string | null;
  reporter_id: string | null;
  estimated_hours: number;
  actual_hours: number;
  remaining_hours: number;
  progress_percent: number;
  order: number;
  wbs_code: string | null;
  is_milestone: boolean;
  is_critical: boolean;
  is_billable: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface TaskList {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
}

// ============================================================================
// TYPES - JALONS
// ============================================================================

export interface MilestoneCreate {
  name: string;
  description?: string | null;
  target_date: string;
  is_key_milestone?: boolean;
  is_customer_visible?: boolean;
  phase_id?: string | null;
  deliverables?: string[];
  acceptance_criteria?: string | null;
}

export interface MilestoneUpdate {
  name?: string;
  description?: string | null;
  target_date?: string;
  actual_date?: string | null;
  status?: MilestoneStatus;
  is_key_milestone?: boolean;
  is_customer_visible?: boolean;
  deliverables?: string[];
  acceptance_criteria?: string | null;
  validation_notes?: string | null;
}

export interface Milestone {
  id: string;
  project_id: string;
  phase_id: string | null;
  name: string;
  description: string | null;
  target_date: string;
  actual_date: string | null;
  status: MilestoneStatus;
  is_key_milestone: boolean;
  is_customer_visible: boolean;
  deliverables: string[];
  acceptance_criteria: string | null;
  validated_by: string | null;
  validated_at: string | null;
  validation_notes: string | null;
  created_by: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - ÉQUIPE
// ============================================================================

export interface TeamMemberCreate {
  user_id: string;
  role?: TeamMemberRole;
  role_description?: string | null;
  employee_id?: string | null;
  allocation_percent?: number;
  start_date?: string | null;
  end_date?: string | null;
  hourly_rate?: number | null;
  daily_rate?: number | null;
  is_billable?: boolean;
  can_log_time?: boolean;
  can_view_budget?: boolean;
  can_manage_tasks?: boolean;
  can_approve_time?: boolean;
}

export interface TeamMemberUpdate {
  role?: TeamMemberRole;
  role_description?: string | null;
  allocation_percent?: number;
  start_date?: string | null;
  end_date?: string | null;
  hourly_rate?: number | null;
  daily_rate?: number | null;
  is_billable?: boolean;
  can_log_time?: boolean;
  can_view_budget?: boolean;
  can_manage_tasks?: boolean;
  can_approve_time?: boolean;
  is_active?: boolean;
}

export interface TeamMember {
  id: string;
  project_id: string;
  user_id: string;
  employee_id: string | null;
  role: TeamMemberRole;
  role_description: string | null;
  allocation_percent: number;
  start_date: string | null;
  end_date: string | null;
  hourly_rate: number | null;
  daily_rate: number | null;
  is_billable: boolean;
  can_log_time: boolean;
  can_view_budget: boolean;
  can_manage_tasks: boolean;
  can_approve_time: boolean;
  is_active: boolean;
  created_at: string;
}

// ============================================================================
// TYPES - RISQUES
// ============================================================================

export interface RiskCreate {
  title: string;
  description?: string | null;
  category?: string | null;
  probability: RiskProbability;
  impact: RiskImpact;
  code?: string | null;
  owner_id?: string | null;
  response_strategy?: string | null;
  mitigation_plan?: string | null;
  contingency_plan?: string | null;
  triggers?: string[];
  estimated_impact_min?: number | null;
  estimated_impact_max?: number | null;
  review_date?: string | null;
}

export interface RiskUpdate {
  title?: string;
  description?: string | null;
  category?: string | null;
  status?: RiskStatus;
  probability?: RiskProbability;
  impact?: RiskImpact;
  owner_id?: string | null;
  response_strategy?: string | null;
  mitigation_plan?: string | null;
  contingency_plan?: string | null;
  triggers?: string[];
  monitoring_notes?: string | null;
  review_date?: string | null;
}

export interface Risk {
  id: string;
  project_id: string;
  code: string | null;
  title: string;
  description: string | null;
  category: string | null;
  status: RiskStatus;
  probability: RiskProbability;
  impact: RiskImpact;
  risk_score: number | null;
  estimated_impact_min: number | null;
  estimated_impact_max: number | null;
  identified_date: string;
  review_date: string | null;
  occurred_date: string | null;
  closed_date: string | null;
  owner_id: string | null;
  response_strategy: string | null;
  mitigation_plan: string | null;
  contingency_plan: string | null;
  triggers: string[];
  monitoring_notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - ISSUES
// ============================================================================

export interface IssueCreate {
  title: string;
  description?: string | null;
  category?: string | null;
  priority?: IssuePriority;
  task_id?: string | null;
  code?: string | null;
  assignee_id?: string | null;
  due_date?: string | null;
  impact_description?: string | null;
  affected_areas?: string[];
  related_risk_id?: string | null;
}

export interface IssueUpdate {
  title?: string;
  description?: string | null;
  category?: string | null;
  status?: IssueStatus;
  priority?: IssuePriority;
  assignee_id?: string | null;
  due_date?: string | null;
  impact_description?: string | null;
  affected_areas?: string[];
  resolution?: string | null;
  resolution_type?: string | null;
}

export interface Issue {
  id: string;
  project_id: string;
  task_id: string | null;
  code: string | null;
  title: string;
  description: string | null;
  category: string | null;
  status: IssueStatus;
  priority: IssuePriority;
  reporter_id: string | null;
  assignee_id: string | null;
  reported_date: string;
  due_date: string | null;
  resolved_date: string | null;
  closed_date: string | null;
  impact_description: string | null;
  affected_areas: string[];
  resolution: string | null;
  resolution_type: string | null;
  is_escalated: boolean;
  related_risk_id: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - TIME ENTRIES
// ============================================================================

export interface TimeEntryCreate {
  date: string;
  hours: number;
  description?: string | null;
  activity_type?: string | null;
  task_id?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  is_billable?: boolean;
  is_overtime?: boolean;
}

export interface TimeEntry {
  id: string;
  project_id: string;
  task_id: string | null;
  user_id: string;
  employee_id: string | null;
  date: string;
  hours: number;
  description: string | null;
  activity_type: string | null;
  start_time: string | null;
  end_time: string | null;
  status: TimeEntryStatus;
  is_billable: boolean;
  billing_rate: number | null;
  billing_amount: number | null;
  is_invoiced: boolean;
  is_overtime: boolean;
  approved_by: string | null;
  approved_at: string | null;
  rejection_reason: string | null;
  created_at: string;
}

export interface TimeEntryList {
  items: TimeEntry[];
  total: number;
  total_hours: number;
  billable_hours: number;
}

// ============================================================================
// TYPES - EXPENSES
// ============================================================================

export interface ExpenseCreate {
  description: string;
  category?: string | null;
  amount: number;
  expense_date: string;
  task_id?: string | null;
  budget_line_id?: string | null;
  reference?: string | null;
  currency?: string;
  quantity?: number;
  unit_price?: number | null;
  vendor?: string | null;
  is_billable?: boolean;
  receipt_url?: string | null;
  attachments?: string[];
}

export interface Expense {
  id: string;
  project_id: string;
  task_id: string | null;
  budget_line_id: string | null;
  reference: string | null;
  description: string;
  category: string | null;
  amount: number;
  currency: string;
  quantity: number;
  unit_price: number | null;
  expense_date: string;
  due_date: string | null;
  paid_date: string | null;
  status: ExpenseStatus;
  submitted_by: string | null;
  vendor: string | null;
  approved_by: string | null;
  approved_at: string | null;
  is_billable: boolean;
  is_invoiced: boolean;
  receipt_url: string | null;
  attachments: string[];
  created_at: string;
}

// ============================================================================
// TYPES - DOCUMENTS
// ============================================================================

export interface DocumentCreate {
  name: string;
  description?: string | null;
  category?: string | null;
  file_name?: string | null;
  file_url?: string | null;
  file_size?: number | null;
  file_type?: string | null;
  version?: string;
  is_public?: boolean;
  access_level?: string;
  tags?: string[];
}

export interface Document {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  category: string | null;
  file_name: string | null;
  file_url: string | null;
  file_size: number | null;
  file_type: string | null;
  version: string;
  is_latest: boolean;
  is_public: boolean;
  access_level: string;
  uploaded_by: string | null;
  created_at: string;
  tags: string[];
}

// ============================================================================
// TYPES - BUDGET
// ============================================================================

export interface BudgetLineCreate {
  code?: string | null;
  name: string;
  description?: string | null;
  category?: string | null;
  budget_amount?: number;
  phase_id?: string | null;
  quantity?: number | null;
  unit?: string | null;
  unit_price?: number | null;
  order?: number;
  parent_line_id?: string | null;
  account_code?: string | null;
}

export interface BudgetCreate {
  name: string;
  description?: string | null;
  fiscal_year?: string | null;
  budget_type?: BudgetType;
  total_budget?: number;
  currency?: string;
  start_date?: string | null;
  end_date?: string | null;
  lines?: BudgetLineCreate[];
}

export interface BudgetLine {
  id: string;
  budget_id: string;
  phase_id: string | null;
  code: string | null;
  name: string;
  description: string | null;
  category: string | null;
  budget_amount: number;
  committed_amount: number;
  actual_amount: number;
  forecast_amount: number;
  quantity: number | null;
  unit: string | null;
  unit_price: number | null;
  order: number;
  parent_line_id: string | null;
  account_code: string | null;
  created_at: string;
}

export interface Budget {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  fiscal_year: string | null;
  budget_type: BudgetType;
  version: string;
  total_budget: number;
  total_committed: number;
  total_actual: number;
  total_forecast: number;
  currency: string;
  is_approved: boolean;
  approved_by: string | null;
  approved_at: string | null;
  is_active: boolean;
  is_locked: boolean;
  start_date: string | null;
  end_date: string | null;
  lines: BudgetLine[];
  created_by: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - TEMPLATES
// ============================================================================

export interface TemplateCreate {
  name: string;
  description?: string | null;
  category?: string | null;
  default_priority?: ProjectPriority;
  default_budget_type?: BudgetType | null;
  estimated_duration_days?: number | null;
  phases_template?: Record<string, unknown>[];
  tasks_template?: Record<string, unknown>[];
  milestones_template?: Record<string, unknown>[];
  risks_template?: Record<string, unknown>[];
  roles_template?: Record<string, unknown>[];
  budget_template?: Record<string, unknown>[];
  checklist?: string[];
  settings?: Record<string, unknown>;
  is_public?: boolean;
}

export interface Template {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  default_priority: ProjectPriority;
  default_budget_type: BudgetType | null;
  estimated_duration_days: number | null;
  phases_template: Record<string, unknown>[];
  tasks_template: Record<string, unknown>[];
  milestones_template: Record<string, unknown>[];
  risks_template: Record<string, unknown>[];
  roles_template: Record<string, unknown>[];
  budget_template: Record<string, unknown>[];
  checklist: string[];
  settings: Record<string, unknown>;
  is_active: boolean;
  is_public: boolean;
  created_by: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - COMMENTS
// ============================================================================

export interface CommentCreate {
  content: string;
  comment_type?: string;
  task_id?: string | null;
  parent_comment_id?: string | null;
  mentions?: string[];
  attachments?: string[];
  is_internal?: boolean;
}

export interface Comment {
  id: string;
  project_id: string;
  task_id: string | null;
  parent_comment_id: string | null;
  content: string;
  comment_type: string;
  mentions: string[];
  attachments: string[];
  is_internal: boolean;
  author_id: string;
  created_at: string;
  updated_at: string;
  is_edited: boolean;
}

// ============================================================================
// TYPES - DASHBOARD
// ============================================================================

export interface ProjectDashboard {
  project: Project;
  stats: ProjectStats;
  recent_tasks: Task[];
  upcoming_milestones: Milestone[];
  high_risks: Risk[];
  open_issues: Issue[];
  burndown: Array<{
    date: string;
    planned_remaining: number;
    actual_remaining: number;
    completed: number;
  }>;
  health_indicators: Record<string, unknown>;
}

// ============================================================================
// API CLIENT
// ============================================================================

const BASE_PATH = '/v1/projects';

export const projectsApi = {
  // --------------------------------------------------------------------------
  // Projets
  // --------------------------------------------------------------------------
  createProject: (data: ProjectCreate) =>
    api.post<Project>(`${BASE_PATH}`, data),

  listProjects: (params?: {
    status?: ProjectStatus;
    priority?: ProjectPriority;
    project_manager_id?: string;
    customer_id?: string;
    category?: string;
    is_active?: boolean;
    search?: string;
    skip?: number;
    limit?: number;
  }) =>
    api.get<ProjectList>(`${BASE_PATH}${buildQueryString(params || {})}`),

  getProject: (projectId: string) =>
    api.get<Project>(`${BASE_PATH}/${projectId}`),

  updateProject: (projectId: string, data: ProjectUpdate) =>
    api.put<Project>(`${BASE_PATH}/${projectId}`, data),

  deleteProject: (projectId: string) =>
    api.delete(`${BASE_PATH}/${projectId}`),

  refreshProjectProgress: (projectId: string) =>
    api.post<Project>(`${BASE_PATH}/${projectId}/refresh-progress`),

  getProjectDashboard: (projectId: string) =>
    api.get<ProjectDashboard>(`${BASE_PATH}/${projectId}/dashboard`),

  getProjectStats: (projectId: string) =>
    api.get<ProjectStats>(`${BASE_PATH}/${projectId}/stats`),

  // --------------------------------------------------------------------------
  // Phases
  // --------------------------------------------------------------------------
  createPhase: (projectId: string, data: PhaseCreate) =>
    api.post<Phase>(`${BASE_PATH}/${projectId}/phases`, data),

  getPhases: (projectId: string) =>
    api.get<Phase[]>(`${BASE_PATH}/${projectId}/phases`),

  updatePhase: (phaseId: string, data: PhaseUpdate) =>
    api.put<Phase>(`${BASE_PATH}/phases/${phaseId}`, data),

  deletePhase: (phaseId: string) =>
    api.delete(`${BASE_PATH}/phases/${phaseId}`),

  // --------------------------------------------------------------------------
  // Tâches
  // --------------------------------------------------------------------------
  createTask: (projectId: string, data: TaskCreate) =>
    api.post<Task>(`${BASE_PATH}/${projectId}/tasks`, data),

  listProjectTasks: (projectId: string, params?: {
    phase_id?: string;
    assignee_id?: string;
    status?: TaskStatus;
    priority?: TaskPriority;
    is_overdue?: boolean;
    search?: string;
    skip?: number;
    limit?: number;
  }) =>
    api.get<TaskList>(`${BASE_PATH}/${projectId}/tasks${buildQueryString(params || {})}`),

  getMyTasks: (params?: { status?: TaskStatus; limit?: number }) =>
    api.get<Task[]>(`${BASE_PATH}/tasks/my${buildQueryString(params || {})}`),

  getTask: (taskId: string) =>
    api.get<Task>(`${BASE_PATH}/tasks/${taskId}`),

  updateTask: (taskId: string, data: TaskUpdate) =>
    api.put<Task>(`${BASE_PATH}/tasks/${taskId}`, data),

  deleteTask: (taskId: string) =>
    api.delete(`${BASE_PATH}/tasks/${taskId}`),

  // --------------------------------------------------------------------------
  // Jalons
  // --------------------------------------------------------------------------
  createMilestone: (projectId: string, data: MilestoneCreate) =>
    api.post<Milestone>(`${BASE_PATH}/${projectId}/milestones`, data),

  getMilestones: (projectId: string) =>
    api.get<Milestone[]>(`${BASE_PATH}/${projectId}/milestones`),

  updateMilestone: (milestoneId: string, data: MilestoneUpdate) =>
    api.put<Milestone>(`${BASE_PATH}/milestones/${milestoneId}`, data),

  // --------------------------------------------------------------------------
  // Équipe
  // --------------------------------------------------------------------------
  addTeamMember: (projectId: string, data: TeamMemberCreate) =>
    api.post<TeamMember>(`${BASE_PATH}/${projectId}/team`, data),

  getTeamMembers: (projectId: string) =>
    api.get<TeamMember[]>(`${BASE_PATH}/${projectId}/team`),

  updateTeamMember: (memberId: string, data: TeamMemberUpdate) =>
    api.put<TeamMember>(`${BASE_PATH}/team/${memberId}`, data),

  removeTeamMember: (memberId: string) =>
    api.delete(`${BASE_PATH}/team/${memberId}`),

  // --------------------------------------------------------------------------
  // Risques
  // --------------------------------------------------------------------------
  createRisk: (projectId: string, data: RiskCreate) =>
    api.post<Risk>(`${BASE_PATH}/${projectId}/risks`, data),

  getRisks: (projectId: string, status?: RiskStatus) =>
    api.get<Risk[]>(`${BASE_PATH}/${projectId}/risks${buildQueryString({ status })}`),

  updateRisk: (riskId: string, data: RiskUpdate) =>
    api.put<Risk>(`${BASE_PATH}/risks/${riskId}`, data),

  // --------------------------------------------------------------------------
  // Issues
  // --------------------------------------------------------------------------
  createIssue: (projectId: string, data: IssueCreate) =>
    api.post<Issue>(`${BASE_PATH}/${projectId}/issues`, data),

  getIssues: (projectId: string, status?: IssueStatus, priority?: IssuePriority) =>
    api.get<Issue[]>(`${BASE_PATH}/${projectId}/issues${buildQueryString({ status, priority })}`),

  updateIssue: (issueId: string, data: IssueUpdate) =>
    api.put<Issue>(`${BASE_PATH}/issues/${issueId}`, data),

  // --------------------------------------------------------------------------
  // Time Entries
  // --------------------------------------------------------------------------
  createTimeEntry: (projectId: string, data: TimeEntryCreate) =>
    api.post<TimeEntry>(`${BASE_PATH}/${projectId}/time`, data),

  getTimeEntries: (projectId: string, params?: {
    task_id?: string;
    user_id?: string;
    start_date?: string;
    end_date?: string;
    status?: TimeEntryStatus;
    skip?: number;
    limit?: number;
  }) =>
    api.get<TimeEntryList>(`${BASE_PATH}/${projectId}/time${buildQueryString(params || {})}`),

  submitTimeEntry: (entryId: string) =>
    api.post<TimeEntry>(`${BASE_PATH}/time/${entryId}/submit`),

  approveTimeEntry: (entryId: string) =>
    api.post<TimeEntry>(`${BASE_PATH}/time/${entryId}/approve`),

  rejectTimeEntry: (entryId: string, reason: string) =>
    api.post<TimeEntry>(`${BASE_PATH}/time/${entryId}/reject${buildQueryString({ reason })}`),

  // --------------------------------------------------------------------------
  // Expenses
  // --------------------------------------------------------------------------
  createExpense: (projectId: string, data: ExpenseCreate) =>
    api.post<Expense>(`${BASE_PATH}/${projectId}/expenses`, data),

  getExpenses: (projectId: string, status?: ExpenseStatus) =>
    api.get<Expense[]>(`${BASE_PATH}/${projectId}/expenses${buildQueryString({ status })}`),

  approveExpense: (expenseId: string) =>
    api.post<Expense>(`${BASE_PATH}/expenses/${expenseId}/approve`),

  // --------------------------------------------------------------------------
  // Documents
  // --------------------------------------------------------------------------
  createDocument: (projectId: string, data: DocumentCreate) =>
    api.post<Document>(`${BASE_PATH}/${projectId}/documents`, data),

  getDocuments: (projectId: string, category?: string) =>
    api.get<Document[]>(`${BASE_PATH}/${projectId}/documents${buildQueryString({ category })}`),

  // --------------------------------------------------------------------------
  // Budgets
  // --------------------------------------------------------------------------
  createBudget: (projectId: string, data: BudgetCreate) =>
    api.post<Budget>(`${BASE_PATH}/${projectId}/budgets`, data),

  getBudgets: (projectId: string) =>
    api.get<Budget[]>(`${BASE_PATH}/${projectId}/budgets`),

  approveBudget: (budgetId: string) =>
    api.post<Budget>(`${BASE_PATH}/budgets/${budgetId}/approve`),

  // --------------------------------------------------------------------------
  // Templates
  // --------------------------------------------------------------------------
  createTemplate: (data: TemplateCreate) =>
    api.post<Template>(`${BASE_PATH}/templates`, data),

  getTemplates: () =>
    api.get<Template[]>(`${BASE_PATH}/templates`),

  createProjectFromTemplate: (templateId: string, code: string, name: string, startDate?: string) =>
    api.post<Project>(`${BASE_PATH}/from-template/${templateId}${buildQueryString({
      code,
      name,
      start_date: startDate,
    })}`),

  // --------------------------------------------------------------------------
  // Comments
  // --------------------------------------------------------------------------
  createComment: (projectId: string, data: CommentCreate) =>
    api.post<Comment>(`${BASE_PATH}/${projectId}/comments`, data),

  getComments: (projectId: string, taskId?: string) =>
    api.get<Comment[]>(`${BASE_PATH}/${projectId}/comments${buildQueryString({ task_id: taskId })}`),

  // --------------------------------------------------------------------------
  // KPIs
  // --------------------------------------------------------------------------
  calculateKPIs: (projectId: string) =>
    api.post<{ message: string; kpi_id: string }>(`${BASE_PATH}/${projectId}/kpis/calculate`),
};

export default projectsApi;
