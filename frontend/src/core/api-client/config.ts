/**
 * AZALSCORE - Configuration API Versionnée
 * =========================================
 * Gestion centralisée des versions d'API (v1/v2) avec fallback automatique.
 *
 * Stratégie de migration:
 * - Par défaut, utiliser v2 pour les nouveaux modules
 * - Fallback sur v1 si v2 non disponible (404)
 * - Modules legacy forcés en v1 via moduleOverrides
 */

import { api } from './index';

// =============================================================================
// Types
// =============================================================================

export type ApiVersion = 'v1' | 'v2';

export interface ApiModuleConfig {
  version: ApiVersion;
  deprecated?: boolean;
  migratedAt?: string;
}

export interface ApiConfigOptions {
  /** Version par défaut pour tous les modules */
  defaultVersion: ApiVersion;
  /** Activer le fallback automatique v2 → v1 */
  enableFallback: boolean;
  /** Logger les appels v1 dépréciés */
  logDeprecation: boolean;
  /** Modules avec version forcée */
  moduleOverrides: Record<string, ApiModuleConfig>;
}

// =============================================================================
// Configuration
// =============================================================================

const DEFAULT_CONFIG: ApiConfigOptions = {
  defaultVersion: 'v2',
  enableFallback: true,
  logDeprecation: true,
  moduleOverrides: {
    // Modules legacy qui restent en v1 (pas encore migrés)
    'odoo-import': { version: 'v1', deprecated: false },
    'enrichment': { version: 'v1', deprecated: false },

    // Modules migrés (forcer v2)
    // Wave 1
    'accounting': { version: 'v2', migratedAt: '2026-02-15' },
    'contacts': { version: 'v2', migratedAt: '2026-02-15' },
    'interventions': { version: 'v2', migratedAt: '2026-02-15' },
    'iam': { version: 'v2', migratedAt: '2026-02-15' },
    'commercial': { version: 'v2', migratedAt: '2026-02-15' },
    'treasury': { version: 'v2', migratedAt: '2026-02-15' },
    'tenants': { version: 'v2', migratedAt: '2026-02-15' },
    // Wave 2
    'finance': { version: 'v2', migratedAt: '2026-02-15' },
    'purchases': { version: 'v2', migratedAt: '2026-02-15' },
    'stripe': { version: 'v2', migratedAt: '2026-02-15' },
    'subscriptions': { version: 'v2', migratedAt: '2026-02-15' },
    // Wave 3
    'inventory': { version: 'v2', migratedAt: '2026-02-15' },
    'production': { version: 'v2', migratedAt: '2026-02-15' },
    'procurement': { version: 'v2', migratedAt: '2026-02-15' },
    'quality': { version: 'v2', migratedAt: '2026-02-15' },
    'qc': { version: 'v2', migratedAt: '2026-02-15' },
    'maintenance': { version: 'v2', migratedAt: '2026-02-15' },
    // Wave 4
    'helpdesk': { version: 'v2', migratedAt: '2026-02-15' },
    'field-service': { version: 'v2', migratedAt: '2026-02-15' },
    'interventions': { version: 'v2', migratedAt: '2026-02-15' },
    'projects': { version: 'v2', migratedAt: '2026-02-15' },
    'hr': { version: 'v2', migratedAt: '2026-02-15' },
    // Wave 5
    'audit': { version: 'v2', migratedAt: '2026-02-15' },
    'compliance': { version: 'v2', migratedAt: '2026-02-15' },
    'backup': { version: 'v2', migratedAt: '2026-02-15' },
    'bi': { version: 'v2', migratedAt: '2026-02-15' },
    'triggers': { version: 'v2', migratedAt: '2026-02-15' },
    'autoconfig': { version: 'v2', migratedAt: '2026-02-15' },
    // Wave 6
    'ai': { version: 'v2', migratedAt: '2026-02-15' },
    'guardian': { version: 'v2', migratedAt: '2026-02-15' },
    'website': { version: 'v2', migratedAt: '2026-02-15' },
    'web': { version: 'v2', migratedAt: '2026-02-15' },
    'ecommerce': { version: 'v2', migratedAt: '2026-02-15' },
    'pos': { version: 'v2', migratedAt: '2026-02-15' },
    // Wave 7
    'contacts': { version: 'v2', migratedAt: '2026-02-15' },
    'email': { version: 'v2', migratedAt: '2026-02-15' },
    'mobile': { version: 'v2', migratedAt: '2026-02-15' },
    'marketplace': { version: 'v2', migratedAt: '2026-02-15' },
    'broadcast': { version: 'v2', migratedAt: '2026-02-15' },
    'country-packs': { version: 'v2', migratedAt: '2026-02-15' },
    'automated-accounting': { version: 'v2', migratedAt: '2026-02-15' },
  },
};

// État global de la config (peut être modifié au runtime)
let currentConfig: ApiConfigOptions = { ...DEFAULT_CONFIG };

// =============================================================================
// API Config Object
// =============================================================================

