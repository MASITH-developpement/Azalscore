/**
 * AZALSCORE Module - Triggers & Diffusion
 * Gestion des déclencheurs, alertes, notifications et rapports planifiés
 * Données fournies par API - AUCUNE logique métier
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Bell,
  AlertTriangle,
  CheckCircle,
  Clock,
  Pause,
  Play,
  Zap,
  FileText,
  Webhook,
  Users,
  RefreshCw,
  Edit,
  Trash2,
  Eye,
  Calendar,
  Activity,
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
  TRIGGER_TYPE_LABELS,
  TRIGGER_STATUS_CONFIG,
  ALERT_SEVERITY_CONFIG,
  NOTIFICATION_STATUS_CONFIG,
  REPORT_FREQUENCY_LABELS,
} from './types';
import type {
  Trigger,
  TriggerListResponse,
  TriggerDashboard,
  TriggerEvent,
  EventListResponse,
  Notification,
  NotificationListResponse,
  NotificationTemplate,
  ScheduledReport,
  WebhookEndpoint,
  TriggerLog,
  TriggerLogListResponse,
  TriggerFilters,
  EventFilters,
  TriggerCreateInput,
  TriggerUpdateInput,
} from './types';

// ============================================================
// API HOOKS
// ============================================================

const useTriggerDashboard = () => {
  return useQuery({
    queryKey: ['triggers', 'dashboard'],
    queryFn: async () => {
      const response = await api.get<TriggerDashboard>('/triggers/dashboard');
      return response.data;
    },
  });
};

const useTriggers = (filters?: TriggerFilters) => {
  return useQuery({
    queryKey: ['triggers', 'list', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.source_module) params.append('source_module', filters.source_module);
      if (filters?.trigger_type) params.append('trigger_type', filters.trigger_type);
      if (filters?.include_inactive) params.append('include_inactive', 'true');
      const url = `/triggers/${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<TriggerListResponse>(url);
      return response.data;
    },
  });
};

const useTrigger = (id: string) => {
  return useQuery({
    queryKey: ['triggers', 'detail', id],
    queryFn: async () => {
      const response = await api.get<Trigger>(`/triggers/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

const useEvents = (filters?: EventFilters) => {
  return useQuery({
    queryKey: ['triggers', 'events', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.trigger_id) params.append('trigger_id', filters.trigger_id);
      if (filters?.resolved !== undefined) params.append('resolved', String(filters.resolved));
      if (filters?.severity) params.append('severity', filters.severity);
      if (filters?.from_date) params.append('from_date', filters.from_date);
      if (filters?.to_date) params.append('to_date', filters.to_date);
      if (filters?.limit) params.append('limit', String(filters.limit));
      const url = `/triggers/events${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<EventListResponse>(url);
      return response.data;
    },
  });
};

const useMyNotifications = (unreadOnly = false) => {
  return useQuery({
    queryKey: ['triggers', 'notifications', unreadOnly],
    queryFn: async () => {
      const response = await api.get<NotificationListResponse>(
        `/triggers/notifications?unread_only=${unreadOnly}`
      );
      return response.data;
    },
  });
};

const useTemplates = () => {
  return useQuery({
    queryKey: ['triggers', 'templates'],
    queryFn: async () => {
      const response = await api.get<NotificationTemplate[]>('/triggers/templates');
      return response.data;
    },
  });
};

const useScheduledReports = (includeInactive = false) => {
  return useQuery({
    queryKey: ['triggers', 'reports', includeInactive],
    queryFn: async () => {
      const response = await api.get<ScheduledReport[]>(
        `/triggers/reports?include_inactive=${includeInactive}`
      );
      return response.data;
    },
  });
};

const useWebhooks = () => {
  return useQuery({
    queryKey: ['triggers', 'webhooks'],
    queryFn: async () => {
      const response = await api.get<WebhookEndpoint[]>('/triggers/webhooks');
      return response.data;
    },
  });
};

const useTriggerLogs = (filters?: { action?: string; limit?: number }) => {
  return useQuery({
    queryKey: ['triggers', 'logs', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.action) params.append('action', filters.action);
      if (filters?.limit) params.append('limit', String(filters.limit));
      const url = `/triggers/logs${params.toString() ? '?' + params.toString() : ''}`;
      const response = await api.get<TriggerLogListResponse>(url);
      return response.data;
    },
  });
};

// ============================================================
// MUTATIONS
// ============================================================

const _useCreateTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: TriggerCreateInput) => {
      const response = await api.post<Trigger>('/triggers/', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

const _useUpdateTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TriggerUpdateInput }) => {
      const response = await api.put<Trigger>(`/triggers/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

const useDeleteTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/triggers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

const usePauseTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Trigger>(`/triggers/${id}/pause`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

const useResumeTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Trigger>(`/triggers/${id}/resume`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

const useFireTrigger = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data?: { triggered_value?: string } }) => {
      const response = await api.post<TriggerEvent>(`/triggers/${id}/fire`, data || {});
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers'] });
    },
  });
};

const useResolveEvent = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, notes }: { id: string; notes?: string }) => {
      const response = await api.post<TriggerEvent>(`/triggers/events/${id}/resolve`, {
        resolution_notes: notes,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers', 'events'] });
      queryClient.invalidateQueries({ queryKey: ['triggers', 'dashboard'] });
    },
  });
};

const useMarkNotificationRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Notification>(`/triggers/notifications/${id}/read`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers', 'notifications'] });
    },
  });
};

const useMarkAllNotificationsRead = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await api.post('/triggers/notifications/read-all');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['triggers', 'notifications'] });
    },
  });
};

// ============================================================
// TRIGGERS DASHBOARD
// ============================================================

export const TriggersDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: dashboard, isLoading } = useTriggerDashboard();

  if (isLoading || !dashboard) {
    return (
      <PageWrapper title="Triggers & Diffusion">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  const { stats } = dashboard;

  const kpis: DashboardKPI[] = [
    {
      id: 'active_triggers',
      label: 'Triggers actifs',
      value: stats.active_triggers,
      icon: <Zap size={20} />,
      severity: stats.active_triggers === 0 ? 'ORANGE' : 'GREEN',
    },
    {
      id: 'unresolved_events',
      label: 'Alertes non resolues',
      value: stats.unresolved_events,
      icon: <AlertTriangle size={20} />,
      severity: stats.unresolved_events > 10 ? 'RED' : stats.unresolved_events > 0 ? 'ORANGE' : 'GREEN',
    },
    {
      id: 'critical_events',
      label: 'Alertes critiques',
      value: stats.critical_events,
      icon: <AlertTriangle size={20} />,
      severity: stats.critical_events > 0 ? 'RED' : 'GREEN',
    },
    {
      id: 'notifications_24h',
      label: 'Notifications (24h)',
      value: stats.total_notifications_24h,
      icon: <Bell size={20} />,
    },
  ];

  return (
    <PageWrapper
      title="Triggers & Diffusion"
      subtitle="Gestion des alertes, notifications et rapports"
      actions={
        <ButtonGroup>
          <Button variant="ghost" onClick={() => navigate('/triggers/events')}>
            <Activity size={16} />
            Evenements
          </Button>
          <CapabilityGuard capability="triggers.create">
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/triggers/new')}>
              Nouveau Trigger
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

      {/* Stats détaillées */}
      <section className="azals-section">
        <Grid cols={3} gap="md">
          <Card title="Triggers" icon={<Zap size={20} />}>
            <div className="azals-stats-list">
              <div className="azals-stats-item">
                <span>Total</span>
                <strong>{stats.total_triggers}</strong>
              </div>
              <div className="azals-stats-item">
                <span>Actifs</span>
                <strong className="azals-text--success">{stats.active_triggers}</strong>
              </div>
              <div className="azals-stats-item">
                <span>En pause</span>
                <strong className="azals-text--warning">{stats.paused_triggers}</strong>
              </div>
              <div className="azals-stats-item">
                <span>Desactives</span>
                <strong className="azals-text--gray">{stats.disabled_triggers}</strong>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="azals-mt-3"
              onClick={() => navigate('/triggers/list')}
            >
              Voir tous les triggers
            </Button>
          </Card>

          <Card title="Notifications" icon={<Bell size={20} />}>
            <div className="azals-stats-list">
              <div className="azals-stats-item">
                <span>Envoyees (24h)</span>
                <strong>{stats.total_notifications_24h}</strong>
              </div>
              <div className="azals-stats-item">
                <span>En attente</span>
                <strong className="azals-text--warning">{stats.pending_notifications}</strong>
              </div>
              <div className="azals-stats-item">
                <span>Echouees</span>
                <strong className="azals-text--danger">{stats.failed_notifications}</strong>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="azals-mt-3"
              onClick={() => navigate('/triggers/notifications')}
            >
              Mes notifications
            </Button>
          </Card>

          <Card title="Rapports planifies" icon={<Calendar size={20} />}>
            <div className="azals-stats-list">
              <div className="azals-stats-item">
                <span>Actifs</span>
                <strong>{stats.scheduled_reports}</strong>
              </div>
              <div className="azals-stats-item">
                <span>Generes (24h)</span>
                <strong>{stats.reports_generated_24h}</strong>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="azals-mt-3"
              onClick={() => navigate('/triggers/reports')}
            >
              Voir les rapports
            </Button>
          </Card>
        </Grid>
      </section>

      {/* Événements récents */}
      <section className="azals-section">
        <Card
          title="Evenements recents"
          icon={<Activity size={20} />}
          actions={
            <Button variant="ghost" size="sm" onClick={() => navigate('/triggers/events')}>
              Voir tout
            </Button>
          }
        >
          <RecentEventsList events={dashboard.recent_events} />
        </Card>
      </section>

      {/* Prochains rapports */}
      {dashboard.upcoming_reports.length > 0 && (
        <section className="azals-section">
          <Card
            title="Prochains rapports"
            icon={<FileText size={20} />}
            actions={
              <Button variant="ghost" size="sm" onClick={() => navigate('/triggers/reports')}>
                Voir tout
              </Button>
            }
          >
            <div className="azals-list">
              {dashboard.upcoming_reports.map((report) => (
                <div key={report.id} className="azals-list-item">
                  <div className="azals-list-item__content">
                    <strong>{report.name}</strong>
                    <span className="azals-text--muted">
                      {REPORT_FREQUENCY_LABELS[report.frequency]} - {report.output_format}
                    </span>
                  </div>
                  {report.next_generation_at && (
                    <span className="azals-text--muted">
                      {formatDate(report.next_generation_at)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </section>
      )}

      {/* Navigation rapide */}
      <section className="azals-section">
        <Grid cols={4} gap="md">
          <Card
            title="Templates"
            subtitle="Modeles de notification"
            icon={<FileText size={20} />}
            onClick={() => navigate('/triggers/templates')}
          >
            <span />
          </Card>
          <Card
            title="Webhooks"
            subtitle="Endpoints externes"
            icon={<Webhook size={20} />}
            onClick={() => navigate('/triggers/webhooks')}
          >
            <span />
          </Card>
          <Card
            title="Abonnements"
            subtitle="Gerer les destinataires"
            icon={<Users size={20} />}
            onClick={() => navigate('/triggers/subscriptions')}
          >
            <span />
          </Card>
          <Card
            title="Logs"
            subtitle="Historique des actions"
            icon={<Clock size={20} />}
            onClick={() => navigate('/triggers/logs')}
          >
            <span />
          </Card>
        </Grid>
      </section>
    </PageWrapper>
  );
};

// ============================================================
// RECENT EVENTS LIST COMPONENT
// ============================================================

const RecentEventsList: React.FC<{ events: TriggerEvent[] }> = ({ events }) => {
  const navigate = useNavigate();
  const resolveEvent = useResolveEvent();

  if (events.length === 0) {
    return <p className="azals-text--muted">Aucun evenement recent</p>;
  }

  return (
    <div className="azals-events-list">
      {events.map((event) => {
        const severityConfig = ALERT_SEVERITY_CONFIG[event.severity];
        return (
          <div key={event.id} className="azals-event-item">
            <div
              className="azals-event-item__severity"
              style={{ backgroundColor: `var(--color-${severityConfig.color}-100)` }}
            >
              <AlertTriangle
                size={16}
                style={{ color: `var(--color-${severityConfig.color}-600)` }}
              />
            </div>
            <div className="azals-event-item__content">
              <div className="azals-event-item__header">
                <span className={`azals-badge azals-badge--${severityConfig.color}`}>
                  {severityConfig.label}
                </span>
                <span className="azals-text--muted">{formatDate(event.triggered_at)}</span>
              </div>
              <p className="azals-event-item__value">
                {event.triggered_value || 'Declenchement automatique'}
              </p>
            </div>
            <div className="azals-event-item__actions">
              {event.resolved ? (
                <span className="azals-badge azals-badge--green">
                  <CheckCircle size={12} /> Resolu
                </span>
              ) : (
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => resolveEvent.mutate({ id: event.id })}
                  disabled={resolveEvent.isPending}
                >
                  Resoudre
                </Button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ============================================================
// TRIGGERS LIST PAGE
// ============================================================

export const TriggersListPage: React.FC = () => {
  const navigate = useNavigate();
  const [includeInactive, setIncludeInactive] = useState(false);
  const { data, isLoading, error, refetch } = useTriggers({ include_inactive: includeInactive });
  const pauseTrigger = usePauseTrigger();
  const resumeTrigger = useResumeTrigger();
  const deleteTrigger = useDeleteTrigger();

  const columns: TableColumn<Trigger>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      sortable: true,
      render: (value) => <code className="azals-code">{value as string}</code>,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      sortable: true,
    },
    {
      id: 'trigger_type',
      header: 'Type',
      accessor: 'trigger_type',
      render: (value) => TRIGGER_TYPE_LABELS[value as keyof typeof TRIGGER_TYPE_LABELS],
    },
    {
      id: 'source_module',
      header: 'Module source',
      accessor: 'source_module',
    },
    {
      id: 'severity',
      header: 'Severite',
      accessor: 'severity',
      render: (value) => {
        const config = ALERT_SEVERITY_CONFIG[value as keyof typeof ALERT_SEVERITY_CONFIG];
        return <span className={`azals-badge azals-badge--${config.color}`}>{config.label}</span>;
      },
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => {
        const config = TRIGGER_STATUS_CONFIG[value as keyof typeof TRIGGER_STATUS_CONFIG];
        return <span className={`azals-badge azals-badge--${config.color}`}>{config.label}</span>;
      },
    },
    {
      id: 'trigger_count',
      header: 'Declenchements',
      accessor: 'trigger_count',
      align: 'right',
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
            onClick={() => navigate(`/triggers/${row.id}`)}
          >
            <Eye size={14} />
          </Button>
          {row.status === 'ACTIVE' ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => pauseTrigger.mutate(row.id)}
              disabled={pauseTrigger.isPending}
            >
              <Pause size={14} />
            </Button>
          ) : row.status === 'PAUSED' ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => resumeTrigger.mutate(row.id)}
              disabled={resumeTrigger.isPending}
            >
              <Play size={14} />
            </Button>
          ) : null}
          <CapabilityGuard capability="triggers.delete">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                if (window.confirm('Supprimer ce trigger ?')) {
                  deleteTrigger.mutate(row.id);
                }
              }}
              disabled={deleteTrigger.isPending}
            >
              <Trash2 size={14} />
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Triggers"
      subtitle="Liste des declencheurs configures"
      actions={
        <ButtonGroup>
          <Button
            variant={includeInactive ? 'secondary' : 'ghost'}
            onClick={() => setIncludeInactive(!includeInactive)}
          >
            {includeInactive ? 'Masquer inactifs' : 'Afficher inactifs'}
          </Button>
          <CapabilityGuard capability="triggers.create">
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/triggers/new')}>
              Nouveau
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.triggers || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          onRowClick={(row) => navigate(`/triggers/${row.id}`)}
          emptyMessage="Aucun trigger configure"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// TRIGGER DETAIL PAGE
// ============================================================

export const TriggerDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: trigger, isLoading, error, refetch } = useTrigger(id!);
  const pauseTrigger = usePauseTrigger();
  const resumeTrigger = useResumeTrigger();
  const fireTrigger = useFireTrigger();

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">Chargement du trigger...</div>
      </PageWrapper>
    );
  }

  if (error || !trigger) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <p className="text-danger">Impossible de charger le trigger.</p>
          <Button variant="secondary" onClick={() => navigate('/triggers/list')} className="mt-4">
            Retour
          </Button>
        </Card>
      </PageWrapper>
    );
  }

  const statusConfig = TRIGGER_STATUS_CONFIG[trigger.status];
  const severityConfig = ALERT_SEVERITY_CONFIG[trigger.severity];

  return (
    <PageWrapper
      title={trigger.name}
      subtitle={`Code: ${trigger.code}`}
      backAction={{
        label: 'Retour',
        onClick: () => navigate('/triggers/list'),
      }}
      actions={
        <ButtonGroup>
          {trigger.status === 'ACTIVE' ? (
            <Button
              variant="secondary"
              leftIcon={<Pause size={16} />}
              onClick={() => pauseTrigger.mutate(trigger.id)}
              disabled={pauseTrigger.isPending}
            >
              Pause
            </Button>
          ) : trigger.status === 'PAUSED' ? (
            <Button
              variant="secondary"
              leftIcon={<Play size={16} />}
              onClick={() => resumeTrigger.mutate(trigger.id)}
              disabled={resumeTrigger.isPending}
            >
              Reprendre
            </Button>
          ) : null}
          <CapabilityGuard capability="triggers.admin">
            <Button
              variant="secondary"
              leftIcon={<Zap size={16} />}
              onClick={() => fireTrigger.mutate({ id: trigger.id })}
              disabled={fireTrigger.isPending}
            >
              Declencher
            </Button>
          </CapabilityGuard>
          <CapabilityGuard capability="triggers.update">
            <Button
              leftIcon={<Edit size={16} />}
              onClick={() => navigate(`/triggers/${trigger.id}/edit`)}
            >
              Modifier
            </Button>
          </CapabilityGuard>
        </ButtonGroup>
      }
    >
      {/* Statut */}
      <section className="azals-section">
        <div className="azals-status-bar">
          <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--lg`}>
            {statusConfig.label}
          </span>
          <span className={`azals-badge azals-badge--${severityConfig.color}`}>
            {severityConfig.label}
          </span>
          <span className="azals-text--muted">
            {trigger.trigger_count} declenchements
          </span>
          {trigger.last_triggered_at && (
            <span className="azals-text--muted">
              Dernier: {formatDate(trigger.last_triggered_at)}
            </span>
          )}
        </div>
      </section>

      {/* Informations */}
      <section className="azals-section">
        <Grid cols={2} gap="md">
          <Card title="Configuration">
            <div className="azals-info-list">
              <div className="azals-info-item">
                <span>Type</span>
                <strong>{TRIGGER_TYPE_LABELS[trigger.trigger_type]}</strong>
              </div>
              <div className="azals-info-item">
                <span>Module source</span>
                <strong>{trigger.source_module}</strong>
              </div>
              {trigger.source_entity && (
                <div className="azals-info-item">
                  <span>Entite</span>
                  <strong>{trigger.source_entity}</strong>
                </div>
              )}
              {trigger.source_field && (
                <div className="azals-info-item">
                  <span>Champ</span>
                  <strong>{trigger.source_field}</strong>
                </div>
              )}
              {trigger.threshold_value && (
                <div className="azals-info-item">
                  <span>Seuil</span>
                  <strong>
                    {trigger.threshold_operator} {trigger.threshold_value}
                  </strong>
                </div>
              )}
              {trigger.schedule_cron && (
                <div className="azals-info-item">
                  <span>Planification</span>
                  <code>{trigger.schedule_cron}</code>
                </div>
              )}
            </div>
          </Card>

          <Card title="Escalade">
            <div className="azals-info-list">
              <div className="azals-info-item">
                <span>Escalade activee</span>
                <strong>{trigger.escalation_enabled ? 'Oui' : 'Non'}</strong>
              </div>
              {trigger.escalation_enabled && (
                <>
                  <div className="azals-info-item">
                    <span>Delai d'escalade</span>
                    <strong>{trigger.escalation_delay_minutes} minutes</strong>
                  </div>
                  {trigger.escalation_level && (
                    <div className="azals-info-item">
                      <span>Niveau actuel</span>
                      <strong>{trigger.escalation_level}</strong>
                    </div>
                  )}
                </>
              )}
              <div className="azals-info-item">
                <span>Cooldown</span>
                <strong>{trigger.cooldown_minutes} minutes</strong>
              </div>
            </div>
          </Card>
        </Grid>
      </section>

      {/* Condition */}
      <section className="azals-section">
        <Card title="Condition">
          <pre className="azals-code-block">
            {JSON.stringify(trigger.condition, null, 2)}
          </pre>
        </Card>
      </section>

      {/* Description */}
      {trigger.description && (
        <section className="azals-section">
          <Card title="Description">
            <p>{trigger.description}</p>
          </Card>
        </section>
      )}

      {/* Métadonnées */}
      <section className="azals-section">
        <Card title="Informations">
          <div className="azals-info-list azals-info-list--horizontal">
            <div className="azals-info-item">
              <span>Cree le</span>
              <strong>{formatDate(trigger.created_at)}</strong>
            </div>
            <div className="azals-info-item">
              <span>Modifie le</span>
              <strong>{formatDate(trigger.updated_at)}</strong>
            </div>
          </div>
        </Card>
      </section>
    </PageWrapper>
  );
};

// ============================================================
// EVENTS PAGE
// ============================================================

export const EventsPage: React.FC = () => {
  const navigate = useNavigate();
  const [showResolved, setShowResolved] = useState(false);
  const { data, isLoading, error, refetch } = useEvents({
    resolved: showResolved ? undefined : false,
    limit: 100,
  });
  const resolveEvent = useResolveEvent();

  const columns: TableColumn<TriggerEvent>[] = [
    {
      id: 'triggered_at',
      header: 'Date',
      accessor: 'triggered_at',
      sortable: true,
      render: (value) => formatDate(value as string),
    },
    {
      id: 'severity',
      header: 'Severite',
      accessor: 'severity',
      render: (value) => {
        const config = ALERT_SEVERITY_CONFIG[value as keyof typeof ALERT_SEVERITY_CONFIG];
        return <span className={`azals-badge azals-badge--${config.color}`}>{config.label}</span>;
      },
    },
    {
      id: 'triggered_value',
      header: 'Valeur',
      accessor: 'triggered_value',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'escalation_level',
      header: 'Niveau',
      accessor: 'escalation_level',
    },
    {
      id: 'resolved',
      header: 'Statut',
      accessor: 'resolved',
      render: (value, row) =>
        value ? (
          <span className="azals-badge azals-badge--green">
            <CheckCircle size={12} /> Resolu
          </span>
        ) : (
          <span className="azals-badge azals-badge--orange">En cours</span>
        ),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <ButtonGroup>
          {!row.resolved && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => resolveEvent.mutate({ id: row.id })}
              disabled={resolveEvent.isPending}
            >
              Resoudre
            </Button>
          )}
        </ButtonGroup>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Evenements"
      subtitle="Historique des declenchements"
      actions={
        <ButtonGroup>
          <Button
            variant={showResolved ? 'secondary' : 'ghost'}
            onClick={() => setShowResolved(!showResolved)}
          >
            {showResolved ? 'Masquer resolus' : 'Afficher resolus'}
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
          data={data?.events || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucun evenement"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// NOTIFICATIONS PAGE
// ============================================================

export const NotificationsPage: React.FC = () => {
  const [unreadOnly, setUnreadOnly] = useState(false);
  const { data, isLoading, error, refetch } = useMyNotifications(unreadOnly);
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();

  const columns: TableColumn<Notification>[] = [
    {
      id: 'sent_at',
      header: 'Date',
      accessor: 'sent_at',
      sortable: true,
      render: (value) => (value ? formatDate(value as string) : '-'),
    },
    {
      id: 'channel',
      header: 'Canal',
      accessor: 'channel',
    },
    {
      id: 'subject',
      header: 'Sujet',
      accessor: 'subject',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => {
        const config = NOTIFICATION_STATUS_CONFIG[value as keyof typeof NOTIFICATION_STATUS_CONFIG];
        return <span className={`azals-badge azals-badge--${config.color}`}>{config.label}</span>;
      },
    },
    {
      id: 'read_at',
      header: 'Lu',
      accessor: 'read_at',
      render: (value) =>
        value ? (
          <CheckCircle size={16} className="azals-text--success" />
        ) : (
          <span className="azals-badge azals-badge--blue">Non lu</span>
        ),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <ButtonGroup>
          {!row.read_at && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => markRead.mutate(row.id)}
              disabled={markRead.isPending}
            >
              Marquer lu
            </Button>
          )}
        </ButtonGroup>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Mes notifications"
      subtitle={data ? `${data.unread_count} non lues` : ''}
      actions={
        <ButtonGroup>
          <Button
            variant={unreadOnly ? 'secondary' : 'ghost'}
            onClick={() => setUnreadOnly(!unreadOnly)}
          >
            {unreadOnly ? 'Toutes' : 'Non lues'}
          </Button>
          {data && data.unread_count > 0 && (
            <Button
              variant="secondary"
              onClick={() => markAllRead.mutate()}
              disabled={markAllRead.isPending}
            >
              Tout marquer lu
            </Button>
          )}
        </ButtonGroup>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.notifications || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucune notification"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// TEMPLATES PAGE
// ============================================================

export const TemplatesPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useTemplates();

  const columns: TableColumn<NotificationTemplate>[] = [
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
      id: 'is_system',
      header: 'Type',
      accessor: 'is_system',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--blue">Systeme</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Personnalise</span>
        ),
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Actif</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Inactif</span>
        ),
    },
  ];

  return (
    <PageWrapper
      title="Templates"
      subtitle="Modeles de notification"
      actions={
        <CapabilityGuard capability="triggers.templates.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/triggers/templates/new')}>
            Nouveau
          </Button>
        </CapabilityGuard>
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
          emptyMessage="Aucun template"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// SCHEDULED REPORTS PAGE
// ============================================================

export const ScheduledReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [includeInactive, setIncludeInactive] = useState(false);
  const { data, isLoading, error, refetch } = useScheduledReports(includeInactive);

  const columns: TableColumn<ScheduledReport>[] = [
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
      id: 'frequency',
      header: 'Frequence',
      accessor: 'frequency',
      render: (value) => REPORT_FREQUENCY_LABELS[value as keyof typeof REPORT_FREQUENCY_LABELS],
    },
    {
      id: 'output_format',
      header: 'Format',
      accessor: 'output_format',
    },
    {
      id: 'generation_count',
      header: 'Generations',
      accessor: 'generation_count',
      align: 'right',
    },
    {
      id: 'next_generation_at',
      header: 'Prochaine',
      accessor: 'next_generation_at',
      render: (value) => (value ? formatDate(value as string) : '-'),
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Actif</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Inactif</span>
        ),
    },
  ];

  return (
    <PageWrapper
      title="Rapports planifies"
      subtitle="Rapports periodiques automatiques"
      actions={
        <ButtonGroup>
          <Button
            variant={includeInactive ? 'secondary' : 'ghost'}
            onClick={() => setIncludeInactive(!includeInactive)}
          >
            {includeInactive ? 'Masquer inactifs' : 'Afficher inactifs'}
          </Button>
          <CapabilityGuard capability="triggers.reports.create">
            <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/triggers/reports/new')}>
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
          emptyMessage="Aucun rapport planifie"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// WEBHOOKS PAGE
// ============================================================

export const WebhooksPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useWebhooks();

  const columns: TableColumn<WebhookEndpoint>[] = [
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
      id: 'url',
      header: 'URL',
      accessor: 'url',
      render: (value) => (
        <span className="azals-text--muted azals-text--truncate" style={{ maxWidth: 200 }}>
          {value as string}
        </span>
      ),
    },
    {
      id: 'method',
      header: 'Methode',
      accessor: 'method',
    },
    {
      id: 'consecutive_failures',
      header: 'Echecs',
      accessor: 'consecutive_failures',
      align: 'right',
      render: (value) =>
        (value as number) > 0 ? (
          <span className="azals-text--danger">{value as number}</span>
        ) : (
          <span>0</span>
        ),
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Actif</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Inactif</span>
        ),
    },
  ];

  return (
    <PageWrapper
      title="Webhooks"
      subtitle="Endpoints de notification externes"
      actions={
        <CapabilityGuard capability="triggers.webhooks.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/triggers/webhooks/new')}>
            Nouveau
          </Button>
        </CapabilityGuard>
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
          emptyMessage="Aucun webhook"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// LOGS PAGE
// ============================================================

export const LogsPage: React.FC = () => {
  const { data, isLoading, error, refetch } = useTriggerLogs({ limit: 200 });

  const columns: TableColumn<TriggerLog>[] = [
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
    },
    {
      id: 'entity_type',
      header: 'Type',
      accessor: 'entity_type',
    },
    {
      id: 'success',
      header: 'Resultat',
      accessor: 'success',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Succes</span>
        ) : (
          <span className="azals-badge azals-badge--red">Echec</span>
        ),
    },
    {
      id: 'error_message',
      header: 'Erreur',
      accessor: 'error_message',
      render: (value) => (value ? <span className="azals-text--danger">{value as string}</span> : '-'),
    },
  ];

  return (
    <PageWrapper
      title="Logs"
      subtitle="Historique des actions du systeme de triggers"
      actions={
        <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
          Actualiser
        </Button>
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
          emptyMessage="Aucun log"
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

export const TriggersRoutes: React.FC = () => (
  <Routes>
    <Route index element={<TriggersDashboard />} />
    <Route path="list" element={<TriggersListPage />} />
    <Route path="new" element={<PlaceholderPage title="Nouveau Trigger" />} />
    <Route path=":id" element={<TriggerDetailPage />} />
    <Route path=":id/edit" element={<PlaceholderPage title="Modifier Trigger" />} />
    <Route path="events" element={<EventsPage />} />
    <Route path="notifications" element={<NotificationsPage />} />
    <Route path="templates" element={<TemplatesPage />} />
    <Route path="templates/new" element={<PlaceholderPage title="Nouveau Template" />} />
    <Route path="reports" element={<ScheduledReportsPage />} />
    <Route path="reports/new" element={<PlaceholderPage title="Nouveau Rapport" />} />
    <Route path="webhooks" element={<WebhooksPage />} />
    <Route path="webhooks/new" element={<PlaceholderPage title="Nouveau Webhook" />} />
    <Route path="subscriptions" element={<PlaceholderPage title="Abonnements" />} />
    <Route path="logs" element={<LogsPage />} />
  </Routes>
);

export default TriggersRoutes;
