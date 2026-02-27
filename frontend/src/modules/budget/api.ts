/**
 * AZALSCORE Module - BUDGET - API Client
 * =======================================
 * Client API pour la gestion budgetaire
 */

import { api } from '@/core/api-client';
import type {
  Budget, BudgetDetail, BudgetLine, BudgetCategory, BudgetAlert,
  BudgetVariance, BudgetRevision, BudgetScenario, BudgetForecast,
  BudgetDashboard, BudgetExecutionRate, BudgetType, BudgetStatus,
  AlertSeverity, AlertStatus, BudgetLineType, AllocationMethod,
  RevisionStatus, ScenarioType, ForecastConfidence,
} from './types';

const BASE_URL = '/budget';

// ============================================================================
// TYPES API
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface BudgetFilters {
  type?: BudgetType;
  status?: BudgetStatus;
  fiscal_year?: number;
  entity_id?: string;
  department_id?: string;
  project_id?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface CategoryFilters {
  parent_id?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}

export interface AlertFilters {
  budget_id?: string;
  status?: AlertStatus;
  severity?: AlertSeverity;
  page?: number;
  page_size?: number;
}

export interface BudgetCreate {
  code: string;
  name: string;
  description?: string;
  budget_type: BudgetType;
  period_type: string;
  fiscal_year: number;
  start_date: string;
  end_date: string;
  currency?: string;
  entity_id?: string;
  department_id?: string;
  cost_center_id?: string;
  project_id?: string;
  control_mode?: string;
  warning_threshold?: number;
  critical_threshold?: number;
  notes?: string;
  assumptions?: string;
  objectives?: string;
  tags?: string[];
  owner_id?: string;
  approvers?: string[];
  template_id?: string;
  copy_from_id?: string;
}

export interface BudgetUpdate {
  name?: string;
  description?: string;
  control_mode?: string;
  warning_threshold?: number;
  critical_threshold?: number;
  notes?: string;
  assumptions?: string;
  objectives?: string;
  tags?: string[];
  owner_id?: string;
  approvers?: string[];
}

export interface CategoryCreate {
  code: string;
  name: string;
  description?: string;
  line_type?: BudgetLineType;
  parent_id?: string;
  account_codes?: string[];
  sort_order?: number;
  is_active?: boolean;
}

export interface LineCreate {
  category_id: string;
  code?: string;
  name: string;
  description?: string;
  line_type?: BudgetLineType;
  annual_amount: number;
  allocation_method?: AllocationMethod;
  seasonal_profile?: string;
  monthly_distribution?: Record<number, number>;
  quantity?: number;
  unit?: string;
  unit_price?: number;
  cost_center_id?: string;
  project_id?: string;
  department_id?: string;
  account_code?: string;
  notes?: string;
  assumptions?: string;
}

export interface LineUpdate {
  category_id?: string;
  name?: string;
  description?: string;
  annual_amount?: number;
  monthly_distribution?: Record<number, number>;
  allocation_method?: AllocationMethod;
  seasonal_profile?: string;
  quantity?: number;
  unit?: string;
  unit_price?: number;
  cost_center_id?: string;
  project_id?: string;
  account_code?: string;
  notes?: string;
}

export interface ActualCreate {
  budget_line_id?: string;
  period: string;
  amount: number;
  line_type?: BudgetLineType;
  source?: string;
  source_document_type?: string;
  source_document_id?: string;
  reference?: string;
  description?: string;
  account_code?: string;
  cost_center_id?: string;
  project_id?: string;
}

export interface RevisionCreate {
  name: string;
  description?: string;
  effective_date: string;
  reason: string;
  impact_analysis?: string;
  details: Array<{
    budget_line_id: string;
    new_amount: number;
    affected_period?: number;
    justification?: string;
  }>;
}

export interface ScenarioCreate {
  name: string;
  description?: string;
  scenario_type?: ScenarioType;
  revenue_adjustment_percent?: number;
  expense_adjustment_percent?: number;
  assumptions?: Record<string, unknown>;
  parameters?: Record<string, unknown>;
  lines?: Array<{
    budget_line_id: string;
    adjusted_amount?: number;
    adjustment_percent?: number;
    justification?: string;
  }>;
}

export interface ForecastCreate {
  budget_line_id?: string;
  period: string;
  revised_forecast: number;
  confidence?: ForecastConfidence;
  probability?: number;
  assumptions?: string;
  methodology?: string;
}

export interface ControlCheck {
  budget_id: string;
  budget_line_id?: string;
  amount: number;
  description?: string;
  cost_center_id?: string;
  project_id?: string;
}

export interface ControlResult {
  allowed: boolean;
  control_mode: string;
  budget_amount: number;
  consumed_amount: number;
  requested_amount: number;
  available_amount: number;
  consumption_after: number;
  consumption_percent: number;
  threshold_exceeded?: string;
  message: string;
  requires_override: boolean;
}

// ============================================================================
// CATEGORIES API
// ============================================================================

async function listCategories(filters?: CategoryFilters) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
  }
  return api.get<PaginatedResponse<BudgetCategory>>(`${BASE_URL}/categories?${params.toString()}`);
}

