/**
 * AZALSCORE Module - BUDGET - Metadata
 * =====================================
 */

export const meta = {
  id: 'budget',
  name: 'Gestion Budgetaire',
  description: 'Budgets, controle et suivi',
  version: '1.0.0',
  category: 'finance',
  icon: 'Wallet',
  color: '#8B5CF6',

  routes: [
    { path: '/budget', label: 'Tableau de bord', icon: 'LayoutDashboard' },
    { path: '/budget/list', label: 'Budgets', icon: 'Wallet' },
    { path: '/budget/categories', label: 'Categories', icon: 'FolderTree' },
    { path: '/budget/variances', label: 'Ecarts', icon: 'TrendingUp' },
    { path: '/budget/alerts', label: 'Alertes', icon: 'AlertTriangle' },
  ],

  capabilities: [
    'budget:read',
    'budget:write',
    'budget:approve',
    'budget:control',
    'budget:categories:write',
    'budget:revisions:write',
    'budget:scenarios:write',
    'budget:forecasts:write',
    'budget:alerts:manage',
  ],

  dependencies: ['accounting'],
  status: 'active',
  certification: 'B',
};

export default meta;
