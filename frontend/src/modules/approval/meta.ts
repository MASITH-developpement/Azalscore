/**
 * AZALSCORE Module - APPROVAL - Metadata
 * =======================================
 */

export const meta = {
  id: 'approval',
  name: 'Approbations',
  description: 'Workflows d\'approbation et validation',
  version: '1.0.0',
  category: 'workflow',
  icon: 'CheckSquare',
  color: '#10B981',

  routes: [
    { path: '/approval', label: 'Approbations', icon: 'CheckSquare' },
    { path: '/approval/pending', label: 'En attente', icon: 'Clock' },
    { path: '/approval/workflows', label: 'Workflows', icon: 'GitBranch', capability: 'approval:workflows:read' },
    { path: '/approval/history', label: 'Historique', icon: 'History' },
  ],

  capabilities: [
    'approval:read',
    'approval:approve',
    'approval:reject',
    'approval:delegate',
    'approval:workflows:read',
    'approval:workflows:write',
    'approval:workflows:delete',
  ],

  dependencies: [],
  status: 'active',
  certification: 'B',
};

export default meta;
