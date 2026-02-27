/**
 * AZALSCORE - Métadonnées Module Manufacturing (AZA-FE-META)
 * ===========================================================
 * Module GPAO/Production
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Manufacturing',
  code: 'manufacturing',
  version: '1.0.0',
  description: 'Gestion de Production Assistee par Ordinateur - Nomenclatures, Ordres de Fabrication, Postes de Travail',

  // ============================================================
  // ÉTAT
  // ============================================================

  status: 'active' as 'active' | 'degraded' | 'inactive',

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: true,
    pagesCount: 7,
    routesCount: 7,
    errorsCount: 0,
    lastAudit: '2026-02-27',
    compliance: true,
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: true,
    lastCheck: '2026-02-27',
    endpoints: [
      '/manufacturing/boms',
      '/manufacturing/work-orders',
      '/manufacturing/workcenters',
      '/manufacturing/routings',
      '/manufacturing/quality-checks',
      '/manufacturing/stats',
      '/manufacturing/dashboard',
    ],
  },

  // ============================================================
  // NAVIGATION
  // ============================================================

  navigation: [
    { label: 'Tableau de bord', path: '/manufacturing', icon: 'LayoutDashboard' },
    { label: 'Nomenclatures', path: '/manufacturing/boms', icon: 'FileStack' },
    { label: 'Ordres de fabrication', path: '/manufacturing/work-orders', icon: 'ClipboardList' },
    { label: 'Postes de travail', path: '/manufacturing/workcenters', icon: 'Wrench' },
    { label: 'Gammes', path: '/manufacturing/routings', icon: 'Route' },
    { label: 'Qualite', path: '/manufacturing/quality', icon: 'BadgeCheck' },
    { label: 'Planning', path: '/manufacturing/planning', icon: 'CalendarRange' },
  ],

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'Production',
  criticality: 'high' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-02-27',
  updatedAt: '2026-02-27',
} as const;

export type ModuleMeta = typeof moduleMeta;

export default moduleMeta;
