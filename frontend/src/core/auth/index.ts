/**
 * AZALSCORE UI Engine - Module Auth
 * Gestion de l'authentification et des sessions
 * AUCUNE logique métier - délégation au backend
 */

import { create } from 'zustand';
import { api, tokenManager, setTenantId, clearTenantId } from '@core/api-client';
import type { User, AuthTokens, AuthState, TypedAuthState } from '@/types';

// ============================================================
// MODE DÉMO (développement sans backend)
// ============================================================

// Mode démo activé UNIQUEMENT si variable explicite (pas par défaut en dev)
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

const DEMO_CAPABILITIES = {
  user: [
    'cockpit.view',
    'partners.view', 'partners.create', 'partners.edit',
    'invoicing.view', 'invoicing.create', 'invoicing.edit',
    'treasury.view', 'treasury.create',
    'accounting.view', 'accounting.journal.view',
    'purchases.view', 'purchases.create',
    'projects.view', 'projects.create',
    'interventions.view', 'interventions.create',
    'admin.view', 'admin.users.view',
  ],
  admin: [
    'cockpit.view',
    'partners.view', 'partners.create', 'partners.edit', 'partners.delete',
    'invoicing.view', 'invoicing.create', 'invoicing.edit', 'invoicing.delete',
    'treasury.view', 'treasury.create', 'treasury.transfer.execute',
    'accounting.view', 'accounting.journal.view', 'accounting.journal.delete',
    'purchases.view', 'purchases.create', 'purchases.edit',
    'projects.view', 'projects.create', 'projects.edit',
    'interventions.view', 'interventions.create', 'interventions.edit',
    'admin.view', 'admin.users.view', 'admin.users.create', 'admin.users.edit', 'admin.users.delete',
    'admin.tenants.view', 'admin.tenants.create', 'admin.tenants.delete',
    'admin.root.break_glass',
  ],
};

const DEMO_USERS: Record<string, { password: string; user: User; capabilities: string[] }> = {
  'demo@azalscore.local': {
    password: 'Demo123!',
    user: {
      id: 'demo-user-001',
      email: 'demo@azalscore.local',
      name: 'Utilisateur Démo',
      roles: ['admin'],
      capabilities: DEMO_CAPABILITIES.user,
      tenant_id: 'demo-tenant',
      is_active: true,
      requires_2fa: false,
    },
    capabilities: DEMO_CAPABILITIES.user,
  },
  'admin@azalscore.local': {
    password: 'Admin123!',
    user: {
      id: 'admin-user-001',
      email: 'admin@azalscore.local',
      name: 'Administrateur Root',
      roles: ['superadmin'],
      capabilities: DEMO_CAPABILITIES.admin,
      tenant_id: 'demo-tenant',
      is_active: true,
      requires_2fa: false,
    },
    capabilities: DEMO_CAPABILITIES.admin,
  },
};

const generateDemoTokens = (): AuthTokens => ({
  access_token: 'demo-access-token-' + Date.now(),
  refresh_token: 'demo-refresh-token-' + Date.now(),
  token_type: 'Bearer',
  expires_in: 3600,
});

// Variable pour stocker les capabilities de l'utilisateur démo courant
let currentDemoCapabilities: string[] = [];

export const getDemoCapabilities = (): string[] => currentDemoCapabilities;

// ============================================================
// TYPES LOCAUX
// ============================================================

interface LoginCredentials {
  email: string;
  password: string;
  totp_code?: string;
}

interface LoginResponse {
  user: User;
  tokens: AuthTokens;
  requires_2fa?: boolean;
  tenant_id: string;
}

// Status d'initialisation explicite
export type AuthStatus = 'idle' | 'loading' | 'ready' | 'error';

interface AuthStore extends AuthState {
  status: AuthStatus;
  login: (credentials: LoginCredentials) => Promise<LoginResponse>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  verify2FA: (code: string) => Promise<void>;
  setUser: (user: User) => void;
  clearAuth: () => void;
  setStatus: (status: AuthStatus) => void;
}

