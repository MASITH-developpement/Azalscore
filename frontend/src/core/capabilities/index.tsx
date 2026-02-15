/**
 * AZALSCORE UI Engine - Module Capabilities
 * Gestion des capacités utilisateur (RBAC/ABAC)
 * L'UI affiche/masque selon les capacités - AUCUNE décision métier
 */

import React from 'react';
import { create } from 'zustand';
import { api } from '@core/api-client';
import type { Capability, CapabilitiesState } from '@/types';
import { LoadingState } from '../../ui-engine/components/StateViews';

// ============================================================
// TYPES LOCAUX
// ============================================================

// Status d'initialisation explicite
export type CapabilitiesStatus = 'idle' | 'loading' | 'ready' | 'error';

interface CapabilitiesStore extends CapabilitiesState {
  status: CapabilitiesStatus;
  loadCapabilities: () => Promise<void>;
  clearCapabilities: () => void;
  refreshCapabilities: () => Promise<void>;
  setStatus: (status: CapabilitiesStatus) => void;
}

interface CapabilitiesResponse {
  capabilities: string[];
  details?: Capability[];
}

// ============================================================
// CAPACITÉS SENSIBLES (UI AWARENESS ONLY)
// ============================================================

const SENSITIVE_CAPABILITIES = [
  'admin.root.break_glass',
  'admin.users.delete',
  'admin.tenants.delete',
  'accounting.journal.delete',
  'treasury.transfer.execute',
] as const;

// ============================================================
// STORE CAPABILITIES (ZUSTAND)
// ============================================================

export const useCapabilitiesStore = create<CapabilitiesStore>((set, get) => ({
  capabilities: [],
  isLoading: false,
  status: 'idle' as CapabilitiesStatus,

  setStatus: (status: CapabilitiesStatus): void => {
    set({ status });
  },

  hasCapability: (cap: string): boolean => {
    return get().capabilities.includes(cap);
  },

  hasAnyCapability: (caps: string[]): boolean => {
    const current = get().capabilities;
    return caps.some((cap) => current.includes(cap));
  },

  hasAllCapabilities: (caps: string[]): boolean => {
    const current = get().capabilities;
    return caps.every((cap) => current.includes(cap));
  },

  loadCapabilities: async (): Promise<void> => {
    set({ isLoading: true, status: 'loading' });

    try {
      const response = await api.get<CapabilitiesResponse>('/v3/auth/capabilities');

      // Handle all possible response formats
      let capabilities: string[] = [];
      const r = response as any;

      // Format 1: { capabilities: [...] }
      if (r && Array.isArray(r.capabilities)) {
        capabilities = r.capabilities;
      }
      // Format 2: { data: { capabilities: [...] } }
      else if (r && r.data && Array.isArray(r.data.capabilities)) {
        capabilities = r.data.capabilities;
      }
      // Format 3: direct array
      else if (Array.isArray(r)) {
        capabilities = r;
      }


      set({
        capabilities,
        isLoading: false,
        status: 'ready',
      });
    } catch (error) {
      console.error('[Capabilities] Error loading capabilities:', error);

      // En mode démo, récupérer les capabilities depuis le module auth
      const { getDemoCapabilities } = await import('@core/auth');
      const demoCapabilities = getDemoCapabilities();
      if (demoCapabilities.length > 0) {
        set({ capabilities: demoCapabilities, isLoading: false, status: 'ready' });
      } else {
        set({ capabilities: [], isLoading: false, status: 'ready' });
      }
    }
  },

  clearCapabilities: (): void => {
    set({ capabilities: [], isLoading: false, status: 'idle' });
  },

  refreshCapabilities: async (): Promise<void> => {
    await get().loadCapabilities();
  },
}));

// Écouter l'événement de login démo pour charger les capabilities
if (typeof window !== 'undefined') {
  window.addEventListener('azals:demo:login', ((event: CustomEvent<{ capabilities: string[] }>) => {
    useCapabilitiesStore.setState({
      capabilities: event.detail.capabilities,
      isLoading: false,
      status: 'ready',
    });
  }) as EventListener);
}

