/**
 * AZALSCORE Module - Dashboards API
 * Client API pour le module de tableaux de bord
 */

import { api } from '@/core/api-client';
import type {
  Dashboard, DashboardCreate, DashboardUpdate, DashboardListResponse, DashboardFilters,
  Widget, WidgetCreate, WidgetUpdate, WidgetLayoutUpdate,
  DataSource, DataSourceCreate, DataSourceUpdate,
  DataQuery, DataQueryCreate, DataQueryUpdate,
  DashboardShare, ShareCreate, ShareUpdate,
  AlertRule, AlertRuleCreate, AlertRuleUpdate, Alert, AlertListResponse,
  ScheduledReport, ScheduledReportCreate, ScheduledReportUpdate,
  DashboardTemplate, TemplateCreate, TemplateUpdate, TemplateListResponse,
  Favorite, FavoriteCreate,
  UserPreference, UserPreferenceCreate, UserPreferenceUpdate,
  ExportRequest, ExportResponse,
} from './types';

const BASE_URL = '/dashboards';

// ============================================================================
// DASHBOARD API
// ============================================================================

export const dashboardApi = {
  list: async (filters?: DashboardFilters): Promise<DashboardListResponse> => {
    const params = new URLSearchParams();
    if (filters?.type) params.set('type', filters.type);
    if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active));
    if (filters?.owner_id) params.set('owner_id', filters.owner_id);
    if (filters?.tags) filters.tags.forEach(t => params.append('tags', t));
    if (filters?.search) params.set('search', filters.search);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    return api.get(`${BASE_URL}?${params}`);
  },

  get: async (id: string): Promise<Dashboard> => {
    return api.get(`${BASE_URL}/${id}`);
  },

  create: async (data: DashboardCreate): Promise<Dashboard> => {
    return api.post(BASE_URL, data);
  },

  update: async (id: string, data: DashboardUpdate): Promise<Dashboard> => {
    return api.put(`${BASE_URL}/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/${id}`);
  },

  duplicate: async (id: string, name?: string): Promise<Dashboard> => {
    return api.post(`${BASE_URL}/${id}/duplicate`, { name });
  },

  export: async (id: string, request: ExportRequest): Promise<ExportResponse> => {
    return api.post(`${BASE_URL}/${id}/export`, request);
  },

  refresh: async (id: string): Promise<void> => {
    return api.post(`${BASE_URL}/${id}/refresh`);
  },
};

// ============================================================================
// WIDGET API
// ============================================================================

export const widgetApi = {
  list: async (dashboardId: string): Promise<Widget[]> => {
    return api.get(`${BASE_URL}/${dashboardId}/widgets`);
  },

  get: async (dashboardId: string, widgetId: string): Promise<Widget> => {
    return api.get(`${BASE_URL}/${dashboardId}/widgets/${widgetId}`);
  },

  create: async (dashboardId: string, data: WidgetCreate): Promise<Widget> => {
    return api.post(`${BASE_URL}/${dashboardId}/widgets`, data);
  },

  update: async (dashboardId: string, widgetId: string, data: WidgetUpdate): Promise<Widget> => {
    return api.put(`${BASE_URL}/${dashboardId}/widgets/${widgetId}`, data);
  },

  delete: async (dashboardId: string, widgetId: string): Promise<void> => {
    return api.delete(`${BASE_URL}/${dashboardId}/widgets/${widgetId}`);
  },

  updateLayout: async (dashboardId: string, layouts: WidgetLayoutUpdate[]): Promise<void> => {
    return api.put(`${BASE_URL}/${dashboardId}/widgets/layout`, { layouts });
  },

  getData: async (dashboardId: string, widgetId: string, params?: Record<string, unknown>): Promise<unknown> => {
    return api.get(`${BASE_URL}/${dashboardId}/widgets/${widgetId}/data`, { params });
  },

  refreshData: async (dashboardId: string, widgetId: string): Promise<unknown> => {
    return api.post(`${BASE_URL}/${dashboardId}/widgets/${widgetId}/refresh`);
  },
};

