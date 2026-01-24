/**
 * AZALSCORE - Métadonnées Module Mobile (AZA-FE-META)
 * =============================================
 * Fichier généré automatiquement - Mettre à jour si nécessaire
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Mobile',
  code: 'mobile',
  version: '1.0.0',

  // ============================================================
  // ÉTAT
  // ============================================================

  status: 'degraded' as 'active' | 'degraded' | 'inactive',

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: true,
    pagesCount: 1,
    routesCount: 1,
    errorsCount: 0,
    lastAudit: '2026-01-23',
    compliance: false,
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: false, // À vérifier manuellement
    lastCheck: '2026-01-23',
    endpoints: [],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'À définir',
  criticality: 'medium' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-01-23',
  updatedAt: '2026-01-23',
} as const;

export type ModuleMeta = typeof moduleMeta;
