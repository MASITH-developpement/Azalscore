/**
 * AZALSCORE - Web Configuration React Query Hooks
 * ================================================
 * Hooks pour le module Web / Site Configuration
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';

// ============================================================================
// TYPES
// ============================================================================

interface Theme {
  id: string;
  name: string;
  description?: string;
  is_default: boolean;
  is_active: boolean;
  primary_color: string;
  secondary_color: string;
  created_at: string;
}

interface Widget {
  id: string;
  name: string;
  widget_type: string;
  config: Record<string, unknown>;
  is_active: boolean;
  position: number;
}

interface Dashboard {
  id: string;
  name: string;
  description?: string;
  is_default: boolean;
  is_public: boolean;
  layout: string;
  widgets: string[];
}

interface CustomPage {
  id: string;
  slug: string;
  title: string;
  content?: string;
  is_published: boolean;
  created_at: string;
}

interface MenuItem {
  id: string;
  label: string;
  icon?: string;
  path?: string;
  parent_id?: string;
  position: number;
  is_visible: boolean;
}

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const webKeys = {
  all: ['web'] as const,
  themes: () => [...webKeys.all, 'themes'] as const,
  widgets: () => [...webKeys.all, 'widgets'] as const,
  dashboards: () => [...webKeys.all, 'dashboards'] as const,
  pages: () => [...webKeys.all, 'pages'] as const,
  menuItems: () => [...webKeys.all, 'menu-items'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

export const useThemes = () => {
  return useQuery({
    queryKey: webKeys.themes(),
    queryFn: () => api.get<{ items: Theme[] }>('/web/themes').then(r => r.data.items || []),
  });
};

export const useWidgets = () => {
  return useQuery({
    queryKey: webKeys.widgets(),
    queryFn: () => api.get<{ items: Widget[] }>('/web/widgets').then(r => r.data.items || []),
  });
};

export const useWebDashboards = () => {
  return useQuery({
    queryKey: webKeys.dashboards(),
    queryFn: () => api.get<{ items: Dashboard[] }>('/web/dashboards').then(r => r.data.items || []),
  });
};

export const usePages = () => {
  return useQuery({
    queryKey: webKeys.pages(),
    queryFn: () => api.get<{ items: CustomPage[] }>('/web/pages').then(r => r.data.items || []),
  });
};

export const useMenuItems = () => {
  return useQuery({
    queryKey: webKeys.menuItems(),
    queryFn: () => api.get<MenuItem[]>('/web/menu-items').then(r => r.data || []),
  });
};

// ============================================================================
// MUTATION HOOKS
// ============================================================================

export const useCreateTheme = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Theme>) => api.post('/web/themes', data).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: webKeys.themes() });
    },
  });
};

export const useCreatePage = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<CustomPage>) => api.post('/web/pages', data).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: webKeys.pages() });
    },
  });
};

export const useDeletePage = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/web/pages/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: webKeys.pages() });
    },
  });
};

// Re-export types
export type { Theme, Widget, Dashboard, CustomPage, MenuItem };
