/**
 * Configuration de marque Azalscore
 *
 * Ce module gère le titre d'onglet et le favicon de l'application.
 * Préparé pour le multi-tenant mais désactivé par défaut.
 *
 * SÉCURITÉ:
 * - Le favicon par défaut est un asset système non modifiable
 * - Le titre par défaut est "Azalscore"
 * - Le mode multi-tenant est désactivé par défaut
 */

export interface BrandingConfig {
  title: string;
  faviconPath: string;
  tenantName?: string;
}

// Configuration par défaut - Asset système non modifiable
const DEFAULT_BRANDING: BrandingConfig = {
  title: 'Azalscore',
  faviconPath: '/favicon.png',
};

// Configuration multi-tenant - DÉSACTIVÉ par défaut
// Activer en passant ENABLE_TENANT_BRANDING à true
const ENABLE_TENANT_BRANDING = false;

/**
 * Récupère la configuration de marque active.
 * Retourne toujours la configuration par défaut si le multi-tenant est désactivé.
 */
export function getBrandingConfig(tenantName?: string): BrandingConfig {
  // Multi-tenant désactivé - retourner la config par défaut
  if (!ENABLE_TENANT_BRANDING || !tenantName) {
    return DEFAULT_BRANDING;
  }

  // Multi-tenant activé - utiliser le nom du tenant comme titre
  return {
    ...DEFAULT_BRANDING,
    title: tenantName,
    tenantName,
  };
}

/**
 * Applique le titre dans le document.
 * Cette fonction est idempotente et peut être appelée plusieurs fois.
 */
export function applyBrowserTitle(config: BrandingConfig = DEFAULT_BRANDING): void {
  if (typeof document !== 'undefined') {
    document.title = config.title;
  }
}

/**
 * Initialise le branding au démarrage de l'application.
 * Garantit que le titre "Azalscore" est affiché dès le chargement.
 */
export function initializeBranding(): void {
  const config = getBrandingConfig();
  applyBrowserTitle(config);
}

export { DEFAULT_BRANDING, ENABLE_TENANT_BRANDING };
