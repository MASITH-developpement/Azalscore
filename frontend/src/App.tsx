/**
 * AZALSCORE UI Engine - Application Root
 * Point d'entrée principal de l'application React
 *
 * INITIALISATION DÉTERMINISTE:
 * - L'application ne se rend pas tant que auth ET capabilities ne sont pas READY
 * - Un indicateur DOM data-app-ready="true" signale que l'app est prête
 * - Aucun composant métier n'est monté avant l'état READY
 */

import React, { useEffect, useState, useCallback } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppRouter } from '@routing/index';
import { useAuthStore, type AuthStatus } from '@core/auth';
import { useCapabilitiesStore, type CapabilitiesStatus } from '@core/capabilities';
import { initAuditUI } from '@core/audit-ui';
import { initializeStores, useUIStore } from '@ui/states';
import { initGuardianErrorHandlers } from '@core/guardian/incident-store';
import { initInterfaceMode } from './utils/interfaceMode';
import { WebsiteTracker } from './components/WebsiteTracker';
import { StructuredData } from './components/StructuredData';
import './styles/main.css';

// ============================================================
// QUERY CLIENT CONFIGURATION
// ============================================================

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

// ============================================================
// APP READY STATUS
// ============================================================

type AppReadyStatus = 'loading' | 'ready' | 'error';

interface AppReadyState {
  status: AppReadyStatus;
  authStatus: AuthStatus;
  capabilitiesStatus: CapabilitiesStatus;
  error: string | null;
}

// ============================================================
// APP INITIALIZER - DETERMINISTIC INITIALIZATION
// ============================================================

const AppInitializer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [appState, setAppState] = useState<AppReadyState>({
    status: 'loading',
    authStatus: 'idle',
    capabilitiesStatus: 'idle',
    error: null,
  });

  // Zustand stores
  const authStatus = useAuthStore((state) => state.status);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const refreshUser = useAuthStore((state) => state.refreshUser);

  const capabilitiesStatus = useCapabilitiesStore((state) => state.status);
  const loadCapabilities = useCapabilitiesStore((state) => state.loadCapabilities);
  const setCapabilitiesStatus = useCapabilitiesStore((state) => state.setStatus);

  const setIsMobile = useUIStore((state) => state.setIsMobile);

  // Determine if app is ready
  const computeReadyStatus = useCallback((): AppReadyStatus => {
    // Auth must be ready
    if (authStatus !== 'ready') return 'loading';

    // If authenticated, capabilities must also be ready
    if (isAuthenticated && capabilitiesStatus !== 'ready') return 'loading';

    // If not authenticated, we're ready (capabilities not needed)
    if (!isAuthenticated) {
      // Set capabilities to ready since we don't need them
      if (capabilitiesStatus !== 'ready') {
        setCapabilitiesStatus('ready');
      }
      return 'ready';
    }

    return 'ready';
  }, [authStatus, isAuthenticated, capabilitiesStatus, setCapabilitiesStatus]);

  // Initialize on mount - STRICT SEQUENCE
  useEffect(() => {
    let mounted = true;

    const initialize = async () => {
      try {
        // 0. Initialize UI mode (data-ui-mode attribute) - FIRST
        initInterfaceMode();

        // 1. Initialize audit system (fire and forget)
        initAuditUI();

        // 1bis. Initialize GUARDIAN error handlers
        initGuardianErrorHandlers();

        // 2. Setup mobile detection
        const checkMobile = () => setIsMobile(window.innerWidth < 768);
        checkMobile();
        window.addEventListener('resize', checkMobile);

        // 3. SEQUENCE CRITIQUE: Auth d'abord
        await refreshUser();

        // 4. Si authentifié après refresh, charger les capabilities
        // Note: refreshUser() met à jour le store, on vérifie directement
        const currentAuthState = useAuthStore.getState();
        if (currentAuthState.isAuthenticated) {
          // NE PAS recharger les capabilities si elles sont déjà READY (mode démo)
          const currentCapStatus = useCapabilitiesStore.getState().status;
          if (currentCapStatus !== 'ready') {
            await loadCapabilities();
          }
          await initializeStores();
        }

        // Cleanup
        return () => {
          window.removeEventListener('resize', checkMobile);
        };
      } catch (err) {
        console.error('[AppInitializer] Initialization error:', err);
        if (mounted) {
          setAppState(prev => ({
            ...prev,
            status: 'error',
            error: 'Erreur lors de l\'initialisation de l\'application',
          }));
        }
      }
    };

    initialize();

    return () => {
      mounted = false;
    };
  }, []); // Only run once on mount

  // Update app state when auth/capabilities status changes
  useEffect(() => {
    const newStatus = computeReadyStatus();
    setAppState(prev => ({
      ...prev,
      status: newStatus,
      authStatus,
      capabilitiesStatus,
    }));
  }, [authStatus, capabilitiesStatus, computeReadyStatus]);

  // LOADING STATE - App not ready
  if (appState.status === 'loading') {
    return (
      <div className="azals-app-loading" data-app-ready="false">
        <div className="azals-app-loading__content">
          <div className="azals-app-loading__logo">AZALSCORE</div>
          <div className="azals-spinner azals-spinner--lg" />
          <p>Chargement de l'application...</p>
          <small className="azals-app-loading__status">
            Auth: {authStatus} | Capabilities: {capabilitiesStatus}
          </small>
        </div>
      </div>
    );
  }

  // ERROR STATE
  if (appState.status === 'error') {
    return (
      <div className="azals-app-error" data-app-ready="false" data-app-error="true">
        <div className="azals-app-error__content">
          <h1>Erreur</h1>
          <p>{appState.error}</p>
          <button onClick={() => window.location.reload()}>Recharger</button>
        </div>
      </div>
    );
  }

  // READY STATE - App can render
  return (
    <div data-app-ready="true" data-auth-status={authStatus} data-capabilities-status={capabilitiesStatus}>
      {children}
    </div>
  );
};

// ============================================================
// MAIN APP COMPONENT
// ============================================================

const App: React.FC = () => {
  return (
    <>
      <StructuredData />
      <WebsiteTracker />
      <QueryClientProvider client={queryClient}>
        <AppInitializer>
          <AppRouter />
        </AppInitializer>
      </QueryClientProvider>
    </>
  );
};

export default App;
