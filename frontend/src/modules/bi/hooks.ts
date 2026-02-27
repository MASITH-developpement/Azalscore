/**
 * AZALSCORE - BI (Business Intelligence) React Query Hooks
 * =========================================================
 * Hooks pour le module BI / Reporting
 */

import { useQuery } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';

// ============================================================================
// TYPES
// ============================================================================

interface Dashboard {
  id: string;
  code: string;
  name: string;
  description?: string;
  type: 'OPERATIONAL' | 'ANALYTICAL' | 'STRATEGIC';
  widgets: Widget[];
  is_public: boolean;
  created_at: string;
}

interface Widget {
  id: string;
  title: string;
  type: 'KPI' | 'CHART' | 'TABLE' | 'MAP';
  chart_type?: 'LINE' | 'BAR' | 'PIE' | 'DONUT' | 'AREA';
  data_source: string;
  config: Record<string, unknown>;
  position: { x: number; y: number; w: number; h: number };
}

interface Report {
  id: string;
  code: string;
  name: string;
  description?: string;
  type: 'STANDARD' | 'CUSTOM' | 'SCHEDULED';
  category: string;
  format: 'PDF' | 'EXCEL' | 'CSV';
  parameters: ReportParameter[];
  last_run?: string;
  schedule?: string;
  is_active: boolean;
}

interface ReportParameter {
  name: string;
  label: string;
  type: 'DATE' | 'DATE_RANGE' | 'SELECT' | 'MULTI_SELECT' | 'TEXT';
  required: boolean;
  options?: { value: string; label: string }[];
  default_value?: unknown;
}

interface DataSource {
  id: string;
  code: string;
  name: string;
  type: 'TABLE' | 'VIEW' | 'QUERY' | 'API';
  module?: string;
  fields: DataField[];
  is_active: boolean;
}

interface DataField {
  name: string;
  label: string;
  type: 'STRING' | 'NUMBER' | 'DATE' | 'BOOLEAN';
  is_dimension: boolean;
  is_measure: boolean;
}

interface BIDashboardStats {
  total_dashboards: number;
  total_reports: number;
  reports_run_today: number;
  active_users: number;
  popular_reports: { report_name: string; run_count: number }[];
}

// ============================================================================
// QUERY KEY FACTORY
// ============================================================================

export const biKeys = {
  all: ['bi'] as const,
  stats: () => [...biKeys.all, 'stats'] as const,
  dashboards: (type?: string) => [...biKeys.all, 'dashboards', type] as const,
  reports: (filters?: { type?: string; category?: string }) =>
    [...biKeys.all, 'reports', serializeFilters(filters)] as const,
  dataSources: () => [...biKeys.all, 'data-sources'] as const,
};

// ============================================================================
// QUERY HOOKS
// ============================================================================

export const useBIDashboardStats = () => {
  return useQuery({
    queryKey: biKeys.stats(),
    queryFn: async () => {
      const response = await api.get<BIDashboardStats>('/bi/stats');
      return response.data;
    },
  });
};

export const useDashboards = (type?: string) => {
  return useQuery({
    queryKey: biKeys.dashboards(type),
    queryFn: async () => {
      const response = await api.get<Dashboard[]>(`/bi/dashboards${type ? `?type=${type}` : ''}`);
      return response.data;
    },
  });
};

export const useReports = (filters?: { type?: string; category?: string }) => {
  return useQuery({
    queryKey: biKeys.reports(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.category) params.append('category', filters.category);
      const queryString = params.toString();
      const response = await api.get<Report[]>(`/bi/reports${queryString ? `?${queryString}` : ''}`);
      return response.data;
    },
  });
};

export const useDataSources = () => {
  return useQuery({
    queryKey: biKeys.dataSources(),
    queryFn: async () => {
      const response = await api.get<DataSource[]>('/bi/data-sources');
      return response.data;
    },
  });
};

// Re-export types
export type { Dashboard, Widget, Report, ReportParameter, DataSource, DataField, BIDashboardStats };
