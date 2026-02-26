/**
 * AZALSCORE - Context de Gamification
 * ====================================
 * Fournit l'état de gamification à tous les composants enfants
 */

import React, { createContext, useContext } from 'react';
import { useGamificationState, type GamificationState } from './useGamification';

// ============================================================================
// CONTEXT
// ============================================================================

const GamificationContext = createContext<GamificationState | null>(null);

// ============================================================================
// PROVIDER
// ============================================================================

interface GamificationProviderProps {
  children: React.ReactNode;
}

/**
 * Provider qui enveloppe l'application pour fournir l'état de gamification
 */
export function GamificationProvider({ children }: GamificationProviderProps) {
  const gamification = useGamificationState();

  return (
    <GamificationContext.Provider value={gamification}>
      {children}
    </GamificationContext.Provider>
  );
}

// ============================================================================
// HOOK
// ============================================================================

/**
 * Hook pour accéder à l'état de gamification
 * @throws Error si utilisé en dehors du GamificationProvider
 */
export function useGamification(): GamificationState {
  const context = useContext(GamificationContext);

  if (!context) {
    // Fallback pour utilisation sans Provider (mode standalone)
    // eslint-disable-next-line react-hooks/rules-of-hooks
    return useGamificationState();
  }

  return context;
}

/**
 * Hook optionnel qui retourne null si pas de provider
 */
export function useGamificationOptional(): GamificationState | null {
  return useContext(GamificationContext);
}
