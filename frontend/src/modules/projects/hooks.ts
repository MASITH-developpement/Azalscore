/**
 * AZALSCORE - Projects Module Hooks
 * ==================================
 * React Query hooks pour la gestion de projets
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { projectsApi } from './api';
import type {
  Project, ProjectCreate, ProjectUpdate, ProjectList, ProjectStats, ProjectDashboard,
  ProjectStatus, ProjectPriority,
  Task, TaskCreate, TaskUpdate, TaskList, TaskStatus, TaskPriority,
  Phase, PhaseCreate, PhaseUpdate,
  Milestone, MilestoneCreate, MilestoneUpdate,
  TeamMember, TeamMemberCreate, TeamMemberUpdate,
  Risk, RiskCreate, RiskUpdate, RiskStatus,
  Issue, IssueCreate, IssueUpdate, IssueStatus, IssuePriority,
  TimeEntry, TimeEntryCreate, TimeEntryList, TimeEntryStatus,
  Expense, ExpenseCreate, ExpenseStatus,
  Document, DocumentCreate,
  Budget, BudgetCreate,
  Template, TemplateCreate,
  Comment, CommentCreate,
} from './api';
import type {
  ProjectStats as GlobalProjectStats,
  Project as SimpleProject,
  Task as SimpleTask,
  TimeEntry as SimpleTimeEntry
} from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const projectsKeys = {
  all: ['projects'] as const,
  lists: () => [...projectsKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) => [...projectsKeys.lists(), filters] as const,
  details: () => [...projectsKeys.all, 'detail'] as const,
  detail: (id: string) => [...projectsKeys.details(), id] as const,
  dashboard: (id: string) => [...projectsKeys.detail(id), 'dashboard'] as const,
  stats: (id: string) => [...projectsKeys.detail(id), 'stats'] as const,
  // Sub-entities
  phases: (projectId: string) => [...projectsKeys.detail(projectId), 'phases'] as const,
  tasks: (projectId: string) => [...projectsKeys.detail(projectId), 'tasks'] as const,
  taskDetail: (taskId: string) => [...projectsKeys.all, 'task', taskId] as const,
  myTasks: () => [...projectsKeys.all, 'my-tasks'] as const,
  milestones: (projectId: string) => [...projectsKeys.detail(projectId), 'milestones'] as const,
  team: (projectId: string) => [...projectsKeys.detail(projectId), 'team'] as const,
  risks: (projectId: string) => [...projectsKeys.detail(projectId), 'risks'] as const,
  issues: (projectId: string) => [...projectsKeys.detail(projectId), 'issues'] as const,
  timeEntries: (projectId: string) => [...projectsKeys.detail(projectId), 'time'] as const,
  expenses: (projectId: string) => [...projectsKeys.detail(projectId), 'expenses'] as const,
  documents: (projectId: string) => [...projectsKeys.detail(projectId), 'documents'] as const,
  budgets: (projectId: string) => [...projectsKeys.detail(projectId), 'budgets'] as const,
  comments: (projectId: string) => [...projectsKeys.detail(projectId), 'comments'] as const,
  templates: () => [...projectsKeys.all, 'templates'] as const,
  // Global (module-level) keys
  globalStats: () => [...projectsKeys.all, 'global-stats'] as const,
  allTasks: (filters?: { status?: string; project_id?: string; assignee_id?: string }) =>
    [...projectsKeys.all, 'all-tasks', filters?.status ?? null, filters?.project_id ?? null, filters?.assignee_id ?? null] as const,
  allTimeEntries: (filters?: { project_id?: string; date_from?: string; date_to?: string }) =>
    [...projectsKeys.all, 'all-time-entries', filters?.project_id ?? null, filters?.date_from ?? null, filters?.date_to ?? null] as const,
};

// ============================================================================
// PROJECTS HOOKS
// ============================================================================

export function useProjects(params?: {
  status?: ProjectStatus;
  priority?: ProjectPriority;
  project_manager_id?: string;
  customer_id?: string;
  category?: string;
  is_active?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: projectsKeys.list(params),
    queryFn: async () => {
      const response = await projectsApi.listProjects(params);
      return response.data;
    },
  });
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: projectsKeys.detail(projectId),
    queryFn: async () => {
      const response = await projectsApi.getProject(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useProjectDashboard(projectId: string) {
  return useQuery({
    queryKey: projectsKeys.dashboard(projectId),
    queryFn: async () => {
      const response = await projectsApi.getProjectDashboard(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useProjectStats(projectId: string) {
  return useQuery({
    queryKey: projectsKeys.stats(projectId),
    queryFn: async () => {
      const response = await projectsApi.getProjectStats(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ProjectCreate) => {
      const response = await projectsApi.createProject(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.lists() });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: ProjectUpdate }) => {
      const response = await projectsApi.updateProject(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.detail(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.lists() });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projectId: string) => {
      await projectsApi.deleteProject(projectId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.lists() });
    },
  });
}

export function useRefreshProjectProgress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projectId: string) => {
      const response = await projectsApi.refreshProjectProgress(projectId);
      return response.data;
    },
    onSuccess: (_data, projectId) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.detail(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

// ============================================================================
// PHASES HOOKS
// ============================================================================

export function usePhases(projectId: string) {
  return useQuery({
    queryKey: projectsKeys.phases(projectId),
    queryFn: async () => {
      const response = await projectsApi.getPhases(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreatePhase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: PhaseCreate }) => {
      const response = await projectsApi.createPhase(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.phases(projectId) });
    },
  });
}

export function useUpdatePhase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ phaseId, data, projectId }: { phaseId: string; data: PhaseUpdate; projectId: string }) => {
      const response = await projectsApi.updatePhase(phaseId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.phases(projectId) });
    },
  });
}

export function useDeletePhase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ phaseId }: { phaseId: string; projectId: string }) => {
      await projectsApi.deletePhase(phaseId);
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.phases(projectId) });
    },
  });
}

// ============================================================================
// TASKS HOOKS
// ============================================================================

export function useTasks(projectId: string, params?: {
  phase_id?: string;
  assignee_id?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  is_overdue?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...projectsKeys.tasks(projectId), params],
    queryFn: async () => {
      const response = await projectsApi.listProjectTasks(projectId, params);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useTask(taskId: string) {
  return useQuery({
    queryKey: projectsKeys.taskDetail(taskId),
    queryFn: async () => {
      const response = await projectsApi.getTask(taskId);
      return response.data;
    },
    enabled: !!taskId,
  });
}

export function useMyTasks(params?: { status?: TaskStatus; limit?: number }) {
  return useQuery({
    queryKey: [...projectsKeys.myTasks(), params],
    queryFn: async () => {
      const response = await projectsApi.getMyTasks(params);
      return response.data;
    },
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: TaskCreate }) => {
      const response = await projectsApi.createTask(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.tasks(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.myTasks() });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ taskId, data, projectId }: { taskId: string; data: TaskUpdate; projectId: string }) => {
      const response = await projectsApi.updateTask(taskId, data);
      return response.data;
    },
    onSuccess: (_data, { taskId, projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.taskDetail(taskId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.tasks(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.myTasks() });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ taskId }: { taskId: string; projectId: string }) => {
      await projectsApi.deleteTask(taskId);
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.tasks(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

// ============================================================================
// MILESTONES HOOKS
// ============================================================================

export function useMilestones(projectId: string) {
  return useQuery({
    queryKey: projectsKeys.milestones(projectId),
    queryFn: async () => {
      const response = await projectsApi.getMilestones(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreateMilestone() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: MilestoneCreate }) => {
      const response = await projectsApi.createMilestone(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.milestones(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

export function useUpdateMilestone() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ milestoneId, data, projectId }: { milestoneId: string; data: MilestoneUpdate; projectId: string }) => {
      const response = await projectsApi.updateMilestone(milestoneId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.milestones(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

// ============================================================================
// TEAM HOOKS
// ============================================================================

export function useTeamMembers(projectId: string) {
  return useQuery({
    queryKey: projectsKeys.team(projectId),
    queryFn: async () => {
      const response = await projectsApi.getTeamMembers(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useAddTeamMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: TeamMemberCreate }) => {
      const response = await projectsApi.addTeamMember(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.team(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

export function useUpdateTeamMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ memberId, data, projectId }: { memberId: string; data: TeamMemberUpdate; projectId: string }) => {
      const response = await projectsApi.updateTeamMember(memberId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.team(projectId) });
    },
  });
}

export function useRemoveTeamMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ memberId }: { memberId: string; projectId: string }) => {
      await projectsApi.removeTeamMember(memberId);
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.team(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

// ============================================================================
// RISKS HOOKS
// ============================================================================

export function useRisks(projectId: string, status?: RiskStatus) {
  return useQuery({
    queryKey: [...projectsKeys.risks(projectId), status],
    queryFn: async () => {
      const response = await projectsApi.getRisks(projectId, status);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreateRisk() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: RiskCreate }) => {
      const response = await projectsApi.createRisk(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.risks(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

export function useUpdateRisk() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ riskId, data, projectId }: { riskId: string; data: RiskUpdate; projectId: string }) => {
      const response = await projectsApi.updateRisk(riskId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.risks(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

// ============================================================================
// ISSUES HOOKS
// ============================================================================

export function useIssues(projectId: string, status?: IssueStatus, priority?: IssuePriority) {
  return useQuery({
    queryKey: [...projectsKeys.issues(projectId), status, priority],
    queryFn: async () => {
      const response = await projectsApi.getIssues(projectId, status, priority);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreateIssue() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: IssueCreate }) => {
      const response = await projectsApi.createIssue(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.issues(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

export function useUpdateIssue() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ issueId, data, projectId }: { issueId: string; data: IssueUpdate; projectId: string }) => {
      const response = await projectsApi.updateIssue(issueId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.issues(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

// ============================================================================
// TIME ENTRIES HOOKS
// ============================================================================

export function useTimeEntries(projectId: string, params?: {
  task_id?: string;
  user_id?: string;
  start_date?: string;
  end_date?: string;
  status?: TimeEntryStatus;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...projectsKeys.timeEntries(projectId), params],
    queryFn: async () => {
      const response = await projectsApi.getTimeEntries(projectId, params);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreateTimeEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: TimeEntryCreate }) => {
      const response = await projectsApi.createTimeEntry(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.timeEntries(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

export function useSubmitTimeEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ entryId }: { entryId: string; projectId: string }) => {
      const response = await projectsApi.submitTimeEntry(entryId);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.timeEntries(projectId) });
    },
  });
}

export function useApproveTimeEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ entryId }: { entryId: string; projectId: string }) => {
      const response = await projectsApi.approveTimeEntry(entryId);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.timeEntries(projectId) });
    },
  });
}

export function useRejectTimeEntry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ entryId, reason }: { entryId: string; reason: string; projectId: string }) => {
      const response = await projectsApi.rejectTimeEntry(entryId, reason);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.timeEntries(projectId) });
    },
  });
}

// ============================================================================
// EXPENSES HOOKS
// ============================================================================

export function useExpenses(projectId: string, status?: ExpenseStatus) {
  return useQuery({
    queryKey: [...projectsKeys.expenses(projectId), status],
    queryFn: async () => {
      const response = await projectsApi.getExpenses(projectId, status);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: ExpenseCreate }) => {
      const response = await projectsApi.createExpense(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.expenses(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
    },
  });
}

export function useApproveExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ expenseId }: { expenseId: string; projectId: string }) => {
      const response = await projectsApi.approveExpense(expenseId);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.expenses(projectId) });
    },
  });
}

// ============================================================================
// DOCUMENTS HOOKS
// ============================================================================

export function useDocuments(projectId: string, category?: string) {
  return useQuery({
    queryKey: [...projectsKeys.documents(projectId), category],
    queryFn: async () => {
      const response = await projectsApi.getDocuments(projectId, category);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreateDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: DocumentCreate }) => {
      const response = await projectsApi.createDocument(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.documents(projectId) });
    },
  });
}

// ============================================================================
// BUDGETS HOOKS
// ============================================================================

export function useBudgets(projectId: string) {
  return useQuery({
    queryKey: projectsKeys.budgets(projectId),
    queryFn: async () => {
      const response = await projectsApi.getBudgets(projectId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: BudgetCreate }) => {
      const response = await projectsApi.createBudget(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.budgets(projectId) });
    },
  });
}

export function useApproveBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ budgetId }: { budgetId: string; projectId: string }) => {
      const response = await projectsApi.approveBudget(budgetId);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.budgets(projectId) });
    },
  });
}

// ============================================================================
// TEMPLATES HOOKS
// ============================================================================

export function useTemplates() {
  return useQuery({
    queryKey: projectsKeys.templates(),
    queryFn: async () => {
      const response = await projectsApi.getTemplates();
      return response.data;
    },
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TemplateCreate) => {
      const response = await projectsApi.createTemplate(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.templates() });
    },
  });
}

export function useCreateProjectFromTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ templateId, code, name, startDate }: {
      templateId: string;
      code: string;
      name: string;
      startDate?: string;
    }) => {
      const response = await projectsApi.createProjectFromTemplate(templateId, code, name, startDate);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.lists() });
    },
  });
}

// ============================================================================
// COMMENTS HOOKS
// ============================================================================

export function useComments(projectId: string, taskId?: string) {
  return useQuery({
    queryKey: [...projectsKeys.comments(projectId), taskId],
    queryFn: async () => {
      const response = await projectsApi.getComments(projectId, taskId);
      return response.data;
    },
    enabled: !!projectId,
  });
}

export function useCreateComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: CommentCreate }) => {
      const response = await projectsApi.createComment(projectId, data);
      return response.data;
    },
    onSuccess: (_data, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.comments(projectId) });
    },
  });
}

// ============================================================================
// KPIS HOOKS
// ============================================================================

export function useCalculateKPIs() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projectId: string) => {
      const response = await projectsApi.calculateKPIs(projectId);
      return response.data;
    },
    onSuccess: (_data, projectId) => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.stats(projectId) });
      queryClient.invalidateQueries({ queryKey: projectsKeys.dashboard(projectId) });
    },
  });
}

// ============================================================================
// GLOBAL HOOKS (Module-level, no project context)
// ============================================================================

/**
 * Récupère les statistiques globales du module projects (dashboard)
 */
