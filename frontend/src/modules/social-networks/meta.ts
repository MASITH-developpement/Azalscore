/**
 * AZALS MODULE - Réseaux Sociaux - Metadata
 * =========================================
 * Conformité AZA-FE-META standard
 */

export const moduleMeta = {
  name: 'Réseaux Sociaux',
  code: 'social_networks',
  version: '1.0.0',

  status: 'active' as const,

  frontend: {
    hasUI: true,
    pagesCount: 1,
    routesCount: 1,
    errorsCount: 0,
    lastAudit: '2026-02-20',
    compliance: true,
  },

  backend: {
    apiAvailable: true,
    lastCheck: '2026-02-20',
    endpoints: [
      '/admin/social-networks/platforms',
      '/admin/social-networks/metrics',
      '/admin/social-networks/summary',
      '/admin/social-networks/google-analytics',
      '/admin/social-networks/google-ads',
      '/admin/social-networks/google-search-console',
      '/admin/social-networks/google-my-business',
      '/admin/social-networks/meta',
      '/admin/social-networks/linkedin',
      '/admin/social-networks/solocal',
      '/admin/social-networks/sync-prometheus',
    ],
  },

  owner: 'AZALS Core Team',
  criticality: 'medium' as const,

  description: 'Module d\'administration pour la saisie manuelle des métriques marketing des réseaux sociaux et plateformes digitales.',

  features: [
    'Saisie des métriques Google Analytics',
    'Saisie des métriques Google Ads',
    'Saisie des métriques Search Console',
    'Saisie des métriques Google My Business',
    'Saisie des métriques Meta (Facebook/Instagram)',
    'Saisie des métriques LinkedIn',
    'Saisie des métriques Solocal',
    'Synchronisation Prometheus/Grafana',
    'Récapitulatif marketing multi-plateformes',
  ],

  createdAt: '2026-02-20',
  updatedAt: '2026-02-20',
} as const;

export default moduleMeta;