async function getCategory(id: string) {
  return api.get<BudgetCategory>(`${BASE_URL}/categories/${id}`);
}

async function createCategory(data: CategoryCreate) {
  return api.post<BudgetCategory>(`${BASE_URL}/categories`, data);
}

async function updateCategory(id: string, data: Partial<CategoryCreate>) {
  return api.put<BudgetCategory>(`${BASE_URL}/categories/${id}`, data);
}

async function deleteCategory(id: string) {
  return api.delete(`${BASE_URL}/categories/${id}`);
}

// ============================================================================
// BUDGETS API
// ============================================================================

async function listBudgets(filters?: BudgetFilters) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
  }
  return api.get<PaginatedResponse<Budget>>(`${BASE_URL}/budgets?${params.toString()}`);
}

async function getBudget(id: string) {
  return api.get<BudgetDetail>(`${BASE_URL}/budgets/${id}`);
}

async function createBudget(data: BudgetCreate) {
  return api.post<Budget>(`${BASE_URL}/budgets`, data);
}

async function updateBudget(id: string, data: BudgetUpdate) {
  return api.put<Budget>(`${BASE_URL}/budgets/${id}`, data);
}

async function deleteBudget(id: string) {
  return api.delete(`${BASE_URL}/budgets/${id}`);
}

// Workflow
async function submitBudget(id: string, comments?: string) {
  return api.post<Budget>(`${BASE_URL}/budgets/${id}/submit`, { comments });
}

async function approveBudget(id: string, comments?: string) {
  return api.post<Budget>(`${BASE_URL}/budgets/${id}/approve`, { comments });
}

async function rejectBudget(id: string, reason: string) {
  return api.post<Budget>(`${BASE_URL}/budgets/${id}/reject`, { reason });
}

async function activateBudget(id: string, effective_date?: string) {
  return api.post<Budget>(`${BASE_URL}/budgets/${id}/activate`, { effective_date });
}

async function closeBudget(id: string) {
  return api.post<Budget>(`${BASE_URL}/budgets/${id}/close`);
}

// ============================================================================
// BUDGET LINES API
// ============================================================================

async function listLines(budgetId: string, filters?: { page?: number; page_size?: number }) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) params.append(key, String(value));
    });
  }
  return api.get<PaginatedResponse<BudgetLine>>(`${BASE_URL}/budgets/${budgetId}/lines?${params.toString()}`);
}

async function addLine(budgetId: string, data: LineCreate) {
  return api.post<BudgetLine>(`${BASE_URL}/budgets/${budgetId}/lines`, data);
}

async function updateLine(lineId: string, data: LineUpdate) {
  return api.put<BudgetLine>(`${BASE_URL}/lines/${lineId}`, data);
}

async function deleteLine(lineId: string) {
  return api.delete(`${BASE_URL}/lines/${lineId}`);
}

// ============================================================================
// ACTUALS API
// ============================================================================

async function recordActual(budgetId: string, data: ActualCreate) {
  return api.post(`${BASE_URL}/budgets/${budgetId}/actuals`, data);
}

async function importActuals(budgetId: string, period: string) {
  return api.post(`${BASE_URL}/budgets/${budgetId}/actuals/import?period=${period}`);
}

// ============================================================================
// VARIANCES API
// ============================================================================

async function getVariances(budgetId: string, period: string) {
  return api.get<BudgetVariance[]>(`${BASE_URL}/budgets/${budgetId}/variances?period=${period}`);
}

async function getExecutionRate(budgetId: string, period: string) {
  return api.get<BudgetExecutionRate>(`${BASE_URL}/budgets/${budgetId}/execution-rate?period=${period}`);
}

// ============================================================================
// REVISIONS API
// ============================================================================

async function listRevisions(budgetId: string, filters?: { page?: number; page_size?: number }) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) params.append(key, String(value));
    });
  }
  return api.get<PaginatedResponse<BudgetRevision>>(`${BASE_URL}/budgets/${budgetId}/revisions?${params.toString()}`);
}

