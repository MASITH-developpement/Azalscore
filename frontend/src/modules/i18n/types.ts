/**
 * AZALSCORE Module I18N - Types TypeScript
 * =========================================
 *
 * Definitions TypeScript pour le module d'internationalisation.
 */

// ============================================================================
// ENUMS
// ============================================================================

export type LanguageStatus = 'ACTIVE' | 'INACTIVE' | 'BETA';

export type TranslationScope = 'SYSTEM' | 'TENANT' | 'CONTENT' | 'CUSTOM';

export type TranslationStatus =
  | 'DRAFT'
  | 'VALIDATED'
  | 'NEEDS_REVIEW'
  | 'MACHINE_TRANSLATED'
  | 'DEPRECATED';

export type DateFormatType = 'DMY' | 'MDY' | 'YMD' | 'LONG';

export type NumberFormatType =
  | 'COMMA_DOT'
  | 'DOT_COMMA'
  | 'SPACE_COMMA'
  | 'QUOTE_DOT';

export type ImportExportFormat = 'JSON' | 'PO' | 'XLIFF' | 'CSV';

export type TranslationJobStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

// ============================================================================
// LANGUAGE
// ============================================================================

export interface Language {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  native_name: string;
  locale?: string;
  rtl: boolean;
  date_format: DateFormatType;
  date_separator: string;
  time_format_24h: boolean;
  number_format: NumberFormatType;
  decimal_separator: string;
  thousands_separator: string;
  currency_code: string;
  currency_symbol: string;
  currency_position: 'before' | 'after';
  first_day_of_week: number;
  flag_emoji?: string;
  flag_url?: string;
  status: LanguageStatus;
  is_default: boolean;
  is_fallback: boolean;
  sort_order: number;
  translation_coverage: number;
  total_keys: number;
  translated_keys: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  version: number;
}

export interface LanguageCreate {
  code: string;
  name: string;
  native_name: string;
  locale?: string;
  rtl?: boolean;
  date_format?: DateFormatType;
  date_separator?: string;
  time_format_24h?: boolean;
  number_format?: NumberFormatType;
  decimal_separator?: string;
  thousands_separator?: string;
  currency_code?: string;
  currency_symbol?: string;
  currency_position?: 'before' | 'after';
  first_day_of_week?: number;
  flag_emoji?: string;
  is_default?: boolean;
  is_fallback?: boolean;
  sort_order?: number;
}

export interface LanguageUpdate {
  name?: string;
  native_name?: string;
  locale?: string;
  rtl?: boolean;
  date_format?: DateFormatType;
  date_separator?: string;
  time_format_24h?: boolean;
  number_format?: NumberFormatType;
  decimal_separator?: string;
  thousands_separator?: string;
  currency_code?: string;
  currency_symbol?: string;
  currency_position?: 'before' | 'after';
  first_day_of_week?: number;
  flag_emoji?: string;
  status?: LanguageStatus;
  is_default?: boolean;
  is_fallback?: boolean;
  sort_order?: number;
}

// ============================================================================
// NAMESPACE
// ============================================================================

