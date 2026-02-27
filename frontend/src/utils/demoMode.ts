/**
 * AZALSCORE - Mode Démonstration
 * ==============================
 *
 * Permet d'activer/désactiver les données de démonstration
 * pour tester l'interface sans backend.
 *
 * P0 SÉCURITÉ: Utilise sessionStorage (pas localStorage)
 * - sessionStorage est vidé à la fermeture du navigateur
 * - Cohérent avec le stockage des tokens (auth/index.ts)
 * - Moins vulnérable aux attaques XSS persistantes
 */

const DEMO_MODE_KEY = 'azals_demo_mode';

export const isDemoMode = (): boolean => {
  // P0 SÉCURITÉ: sessionStorage au lieu de localStorage
  return sessionStorage.getItem(DEMO_MODE_KEY) === 'true';
};

export const setDemoMode = (enabled: boolean): void => {
  // P0 SÉCURITÉ: sessionStorage au lieu de localStorage
  sessionStorage.setItem(DEMO_MODE_KEY, String(enabled));
  // Dispatch event pour que les composants puissent réagir
  window.dispatchEvent(new CustomEvent('azals:demoModeChanged', { detail: { enabled } }));
  // Reload pour appliquer le changement
  window.location.reload();
};

export const toggleDemoMode = (): boolean => {
  const newValue = !isDemoMode();
  setDemoMode(newValue);
  return newValue;
};

// Hook React pour écouter les changements
export const useDemoMode = (): boolean => {
  // Simple check - in a real implementation you'd use useState + useEffect
  return isDemoMode();
};