async function createRevision(budgetId: string, data: RevisionCreate) {
  return api.post<BudgetRevision>(`${BASE_URL}/budgets/${budgetId}/revisions`, data);
}

async function submitRevision(revisionId: string) {
  return api.post<BudgetRevision>(`${BASE_URL}/revisions/${revisionId}/submit`);
}

async function approveRevision(revisionId: string, comments?: string) {
  return api.post<BudgetRevision>(`${BASE_URL}/revisions/${revisionId}/approve`, { comments });
}

async function applyRevision(revisionId: string) {
  return api.post<BudgetRevision>(`${BASE_URL}/revisions/${revisionId}/apply`);
}

// ============================================================================
// SCENARIOS API
// ============================================================================

async function listScenarios(budgetId: string, filters?: { is_active?: boolean; page?: number; page_size?: number }) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) params.append(key, String(value));
    });
  }
  return api.get<PaginatedResponse<BudgetScenario>>(`${BASE_URL}/budgets/${budgetId}/scenarios?${params.toString()}`);
}

async function createScenario(budgetId: string, data: ScenarioCreate) {
  return api.post<BudgetScenario>(`${BASE_URL}/budgets/${budgetId}/scenarios`, data);
}

// ============================================================================
// FORECASTS API
// ============================================================================

async function listForecasts(budgetId: string, filters?: { period?: string; page?: number; page_size?: number }) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) params.append(key, String(value));
    });
  }
  return api.get<PaginatedResponse<BudgetForecast>>(`${BASE_URL}/budgets/${budgetId}/forecasts?${params.toString()}`);
}

async function createForecast(budgetId: string, data: ForecastCreate) {
  return api.post<BudgetForecast>(`${BASE_URL}/budgets/${budgetId}/forecasts`, data);
}

// ============================================================================
// ALERTS API
// ============================================================================

async function listAlerts(filters?: AlertFilters) {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, String(value));
      }
    });
  }
  return api.get<PaginatedResponse<BudgetAlert>>(`${BASE_URL}/alerts?${params.toString()}`);
}

async function acknowledgeAlert(alertId: string, notes?: string) {
  return api.post<BudgetAlert>(`${BASE_URL}/alerts/${alertId}/acknowledge`, { notes });
}

async function resolveAlert(alertId: string, resolution_notes: string) {
  return api.post<BudgetAlert>(`${BASE_URL}/alerts/${alertId}/resolve`, { resolution_notes });
}

// ============================================================================
// DASHBOARD & CONTROL API
// ============================================================================

async function getDashboard(fiscal_year?: number, as_of_date?: string) {
  const params = new URLSearchParams();
  if (fiscal_year) params.append('fiscal_year', String(fiscal_year));
  if (as_of_date) params.append('as_of_date', as_of_date);
  return api.get<BudgetDashboard>(`${BASE_URL}/dashboard?${params.toString()}`);
}

async function getSummary(fiscal_year?: number) {
  const params = fiscal_year ? `?fiscal_year=${fiscal_year}` : '';
  return api.get<{
    fiscal_year: number;
    total_budgeted_expense: number;
    total_budgeted_revenue: number;
    total_actual_expense: number;
    total_actual_revenue: number;
    consumption_rate: number;
    active_budgets: number;
    active_alerts: number;
    critical_alerts: number;
  }>(`${BASE_URL}/summary${params}`);
}

async function checkControl(data: ControlCheck) {
  return api.post<ControlResult>(`${BASE_URL}/control/check`, data);
}

// ============================================================================
// EXPORT
// ============================================================================

export const budgetApi = {
  // Categories
  listCategories,
  getCategory,
  createCategory,
  updateCategory,
  deleteCategory,

  // Budgets
  listBudgets,
  getBudget,
  createBudget,
  updateBudget,
  deleteBudget,
  submitBudget,
  approveBudget,
  rejectBudget,
  activateBudget,
  closeBudget,

  // Lines
  listLines,
  addLine,
  updateLine,
  deleteLine,

  // Actuals
  recordActual,
  importActuals,

  // Variances
  getVariances,
  getExecutionRate,

  // Revisions
  listRevisions,
  createRevision,
  submitRevision,
  approveRevision,
  applyRevision,

  // Scenarios
  listScenarios,
  createScenario,

  // Forecasts
  listForecasts,
  createForecast,

  // Alerts
  listAlerts,
  acknowledgeAlert,
  resolveAlert,

  // Dashboard & Control
  getDashboard,
  getSummary,
  checkControl,
};

export default budgetApi;
