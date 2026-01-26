/**
 * AZALSCORE - Métadonnées Module Interventions (AZA-FE-META)
 * =============================================
 * Dernière mise à jour : 2026-01-26
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Interventions',
  code: 'interventions',
  version: '1.1.0',

  // ============================================================
  // ÉTAT
  // ============================================================

  status: 'active' as 'active' | 'degraded' | 'inactive',

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: true,
    pagesCount: 5,
    routesCount: 1,
    errorsCount: 0,
    lastAudit: '2026-01-26',
    compliance: true,
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: true,
    lastCheck: '2026-01-26',
    endpoints: [
      'GET    /v2/interventions/donneurs-ordre',
      'GET    /v2/interventions/donneurs-ordre/:id',
      'POST   /v2/interventions/donneurs-ordre',
      'PUT    /v2/interventions/donneurs-ordre/:id',
      'GET    /v2/interventions',
      'GET    /v2/interventions/stats',
      'GET    /v2/interventions/:id',
      'GET    /v2/interventions/ref/:reference',
      'POST   /v2/interventions',
      'PUT    /v2/interventions/:id',
      'DELETE /v2/interventions/:id',
      'POST   /v2/interventions/:id/planifier',
      'PUT    /v2/interventions/:id/planification',
      'DELETE /v2/interventions/:id/planification',
      'POST   /v2/interventions/:id/arrivee',
      'POST   /v2/interventions/:id/demarrer',
      'POST   /v2/interventions/:id/terminer',
      'GET    /v2/interventions/:id/rapport',
      'PUT    /v2/interventions/:id/rapport',
      'POST   /v2/interventions/:id/rapport/photos',
      'POST   /v2/interventions/:id/rapport/signer',
      'GET    /v2/interventions/rapports-finaux',
      'GET    /v2/interventions/rapports-finaux/:id',
      'POST   /v2/interventions/rapports-finaux',
    ],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'Interventions',
  criticality: 'high' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-01-23',
  updatedAt: '2026-01-26',
} as const;

export type ModuleMeta = typeof moduleMeta;
