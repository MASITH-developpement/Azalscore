/**
 * AZALSCORE - Country Packs API
 * ==============================
 * Complete typed API client for Country Packs / Localization module.
 * Covers: Country Packs, Tax Rates, Document Templates, Bank Configs, Public Holidays, Legal Requirements
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const countryPacksKeys = {
  all: ['country-packs'] as const,
  packs: () => [...countryPacksKeys.all, 'packs'] as const,
  pack: (id: number) => [...countryPacksKeys.packs(), id] as const,
  packSummary: (code: string) => [...countryPacksKeys.all, 'summary', code] as const,
  taxRates: (packId: number) => [...countryPacksKeys.all, 'tax-rates', packId] as const,
  taxRate: (id: number) => [...countryPacksKeys.all, 'tax-rate', id] as const,
  templates: (packId: number) => [...countryPacksKeys.all, 'templates', packId] as const,
  template: (id: number) => [...countryPacksKeys.all, 'template', id] as const,
  bankConfigs: (packId: number) => [...countryPacksKeys.all, 'bank-configs', packId] as const,
  bankConfig: (id: number) => [...countryPacksKeys.all, 'bank-config', id] as const,
  holidays: (packId: number) => [...countryPacksKeys.all, 'holidays', packId] as const,
  holiday: (id: number) => [...countryPacksKeys.all, 'holiday', id] as const,
  holidaysForYear: (packId: number, year: number) => [...countryPacksKeys.holidays(packId), 'year', year] as const,
  legalRequirements: (packId: number) => [...countryPacksKeys.all, 'requirements', packId] as const,
  legalRequirement: (id: number) => [...countryPacksKeys.all, 'requirement', id] as const,
  tenantSettings: () => [...countryPacksKeys.all, 'tenant-settings'] as const,
};

// ============================================================================
// TYPES - ENUMS
// ============================================================================

export type TaxType = 'VAT' | 'SALES_TAX' | 'CORPORATE_TAX' | 'PAYROLL_TAX' | 'WITHHOLDING' | 'CUSTOMS' | 'EXCISE' | 'OTHER';

export type DocumentType = 'INVOICE' | 'CREDIT_NOTE' | 'PURCHASE_ORDER' | 'DELIVERY_NOTE' | 'PAYSLIP' | 'TAX_RETURN' | 'BALANCE_SHEET' | 'INCOME_STATEMENT' | 'CONTRACT' | 'OTHER';

export type BankFormat = 'SEPA' | 'SWIFT' | 'ACH' | 'BACS' | 'CMI' | 'RTGS' | 'OTHER';

export type DateFormatStyle = 'DMY' | 'MDY' | 'YMD' | 'DDMMYYYY' | 'MMDDYYYY' | 'YYYYMMDD';

export type NumberFormatStyle = 'EU' | 'US' | 'CH';

export type PackStatus = 'DRAFT' | 'ACTIVE' | 'DEPRECATED';

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface CountryPack {
  id: number;
  country_code: string;
  country_name: string;
  default_currency: string;
  country_name_local?: string | null;
  default_language: string;
  currency_symbol?: string | null;
  currency_position: string;
  date_format: DateFormatStyle;
  number_format: NumberFormatStyle;
  decimal_separator: string;
  thousands_separator: string;
  timezone: string;
  week_start: number;
  fiscal_year_start_month: number;
  fiscal_year_start_day: number;
  default_vat_rate: number;
  has_regional_taxes: boolean;
  company_id_label: string;
  company_id_format?: string | null;
  vat_id_label: string;
  vat_id_format?: string | null;
  config?: Record<string, unknown> | null;
  is_default: boolean;
  status: PackStatus;
  created_at: string;
  updated_at?: string | null;
  created_by?: number | null;
}

export interface TaxRate {
  id: number;
  country_pack_id: number;
  tax_type: TaxType;
  code: string;
  name: string;
  description?: string | null;
  rate: number;
  is_percentage: boolean;
  applies_to?: string | null;
  region?: string | null;
  account_collected?: string | null;
  account_deductible?: string | null;
  account_payable?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface DocumentTemplate {
  id: number;
  country_pack_id: number;
  document_type: DocumentType;
  code: string;
  name: string;
  description?: string | null;
  template_format: string;
  template_content?: string | null;
  template_path?: string | null;
  mandatory_fields?: string[] | null;
  legal_mentions?: string | null;
  numbering_prefix?: string | null;
  numbering_pattern?: string | null;
  numbering_reset: string;
  language: string;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
  created_by?: number | null;
}

export interface BankConfig {
  id: number;
  country_pack_id: number;
  bank_format: BankFormat;
  code: string;
  name: string;
  description?: string | null;
  iban_prefix?: string | null;
  iban_length?: number | null;
  bic_required: boolean;
  export_format: string;
  export_encoding: string;
  export_template?: string | null;
  config?: Record<string, unknown> | null;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface PublicHoliday {
  id: number;
  country_pack_id: number;
  name: string;
  name_local?: string | null;
  holiday_date?: string | null;
  month?: number | null;
  day?: number | null;
  is_fixed: boolean;
  calculation_rule?: string | null;
  year?: number | null;
  region?: string | null;
  is_national: boolean;
  is_work_day: boolean;
  affects_banks: boolean;
  affects_business: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface HolidayWithDate {
  id: number;
  name: string;
  name_local?: string | null;
  date: string;
  is_work_day: boolean;
  affects_banks: boolean;
  region?: string | null;
}

export interface LegalRequirement {
  id: number;
  country_pack_id: number;
  category: string;
  code: string;
  name: string;
  description?: string | null;
  requirement_type?: string | null;
  frequency?: string | null;
  deadline_rule?: string | null;
  config?: Record<string, unknown> | null;
  legal_reference?: string | null;
  effective_date?: string | null;
  end_date?: string | null;
  is_mandatory: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface TenantCountrySettings {
  id: number;
  country_pack_id: number;
  is_primary: boolean;
  is_active: boolean;
  custom_currency?: string | null;
  custom_language?: string | null;
  custom_timezone?: string | null;
  custom_config?: Record<string, unknown> | null;
  activated_at: string;
  activated_by?: number | null;
}

export interface CountrySummary {
  country_code: string;
  country_name: string;
  currency: string;
  language: string;
  timezone: string;
  vat_rates_count: number;
  templates_count: number;
  bank_configs_count: number;
  holidays_count: number;
  requirements_count: number;
  default_vat_rate: number;
  fiscal_year_start: string;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface CountryPackCreate {
  country_code: string;
  country_name: string;
  default_currency: string;
  country_name_local?: string;
  default_language?: string;
  currency_symbol?: string;
  currency_position?: string;
  date_format?: DateFormatStyle;
  number_format?: NumberFormatStyle;
  decimal_separator?: string;
  thousands_separator?: string;
  timezone?: string;
  week_start?: number;
  fiscal_year_start_month?: number;
  fiscal_year_start_day?: number;
  default_vat_rate?: number;
  has_regional_taxes?: boolean;
  company_id_label?: string;
  company_id_format?: string;
  vat_id_label?: string;
  vat_id_format?: string;
  config?: Record<string, unknown>;
  is_default?: boolean;
}

export interface CountryPackUpdate {
  country_name?: string;
  country_name_local?: string;
  default_language?: string;
  currency_symbol?: string;
  currency_position?: string;
  date_format?: DateFormatStyle;
  number_format?: NumberFormatStyle;
  timezone?: string;
  default_vat_rate?: number;
  company_id_label?: string;
  vat_id_label?: string;
  config?: Record<string, unknown>;
  is_default?: boolean;
  status?: PackStatus;
}

export interface TaxRateCreate {
  country_pack_id: number;
  tax_type: TaxType;
  code: string;
  name: string;
  description?: string;
  rate: number;
  is_percentage?: boolean;
  applies_to?: string;
  region?: string;
  account_collected?: string;
  account_deductible?: string;
  account_payable?: string;
  valid_from?: string;
  valid_to?: string;
  is_default?: boolean;
}

export interface TaxRateUpdate {
  name?: string;
  description?: string;
  rate?: number;
  applies_to?: string;
  region?: string;
  account_collected?: string;
  account_deductible?: string;
  account_payable?: string;
  valid_from?: string;
  valid_to?: string;
  is_active?: boolean;
  is_default?: boolean;
}

export interface DocumentTemplateCreate {
  country_pack_id: number;
  document_type: DocumentType;
  code: string;
  name: string;
  description?: string;
  template_format?: string;
  template_content?: string;
  template_path?: string;
  mandatory_fields?: string[];
  legal_mentions?: string;
  numbering_prefix?: string;
  numbering_pattern?: string;
  numbering_reset?: string;
  language?: string;
  is_default?: boolean;
}

export interface DocumentTemplateUpdate {
  name?: string;
  description?: string;
  template_content?: string;
  template_path?: string;
  mandatory_fields?: string[];
  legal_mentions?: string;
  numbering_prefix?: string;
  numbering_pattern?: string;
  is_active?: boolean;
  is_default?: boolean;
}

export interface BankConfigCreate {
  country_pack_id: number;
  bank_format: BankFormat;
  code: string;
  name: string;
  description?: string;
  iban_prefix?: string;
  iban_length?: number;
  bic_required?: boolean;
  export_format?: string;
  export_encoding?: string;
  export_template?: string;
  config?: Record<string, unknown>;
  is_default?: boolean;
}

export interface BankConfigUpdate {
  name?: string;
  description?: string;
  iban_prefix?: string;
  iban_length?: number;
  bic_required?: boolean;
  export_format?: string;
  export_template?: string;
  config?: Record<string, unknown>;
  is_active?: boolean;
  is_default?: boolean;
}

export interface PublicHolidayCreate {
  country_pack_id: number;
  name: string;
  name_local?: string;
  holiday_date?: string;
  month?: number;
  day?: number;
  is_fixed?: boolean;
  calculation_rule?: string;
  year?: number;
  region?: string;
  is_national?: boolean;
  is_work_day?: boolean;
  affects_banks?: boolean;
  affects_business?: boolean;
}

export interface PublicHolidayUpdate {
  name?: string;
  name_local?: string;
  holiday_date?: string;
  month?: number;
  day?: number;
  is_work_day?: boolean;
  is_active?: boolean;
}

export interface LegalRequirementCreate {
  country_pack_id: number;
  category: string;
  code: string;
  name: string;
  description?: string;
  requirement_type?: string;
  frequency?: string;
  deadline_rule?: string;
  config?: Record<string, unknown>;
  legal_reference?: string;
  effective_date?: string;
  end_date?: string;
  is_mandatory?: boolean;
}

export interface LegalRequirementUpdate {
  name?: string;
  description?: string;
  requirement_type?: string;
  frequency?: string;
  deadline_rule?: string;
  config?: Record<string, unknown>;
  is_mandatory?: boolean;
  is_active?: boolean;
}

export interface TenantCountryActivate {
  country_pack_id: number;
  is_primary?: boolean;
  custom_currency?: string;
  custom_language?: string;
  custom_timezone?: string;
  custom_config?: Record<string, unknown>;
}

export interface IBANValidationRequest {
  iban: string;
  country_code: string;
}

export interface IBANValidationResponse {
  valid: boolean;
  formatted_iban?: string | null;
  error?: string | null;
}

export interface CurrencyFormatRequest {
  amount: number;
  country_code: string;
}

export interface CurrencyFormatResponse {
  formatted: string;
  currency: string;
  symbol?: string | null;
}

export interface DateFormatRequest {
  date: string;
  country_code: string;
}

export interface DateFormatResponse {
  formatted: string;
  format_style: string;
}

// ============================================================================
// HOOKS - COUNTRY PACKS
// ============================================================================

export function useCountryPacks(filters?: {
  status?: PackStatus;
  skip?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: [...countryPacksKeys.packs(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.skip) params.append('skip', String(filters.skip));
      if (filters?.limit) params.append('limit', String(filters.limit));
      const queryString = params.toString();
      const response = await api.get<{ items: CountryPack[]; total: number; skip: number; limit: number }>(
        `/country-packs${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useCountryPack(id: number) {
  return useQuery({
    queryKey: countryPacksKeys.pack(id),
    queryFn: async () => {
      const response = await api.get<CountryPack>(`/country-packs/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCountrySummary(countryCode: string) {
  return useQuery({
    queryKey: countryPacksKeys.packSummary(countryCode),
    queryFn: async () => {
      const response = await api.get<CountrySummary>(`/country-packs/summary/${countryCode}`);
      return response;
    },
    enabled: !!countryCode,
  });
}

export function useCreateCountryPack() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CountryPackCreate) => {
      return api.post<CountryPack>('/country-packs', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.packs() });
    },
  });
}

export function useUpdateCountryPack() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: CountryPackUpdate }) => {
      return api.put<CountryPack>(`/country-packs/${id}`, data);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.pack(id) });
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.packs() });
    },
  });
}

export function useDeleteCountryPack() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      return api.delete(`/country-packs/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.packs() });
    },
  });
}

// ============================================================================
// HOOKS - TAX RATES
// ============================================================================

export function useTaxRates(packId: number, filters?: {
  tax_type?: TaxType;
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: [...countryPacksKeys.taxRates(packId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.tax_type) params.append('tax_type', filters.tax_type);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: TaxRate[]; total: number }>(
        `/country-packs/${packId}/tax-rates${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!packId,
  });
}

export function useTaxRate(id: number) {
  return useQuery({
    queryKey: countryPacksKeys.taxRate(id),
    queryFn: async () => {
      const response = await api.get<TaxRate>(`/country-packs/tax-rates/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateTaxRate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TaxRateCreate) => {
      return api.post<TaxRate>('/country-packs/tax-rates', data);
    },
    onSuccess: (_, { country_pack_id }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.taxRates(country_pack_id) });
    },
  });
}

export function useUpdateTaxRate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; packId: number; data: TaxRateUpdate }) => {
      return api.put<TaxRate>(`/country-packs/tax-rates/${id}`, data);
    },
    onSuccess: (_, { id, packId }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.taxRate(id) });
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.taxRates(packId) });
    },
  });
}

export function useDeleteTaxRate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id }: { id: number; packId: number }) => {
      return api.delete(`/country-packs/tax-rates/${id}`);
    },
    onSuccess: (_, { packId }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.taxRates(packId) });
    },
  });
}

// ============================================================================
// HOOKS - DOCUMENT TEMPLATES
// ============================================================================

export function useDocumentTemplates(packId: number, filters?: {
  document_type?: DocumentType;
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: [...countryPacksKeys.templates(packId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.document_type) params.append('document_type', filters.document_type);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: DocumentTemplate[]; total: number }>(
        `/country-packs/${packId}/templates${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!packId,
  });
}

export function useDocumentTemplate(id: number) {
  return useQuery({
    queryKey: countryPacksKeys.template(id),
    queryFn: async () => {
      const response = await api.get<DocumentTemplate>(`/country-packs/templates/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateDocumentTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: DocumentTemplateCreate) => {
      return api.post<DocumentTemplate>('/country-packs/templates', data);
    },
    onSuccess: (_, { country_pack_id }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.templates(country_pack_id) });
    },
  });
}

export function useUpdateDocumentTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; packId: number; data: DocumentTemplateUpdate }) => {
      return api.put<DocumentTemplate>(`/country-packs/templates/${id}`, data);
    },
    onSuccess: (_, { id, packId }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.template(id) });
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.templates(packId) });
    },
  });
}

export function useDeleteDocumentTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id }: { id: number; packId: number }) => {
      return api.delete(`/country-packs/templates/${id}`);
    },
    onSuccess: (_, { packId }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.templates(packId) });
    },
  });
}

// ============================================================================
// HOOKS - BANK CONFIGS
// ============================================================================

export function useBankConfigs(packId: number, filters?: {
  bank_format?: BankFormat;
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: [...countryPacksKeys.bankConfigs(packId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.bank_format) params.append('bank_format', filters.bank_format);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: BankConfig[]; total: number }>(
        `/country-packs/${packId}/bank-configs${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!packId,
  });
}

export function useBankConfig(id: number) {
  return useQuery({
    queryKey: countryPacksKeys.bankConfig(id),
    queryFn: async () => {
      const response = await api.get<BankConfig>(`/country-packs/bank-configs/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateBankConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: BankConfigCreate) => {
      return api.post<BankConfig>('/country-packs/bank-configs', data);
    },
    onSuccess: (_, { country_pack_id }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.bankConfigs(country_pack_id) });
    },
  });
}

export function useUpdateBankConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; packId: number; data: BankConfigUpdate }) => {
      return api.put<BankConfig>(`/country-packs/bank-configs/${id}`, data);
    },
    onSuccess: (_, { id, packId }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.bankConfig(id) });
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.bankConfigs(packId) });
    },
  });
}

export function useDeleteBankConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id }: { id: number; packId: number }) => {
      return api.delete(`/country-packs/bank-configs/${id}`);
    },
    onSuccess: (_, { packId }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.bankConfigs(packId) });
    },
  });
}

// ============================================================================
// HOOKS - PUBLIC HOLIDAYS
// ============================================================================

export function usePublicHolidays(packId: number, filters?: {
  region?: string;
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: [...countryPacksKeys.holidays(packId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.region) params.append('region', filters.region);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: PublicHoliday[]; total: number }>(
        `/country-packs/${packId}/holidays${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!packId,
  });
}

export function usePublicHolidaysForYear(packId: number, year: number, region?: string) {
  return useQuery({
    queryKey: [...countryPacksKeys.holidaysForYear(packId, year), region],
    queryFn: async () => {
      const params = new URLSearchParams();
      params.append('year', String(year));
      if (region) params.append('region', region);
      const response = await api.get<{ items: HolidayWithDate[] }>(
        `/country-packs/${packId}/holidays/calendar?${params.toString()}`
      );
      return response;
    },
    enabled: !!packId && !!year,
  });
}

export function usePublicHoliday(id: number) {
  return useQuery({
    queryKey: countryPacksKeys.holiday(id),
    queryFn: async () => {
      const response = await api.get<PublicHoliday>(`/country-packs/holidays/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreatePublicHoliday() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: PublicHolidayCreate) => {
      return api.post<PublicHoliday>('/country-packs/holidays', data);
    },
    onSuccess: (_, { country_pack_id }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.holidays(country_pack_id) });
    },
  });
}

export function useUpdatePublicHoliday() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; packId: number; data: PublicHolidayUpdate }) => {
      return api.put<PublicHoliday>(`/country-packs/holidays/${id}`, data);
    },
    onSuccess: (_, { id, packId }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.holiday(id) });
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.holidays(packId) });
    },
  });
}

export function useDeletePublicHoliday() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id }: { id: number; packId: number }) => {
      return api.delete(`/country-packs/holidays/${id}`);
    },
    onSuccess: (_, { packId }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.holidays(packId) });
    },
  });
}

// ============================================================================
// HOOKS - LEGAL REQUIREMENTS
// ============================================================================

export function useLegalRequirements(packId: number, filters?: {
  category?: string;
  is_mandatory?: boolean;
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: [...countryPacksKeys.legalRequirements(packId), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.category) params.append('category', filters.category);
      if (filters?.is_mandatory !== undefined) params.append('is_mandatory', String(filters.is_mandatory));
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const response = await api.get<{ items: LegalRequirement[]; total: number }>(
        `/country-packs/${packId}/requirements${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    enabled: !!packId,
  });
}

export function useLegalRequirement(id: number) {
  return useQuery({
    queryKey: countryPacksKeys.legalRequirement(id),
    queryFn: async () => {
      const response = await api.get<LegalRequirement>(`/country-packs/requirements/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useCreateLegalRequirement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: LegalRequirementCreate) => {
      return api.post<LegalRequirement>('/country-packs/requirements', data);
    },
    onSuccess: (_, { country_pack_id }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.legalRequirements(country_pack_id) });
    },
  });
}

export function useUpdateLegalRequirement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; packId: number; data: LegalRequirementUpdate }) => {
      return api.put<LegalRequirement>(`/country-packs/requirements/${id}`, data);
    },
    onSuccess: (_, { id, packId }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.legalRequirement(id) });
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.legalRequirements(packId) });
    },
  });
}

export function useDeleteLegalRequirement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id }: { id: number; packId: number }) => {
      return api.delete(`/country-packs/requirements/${id}`);
    },
    onSuccess: (_, { packId }) => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.legalRequirements(packId) });
    },
  });
}

// ============================================================================
// HOOKS - TENANT SETTINGS
// ============================================================================

export function useTenantCountrySettings() {
  return useQuery({
    queryKey: countryPacksKeys.tenantSettings(),
    queryFn: async () => {
      const response = await api.get<{ items: TenantCountrySettings[] }>('/country-packs/tenant/settings');
      return response;
    },
  });
}

export function useActivateCountryPack() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TenantCountryActivate) => {
      return api.post<TenantCountrySettings>('/country-packs/tenant/activate', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.tenantSettings() });
    },
  });
}

export function useDeactivateCountryPack() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (packId: number) => {
      return api.post(`/country-packs/tenant/deactivate/${packId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.tenantSettings() });
    },
  });
}

export function useSetPrimaryCountry() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (packId: number) => {
      return api.post(`/country-packs/tenant/set-primary/${packId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: countryPacksKeys.tenantSettings() });
    },
  });
}

// ============================================================================
// HOOKS - UTILITIES
// ============================================================================

export function useValidateIBAN() {
  return useMutation({
    mutationFn: async (data: IBANValidationRequest) => {
      return api.post<IBANValidationResponse>('/country-packs/validate/iban', data);
    },
  });
}

export function useFormatCurrency() {
  return useMutation({
    mutationFn: async (data: CurrencyFormatRequest) => {
      return api.post<CurrencyFormatResponse>('/country-packs/format/currency', data);
    },
  });
}

export function useFormatDate() {
  return useMutation({
    mutationFn: async (data: DateFormatRequest) => {
      return api.post<DateFormatResponse>('/country-packs/format/date', data);
    },
  });
}
