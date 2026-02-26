/**
 * AZALSCORE - Consolidation API
 * ==============================
 * Complete typed API client for Multi-Entity Accounting Consolidation module.
 * Covers: Perimeters, Entities, Participations, Packages, Eliminations, Restatements, Reports
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const consolidationKeys = {
  all: ['consolidation'] as const,

  // Perimeters
  perimeters: () => [...consolidationKeys.all, 'perimeters'] as const,
  perimeter: (id: string) => [...consolidationKeys.perimeters(), id] as const,

  // Entities
  entities: (perimeterId?: string) => [...consolidationKeys.all, 'entities', perimeterId] as const,
  entity: (id: string) => [...consolidationKeys.all, 'entity', id] as const,

  // Participations
  participations: (perimeterId?: string) => [...consolidationKeys.all, 'participations', perimeterId] as const,

  // Exchange Rates
  exchangeRates: () => [...consolidationKeys.all, 'exchange-rates'] as const,

  // Consolidations
  consolidations: (perimeterId?: string) => [...consolidationKeys.all, 'consolidations', perimeterId] as const,
  consolidation: (id: string) => [...consolidationKeys.all, 'consolidation', id] as const,
  consolidationProgress: (id: string) => [...consolidationKeys.consolidation(id), 'progress'] as const,

  // Packages
  packages: (consolidationId?: string) => consolidationId
    ? [...consolidationKeys.consolidation(consolidationId), 'packages'] as const
    : [...consolidationKeys.all, 'packages'] as const,
  package: (id: string) => [...consolidationKeys.all, 'package', id] as const,

  // Eliminations
  eliminations: (consolidationId?: string) => consolidationId
    ? [...consolidationKeys.consolidation(consolidationId), 'eliminations'] as const
    : [...consolidationKeys.all, 'eliminations'] as const,

  // Restatements
  restatements: (consolidationId?: string) => consolidationId
    ? [...consolidationKeys.consolidation(consolidationId), 'restatements'] as const
    : [...consolidationKeys.all, 'restatements'] as const,

  // Intercompany Reconciliation
  reconciliations: (consolidationId?: string) => consolidationId
    ? [...consolidationKeys.consolidation(consolidationId), 'reconciliations'] as const
    : [...consolidationKeys.all, 'reconciliations'] as const,

  // Goodwill
  goodwillCalculations: (consolidationId?: string) => consolidationId
    ? [...consolidationKeys.consolidation(consolidationId), 'goodwill'] as const
    : [...consolidationKeys.all, 'goodwill'] as const,

  // Reports
  reports: (consolidationId?: string) => consolidationId
    ? [...consolidationKeys.consolidation(consolidationId), 'reports'] as const
    : [...consolidationKeys.all, 'reports'] as const,

  // Account Mappings
  accountMappings: (perimeterId?: string) => perimeterId
    ? [...consolidationKeys.perimeter(perimeterId), 'account-mappings'] as const
    : [...consolidationKeys.all, 'account-mappings'] as const,

  // Dashboard
  dashboard: () => [...consolidationKeys.all, 'dashboard'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type AccountingStandard = 'FRENCH_GAAP' | 'IFRS' | 'US_GAAP';
export type ConsolidationMethod = 'FULL' | 'PROPORTIONAL' | 'EQUITY' | 'NOT_CONSOLIDATED';
export type ControlType = 'EXCLUSIVE' | 'JOINT' | 'SIGNIFICANT_INFLUENCE' | 'NONE';
export type ConsolidationStatus = 'DRAFT' | 'IN_PROGRESS' | 'SUBMITTED' | 'VALIDATED' | 'PUBLISHED' | 'ARCHIVED';
export type PackageStatus = 'DRAFT' | 'SUBMITTED' | 'VALIDATED' | 'REJECTED';
export type EliminationType = 'INTERCOMPANY_RECEIVABLE_PAYABLE' | 'INTERCOMPANY_REVENUE_EXPENSE' | 'DIVIDENDS' | 'EQUITY' | 'MARGIN_INVENTORY' | 'MARGIN_FIXED_ASSETS' | 'OTHER';
export type RestatementType = 'LEASE_CAPITALIZATION' | 'PENSION_PROVISION' | 'DEPRECIATION_METHOD' | 'INVENTORY_VALUATION' | 'REVENUE_RECOGNITION' | 'DEFERRED_TAX' | 'OTHER';
export type CurrencyConversionMethod = 'CLOSING_RATE' | 'AVERAGE_RATE' | 'HISTORICAL_RATE';
export type ReportType = 'BALANCE_SHEET' | 'INCOME_STATEMENT' | 'CASH_FLOW' | 'EQUITY_VARIATION' | 'NOTES' | 'SEGMENT' | 'INTERCOMPANY';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface ConsolidationPerimeter {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string | null;
  fiscal_year: number;
  start_date: string;
  end_date: string;
  consolidation_currency: string;
  accounting_standard: AccountingStandard;
  status: ConsolidationStatus;
  is_active: boolean;
  version: number;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
  entity_count?: number;
  consolidation_count?: number;
}

export interface ConsolidationEntity {
  id: string;
  tenant_id: string;
  perimeter_id: string;
  parent_entity_id?: string | null;
  code: string;
  name: string;
  legal_name?: string | null;
  registration_number?: string | null;
  country: string;
  currency: string;
  is_parent: boolean;
  consolidation_method: ConsolidationMethod;
  control_type: ControlType;
  direct_ownership_pct: number;
  indirect_ownership_pct: number;
  voting_rights_pct: number;
  integration_pct: number;
  total_ownership_pct: number;
  acquisition_date?: string | null;
  disposal_date?: string | null;
  fiscal_year_end_month: number;
  sector?: string | null;
  segment?: string | null;
  is_active: boolean;
  version: number;
  created_at: string;
  updated_at: string;
  parent_name?: string | null;
  subsidiaries_count?: number;
}

export interface Participation {
  id: string;
  tenant_id: string;
  parent_id: string;
  subsidiary_id: string;
  direct_ownership: number;
  indirect_ownership: number;
  voting_rights: number;
  total_ownership: number;
  acquisition_date: string;
  acquisition_cost: number;
  fair_value_at_acquisition: number;
  goodwill_amount: number;
  goodwill_impairment: number;
  goodwill_currency: string;
  notes?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  parent_name?: string | null;
  subsidiary_name?: string | null;
}

export interface ExchangeRate {
  id: string;
  tenant_id: string;
  from_currency: string;
  to_currency: string;
  rate_date: string;
  closing_rate: number;
  average_rate: number;
  historical_rate?: number | null;
  source?: string | null;
  created_at: string;
}

export interface Consolidation {
  id: string;
  tenant_id: string;
  perimeter_id: string;
  code: string;
  name: string;
  description?: string | null;
  period_start: string;
  period_end: string;
  fiscal_year: number;
  period_type: string;
  consolidation_currency: string;
  accounting_standard: AccountingStandard;
  status: ConsolidationStatus;
  // Results
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
  group_equity: number;
  minority_interests: number;
  consolidated_revenue: number;
  consolidated_net_income: number;
  group_net_income: number;
  minority_net_income: number;
  translation_difference: number;
  total_goodwill: number;
  // Workflow
  submitted_at?: string | null;
  validated_at?: string | null;
  published_at?: string | null;
  // Audit
  version: number;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
  // Statistics
  packages_count?: number;
  packages_validated?: number;
  eliminations_count?: number;
}

export interface TrialBalanceEntry {
  account_code: string;
  account_name: string;
  debit: number;
  credit: number;
  balance: number;
  currency: string;
}

export interface IntercompanyDetail {
  counterparty_entity_id: string;
  counterparty_code: string;
  transaction_type: string;
  account_code: string;
  amount: number;
  currency: string;
  description?: string | null;
}

export interface ConsolidationPackage {
  id: string;
  tenant_id: string;
  consolidation_id: string;
  entity_id: string;
  period_start: string;
  period_end: string;
  local_currency: string;
  reporting_currency: string;
  status: PackageStatus;
  // Local amounts
  total_assets_local: number;
  total_liabilities_local: number;
  total_equity_local: number;
  net_income_local: number;
  // Intercompany
  intercompany_receivables: number;
  intercompany_payables: number;
  intercompany_sales: number;
  intercompany_purchases: number;
  dividends_to_parent: number;
  // Exchange rates
  closing_rate?: number | null;
  average_rate?: number | null;
  // Converted amounts
  total_assets_converted: number;
  total_liabilities_converted: number;
  total_equity_converted: number;
  net_income_converted: number;
  translation_difference: number;
  // Details
  trial_balance: TrialBalanceEntry[];
  intercompany_details: IntercompanyDetail[];
  is_audited: boolean;
  auditor_notes?: string | null;
  // Workflow
  submitted_at?: string | null;
  validated_at?: string | null;
  rejected_at?: string | null;
  rejection_reason?: string | null;
  // Audit
  version: number;
  created_at: string;
  updated_at: string;
  // Relations
  entity_name?: string | null;
  entity_code?: string | null;
}

export interface JournalEntryLine {
  account: string;
  debit: number;
  credit: number;
  label: string;
  entity_id?: string | null;
}

export interface EliminationEntry {
  id: string;
  tenant_id: string;
  consolidation_id: string;
  code?: string | null;
  elimination_type: EliminationType;
  description: string;
  amount: number;
  currency: string;
  entity1_id?: string | null;
  entity2_id?: string | null;
  source_document_type?: string | null;
  source_document_id?: string | null;
  journal_entries: JournalEntryLine[];
  is_automatic: boolean;
  is_validated: boolean;
  validated_at?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  entity1_name?: string | null;
  entity2_name?: string | null;
}

export interface Restatement {
  id: string;
  tenant_id: string;
  consolidation_id: string;
  entity_id: string;
  code?: string | null;
  restatement_type: RestatementType;
  description: string;
  standard_reference?: string | null;
  impact_assets: number;
  impact_liabilities: number;
  impact_equity: number;
  impact_income: number;
  impact_expense: number;
  tax_impact: number;
  journal_entries: JournalEntryLine[];
  calculation_details: Record<string, unknown>;
  is_recurring: boolean;
  recurrence_pattern?: string | null;
  is_validated: boolean;
  validated_at?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  entity_name?: string | null;
}

export interface IntercompanyReconciliation {
  id: string;
  tenant_id: string;
  consolidation_id: string;
  entity1_id: string;
  entity2_id: string;
  transaction_type: string;
  amount_entity1: number;
  amount_entity2: number;
  currency: string;
  difference: number;
  difference_pct: number;
  tolerance_amount: number;
  tolerance_pct: number;
  is_reconciled: boolean;
  reconciled_at?: string | null;
  is_within_tolerance: boolean;
  difference_reason?: string | null;
  action_required?: string | null;
  action_taken?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  entity1_name?: string | null;
  entity2_name?: string | null;
}

export interface ReconciliationSummary {
  total_pairs: number;
  reconciled_count: number;
  unreconciled_count: number;
  within_tolerance_count: number;
  total_difference: number;
  by_type: Record<string, number>;
}

export interface GoodwillCalculation {
  id: string;
  tenant_id: string;
  consolidation_id: string;
  participation_id: string;
  calculation_date: string;
  acquisition_cost: number;
  acquisition_currency: string;
  assets_fair_value: number;
  liabilities_fair_value: number;
  ownership_percentage: number;
  revaluation_adjustments: Array<Record<string, unknown>>;
  notes?: string | null;
  net_assets_fair_value: number;
  group_share_net_assets: number;
  goodwill_amount: number;
  badwill_amount: number;
  cumulative_impairment: number;
  current_period_impairment: number;
  carrying_value: number;
  impairment_test_date?: string | null;
  impairment_test_result?: Record<string, unknown> | null;
  version: number;
  created_at: string;
  updated_at: string;
  subsidiary_name?: string | null;
}

export interface ConsolidatedReport {
  id: string;
  tenant_id: string;
  consolidation_id: string;
  report_type: ReportType;
  name: string;
  description?: string | null;
  period_start: string;
  period_end: string;
  parameters: Record<string, unknown>;
  report_data: Record<string, unknown>;
  comparative_data?: Record<string, unknown> | null;
  pdf_url?: string | null;
  excel_url?: string | null;
  generated_at?: string | null;
  is_final: boolean;
  finalized_at?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface AccountMapping {
  id: string;
  tenant_id: string;
  perimeter_id: string;
  entity_id?: string | null;
  local_account_code: string;
  local_account_label?: string | null;
  group_account_code: string;
  group_account_label?: string | null;
  reporting_category?: string | null;
  reporting_subcategory?: string | null;
  currency_method: CurrencyConversionMethod;
  is_active: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ConsolidationDashboard {
  active_perimeters: number;
  total_entities: number;
  entities_by_method: Record<string, number>;
  consolidations_in_progress: number;
  consolidations_validated: number;
  packages_pending: number;
  packages_validated: number;
  packages_rejected: number;
  total_intercompany_balance: number;
  unreconciled_items: number;
  reconciliation_rate: number;
  total_eliminations: number;
  elimination_amount: number;
  total_goodwill: number;
  total_impairment: number;
}

export interface ConsolidationProgress {
  consolidation_id: string;
  total_entities: number;
  packages_submitted: number;
  packages_validated: number;
  packages_rejected: number;
  completion_pct: number;
  eliminations_generated: boolean;
  restatements_validated: boolean;
  reports_generated: string[];
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface PerimeterCreate {
  code: string;
  name: string;
  description?: string;
  fiscal_year: number;
  start_date: string;
  end_date: string;
  consolidation_currency?: string;
  accounting_standard?: AccountingStandard;
}

export interface PerimeterUpdate {
  name?: string;
  description?: string;
  consolidation_currency?: string;
  accounting_standard?: AccountingStandard;
  status?: ConsolidationStatus;
  is_active?: boolean;
}

export interface EntityCreate {
  perimeter_id: string;
  parent_entity_id?: string;
  code: string;
  name: string;
  legal_name?: string;
  registration_number?: string;
  country: string;
  currency: string;
  is_parent?: boolean;
  consolidation_method?: ConsolidationMethod;
  control_type?: ControlType;
  direct_ownership_pct?: number;
  indirect_ownership_pct?: number;
  voting_rights_pct?: number;
  integration_pct?: number;
  acquisition_date?: string;
  disposal_date?: string;
  fiscal_year_end_month?: number;
  sector?: string;
  segment?: string;
}

export interface EntityUpdate {
  name?: string;
  legal_name?: string;
  registration_number?: string;
  country?: string;
  currency?: string;
  parent_entity_id?: string;
  consolidation_method?: ConsolidationMethod;
  control_type?: ControlType;
  direct_ownership_pct?: number;
  indirect_ownership_pct?: number;
  voting_rights_pct?: number;
  integration_pct?: number;
  acquisition_date?: string;
  disposal_date?: string;
  sector?: string;
  segment?: string;
  is_active?: boolean;
}

export interface ParticipationCreate {
  parent_id: string;
  subsidiary_id: string;
  direct_ownership: number;
  indirect_ownership?: number;
  voting_rights?: number;
  acquisition_date: string;
  acquisition_cost?: number;
  fair_value_at_acquisition?: number;
  goodwill_amount?: number;
  goodwill_currency?: string;
  notes?: string;
}

export interface ParticipationUpdate {
  direct_ownership?: number;
  indirect_ownership?: number;
  voting_rights?: number;
  acquisition_cost?: number;
  fair_value_at_acquisition?: number;
  goodwill_amount?: number;
  goodwill_impairment?: number;
  notes?: string;
}

export interface ExchangeRateCreate {
  from_currency: string;
  to_currency: string;
  rate_date: string;
  closing_rate: number;
  average_rate: number;
  historical_rate?: number;
  source?: string;
}

export interface ConsolidationCreate {
  perimeter_id: string;
  code: string;
  name: string;
  description?: string;
  period_start: string;
  period_end: string;
  fiscal_year: number;
  period_type?: string;
  consolidation_currency?: string;
  accounting_standard?: AccountingStandard;
}

export interface ConsolidationUpdate {
  name?: string;
  description?: string;
  status?: ConsolidationStatus;
  metadata?: Record<string, unknown>;
}

export interface PackageCreate {
  consolidation_id: string;
  entity_id: string;
  period_start: string;
  period_end: string;
  local_currency: string;
  total_assets_local?: number;
  total_liabilities_local?: number;
  total_equity_local?: number;
  net_income_local?: number;
  intercompany_receivables?: number;
  intercompany_payables?: number;
  intercompany_sales?: number;
  intercompany_purchases?: number;
  dividends_to_parent?: number;
  trial_balance?: TrialBalanceEntry[];
  intercompany_details?: IntercompanyDetail[];
  is_audited?: boolean;
  auditor_notes?: string;
}

export interface PackageUpdate {
  total_assets_local?: number;
  total_liabilities_local?: number;
  total_equity_local?: number;
  net_income_local?: number;
  intercompany_receivables?: number;
  intercompany_payables?: number;
  intercompany_sales?: number;
  intercompany_purchases?: number;
  dividends_to_parent?: number;
  trial_balance?: TrialBalanceEntry[];
  intercompany_details?: IntercompanyDetail[];
  is_audited?: boolean;
  auditor_notes?: string;
}

export interface EliminationCreate {
  consolidation_id: string;
  elimination_type: EliminationType;
  description: string;
  amount: number;
  currency?: string;
  entity1_id?: string;
  entity2_id?: string;
  source_document_type?: string;
  source_document_id?: string;
  journal_entries?: JournalEntryLine[];
  is_automatic?: boolean;
}

export interface EliminationUpdate {
  description?: string;
  amount?: number;
  journal_entries?: JournalEntryLine[];
  is_validated?: boolean;
}

export interface RestatementCreate {
  consolidation_id: string;
  entity_id: string;
  restatement_type: RestatementType;
  description: string;
  standard_reference?: string;
  impact_assets?: number;
  impact_liabilities?: number;
  impact_equity?: number;
  impact_income?: number;
  impact_expense?: number;
  tax_impact?: number;
  journal_entries?: JournalEntryLine[];
  calculation_details?: Record<string, unknown>;
  is_recurring?: boolean;
  recurrence_pattern?: string;
}

export interface RestatementUpdate {
  description?: string;
  impact_assets?: number;
  impact_liabilities?: number;
  impact_equity?: number;
  impact_income?: number;
  impact_expense?: number;
  tax_impact?: number;
  journal_entries?: JournalEntryLine[];
  calculation_details?: Record<string, unknown>;
  is_validated?: boolean;
}

export interface ReconciliationCreate {
  consolidation_id: string;
  entity1_id: string;
  entity2_id: string;
  transaction_type: string;
  amount_entity1: number;
  amount_entity2: number;
  currency?: string;
  difference_reason?: string;
  tolerance_amount?: number;
  tolerance_pct?: number;
}

export interface ReconciliationUpdate {
  amount_entity1?: number;
  amount_entity2?: number;
  difference_reason?: string;
  action_required?: string;
  action_taken?: string;
  is_reconciled?: boolean;
}

export interface GoodwillUpdate {
  current_period_impairment?: number;
  impairment_test_date?: string;
  impairment_test_result?: Record<string, unknown>;
  notes?: string;
}

export interface AccountMappingCreate {
  perimeter_id: string;
  entity_id?: string;
  local_account_code: string;
  local_account_label?: string;
  group_account_code: string;
  group_account_label?: string;
  reporting_category?: string;
  reporting_subcategory?: string;
  currency_method?: CurrencyConversionMethod;
}

export interface GenerateReportRequest {
  consolidation_id: string;
  report_type: ReportType;
  include_comparative?: boolean;
  comparative_consolidation_id?: string;
  parameters?: Record<string, unknown>;
}

// ============================================================================
// HOOKS - PERIMETERS
// ============================================================================

export function usePerimeters(filters?: {
  fiscal_year?: number;
  status?: ConsolidationStatus;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...consolidationKeys.perimeters(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.fiscal_year) params.append('fiscal_year', String(filters.fiscal_year));
      if (filters?.status) params.append('status', filters.status);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ConsolidationPerimeter[]; total: number; page: number; per_page: number; pages: number }>(
        `/consolidation/perimeters${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function usePerimeter(id: string) {
  return useQuery({
    queryKey: consolidationKeys.perimeter(id),
    queryFn: async () => {
      const response = await api.get<ConsolidationPerimeter>(`/consolidation/perimeters/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreatePerimeter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: PerimeterCreate) => {
      return api.post<ConsolidationPerimeter>('/consolidation/perimeters', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.perimeters() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function useUpdatePerimeter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PerimeterUpdate }) => {
      return api.put<ConsolidationPerimeter>(`/consolidation/perimeters/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.perimeters() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.perimeter(id) });
    },
  });
}

export function useDeletePerimeter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/consolidation/perimeters/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.perimeters() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

// ============================================================================
// HOOKS - ENTITIES
// ============================================================================

export function useConsolidationEntities(perimeterId: string, filters?: {
  country?: string;
  currency?: string;
  consolidation_method?: ConsolidationMethod;
  is_parent?: boolean;
  is_active?: boolean;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...consolidationKeys.entities(perimeterId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.country) params.append('country', filters.country);
      if (filters?.currency) params.append('currency', filters.currency);
      if (filters?.consolidation_method) params.append('consolidation_method', filters.consolidation_method);
      if (filters?.is_parent !== undefined) params.append('is_parent', String(filters.is_parent));
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ConsolidationEntity[]; total: number; page: number; per_page: number; pages: number }>(
        `/consolidation/perimeters/${perimeterId}/entities${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!perimeterId,
  });
}

export function useConsolidationEntity(id: string) {
  return useQuery({
    queryKey: consolidationKeys.entity(id),
    queryFn: async () => {
      const response = await api.get<ConsolidationEntity>(`/consolidation/entities/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateEntity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: EntityCreate) => {
      return api.post<ConsolidationEntity>('/consolidation/entities', data);
    },
    onSuccess: (_, { perimeter_id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.entities(perimeter_id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.perimeter(perimeter_id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function useUpdateEntity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: EntityUpdate }) => {
      return api.put<ConsolidationEntity>(`/consolidation/entities/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.entity(id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.entities() });
    },
  });
}

export function useDeleteEntity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/consolidation/entities/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.entities() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function useEntityHierarchy(perimeterId: string) {
  return useQuery({
    queryKey: [...consolidationKeys.entities(perimeterId), 'hierarchy'],
    queryFn: async () => {
      const response = await api.get<{ entities: ConsolidationEntity[]; tree: Record<string, unknown> }>(
        `/consolidation/perimeters/${perimeterId}/entities/hierarchy`
      );
      return response;
    },
    enabled: !!perimeterId,
  });
}

// ============================================================================
// HOOKS - PARTICIPATIONS
// ============================================================================

export function useParticipations(perimeterId: string) {
  return useQuery({
    queryKey: consolidationKeys.participations(perimeterId),
    queryFn: async () => {
      const response = await api.get<{ items: Participation[] }>(
        `/consolidation/perimeters/${perimeterId}/participations`
      );
      return response;
    },
    enabled: !!perimeterId,
  });
}

export function useCreateParticipation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ParticipationCreate) => {
      return api.post<Participation>('/consolidation/participations', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.participations() });
    },
  });
}

export function useUpdateParticipation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ParticipationUpdate }) => {
      return api.put<Participation>(`/consolidation/participations/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.participations() });
    },
  });
}

// ============================================================================
// HOOKS - EXCHANGE RATES
// ============================================================================

export function useExchangeRates(filters?: {
  from_currency?: string;
  to_currency?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...consolidationKeys.exchangeRates(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.from_currency) params.append('from_currency', filters.from_currency);
      if (filters?.to_currency) params.append('to_currency', filters.to_currency);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ExchangeRate[]; total: number; page: number; per_page: number; pages: number }>(
        `/consolidation/exchange-rates${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCreateExchangeRate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ExchangeRateCreate) => {
      return api.post<ExchangeRate>('/consolidation/exchange-rates', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.exchangeRates() });
    },
  });
}

export function useBulkCreateExchangeRates() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (rates: ExchangeRateCreate[]) => {
      return api.post<{ created: number }>('/consolidation/exchange-rates/bulk', { rates });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.exchangeRates() });
    },
  });
}

export function useImportExchangeRates() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ source, date }: { source: string; date: string }) => {
      return api.post<{ imported: number }>('/consolidation/exchange-rates/import', { source, date });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.exchangeRates() });
    },
  });
}

// ============================================================================
// HOOKS - CONSOLIDATIONS
// ============================================================================

export function useConsolidations(perimeterId?: string, filters?: {
  fiscal_year?: number;
  status?: ConsolidationStatus;
  accounting_standard?: AccountingStandard;
  date_from?: string;
  date_to?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...consolidationKeys.consolidations(perimeterId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (perimeterId) params.append('perimeter_id', perimeterId);
      if (filters?.fiscal_year) params.append('fiscal_year', String(filters.fiscal_year));
      if (filters?.status) params.append('status', filters.status);
      if (filters?.accounting_standard) params.append('accounting_standard', filters.accounting_standard);
      if (filters?.date_from) params.append('date_from', filters.date_from);
      if (filters?.date_to) params.append('date_to', filters.date_to);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Consolidation[]; total: number; page: number; per_page: number; pages: number }>(
        `/consolidation/consolidations${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useConsolidation(id: string) {
  return useQuery({
    queryKey: consolidationKeys.consolidation(id),
    queryFn: async () => {
      const response = await api.get<Consolidation>(`/consolidation/consolidations/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useConsolidationProgress(id: string) {
  return useQuery({
    queryKey: consolidationKeys.consolidationProgress(id),
    queryFn: async () => {
      const response = await api.get<ConsolidationProgress>(`/consolidation/consolidations/${id}/progress`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateConsolidation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ConsolidationCreate) => {
      return api.post<Consolidation>('/consolidation/consolidations', data);
    },
    onSuccess: (_, { perimeter_id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidations(perimeter_id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.perimeter(perimeter_id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function useUpdateConsolidation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ConsolidationUpdate }) => {
      return api.put<Consolidation>(`/consolidation/consolidations/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidation(id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidations() });
    },
  });
}

export function useDeleteConsolidation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/consolidation/consolidations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidations() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function useSubmitConsolidation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Consolidation>(`/consolidation/consolidations/${id}/submit`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidation(id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidations() });
    },
  });
}

export function useValidateConsolidation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Consolidation>(`/consolidation/consolidations/${id}/validate`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidation(id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidations() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function usePublishConsolidation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Consolidation>(`/consolidation/consolidations/${id}/publish`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidation(id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidations() });
    },
  });
}

export function useRecalculateConsolidation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<Consolidation>(`/consolidation/consolidations/${id}/recalculate`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidation(id) });
    },
  });
}

// ============================================================================
// HOOKS - PACKAGES
// ============================================================================

export function useConsolidationPackages(consolidationId: string, filters?: {
  entity_id?: string;
  status?: PackageStatus;
  is_audited?: boolean;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...consolidationKeys.packages(consolidationId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.entity_id) params.append('entity_id', filters.entity_id);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.is_audited !== undefined) params.append('is_audited', String(filters.is_audited));
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: ConsolidationPackage[]; total: number; page: number; per_page: number; pages: number }>(
        `/consolidation/consolidations/${consolidationId}/packages${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!consolidationId,
  });
}

export function useConsolidationPackage(id: string) {
  return useQuery({
    queryKey: consolidationKeys.package(id),
    queryFn: async () => {
      const response = await api.get<ConsolidationPackage>(`/consolidation/packages/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreatePackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: PackageCreate) => {
      return api.post<ConsolidationPackage>('/consolidation/packages', data);
    },
    onSuccess: (_, { consolidation_id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.packages(consolidation_id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidation(consolidation_id) });
    },
  });
}

export function useUpdatePackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: PackageUpdate }) => {
      return api.put<ConsolidationPackage>(`/consolidation/packages/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.package(id) });
    },
  });
}

export function useSubmitPackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, comments }: { id: string; comments?: string }) => {
      return api.post<ConsolidationPackage>(`/consolidation/packages/${id}/submit`, { comments });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.package(id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.packages() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function useValidatePackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, comments }: { id: string; comments?: string }) => {
      return api.post<ConsolidationPackage>(`/consolidation/packages/${id}/validate`, { comments });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.package(id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.packages() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function useRejectPackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      return api.post<ConsolidationPackage>(`/consolidation/packages/${id}/reject`, { reason });
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.package(id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.packages() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function useConvertPackage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<ConsolidationPackage>(`/consolidation/packages/${id}/convert`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.package(id) });
    },
  });
}

// ============================================================================
// HOOKS - ELIMINATIONS
// ============================================================================

export function useEliminations(consolidationId: string, filters?: {
  elimination_type?: EliminationType;
  is_validated?: boolean;
  entity_id?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...consolidationKeys.eliminations(consolidationId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.elimination_type) params.append('elimination_type', filters.elimination_type);
      if (filters?.is_validated !== undefined) params.append('is_validated', String(filters.is_validated));
      if (filters?.entity_id) params.append('entity_id', filters.entity_id);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: EliminationEntry[]; total: number; page: number; per_page: number; pages: number }>(
        `/consolidation/consolidations/${consolidationId}/eliminations${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!consolidationId,
  });
}

export function useCreateElimination() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: EliminationCreate) => {
      return api.post<EliminationEntry>('/consolidation/eliminations', data);
    },
    onSuccess: (_, { consolidation_id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.eliminations(consolidation_id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidation(consolidation_id) });
    },
  });
}

export function useUpdateElimination() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: EliminationUpdate }) => {
      return api.put<EliminationEntry>(`/consolidation/eliminations/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.eliminations() });
    },
  });
}

export function useDeleteElimination() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/consolidation/eliminations/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.eliminations() });
    },
  });
}

export function useGenerateEliminations() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ consolidationId, types }: { consolidationId: string; types?: EliminationType[] }) => {
      return api.post<{ generated_count: number; eliminations: EliminationEntry[]; warnings: string[] }>(
        `/consolidation/consolidations/${consolidationId}/generate-eliminations`,
        { elimination_types: types }
      );
    },
    onSuccess: (_, { consolidationId }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.eliminations(consolidationId) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidation(consolidationId) });
    },
  });
}

// ============================================================================
// HOOKS - RESTATEMENTS
// ============================================================================

export function useRestatements(consolidationId: string, filters?: {
  restatement_type?: RestatementType;
  entity_id?: string;
  is_validated?: boolean;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...consolidationKeys.restatements(consolidationId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.restatement_type) params.append('restatement_type', filters.restatement_type);
      if (filters?.entity_id) params.append('entity_id', filters.entity_id);
      if (filters?.is_validated !== undefined) params.append('is_validated', String(filters.is_validated));
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: Restatement[]; total: number; page: number; per_page: number; pages: number }>(
        `/consolidation/consolidations/${consolidationId}/restatements${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!consolidationId,
  });
}

export function useCreateRestatement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: RestatementCreate) => {
      return api.post<Restatement>('/consolidation/restatements', data);
    },
    onSuccess: (_, { consolidation_id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.restatements(consolidation_id) });
    },
  });
}

export function useUpdateRestatement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: RestatementUpdate }) => {
      return api.put<Restatement>(`/consolidation/restatements/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.restatements() });
    },
  });
}

export function useDeleteRestatement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/consolidation/restatements/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.restatements() });
    },
  });
}

// ============================================================================
// HOOKS - INTERCOMPANY RECONCILIATION
// ============================================================================

export function useReconciliations(consolidationId: string, filters?: {
  entity_id?: string;
  transaction_type?: string;
  is_reconciled?: boolean;
  is_within_tolerance?: boolean;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...consolidationKeys.reconciliations(consolidationId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.entity_id) params.append('entity_id', filters.entity_id);
      if (filters?.transaction_type) params.append('transaction_type', filters.transaction_type);
      if (filters?.is_reconciled !== undefined) params.append('is_reconciled', String(filters.is_reconciled));
      if (filters?.is_within_tolerance !== undefined) params.append('is_within_tolerance', String(filters.is_within_tolerance));
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: IntercompanyReconciliation[]; total: number; page: number; per_page: number; pages: number }>(
        `/consolidation/consolidations/${consolidationId}/reconciliations${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!consolidationId,
  });
}

export function useReconciliationSummary(consolidationId: string) {
  return useQuery({
    queryKey: [...consolidationKeys.reconciliations(consolidationId), 'summary'],
    queryFn: async () => {
      const response = await api.get<ReconciliationSummary>(
        `/consolidation/consolidations/${consolidationId}/reconciliations/summary`
      );
      return response;
    },
    enabled: !!consolidationId,
  });
}

export function useCreateReconciliation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: ReconciliationCreate) => {
      return api.post<IntercompanyReconciliation>('/consolidation/reconciliations', data);
    },
    onSuccess: (_, { consolidation_id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.reconciliations(consolidation_id) });
    },
  });
}

export function useUpdateReconciliation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ReconciliationUpdate }) => {
      return api.put<IntercompanyReconciliation>(`/consolidation/reconciliations/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.reconciliations() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function useAutoReconcile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (consolidationId: string) => {
      return api.post<{ reconciled_count: number; unreconciled_count: number }>(
        `/consolidation/consolidations/${consolidationId}/auto-reconcile`
      );
    },
    onSuccess: (_, consolidationId) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.reconciliations(consolidationId) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

// ============================================================================
// HOOKS - GOODWILL
// ============================================================================

export function useGoodwillCalculations(consolidationId: string) {
  return useQuery({
    queryKey: consolidationKeys.goodwillCalculations(consolidationId),
    queryFn: async () => {
      const response = await api.get<{ items: GoodwillCalculation[] }>(
        `/consolidation/consolidations/${consolidationId}/goodwill`
      );
      return response;
    },
    enabled: !!consolidationId,
  });
}

export function useUpdateGoodwill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: GoodwillUpdate }) => {
      return api.put<GoodwillCalculation>(`/consolidation/goodwill/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.goodwillCalculations() });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.dashboard() });
    },
  });
}

export function useRecalculateGoodwill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (consolidationId: string) => {
      return api.post<{ items: GoodwillCalculation[] }>(
        `/consolidation/consolidations/${consolidationId}/recalculate-goodwill`
      );
    },
    onSuccess: (_, consolidationId) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.goodwillCalculations(consolidationId) });
    },
  });
}

// ============================================================================
// HOOKS - REPORTS
// ============================================================================

export function useConsolidatedReports(consolidationId: string) {
  return useQuery({
    queryKey: consolidationKeys.reports(consolidationId),
    queryFn: async () => {
      const response = await api.get<{ items: ConsolidatedReport[]; total: number; page: number; per_page: number; pages: number }>(
        `/consolidation/consolidations/${consolidationId}/reports`
      );
      return response;
    },
    enabled: !!consolidationId,
  });
}

export function useGenerateReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: GenerateReportRequest) => {
      return api.post<ConsolidatedReport>('/consolidation/reports/generate', data);
    },
    onSuccess: (_, { consolidation_id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.reports(consolidation_id) });
      queryClient.invalidateQueries({ queryKey: consolidationKeys.consolidationProgress(consolidation_id) });
    },
  });
}

export function useFinalizeReport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<ConsolidatedReport>(`/consolidation/reports/${id}/finalize`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.reports() });
    },
  });
}

export function useExportReport() {
  return useMutation({
    mutationFn: async ({ id, format }: { id: string; format: 'pdf' | 'excel' }) => {
      return api.post<{ download_url: string; expires_at: string }>(
        `/consolidation/reports/${id}/export`,
        { format }
      );
    },
  });
}

// ============================================================================
// HOOKS - ACCOUNT MAPPINGS
// ============================================================================

export function useAccountMappings(perimeterId: string, filters?: {
  entity_id?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...consolidationKeys.accountMappings(perimeterId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.entity_id) params.append('entity_id', filters.entity_id);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: AccountMapping[]; total: number; page: number; per_page: number; pages: number }>(
        `/consolidation/perimeters/${perimeterId}/account-mappings${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!perimeterId,
  });
}

export function useCreateAccountMapping() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: AccountMappingCreate) => {
      return api.post<AccountMapping>('/consolidation/account-mappings', data);
    },
    onSuccess: (_, { perimeter_id }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.accountMappings(perimeter_id) });
    },
  });
}

export function useBulkCreateAccountMappings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ perimeterId, entityId, mappings }: {
      perimeterId: string;
      entityId?: string;
      mappings: Omit<AccountMappingCreate, 'perimeter_id' | 'entity_id'>[];
    }) => {
      return api.post<{ created: number }>('/consolidation/account-mappings/bulk', {
        perimeter_id: perimeterId,
        entity_id: entityId,
        mappings,
      });
    },
    onSuccess: (_, { perimeterId }) => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.accountMappings(perimeterId) });
    },
  });
}

export function useDeleteAccountMapping() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.delete(`/consolidation/account-mappings/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: consolidationKeys.accountMappings() });
    },
  });
}

// ============================================================================
// HOOKS - DASHBOARD
// ============================================================================

export function useConsolidationDashboard() {
  return useQuery({
    queryKey: consolidationKeys.dashboard(),
    queryFn: async () => {
      const response = await api.get<ConsolidationDashboard>('/consolidation/dashboard');
      return response;
    },
  });
}
