/**
 * AZALSCORE Module - Audit Dashboard
 * Vue d'ensemble avec statistiques et KPIs
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, Download, Activity, XCircle, User, AlertTriangle,
  Database, Clock, Shield
} from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button, ButtonGroup } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import { PageWrapper, Card, Grid } from '@ui/layout';
import type { DashboardKPI } from '@/types';
import { useAuditDashboard } from '../hooks';
import {
  AUDIT_ACTION_LABELS,
  AUDIT_LEVEL_CONFIG,
} from '../types';
import { RecentLogsList } from './RecentLogsList';

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
            icon={<Activity size={20} />}
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

export default AuditDashboard;