// ============================================================
// STORE AUTH (ZUSTAND)
// ============================================================

export const useAuthStore = create<AuthStore>((set, _get) => ({
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  status: 'idle' as AuthStatus,

  setStatus: (status: AuthStatus): void => {
    set({ status });
  },

  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    set({ isLoading: true, error: null });

    // Mode démo - vérifier d'abord les credentials démo
    if (DEMO_MODE) {
      const demoUser = DEMO_USERS[credentials.email.toLowerCase()];
      if (demoUser && demoUser.password === credentials.password) {
        const tokens = generateDemoTokens();
        const tenant_id = demoUser.user.tenant_id;

        tokenManager.setTokens(tokens.access_token, tokens.refresh_token);
        setTenantId(tenant_id);
        // Stocker l'email pour pouvoir récupérer l'utilisateur au refresh
        sessionStorage.setItem('azals_demo_email', credentials.email.toLowerCase());
        currentDemoCapabilities = demoUser.capabilities;

        // Charger les capabilities directement dans le store (évite les problèmes d'événements)
        const { useCapabilitiesStore } = await import('@core/capabilities');
        useCapabilitiesStore.setState({
          capabilities: demoUser.capabilities,
          isLoading: false,
          status: 'ready',
        });

        set({
          user: demoUser.user,
          tokens,
          isAuthenticated: true,
          isLoading: false,
          error: null,
          status: 'ready', // CRITICAL: Marquer auth comme READY après login démo
        });

        // Émettre l'événement de login pour démarrer le polling des capabilities
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('azals:auth:login'));
        }

        return {
          user: demoUser.user,
          tokens,
          tenant_id,
        };
      }
    }

    try {
      const response = await api.post<LoginResponse>('/auth/login', credentials, {
        skipAuth: true,
      });

      // api.post retourne deja response.data, donc response contient directement les donnees
      const loginData = response as unknown as LoginResponse;
      const { user, tokens, tenant_id } = loginData;

      // Stockage des tokens
      tokenManager.setTokens(tokens.access_token, tokens.refresh_token);
      setTenantId(tenant_id);

      set({
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        status: 'ready', // Marquer auth comme READY après login réussi
      });

      // Émettre l'événement de login pour démarrer le polling des capabilities
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('azals:auth:login'));
      }

      return loginData;
    } catch (error) {
      // En mode démo, afficher un message plus clair
      if (DEMO_MODE) {
        set({ isLoading: false, error: 'Identifiants invalides. Utilisez demo@azalscore.local / Demo123! ou admin@azalscore.local / Admin123!' });
        throw new Error('Identifiants démo invalides');
      }
      const message = error instanceof Error ? error.message : 'Échec de connexion';
      set({ isLoading: false, error: message });
      throw error;
    }
  },

  logout: async (): Promise<void> => {
    try {
      await api.post('/auth/logout', {});
    } catch {
      // Ignorer les erreurs de logout
    } finally {
      tokenManager.clearTokens();
      clearTenantId();
      set({
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
      // Émettre l'événement de logout pour arrêter le polling
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('azals:auth:logout'));
      }
    }
  },

  refreshUser: async (): Promise<void> => {
    set({ status: 'loading', isLoading: true });

    const token = tokenManager.getAccessToken();
    if (!token) {
      set({ isLoading: false, isAuthenticated: false, status: 'ready' });
      return;
    }

    // En mode démo, si on a un token démo valide, utiliser les données cachées
    if (DEMO_MODE && token.startsWith('demo-access-token-')) {
      // Chercher l'utilisateur démo correspondant au token stocké
      const storedEmail = sessionStorage.getItem('azals_demo_email');
      const demoUserData = storedEmail ? DEMO_USERS[storedEmail.toLowerCase()] : null;

      if (demoUserData) {
        currentDemoCapabilities = demoUserData.capabilities;
        // Charger les capabilities directement dans le store
        const { useCapabilitiesStore } = await import('@core/capabilities');
        useCapabilitiesStore.setState({
          capabilities: demoUserData.capabilities,
          isLoading: false,
          status: 'ready',
        });
        set({
          user: demoUserData.user,
          isAuthenticated: true,
          isLoading: false,
          error: null,
          status: 'ready',
        });
        return;
      }
      // Token démo mais pas d'email stocké - session invalide
      tokenManager.clearTokens();
      sessionStorage.removeItem('azals_demo_email');
      set({ isLoading: false, isAuthenticated: false, status: 'ready' });
      return;
    }

    try {
      const response = await api.get<User>('/auth/me');
      set({
        user: response.data,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        status: 'ready',
      });
    } catch {
      tokenManager.clearTokens();
      clearTenantId();
      set({
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        status: 'ready',
      });
    }
  },

  verify2FA: async (code: string): Promise<void> => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.post<LoginResponse>('/auth/verify-2fa', { totp_code: code });
      const { user, tokens, tenant_id } = response.data;

      tokenManager.setTokens(tokens.access_token, tokens.refresh_token);
      setTenantId(tenant_id);

      set({
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Code 2FA invalide';
      set({ isLoading: false, error: message });
      throw error;
    }
  },

  setUser: (user: User): void => {
    set({ user, isAuthenticated: true });
  },

  clearAuth: (): void => {
    tokenManager.clearTokens();
    clearTenantId();
    sessionStorage.removeItem('azals_demo_email');
    currentDemoCapabilities = [];
    set({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      status: 'ready', // Explicite : ready + !isAuthenticated = unauthenticated
    });
  },
}));

