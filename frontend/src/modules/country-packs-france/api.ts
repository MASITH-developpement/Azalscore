/**
 * AZALSCORE - Country Packs France API
 * =====================================
 * Client API typé pour PCG, TVA, FEC, DSN, RGPD
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
// TYPES - PCG (Plan Comptable Général)
// ============================================================================

export interface PCGAccount {
  id: number;
  account_number: string;
  account_label: string;
  pcg_class: string;
  parent_account: string | null;
  is_summary: boolean;
  is_active: boolean;
  is_custom: boolean;
  normal_balance: 'D' | 'C';
  default_vat_code: string | null;
  description: string | null;
  created_at: string;
}

export interface PCGAccountCreate {
  account_number: string;
  account_label: string;
  pcg_class: string;
  parent_account?: string | null;
  is_summary?: boolean;
  normal_balance?: 'D' | 'C';
  default_vat_code?: string | null;
  description?: string | null;
}

export interface PCGAccountUpdate {
  account_label?: string;
  is_active?: boolean;
  default_vat_code?: string | null;
  description?: string | null;
  notes?: string | null;
}

// ============================================================================
// TYPES - TVA Française
// ============================================================================

export interface FRVATRate {
  id: number;
  code: string;
  name: string;
  rate_type: 'NORMAL' | 'REDUCED' | 'SUPER_REDUCED' | 'ZERO' | 'EXEMPT';
  rate: number;
  account_collected: string | null;
  account_deductible: string | null;
  applies_to_goods: boolean;
  applies_to_services: boolean;
  is_active: boolean;
  valid_from: string;
}

export interface VATDeclarationCreate {
  declaration_type?: 'CA3' | 'CA12';
  regime: 'REEL_NORMAL' | 'REEL_SIMPLIFIE' | 'MICRO';
  period_start: string;
  period_end: string;
  due_date?: string | null;
}

export interface VATDeclaration {
  id: number;
  declaration_number: string;
  declaration_type: string;
  regime: string;
  period_start: string;
  period_end: string;
  due_date: string | null;
  total_ht: number;
  total_tva_collectee: number;
  total_tva_deductible: number;
  tva_nette: number;
  credit_tva: number;
  status: 'DRAFT' | 'CALCULATED' | 'SUBMITTED' | 'ACCEPTED' | 'REJECTED';
  submitted_at: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - FEC (Fichier des Écritures Comptables)
// ============================================================================

export interface FECGenerateRequest {
  fiscal_year: number;
  period_start: string;
  period_end: string;
  siren: string;
}

export interface FECExport {
  id: number;
  file_name: string;
  fiscal_year: number;
  period_start: string;
  period_end: string;
  siren: string;
  entries_count: number;
  status: 'GENERATED' | 'VALIDATED' | 'EXPORTED';
  validation_errors: string[];
  generated_at: string;
}

export interface FECValidationResult {
  is_valid: boolean;
  errors: Array<{
    line: number;
    field: string;
    message: string;
  }>;
  warnings: Array<{
    line: number;
    field: string;
    message: string;
  }>;
}

// ============================================================================
// TYPES - DSN (Déclaration Sociale Nominative)
// ============================================================================

export interface DSNGenerateRequest {
  dsn_type: 'MENSUELLE' | 'ARRET_TRAVAIL' | 'FIN_CONTRAT' | 'REPRISE_TRAVAIL';
  period_month: number;
  period_year: number;
}

export interface DSNEmployeeData {
  employee_id: number;
  nir: string;
  nom_famille: string;
  prenoms: string;
  date_naissance: string;
  lieu_naissance: string;
  salaire_brut: number;
  salaire_net: number;
  heures_travaillees: number;
}

export interface DSNDeclaration {
  id: number;
  dsn_number: string;
  dsn_type: string;
  period_month: number;
  period_year: number;
  employees_count: number;
  total_brut: number;
  total_cotisations: number;
  status: 'DRAFT' | 'READY' | 'SUBMITTED' | 'ACCEPTED' | 'REJECTED';
  submitted_at: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - RGPD
// ============================================================================

export interface RGPDConsentCreate {
  contact_id: number;
  purpose: string;
  legal_basis: 'CONSENT' | 'CONTRACT' | 'LEGAL_OBLIGATION' | 'VITAL_INTEREST' | 'PUBLIC_INTEREST' | 'LEGITIMATE_INTEREST';
  data_categories: string[];
  retention_period_days: number;
  consent_text: string;
}

export interface RGPDConsent {
  id: number;
  contact_id: number;
  purpose: string;
  legal_basis: string;
  data_categories: string[];
  retention_period_days: number;
  consent_given_at: string;
  consent_expires_at: string | null;
  is_active: boolean;
  withdrawal_date: string | null;
}

export interface RGPDRequestCreate {
  contact_id: number;
  request_type: 'ACCESS' | 'RECTIFICATION' | 'ERASURE' | 'PORTABILITY' | 'RESTRICTION' | 'OBJECTION';
  description: string;
}

export interface RGPDRequest {
  id: number;
  request_number: string;
  contact_id: number;
  request_type: string;
  description: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED';
  due_date: string;
  completed_at: string | null;
  response: string | null;
  created_at: string;
}

export interface RGPDProcessingCreate {
  name: string;
  purpose: string;
  legal_basis: string;
  data_categories: string[];
  recipients: string[];
  retention_period_days: number;
  security_measures: string[];
  dpo_contact?: string | null;
}

export interface RGPDProcessing {
  id: number;
  name: string;
  purpose: string;
  legal_basis: string;
  data_categories: string[];
  recipients: string[];
  retention_period_days: number;
  security_measures: string[];
  is_active: boolean;
  created_at: string;
}

export interface RGPDBreachCreate {
  breach_date: string;
  description: string;
  data_affected: string[];
  individuals_affected: number;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  measures_taken: string;
}

export interface RGPDBreach {
  id: number;
  breach_number: string;
  breach_date: string;
  description: string;
  data_affected: string[];
  individuals_affected: number;
  severity: string;
  measures_taken: string;
  notified_cnil: boolean;
  notified_cnil_at: string | null;
  notified_individuals: boolean;
  status: 'DETECTED' | 'INVESTIGATING' | 'CONTAINED' | 'RESOLVED';
  created_at: string;
}

// ============================================================================
// TYPES - Contrats France
// ============================================================================

export interface FRContractCreate {
  employee_id: number;
  contract_type: 'CDI' | 'CDD' | 'CTT' | 'APPRENTISSAGE' | 'PROFESSIONNALISATION' | 'STAGE';
  start_date: string;
  end_date?: string | null;
  trial_period_months?: number;
  job_title: string;
  classification: string;
  coefficient?: number;
  monthly_salary: number;
  working_hours_weekly: number;
  workplace: string;
}

export interface FRContract {
  id: number;
  employee_id: number;
  contract_type: string;
  start_date: string;
  end_date: string | null;
  trial_period_end: string | null;
  job_title: string;
  classification: string;
  coefficient: number | null;
  monthly_salary: number;
  working_hours_weekly: number;
  workplace: string;
  status: 'ACTIVE' | 'SUSPENDED' | 'TERMINATED';
  created_at: string;
}

// ============================================================================
// TYPES - Stats
// ============================================================================

export interface FrancePackStats {
  pcg_accounts_count: number;
  vat_declarations_pending: number;
  fec_exports_this_year: number;
  dsn_last_submitted: string | null;
  rgpd_requests_pending: number;
  rgpd_breaches_open: number;
}

// ============================================================================
// API CLIENT
// ============================================================================

const BASE_PATH = '/v1/country-packs/france';

export const francePackApi = {
  // --------------------------------------------------------------------------
  // Stats
  // --------------------------------------------------------------------------
  getStats: () =>
    api.get<FrancePackStats>(`${BASE_PATH}/stats`),

  // --------------------------------------------------------------------------
  // PCG
  // --------------------------------------------------------------------------
  initializePCG: () =>
    api.post<{ message: string; count: number }>(`${BASE_PATH}/pcg/initialize`),

  listPCGAccounts: (params?: {
    pcg_class?: string;
    active_only?: boolean;
    skip?: number;
    limit?: number;
  }) =>
    api.get<PCGAccount[]>(`${BASE_PATH}/pcg/accounts${buildQueryString(params || {})}`),

  getPCGAccount: (accountNumber: string) =>
    api.get<PCGAccount>(`${BASE_PATH}/pcg/accounts/${accountNumber}`),

  createPCGAccount: (data: PCGAccountCreate) =>
    api.post<PCGAccount>(`${BASE_PATH}/pcg/accounts`, data),

  updatePCGAccount: (accountNumber: string, data: PCGAccountUpdate) =>
    api.patch<PCGAccount>(`${BASE_PATH}/pcg/accounts/${accountNumber}`, data),

  // --------------------------------------------------------------------------
  // TVA
  // --------------------------------------------------------------------------
  initializeVATRates: () =>
    api.post<{ message: string; count: number }>(`${BASE_PATH}/tva/initialize`),

  listVATRates: (activeOnly = true) =>
    api.get<FRVATRate[]>(`${BASE_PATH}/tva/rates${buildQueryString({ active_only: activeOnly })}`),

  getVATRate: (code: string) =>
    api.get<FRVATRate>(`${BASE_PATH}/tva/rates/${code}`),

  createVATDeclaration: (data: VATDeclarationCreate) =>
    api.post<VATDeclaration>(`${BASE_PATH}/tva/declarations`, data),

  calculateVATDeclaration: (declarationId: number) =>
    api.post<VATDeclaration>(`${BASE_PATH}/tva/declarations/${declarationId}/calculate`),

  listVATDeclarations: (params?: { status?: string; year?: number }) =>
    api.get<VATDeclaration[]>(`${BASE_PATH}/tva/declarations${buildQueryString(params || {})}`),

  // --------------------------------------------------------------------------
  // FEC
  // --------------------------------------------------------------------------
  generateFEC: (data: FECGenerateRequest) =>
    api.post<FECExport>(`${BASE_PATH}/fec/generate`, data),

  validateFEC: (fecId: number) =>
    api.post<FECValidationResult>(`${BASE_PATH}/fec/${fecId}/validate`),

  exportFEC: (fecId: number) =>
    api.get<{ content: string; format: string }>(`${BASE_PATH}/fec/${fecId}/export`),

  listFECExports: (params?: { fiscal_year?: number }) =>
    api.get<FECExport[]>(`${BASE_PATH}/fec${buildQueryString(params || {})}`),

  // --------------------------------------------------------------------------
  // DSN
  // --------------------------------------------------------------------------
  createDSN: (data: DSNGenerateRequest) =>
    api.post<DSNDeclaration>(`${BASE_PATH}/dsn`, data),

  addDSNEmployee: (dsnId: number, data: DSNEmployeeData) =>
    api.post<{ message: string; employee_id: number }>(`${BASE_PATH}/dsn/${dsnId}/employees`, data),

  submitDSN: (dsnId: number) =>
    api.post<DSNDeclaration>(`${BASE_PATH}/dsn/${dsnId}/submit`),

  listDSNDeclarations: (params?: { year?: number; status?: string }) =>
    api.get<DSNDeclaration[]>(`${BASE_PATH}/dsn${buildQueryString(params || {})}`),

  // --------------------------------------------------------------------------
  // RGPD - Consentements
  // --------------------------------------------------------------------------
  createConsent: (data: RGPDConsentCreate) =>
    api.post<RGPDConsent>(`${BASE_PATH}/rgpd/consents`, data),

  listConsents: (params?: { contact_id?: number; active_only?: boolean }) =>
    api.get<RGPDConsent[]>(`${BASE_PATH}/rgpd/consents${buildQueryString(params || {})}`),

  withdrawConsent: (consentId: number) =>
    api.post<RGPDConsent>(`${BASE_PATH}/rgpd/consents/${consentId}/withdraw`),

  // --------------------------------------------------------------------------
  // RGPD - Demandes
  // --------------------------------------------------------------------------
  createRequest: (data: RGPDRequestCreate) =>
    api.post<RGPDRequest>(`${BASE_PATH}/rgpd/requests`, data),

  listRequests: (params?: { status?: string; contact_id?: number }) =>
    api.get<RGPDRequest[]>(`${BASE_PATH}/rgpd/requests${buildQueryString(params || {})}`),

  processRequest: (requestId: number, response: string) =>
    api.post<RGPDRequest>(`${BASE_PATH}/rgpd/requests/${requestId}/process`, { response }),

  // --------------------------------------------------------------------------
  // RGPD - Traitements
  // --------------------------------------------------------------------------
  createProcessing: (data: RGPDProcessingCreate) =>
    api.post<RGPDProcessing>(`${BASE_PATH}/rgpd/processings`, data),

  listProcessings: (activeOnly = true) =>
    api.get<RGPDProcessing[]>(`${BASE_PATH}/rgpd/processings${buildQueryString({ active_only: activeOnly })}`),

  // --------------------------------------------------------------------------
  // RGPD - Violations
  // --------------------------------------------------------------------------
  createBreach: (data: RGPDBreachCreate) =>
    api.post<RGPDBreach>(`${BASE_PATH}/rgpd/breaches`, data),

  listBreaches: (params?: { status?: string }) =>
    api.get<RGPDBreach[]>(`${BASE_PATH}/rgpd/breaches${buildQueryString(params || {})}`),

  notifyBreachToCNIL: (breachId: number) =>
    api.post<RGPDBreach>(`${BASE_PATH}/rgpd/breaches/${breachId}/notify-cnil`),

  // --------------------------------------------------------------------------
  // Contrats France
  // --------------------------------------------------------------------------
  createContract: (data: FRContractCreate) =>
    api.post<FRContract>(`${BASE_PATH}/contracts`, data),

  listContracts: (params?: { employee_id?: number; status?: string }) =>
    api.get<FRContract[]>(`${BASE_PATH}/contracts${buildQueryString(params || {})}`),

  getContract: (contractId: number) =>
    api.get<FRContract>(`${BASE_PATH}/contracts/${contractId}`),

  terminateContract: (contractId: number, endDate: string, reason: string) =>
    api.post<FRContract>(`${BASE_PATH}/contracts/${contractId}/terminate`, { end_date: endDate, reason }),
};

export default francePackApi;
