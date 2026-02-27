/**
 * AZALSCORE Module - Dashboards API
 * Client API pour le module de tableaux de bord
 */

import { api } from '@core/api-client';
import { unwrapApiResponse } from '@/types';
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
    const queryString = params.toString();
    const url = `${BASE_URL}${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<DashboardListResponse>(url);
    return unwrapApiResponse(response) as DashboardListResponse;
  },

  get: async (id: string): Promise<Dashboard> => {
    const response = await api.get<Dashboard>(`${BASE_URL}/${id}`);
    return response as unknown as Dashboard;
  },

  create: async (data: DashboardCreate): Promise<Dashboard> => {
    const response = await api.post<Dashboard>(BASE_URL, data);
    return response as unknown as Dashboard;
  },

  update: async (id: string, data: DashboardUpdate): Promise<Dashboard> => {
    const response = await api.put<Dashboard>(`${BASE_URL}/${id}`, data);
    return response as unknown as Dashboard;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/${id}`);
  },

  duplicate: async (id: string, name?: string): Promise<Dashboard> => {
    const response = await api.post<Dashboard>(`${BASE_URL}/${id}/duplicate`, { name });
    return response as unknown as Dashboard;
  },

  export: async (id: string, request: ExportRequest): Promise<ExportResponse> => {
    const response = await api.post<ExportResponse>(`${BASE_URL}/${id}/export`, request);
    return response as unknown as ExportResponse;
  },

  refresh: async (id: string): Promise<void> => {
    await api.post(`${BASE_URL}/${id}/refresh`);
  },
};

// ============================================================================
// WIDGET API
// ============================================================================

export const widgetApi = {
  list: async (dashboardId: string): Promise<Widget[]> => {
    const response = await api.get<Widget[]>(`${BASE_URL}/${dashboardId}/widgets`);
    return response as unknown as Widget[];
  },

  get: async (dashboardId: string, widgetId: string): Promise<Widget> => {
    const response = await api.get<Widget>(`${BASE_URL}/${dashboardId}/widgets/${widgetId}`);
    return response as unknown as Widget;
  },

  create: async (dashboardId: string, data: WidgetCreate): Promise<Widget> => {
    const response = await api.post<Widget>(`${BASE_URL}/${dashboardId}/widgets`, data);
    return response as unknown as Widget;
  },

  update: async (dashboardId: string, widgetId: string, data: WidgetUpdate): Promise<Widget> => {
    const response = await api.put<Widget>(`${BASE_URL}/${dashboardId}/widgets/${widgetId}`, data);
    return response as unknown as Widget;
  },

  delete: async (dashboardId: string, widgetId: string): Promise<void> => {
    await api.delete(`${BASE_URL}/${dashboardId}/widgets/${widgetId}`);
  },

  updateLayout: async (dashboardId: string, layouts: WidgetLayoutUpdate[]): Promise<void> => {
    await api.put(`${BASE_URL}/${dashboardId}/widgets/layout`, { layouts });
  },

  getData: async (dashboardId: string, widgetId: string, params?: Record<string, unknown>): Promise<unknown> => {
    const queryString = params ? '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString() : '';
    const response = await api.get<unknown>(`${BASE_URL}/${dashboardId}/widgets/${widgetId}/data${queryString}`);
    return response as unknown;
  },

  refreshData: async (dashboardId: string, widgetId: string): Promise<unknown> => {
    const response = await api.post<unknown>(`${BASE_URL}/${dashboardId}/widgets/${widgetId}/refresh`);
    return response as unknown;
  },
};

// ============================================================================
// DATA SOURCE API
// ============================================================================

