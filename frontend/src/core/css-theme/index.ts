/**
 * AZALSCORE - CSS Theme Manager
 * ==============================
 * Gestion du theme CSS personnalise par tenant.
 * Charge depuis l'API et applique les variables CSS en temps reel.
 */

import { api } from '@core/api-client';

export interface TenantCSS {
  tenant_id: string;
  variables: Record<string, string>;
  custom_css: string;
  updated_at?: string;
}

// Cache local pour éviter les requêtes répétées
let currentConfig: TenantCSS | null = null;

/**
 * Applique les variables CSS au document
 */
export const applyTenantCSS = (config: TenantCSS | null): void => {
  if (!config) return;

  const root = document.documentElement;

  // Appliquer les variables CSS
  if (config.variables) {
    Object.entries(config.variables).forEach(([name, value]) => {
      if (name.startsWith('--') && value) {
        root.style.setProperty(name, value);
      }
    });
  }

  // Appliquer le CSS personnalise (si present)
  let styleEl = document.getElementById('azals-tenant-custom-css');
  if (config.custom_css) {
    if (!styleEl) {
      styleEl = document.createElement('style');
      styleEl.id = 'azals-tenant-custom-css';
      document.head.appendChild(styleEl);
    }
    styleEl.textContent = config.custom_css;
  } else if (styleEl) {
    // Supprimer le style si pas de CSS personnalisé
    styleEl.remove();
  }

  currentConfig = config;
};

/**
 * Réinitialise le CSS aux valeurs par défaut
 */
export const resetTenantCSS = (): void => {
  const root = document.documentElement;

  // Supprimer toutes les propriétés personnalisées
  if (currentConfig?.variables) {
    Object.keys(currentConfig.variables).forEach((name) => {
      root.style.removeProperty(name);
    });
  }

  // Supprimer le CSS personnalisé
  const styleEl = document.getElementById('azals-tenant-custom-css');
  if (styleEl) {
    styleEl.remove();
  }

  currentConfig = null;
};

/**
 * Charge le CSS depuis l'API et l'applique
 */
export const loadAndApplyTenantCSS = async (): Promise<void> => {
  try {
    const response = await api.get<TenantCSS>('/admin/tenant/css');
    if (response.data) {
      applyTenantCSS(response.data);
    }
  } catch {
    // Silencieux si pas de config ou erreur
  }
};

/**
 * Retourne la config CSS actuelle
 */
export const getCurrentCSS = (): TenantCSS | null => currentConfig;

/**
 * Initialise le theme CSS - écoute les événements de login
 */
export const initTenantTheme = (): void => {
  if (typeof window === 'undefined') return;

  // Charger le CSS après login
  window.addEventListener('azals:auth:login', () => {
    loadAndApplyTenantCSS();
  });

  // Réinitialiser après logout
  window.addEventListener('azals:auth:logout', () => {
    resetTenantCSS();
  });

  // Écouter les mises à jour de CSS (depuis le composant admin)
  window.addEventListener('azals:css:updated', ((event: CustomEvent<TenantCSS>) => {
    applyTenantCSS(event.detail);
  }) as EventListener);
};
