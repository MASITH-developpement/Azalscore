/**
 * AZALSCORE Module - Dashboards Meta
 * Metadonnees du module de tableaux de bord
 */

import type { ModuleMeta } from '@/core/types';

export const dashboardsMeta: ModuleMeta = {
  id: 'dashboards',
  name: 'Tableaux de bord',
  description: 'Visualisation de donnees, KPIs, graphiques et rapports personnalisables',
  icon: 'LayoutDashboard',
  route: '/dashboards',
  category: 'analytics',
  permissions: ['dashboards:read', 'dashboards:write', 'dashboards:admin'],
  features: [
    'dashboards',    // Tableaux de bord
    'widgets',       // Widgets KPI/Charts
    'data-sources',  // Sources de donnees
    'alerts',        // Alertes
    'reports',       // Rapports planifies
    'templates',     // Modeles
  ],
  navigation: [
    {
      label: 'Mes tableaux',
      path: '/dashboards',
      icon: 'LayoutDashboard',
    },
    {
      label: 'Favoris',
      path: '/dashboards/favorites',
      icon: 'Star',
    },
    {
      label: 'Alertes',
      path: '/dashboards/alerts',
      icon: 'Bell',
    },
    {
      label: 'Rapports',
      path: '/dashboards/reports',
      icon: 'FileText',
    },
    {
      label: 'Templates',
      path: '/dashboards/templates',
      icon: 'LayoutTemplate',
    },
  ],
  stats: [
    { key: 'total_dashboards', label: 'Tableaux', icon: 'LayoutDashboard' },
    { key: 'total_widgets', label: 'Widgets', icon: 'BarChart' },
    { key: 'active_alerts', label: 'Alertes', icon: 'Bell' },
    { key: 'scheduled_reports', label: 'Rapports', icon: 'Calendar' },
  ],
};

export default dashboardsMeta;
