/**
 * AZALSCORE UI Engine - useUIMode Hook
 * Gestion du mode UI (AZALSCORE / ERP) sans rechargement de page
 *
 * Le changement de mode se fait via l'attribut data-ui-mode sur l'élément racine,
 * permettant au CSS de gérer les différences visuelles.
 */

import { useState, useEffect, useCallback } from 'react';

export type UIMode = 'azalscore' | 'erp';

const MODE_STORAGE_KEY = 'azalscore_interface_mode';
const UI_MODE_ATTRIBUTE = 'data-ui-mode';

/**
 * Récupérer le mode actuel depuis localStorage
 */
const getStoredMode = (): UIMode => {
  if (typeof window === 'undefined') return 'azalscore';
  const stored = localStorage.getItem(MODE_STORAGE_KEY);
  return stored === 'erp' ? 'erp' : 'azalscore';
};

/**
 * Appliquer le mode sur l'élément racine du DOM
 */
const applyModeToDOM = (mode: UIMode): void => {
  if (typeof document === 'undefined') return;

  // Appliquer sur l'élément html pour être sûr que tout le CSS fonctionne
  document.documentElement.setAttribute(UI_MODE_ATTRIBUTE, mode);

  // Également sur body pour compatibilité
  document.body.setAttribute(UI_MODE_ATTRIBUTE, mode);

  // Appliquer sur l'élément racine de l'app si présent
  const appRoot = document.querySelector('[data-app-ready]');
  if (appRoot) {
    appRoot.setAttribute(UI_MODE_ATTRIBUTE, mode);
  }
};

/**
 * Hook pour gérer le mode UI (AZALSCORE / ERP)
 *
 * Fournit:
 * - mode: Le mode actuel ('azalscore' | 'erp')
 * - setMode: Fonction pour changer de mode (sans reload)
 * - toggleMode: Fonction pour basculer entre les modes
 * - isAzalscore: Boolean true si mode AZALSCORE
 * - isERP: Boolean true si mode ERP
 *
 * @example
 * ```tsx
 * const { mode, toggleMode, isAzalscore } = useUIMode();
 *
 * return (
 *   <button onClick={toggleMode}>
 *     Mode: {mode}
 *   </button>
 * );
 * ```
 */
export const useUIMode = () => {
  const [mode, setModeState] = useState<UIMode>(getStoredMode);

  // Initialiser le mode au montage
  useEffect(() => {
    const initialMode = getStoredMode();
    setModeState(initialMode);
    applyModeToDOM(initialMode);
  }, []);

  // Écouter les changements de localStorage (pour synchroniser entre onglets)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === MODE_STORAGE_KEY) {
        const newMode: UIMode = e.newValue === 'erp' ? 'erp' : 'azalscore';
        setModeState(newMode);
        applyModeToDOM(newMode);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  /**
   * Changer le mode UI sans rechargement de page
   */
  const setMode = useCallback((newMode: UIMode) => {
    localStorage.setItem(MODE_STORAGE_KEY, newMode);
    setModeState(newMode);
    applyModeToDOM(newMode);

    // Émettre un événement custom pour que d'autres composants puissent réagir
    window.dispatchEvent(
      new CustomEvent('uiModeChange', { detail: { mode: newMode } })
    );
  }, []);

  /**
   * Basculer entre les modes
   */
  const toggleMode = useCallback(() => {
    const newMode = mode === 'azalscore' ? 'erp' : 'azalscore';
    setMode(newMode);
  }, [mode, setMode]);

  return {
    mode,
    setMode,
    toggleMode,
    isAzalscore: mode === 'azalscore',
    isERP: mode === 'erp',
  };
};

/**
 * Initialiser le mode UI au démarrage de l'application
 * À appeler une fois dans App.tsx ou au plus haut niveau
 */
export const initUIMode = (): UIMode => {
  const mode = getStoredMode();
  applyModeToDOM(mode);
  return mode;
};

/**
 * Récupérer le mode actuel sans hook (pour usage en dehors de React)
 */
export const getCurrentUIMode = (): UIMode => getStoredMode();

/**
 * Définir le mode UI sans hook (pour usage en dehors de React)
 */
export const setUIMode = (mode: UIMode): void => {
  localStorage.setItem(MODE_STORAGE_KEY, mode);
  applyModeToDOM(mode);
  window.dispatchEvent(
    new CustomEvent('uiModeChange', { detail: { mode } })
  );
};

export default useUIMode;
