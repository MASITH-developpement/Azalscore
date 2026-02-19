/**
 * AZALSCORE - Métadonnées Module Compliance (AZA-FE-META)
 * =============================================
 * Fichier généré automatiquement - Mettre à jour si nécessaire
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Compliance',
  code: 'compliance',
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
    lastAudit: '2026-02-17',
    compliance: true,
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: true,
    lastCheck: '2026-02-17',
    endpoints: [
      'GET /compliance/stats',
      'GET /compliance/metrics',
      'GET /compliance/policies',
      'GET /compliance/audits',
      'GET /compliance/audits/{id}',
      'POST /compliance/audits',
      'POST /compliance/audits/{id}/start',
      'POST /compliance/audits/{id}/complete',
      'POST /compliance/audits/{id}/close',
      'GET /compliance/regulations',
      'POST /compliance/regulations',
      'GET /compliance/requirements',
      'POST /compliance/requirements',
      'GET /compliance/policies/{id}',
      'POST /compliance/policies',
      'POST /compliance/policies/{id}/publish',
      'GET /compliance/risks/{id}',
      'POST /compliance/risks',
      'GET /compliance/incidents/{id}',
      'POST /compliance/incidents',
    ],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'AZALSCORE',
  criticality: 'high' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-01-23',
  updatedAt: '2026-02-17',
} as const;

export type ModuleMeta = typeof moduleMeta;
