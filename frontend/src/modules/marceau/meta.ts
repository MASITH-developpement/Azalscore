/**
 * AZALSCORE - Métadonnées Module Marceau (AZA-FE-META)
 * ====================================================
 * Module Marceau - Gestion des tarifs et marges
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Marceau',
  code: 'marceau',
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
    apiAvailable: true,
    lastCheck: '2026-02-20',
    endpoints: [
      'GET /marceau/pricing',
      'POST /marceau/pricing',
      'GET /marceau/margins',
      'POST /marceau/calculate',
    ] as readonly string[],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'AZALSCORE',
  criticality: 'medium' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-02-14',
  updatedAt: '2026-02-20',
} as const;

export type ModuleMeta = typeof moduleMeta;
