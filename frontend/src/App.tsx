/**
 * AZALSCORE UI Engine - Application Root
 * Point d'entrée principal de l'application React
 */

import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppRouter } from '@routing/index';
import { initAuth } from '@core/auth';
import { useCapabilitiesStore } from '@core/capabilities';
import { initAuditUI } from '@core/audit-ui';
import { initializeStores, useUIStore } from '@ui/states';
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
// APP INITIALIZER
// ============================================================

const AppInitializer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const loadCapabilities = useCapabilitiesStore((state) => state.loadCapabilities);
  const setIsMobile = useUIStore((state) => state.setIsMobile);

  useEffect(() => {
    const initialize = async () => {
      try {
        // Initialiser le système d'audit UI
        initAuditUI();

        // Vérifier l'authentification existante
        await initAuth();

        // Charger les capacités si authentifié
        const token = sessionStorage.getItem('azals_access_token');
        if (token) {
          await loadCapabilities();
          await initializeStores();
        }

        // Détecter le mode mobile
        const checkMobile = () => {
          setIsMobile(window.innerWidth < 768);
        };
        checkMobile();
        window.addEventListener('resize', checkMobile);

        setIsInitialized(true);
      } catch (err) {
        console.error('Initialization error:', err);
        setError('Erreur lors de l\'initialisation de l\'application');
        setIsInitialized(true); // Continue anyway to show login
      }
    };

    initialize();
  }, [loadCapabilities, setIsMobile]);

  if (!isInitialized) {
    return (
      <div className="azals-app-loading">
        <div className="azals-app-loading__content">
          <div className="azals-app-loading__logo">AZALSCORE</div>
          <div className="azals-spinner azals-spinner--lg" />
          <p>Chargement de l'application...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="azals-app-error">
        <div className="azals-app-error__content">
          <h1>Erreur</h1>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Recharger</button>
        </div>
      </div>
    );
  }

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
