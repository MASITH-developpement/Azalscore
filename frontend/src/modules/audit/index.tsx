/**
 * AZALSCORE Module - Audit & Benchmark
 * Logs d'audit, sessions, metriques, benchmarks, conformite
 * Donnees fournies par API - AUCUNE logique metier
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Search,
  Download,
  RefreshCw,
  Clock,
  User,
  Shield,
  Activity,
  BarChart3,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  Database,
  Play,
  Eye,
  Settings,
  Filter,
  Calendar,
} from 'lucide-react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { Button, ButtonGroup } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn, DashboardKPI } from '@/types';
import { formatDate } from '@/utils/formatters';
import {
  AUDIT_ACTION_LABELS,
  AUDIT_LEVEL_CONFIG,
  AUDIT_CATEGORY_LABELS,
  BENCHMARK_STATUS_CONFIG,
  COMPLIANCE_STATUS_CONFIG,
  COMPLIANCE_FRAMEWORK_LABELS,
} from './types';
import type {
  AuditLog,
  AuditLogListResponse,
  AuditLogFilters,
  AuditSession,
  AuditDashboardResponse,
  AuditStats,
  Metric,
  MetricValue,
  Benchmark,
  BenchmarkResult,
  ComplianceCheck,
  ComplianceSummary,
  RetentionRule,
  AuditExport,
} from './types';

// ============================================================
// API HOOKS
// ============================================================

const useAuditDashboard = () => {
  return useQuery({
    queryKey: ['audit', 'dashboard'],
    queryFn: async () => {
      const response = await api.get<AuditDashboardResponse>('/audit/dashboard');
      return response.data;
    },
  });
};

const _useAuditStats = () => {
  return useQuery({
    queryKey: ['audit', 'stats'],
    queryFn: async () => {
      const response = await api.get<AuditStats>('/audit/stats');
      return response.data;
    },
  });
};

const useAuditLogs = (filters?: AuditLogFilters) => {
  return useQuery({
    queryKey: ['audit', 'logs', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.action) params.append('action', filters.action);
      if (filters?.level) params.append('level', filters.level);
      if (filters?.category) params.append('category', filters.category);
      if (filters?.module) params.append('module', filters.module);
      if (filters?.entity_type) params.append('entity_type', filters.entity_type);
      if (filters?.entity_id) params.append('entity_id', filters.entity_id);
      if (filters?.user_id) params.append('user_id', filters.user_id);
      if (filters?.session_id) params.append('session_id', filters.session_id);
      if (filters?.success !== undefined) params.append('success', String(filters.success));
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.search_text) params.append('search_text', filters.search_text);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.page_size) params.append('page_size', String(filters.page_size));

      const url = `/audit/logs${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<AuditLogListResponse>(url);
      return response.data;
    },
  });
};

const useAuditLog = (id: string) => {
  return useQuery({
    queryKey: ['audit', 'log', id],
    queryFn: async () => {
      const response = await api.get<AuditLog>(`/audit/logs/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

const _useEntityHistory = (entityType: string, entityId: string) => {
  return useQuery({
    queryKey: ['audit', 'entity-history', entityType, entityId],
    queryFn: async () => {
      const response = await api.get<AuditLog[]>(`/audit/logs/entity/${entityType}/${entityId}`);
      return response.data;
    },
    enabled: !!entityType && !!entityId,
  });
};

const _useUserActivity = (userId: string) => {
  return useQuery({
    queryKey: ['audit', 'user-activity', userId],
    queryFn: async () => {
      const response = await api.get<AuditLog[]>(`/audit/logs/user/${userId}`);
      return response.data;
    },
    enabled: !!userId,
  });
};

const useActiveSessions = () => {
  return useQuery({
    queryKey: ['audit', 'sessions'],
    queryFn: async () => {
      const response = await api.get<AuditSession[]>('/audit/sessions');
      return response.data;
    },
  });
};

const _useMetrics = (module?: string) => {
  return useQuery({
    queryKey: ['audit', 'metrics', module],
    queryFn: async () => {
      const url = module ? `/audit/metrics?module=${module}` : '/audit/metrics';
      const response = await api.get<Metric[]>(url);
      return response.data;
    },
  });
};

const _useMetricValues = (metricCode: string, fromDate?: string, toDate?: string) => {
  return useQuery({
    queryKey: ['audit', 'metric-values', metricCode, fromDate, toDate],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);
      const url = `/audit/metrics/${metricCode}/values${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<MetricValue[]>(url);
      return response.data;
    },
    enabled: !!metricCode,
  });
};

const useBenchmarks = (benchmarkType?: string) => {
  return useQuery({
    queryKey: ['audit', 'benchmarks', benchmarkType],
    queryFn: async () => {
      const url = benchmarkType ? `/audit/benchmarks?benchmark_type=${benchmarkType}` : '/audit/benchmarks';
      const response = await api.get<Benchmark[]>(url);
      return response.data;
    },
  });
};

const _useBenchmarkResults = (benchmarkId: string) => {
  return useQuery({
    queryKey: ['audit', 'benchmark-results', benchmarkId],
    queryFn: async () => {
      const response = await api.get<BenchmarkResult[]>(`/audit/benchmarks/${benchmarkId}/results`);
      return response.data;
    },
    enabled: !!benchmarkId,
  });
};

const useComplianceChecks = (framework?: string, status?: string) => {
  return useQuery({
    queryKey: ['audit', 'compliance-checks', framework, status],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (framework) params.append('framework', framework);
      if (status) params.append('status', status);
      const url = `/audit/compliance/checks${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<ComplianceCheck[]>(url);
      return response.data;
    },
  });
};

const useComplianceSummary = (framework?: string) => {
  return useQuery({
    queryKey: ['audit', 'compliance-summary', framework],
    queryFn: async () => {
      const url = framework ? `/audit/compliance/summary?framework=${framework}` : '/audit/compliance/summary';
      const response = await api.get<ComplianceSummary>(url);
      return response.data;
    },
  });
};

const _useRetentionRules = () => {
  return useQuery({
    queryKey: ['audit', 'retention-rules'],
    queryFn: async () => {
      const response = await api.get<RetentionRule[]>('/audit/retention/rules');
      return response.data;
    },
  });
};

const _useExports = () => {
  return useQuery({
    queryKey: ['audit', 'exports'],
    queryFn: async () => {
      const response = await api.get<AuditExport[]>('/audit/exports');
      return response.data;
    },
  });
};

// ============================================================
// MUTATIONS
// ============================================================

const useTerminateSession = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ sessionId, reason }: { sessionId: string; reason?: string }) => {
      const url = reason
        ? `/audit/sessions/${sessionId}/terminate?reason=${encodeURIComponent(reason)}`
        : `/audit/sessions/${sessionId}/terminate`;
      await api.post(url);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit', 'sessions'] });
      queryClient.invalidateQueries({ queryKey: ['audit', 'dashboard'] });
    },
  });
};

const useRunBenchmark = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (benchmarkId: string) => {
      const response = await api.post<BenchmarkResult>(`/audit/benchmarks/${benchmarkId}/run`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit', 'benchmarks'] });
      queryClient.invalidateQueries({ queryKey: ['audit', 'benchmark-results'] });
    },
  });
};

const _useApplyRetentionRules = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post('/audit/retention/apply');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit', 'retention-rules'] });
    },
  });
};

const _useCreateExport = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { export_type: string; format?: string; date_from?: string; date_to?: string }) => {
      const response = await api.post<AuditExport>('/audit/exports', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit', 'exports'] });
    },
  });
};

// ============================================================
// AUDIT DASHBOARD
// ============================================================

export const AuditDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: dashboard, isLoading } = useAuditDashboard();

  if (isLoading || !dashboard) {
    return (
      <PageWrapper title="Audit & Benchmark">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  const { stats } = dashboard;

  const kpis: DashboardKPI[] = [
    {
      id: 'logs_24h',
      label: 'Logs (24h)',
      value: stats.total_logs_24h,
      icon: <Activity size={20} />,
    },
    {
      id: 'failed_24h',
      label: 'Echecs (24h)',
      value: stats.failed_24h,
      icon: <XCircle size={20} />,
      severity: stats.failed_24h > 10 ? 'RED' : stats.failed_24h > 0 ? 'ORANGE' : 'GREEN',
    },
    {
      id: 'active_sessions',
      label: 'Sessions actives',
      value: stats.active_sessions,
      icon: <User size={20} />,
    },
    {
      id: 'unique_users',
      label: 'Utilisateurs (24h)',
      value: stats.unique_users_24h,
      icon: <User size={20} />,
    },
  ];

  return (
    <PageWrapper
      title="Audit & Benchmark"
      subtitle="Surveillance, metriques et conformite"
      actions={
        <ButtonGroup>
          <Button variant="ghost" onClick={() => navigate('/audit/logs')}>
            <Search size={16} />
            Rechercher
          </Button>
          <CapabilityGuard capability="audit.exports.create">
            <Button variant="ghost" leftIcon={<Download size={16} />} onClick={() => navigate('/audit/exports')}>
              Exports
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      }
    >
      {/* KPIs */}
      <section className="azals-section">
        <Grid cols={4} gap="md">
          {kpis.map((kpi) => (
            <KPICard key={kpi.id} kpi={kpi} />
          ))}
        </Grid>
      </section>

      {/* Stats par action/module */}
      <section className="azals-section">
        <Grid cols={3} gap="md">
          <Card title="Par action" icon={<Activity size={20} />}>
            {stats.logs_by_action ? (
              <div className="azals-stats-list">
                {Object.entries(stats.logs_by_action)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 5)
                  .map(([action, count]) => (
                    <div key={action} className="azals-stats-item">
                      <span>{AUDIT_ACTION_LABELS[action as keyof typeof AUDIT_ACTION_LABELS] || action}</span>
                      <strong>{count}</strong>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="azals-text--muted">Aucune donnee</p>
            )}
          </Card>

          <Card title="Par module" icon={<Database size={20} />}>
            {stats.logs_by_module ? (
              <div className="azals-stats-list">
                {Object.entries(stats.logs_by_module)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 5)
                  .map(([module, count]) => (
                    <div key={module} className="azals-stats-item">
                      <span>{module}</span>
                      <strong>{count}</strong>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="azals-text--muted">Aucune donnee</p>
            )}
          </Card>

          <Card title="Par niveau" icon={<AlertTriangle size={20} />}>
            {stats.logs_by_level ? (
              <div className="azals-stats-list">
                {Object.entries(stats.logs_by_level).map(([level, count]) => {
                  const config = AUDIT_LEVEL_CONFIG[level as keyof typeof AUDIT_LEVEL_CONFIG];
                  return (
                    <div key={level} className="azals-stats-item">
                      <span className={`azals-badge azals-badge--${config?.color || 'gray'}`}>
                        {config?.label || level}
                      </span>
                      <strong>{count}</strong>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="azals-text--muted">Aucune donnee</p>
            )}
          </Card>
        </Grid>
      </section>

      {/* Logs récents */}
      <section className="azals-section">
        <Card
          title="Logs recents"
          icon={<Clock size={20} />}
          actions={
            <Button variant="ghost" size="sm" onClick={() => navigate('/audit/logs')}>
              Voir tout
            </Button>
          }
        >
          <RecentLogsList logs={dashboard.recent_logs} />
        </Card>
      </section>

      {/* Sessions actives */}
      <section className="azals-section">
        <Card
          title="Sessions actives"
          icon={<User size={20} />}
          actions={
            <Button variant="ghost" size="sm" onClick={() => navigate('/audit/sessions')}>
              Voir tout
            </Button>
          }
        >
          {dashboard.active_sessions.length > 0 ? (
            <div className="azals-list">
              {dashboard.active_sessions.slice(0, 5).map((session) => (
                <div key={session.id} className="azals-list-item">
                  <div className="azals-list-item__content">
                    <strong>{session.user_email || 'Utilisateur inconnu'}</strong>
                    <span className="azals-text--muted">
                      {session.ip_address} - {session.browser} / {session.os}
                    </span>
                  </div>
                  <span className="azals-text--muted">{session.actions_count} actions</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="azals-text--muted">Aucune session active</p>
          )}
        </Card>
      </section>

      {/* Conformité */}
      {dashboard.compliance_summary && (
        <section className="azals-section">
          <Card title="Conformite" icon={<Shield size={20} />}>
            <div className="azals-compliance-summary">
              <div className="azals-compliance-rate">
                <span className="azals-compliance-rate__value">
                  {Math.round(dashboard.compliance_summary.compliance_rate * 100)}%
                </span>
                <span className="azals-compliance-rate__label">Taux de conformite</span>
              </div>
              <div className="azals-stats-list">
                <div className="azals-stats-item">
                  <span className="azals-badge azals-badge--green">Conforme</span>
                  <strong>{dashboard.compliance_summary.compliant}</strong>
                </div>
                <div className="azals-stats-item">
                  <span className="azals-badge azals-badge--red">Non conforme</span>
                  <strong>{dashboard.compliance_summary.non_compliant}</strong>
                </div>
                <div className="azals-stats-item">
                  <span className="azals-badge azals-badge--gray">En attente</span>
                  <strong>{dashboard.compliance_summary.pending}</strong>
                </div>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="azals-mt-3"
              onClick={() => navigate('/audit/compliance')}
            >
              Voir les controles
            </Button>
          </Card>
        </section>
      )}

      {/* Navigation rapide */}
      <section className="azals-section">
        <Grid cols={4} gap="md">
          <Card
            title="Metriques"
            subtitle="Indicateurs de performance"
            icon={<BarChart3 size={20} />}
            onClick={() => navigate('/audit/metrics')}
          >
            <span />
          </Card>
          <Card
            title="Benchmarks"
            subtitle="Tests de performance"
            icon={<Activity size={20} />}
            onClick={() => navigate('/audit/benchmarks')}
          >
            <span />
          </Card>
          <Card
            title="Retention"
            subtitle="Regles de conservation"
            icon={<Database size={20} />}
            onClick={() => navigate('/audit/retention')}
          >
            <span />
          </Card>
          <Card
            title="Exports"
            subtitle="Telecharger les donnees"
            icon={<Download size={20} />}
            onClick={() => navigate('/audit/exports')}
          >
            <span />
          </Card>
        </Grid>
      </section>
    </PageWrapper>
  );
};

// ============================================================
// RECENT LOGS LIST COMPONENT
// ============================================================

const RecentLogsList: React.FC<{ logs: AuditLog[] }> = ({ logs }) => {
  const navigate = useNavigate();

  if (logs.length === 0) {
    return <p className="azals-text--muted">Aucun log recent</p>;
  }

  return (
    <div className="azals-list">
      {logs.map((log) => {
        const levelConfig = AUDIT_LEVEL_CONFIG[log.level];
        return (
          <div
            key={log.id}
            className="azals-list-item azals-list-item--clickable"
            onClick={() => navigate(`/audit/logs/${log.id}`)}
          >
            <div className="azals-list-item__icon">
              {log.success ? (
                <CheckCircle size={16} className="azals-text--success" />
              ) : (
                <XCircle size={16} className="azals-text--danger" />
              )}
            </div>
            <div className="azals-list-item__content">
              <div className="azals-list-item__header">
                <span className={`azals-badge azals-badge--${levelConfig.color}`}>
                  {AUDIT_ACTION_LABELS[log.action] || log.action}
                </span>
                <span className="azals-text--muted">{log.module}</span>
              </div>
              <p className="azals-list-item__description">
                {log.description || `${log.entity_type || ''} ${log.entity_id || ''}`}
              </p>
            </div>
            <div className="azals-list-item__meta">
              <span className="azals-text--muted">{formatDate(log.created_at)}</span>
              {log.user_email && <span className="azals-text--muted">{log.user_email}</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ============================================================
// LOGS PAGE
// ============================================================

export const LogsPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const { data, isLoading, error, refetch } = useAuditLogs({ page, page_size: pageSize });

  const columns: TableColumn<AuditLog>[] = [
    {
      id: 'created_at',
      header: 'Date',
      accessor: 'created_at',
      sortable: true,
      render: (value) => formatDate(value as string),
    },
    {
      id: 'action',
      header: 'Action',
      accessor: 'action',
      render: (value) => AUDIT_ACTION_LABELS[value as keyof typeof AUDIT_ACTION_LABELS] || String(value),
    },
    {
      id: 'level',
      header: 'Niveau',
      accessor: 'level',
      render: (value) => {
        const config = AUDIT_LEVEL_CONFIG[value as keyof typeof AUDIT_LEVEL_CONFIG];
        return <span className={`azals-badge azals-badge--${config?.color || 'gray'}`}>{config?.label || String(value)}</span>;
      },
    },
    {
      id: 'module',
      header: 'Module',
      accessor: 'module',
    },
    {
      id: 'user_email',
      header: 'Utilisateur',
      accessor: 'user_email',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'success',
      header: 'Resultat',
      accessor: 'success',
      render: (value) =>
        value ? (
          <CheckCircle size={16} className="azals-text--success" />
        ) : (
          <XCircle size={16} className="azals-text--danger" />
        ),
    },
    {
      id: 'description',
      header: 'Description',
      accessor: 'description',
      render: (value) => (
        <span className="azals-text--truncate" style={{ maxWidth: 200 }}>
          {(value as string) || '-'}
        </span>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Logs d'audit"
      subtitle={data ? `${data.total} logs au total` : ''}
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<Filter size={16} />}>
            Filtrer
          </Button>
          <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
            Actualiser
          </Button>
        </ButtonGroup>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.logs || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          onRowClick={(row) => navigate(`/audit/logs/${row.id}`)}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          emptyMessage="Aucun log"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// LOG DETAIL PAGE
// ============================================================

export const LogDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: log, isLoading, error } = useAuditLog(id!);

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">Chargement du log...</div>
      </PageWrapper>
    );
  }

  if (error || !log) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <p className="text-danger">Impossible de charger le log.</p>
          <Button variant="secondary" onClick={() => navigate('/audit/logs')} className="mt-4">
            Retour
          </Button>
        </Card>
      </PageWrapper>
    );
  }

  const levelConfig = AUDIT_LEVEL_CONFIG[log.level];

  return (
    <PageWrapper
      title={`Log ${log.id.slice(0, 8)}`}
      subtitle={`${AUDIT_ACTION_LABELS[log.action]} - ${log.module}`}
      backAction={{
        label: 'Retour',
        onClick: () => navigate('/audit/logs'),
      }}
    >
      {/* Statut */}
      <section className="azals-section">
        <div className="azals-status-bar">
          <span className={`azals-badge azals-badge--${levelConfig.color} azals-badge--lg`}>
            {levelConfig.label}
          </span>
          <span className={`azals-badge azals-badge--${log.success ? 'green' : 'red'}`}>
            {log.success ? 'Succes' : 'Echec'}
          </span>
          <span className="azals-text--muted">{formatDate(log.created_at)}</span>
        </div>
      </section>

      {/* Informations */}
      <section className="azals-section">
        <Grid cols={2} gap="md">
          <Card title="Details">
            <div className="azals-info-list">
              <div className="azals-info-item">
                <span>Action</span>
                <strong>{AUDIT_ACTION_LABELS[log.action]}</strong>
              </div>
              <div className="azals-info-item">
                <span>Categorie</span>
                <strong>{AUDIT_CATEGORY_LABELS[log.category]}</strong>
              </div>
              <div className="azals-info-item">
                <span>Module</span>
                <strong>{log.module}</strong>
              </div>
              {log.entity_type && (
                <div className="azals-info-item">
                  <span>Entite</span>
                  <strong>
                    {log.entity_type} {log.entity_id && `#${log.entity_id}`}
                  </strong>
                </div>
              )}
              {log.duration_ms && (
                <div className="azals-info-item">
                  <span>Duree</span>
                  <strong>{log.duration_ms.toFixed(2)} ms</strong>
                </div>
              )}
            </div>
          </Card>

          <Card title="Contexte">
            <div className="azals-info-list">
              {log.user_email && (
                <div className="azals-info-item">
                  <span>Utilisateur</span>
                  <strong>{log.user_email}</strong>
                </div>
              )}
              {log.user_role && (
                <div className="azals-info-item">
                  <span>Role</span>
                  <strong>{log.user_role}</strong>
                </div>
              )}
              {log.ip_address && (
                <div className="azals-info-item">
                  <span>Adresse IP</span>
                  <strong>{log.ip_address}</strong>
                </div>
              )}
              {log.session_id && (
                <div className="azals-info-item">
                  <span>Session</span>
                  <code>{log.session_id.slice(0, 12)}...</code>
                </div>
              )}
              {log.request_id && (
                <div className="azals-info-item">
                  <span>Request ID</span>
                  <code>{log.request_id.slice(0, 12)}...</code>
                </div>
              )}
            </div>
          </Card>
        </Grid>
      </section>

      {/* Description et erreur */}
      {(log.description || log.error_message) && (
        <section className="azals-section">
          <Grid cols={2} gap="md">
            {log.description && (
              <Card title="Description">
                <p>{log.description}</p>
              </Card>
            )}
            {log.error_message && (
              <Card title="Erreur">
                <p className="azals-text--danger">{log.error_message}</p>
                {log.error_code && (
                  <code className="azals-code">{log.error_code}</code>
                )}
              </Card>
            )}
          </Grid>
        </section>
      )}

      {/* Valeurs */}
      {(log.old_value || log.new_value || log.diff) && (
        <section className="azals-section">
          <Grid cols={log.diff ? 3 : 2} gap="md">
            {log.old_value && (
              <Card title="Ancienne valeur">
                <pre className="azals-code-block">{JSON.stringify(log.old_value, null, 2)}</pre>
              </Card>
            )}
            {log.new_value && (
              <Card title="Nouvelle valeur">
                <pre className="azals-code-block">{JSON.stringify(log.new_value, null, 2)}</pre>
              </Card>
            )}
            {log.diff && (
              <Card title="Differences">
                <pre className="azals-code-block">{JSON.stringify(log.diff, null, 2)}</pre>
              </Card>
            )}
          </Grid>
        </section>
      )}
    </PageWrapper>
  );
};

// ============================================================
// SESSIONS PAGE
// ============================================================

export const SessionsPage: React.FC = () => {
  const { data, isLoading, error, refetch } = useActiveSessions();
  const terminateSession = useTerminateSession();

  const columns: TableColumn<AuditSession>[] = [
    {
      id: 'user_email',
      header: 'Utilisateur',
      accessor: 'user_email',
      render: (value) => (value as string) || 'Inconnu',
    },
    {
      id: 'login_at',
      header: 'Connexion',
      accessor: 'login_at',
      render: (value) => formatDate(value as string),
    },
    {
      id: 'last_activity_at',
      header: 'Derniere activite',
      accessor: 'last_activity_at',
      render: (value) => formatDate(value as string),
    },
    {
      id: 'ip_address',
      header: 'IP',
      accessor: 'ip_address',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'browser',
      header: 'Navigateur',
      accessor: 'browser',
      render: (value, row) => `${(value as string) || '?'} / ${row.os || '?'}`,
    },
    {
      id: 'location',
      header: 'Localisation',
      accessor: 'country',
      render: (_, row) => (row.city && row.country ? `${row.city}, ${row.country}` : '-'),
    },
    {
      id: 'actions_count',
      header: 'Actions',
      accessor: 'actions_count',
      align: 'right',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <CapabilityGuard capability="audit.sessions.terminate">
          <Button
            size="sm"
            variant="danger"
            onClick={() => {
              if (window.confirm('Terminer cette session ?')) {
                terminateSession.mutate({ sessionId: row.session_id });
              }
            }}
            disabled={terminateSession.isPending}
          >
            Terminer
          </Button>
        </CapabilityGuard>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Sessions actives"
      subtitle={data ? `${data.length} sessions actives` : ''}
      actions={
        <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
          Actualiser
        </Button>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucune session active"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// BENCHMARKS PAGE
// ============================================================

export const BenchmarksPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useBenchmarks();
  const runBenchmark = useRunBenchmark();

  const columns: TableColumn<Benchmark>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      render: (value) => <code className="azals-code">{value as string}</code>,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
    },
    {
      id: 'benchmark_type',
      header: 'Type',
      accessor: 'benchmark_type',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => {
        const config = BENCHMARK_STATUS_CONFIG[value as keyof typeof BENCHMARK_STATUS_CONFIG];
        return <span className={`azals-badge azals-badge--${config?.color || 'gray'}`}>{config?.label || String(value)}</span>;
      },
    },
    {
      id: 'last_run_at',
      header: 'Dernier run',
      accessor: 'last_run_at',
      render: (value) => (value ? formatDate(value as string) : 'Jamais'),
    },
    {
      id: 'is_active',
      header: 'Actif',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <CheckCircle size={16} className="azals-text--success" />
        ) : (
          <XCircle size={16} className="azals-text--gray" />
        ),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <ButtonGroup>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => navigate(`/audit/benchmarks/${row.id}`)}
          >
            <Eye size={14} />
          </Button>
          <CapabilityGuard capability="audit.benchmarks.execute">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => runBenchmark.mutate(row.id)}
              disabled={runBenchmark.isPending || row.status === 'RUNNING'}
            >
              <Play size={14} />
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Benchmarks"
      subtitle="Tests de performance et securite"
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
            Actualiser
          </Button>
          <CapabilityGuard capability="audit.benchmarks.create">
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/audit/benchmarks/new')}>
              Nouveau
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucun benchmark"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// COMPLIANCE PAGE
// ============================================================

export const CompliancePage: React.FC = () => {
  const navigate = useNavigate();
  const { data: checks, isLoading, error, refetch } = useComplianceChecks();
  const { data: summary } = useComplianceSummary();

  const columns: TableColumn<ComplianceCheck>[] = [
    {
      id: 'framework',
      header: 'Referentiel',
      accessor: 'framework',
      render: (value) => COMPLIANCE_FRAMEWORK_LABELS[value as keyof typeof COMPLIANCE_FRAMEWORK_LABELS] || String(value),
    },
    {
      id: 'control_id',
      header: 'Controle',
      accessor: 'control_id',
      render: (value) => <code className="azals-code">{value as string}</code>,
    },
    {
      id: 'control_name',
      header: 'Nom',
      accessor: 'control_name',
    },
    {
      id: 'category',
      header: 'Categorie',
      accessor: 'category',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => {
        const config = COMPLIANCE_STATUS_CONFIG[value as keyof typeof COMPLIANCE_STATUS_CONFIG];
        return <span className={`azals-badge azals-badge--${config?.color || 'gray'}`}>{config?.label || String(value)}</span>;
      },
    },
    {
      id: 'severity',
      header: 'Severite',
      accessor: 'severity',
    },
    {
      id: 'last_checked_at',
      header: 'Derniere verif',
      accessor: 'last_checked_at',
      render: (value) => (value ? formatDate(value as string) : 'Jamais'),
    },
  ];

  return (
    <PageWrapper
      title="Conformite"
      subtitle={summary ? `${Math.round(summary.compliance_rate * 100)}% de conformite` : ''}
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
            Actualiser
          </Button>
          <CapabilityGuard capability="audit.compliance.create">
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/audit/compliance/new')}>
              Nouveau
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      }
    >
      {/* Résumé */}
      {summary && (
        <section className="azals-section">
          <Grid cols={4} gap="md">
            <Card>
              <div className="azals-stat">
                <span className="azals-stat__value">{summary.total}</span>
                <span className="azals-stat__label">Total</span>
              </div>
            </Card>
            <Card>
              <div className="azals-stat azals-stat--success">
                <span className="azals-stat__value">{summary.compliant}</span>
                <span className="azals-stat__label">Conformes</span>
              </div>
            </Card>
            <Card>
              <div className="azals-stat azals-stat--danger">
                <span className="azals-stat__value">{summary.non_compliant}</span>
                <span className="azals-stat__label">Non conformes</span>
              </div>
            </Card>
            <Card>
              <div className="azals-stat azals-stat--primary">
                <span className="azals-stat__value">{Math.round(summary.compliance_rate * 100)}%</span>
                <span className="azals-stat__label">Taux de conformite</span>
              </div>
            </Card>
          </Grid>
        </section>
      )}

      <Card noPadding>
        <DataTable
          columns={columns}
          data={checks || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucun controle de conformite"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// PLACEHOLDER PAGES
// ============================================================

const PlaceholderPage: React.FC<{ title: string }> = ({ title }) => (
  <PageWrapper title={title}>
    <Card>
      <p className="azals-text--muted">Cette page est en cours de developpement.</p>
    </Card>
  </PageWrapper>
);

// ============================================================
// MODULE ROUTES
// ============================================================

export const AuditRoutes: React.FC = () => (
  <Routes>
    <Route index element={<AuditDashboard />} />
    <Route path="logs" element={<LogsPage />} />
    <Route path="logs/:id" element={<LogDetailPage />} />
    <Route path="sessions" element={<SessionsPage />} />
    <Route path="metrics" element={<PlaceholderPage title="Metriques" />} />
    <Route path="metrics/:code" element={<PlaceholderPage title="Detail Metrique" />} />
    <Route path="benchmarks" element={<BenchmarksPage />} />
    <Route path="benchmarks/new" element={<PlaceholderPage title="Nouveau Benchmark" />} />
    <Route path="benchmarks/:id" element={<PlaceholderPage title="Detail Benchmark" />} />
    <Route path="compliance" element={<CompliancePage />} />
    <Route path="compliance/new" element={<PlaceholderPage title="Nouveau Controle" />} />
    <Route path="retention" element={<PlaceholderPage title="Regles de Retention" />} />
    <Route path="exports" element={<PlaceholderPage title="Exports" />} />
  </Routes>
);

export default AuditRoutes;
