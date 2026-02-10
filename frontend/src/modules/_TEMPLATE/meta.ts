/**
 * AZALSCORE - Métadonnées Module (AZA-FE-META)
 * =============================================
 * Fichier obligatoire par module
 *
 * Ce template doit être copié et adapté pour chaque nouveau module
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Nom du Module',
  code: 'module_code', // Identifiant unique (snake_case)
  version: '1.0.0',

  // ============================================================
  // ÉTAT
  // ============================================================

  status: 'active' as 'active' | 'degraded' | 'inactive',
  // active: Module fonctionnel et conforme
  // degraded: Module fonctionnel mais non conforme AZA-FE
  // inactive: Module désactivé

  // ============================================================
  // FRONTEND
  // ============================================================

  frontend: {
    hasUI: true, // Module a une interface utilisateur
    pagesCount: 1, // Nombre de pages/vues
    routesCount: 1, // Nombre de routes
    errorsCount: 0, // Nombre d'erreurs détectées
    lastAudit: '2024-01-23', // Date dernier audit (YYYY-MM-DD)
    compliance: true, // Conformité AZA-FE (ENF/DASH/META)
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: false, // API backend disponible
    lastCheck: '2024-01-23', // Date dernière vérification (YYYY-MM-DD)
    endpoints: [
      // Liste des endpoints API disponibles
      // '/api/v1/resource',
      // '/api/v1/resource/:id',
    ],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'À définir', // Équipe ou responsable du module
  criticality: 'medium' as 'high' | 'medium' | 'low',
  // high: Module critique (facturation, compta, etc.)
  // medium: Module important (CRM, projets, etc.)
  // low: Module secondaire (paramètres, etc.)

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2024-01-01', // Date création module (YYYY-MM-DD)
  updatedAt: '2024-01-23', // Date dernière mise à jour (YYYY-MM-DD)
} as const;

export type ModuleMeta = typeof moduleMeta;
