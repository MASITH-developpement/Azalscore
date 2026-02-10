/**
 * AZALSCORE - Module Template - Types
 * ====================================
 * Définitions TypeScript pour le module
 */

// ============================================================
// INTERFACES
// ============================================================

/**
 * Interface principale de l'entité
 */
export interface TemplateEntity {
  id: string;
  name: string;
  description?: string;
  status: TemplateStatus;
  createdAt: string;
  updatedAt: string;
}

/**
 * Données pour création/modification
 */
export interface TemplateFormData {
  name: string;
  description?: string;
  status: TemplateStatus;
}

// ============================================================
// ENUMS & TYPES
// ============================================================

/**
 * Statuts possibles
 */
export type TemplateStatus = 'active' | 'inactive' | 'pending';

/**
 * Modes de vue
 */
export type ViewMode = 'list' | 'detail' | 'create' | 'edit';

// ============================================================
// CONSTANTES
// ============================================================

/**
 * Options de statut pour les formulaires
 */
export const STATUS_OPTIONS = [
  { value: 'active', label: 'Actif' },
  { value: 'inactive', label: 'Inactif' },
  { value: 'pending', label: 'En attente' },
] as const;

/**
 * Configuration par défaut
 */
export const DEFAULT_TEMPLATE: Partial<TemplateFormData> = {
  name: '',
  description: '',
  status: 'pending',
};
