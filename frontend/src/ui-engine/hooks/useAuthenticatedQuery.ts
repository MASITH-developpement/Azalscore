/**
 * AZALSCORE UI Engine - useAuthenticatedQuery
 * Hook React Query qui attend l'authentification avant d'executer la requete.
 *
 * Drop-in replacement pour useQuery : meme API, meme retour.
 * Evite les erreurs AUTH_NOT_READY dans l'intercepteur Axios.
 *
 * Usage:
 * ```tsx
 * const { data, isLoading, error } = useAuthenticatedQuery({
 *   queryKey: ['partners', page],
 *   queryFn: () => api.get('/partners'),
 * });
 * ```
 */

import { useQuery, type UseQueryOptions, type UseQueryResult } from '@tanstack/react-query';
import { useAuthStore } from '@core/auth';

export interface AuthenticatedQueryOptions<T> extends Omit<UseQueryOptions<T>, 'enabled'> {
  /** Si true (defaut), la requete attend auth ready + authenticated.
   *  Si false, attend seulement auth ready (pour les requetes publiques). */
  requireAuth?: boolean;
  /** Condition supplementaire pour activer la requete. */
  enabled?: boolean;
}

export function useAuthenticatedQuery<T>(
  options: AuthenticatedQueryOptions<T>
): UseQueryResult<T> {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const authReady = useAuthStore((s) => s.status === 'ready');

  const { requireAuth = true, enabled, ...rest } = options;

  const effectiveEnabled = requireAuth
    ? authReady && isAuthenticated && (enabled !== false)
    : authReady && (enabled !== false);

  return useQuery<T>({
    ...rest,
    enabled: effectiveEnabled,
  } as UseQueryOptions<T>);
}