export const dataSourceApi = {
  list: async (): Promise<DataSource[]> => {
    const response = await api.get<DataSource[]>(`${BASE_URL}/data-sources`);
    return response as unknown as DataSource[];
  },

  get: async (id: string): Promise<DataSource> => {
    const response = await api.get<DataSource>(`${BASE_URL}/data-sources/${id}`);
    return response as unknown as DataSource;
  },

  create: async (data: DataSourceCreate): Promise<DataSource> => {
    const response = await api.post<DataSource>(`${BASE_URL}/data-sources`, data);
    return response as unknown as DataSource;
  },

  update: async (id: string, data: DataSourceUpdate): Promise<DataSource> => {
    const response = await api.put<DataSource>(`${BASE_URL}/data-sources/${id}`, data);
    return response as unknown as DataSource;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/data-sources/${id}`);
  },

  test: async (id: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.post<{ success: boolean; message: string }>(`${BASE_URL}/data-sources/${id}/test`);
    return response as unknown as { success: boolean; message: string };
  },
};

// ============================================================================
// DATA QUERY API
// ============================================================================

export const dataQueryApi = {
  list: async (dataSourceId?: string): Promise<DataQuery[]> => {
    const params = dataSourceId ? `?data_source_id=${dataSourceId}` : '';
    const response = await api.get<DataQuery[]>(`${BASE_URL}/queries${params}`);
    return response as unknown as DataQuery[];
  },

  get: async (id: string): Promise<DataQuery> => {
    const response = await api.get<DataQuery>(`${BASE_URL}/queries/${id}`);
    return response as unknown as DataQuery;
  },

  create: async (data: DataQueryCreate): Promise<DataQuery> => {
    const response = await api.post<DataQuery>(`${BASE_URL}/queries`, data);
    return response as unknown as DataQuery;
  },

  update: async (id: string, data: DataQueryUpdate): Promise<DataQuery> => {
    const response = await api.put<DataQuery>(`${BASE_URL}/queries/${id}`, data);
    return response as unknown as DataQuery;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/queries/${id}`);
  },

  execute: async (id: string, params?: Record<string, unknown>): Promise<unknown> => {
    const response = await api.post<unknown>(`${BASE_URL}/queries/${id}/execute`, params);
    return response as unknown;
  },
};

// ============================================================================
// SHARE API
// ============================================================================

export const shareApi = {
  list: async (dashboardId: string): Promise<DashboardShare[]> => {
    const response = await api.get<DashboardShare[]>(`${BASE_URL}/${dashboardId}/shares`);
    return response as unknown as DashboardShare[];
  },

  create: async (dashboardId: string, data: ShareCreate): Promise<DashboardShare> => {
    const response = await api.post<DashboardShare>(`${BASE_URL}/${dashboardId}/shares`, data);
    return response as unknown as DashboardShare;
  },

  update: async (dashboardId: string, shareId: string, data: ShareUpdate): Promise<DashboardShare> => {
    const response = await api.put<DashboardShare>(`${BASE_URL}/${dashboardId}/shares/${shareId}`, data);
    return response as unknown as DashboardShare;
  },

  delete: async (dashboardId: string, shareId: string): Promise<void> => {
    await api.delete(`${BASE_URL}/${dashboardId}/shares/${shareId}`);
  },
};

// ============================================================================
// ALERT RULE API
// ============================================================================