// ============================================================================
// DATA SOURCE API
// ============================================================================

export const dataSourceApi = {
  list: async (): Promise<DataSource[]> => {
    return api.get(`${BASE_URL}/data-sources`);
  },

  get: async (id: string): Promise<DataSource> => {
    return api.get(`${BASE_URL}/data-sources/${id}`);
  },

  create: async (data: DataSourceCreate): Promise<DataSource> => {
    return api.post(`${BASE_URL}/data-sources`, data);
  },

  update: async (id: string, data: DataSourceUpdate): Promise<DataSource> => {
    return api.put(`${BASE_URL}/data-sources/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/data-sources/${id}`);
  },

  test: async (id: string): Promise<{ success: boolean; message: string }> => {
    return api.post(`${BASE_URL}/data-sources/${id}/test`);
  },
};

// ============================================================================
// DATA QUERY API
// ============================================================================

export const dataQueryApi = {
  list: async (dataSourceId?: string): Promise<DataQuery[]> => {
    const params = dataSourceId ? `?data_source_id=${dataSourceId}` : '';
    return api.get(`${BASE_URL}/queries${params}`);
  },

  get: async (id: string): Promise<DataQuery> => {
    return api.get(`${BASE_URL}/queries/${id}`);
  },

  create: async (data: DataQueryCreate): Promise<DataQuery> => {
    return api.post(`${BASE_URL}/queries`, data);
  },

  update: async (id: string, data: DataQueryUpdate): Promise<DataQuery> => {
    return api.put(`${BASE_URL}/queries/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/queries/${id}`);
  },

  execute: async (id: string, params?: Record<string, unknown>): Promise<unknown> => {
    return api.post(`${BASE_URL}/queries/${id}/execute`, params);
  },
};

// ============================================================================
// SHARE API
// ============================================================================

export const shareApi = {
  list: async (dashboardId: string): Promise<DashboardShare[]> => {
    return api.get(`${BASE_URL}/${dashboardId}/shares`);
  },

  create: async (dashboardId: string, data: ShareCreate): Promise<DashboardShare> => {
    return api.post(`${BASE_URL}/${dashboardId}/shares`, data);
  },

  update: async (dashboardId: string, shareId: string, data: ShareUpdate): Promise<DashboardShare> => {
    return api.put(`${BASE_URL}/${dashboardId}/shares/${shareId}`, data);
  },

  delete: async (dashboardId: string, shareId: string): Promise<void> => {
    return api.delete(`${BASE_URL}/${dashboardId}/shares/${shareId}`);
  },
};

// ============================================================================
// ALERT RULE API
// ============================================================================

export const alertRuleApi = {
  list: async (dashboardId?: string): Promise<AlertRule[]> => {
    const params = dashboardId ? `?dashboard_id=${dashboardId}` : '';
    return api.get(`${BASE_URL}/alert-rules${params}`);
  },

  get: async (id: string): Promise<AlertRule> => {
    return api.get(`${BASE_URL}/alert-rules/${id}`);
  },

  create: async (data: AlertRuleCreate): Promise<AlertRule> => {
    return api.post(`${BASE_URL}/alert-rules`, data);
  },

  update: async (id: string, data: AlertRuleUpdate): Promise<AlertRule> => {
    return api.put(`${BASE_URL}/alert-rules/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/alert-rules/${id}`);
  },
};

// ============================================================================
// ALERT API
// ============================================================================

