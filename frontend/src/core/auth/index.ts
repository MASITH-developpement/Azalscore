/**
 * AZALSCORE UI Engine - Module Auth
 * Gestion de l'authentification et des sessions
 * AUCUNE logique métier - délégation au backend
 */

import { create } from 'zustand';
import { api, tokenManager, setTenantId, clearTenantId } from '@core/api-client';
import type { User, AuthTokens, AuthState } from '@/types';

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

interface AuthStore extends AuthState {
  login: (credentials: LoginCredentials) => Promise<LoginResponse>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  verify2FA: (code: string) => Promise<void>;
  setUser: (user: User) => void;
  clearAuth: () => void;
}

// ============================================================
// STORE AUTH (ZUSTAND)
// ============================================================

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.post<LoginResponse>('/v1/auth/login', credentials, {
        skipAuth: true,
      });

      const { user, tokens, tenant_id } = response.data;

      // Stockage des tokens
      tokenManager.setTokens(tokens.access_token, tokens.refresh_token);
      setTenantId(tenant_id);

      set({
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      return response.data;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Échec de connexion';
      set({ isLoading: false, error: message });
      throw error;
    }
  },

  logout: async (): Promise<void> => {
    try {
      await api.post('/v1/auth/logout', {});
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
    }
  },

  refreshUser: async (): Promise<void> => {
    const token = tokenManager.getAccessToken();
    if (!token) {
      set({ isLoading: false, isAuthenticated: false });
      return;
    }

    set({ isLoading: true });

    try {
      const response = await api.get<User>('/v1/auth/me');
      set({
        user: response.data,
        isAuthenticated: true,
        isLoading: false,
        error: null,
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
      });
    }
  },

  verify2FA: async (code: string): Promise<void> => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.post<LoginResponse>('/v1/auth/verify-2fa', { totp_code: code });
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
    set({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
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
    login: store.login,
    logout: store.logout,
    refreshUser: store.refreshUser,
    verify2FA: store.verify2FA,
  };
};

export const useUser = (): User | null => {
  return useAuthStore((state) => state.user);
};

export const useIsAuthenticated = (): boolean => {
  return useAuthStore((state) => state.isAuthenticated);
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
