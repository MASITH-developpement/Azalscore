/**
 * AZALSCORE - Query Keys Utilities
 * =================================
 * Fonctions utilitaires pour les clés de requête React Query.
 *
 * PROBLEME: Les objets dans queryKey causent des cache miss car
 * React Query compare par référence, pas par valeur.
 *
 * SOLUTION: Sérialiser les objets en chaîne stable.
 */

/**
 * Sérialise un objet de filtres en chaîne stable pour les query keys.
 *
 * @example
 * // Au lieu de:
 * queryKey: ['products', filters]  // Cache miss si nouvelle référence
 *
 * // Utiliser:
 * queryKey: ['products', serializeFilters(filters)]  // Cache hit si mêmes valeurs
 */
export function serializeFilters(filters: Record<string, unknown> | undefined | null): string {
  if (!filters) return '';

  // Trier les clés pour garantir un ordre stable
  const sortedKeys = Object.keys(filters).sort();

  // Construire une chaîne avec seulement les valeurs non-null/undefined
  const parts: string[] = [];
  for (const key of sortedKeys) {
    const value = filters[key];
    if (value !== null && value !== undefined && value !== '') {
      parts.push(`${key}:${String(value)}`);
    }
  }

  return parts.join('|');
}

/**
 * Crée une clé de requête avec filtres sérialisés.
 *
 * @example
 * const filters = { status: 'active', page: 1 };
 * createQueryKey('products', 'list', filters);
 * // Returns: ['products', 'list', 'page:1|status:active']
 */
export function createQueryKey(
  module: string,
  action: string,
  filters?: Record<string, unknown> | null,
  ...extras: (string | number | null | undefined)[]
): (string | number)[] {
  const key: (string | number)[] = [module, action];

  // Ajouter les extras (page, pageSize, etc.)
  for (const extra of extras) {
    if (extra !== null && extra !== undefined) {
      key.push(extra);
    }
  }

  // Ajouter les filtres sérialisés
  const serialized = serializeFilters(filters as Record<string, unknown>);
  if (serialized) {
    key.push(serialized);
  }

  return key;
}

/**
 * Extrait les valeurs primitives d'un objet de filtres pour les query keys.
 * Alternative à serializeFilters pour garder des valeurs séparées.
 *
 * @example
 * const filters = { status: 'active', client_id: '123' };
 * queryKey: ['products', 'list', ...extractFilterValues(filters, ['status', 'client_id'])]
 * // Returns: ['products', 'list', 'active', '123']
 */
export function extractFilterValues(
  filters: Record<string, unknown> | undefined | null,
  keys: string[]
): (string | number | null)[] {
  if (!filters) {
    return keys.map(() => null);
  }

  return keys.map(key => {
    const value = filters[key];
    if (value === null || value === undefined || value === '') {
      return null;
    }
    return typeof value === 'number' ? value : String(value);
  });
}
