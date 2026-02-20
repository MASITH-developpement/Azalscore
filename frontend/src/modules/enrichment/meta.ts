/**
 * AZALSCORE - Métadonnées Module Enrichment (AZA-FE-META)
 * =======================================================
 * Service d'enrichissement de données (SIRET, risques, scoring)
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Enrichment',
  code: 'enrichment',
  version: '2.0.0',

  // ============================================================
  // ÉTAT
  // ============================================================

  status: 'active' as 'active' | 'degraded' | 'inactive',

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: false, // Service uniquement - pas de pages dédiées
    pagesCount: 0,
    routesCount: 0,
    errorsCount: 0,
    lastAudit: '2026-02-20',
    compliance: true,
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: true,
    lastCheck: '2026-02-20',
    endpoints: [
      'POST /enrichment/siret/lookup',
      'POST /enrichment/siret/batch',
      'POST /enrichment/barcode/lookup',
      'POST /enrichment/barcode/batch',
      'GET /enrichment/risk/{entity_type}/{entity_id}',
      'POST /enrichment/risk/analyze',
      'GET /enrichment/score/{entity_type}/{entity_id}',
      'POST /enrichment/score/calculate',
    ] as readonly string[],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'AZALSCORE',
  criticality: 'high' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-02-15',
  updatedAt: '2026-02-20',
} as const;

export type ModuleMeta = typeof moduleMeta;
