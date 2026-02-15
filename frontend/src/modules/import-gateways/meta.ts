/**
 * AZALSCORE - Module Passerelles d'Import - Metadata
 * ===================================================
 */

import { Download } from 'lucide-react';

export const meta = {
  id: 'import-gateways',
  name: 'Passerelles d\'Import',
  description: 'Gestion des connexions d\'import multi-sources (Odoo, etc.)',
  icon: Download,
  route: '/import-gateways',
  category: 'administration',
  order: 50,
  permissions: ['admin', 'manager'],
  keywords: ['import', 'odoo', 'sync', 'connexion', 'passerelle', 'gateway'],
};

export default meta;