export const API_CONFIG = {
  /**
   * Obtient la version d'API pour un module donné.
   */
  getVersion(module: string): ApiVersion {
    const override = currentConfig.moduleOverrides[module];
    if (override) {
      return override.version;
    }
    return currentConfig.defaultVersion;
  },

  /**
   * Construit l'URL complète pour un endpoint.
   *
   * @param module - Nom du module (ex: 'accounting', 'commercial')
   * @param path - Chemin de l'endpoint (ex: '/summary', '/customers/123')
   * @returns URL complète (ex: '/v3/accounting/summary')
   */
  getUrl(module: string, path: string): string {
    const version = this.getVersion(module);
    // Normaliser le path (enlever le / initial si présent)
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `/${version}/${module}${normalizedPath}`;
  },

  /**
   * Vérifie si un module est en version dépréciée (v1).
   */
  isDeprecated(module: string): boolean {
    const version = this.getVersion(module);
    if (version === 'v1') {
      // v1 est considéré déprécié sauf exception explicite
      const override = currentConfig.moduleOverrides[module];
      return override?.deprecated !== false;
    }
    return false;
  },

  /**
   * Log un avertissement de dépréciation si nécessaire.
   */
  logIfDeprecated(module: string, path: string): void {
    if (currentConfig.logDeprecation && this.isDeprecated(module)) {
      console.warn(
        `[DEPRECATION] API v1 call: ${module}${path}. ` +
        `Please migrate to v2. See /docs/migration`
      );
    }
  },

  /**
   * Fetch avec fallback automatique v2 → v1.
   *
   * @example
   * const data = await API_CONFIG.fetchWithFallback<Customer[]>(
   *   'commercial',
   *   '/customers'
   * );
   */
  async fetchWithFallback<T>(
    module: string,
    path: string,
    options?: RequestInit
  ): Promise<T> {
    const version = this.getVersion(module);

    // Log si v1
    this.logIfDeprecated(module, path);

    // Construire l'URL
    const url = this.getUrl(module, path);

    try {
      const response = await api.get<T>(url);
      return response as T;
    } catch (error: any) {
      // Fallback v2 → v1 si 404 et fallback activé
      if (
        currentConfig.enableFallback &&
        version === 'v2' &&
        error?.status === 404
      ) {
        console.warn(
          `[API] v2 endpoint not found, falling back to v1: ${module}${path}`
        );

        const v1Url = `/v3/${module}${path}`;
        return await api.get<T>(v1Url) as T;
      }

      throw error;
    }
  },

  /**
   * POST avec fallback automatique.
   */
  async postWithFallback<T>(
    module: string,
    path: string,
    data: unknown,
    options?: RequestInit
  ): Promise<T> {
    const version = this.getVersion(module);
    this.logIfDeprecated(module, path);
    const url = this.getUrl(module, path);

    try {
      const response = await api.post<T>(url, data);
      return response as T;
    } catch (error: any) {
      if (
        currentConfig.enableFallback &&
        version === 'v2' &&
        error?.status === 404
      ) {
        console.warn(
          `[API] v2 endpoint not found, falling back to v1: ${module}${path}`
        );
        const v1Url = `/v3/${module}${path}`;
        return await api.post<T>(v1Url, data) as T;
      }
      throw error;
    }
  },

  /**
   * Met à jour la configuration au runtime.
   */
  configure(options: Partial<ApiConfigOptions>): void {
    currentConfig = {
      ...currentConfig,
      ...options,
      moduleOverrides: {
        ...currentConfig.moduleOverrides,
        ...options.moduleOverrides,
      },
    };
  },

  /**
   * Réinitialise la configuration par défaut.
   */
  reset(): void {
    currentConfig = { ...DEFAULT_CONFIG };
  },

  /**
   * Obtient la configuration actuelle (pour debug).
   */
  getConfig(): ApiConfigOptions {
    return { ...currentConfig };
  },
};

// =============================================================================
// Hooks React pour utiliser la config
// =============================================================================

/**
 * Hook pour obtenir l'URL d'un module.
 *
 * @example
 * const accountingUrl = useApiUrl('accounting', '/summary');
 * // Returns: '/v3/accounting/summary'
 */
export function useApiUrl(module: string, path: string): string {
  return API_CONFIG.getUrl(module, path);
}

/**
 * Constantes pour les modules principaux.
 */
export const MODULES = {
  ACCOUNTING: 'accounting',
  COMMERCIAL: 'commercial',
  CONTACTS: 'contacts',
  FINANCE: 'finance',
  HR: 'hr',
  IAM: 'iam',
  INVENTORY: 'inventory',
  INTERVENTIONS: 'interventions',
  INVOICING: 'invoicing',
  PRODUCTION: 'production',
  PROJECTS: 'projects',
  PURCHASES: 'purchases',
  TENANTS: 'tenants',
  TREASURY: 'treasury',
} as const;

export type ModuleName = typeof MODULES[keyof typeof MODULES];

// =============================================================================
// Export par défaut
// =============================================================================

export default API_CONFIG;
