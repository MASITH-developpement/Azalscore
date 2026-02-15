/**
 * AZALSCORE - Modules (DEPRECATED)
 * =================================
 * CE FICHIER EST DEPRECIE.
 *
 * La source de verite est maintenant: GET /api/v3/admin/modules/available
 *
 * Ce fichier reste pour compatibilite mais ne doit plus etre modifie.
 * Pour ajouter un module, modifier: app/core/modules_registry.py
 */

export interface AvailableModule {
  code: string;
  name: string;
  label?: string; // alias pour name
  description: string;
  category: string;
  icon?: string;
  route?: string;
  enabled_by_default?: boolean;
}

// FALLBACK - utilise uniquement si l'API n'est pas disponible
export const AVAILABLE_MODULES: AvailableModule[] = [];

// Hook pour charger les modules depuis l'API
export const MODULES_API_ENDPOINT = '/api/v3/admin/modules/available';
