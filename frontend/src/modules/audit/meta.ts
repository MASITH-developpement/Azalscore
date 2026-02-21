/**
 * AZALSCORE - Metadonnees Module Audit (AZA-FE-META)
 * =============================================
 * Module d'audit, benchmark et conformite
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Audit & Benchmark',
  code: 'audit',
  version: '1.0.0',

  // ============================================================
  // ETAT
  // ============================================================

  status: 'active' as 'active' | 'degraded' | 'inactive',

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: true,
    pagesCount: 8,
    routesCount: 13,
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
      // Logs
      'GET /audit/logs',
      'GET /audit/logs/{id}',
      'GET /audit/logs/entity/{entity_type}/{entity_id}',
      'GET /audit/logs/user/{user_id}',
      // Sessions
      'GET /audit/sessions',
      'POST /audit/sessions/{session_id}/terminate',
      // Metriques
      'POST /audit/metrics',
      'GET /audit/metrics',
      'POST /audit/metrics/record',
      'GET /audit/metrics/{code}/values',
      // Benchmarks
      'POST /audit/benchmarks',
      'GET /audit/benchmarks',
      'POST /audit/benchmarks/{id}/run',
      'GET /audit/benchmarks/{id}/results',
      // Conformite
      'POST /audit/compliance/checks',
      'GET /audit/compliance/checks',
      'PUT /audit/compliance/checks/{id}',
      'GET /audit/compliance/summary',
      // Retention
      'POST /audit/retention/rules',
      'GET /audit/retention/rules',
      'POST /audit/retention/apply',
      // Exports
      'POST /audit/exports',
      'GET /audit/exports',
      'GET /audit/exports/{id}',
      'POST /audit/exports/{id}/process',
      // Dashboards
      'POST /audit/dashboards',
      'GET /audit/dashboards',
      'GET /audit/dashboards/{id}/data',
      // Stats
      'GET /audit/stats',
      'GET /audit/dashboard',
    ],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'Security',
  criticality: 'high' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-02-20',
  updatedAt: '2026-02-20',
} as const;

export type ModuleMeta = typeof moduleMeta;
