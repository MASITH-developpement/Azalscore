import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, FileText, Play, Users } from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button } from '@ui/actions';
import { Select } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import type { TableColumn } from '@/types';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavItem {
  id: string;
  label: string;
}

interface TabNavProps {
  tabs: TabNavItem[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <nav className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </nav>
);

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
  config: Record<string, any>;
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
  default_value?: any;
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
// CONSTANTES
// ============================================================================

const DASHBOARD_TYPES = [
  { value: 'OPERATIONAL', label: 'Operationnel' },
  { value: 'ANALYTICAL', label: 'Analytique' },
  { value: 'STRATEGIC', label: 'Strategique' }
];

const REPORT_TYPES = [
  { value: 'STANDARD', label: 'Standard' },
  { value: 'CUSTOM', label: 'Personnalise' },
  { value: 'SCHEDULED', label: 'Planifie' }
];

const REPORT_FORMATS = [
  { value: 'PDF', label: 'PDF' },
  { value: 'EXCEL', label: 'Excel' },
  { value: 'CSV', label: 'CSV' }
];

const REPORT_CATEGORIES = [
  { value: 'SALES', label: 'Ventes' },
  { value: 'FINANCE', label: 'Finance' },
  { value: 'INVENTORY', label: 'Stock' },
  { value: 'HR', label: 'RH' },
  { value: 'PRODUCTION', label: 'Production' },
  { value: 'OPERATIONS', label: 'Operations' }
];

// ============================================================================
// HELPERS
// ============================================================================

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

// ============================================================================
// API HOOKS
// ============================================================================

const useBIDashboardStats = () => {
  return useQuery({
    queryKey: ['bi', 'stats'],
    queryFn: async () => {
      const response = await api.get<BIDashboardStats>('/bi/stats');
      return response.data;
    }
  });
};

const useDashboards = (type?: string) => {
  return useQuery({
    queryKey: ['bi', 'dashboards', type],
    queryFn: async () => {
      const response = await api.get<Dashboard[]>(`/bi/dashboards${type ? `?type=${type}` : ''}`);
      return response.data;
    }
  });
};

const useReports = (filters?: { type?: string; category?: string }) => {
  return useQuery({
    queryKey: ['bi', 'reports', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.category) params.append('category', filters.category);
      const queryString = params.toString();
      const response = await api.get<Report[]>(`/bi/reports${queryString ? `?${queryString}` : ''}`);
      return response.data;
    }
  });
};

const useDataSources = () => {
  return useQuery({
    queryKey: ['bi', 'data-sources'],
    queryFn: async () => {
      const response = await api.get<DataSource[]>('/bi/data-sources');
      return response.data;
    }
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const DashboardsView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const { data: dashboards = [], isLoading, error: dashboardsError, refetch: refetchDashboards } = useDashboards(filterType || undefined);

  const columns: TableColumn<Dashboard>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'description', header: 'Description', accessor: 'description', render: (v) => (v as string) || '-' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = DASHBOARD_TYPES.find(t => t.value === (v as string));
      return <Badge color="blue">{info?.label || (v as string)}</Badge>;
    }},
    { id: 'widgets', header: 'Widgets', accessor: 'widgets', render: (v) => <Badge color="purple">{(v as Widget[])?.length || 0}</Badge> },
    { id: 'is_public', header: 'Public', accessor: 'is_public', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_v, row) => (
      <Button size="sm" onClick={() => { window.dispatchEvent(new CustomEvent('azals:open', { detail: { module: 'bi', type: 'dashboard', id: (row as Dashboard).id } })); }}>Ouvrir</Button>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Tableaux de bord</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous les types' }, ...DASHBOARD_TYPES]}
            className="w-40"
          />
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'bi', type: 'dashboard' } })); }}>Nouveau tableau</Button>
        </div>
      </div>
      <DataTable columns={columns} data={dashboards} isLoading={isLoading} keyField="id" filterable error={dashboardsError instanceof Error ? dashboardsError : null} onRetry={() => refetchDashboards()} />
    </Card>
  );
};