export const alertApi = {
  list: async (filters?: { is_acknowledged?: boolean; is_resolved?: boolean; page?: number; page_size?: number }): Promise<AlertListResponse> => {
    const params = new URLSearchParams();
    if (filters?.is_acknowledged !== undefined) params.set('is_acknowledged', String(filters.is_acknowledged));
    if (filters?.is_resolved !== undefined) params.set('is_resolved', String(filters.is_resolved));
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    return api.get(`${BASE_URL}/alerts?${params}`);
  },

  get: async (id: string): Promise<Alert> => {
    return api.get(`${BASE_URL}/alerts/${id}`);
  },

  acknowledge: async (id: string, note?: string): Promise<Alert> => {
    return api.post(`${BASE_URL}/alerts/${id}/acknowledge`, { note });
  },

  resolve: async (id: string, resolution_note?: string): Promise<Alert> => {
    return api.post(`${BASE_URL}/alerts/${id}/resolve`, { resolution_note });
  },

  snooze: async (id: string, snooze_until: string): Promise<Alert> => {
    return api.post(`${BASE_URL}/alerts/${id}/snooze`, { snooze_until });
  },
};

// ============================================================================
// SCHEDULED REPORT API
// ============================================================================

export const scheduledReportApi = {
  list: async (dashboardId?: string): Promise<ScheduledReport[]> => {
    const params = dashboardId ? `?dashboard_id=${dashboardId}` : '';
    return api.get(`${BASE_URL}/scheduled-reports${params}`);
  },

  get: async (id: string): Promise<ScheduledReport> => {
    return api.get(`${BASE_URL}/scheduled-reports/${id}`);
  },

  create: async (data: ScheduledReportCreate): Promise<ScheduledReport> => {
    return api.post(`${BASE_URL}/scheduled-reports`, data);
  },

  update: async (id: string, data: ScheduledReportUpdate): Promise<ScheduledReport> => {
    return api.put(`${BASE_URL}/scheduled-reports/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/scheduled-reports/${id}`);
  },

  runNow: async (id: string): Promise<void> => {
    return api.post(`${BASE_URL}/scheduled-reports/${id}/run`);
  },
};

// ============================================================================
// TEMPLATE API
// ============================================================================

export const templateApi = {
  list: async (category?: string): Promise<TemplateListResponse> => {
    const params = category ? `?category=${category}` : '';
    return api.get(`${BASE_URL}/templates${params}`);
  },

  get: async (id: string): Promise<DashboardTemplate> => {
    return api.get(`${BASE_URL}/templates/${id}`);
  },

  create: async (data: TemplateCreate): Promise<DashboardTemplate> => {
    return api.post(`${BASE_URL}/templates`, data);
  },

  update: async (id: string, data: TemplateUpdate): Promise<DashboardTemplate> => {
    return api.put(`${BASE_URL}/templates/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/templates/${id}`);
  },

  createFromDashboard: async (dashboardId: string, data: TemplateCreate): Promise<DashboardTemplate> => {
    return api.post(`${BASE_URL}/${dashboardId}/create-template`, data);
  },

  instantiate: async (templateId: string, name: string): Promise<Dashboard> => {
    return api.post(`${BASE_URL}/templates/${templateId}/instantiate`, { name });
  },
};

// ============================================================================
// FAVORITE API
// ============================================================================

export const favoriteApi = {
  list: async (): Promise<Favorite[]> => {
    return api.get(`${BASE_URL}/favorites`);
  },

  add: async (data: FavoriteCreate): Promise<Favorite> => {
    return api.post(`${BASE_URL}/favorites`, data);
  },

  remove: async (dashboardId: string): Promise<void> => {
    return api.delete(`${BASE_URL}/favorites/${dashboardId}`);
  },

  reorder: async (favorites: { dashboard_id: string; display_order: number }[]): Promise<void> => {
    return api.put(`${BASE_URL}/favorites/reorder`, { favorites });
  },
};

// ============================================================================
// USER PREFERENCE API
// ============================================================================

export const preferenceApi = {
  get: async (): Promise<UserPreference> => {
    return api.get(`${BASE_URL}/preferences`);
  },

  create: async (data: UserPreferenceCreate): Promise<UserPreference> => {
    return api.post(`${BASE_URL}/preferences`, data);
  },

  update: async (data: UserPreferenceUpdate): Promise<UserPreference> => {
    return api.put(`${BASE_URL}/preferences`, data);
  },
};
