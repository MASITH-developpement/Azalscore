/**
 * AZALSCORE - QueryClient Singleton
 * ==================================
 * Instance unique de React Query pour toute l'application.
 *
 * IMPORTANT: Importer ce fichier au lieu de créer de nouvelles instances.
 * Cela garantit un cache partagé et un comportement cohérent.
 */

import { QueryClient } from '@tanstack/react-query';

/**
 * Configuration par défaut des queries.
 *
 * - staleTime: 5 minutes (données considérées fraîches)
 * - retry: 1 seul retry en cas d'échec
 * - refetchOnWindowFocus: désactivé (évite les refetch intempestifs)
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 minutes
      retry: (failureCount, error) => {
        // Ne pas retry les erreurs d'auth
        if (error instanceof Error &&
            (error.message.includes('AUTH_NOT_READY') ||
             error.message.includes('401') ||
             error.message.includes('403'))) {
          return false;
        }
        return failureCount < 1;
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});

export default queryClient;
