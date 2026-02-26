/**
 * AZALSCORE - Integration Hub Meta
 * =================================
 * Metadonnees du module Integration Hub (GAP-086).
 */

import { Plug } from 'lucide-react';

export const moduleMeta = {
  id: 'integration',
  name: 'Hub d\'Integrations',
  description: 'Gestion centralisee des integrations tierces et connecteurs',
  icon: Plug,
  category: 'administration',
  path: '/admin/integration',
  permissions: ['admin.integration.view', 'admin.integration.manage'],
  tags: ['admin', 'integration', 'connecteurs', 'api', 'synchronisation'],
  version: '1.0.0',
  status: 'active',
  features: [
    'Dashboard KPIs et statistiques',
    'Catalogue de connecteurs',
    'Gestion des connexions actives',
    'Monitoring des synchronisations',
    'Resolution des conflits de donnees',
    'Configuration des webhooks',
    'Historique des executions',
  ],
  dependencies: [],
  tier: 'admin',
} as const;

export type ModuleMeta = typeof moduleMeta;
export const integrationMeta = moduleMeta;
export default moduleMeta;
