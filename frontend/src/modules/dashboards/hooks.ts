/**
 * AZALSCORE Module - Dashboards Hooks
 * React Query hooks pour le module de tableaux de bord
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  dashboardApi, widgetApi, dataSourceApi, dataQueryApi,
  shareApi, alertRuleApi, alertApi, scheduledReportApi,
  templateApi, favoriteApi, preferenceApi,
} from './api';
import type {
  DashboardCreate, DashboardUpdate, DashboardFilters,
  WidgetCreate, WidgetUpdate, WidgetLayoutUpdate,
  DataSourceCreate, DataSourceUpdate,
  DataQueryCreate, DataQueryUpdate,
  ShareCreate, ShareUpdate,
  AlertRuleCreate, AlertRuleUpdate,
  ScheduledReportCreate, ScheduledReportUpdate,
  TemplateCreate, TemplateUpdate,
  FavoriteCreate,
  UserPreferenceCreate, UserPreferenceUpdate,
  ExportRequest,
} from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const dashboardKeys = {
  all: ['dashboards'] as const,
  list: (filters?: DashboardFilters) => [...dashboardKeys.all, 'list', filters] as const,
  detail: (id: string) => [...dashboardKeys.all, 'detail', id] as const,
  widgets: (dashboardId: string) => [...dashboardKeys.all, 'widgets', dashboardId] as const,
  widgetData: (dashboardId: string, widgetId: string) => [...dashboardKeys.all, 'widget-data', dashboardId, widgetId] as const,
  shares: (dashboardId: string) => [...dashboardKeys.all, 'shares', dashboardId] as const,

  dataSources: () => ['dataSources'] as const,
  dataQueries: (dataSourceId?: string) => ['dataQueries', dataSourceId] as const,

  alertRules: (dashboardId?: string) => ['alertRules', dashboardId] as const,
  alerts: () => ['alerts'] as const,

  scheduledReports: (dashboardId?: string) => ['scheduledReports', dashboardId] as const,

  templates: (category?: string) => ['templates', category] as const,
  templateDetail: (id: string) => ['templates', 'detail', id] as const,

  favorites: () => ['favorites'] as const,
  preferences: () => ['preferences'] as const,
};

// ============================================================================
// DASHBOARD HOOKS
// ============================================================================

export function useDashboardList(filters?: DashboardFilters) {
  return useQuery({
    queryKey: dashboardKeys.list(filters),
    queryFn: () => dashboardApi.list(filters),
  });
}

export function useDashboard(id: string) {
  return useQuery({
    queryKey: dashboardKeys.detail(id),
    queryFn: () => dashboardApi.get(id),
    enabled: !!id,
  });
}

export function useCreateDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DashboardCreate) => dashboardApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
    },
  });
}

export function useUpdateDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DashboardUpdate }) => dashboardApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
    },
  });
}

export function useDeleteDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => dashboardApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
    },
  });
}

export function useDuplicateDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name?: string }) => dashboardApi.duplicate(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
    },
  });
}

export function useExportDashboard() {
  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: ExportRequest }) => dashboardApi.export(id, request),
  });
}

export function useRefreshDashboard() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => dashboardApi.refresh(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.detail(id) });
    },
  });
}

// ============================================================================
// WIDGET HOOKS
// ============================================================================

export function useWidgets(dashboardId: string) {
  return useQuery({
    queryKey: dashboardKeys.widgets(dashboardId),
    queryFn: () => widgetApi.list(dashboardId),
    enabled: !!dashboardId,
  });
}

export function useWidgetData(dashboardId: string, widgetId: string, params?: Record<string, unknown>) {
  return useQuery({
    queryKey: dashboardKeys.widgetData(dashboardId, widgetId),
    queryFn: () => widgetApi.getData(dashboardId, widgetId, params),
    enabled: !!dashboardId && !!widgetId,
  });
}

export function useCreateWidget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, data }: { dashboardId: string; data: WidgetCreate }) =>
      widgetApi.create(dashboardId, data),
    onSuccess: (_, { dashboardId }) => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.widgets(dashboardId) });
    },
  });
}

export function useUpdateWidget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, widgetId, data }: { dashboardId: string; widgetId: string; data: WidgetUpdate }) =>
      widgetApi.update(dashboardId, widgetId, data),
    onSuccess: (_, { dashboardId }) => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.widgets(dashboardId) });
    },
  });
}

export function useDeleteWidget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, widgetId }: { dashboardId: string; widgetId: string }) =>
      widgetApi.delete(dashboardId, widgetId),
    onSuccess: (_, { dashboardId }) => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.widgets(dashboardId) });
    },
  });
}

export function useUpdateWidgetLayout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, layouts }: { dashboardId: string; layouts: WidgetLayoutUpdate[] }) =>
      widgetApi.updateLayout(dashboardId, layouts),
    onSuccess: (_, { dashboardId }) => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.widgets(dashboardId) });
    },
  });
}

// ============================================================================
// DATA SOURCE HOOKS
// ============================================================================

export function useDataSources() {
  return useQuery({
    queryKey: dashboardKeys.dataSources(),
    queryFn: () => dataSourceApi.list(),
  });
}

export function useCreateDataSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DataSourceCreate) => dataSourceApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.dataSources() });
    },
  });
}

export function useUpdateDataSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DataSourceUpdate }) => dataSourceApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.dataSources() });
    },
  });
}

export function useDeleteDataSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => dataSourceApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.dataSources() });
    },
  });
}

export function useTestDataSource() {
  return useMutation({
    mutationFn: (id: string) => dataSourceApi.test(id),
  });
}

// ============================================================================
// DATA QUERY HOOKS
// ============================================================================

export function useDataQueries(dataSourceId?: string) {
  return useQuery({
    queryKey: dashboardKeys.dataQueries(dataSourceId),
    queryFn: () => dataQueryApi.list(dataSourceId),
  });
}

export function useCreateDataQuery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DataQueryCreate) => dataQueryApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.dataQueries() });
    },
  });
}

export function useUpdateDataQuery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DataQueryUpdate }) => dataQueryApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.dataQueries() });
    },
  });
}

export function useExecuteDataQuery() {
  return useMutation({
    mutationFn: ({ id, params }: { id: string; params?: Record<string, unknown> }) =>
      dataQueryApi.execute(id, params),
  });
}

// ============================================================================
// SHARE HOOKS
// ============================================================================

export function useDashboardShares(dashboardId: string) {
  return useQuery({
    queryKey: dashboardKeys.shares(dashboardId),
    queryFn: () => shareApi.list(dashboardId),
    enabled: !!dashboardId,
  });
}

export function useCreateShare() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, data }: { dashboardId: string; data: ShareCreate }) =>
      shareApi.create(dashboardId, data),
    onSuccess: (_, { dashboardId }) => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.shares(dashboardId) });
    },
  });
}

export function useDeleteShare() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ dashboardId, shareId }: { dashboardId: string; shareId: string }) =>
      shareApi.delete(dashboardId, shareId),
    onSuccess: (_, { dashboardId }) => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.shares(dashboardId) });
    },
  });
}

// ============================================================================
// ALERT HOOKS
// ============================================================================

export function useAlertRules(dashboardId?: string) {
  return useQuery({
    queryKey: dashboardKeys.alertRules(dashboardId),
    queryFn: () => alertRuleApi.list(dashboardId),
  });
}

export function useCreateAlertRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AlertRuleCreate) => alertRuleApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.alertRules() });
    },
  });
}

export function useAlerts(filters?: { is_acknowledged?: boolean; is_resolved?: boolean }) {
  return useQuery({
    queryKey: dashboardKeys.alerts(),
    queryFn: () => alertApi.list(filters),
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string }) => alertApi.acknowledge(id, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.alerts() });
    },
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, resolution_note }: { id: string; resolution_note?: string }) =>
      alertApi.resolve(id, resolution_note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.alerts() });
    },
  });
}

// ============================================================================
// TEMPLATE HOOKS
// ============================================================================

export function useTemplates(category?: string) {
  return useQuery({
    queryKey: dashboardKeys.templates(category),
    queryFn: () => templateApi.list(category),
  });
}

export function useTemplate(id: string) {
  return useQuery({
    queryKey: dashboardKeys.templateDetail(id),
    queryFn: () => templateApi.get(id),
    enabled: !!id,
  });
}

export function useInstantiateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ templateId, name }: { templateId: string; name: string }) =>
      templateApi.instantiate(templateId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.all });
    },
  });
}

// ============================================================================
// FAVORITE HOOKS
// ============================================================================

export function useFavorites() {
  return useQuery({
    queryKey: dashboardKeys.favorites(),
    queryFn: () => favoriteApi.list(),
  });
}

export function useAddFavorite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: FavoriteCreate) => favoriteApi.add(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.favorites() });
    },
  });
}

export function useRemoveFavorite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (dashboardId: string) => favoriteApi.remove(dashboardId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.favorites() });
    },
  });
}

// ============================================================================
// PREFERENCE HOOKS
// ============================================================================

export function usePreferences() {
  return useQuery({
    queryKey: dashboardKeys.preferences(),
    queryFn: () => preferenceApi.get(),
  });
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UserPreferenceUpdate) => preferenceApi.update(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: dashboardKeys.preferences() });
    },
  });
}
