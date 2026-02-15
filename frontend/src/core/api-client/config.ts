/**
 * AZALSCORE - Configuration API
 * ==============================
 * API sans version - URLs directes (ex: /commercial/customers)
 *
 * Principe: Pas de préfixe de version (/v1, /v2, /v3)
 * Les URLs sont stables et ne changent pas.
 */

import { api } from './index';

// =============================================================================
// API Config Object
// =============================================================================

export const API_CONFIG = {
  /**
   * Construit l'URL complète pour un endpoint.
   *
   * @param module - Nom du module (ex: 'accounting', 'commercial')
   * @param path - Chemin de l'endpoint (ex: '/summary', '/customers/123')
   * @returns URL complète (ex: '/accounting/summary')
   */
  getUrl(module: string, path: string): string {
    // Normaliser le path (enlever le / initial si présent)
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `/${module}${normalizedPath}`;
  },

  /**
   * Fetch simple sans version.
   */
  async fetch<T>(
    module: string,
    path: string,
    options?: RequestInit
  ): Promise<T> {
    const url = this.getUrl(module, path);
    return await api.get<T>(url) as T;
  },

  /**
   * POST simple sans version.
   */
  async post<T>(
    module: string,
    path: string,
    data: unknown,
    options?: RequestInit
  ): Promise<T> {
    const url = this.getUrl(module, path);
    return await api.post<T>(url, data) as T;
  },
};

// =============================================================================
// Hooks React
// =============================================================================

/**
 * Hook pour obtenir l'URL d'un module.
 *
 * @example
 * const accountingUrl = useApiUrl('accounting', '/summary');
 * // Returns: '/accounting/summary'
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
