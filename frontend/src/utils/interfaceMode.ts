/**
 * AZALSCORE - Interface Mode Utility
 * Gestion du basculement entre mode AZALSCORE et mode ERP
 */

const MODE_STORAGE_KEY = 'azalscore_interface_mode';

export type InterfaceMode = 'azalscore' | 'erp';

/**
 * Récupérer le mode actuel depuis localStorage
 */
export const getCurrentMode = (): InterfaceMode => {
  if (typeof window === 'undefined') return 'azalscore';
  const stored = localStorage.getItem(MODE_STORAGE_KEY);
  return stored === 'erp' ? 'erp' : 'azalscore';
};

/**
 * Changer le mode d'interface et recharger la page
 */
export const setInterfaceMode = (mode: InterfaceMode): void => {
  localStorage.setItem(MODE_STORAGE_KEY, mode);
  window.location.reload();
};

/**
 * Basculer entre les modes
 */
export const toggleInterfaceMode = (): void => {
  const current = getCurrentMode();
  setInterfaceMode(current === 'azalscore' ? 'erp' : 'azalscore');
};
