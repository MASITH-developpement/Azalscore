/**
 * AZALSCORE UI Engine - Module Capabilities
 * Gestion des capacités utilisateur (RBAC/ABAC)
 * L'UI affiche/masque selon les capacités - AUCUNE décision métier
 */

import { create } from 'zustand';
import { api } from '@core/api-client';
import type { Capability, CapabilitiesState } from '@/types';

// ============================================================
// TYPES LOCAUX
// ============================================================

interface CapabilitiesStore extends CapabilitiesState {
  loadCapabilities: () => Promise<void>;
  clearCapabilities: () => void;
  refreshCapabilities: () => Promise<void>;
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
    set({ isLoading: true });

    try {
      const response = await api.get<CapabilitiesResponse>('/v1/auth/capabilities');
      set({
        capabilities: response.data.capabilities,
        isLoading: false,
      });
    } catch {
      set({ capabilities: [], isLoading: false });
    }
  },

  clearCapabilities: (): void => {
    set({ capabilities: [], isLoading: false });
  },

  refreshCapabilities: async (): Promise<void> => {
    await get().loadCapabilities();
  },
}));

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
    hasCapability: store.hasCapability,
    hasAnyCapability: store.hasAnyCapability,
    hasAllCapabilities: store.hasAllCapabilities,
    refresh: store.refreshCapabilities,
  };
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
