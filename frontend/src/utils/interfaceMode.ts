/**
 * AZALSCORE - Interface Mode Utility
 * Gestion du basculement entre mode AZALSCORE et mode ERP
 *
 * IMPORTANT: Cette version utilise l'attribut data-ui-mode pour le changement
 * de mode SANS rechargement de page. Le CSS gère les différences visuelles.
 *
 * @deprecated Préférer l'utilisation du hook useUIMode pour les composants React
 * @see useUIMode dans @ui/hooks/useUIMode
 */

const MODE_STORAGE_KEY = 'azalscore_interface_mode';
const UI_MODE_ATTRIBUTE = 'data-ui-mode';

export type InterfaceMode = 'azalscore' | 'erp';

/**
 * Appliquer le mode sur les éléments DOM
 */
const applyModeToDOM = (mode: InterfaceMode): void => {
  if (typeof document === 'undefined') return;

  document.documentElement.setAttribute(UI_MODE_ATTRIBUTE, mode);
  document.body.setAttribute(UI_MODE_ATTRIBUTE, mode);

  const appRoot = document.querySelector('[data-app-ready]');
  if (appRoot) {
    appRoot.setAttribute(UI_MODE_ATTRIBUTE, mode);
  }
};

/**
 * Récupérer le mode actuel depuis localStorage
 */
export const getCurrentMode = (): InterfaceMode => {
  if (typeof window === 'undefined') return 'azalscore';
  const stored = localStorage.getItem(MODE_STORAGE_KEY);
  return stored === 'erp' ? 'erp' : 'azalscore';
};

/**
 * Changer le mode d'interface SANS recharger la page
 * Le CSS gère les différences visuelles via data-ui-mode
 */
export const setInterfaceMode = (mode: InterfaceMode): void => {
  localStorage.setItem(MODE_STORAGE_KEY, mode);
  applyModeToDOM(mode);

  // Émettre un événement pour que les composants React puissent réagir
  window.dispatchEvent(
    new CustomEvent('uiModeChange', { detail: { mode } })
  );
};

/**
 * Basculer entre les modes
 */
export const toggleInterfaceMode = (): void => {
  const current = getCurrentMode();
  setInterfaceMode(current === 'azalscore' ? 'erp' : 'azalscore');
};

/**
 * Initialiser le mode au démarrage de l'application
 * Applique l'attribut data-ui-mode basé sur localStorage
 */
export const initInterfaceMode = (): InterfaceMode => {
  const mode = getCurrentMode();
  applyModeToDOM(mode);
  return mode;
};
