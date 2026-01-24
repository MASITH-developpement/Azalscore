/**
 * AZALSCORE - Métadonnées Module Not Found (AZA-FE-META)
 */

export const moduleMeta = {
  name: 'Page 404',
  code: 'not-found',
  version: '1.0.0',
  status: 'active' as const,

  frontend: {
    hasUI: true,
    pagesCount: 1,
    routesCount: 1,
    errorsCount: 0,
    lastAudit: '2026-01-23',
    compliance: true,
  },

  backend: {
    apiAvailable: false,
    lastCheck: '2026-01-23',
    endpoints: [],
  },

  owner: 'Frontend Team',
  criticality: 'low' as const,

  createdAt: '2026-01-23',
  updatedAt: '2026-01-23',
} as const;

export type ModuleMeta = typeof moduleMeta;
