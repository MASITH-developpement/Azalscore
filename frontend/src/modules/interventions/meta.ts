/**
 * AZALSCORE - Métadonnées Module Interventions (AZA-FE-META)
 * ==========================================================
 * Conforme AZA-META, AZA-CERT, AZA-MNT
 * Dernière mise à jour : 2026-01-28
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Interventions',
  code: 'interventions',
  version: '1.2.0',

  // ============================================================
  // ÉTAT
  // ============================================================

  status: 'active' as 'active' | 'degraded' | 'inactive',

  // ============================================================
  // CERTIFICATION (AZA-CERT)
  // ============================================================

  certification: {
    frontend: 'CERT-B' as 'CERT-A' | 'CERT-B' | 'CERT-C' | 'CERT-X',
    backend: 'CERT-B' as 'CERT-A' | 'CERT-B' | 'CERT-C' | 'CERT-X',
    lastAudit: '2026-01-28',
    auditor: 'AZALSCORE-Audit-System',
    nonConformities: 0,
    nextAudit: '2026-02-28',
  },

  // ============================================================
  // MAINTENANCE (AZA-MNT)
  // ============================================================

  maintenance: {
    lifecycle: 'Actif' as 'Actif' | 'Maintenu' | 'Surveillance' | 'Obsolète' | 'Retiré',
    sla: {
      uptime: 99.5,
      maxResponseTime: 2000,
      maxDowntime: '4h',
    },
    scoring: {
      reliability: 85,
      testCoverage: 70,
      documentation: 75,
      codeQuality: 80,
    },
    changelog: [
      { version: '1.2.0', date: '2026-01-28', description: 'Mise en conformité AZA complète' },
      { version: '1.1.0', date: '2026-01-26', description: 'Migration vers BaseViewStandard' },
      { version: '1.0.0', date: '2026-01-23', description: 'Version initiale du module' },
    ],
  },

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: true,
    pagesCount: 5,
    routesCount: 1,
    errorsCount: 0,
    lastAudit: '2026-01-28',
    compliance: true,
    structure: {
      'index.tsx': 'Module principal (page)',
      'api.ts': 'Couche API (hooks React Query)',
      'types.ts': 'Types partagés',
      'meta.ts': 'Métadonnées module',
      'components/': 'Composants onglets',
      'hooks/': 'Hooks workflow',
    },
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: true,
    apiVersion: 'v2',
    lastCheck: '2026-01-28',
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
      'POST   /v2/interventions/:id/annuler',
      'GET    /v2/interventions/:id/rapport',
      'PUT    /v2/interventions/:id/rapport',
      'POST   /v2/interventions/:id/rapport/photos',
      'POST   /v2/interventions/:id/rapport/signer',
      'GET    /v2/interventions/rapports-finaux',
      'GET    /v2/interventions/rapports-finaux/:id',
      'POST   /v2/interventions/rapports-finaux',
    ],
    structure: {
      'models.py': 'Modèles SQLAlchemy (tenant-aware)',
      'service.py': 'Logique métier pure',
      'router_v2.py': 'Endpoints API v2',
      'schemas.py': 'Schémas Pydantic (input)',
      'schemas_v2.py': 'Schémas Pydantic (output v2)',
    },
  },

  // ============================================================
  // GOUVERNANCE (AZA-NF)
  // ============================================================

  owner: 'Équipe Terrain',
  criticality: 'high' as 'high' | 'medium' | 'low',

  dependencies: {
    consumes: ['commercial', 'hr', 'planning'],
    consumedBy: ['facturation', 'reporting'],
  },

  // ============================================================
  // SÉCURITÉ (AZA-SEC)
  // ============================================================

  security: {
    rbac: true,
    tenantIsolation: true,
    auditLog: true,
    dataRetention: 'LEGAL',
  },

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-01-23',
  updatedAt: '2026-01-28',
} as const;

export type ModuleMeta = typeof moduleMeta;
