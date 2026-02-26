/**
 * AZALSCORE - Metadonnees Module Triggers (AZA-FE-META)
 * =============================================
 * Module de gestion des declencheurs, alertes et notifications
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Triggers & Diffusion',
  code: 'triggers',
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
    pagesCount: 10,
    routesCount: 14,
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
      // Triggers CRUD
      'POST /triggers/',
      'GET /triggers/',
      'GET /triggers/{id}',
      'PUT /triggers/{id}',
      'DELETE /triggers/{id}',
      'POST /triggers/{id}/pause',
      'POST /triggers/{id}/resume',
      'POST /triggers/{id}/fire',
      // Subscriptions
      'POST /triggers/subscriptions',
      'GET /triggers/subscriptions/{trigger_id}',
      'DELETE /triggers/subscriptions/{id}',
      // Events
      'GET /triggers/events',
      'GET /triggers/events/{id}',
      'POST /triggers/events/{id}/resolve',
      'POST /triggers/events/{id}/escalate',
      // Notifications
      'GET /triggers/notifications',
      'POST /triggers/notifications/{id}/read',
      'POST /triggers/notifications/read-all',
      'POST /triggers/notifications/send-pending',
      // Templates
      'POST /triggers/templates',
      'GET /triggers/templates',
      'GET /triggers/templates/{id}',
      'PUT /triggers/templates/{id}',
      'DELETE /triggers/templates/{id}',
      // Scheduled Reports
      'POST /triggers/reports',
      'GET /triggers/reports',
      'GET /triggers/reports/{id}',
      'PUT /triggers/reports/{id}',
      'DELETE /triggers/reports/{id}',
      'POST /triggers/reports/{id}/generate',
      'GET /triggers/reports/{id}/history',
      // Webhooks
      'POST /triggers/webhooks',
      'GET /triggers/webhooks',
      'GET /triggers/webhooks/{id}',
      'PUT /triggers/webhooks/{id}',
      'DELETE /triggers/webhooks/{id}',
      'POST /triggers/webhooks/{id}/test',
      // Logs & Dashboard
      'GET /triggers/logs',
      'GET /triggers/dashboard',
    ],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'System',
  criticality: 'high' as 'high' | 'medium' | 'low',

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-02-20',
  updatedAt: '2026-02-20',
} as const;

export type ModuleMeta = typeof moduleMeta;