export const alertRuleApi = {
  list: async (dashboardId?: string): Promise<AlertRule[]> => {
    const params = dashboardId ? `?dashboard_id=${dashboardId}` : '';
    const response = await api.get<AlertRule[]>(`${BASE_URL}/alert-rules${params}`);
    return response as unknown as AlertRule[];
  },

  get: async (id: string): Promise<AlertRule> => {
    const response = await api.get<AlertRule>(`${BASE_URL}/alert-rules/${id}`);
    return response as unknown as AlertRule;
  },

  create: async (data: AlertRuleCreate): Promise<AlertRule> => {
    const response = await api.post<AlertRule>(`${BASE_URL}/alert-rules`, data);
    return response as unknown as AlertRule;
  },

  update: async (id: string, data: AlertRuleUpdate): Promise<AlertRule> => {
    const response = await api.put<AlertRule>(`${BASE_URL}/alert-rules/${id}`, data);
    return response as unknown as AlertRule;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/alert-rules/${id}`);
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
    const queryString = params.toString();
    const url = `${BASE_URL}/alerts${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<AlertListResponse>(url);
    return unwrapApiResponse(response) as AlertListResponse;
  },

  get: async (id: string): Promise<Alert> => {
    const response = await api.get<Alert>(`${BASE_URL}/alerts/${id}`);
    return response as unknown as Alert;
  },

  acknowledge: async (id: string, note?: string): Promise<Alert> => {
    const response = await api.post<Alert>(`${BASE_URL}/alerts/${id}/acknowledge`, { note });
    return response as unknown as Alert;
  },

  resolve: async (id: string, resolution_note?: string): Promise<Alert> => {
    const response = await api.post<Alert>(`${BASE_URL}/alerts/${id}/resolve`, { resolution_note });
    return response as unknown as Alert;
  },

  snooze: async (id: string, snooze_until: string): Promise<Alert> => {
    const response = await api.post<Alert>(`${BASE_URL}/alerts/${id}/snooze`, { snooze_until });
    return response as unknown as Alert;
  },
};

// ============================================================================
// SCHEDULED REPORT API
// ============================================================================

export const scheduledReportApi = {
  list: async (dashboardId?: string): Promise<ScheduledReport[]> => {
    const params = dashboardId ? `?dashboard_id=${dashboardId}` : '';
    const response = await api.get<ScheduledReport[]>(`${BASE_URL}/scheduled-reports${params}`);
    return response as unknown as ScheduledReport[];
  },

  get: async (id: string): Promise<ScheduledReport> => {
    const response = await api.get<ScheduledReport>(`${BASE_URL}/scheduled-reports/${id}`);
    return response as unknown as ScheduledReport;
  },

  create: async (data: ScheduledReportCreate): Promise<ScheduledReport> => {
    const response = await api.post<ScheduledReport>(`${BASE_URL}/scheduled-reports`, data);
    return response as unknown as ScheduledReport;
  },

  update: async (id: string, data: ScheduledReportUpdate): Promise<ScheduledReport> => {
    const response = await api.put<ScheduledReport>(`${BASE_URL}/scheduled-reports/${id}`, data);
    return response as unknown as ScheduledReport;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/scheduled-reports/${id}`);
  },

  runNow: async (id: string): Promise<void> => {
    await api.post(`${BASE_URL}/scheduled-reports/${id}/run`);
  },
};

// ============================================================================
// TEMPLATE API
// ============================================================================

export const templateApi = {
  list: async (category?: string): Promise<TemplateListResponse> => {
    const params = category ? `?category=${category}` : '';
    const response = await api.get<TemplateListResponse>(`${BASE_URL}/templates${params}`);
    return unwrapApiResponse(response) as TemplateListResponse;
  },

  get: async (id: string): Promise<DashboardTemplate> => {
    const response = await api.get<DashboardTemplate>(`${BASE_URL}/templates/${id}`);
    return response as unknown as DashboardTemplate;
  },

  create: async (data: TemplateCreate): Promise<DashboardTemplate> => {
    const response = await api.post<DashboardTemplate>(`${BASE_URL}/templates`, data);
    return response as unknown as DashboardTemplate;
  },

  update: async (id: string, data: TemplateUpdate): Promise<DashboardTemplate> => {
    const response = await api.put<DashboardTemplate>(`${BASE_URL}/templates/${id}`, data);
    return response as unknown as DashboardTemplate;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/templates/${id}`);
  },

  createFromDashboard: async (dashboardId: string, data: TemplateCreate): Promise<DashboardTemplate> => {
    const response = await api.post<DashboardTemplate>(`${BASE_URL}/${dashboardId}/create-template`, data);
    return response as unknown as DashboardTemplate;
  },

  instantiate: async (templateId: string, name: string): Promise<Dashboard> => {
    const response = await api.post<Dashboard>(`${BASE_URL}/templates/${templateId}/instantiate`, { name });
    return response as unknown as Dashboard;
  },
};

// ============================================================================
// FAVORITE API
// ============================================================================

export const favoriteApi = {
  list: async (): Promise<Favorite[]> => {
    const response = await api.get<Favorite[]>(`${BASE_URL}/favorites`);
    return response as unknown as Favorite[];
  },

  add: async (data: FavoriteCreate): Promise<Favorite> => {
    const response = await api.post<Favorite>(`${BASE_URL}/favorites`, data);
    return response as unknown as Favorite;
  },

  remove: async (dashboardId: string): Promise<void> => {
    await api.delete(`${BASE_URL}/favorites/${dashboardId}`);
  },

  reorder: async (favorites: { dashboard_id: string; display_order: number }[]): Promise<void> => {
    await api.put(`${BASE_URL}/favorites/reorder`, { favorites });
  },
};

// ============================================================================
// USER PREFERENCE API
// ============================================================================

export const preferenceApi = {
  get: async (): Promise<UserPreference> => {
    const response = await api.get<UserPreference>(`${BASE_URL}/preferences`);
    return response as unknown as UserPreference;
  },

  create: async (data: UserPreferenceCreate): Promise<UserPreference> => {
    const response = await api.post<UserPreference>(`${BASE_URL}/preferences`, data);
    return response as unknown as UserPreference;
  },

  update: async (data: UserPreferenceUpdate): Promise<UserPreference> => {
    const response = await api.put<UserPreference>(`${BASE_URL}/preferences`, data);
    return response as unknown as UserPreference;
  },
};
