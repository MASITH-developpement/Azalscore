/**
 * AZALSCORE Module - BUDGET - Types
 * ==================================
 * Types TypeScript pour la gestion budgetaire
 */

// ============================================================================
// ENUMS
// ============================================================================

export type BudgetType = 'OPERATING' | 'INVESTMENT' | 'CASH_FLOW' | 'PROJECT' | 'CONSOLIDATED';
export type BudgetStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'ACTIVE' | 'CLOSED' | 'CANCELLED';
export type BudgetLineType = 'REVENUE' | 'EXPENSE' | 'INVESTMENT';
export type BudgetPeriodType = 'ANNUAL' | 'SEMI_ANNUAL' | 'QUARTERLY' | 'MONTHLY';
export type AllocationMethod = 'EQUAL' | 'SEASONAL' | 'PROGRESSIVE' | 'CUSTOM';
export type ControlMode = 'NONE' | 'WARNING_ONLY' | 'SOFT_BLOCK' | 'HARD_BLOCK';
export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL';
export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED' | 'EXPIRED';
export type RevisionStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'APPLIED';
export type ScenarioType = 'WHAT_IF' | 'OPTIMISTIC' | 'PESSIMISTIC' | 'BASELINE';
export type ForecastConfidence = 'LOW' | 'MEDIUM' | 'HIGH' | 'VERY_HIGH';
export type VarianceType = 'FAVORABLE' | 'UNFAVORABLE' | 'ON_TARGET';

// ============================================================================
// INTERFACES
// ============================================================================

export interface BudgetCategory {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  line_type: BudgetLineType;
  parent_id?: string;
  level: number;
  path?: string;
  account_codes: string[];
  sort_order: number;
  is_active: boolean;
  is_summary: boolean;
  created_at: string;
  updated_at: string;
}

export interface BudgetLine {
  id: string;
  tenant_id: string;
  budget_id: string;
  category_id: string;
  code?: string;
  name: string;
  description?: string;
  line_type: BudgetLineType;
  annual_amount: number;
  monthly_distribution: Record<string, number>;
  allocation_method: AllocationMethod;
  seasonal_profile?: string;
  quantity?: number;
  unit?: string;
  unit_price?: number;
  cost_center_id?: string;
  project_id?: string;
  department_id?: string;
  account_code?: string;
  parent_line_id?: string;
  sort_order: number;
  is_summary: boolean;
  ytd_actual: number;
  ytd_committed: number;
  remaining_budget: number;
  consumption_rate: number;
  notes?: string;
  assumptions?: string;
  created_at: string;
  updated_at: string;
}

export interface BudgetPeriod {
  id: string;
  tenant_id: string;
  budget_id: string;
  period_number: number;
  name: string;
  start_date: string;
  end_date: string;
  is_open: boolean;
  is_locked: boolean;
  total_budget: number;
  total_actual: number;
  total_committed: number;
  total_available: number;
  variance: number;
}

