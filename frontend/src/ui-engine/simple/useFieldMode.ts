/**
 * AZALSCORE - useFieldMode
 * ========================
 *
 * Hook universel qui détermine le mode d'un champ selon:
 * - Les permissions de l'utilisateur
 * - Le contexte (création/édition/lecture)
 *
 * Exemple d'utilisation:
 *   const mode = useFieldMode('projects', 'edit');
 *   // Retourne 'edit' si l'utilisateur a projects.edit
 *   // Retourne 'view' sinon
 */

import { useHasCapability, useHasAnyCapability } from '@core/capabilities';

export type FieldMode = 'view' | 'edit' | 'create';
export type ContextMode = 'view' | 'edit' | 'create';

/**
 * Détermine le mode d'un champ selon les permissions
 *
 * @param module - Le module (ex: 'projects', 'partners', 'invoicing')
 * @param context - Le contexte demandé ('view', 'edit', 'create')
 * @returns Le mode effectif selon les permissions
 */
export const useFieldMode = (module: string, context: ContextMode): FieldMode => {
  // Vérifier les capabilities du module
  const _canView = useHasCapability(`${module}.view`);
  const canEdit = useHasCapability(`${module}.edit`);
  const canCreate = useHasCapability(`${module}.create`);

  // Fallback: vérifier les capabilities génériques
  const canEditGeneric = useHasAnyCapability([`${module}.edit`, `${module}.write`, `${module}.manage`]);
  const canCreateGeneric = useHasAnyCapability([`${module}.create`, `${module}.write`, `${module}.manage`]);

  // Déterminer le mode effectif
  if (context === 'create') {
    return (canCreate || canCreateGeneric) ? 'create' : 'view';
  }

  if (context === 'edit') {
    return (canEdit || canEditGeneric) ? 'edit' : 'view';
  }

  return 'view';
};

/**
 * Hook pour vérifier les permissions d'un module
 */
export const useModulePermissions = (module: string) => {
  const canView = useHasAnyCapability([`${module}.view`, `${module}.read`, `${module}.*`]);
  const canEdit = useHasAnyCapability([`${module}.edit`, `${module}.write`, `${module}.manage`, `${module}.*`]);
  const canCreate = useHasAnyCapability([`${module}.create`, `${module}.write`, `${module}.manage`, `${module}.*`]);
  const canDelete = useHasAnyCapability([`${module}.delete`, `${module}.manage`, `${module}.*`]);

  return {
    canView,
    canEdit,
    canCreate,
    canDelete,
    // Helper pour déterminer le mode
    getMode: (context: ContextMode): FieldMode => {
      if (context === 'create') return canCreate ? 'create' : 'view';
      if (context === 'edit') return canEdit ? 'edit' : 'view';
      return 'view';
    },
  };
};

/**
 * Liste des modules et leurs capabilities standard
 * Utilisé pour l'interface d'administration
 */
export const MODULE_CAPABILITIES = {
  // Commercial
  projects: {
    name: 'Affaires',
    capabilities: ['view', 'create', 'edit', 'delete'],
  },
  partners: {
    name: 'Partenaires (CRM)',
    capabilities: ['view', 'create', 'edit', 'delete'],
  },
  invoicing: {
    name: 'Facturation',
    capabilities: ['view', 'create', 'edit', 'delete', 'validate', 'export'],
  },
  interventions: {
    name: 'Interventions',
    capabilities: ['view', 'create', 'edit', 'delete', 'validate'],
  },

  // Stock & Achats
  inventory: {
    name: 'Stock',
    capabilities: ['view', 'create', 'edit', 'delete', 'movements'],
  },
  purchases: {
    name: 'Achats',
    capabilities: ['view', 'create', 'edit', 'delete', 'validate'],
  },

  // Finance
  accounting: {
    name: 'Comptabilité',
    capabilities: ['view', 'create', 'edit', 'delete', 'validate', 'close'],
  },
  treasury: {
    name: 'Trésorerie',
    capabilities: ['view', 'create', 'edit', 'delete', 'transfer'],
  },

  // RH
  hr: {
    name: 'Ressources Humaines',
    capabilities: ['view', 'create', 'edit', 'delete', 'payroll'],
  },

  // Production
  production: {
    name: 'Production',
    capabilities: ['view', 'create', 'edit', 'delete'],
  },
  maintenance: {
    name: 'Maintenance',
    capabilities: ['view', 'create', 'edit', 'delete'],
  },
  quality: {
    name: 'Qualité',
    capabilities: ['view', 'create', 'edit', 'delete'],
  },

  // Commerce
  pos: {
    name: 'Point de Vente',
    capabilities: ['view', 'create', 'edit', 'delete', 'cashier'],
  },
  ecommerce: {
    name: 'E-commerce',
    capabilities: ['view', 'create', 'edit', 'delete'],
  },

  // Support
  helpdesk: {
    name: 'Support',
    capabilities: ['view', 'create', 'edit', 'delete', 'assign'],
  },

  // Admin
  admin: {
    name: 'Administration',
    capabilities: ['view', 'users', 'roles', 'settings', 'audit'],
  },
} as const;

export type ModuleKey = keyof typeof MODULE_CAPABILITIES;