const ReportsView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterCategory, setFilterCategory] = useState<string>('');
  const { data: reports = [], isLoading, error: reportsError, refetch: refetchReports } = useReports({
    type: filterType || undefined,
    category: filterCategory || undefined
  });

  const columns: TableColumn<Report>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'category', header: 'Categorie', accessor: 'category', render: (v) => {
      const info = REPORT_CATEGORIES.find(c => c.value === (v as string));
      return info?.label || (v as string);
    }},
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = REPORT_TYPES.find(t => t.value === (v as string));
      return <Badge color="blue">{info?.label || (v as string)}</Badge>;
    }},
    { id: 'format', header: 'Format', accessor: 'format', render: (v) => {
      const info = REPORT_FORMATS.find(f => f.value === (v as string));
      return info?.label || (v as string);
    }},
    { id: 'last_run', header: 'Derniere execution', accessor: 'last_run', render: (v) => (v as string) ? formatDateTime(v as string) : '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_v, row) => (
      <Button size="sm" onClick={() => { window.dispatchEvent(new CustomEvent('azals:execute', { detail: { module: 'bi', type: 'report', id: (row as Report).id } })); }}>Executer</Button>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Rapports</h3>
        <div className="flex gap-2">
          <Select
            value={filterCategory}
            onChange={(v) => setFilterCategory(v)}
            options={[{ value: '', label: 'Toutes categories' }, ...REPORT_CATEGORIES]}
            className="w-36"
          />
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous types' }, ...REPORT_TYPES]}
            className="w-36"
          />
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'bi', type: 'report' } })); }}>Nouveau rapport</Button>
        </div>
      </div>
      <DataTable columns={columns} data={reports} isLoading={isLoading} keyField="id" filterable error={reportsError instanceof Error ? reportsError : null} onRetry={() => refetchReports()} />
    </Card>
  );
};

const DataSourcesView: React.FC = () => {
  const { data: dataSources = [], isLoading, error: dataSourcesError, refetch: refetchDataSources } = useDataSources();

  const columns: TableColumn<DataSource>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => <Badge color="blue">{v as string}</Badge> },
    { id: 'module', header: 'Module', accessor: 'module', render: (v) => (v as string) || '-' },
    { id: 'fields', header: 'Champs', accessor: 'fields', render: (v) => <Badge color="purple">{(v as DataField[])?.length || 0}</Badge> },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Sources de donnees</h3>
        <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'bi', type: 'data-source' } })); }}>Nouvelle source</Button>
      </div>
      <DataTable columns={columns} data={dataSources} isLoading={isLoading} keyField="id" filterable error={dataSourcesError instanceof Error ? dataSourcesError : null} onRetry={() => refetchDataSources()} />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'dashboards' | 'reports' | 'data-sources';

const BIModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats } = useBIDashboardStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'dashboards', label: 'Tableaux de bord' },
    { id: 'reports', label: 'Rapports' },
    { id: 'data-sources', label: 'Sources de donnees' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'dashboards':
        return <DashboardsView />;
      case 'reports':
        return <ReportsView />;
      case 'data-sources':
        return <DataSourcesView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Tableaux de bord"
                value={String(stats?.total_dashboards || 0)}
                icon={<BarChart3 />}
                variant="default"
                onClick={() => setCurrentView('dashboards')}
              />
              <StatCard
                title="Rapports"
                value={String(stats?.total_reports || 0)}
                icon={<FileText />}
                variant="default"
                onClick={() => setCurrentView('reports')}
              />
              <StatCard
                title="Rapports executes"
                value={String(stats?.reports_run_today || 0)}
                icon={<Play />}
                variant="success"
              />
              <StatCard
                title="Utilisateurs actifs"
                value={String(stats?.active_users || 0)}
                icon={<Users />}
                variant="warning"
              />
            </Grid>
            {stats?.popular_reports && stats.popular_reports.length > 0 && (
              <Card>
                <h3 className="text-lg font-semibold mb-4">Rapports populaires</h3>
                <div className="space-y-2">
                  {stats.popular_reports.map((r, i) => (
                    <div key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span>{r.report_name}</span>
                      <Badge color="blue">{r.run_count} executions</Badge>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        );
    }
  };

  return (
    <PageWrapper
      title="Business Intelligence"
      subtitle="Tableaux de bord et rapports"
    >
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default BIModule;
