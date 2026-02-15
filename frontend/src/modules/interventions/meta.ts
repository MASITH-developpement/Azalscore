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
    apiVersion: 'v3',
    lastCheck: '2026-01-28',
    endpoints: [
      'GET    /interventions/donneurs-ordre',
      'GET    /interventions/donneurs-ordre/:id',
      'POST   /interventions/donneurs-ordre',
      'PUT    /interventions/donneurs-ordre/:id',
      'GET    /interventions',
      'GET    /interventions/stats',
      'GET    /interventions/:id',
      'GET    /interventions/ref/:reference',
      'POST   /interventions',
      'PUT    /interventions/:id',
      'DELETE /interventions/:id',
      'POST   /interventions/:id/planifier',
      'PUT    /interventions/:id/planification',
      'DELETE /interventions/:id/planification',
      'POST   /interventions/:id/arrivee',
      'POST   /interventions/:id/demarrer',
      'POST   /interventions/:id/terminer',
      'POST   /interventions/:id/annuler',
      'GET    /interventions/:id/rapport',
      'PUT    /interventions/:id/rapport',
      'POST   /interventions/:id/rapport/photos',
      'POST   /interventions/:id/rapport/signer',
      'GET    /interventions/rapports-finaux',
      'GET    /interventions/rapports-finaux/:id',
      'POST   /interventions/rapports-finaux',
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