// ============================================================
// HOOKS UTILITAIRES
// ============================================================

export const useAuth = () => {
  const store = useAuthStore();
  return {
    user: store.user,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
    status: store.status,
    login: store.login,
    logout: store.logout,
    refreshUser: store.refreshUser,
    verify2FA: store.verify2FA,
  };
};

export const useAuthStatus = (): AuthStatus => {
  return useAuthStore((state) => state.status);
};

export const useIsAuthReady = (): boolean => {
  return useAuthStore((state) => state.status === 'ready');
};

export const useUser = (): User | null => {
  return useAuthStore((state) => state.user);
};

export const useIsAuthenticated = (): boolean => {
  return useAuthStore((state) => state.isAuthenticated);
};

// ============================================================
// HOOK TYPE-SAFE — DISCRIMINATED UNION
// ============================================================

/**
 * Hook type-safe qui derive un TypedAuthState du store existant.
 * Le discriminant 'authenticated' garantit que user est non-null.
 *
 * Usage:
 * const auth = useTypedAuth();
 * if (auth.status === 'authenticated') {
 *   auth.user.email; // OK — garanti non-null par le discriminant
 * }
 */
export const useTypedAuth = (): TypedAuthState => {
  return useAuthStore((state) => {
    if (state.status === 'idle') return { status: 'idle' as const };
    if (state.status === 'loading' || state.isLoading) return { status: 'loading' as const };
    if (state.error) return { status: 'error' as const, error: state.error };
    if (state.isAuthenticated && state.user) {
      return {
        status: 'authenticated' as const,
        user: state.user,
        tenantId: state.user.tenant_id,
      };
    }
    return { status: 'unauthenticated' as const };
  });
};

// ============================================================
// LISTENER ÉVÉNEMENT LOGOUT FORCÉ
// ============================================================

if (typeof window !== 'undefined') {
  window.addEventListener('azals:auth:logout', () => {
    useAuthStore.getState().clearAuth();
  });
}

// ============================================================
// INITIALISATION
// ============================================================

export const initAuth = async (): Promise<void> => {
  await useAuthStore.getState().refreshUser();
};
