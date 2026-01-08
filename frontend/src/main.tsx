/**
 * AZALSCORE UI Engine - Entry Point
 * Point d'entrée de l'application
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { initializeBranding } from './core/branding';

// ============================================================
// BRANDING INITIALIZATION
// Applique le titre "Azalscore" au bootstrap
// ============================================================

initializeBranding();

// ============================================================
// RENDER APPLICATION
// ============================================================

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
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
      })
      .catch((error) => {
        console.log('SW registration failed:', error);
      });
  });
}