export function useProjectsGlobalStats() {
  return useQuery({
    queryKey: projectsKeys.globalStats(),
    queryFn: async () => {
      const response = await api.get<GlobalProjectStats>('/projects/summary');
      return response.data;
    },
  });
}

/**
 * Liste simplifiée des projets avec filtres basiques
 */
export function useSimpleProjectsList(filters?: { status?: string; client_id?: string }) {
  return useQuery({
    queryKey: projectsKeys.list({ status: filters?.status, client_id: filters?.client_id }),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.client_id) params.append('client_id', filters.client_id);
      const queryString = params.toString();
      const url = queryString ? `/projects?${queryString}` : '/projects';
      const response = await api.get<{ items: SimpleProject[] }>(url);
      return response.data?.items || [];
    },
  });
}

/**
 * Récupère un projet par son ID (version simplifiée)
 */
export function useSimpleProject(id: string) {
  return useQuery({
    queryKey: projectsKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<SimpleProject>(`/projects/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

/**
 * Liste toutes les tâches (cross-project)
 */
export function useAllTasks(filters?: { status?: string; project_id?: string; assignee_id?: string }) {
  return useQuery({
    queryKey: projectsKeys.allTasks(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.project_id) params.append('project_id', filters.project_id);
      if (filters?.assignee_id) params.append('assignee_id', filters.assignee_id);
      const queryString = params.toString();
      const url = queryString ? `/projects/tasks?${queryString}` : '/projects/tasks';
      const response = await api.get<{ items: SimpleTask[] }>(url);
      return response.data?.items || [];
    },
  });
}

/**
 * Liste toutes les entrées de temps (cross-project)
 */
export function useAllTimeEntries(filters?: { project_id?: string; date_from?: string; date_to?: string }) {
  return useQuery({
    queryKey: projectsKeys.allTimeEntries(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.project_id) params.append('project_id', filters.project_id);
      if (filters?.date_from) params.append('date_from', filters.date_from);
      if (filters?.date_to) params.append('date_to', filters.date_to);
      const queryString = params.toString();
      const url = queryString ? `/projects/time-entries?${queryString}` : '/projects/time-entries';
      const response = await api.get<SimpleTimeEntry[]>(url);
      return response.data;
    },
  });
}

/**
 * Mise à jour rapide du statut d'une tâche
 */
export function useUpdateTaskStatusQuick() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      const response = await api.patch<SimpleTask>(`/projects/tasks/${id}/status`, { status });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.allTasks() });
      queryClient.invalidateQueries({ queryKey: projectsKeys.globalStats() });
    },
  });
}

/**
 * Saisie de temps globale (sans contexte projet obligatoire)
 */
export function useLogTimeGlobal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      project_id: string;
      task_id?: string;
      date: string;
      hours: number;
      description?: string;
      is_billable?: boolean;
    }) => {
      const response = await api.post<SimpleTimeEntry>('/projects/time-entries', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectsKeys.allTimeEntries() });
      queryClient.invalidateQueries({ queryKey: projectsKeys.globalStats() });
    },
  });
}