// ============================================================
// HOOKS UTILITAIRES
// ============================================================

/**
 * Hook principal pour accéder aux capacités
 */
export const useCapabilities = () => {
  const store = useCapabilitiesStore();
  return {
    capabilities: store.capabilities,
    isLoading: store.isLoading,
    status: store.status,
    hasCapability: store.hasCapability,
    hasAnyCapability: store.hasAnyCapability,
    hasAllCapabilities: store.hasAllCapabilities,
    refresh: store.refreshCapabilities,
  };
};

export const useCapabilitiesStatus = (): CapabilitiesStatus => {
  return useCapabilitiesStore((state) => state.status);
};

export const useIsCapabilitiesReady = (): boolean => {
  return useCapabilitiesStore((state) => state.status === 'ready');
};

/**
 * Hook pour vérifier une capacité spécifique
 */
export const useHasCapability = (capability: string): boolean => {
  return useCapabilitiesStore((state) => state.capabilities.includes(capability));
};

/**
 * Hook pour vérifier plusieurs capacités (OR)
 */
export const useHasAnyCapability = (capabilities: string[]): boolean => {
  return useCapabilitiesStore((state) =>
    capabilities.some((cap) => state.capabilities.includes(cap))
  );
};

/**
 * Hook pour vérifier plusieurs capacités (AND)
 */
export const useHasAllCapabilities = (capabilities: string[]): boolean => {
  return useCapabilitiesStore((state) =>
    capabilities.every((cap) => state.capabilities.includes(cap))
  );
};

/**
 * Hook pour vérifier si l'utilisateur a une capacité sensible
 */
export const useHasSensitiveCapability = (): boolean => {
  return useCapabilitiesStore((state) =>
    SENSITIVE_CAPABILITIES.some((cap) => state.capabilities.includes(cap))
  );
};

/**
 * Hook spécifique pour break-glass
 */
export const useCanBreakGlass = (): boolean => {
  return useHasCapability('admin.root.break_glass');
};

// ============================================================
// COMPOSANT GUARD (CONDITIONAL RENDER)
// ============================================================

interface CapabilityGuardProps {
  capability?: string;
  capabilities?: string[];
  mode?: 'any' | 'all';
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const CapabilityGuard: React.FC<CapabilityGuardProps> = ({
  capability,
  capabilities,
  mode = 'any',
  children,
  fallback = null,
}) => {
  const store = useCapabilitiesStore();
  const status = store.status;

  // CRITICAL: Ne pas décider tant que les capabilities ne sont pas READY
  // Cela évite les redirections prématurées avant le chargement
  if (status !== 'ready') {
    return <LoadingState message="Verification des acces..." />;
  }

  let hasAccess = false;

  if (capability) {
    hasAccess = store.hasCapability(capability);
  } else if (capabilities) {
    hasAccess =
      mode === 'all'
        ? store.hasAllCapabilities(capabilities)
        : store.hasAnyCapability(capabilities);
  } else {
    hasAccess = true;
  }

  return hasAccess ? <>{children}</> : <>{fallback}</>;
};

// ============================================================
// UTILITAIRES
// ============================================================

/**
 * Vérifie si une capacité est sensible
 */
export const isSensitiveCapability = (capability: string): boolean => {
  return SENSITIVE_CAPABILITIES.includes(capability as typeof SENSITIVE_CAPABILITIES[number]);
};

/**
 * Filtre les items selon les capacités
 */
export const filterByCapability = <T extends { capability?: string }>(
  items: T[],
  capabilities: string[]
): T[] => {
  return items.filter((item) => {
    if (!item.capability) return true;
    return capabilities.includes(item.capability);
  });
};

// ============================================================
// LISTENER ÉVÉNEMENT LOGOUT
// ============================================================

if (typeof window !== 'undefined') {
  window.addEventListener('azals:auth:logout', () => {
    useCapabilitiesStore.getState().clearCapabilities();
  });
}
