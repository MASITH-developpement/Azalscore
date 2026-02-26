/**
 * AZALSCORE Module - Triggers - Dashboard
 * Tableau de bord des triggers et diffusion
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus, Bell, AlertTriangle, Zap, FileText,
  Webhook, Users, Clock, Calendar, Activity
} from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button, ButtonGroup } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import { PageWrapper, Card, Grid } from '@ui/layout';
import type { DashboardKPI } from '@/types';
import { formatDate } from '@/utils/formatters';
import { REPORT_FREQUENCY_LABELS } from '../types';
import { useTriggerDashboard } from '../hooks';
import { RecentEventsList } from './RecentEventsList';

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

      {/* Stats detaillees */}
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

      {/* Evenements recents */}
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

export default TriggersDashboard;
