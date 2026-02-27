/**
 * AZALSCORE Module - Manufacturing Meta
 * Metadonnees du module GPAO/Production
 */

import type { ModuleMeta } from '@/core/types';

export const manufacturingMeta: ModuleMeta = {
  id: 'manufacturing',
  name: 'Production (GPAO)',
  description: 'Gestion de Production Assistee par Ordinateur - Nomenclatures, Ordres de Fabrication, Postes de Travail',
  icon: 'Factory',
  route: '/manufacturing',
  category: 'production',
  permissions: ['manufacturing:read', 'manufacturing:write', 'manufacturing:admin'],
  features: [
    'bom',           // Nomenclatures (Bill of Materials)
    'work-orders',   // Ordres de fabrication
    'workcenters',   // Postes de travail
    'routings',      // Gammes operatoires
    'quality',       // Controles qualite
    'planning',      // Planification / Gantt
  ],
  navigation: [
    {
      label: 'Tableau de bord',
      path: '/manufacturing',
      icon: 'LayoutDashboard',
    },
    {
      label: 'Nomenclatures',
      path: '/manufacturing/boms',
      icon: 'FileStack',
    },
    {
      label: 'Ordres de fabrication',
      path: '/manufacturing/work-orders',
      icon: 'ClipboardList',
    },
    {
      label: 'Postes de travail',
      path: '/manufacturing/workcenters',
      icon: 'Wrench',
    },
    {
      label: 'Gammes',
      path: '/manufacturing/routings',
      icon: 'Route',
    },
    {
      label: 'Qualite',
      path: '/manufacturing/quality',
      icon: 'BadgeCheck',
    },
    {
      label: 'Planning',
      path: '/manufacturing/planning',
      icon: 'CalendarRange',
    },
  ],
  stats: [
    { key: 'active_work_orders', label: 'OF actifs', icon: 'ClipboardList' },
    { key: 'in_progress', label: 'En cours', icon: 'Play' },
    { key: 'completed_today', label: 'Termines aujourd\'hui', icon: 'CheckCircle' },
    { key: 'oee_today', label: 'OEE', icon: 'Gauge', format: 'percent' },
  ],
};

export default manufacturingMeta;
