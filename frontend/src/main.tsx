/**
 * AZALSCORE - Point d'entrée
 * ==========================
 *
 * Application unifiée avec deux modes d'interface :
 * - Mode AZALSCORE = interface simplifiée avec menu déroulant
 * - Mode ERP = interface complète avec sidebar multi-modules
 *
 * Le mode est stocké dans localStorage et peut être changé dynamiquement.
 * Les deux modes partagent le même code, seul le layout change.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';

// Application unifiée - un seul composant pour les deux modes
const AppComponent = React.lazy(() => import('./UnifiedApp'));

// ============================================================
// BRANDING
// ============================================================

document.title = 'AZALSCORE';

// ============================================================
// RENDER
// ============================================================

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <React.Suspense fallback={
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#f5f6f8',
        fontFamily: "'Inter', system-ui, sans-serif",
        color: '#6b7280'
      }}>
        Chargement...
      </div>
    }>
      <AppComponent />
    </React.Suspense>
  </React.StrictMode>
);

// ============================================================
// SERVICE WORKER REGISTRATION (PWA)
// ============================================================

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then((registration) => {
        console.log('SW registered:', registration.scope);
        // Check for updates every 60 seconds
        setInterval(() => registration.update(), 60 * 1000);
      })
      .catch((error) => {
        console.log('SW registration failed:', error);
      });
  });

  // When a new SW takes control, reload to get fresh assets
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    window.location.reload();
  });
}