export interface Budget {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  budget_type: BudgetType;
  period_type: BudgetPeriodType;
  status: BudgetStatus;
  fiscal_year: number;
  start_date: string;
  end_date: string;
  currency: string;
  entity_id?: string;
  department_id?: string;
  cost_center_id?: string;
  project_id?: string;
  control_mode: ControlMode;
  warning_threshold: number;
  critical_threshold: number;
  version_number: number;
  is_current_version: boolean;
  parent_budget_id?: string;
  total_revenue: number;
  total_expense: number;
  total_investment: number;
  net_result: number;
  owner_id?: string;
  approvers: string[];
  notes?: string;
  assumptions?: string;
  objectives?: string;
  tags: string[];
  submitted_at?: string;
  approved_at?: string;
  activated_at?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface BudgetDetail extends Budget {
  lines: BudgetLine[];
  periods: BudgetPeriod[];
  approval_history: Record<string, unknown>[];
}

export interface BudgetAlert {
  id: string;
  tenant_id: string;
  budget_id: string;
  budget_line_id?: string;
  alert_type: string;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  message: string;
  threshold_percent?: number;
  current_percent?: number;
  budget_amount?: number;
  actual_amount?: number;
  period?: string;
  triggered_at: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  resolved_at?: string;
}

export interface BudgetVariance {
  category_id?: string;
  category_name: string;
  budget_line_id?: string;
  line_name?: string;
  period: string;
  line_type: BudgetLineType;
  budget_amount: number;
  actual_amount: number;
  committed_amount: number;
  available_amount: number;
  variance_amount: number;
  variance_percent: number;
  variance_type: VarianceType;
  budget_ytd: number;
  actual_ytd: number;
  variance_ytd: number;
  variance_ytd_percent: number;
}

export interface BudgetRevision {
  id: string;
  tenant_id: string;
  budget_id: string;
  revision_number: number;
  name: string;
  description?: string;
  status: RevisionStatus;
  effective_date: string;
  reason: string;
  impact_analysis?: string;
  total_change_amount: number;
  submitted_at?: string;
  submitted_by?: string;
  approved_at?: string;
  approved_by?: string;
  applied_at?: string;
  details: RevisionDetail[];
  created_at: string;
  created_by?: string;
}

export interface RevisionDetail {
  id: string;
  budget_line_id?: string;
  previous_amount: number;
  new_amount: number;
  change_amount: number;
  affected_period?: number;
  justification?: string;
}

export interface BudgetScenario {
  id: string;
  tenant_id: string;
  budget_id: string;
  name: string;
  description?: string;
  scenario_type: ScenarioType;
  is_active: boolean;
  is_default: boolean;
  revenue_adjustment_percent: number;
  expense_adjustment_percent: number;
  assumptions?: Record<string, unknown>;
  total_revenue: number;
  total_expense: number;
  net_result: number;
  variance_vs_baseline?: number;
  lines: ScenarioLine[];
  created_at: string;
  created_by?: string;
}

export interface ScenarioLine {
  id: string;
  scenario_id: string;
  budget_line_id: string;
  original_amount: number;
  adjusted_amount: number;
  adjustment_percent?: number;
  variance?: number;
  justification?: string;
}

export interface BudgetForecast {
  id: string;
  tenant_id: string;
  budget_id: string;
  budget_line_id?: string;
  forecast_date: string;
  period: string;
  original_budget: number;
  revised_forecast: number;
  variance: number;
  variance_percent?: number;
  confidence: ForecastConfidence;
  probability?: number;
  assumptions?: string;
  methodology?: string;
  created_at: string;
  created_by?: string;
}

export interface BudgetExecutionRate {
  budget_id: string;
  as_of_period: string;
  expense: Record<string, unknown>;
  revenue: Record<string, unknown>;
  investment?: Record<string, unknown>;
  net_result: Record<string, unknown>;
  consumption_rate: number;
  remaining_budget: number;
}

export interface BudgetSummary {
  id: string;
  code: string;
  name: string;
  budget_type: BudgetType;
  status: BudgetStatus;
  fiscal_year: number;
  version_number: number;
  total_revenue: number;
  total_expense: number;
  total_investment: number;
  net_result: number;
  ytd_actual_expense: number;
  ytd_actual_revenue: number;
  consumption_rate: number;
  alerts_count: number;
  lines_count: number;
  execution_rate?: BudgetExecutionRate;
}

export interface BudgetDashboard {
  tenant_id: string;
  fiscal_year: number;
  as_of_date: string;
  total_budgeted_expense: number;
  total_budgeted_revenue: number;
  total_actual_expense: number;
  total_actual_revenue: number;
  total_variance: number;
  overall_consumption_rate: number;
  active_budgets_count: number;
  budgets_summary: BudgetSummary[];
  active_alerts_count: number;
  critical_alerts_count: number;
  recent_alerts: BudgetAlert[];
  top_overruns: BudgetVariance[];
  top_savings: BudgetVariance[];
  monthly_trend: Record<string, unknown>[];
}

// ============================================================================
// CONFIGURATION
// ============================================================================

export const BUDGET_TYPE_CONFIG: Record<BudgetType, { label: string; color: string }> = {
  OPERATING: { label: 'Exploitation', color: 'blue' },
  INVESTMENT: { label: 'Investissement', color: 'purple' },
  CASH_FLOW: { label: 'Tresorerie', color: 'green' },
  PROJECT: { label: 'Projet', color: 'orange' },
  CONSOLIDATED: { label: 'Consolide', color: 'gray' },
};

export const BUDGET_STATUS_CONFIG: Record<BudgetStatus, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray' },
  SUBMITTED: { label: 'Soumis', color: 'blue' },
  APPROVED: { label: 'Approuve', color: 'green' },
  ACTIVE: { label: 'Actif', color: 'green' },
  CLOSED: { label: 'Cloture', color: 'purple' },
  CANCELLED: { label: 'Annule', color: 'red' },
};

export const LINE_TYPE_CONFIG: Record<BudgetLineType, { label: string; color: string }> = {
  REVENUE: { label: 'Recette', color: 'green' },
  EXPENSE: { label: 'Depense', color: 'red' },
  INVESTMENT: { label: 'Investissement', color: 'purple' },
};

export const ALERT_SEVERITY_CONFIG: Record<AlertSeverity, { label: string; color: string }> = {
  INFO: { label: 'Information', color: 'blue' },
  WARNING: { label: 'Avertissement', color: 'orange' },
  CRITICAL: { label: 'Critique', color: 'red' },
};

export const VARIANCE_TYPE_CONFIG: Record<VarianceType, { label: string; color: string }> = {
  FAVORABLE: { label: 'Favorable', color: 'green' },
  UNFAVORABLE: { label: 'Defavorable', color: 'red' },
  ON_TARGET: { label: 'Conforme', color: 'blue' },
};

export const SCENARIO_TYPE_CONFIG: Record<ScenarioType, { label: string }> = {
  WHAT_IF: { label: 'Hypothetique' },
  OPTIMISTIC: { label: 'Optimiste' },
  PESSIMISTIC: { label: 'Pessimiste' },
  BASELINE: { label: 'Reference' },
};
