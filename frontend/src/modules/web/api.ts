/**
 * AZALSCORE - Web API
 * ===================
 * API client pour le module Web/Configuration UI
 * Couvre: Themes, Widgets, Dashboards, Pages, Menu
 */

import { api } from '@/core/api-client';

// ============================================================================
// TYPES
// ============================================================================

export interface Theme {
  id: string;
  name: string;
  description?: string;
  is_default: boolean;
  is_active: boolean;
  primary_color: string;
  secondary_color: string;
  accent_color?: string;
  background_color?: string;
  text_color?: string;
  created_at: string;
  updated_at?: string;
}

export interface Widget {
  id: string;
  name: string;
  widget_type: string;
  config: Record<string, unknown>;
  is_active: boolean;
  position: number;
  created_at: string;
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  is_default: boolean;
  is_public: boolean;
  layout: string;
  widgets: string[];
  created_at: string;
  updated_at?: string;
}

export interface CustomPage {
  id: string;
  slug: string;
  title: string;
  content?: string;
  meta_title?: string;
  meta_description?: string;
  is_published: boolean;
  created_at: string;
  updated_at?: string;
}

export interface MenuItem {
  id: string;
  label: string;
  icon?: string;
  path?: string;
  parent_id?: string;
  position: number;
  is_visible: boolean;
  children?: MenuItem[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

// ============================================================================
// REQUEST TYPES
// ============================================================================

export interface ThemeCreate {
  name: string;
  description?: string;
  primary_color: string;
  secondary_color: string;
  accent_color?: string;
  background_color?: string;
  text_color?: string;
}

export interface WidgetCreate {
  name: string;
  widget_type: string;
  config?: Record<string, unknown>;
  position?: number;
}

export interface DashboardCreate {
  name: string;
  description?: string;
  layout?: string;
  is_public?: boolean;
  widgets?: string[];
}

export interface PageCreate {
  slug: string;
  title: string;
  content?: string;
  meta_title?: string;
  meta_description?: string;
  is_published?: boolean;
}

export interface MenuItemCreate {
  label: string;
  icon?: string;
  path?: string;
  parent_id?: string;
  position?: number;
  is_visible?: boolean;
}

// ============================================================================
// HELPERS
// ============================================================================

const BASE_PATH = '/web';

// ============================================================================
// API CLIENT
// ============================================================================

export const webApi = {
  // ==========================================================================
  // Themes
  // ==========================================================================

  /**
   * Liste les themes
   */
  listThemes: () =>
    api.get<PaginatedResponse<Theme>>(`${BASE_PATH}/themes`),

  /**
   * Recupere un theme par son ID
   */
  getTheme: (id: string) =>
    api.get<Theme>(`${BASE_PATH}/themes/${id}`),

  /**
   * Cree un nouveau theme
   */
  createTheme: (data: ThemeCreate) =>
    api.post<Theme>(`${BASE_PATH}/themes`, data),

  /**
   * Met a jour un theme
   */
  updateTheme: (id: string, data: Partial<ThemeCreate>) =>
    api.put<Theme>(`${BASE_PATH}/themes/${id}`, data),

  /**
   * Supprime un theme
   */
  deleteTheme: (id: string) =>
    api.delete(`${BASE_PATH}/themes/${id}`),

  /**
   * Definit le theme par defaut
   */
  setDefaultTheme: (id: string) =>
    api.post<Theme>(`${BASE_PATH}/themes/${id}/set-default`, {}),

  /**
   * Active/desactive un theme
   */
  toggleTheme: (id: string, isActive: boolean) =>
    api.patch<Theme>(`${BASE_PATH}/themes/${id}`, { is_active: isActive }),

  // ==========================================================================
  // Widgets
  // ==========================================================================

  /**
   * Liste les widgets
   */
  listWidgets: () =>
    api.get<PaginatedResponse<Widget>>(`${BASE_PATH}/widgets`),

  /**
   * Recupere un widget par son ID
   */
  getWidget: (id: string) =>
    api.get<Widget>(`${BASE_PATH}/widgets/${id}`),

  /**
   * Cree un nouveau widget
   */
  createWidget: (data: WidgetCreate) =>
    api.post<Widget>(`${BASE_PATH}/widgets`, data),

  /**
   * Met a jour un widget
   */
  updateWidget: (id: string, data: Partial<WidgetCreate>) =>
    api.put<Widget>(`${BASE_PATH}/widgets/${id}`, data),

  /**
   * Supprime un widget
   */
  deleteWidget: (id: string) =>
    api.delete(`${BASE_PATH}/widgets/${id}`),

  /**
   * Reordonne les widgets
   */
  reorderWidgets: (positions: Array<{ id: string; position: number }>) =>
    api.post(`${BASE_PATH}/widgets/reorder`, { positions }),

  // ==========================================================================
  // Dashboards
  // ==========================================================================

  /**
   * Liste les dashboards
   */
  listDashboards: () =>
    api.get<PaginatedResponse<Dashboard>>(`${BASE_PATH}/dashboards`),

  /**
   * Recupere un dashboard par son ID
   */
  getDashboard: (id: string) =>
    api.get<Dashboard>(`${BASE_PATH}/dashboards/${id}`),

  /**
   * Cree un nouveau dashboard
   */
  createDashboard: (data: DashboardCreate) =>
    api.post<Dashboard>(`${BASE_PATH}/dashboards`, data),

  /**
   * Met a jour un dashboard
   */
  updateDashboard: (id: string, data: Partial<DashboardCreate>) =>
    api.put<Dashboard>(`${BASE_PATH}/dashboards/${id}`, data),

  /**
   * Supprime un dashboard
   */
  deleteDashboard: (id: string) =>
    api.delete(`${BASE_PATH}/dashboards/${id}`),

  /**
   * Definit le dashboard par defaut
   */
  setDefaultDashboard: (id: string) =>
    api.post<Dashboard>(`${BASE_PATH}/dashboards/${id}/set-default`, {}),

  /**
   * Ajoute un widget au dashboard
   */
  addWidgetToDashboard: (dashboardId: string, widgetId: string) =>
    api.post<Dashboard>(`${BASE_PATH}/dashboards/${dashboardId}/widgets`, { widget_id: widgetId }),

  /**
   * Retire un widget du dashboard
   */
  removeWidgetFromDashboard: (dashboardId: string, widgetId: string) =>
    api.delete(`${BASE_PATH}/dashboards/${dashboardId}/widgets/${widgetId}`),

  // ==========================================================================
  // Pages
  // ==========================================================================

  /**
   * Liste les pages
   */
  listPages: () =>
    api.get<PaginatedResponse<CustomPage>>(`${BASE_PATH}/pages`),

  /**
   * Recupere une page par son ID
   */
  getPage: (id: string) =>
    api.get<CustomPage>(`${BASE_PATH}/pages/${id}`),

  /**
   * Recupere une page par son slug
   */
  getPageBySlug: (slug: string) =>
    api.get<CustomPage>(`${BASE_PATH}/pages/slug/${slug}`),

  /**
   * Cree une nouvelle page
   */
  createPage: (data: PageCreate) =>
    api.post<CustomPage>(`${BASE_PATH}/pages`, data),

  /**
   * Met a jour une page
   */
  updatePage: (id: string, data: Partial<PageCreate>) =>
    api.put<CustomPage>(`${BASE_PATH}/pages/${id}`, data),

  /**
   * Supprime une page
   */
  deletePage: (id: string) =>
    api.delete(`${BASE_PATH}/pages/${id}`),

  /**
   * Publie une page
   */
  publishPage: (id: string) =>
    api.post<CustomPage>(`${BASE_PATH}/pages/${id}/publish`, {}),

  /**
   * Depublie une page
   */
  unpublishPage: (id: string) =>
    api.post<CustomPage>(`${BASE_PATH}/pages/${id}/unpublish`, {}),

  // ==========================================================================
  // Menu
  // ==========================================================================

  /**
   * Liste les elements du menu
   */
  listMenuItems: () =>
    api.get<MenuItem[]>(`${BASE_PATH}/menu-items`),

  /**
   * Cree un element de menu
   */
  createMenuItem: (data: MenuItemCreate) =>
    api.post<MenuItem>(`${BASE_PATH}/menu-items`, data),

  /**
   * Met a jour un element de menu
   */
  updateMenuItem: (id: string, data: Partial<MenuItemCreate>) =>
    api.put<MenuItem>(`${BASE_PATH}/menu-items/${id}`, data),

  /**
   * Supprime un element de menu
   */
  deleteMenuItem: (id: string) =>
    api.delete(`${BASE_PATH}/menu-items/${id}`),

  /**
   * Reordonne le menu
   */
  reorderMenu: (positions: Array<{ id: string; position: number; parent_id?: string }>) =>
    api.post(`${BASE_PATH}/menu-items/reorder`, { positions }),
};

export default webApi;
