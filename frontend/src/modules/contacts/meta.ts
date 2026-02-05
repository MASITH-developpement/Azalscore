/**
 * AZALSCORE - Métadonnées Module Contacts Unifiés (AZA-FE-META)
 * ==============================================================
 * Gestion unifiée des clients et fournisseurs
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Contacts',
  code: 'contacts',
  version: '2.0.0',

  // ============================================================
  // ÉTAT
  // ============================================================

  status: 'active' as 'active' | 'degraded' | 'inactive',

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: true,
    pagesCount: 2,
    routesCount: 3,
    errorsCount: 0,
    lastAudit: '2026-01-29',
    compliance: true,
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: true,
    lastCheck: '2026-01-29',
    endpoints: [
      '/v2/contacts',
      '/v2/contacts/{id}',
      '/v2/contacts/lookup',
      '/v2/contacts/{id}/persons',
      '/v2/contacts/{id}/addresses',
      '/v2/contacts/{id}/logo',
      '/v2/contacts/{id}/stats',
    ] as readonly string[],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'Commercial / Achats',
  criticality: 'high' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-01-29',
  updatedAt: '2026-01-29',
} as const;

export type ModuleMeta = typeof moduleMeta;
