/**
 * AZALSCORE UI Engine - Application Root
 * Point d'entrée principal de l'application React
 *
 * VERSION SIMPLIFIÉE:
 * - L'application s'affiche immédiatement
 * - L'initialisation tourne en arrière-plan
 * - Les routes protégées redirigent vers login si non authentifié
 */

import React, { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppRouter } from '@routing/index';
import { useAuthStore } from '@core/auth';
import { useCapabilitiesStore } from '@core/capabilities';
import { initAuditUI } from '@core/audit-ui';
import { useUIStore } from '@ui/states';
import { initGuardianErrorHandlers } from '@core/guardian/incident-store';
import './styles/main.css';

// ============================================================
// QUERY CLIENT CONFIGURATION
// ============================================================

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      retryDelay: 1000,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});

// ============================================================
// APP INITIALIZER - NON-BLOCKING
// ============================================================

const AppInitializer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const refreshUser = useAuthStore((state) => state.refreshUser);
  const setAuthStatus = useAuthStore((state) => state.setStatus);
  const setCapabilitiesStatus = useCapabilitiesStore((state) => state.setStatus);
  const setIsMobile = useUIStore((state) => state.setIsMobile);

  // Initialize on mount - NON-BLOCKING
  useEffect(() => {
    const initialize = async () => {
      try {
        // 1. Initialize audit system (fire and forget)
        initAuditUI();

        // 2. Initialize GUARDIAN error handlers
        initGuardianErrorHandlers();

        // 3. Setup mobile detection
        const checkMobile = () => setIsMobile(window.innerWidth < 768);
        checkMobile();
        window.addEventListener('resize', checkMobile);

        // 4. Try to refresh user (non-blocking)
        try {
          await refreshUser();
        } catch {
          // Si refresh échoue, marquer auth comme ready (non authentifié)
          setAuthStatus('ready');
          setCapabilitiesStatus('ready');
        }

        return () => {
          window.removeEventListener('resize', checkMobile);
        };
      } catch (err) {
        console.error('[AppInitializer] Initialization error:', err);
        // Marquer comme ready même en cas d'erreur pour permettre l'affichage
        setAuthStatus('ready');
        setCapabilitiesStatus('ready');
      }
    };

    initialize();
  }, [refreshUser, setAuthStatus, setCapabilitiesStatus, setIsMobile]);

  // ALWAYS render children - no blocking
  return <>{children}</>;
};

// ============================================================
// MAIN APP COMPONENT
// ============================================================

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AppInitializer>
        <AppRouter />
      </AppInitializer>
    </QueryClientProvider>
  );
};

export default App;
