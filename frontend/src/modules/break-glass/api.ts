/**
 * AZALSCORE - Break-Glass API
 * ============================
 * API client sécurisé pour le module Break-Glass souverain.
 *
 * MÉCANISME D'URGENCE SOUVERAIN
 * - Accessible UNIQUEMENT si capacité backend `admin.root.break_glass` présente
 * - Traçabilité complète et inviolable
 * - Responsabilité personnelle engagée
 */

import { api } from '@/core/api-client';

// ============================================================================
// TYPES
// ============================================================================

/**
 * Scope définissant le périmètre d'intervention Break-Glass
 */
export interface BreakGlassScope {
  tenant_id?: string;
  module?: string;
  start_date?: string;
  end_date?: string;
}

/**
 * Challenge de confirmation Break-Glass
 * Contient la phrase à taper pour confirmer l'intention
 */
export interface BreakGlassChallenge {
  challenge_id: string;
  confirmation_phrase: string;
  expires_at: string;
  scope: BreakGlassScope;
}

/**
 * Requête d'exécution Break-Glass
 * Inclut toutes les données de confirmation et d'authentification
 */
export interface BreakGlassRequest {
  scope: BreakGlassScope;
  confirmation_phrase: string;
  reason?: string;
  password: string;
  totp_code?: string;
}

/**
 * Résultat de l'exécution Break-Glass
 */
export interface BreakGlassResult {
  success: boolean;
  execution_id: string;
  executed_at: string;
  scope: BreakGlassScope;
  audit_reference: string;
}

/**
 * Option de tenant pour la sélection de périmètre
 */
export interface TenantOption {
  id: string;
  name: string;
}

/**
 * Option de module pour la sélection de périmètre
 */
export interface ModuleOption {
  id: string;
  name: string;
}

/**
 * Liste paginée de tenants
 */
export interface TenantList {
  items: TenantOption[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Liste de modules
 */
export interface ModuleList {
  items: ModuleOption[];
}

// ============================================================================
// HELPERS
// ============================================================================

const ADMIN_PATH = '/admin';

function buildQueryString(
  params: Record<string, string | number | boolean | undefined | null>
): string {
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
// API CLIENT
// ============================================================================

export const breakGlassApi = {
  // ==========================================================================
  // Challenge & Execution
  // ==========================================================================

  /**
   * Demande un challenge de confirmation Break-Glass
   * Génère une phrase unique à taper pour confirmer l'intention
   */
  requestChallenge: (scope: BreakGlassScope) =>
    api.post<BreakGlassChallenge>(`${ADMIN_PATH}/break-glass/challenge`, scope),

  /**
   * Exécute la procédure Break-Glass après confirmation complète
   * Nécessite: phrase correcte + mot de passe + 2FA (si activé)
   */
  execute: (request: BreakGlassRequest) =>
    api.post<BreakGlassResult>(`${ADMIN_PATH}/break-glass/execute`, request),

  // ==========================================================================
  // Scope Options (pour le formulaire)
  // ==========================================================================

  /**
   * Liste tous les tenants disponibles pour la sélection de périmètre
   */
  listTenants: (params?: { page_size?: number }) =>
    api.get<TenantList>(
      `${ADMIN_PATH}/tenants${buildQueryString({ page_size: params?.page_size || 1000 })}`
    ),

  /**
   * Liste tous les modules disponibles pour la sélection de périmètre
   */
  listModules: () =>
    api.get<ModuleList>(`${ADMIN_PATH}/modules`),
};

export default breakGlassApi;
