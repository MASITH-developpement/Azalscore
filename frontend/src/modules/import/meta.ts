/**
 * AZALSCORE - Métadonnées Module Import (AZA-FE-META)
 * ===================================================
 * Import de données depuis fichiers (CSV, Excel, etc.)
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Import',
  code: 'import',
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
      'POST /import/upload',
      'POST /import/parse',
      'POST /import/validate',
      'POST /import/execute',
      'GET /import/history',
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

  createdAt: '2026-02-18',
  updatedAt: '2026-02-20',
} as const;

export type ModuleMeta = typeof moduleMeta;
