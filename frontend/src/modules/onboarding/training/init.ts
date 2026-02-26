/**
 * AZALSCORE - Initialisation des Modules de Formation
 * ====================================================
 * Ce fichier enregistre tous les modules de formation disponibles
 * Il doit etre importe une fois au demarrage de l'application
 */

import { registerTrainingModule } from './registry';

// ============================================================================
// ENREGISTREMENT DES MODULES DE FORMATION
// ============================================================================

/**
 * Initialiser tous les modules de formation
 * Cette fonction doit etre appelee une fois au demarrage
 */
export async function initializeTrainingModules(): Promise<void> {
  // Module CRM
  registerTrainingModule(
    'crm',
    async (language) => {
      const module = await import('@/modules/crm/training');
      return module.loadTrainingContent(language);
    },
    ['crm.view']
  );

  // Module Commercial
  registerTrainingModule(
    'commercial',
    async (language) => {
      const module = await import('@/modules/commercial/training');
      return module.loadTrainingContent(language);
    },
    ['commercial.view']
  );

  // Module Comptabilite
  registerTrainingModule(
    'accounting',
    async (language) => {
      const module = await import('@/modules/accounting/training');
      return module.loadTrainingContent(language);
    },
    ['accounting.view']
  );

  // Module Inventaire
  registerTrainingModule(
    'inventory',
    async (language) => {
      const module = await import('@/modules/inventory/training');
      return module.loadTrainingContent(language);
    },
    ['inventory.view']
  );

  // Module RH
  registerTrainingModule(
    'hr',
    async (language) => {
      const module = await import('@/modules/hr/training');
      return module.loadTrainingContent(language);
    },
    ['hr.view']
  );

  // Module Production
  registerTrainingModule(
    'production',
    async (language) => {
      const module = await import('@/modules/production/training');
      return module.loadTrainingContent(language);
    },
    ['production.view']
  );

  // Module Helpdesk
  registerTrainingModule(
    'helpdesk',
    async (language) => {
      const module = await import('@/modules/helpdesk/training');
      return module.loadTrainingContent(language);
    },
    ['helpdesk.view']
  );

  // Module Marceau (Agent IA)
  registerTrainingModule(
    'marceau',
    async (language) => {
      const module = await import('@/modules/marceau/training');
      return module.loadTrainingContent(language);
    },
    ['marceau.view']
  );

  console.log('[Training] Tous les modules de formation ont ete enregistres');
}

// ============================================================================
// LISTE DES MODULES DISPONIBLES (pour reference)
// ============================================================================

export const AVAILABLE_TRAINING_MODULES = [
  {
    id: 'crm',
    name: 'CRM - Gestion Relation Client',
    icon: 'Users',
    color: '#3B82F6',
    permissions: ['crm.view'],
  },
  {
    id: 'commercial',
    name: 'Commercial - Devis et Factures',
    icon: 'FileText',
    color: '#10B981',
    permissions: ['commercial.view'],
  },
  {
    id: 'accounting',
    name: 'Comptabilite',
    icon: 'Calculator',
    color: '#6366F1',
    permissions: ['accounting.view'],
  },
  {
    id: 'inventory',
    name: 'Inventaire et Stocks',
    icon: 'Package',
    color: '#F59E0B',
    permissions: ['inventory.view'],
  },
  {
    id: 'hr',
    name: 'Ressources Humaines',
    icon: 'Users',
    color: '#8B5CF6',
    permissions: ['hr.view'],
  },
  {
    id: 'production',
    name: 'Production',
    icon: 'Factory',
    color: '#F59E0B',
    permissions: ['production.view'],
  },
  {
    id: 'helpdesk',
    name: 'Support Client',
    icon: 'Headphones',
    color: '#06B6D4',
    permissions: ['helpdesk.view'],
  },
  {
    id: 'marceau',
    name: 'Marceau - Agent IA',
    icon: 'Bot',
    color: '#7C3AED',
    permissions: ['marceau.view'],
  },
] as const;

export type TrainingModuleId = typeof AVAILABLE_TRAINING_MODULES[number]['id'];
