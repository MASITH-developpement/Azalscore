/**
 * AZALSCORE - Publications Réseaux Sociaux - Métadonnées
 * ======================================================
 * Configuration module conforme AZA-FE-META
 */

export const moduleMeta = {
  // ============================================================
  // IDENTIFICATION
  // ============================================================

  name: 'Publications Réseaux Sociaux',
  code: 'social_publications',
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
    pagesCount: 4, // Dashboard, Posts, Leads, Templates
    routesCount: 4,
    errorsCount: 0,
    lastAudit: '2026-02-25',
    compliance: true,
  },

  // ============================================================
  // BACKEND
  // ============================================================

  backend: {
    apiAvailable: true,
    lastCheck: '2026-02-25',
    endpoints: [
      // Campagnes
      '/api/v1/social/publications/campaigns',
      '/api/v1/social/publications/campaigns/{id}',
      '/api/v1/social/publications/campaigns/{id}/stats',
      // Publications
      '/api/v1/social/publications/posts',
      '/api/v1/social/publications/posts/{id}',
      '/api/v1/social/publications/posts/{id}/schedule',
      '/api/v1/social/publications/posts/{id}/publish',
      '/api/v1/social/publications/posts/{id}/duplicate',
      // Leads
      '/api/v1/social/publications/leads',
      '/api/v1/social/publications/leads/{id}',
      '/api/v1/social/publications/leads/{id}/interactions',
      '/api/v1/social/publications/leads/{id}/convert',
      '/api/v1/social/publications/leads/funnel',
      // Templates
      '/api/v1/social/publications/templates',
      '/api/v1/social/publications/templates/{id}',
      '/api/v1/social/publications/templates/{id}/render',
      // Calendrier & Analytics
      '/api/v1/social/publications/calendar',
      '/api/v1/social/publications/slots',
      '/api/v1/social/publications/optimal-time',
      '/api/v1/social/publications/analytics/platforms',
      '/api/v1/social/publications/analytics/suggestions',
    ],
  },

  // ============================================================
  // GOUVERNANCE
  // ============================================================

  owner: 'Marketing',
  criticality: 'medium' as 'high' | 'medium' | 'low',

  // ============================================================
  // DESCRIPTION
  // ============================================================

  description: `
    Module de création et gestion des publications sur les réseaux sociaux
    pour générer des leads vers azalscore.com.

    Fonctionnalités principales:
    - Création de publications multi-plateformes (Facebook, Instagram, LinkedIn, Twitter)
    - Programmation et calendrier éditorial
    - Templates réutilisables avec variables
    - Tracking UTM automatique
    - Génération et qualification de leads
    - Conversion en contacts/opportunités CRM
    - Analytics par plateforme
    - Suggestions de contenu IA
  `,

  // ============================================================
  // AUDIT
  // ============================================================

  createdAt: '2026-02-25',
  updatedAt: '2026-02-25',
} as const;

export type ModuleMeta = typeof moduleMeta;
