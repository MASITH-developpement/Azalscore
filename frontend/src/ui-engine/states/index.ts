/**
 * AZALSCORE UI Engine - Global States
 * Gestion des états globaux de l'UI
 */

import { create } from 'zustand';
import type { ModuleInfo, Tenant } from '@/types';
import { api } from '@core/api-client';
import { logError } from '@core/error-handling';

// ============================================================
// UI GLOBAL STATE
// ============================================================

interface UIState {
  // Sidebar
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // Theme
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;

  // Mobile
  isMobile: boolean;
  setIsMobile: (isMobile: boolean) => void;

  // Loading states
  globalLoading: boolean;
  setGlobalLoading: (loading: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  theme: 'system',
  setTheme: (theme) => {
    set({ theme });
    // Apply theme to document
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('data-theme', theme);
    }
  },

  isMobile: false,
  setIsMobile: (isMobile) => set({ isMobile }),

  globalLoading: false,
  setGlobalLoading: (globalLoading) => set({ globalLoading }),
}));

// ============================================================
// MODULES STATE
// ============================================================

interface ModulesState {
  modules: ModuleInfo[];
  isLoading: boolean;
  error: string | null;
  loadModules: () => Promise<void>;
  isModuleActive: (moduleId: string) => boolean;
  isModuleAvailable: (moduleId: string) => boolean;
}

export const useModulesStore = create<ModulesState>((set, get) => ({
  modules: [],
  isLoading: false,
  error: null,

  loadModules: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<{ modules: ModuleInfo[] }>('/modules');
      set({ modules: response.data.modules, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load modules',
        isLoading: false,
      });
    }
  },

  isModuleActive: (moduleId: string) => {
    const module = get().modules.find((m) => m.id === moduleId);
    return module?.is_active ?? false;
  },

  isModuleAvailable: (moduleId: string) => {
    const module = get().modules.find((m) => m.id === moduleId);
    return module?.is_available ?? false;
  },
}));

// ============================================================
// TENANT STATE
// ============================================================

interface TenantState {
  tenant: Tenant | null;
  isLoading: boolean;
  error: string | null;
  loadTenant: () => Promise<void>;
  clearTenant: () => void;
}

export const useTenantStore = create<TenantState>((set) => ({
  tenant: null,
  isLoading: false,
  error: null,

  loadTenant: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.get<Tenant>('/tenant/current');
      set({ tenant: response.data, isLoading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load tenant',
        isLoading: false,
      });
    }
  },

  clearTenant: () => {
    set({ tenant: null, error: null });
  },
}));

// ============================================================
// NOTIFICATION STATE
// ============================================================

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  created_at: string;
  action_url?: string;
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  loadNotifications: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,

  loadNotifications: async () => {
    set({ isLoading: true });
    try {
      const response = await api.get<{ notifications: Notification[] }>('/notifications');
      const notifications = response.data.notifications;
      set({
        notifications,
        unreadCount: notifications.filter((n) => !n.read).length,
        isLoading: false,
      });
    } catch {
      set({ isLoading: false });
    }
  },

  markAsRead: async (id: string) => {
    try {
      await api.post(`/notifications/${id}/read`);
      set((state) => ({
        notifications: state.notifications.map((n) =>
          n.id === id ? { ...n, read: true } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }));
    } catch (error) {
      logError(error, 'UIStates.retryAction');
    }
  },

  markAllAsRead: async () => {
    try {
      await api.post('/notifications/read-all');
      set((state) => ({
        notifications: state.notifications.map((n) => ({ ...n, read: true })),
        unreadCount: 0,
      }));
    } catch (error) {
      logError(error, 'UIStates.retryAll');
    }
  },
}));

// ============================================================
// HOOKS
// ============================================================

export const useIsMobile = () => useUIStore((state) => state.isMobile);
export const useTheme = () => useUIStore((state) => state.theme);
export const useSidebarCollapsed = () => useUIStore((state) => state.sidebarCollapsed);
export const useGlobalLoading = () => useUIStore((state) => state.globalLoading);

export const useModules = () => {
  const store = useModulesStore();
  return {
    modules: store.modules,
    isLoading: store.isLoading,
    isModuleActive: store.isModuleActive,
    isModuleAvailable: store.isModuleAvailable,
    refresh: store.loadModules,
  };
};

export const useTenant = () => {
  const store = useTenantStore();
  return {
    tenant: store.tenant,
    isLoading: store.isLoading,
    refresh: store.loadTenant,
  };
};

export const useNotifications = () => {
  const store = useNotificationStore();
  return {
    notifications: store.notifications,
    unreadCount: store.unreadCount,
    isLoading: store.isLoading,
    markAsRead: store.markAsRead,
    markAllAsRead: store.markAllAsRead,
    refresh: store.loadNotifications,
  };
};

// ============================================================
// INITIALIZATION
// ============================================================

export const initializeStores = async () => {
  await Promise.all([
    useModulesStore.getState().loadModules(),
    useTenantStore.getState().loadTenant(),
    useNotificationStore.getState().loadNotifications(),
  ]);
};

// Listen for logout
if (typeof window !== 'undefined') {
  window.addEventListener('azals:auth:logout', () => {
    useTenantStore.getState().clearTenant();
  });
}
