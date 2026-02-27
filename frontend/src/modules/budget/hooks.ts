/**
 * AZALSCORE Module - BUDGET - React Query Hooks
 * ==============================================
 * Hooks pour la gestion budgetaire
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { budgetApi } from './api';
import type {
  BudgetFilters, CategoryFilters, AlertFilters,
  BudgetCreate, BudgetUpdate, CategoryCreate, LineCreate, LineUpdate,
  ActualCreate, RevisionCreate, ScenarioCreate, ForecastCreate, ControlCheck,
} from './api';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const budgetKeys = {
  all: ['budget'] as const,
  dashboard: (year?: number) => [...budgetKeys.all, 'dashboard', year] as const,
  summary: (year?: number) => [...budgetKeys.all, 'summary', year] as const,

  // Categories
  categories: () => [...budgetKeys.all, 'categories'] as const,
  categoriesList: (filters?: CategoryFilters) => [...budgetKeys.categories(), 'list', filters] as const,
  category: (id: string) => [...budgetKeys.categories(), id] as const,

  // Budgets
  budgets: () => [...budgetKeys.all, 'budgets'] as const,
  budgetsList: (filters?: BudgetFilters) => [...budgetKeys.budgets(), 'list', filters] as const,
  budget: (id: string) => [...budgetKeys.budgets(), id] as const,
  budgetLines: (id: string) => [...budgetKeys.budget(id), 'lines'] as const,
  budgetVariances: (id: string, period: string) => [...budgetKeys.budget(id), 'variances', period] as const,
  budgetExecution: (id: string, period: string) => [...budgetKeys.budget(id), 'execution', period] as const,
  budgetRevisions: (id: string) => [...budgetKeys.budget(id), 'revisions'] as const,
  budgetScenarios: (id: string) => [...budgetKeys.budget(id), 'scenarios'] as const,
  budgetForecasts: (id: string) => [...budgetKeys.budget(id), 'forecasts'] as const,

  // Alerts
  alerts: () => [...budgetKeys.all, 'alerts'] as const,
  alertsList: (filters?: AlertFilters) => [...budgetKeys.alerts(), 'list', filters] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export function useBudgetDashboard(fiscalYear?: number) {
  return useQuery({
    queryKey: budgetKeys.dashboard(fiscalYear),
    queryFn: async () => {
      const response = await budgetApi.getDashboard(fiscalYear);
      return response.data;
    },
  });
}

export function useBudgetSummary(fiscalYear?: number) {
  return useQuery({
    queryKey: budgetKeys.summary(fiscalYear),
    queryFn: async () => {
      const response = await budgetApi.getSummary(fiscalYear);
      return response.data;
    },
  });
}

// ============================================================================
// CATEGORIES HOOKS
// ============================================================================

export function useBudgetCategories(filters?: CategoryFilters) {
  return useQuery({
    queryKey: budgetKeys.categoriesList(filters),
    queryFn: async () => {
      const response = await budgetApi.listCategories(filters);
      return response.data;
    },
  });
}

export function useBudgetCategory(id: string) {
  return useQuery({
    queryKey: budgetKeys.category(id),
    queryFn: async () => {
      const response = await budgetApi.getCategory(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CategoryCreate) => {
      const response = await budgetApi.createCategory(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.categories() });
    },
  });
}

export function useUpdateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<CategoryCreate> }) => {
      const response = await budgetApi.updateCategory(id, data);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.category(id) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.categories() });
    },
  });
}

export function useDeleteCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await budgetApi.deleteCategory(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.categories() });
    },
  });
}

// ============================================================================
// BUDGETS HOOKS
// ============================================================================

export function useBudgets(filters?: BudgetFilters) {
  return useQuery({
    queryKey: budgetKeys.budgetsList(filters),
    queryFn: async () => {
      const response = await budgetApi.listBudgets(filters);
      return response.data;
    },
  });
}

export function useBudget(id: string) {
  return useQuery({
    queryKey: budgetKeys.budget(id),
    queryFn: async () => {
      const response = await budgetApi.getBudget(id);
      return response.data;
    },
    enabled: !!id,
  });
}

export function useCreateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BudgetCreate) => {
      const response = await budgetApi.createBudget(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgets() });
      queryClient.invalidateQueries({ queryKey: budgetKeys.dashboard() });
    },
  });
}

export function useUpdateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: BudgetUpdate }) => {
      const response = await budgetApi.updateBudget(id, data);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(id) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgets() });
    },
  });
}

export function useDeleteBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await budgetApi.deleteBudget(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgets() });
      queryClient.invalidateQueries({ queryKey: budgetKeys.dashboard() });
    },
  });
}

// Workflow hooks
export function useSubmitBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, comments }: { id: string; comments?: string }) => {
      const response = await budgetApi.submitBudget(id, comments);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(id) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgets() });
    },
  });
}

export function useApproveBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, comments }: { id: string; comments?: string }) => {
      const response = await budgetApi.approveBudget(id, comments);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(id) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgets() });
    },
  });
}

export function useRejectBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      const response = await budgetApi.rejectBudget(id, reason);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(id) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgets() });
    },
  });
}

export function useActivateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, effective_date }: { id: string; effective_date?: string }) => {
      const response = await budgetApi.activateBudget(id, effective_date);
      return response.data;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(id) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgets() });
      queryClient.invalidateQueries({ queryKey: budgetKeys.dashboard() });
    },
  });
}

export function useCloseBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await budgetApi.closeBudget(id);
      return response.data;
    },
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(id) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgets() });
    },
  });
}

// ============================================================================
// BUDGET LINES HOOKS
// ============================================================================

export function useBudgetLines(budgetId: string) {
  return useQuery({
    queryKey: budgetKeys.budgetLines(budgetId),
    queryFn: async () => {
      const response = await budgetApi.listLines(budgetId);
      return response.data;
    },
    enabled: !!budgetId,
  });
}

export function useAddLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ budgetId, data }: { budgetId: string; data: LineCreate }) => {
      const response = await budgetApi.addLine(budgetId, data);
      return response.data;
    },
    onSuccess: (_data, { budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(budgetId) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetLines(budgetId) });
    },
  });
}

export function useUpdateLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ lineId, data, budgetId }: { lineId: string; data: LineUpdate; budgetId: string }) => {
      const response = await budgetApi.updateLine(lineId, data);
      return response.data;
    },
    onSuccess: (_data, { budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(budgetId) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetLines(budgetId) });
    },
  });
}

export function useDeleteLine() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ lineId, budgetId }: { lineId: string; budgetId: string }) => {
      await budgetApi.deleteLine(lineId);
      return { budgetId };
    },
    onSuccess: (_data, { budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(budgetId) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetLines(budgetId) });
    },
  });
}

// ============================================================================
// ACTUALS HOOKS
// ============================================================================

export function useRecordActual() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ budgetId, data }: { budgetId: string; data: ActualCreate }) => {
      const response = await budgetApi.recordActual(budgetId, data);
      return response.data;
    },
    onSuccess: (_data, { budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(budgetId) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetLines(budgetId) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.dashboard() });
    },
  });
}

export function useImportActuals() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ budgetId, period }: { budgetId: string; period: string }) => {
      const response = await budgetApi.importActuals(budgetId, period);
      return response.data;
    },
    onSuccess: (_data, { budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(budgetId) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetLines(budgetId) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.dashboard() });
    },
  });
}

// ============================================================================
// VARIANCES HOOKS
// ============================================================================

export function useBudgetVariances(budgetId: string, period: string) {
  return useQuery({
    queryKey: budgetKeys.budgetVariances(budgetId, period),
    queryFn: async () => {
      const response = await budgetApi.getVariances(budgetId, period);
      return response.data;
    },
    enabled: !!budgetId && !!period,
  });
}

export function useBudgetExecutionRate(budgetId: string, period: string) {
  return useQuery({
    queryKey: budgetKeys.budgetExecution(budgetId, period),
    queryFn: async () => {
      const response = await budgetApi.getExecutionRate(budgetId, period);
      return response.data;
    },
    enabled: !!budgetId && !!period,
  });
}

// ============================================================================
// REVISIONS HOOKS
// ============================================================================

export function useBudgetRevisions(budgetId: string) {
  return useQuery({
    queryKey: budgetKeys.budgetRevisions(budgetId),
    queryFn: async () => {
      const response = await budgetApi.listRevisions(budgetId);
      return response.data;
    },
    enabled: !!budgetId,
  });
}

export function useCreateRevision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ budgetId, data }: { budgetId: string; data: RevisionCreate }) => {
      const response = await budgetApi.createRevision(budgetId, data);
      return response.data;
    },
    onSuccess: (_data, { budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetRevisions(budgetId) });
    },
  });
}

export function useSubmitRevision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ revisionId, budgetId }: { revisionId: string; budgetId: string }) => {
      const response = await budgetApi.submitRevision(revisionId);
      return { data: response.data, budgetId };
    },
    onSuccess: ({ budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetRevisions(budgetId) });
    },
  });
}

export function useApproveRevision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ revisionId, budgetId, comments }: { revisionId: string; budgetId: string; comments?: string }) => {
      const response = await budgetApi.approveRevision(revisionId, comments);
      return { data: response.data, budgetId };
    },
    onSuccess: ({ budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetRevisions(budgetId) });
    },
  });
}

export function useApplyRevision() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ revisionId, budgetId }: { revisionId: string; budgetId: string }) => {
      const response = await budgetApi.applyRevision(revisionId);
      return { data: response.data, budgetId };
    },
    onSuccess: ({ budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budget(budgetId) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetRevisions(budgetId) });
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetLines(budgetId) });
    },
  });
}

// ============================================================================
// SCENARIOS HOOKS
// ============================================================================

export function useBudgetScenarios(budgetId: string) {
  return useQuery({
    queryKey: budgetKeys.budgetScenarios(budgetId),
    queryFn: async () => {
      const response = await budgetApi.listScenarios(budgetId);
      return response.data;
    },
    enabled: !!budgetId,
  });
}

export function useCreateScenario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ budgetId, data }: { budgetId: string; data: ScenarioCreate }) => {
      const response = await budgetApi.createScenario(budgetId, data);
      return response.data;
    },
    onSuccess: (_data, { budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetScenarios(budgetId) });
    },
  });
}

// ============================================================================
// FORECASTS HOOKS
// ============================================================================

export function useBudgetForecasts(budgetId: string) {
  return useQuery({
    queryKey: budgetKeys.budgetForecasts(budgetId),
    queryFn: async () => {
      const response = await budgetApi.listForecasts(budgetId);
      return response.data;
    },
    enabled: !!budgetId,
  });
}

export function useCreateForecast() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ budgetId, data }: { budgetId: string; data: ForecastCreate }) => {
      const response = await budgetApi.createForecast(budgetId, data);
      return response.data;
    },
    onSuccess: (_data, { budgetId }) => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.budgetForecasts(budgetId) });
    },
  });
}

// ============================================================================
// ALERTS HOOKS
// ============================================================================

export function useBudgetAlerts(filters?: AlertFilters) {
  return useQuery({
    queryKey: budgetKeys.alertsList(filters),
    queryFn: async () => {
      const response = await budgetApi.listAlerts(filters);
      return response.data;
    },
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ alertId, notes }: { alertId: string; notes?: string }) => {
      const response = await budgetApi.acknowledgeAlert(alertId, notes);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.alerts() });
      queryClient.invalidateQueries({ queryKey: budgetKeys.dashboard() });
    },
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ alertId, resolution_notes }: { alertId: string; resolution_notes: string }) => {
      const response = await budgetApi.resolveAlert(alertId, resolution_notes);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: budgetKeys.alerts() });
      queryClient.invalidateQueries({ queryKey: budgetKeys.dashboard() });
    },
  });
}

// ============================================================================
// CONTROL HOOKS
// ============================================================================

export function useCheckBudgetControl() {
  return useMutation({
    mutationFn: async (data: ControlCheck) => {
      const response = await budgetApi.checkControl(data);
      return response.data;
    },
  });
}
