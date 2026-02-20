/**
 * AZALSCORE - Métadonnées Module Triggers (AZA-FE-META)
 * =============================================
 * Fichier généré automatiquement - Mettre à jour si nécessaire
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Triggers',
  code: 'triggers',
  version: '1.0.0',

  // ============================================================
  // ÉTAT
  // ============================================================

  status: 'active' as 'active' | 'degraded' | 'inactive',

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: true,
    pagesCount: 1,
    routesCount: 1,
    errorsCount: 0,
    lastAudit: '2026-02-20',
    compliance: true,
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: false, // À vérifier manuellement
    lastCheck: '2026-02-20',
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

  createdAt: '2026-02-20',
  updatedAt: '2026-02-20',
} as const;

export type ModuleMeta = typeof moduleMeta;
