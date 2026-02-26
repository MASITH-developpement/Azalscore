/**
 * AZALSCORE - Métadonnées Module Passerelles d'Import (AZA-FE-META)
 * =================================================================
 * Gestion des connexions d'import multi-sources (Odoo, etc.)
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Passerelles d\'Import',
  code: 'import-gateways',
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
      'GET /import-gateways',
      'GET /import-gateways/{id}',
      'POST /import-gateways',
      'PUT /import-gateways/{id}',
      'DELETE /import-gateways/{id}',
      'POST /import-gateways/{id}/sync',
      'POST /import-gateways/{id}/test',
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

  createdAt: '2026-02-15',
  updatedAt: '2026-02-20',
} as const;

export type ModuleMeta = typeof moduleMeta;
