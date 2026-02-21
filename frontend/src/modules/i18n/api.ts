/**
 * AZALSCORE Module I18N - API Client
 * ===================================
 *
 * Client API pour le module d'internationalisation.
 */

import {
  Language,
  LanguageCreate,
  LanguageUpdate,
  TranslationNamespace,
  NamespaceCreate,
  NamespaceUpdate,
  TranslationKey,
  TranslationKeyCreate,
  TranslationKeyUpdate,
  TranslationKeyWithTranslations,
  Translation,
  TranslationUpdate,
  TranslationBulkUpdate,
  TranslationBundle,
  TranslationBundleRequest,
  InlineTranslationRequest,
  InlineTranslationResponse,
  AutoTranslateRequest,
  TranslationJob,
  ImportRequest,
  ExportRequest,
  ImportExportResult,
  GlossaryTerm,
  GlossaryCreate,
  GlossaryUpdate,
  TranslationDashboard,
  CoverageReport,
  PaginatedResponse,
  LanguageFilters,
  TranslationKeyFilters,
  TranslationFilters,
} from './types';

// ============================================================================
// API BASE
// ============================================================================

const API_BASE = '/api/v1/i18n';

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// ============================================================================
// LANGUAGE API
// ============================================================================

export const languageApi = {
  /**
   * Liste les langues avec pagination et filtres.
   */
  list: async (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string[];
    is_default?: boolean;
    rtl?: boolean;
  }): Promise<PaginatedResponse<Language>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.status) params.status.forEach(s => searchParams.append('status', s));
    if (params?.is_default !== undefined) searchParams.set('is_default', String(params.is_default));
    if (params?.rtl !== undefined) searchParams.set('rtl', String(params.rtl));

    return fetchAPI(`/languages?${searchParams}`);
  },

  /**
   * Liste les langues actives.
   */
  listActive: async (): Promise<Language[]> => {
    return fetchAPI('/languages/active');
  },

  /**
   * Recupere une langue par ID.
   */
  get: async (id: string): Promise<Language> => {
    return fetchAPI(`/languages/${id}`);
  },

  /**
   * Recupere la langue par defaut.
   */
  getDefault: async (): Promise<Language> => {
    return fetchAPI('/languages/default');
  },

  /**
   * Cree une nouvelle langue.
   */
  create: async (data: LanguageCreate): Promise<Language> => {
    return fetchAPI('/languages', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Met a jour une langue.
   */
  update: async (id: string, data: LanguageUpdate): Promise<Language> => {
    return fetchAPI(`/languages/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Supprime une langue.
   */
  delete: async (id: string, hard = false): Promise<void> => {
    return fetchAPI(`/languages/${id}?hard=${hard}`, {
      method: 'DELETE',
    });
  },

  /**
   * Definit une langue comme langue par defaut.
   */
  setDefault: async (id: string): Promise<Language> => {
    return fetchAPI(`/languages/${id}/set-default`, {
      method: 'POST',
    });
  },

  /**
   * Autocomplete pour les langues.
   */
  autocomplete: async (prefix: string, limit = 10): Promise<Array<{
    id: string;
    code: string;
    name: string;
    label: string;
  }>> => {
    const response = await fetchAPI<{ items: any[] }>(
      `/languages/autocomplete?prefix=${encodeURIComponent(prefix)}&limit=${limit}`
    );
    return response.items;
  },
};

// ============================================================================
// NAMESPACE API
// ============================================================================

export const namespaceApi = {
  /**
   * Liste les namespaces.
   */
  list: async (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    module_code?: string;
  }): Promise<PaginatedResponse<TranslationNamespace>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.module_code) searchParams.set('module_code', params.module_code);

    return fetchAPI(`/namespaces?${searchParams}`);
  },

  /**
   * Recupere un namespace par ID.
   */
  get: async (id: string): Promise<TranslationNamespace> => {
    return fetchAPI(`/namespaces/${id}`);
  },

  /**
   * Cree un nouveau namespace.
   */
  create: async (data: NamespaceCreate): Promise<TranslationNamespace> => {
    return fetchAPI('/namespaces', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Met a jour un namespace.
   */
  update: async (id: string, data: NamespaceUpdate): Promise<TranslationNamespace> => {
    return fetchAPI(`/namespaces/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Supprime un namespace.
   */
  delete: async (id: string): Promise<void> => {
    return fetchAPI(`/namespaces/${id}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// TRANSLATION KEY API
// ============================================================================

export const keyApi = {
  /**
   * Liste les cles de traduction.
   */
  list: async (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    namespace_id?: string;
    namespace_code?: string;
    scope?: string;
    entity_type?: string;
  }): Promise<PaginatedResponse<TranslationKey>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.namespace_id) searchParams.set('namespace_id', params.namespace_id);
    if (params?.namespace_code) searchParams.set('namespace_code', params.namespace_code);
    if (params?.scope) searchParams.set('scope', params.scope);
    if (params?.entity_type) searchParams.set('entity_type', params.entity_type);

    return fetchAPI(`/keys?${searchParams}`);
  },

  /**
   * Recupere une cle avec ses traductions.
   */
  get: async (id: string): Promise<TranslationKeyWithTranslations> => {
    return fetchAPI(`/keys/${id}`);
  },

  /**
   * Recupere les cles manquantes pour une langue.
   */
  getMissing: async (languageCode: string, params?: {
    namespace_code?: string;
    limit?: number;
  }): Promise<{ items: TranslationKey[]; count: number }> => {
    const searchParams = new URLSearchParams();
    if (params?.namespace_code) searchParams.set('namespace_code', params.namespace_code);
    if (params?.limit) searchParams.set('limit', String(params.limit));

    return fetchAPI(`/keys/missing/${languageCode}?${searchParams}`);
  },

  /**
   * Cree une nouvelle cle.
   */
  create: async (data: TranslationKeyCreate): Promise<TranslationKey> => {
    return fetchAPI('/keys', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Met a jour une cle.
   */
  update: async (id: string, data: TranslationKeyUpdate): Promise<TranslationKey> => {
    return fetchAPI(`/keys/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Supprime une cle.
   */
  delete: async (id: string): Promise<void> => {
    return fetchAPI(`/keys/${id}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// TRANSLATION API
// ============================================================================

export const translationApi = {
  /**
   * Liste les traductions.
   */
  list: async (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    language_code?: string;
    namespace_code?: string;
    status?: string[];
    is_machine_translated?: boolean;
  }): Promise<PaginatedResponse<Translation>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.language_code) searchParams.set('language_code', params.language_code);
    if (params?.namespace_code) searchParams.set('namespace_code', params.namespace_code);
    if (params?.status) params.status.forEach(s => searchParams.append('status', s));
    if (params?.is_machine_translated !== undefined) {
      searchParams.set('is_machine_translated', String(params.is_machine_translated));
    }

    return fetchAPI(`/translations?${searchParams}`);
  },

  /**
   * Definit ou met a jour une traduction.
   */
  set: async (keyId: string, languageId: string, data: TranslationUpdate): Promise<Translation> => {
    return fetchAPI(`/translations/${keyId}/${languageId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Valide une traduction.
   */
  validate: async (id: string): Promise<Translation> => {
    return fetchAPI(`/translations/${id}/validate`, {
      method: 'POST',
    });
  },

  /**
   * Mise a jour en masse.
   */
  bulkUpdate: async (data: TranslationBulkUpdate): Promise<{ success: number; errors: any[] }> => {
    return fetchAPI('/translations/bulk', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Traduction inline.
   */
  inline: async (data: InlineTranslationRequest): Promise<InlineTranslationResponse> => {
    return fetchAPI('/translations/inline', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

// ============================================================================
// BUNDLE API
// ============================================================================

export const bundleApi = {
  /**
   * Recupere un bundle de traductions.
   */
  get: async (languageCode: string, namespaceCode: string, noCache = false): Promise<TranslationBundle> => {
    return fetchAPI(`/bundle/${languageCode}/${namespaceCode}?no_cache=${noCache}`);
  },

  /**
   * Recupere plusieurs bundles.
   */
  getMultiple: async (request: TranslationBundleRequest): Promise<Record<string, Record<string, any>>> => {
    return fetchAPI('/bundles', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Invalide le cache.
   */
  invalidateCache: async (params?: {
    namespace_code?: string;
    language_code?: string;
  }): Promise<{ invalidated: number }> => {
    const searchParams = new URLSearchParams();
    if (params?.namespace_code) searchParams.set('namespace_code', params.namespace_code);
    if (params?.language_code) searchParams.set('language_code', params.language_code);

    return fetchAPI(`/cache/invalidate?${searchParams}`, {
      method: 'POST',
    });
  },
};

// ============================================================================
// TRANSLATE API (simple)
// ============================================================================

export const translateApi = {
  /**
   * Traduit une cle (API simple).
   */
  t: async (namespace: string, key: string, lang = 'fr'): Promise<string> => {
    const response = await fetchAPI<{ value: string }>(
      `/t/${namespace}/${key}?lang=${lang}`
    );
    return response.value;
  },
};

// ============================================================================
// AUTO-TRANSLATE API
// ============================================================================

export const autoTranslateApi = {
  /**
   * Lance un job de traduction automatique.
   */
  start: async (data: AutoTranslateRequest): Promise<TranslationJob> => {
    return fetchAPI('/auto-translate', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Liste les jobs de traduction.
   */
  listJobs: async (params?: {
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<TranslationJob>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));

    return fetchAPI(`/jobs?${searchParams}`);
  },

  /**
   * Recupere un job de traduction.
   */
  getJob: async (id: string): Promise<TranslationJob> => {
    return fetchAPI(`/jobs/${id}`);
  },
};

// ============================================================================
// IMPORT/EXPORT API
// ============================================================================

export const importExportApi = {
  /**
   * Exporte les traductions.
   */
  export: async (request: ExportRequest): Promise<Record<string, any>> => {
    return fetchAPI('/export', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Importe des traductions depuis un fichier.
   */
  import: async (file: File, request: ImportRequest): Promise<ImportExportResult> => {
    const formData = new FormData();
    formData.append('file', file);

    // Add request params as query string
    const searchParams = new URLSearchParams();
    searchParams.set('format', request.format);
    if (request.language_codes) {
      request.language_codes.forEach(lc => searchParams.append('language_codes', lc));
    }
    if (request.namespace_codes) {
      request.namespace_codes.forEach(nc => searchParams.append('namespace_codes', nc));
    }
    if (request.overwrite_existing !== undefined) {
      searchParams.set('overwrite_existing', String(request.overwrite_existing));
    }
    if (request.mark_as_validated !== undefined) {
      searchParams.set('mark_as_validated', String(request.mark_as_validated));
    }

    const response = await fetch(`${API_BASE}/import?${searchParams}`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  },
};

// ============================================================================
// FORMAT API
// ============================================================================

export const formatApi = {
  /**
   * Formate une date.
   */
  formatDate: async (dateStr: string, languageCode = 'fr', formatType?: string): Promise<string> => {
    const searchParams = new URLSearchParams();
    searchParams.set('date_str', dateStr);
    searchParams.set('language_code', languageCode);
    if (formatType) searchParams.set('format_type', formatType);

    const response = await fetchAPI<{ formatted: string }>(`/format/date?${searchParams}`, {
      method: 'POST',
    });
    return response.formatted;
  },

  /**
   * Formate un nombre.
   */
  formatNumber: async (value: number, languageCode = 'fr', decimals = 2): Promise<string> => {
    const searchParams = new URLSearchParams();
    searchParams.set('value', String(value));
    searchParams.set('language_code', languageCode);
    searchParams.set('decimals', String(decimals));

    const response = await fetchAPI<{ formatted: string }>(`/format/number?${searchParams}`, {
      method: 'POST',
    });
    return response.formatted;
  },

  /**
   * Formate un montant.
   */
  formatCurrency: async (
    amount: number,
    currency = 'EUR',
    languageCode = 'fr',
    decimals = 2
  ): Promise<string> => {
    const searchParams = new URLSearchParams();
    searchParams.set('amount', String(amount));
    searchParams.set('currency', currency);
    searchParams.set('language_code', languageCode);
    searchParams.set('decimals', String(decimals));

    const response = await fetchAPI<{ formatted: string }>(`/format/currency?${searchParams}`, {
      method: 'POST',
    });
    return response.formatted;
  },
};

// ============================================================================
// GLOSSARY API
// ============================================================================

export const glossaryApi = {
  /**
   * Liste les termes du glossaire.
   */
  list: async (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    term_type?: string;
  }): Promise<PaginatedResponse<GlossaryTerm>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', String(params.page));
    if (params?.page_size) searchParams.set('page_size', String(params.page_size));
    if (params?.search) searchParams.set('search', params.search);
    if (params?.term_type) searchParams.set('term_type', params.term_type);

    return fetchAPI(`/glossary?${searchParams}`);
  },

  /**
   * Cree un terme de glossaire.
   */
  create: async (data: GlossaryCreate): Promise<GlossaryTerm> => {
    return fetchAPI('/glossary', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /**
   * Met a jour un terme de glossaire.
   */
  update: async (id: string, data: GlossaryUpdate): Promise<GlossaryTerm> => {
    return fetchAPI(`/glossary/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Supprime un terme de glossaire.
   */
  delete: async (id: string): Promise<void> => {
    return fetchAPI(`/glossary/${id}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// DASHBOARD API
// ============================================================================

export const dashboardApi = {
  /**
   * Recupere le dashboard de couverture.
   */
  get: async (): Promise<TranslationDashboard> => {
    return fetchAPI('/dashboard');
  },

  /**
   * Rapport de couverture pour une langue.
   */
  getCoverage: async (languageCode: string): Promise<CoverageReport> => {
    return fetchAPI(`/coverage/${languageCode}`);
  },
};

// ============================================================================
// COMBINED API EXPORT
// ============================================================================

export const i18nApi = {
  language: languageApi,
  namespace: namespaceApi,
  key: keyApi,
  translation: translationApi,
  bundle: bundleApi,
  translate: translateApi,
  autoTranslate: autoTranslateApi,
  importExport: importExportApi,
  format: formatApi,
  glossary: glossaryApi,
  dashboard: dashboardApi,
};

export default i18nApi;