export interface TranslationNamespace {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description?: string;
  parent_id?: string;
  module_code?: string;
  is_system: boolean;
  is_editable: boolean;
  total_keys: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface NamespaceCreate {
  code: string;
  name: string;
  description?: string;
  parent_id?: string;
  module_code?: string;
  is_system?: boolean;
  is_editable?: boolean;
}

export interface NamespaceUpdate {
  name?: string;
  description?: string;
  parent_id?: string;
  module_code?: string;
  is_editable?: boolean;
}

// ============================================================================
// TRANSLATION KEY
// ============================================================================

export interface TranslationKey {
  id: string;
  tenant_id: string;
  namespace_id: string;
  key: string;
  scope: TranslationScope;
  description?: string;
  context?: string;
  screenshot_url?: string;
  supports_plural: boolean;
  plural_forms: string[];
  parameters: string[];
  max_length?: number;
  entity_type?: string;
  entity_id?: string;
  entity_field?: string;
  tags: string[];
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  version: number;
}

export interface TranslationKeyCreate {
  key: string;
  namespace_id: string;
  scope?: TranslationScope;
  description?: string;
  context?: string;
  screenshot_url?: string;
  supports_plural?: boolean;
  plural_forms?: string[];
  parameters?: string[];
  max_length?: number;
  entity_type?: string;
  entity_id?: string;
  entity_field?: string;
  tags?: string[];
  translations?: Record<string, string>;
}

export interface TranslationKeyUpdate {
  description?: string;
  context?: string;
  screenshot_url?: string;
  supports_plural?: boolean;
  plural_forms?: string[];
  parameters?: string[];
  max_length?: number;
  tags?: string[];
}

export interface TranslationKeyWithTranslations extends TranslationKey {
  translations: Record<string, Translation>;
}

// ============================================================================
// TRANSLATION
// ============================================================================

export interface Translation {
  id: string;
  tenant_id: string;
  translation_key_id: string;
  language_id: string;
  language_code: string;
  value: string;
  plural_values: Record<string, string>;
  status: TranslationStatus;
  is_machine_translated: boolean;
  machine_translation_provider?: string;
  machine_translation_confidence?: number;
  validated_by?: string;
  validated_at?: string;
  translator_notes?: string;
  reviewer_notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  version: number;
}

export interface TranslationUpdate {
  value?: string;
  plural_values?: Record<string, string>;
  status?: TranslationStatus;
  translator_notes?: string;
  reviewer_notes?: string;
}

export interface TranslationBulkUpdate {
  translations: Record<string, string>;
  language_code: string;
  namespace_code: string;
  status?: TranslationStatus;
}

// ============================================================================
// INLINE TRANSLATION
// ============================================================================

export interface InlineTranslationRequest {
  key: string;
  namespace: string;
  language: string;
  value: string;
  create_if_missing?: boolean;
}

export interface InlineTranslationResponse {
  key: string;
  namespace: string;
  language: string;
  value: string;
  created: boolean;
  updated: boolean;
}

// ============================================================================
// BUNDLE
// ============================================================================

export interface TranslationBundle {
  language: string;
  namespace: string;
  translations: Record<string, string | Record<string, string>>;
  generated_at: string;
  key_count: number;
}

export interface TranslationBundleRequest {
  language: string;
  namespaces: string[];
}

// ============================================================================
// AUTO-TRANSLATE
// ============================================================================

export interface AutoTranslateRequest {
  source_language_code: string;
  target_language_codes: string[];
  namespace_codes?: string[];
  scope?: TranslationScope;
  provider: 'openai' | 'google' | 'deepl' | 'azure';
  model?: string;
  overwrite_existing?: boolean;
}

export interface TranslationJob {
  id: string;
  tenant_id: string;
  source_language_id?: string;
  target_language_ids: string[];
  namespace_ids: string[];
  provider: string;
  model?: string;
  status: TranslationJobStatus;
  total_keys: number;
  processed_keys: number;
  failed_keys: number;
  progress_percent: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  created_by?: string;
  created_at: string;
}

// ============================================================================
// IMPORT/EXPORT
// ============================================================================

export interface ImportRequest {
  format: ImportExportFormat;
  language_codes?: string[];
  namespace_codes?: string[];
  overwrite_existing?: boolean;
  mark_as_validated?: boolean;
}

export interface ExportRequest {
  format: ImportExportFormat;
  language_codes: string[];
  namespace_codes?: string[];
  include_empty?: boolean;
  include_metadata?: boolean;
}

export interface ImportExportResult {
  id: string;
  tenant_id: string;
  operation: 'import' | 'export';
  format: ImportExportFormat;
  file_name?: string;
  file_url?: string;
  file_size?: number;
  language_codes: string[];
  namespace_codes: string[];
  status: string;
  total_keys: number;
  processed_keys: number;
  new_keys: number;
  updated_keys: number;
  skipped_keys: number;
  error_keys: number;
  errors: Array<{ key?: string; error: string }>;
  created_by?: string;
  created_at: string;
  completed_at?: string;
}

// ============================================================================
// GLOSSARY
// ============================================================================

export interface GlossaryTerm {
  id: string;
  tenant_id: string;
  source_term: string;
  source_language_code: string;
  translations: Record<string, string>;
  term_type?: string;
  do_not_translate: boolean;
  definition?: string;
  usage_notes?: string;
  tags: string[];
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface GlossaryCreate {
  source_term: string;
  source_language_code: string;
  translations?: Record<string, string>;
  term_type?: string;
  do_not_translate?: boolean;
  definition?: string;
  usage_notes?: string;
  tags?: string[];
}

export interface GlossaryUpdate {
  translations?: Record<string, string>;
  term_type?: string;
  do_not_translate?: boolean;
  definition?: string;
  usage_notes?: string;
  tags?: string[];
}

// ============================================================================
// DASHBOARD & STATS
// ============================================================================

export interface LanguageStats {
  language_code: string;
  language_name: string;
  total_keys: number;
  translated_keys: number;
  missing_keys: number;
  needs_review: number;
  machine_translated: number;
  coverage_percent: number;
}

export interface TranslationDashboard {
  total_languages: number;
  active_languages: number;
  total_keys: number;
  total_translations: number;
  overall_coverage: number;
  languages_stats: LanguageStats[];
  recent_activity: Array<{
    type: string;
    key: string;
    language: string;
    timestamp: string;
  }>;
  pending_reviews: number;
  machine_translated_pending: number;
}

export interface CoverageReport {
  language_code: string;
  namespaces: Array<{
    namespace: string;
    total: number;
    translated: number;
    coverage: number;
  }>;
  missing_keys: string[];
  needs_review: string[];
}

// ============================================================================
// PAGINATION & FILTERS
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface LanguageFilters {
  search?: string;
  status?: LanguageStatus[];
  is_default?: boolean;
  rtl?: boolean;
}

export interface TranslationKeyFilters {
  search?: string;
  namespace_id?: string;
  namespace_code?: string;
  scope?: TranslationScope;
  tags?: string[];
  has_translation?: boolean;
  language_code?: string;
  entity_type?: string;
}

export interface TranslationFilters {
  search?: string;
  language_code?: string;
  namespace_code?: string;
  status?: TranslationStatus[];
  is_machine_translated?: boolean;
}

// ============================================================================
// UI CONSTANTS
// ============================================================================

export const LANGUAGE_STATUS_OPTIONS = [
  { value: 'ACTIVE', label: 'Actif', color: 'green' },
  { value: 'INACTIVE', label: 'Inactif', color: 'gray' },
  { value: 'BETA', label: 'Beta', color: 'yellow' },
] as const;

export const TRANSLATION_STATUS_OPTIONS = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'VALIDATED', label: 'Valide', color: 'green' },
  { value: 'NEEDS_REVIEW', label: 'A revoir', color: 'yellow' },
  { value: 'MACHINE_TRANSLATED', label: 'Traduit auto', color: 'blue' },
  { value: 'DEPRECATED', label: 'Obsolete', color: 'red' },
] as const;

