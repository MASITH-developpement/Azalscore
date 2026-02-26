/**
 * AZALSCORE - Cache Module Meta
 * ==============================
 * Metadonnees du module Cache Admin Panel.
 */

import { Database } from 'lucide-react';

export const moduleMeta = {
  id: 'cache',
  name: 'Gestion du Cache',
  description: 'Administration du cache applicatif multi-niveau (L1/L2/L3)',
  icon: Database,
  category: 'administration',
  path: '/admin/cache',
  permissions: ['admin.cache.view', 'admin.cache.manage'],
  tags: ['admin', 'cache', 'performance', 'monitoring'],
  version: '1.0.0',
  status: 'active',
  features: [
    'Dashboard statistiques temps reel',
    'Gestion des regions de cache',
    'Invalidation par cle/pattern/tag/entite',
    'Prechargement automatique',
    'Alertes et monitoring',
    'Journal d\'audit',
    'Configuration multi-niveau',
  ],
  dependencies: [],
  tier: 'admin',
} as const;

export type ModuleMeta = typeof moduleMeta;
export const cacheMeta = moduleMeta;
export default moduleMeta;