export const TRANSLATION_SCOPE_OPTIONS = [
  { value: 'SYSTEM', label: 'Systeme' },
  { value: 'TENANT', label: 'Tenant' },
  { value: 'CONTENT', label: 'Contenu' },
  { value: 'CUSTOM', label: 'Personnalise' },
] as const;

export const DATE_FORMAT_OPTIONS = [
  { value: 'DMY', label: 'JJ/MM/AAAA' },
  { value: 'MDY', label: 'MM/JJ/AAAA' },
  { value: 'YMD', label: 'AAAA-MM-JJ' },
  { value: 'LONG', label: 'Format long' },
] as const;

export const NUMBER_FORMAT_OPTIONS = [
  { value: 'COMMA_DOT', label: '1,234.56 (US/UK)' },
  { value: 'DOT_COMMA', label: '1.234,56 (DE/ES)' },
  { value: 'SPACE_COMMA', label: '1 234,56 (FR)' },
  { value: 'QUOTE_DOT', label: "1'234.56 (CH)" },
] as const;

export const IMPORT_EXPORT_FORMAT_OPTIONS = [
  { value: 'JSON', label: 'JSON' },
  { value: 'PO', label: 'PO (gettext)' },
  { value: 'XLIFF', label: 'XLIFF' },
  { value: 'CSV', label: 'CSV' },
] as const;

export const TRANSLATION_PROVIDER_OPTIONS = [
  { value: 'openai', label: 'OpenAI GPT-4' },
  { value: 'google', label: 'Google Translate' },
  { value: 'deepl', label: 'DeepL' },
  { value: 'azure', label: 'Azure Translator' },
] as const;

// ============================================================================
// COMMON LANGUAGE CODES
// ============================================================================

export const COMMON_LANGUAGES = [
  { code: 'fr', name: 'Francais', native: 'Francais', flag: 'FR' },
  { code: 'en', name: 'English', native: 'English', flag: 'GB' },
  { code: 'de', name: 'German', native: 'Deutsch', flag: 'DE' },
  { code: 'es', name: 'Spanish', native: 'Espanol', flag: 'ES' },
  { code: 'it', name: 'Italian', native: 'Italiano', flag: 'IT' },
  { code: 'pt', name: 'Portuguese', native: 'Portugues', flag: 'PT' },
  { code: 'nl', name: 'Dutch', native: 'Nederlands', flag: 'NL' },
  { code: 'pl', name: 'Polish', native: 'Polski', flag: 'PL' },
  { code: 'ru', name: 'Russian', native: 'Russkij', flag: 'RU' },
  { code: 'ar', name: 'Arabic', native: 'Al-arabiyya', flag: 'SA', rtl: true },
  { code: 'zh', name: 'Chinese', native: 'Zhongwen', flag: 'CN' },
  { code: 'ja', name: 'Japanese', native: 'Nihongo', flag: 'JP' },
] as const;

// ============================================================================
// UTILITY FUNCTIONS (from original file)
// ============================================================================

export type ItemStatus = 'draft' | 'active' | 'archived';

export const STATUS_CONFIG: Record<ItemStatus, { label: string; color: string }> = {
  draft: { label: 'Brouillon', color: 'gray' },
  active: { label: 'Actif', color: 'green' },
  archived: { label: 'Archive', color: 'gray' },
};

export function getStatusLabel(status: ItemStatus): string {
  return STATUS_CONFIG[status]?.label || status;
}

export function getStatusColor(status: ItemStatus): string {
  return STATUS_CONFIG[status]?.color || 'gray';
}
