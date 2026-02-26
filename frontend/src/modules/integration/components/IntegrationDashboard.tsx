/**
 * AZALS MODULE GAP-086 - Integration Hub - Dashboard
 * Tableau de bord principal des integrations
 */

import React from 'react';
import {
  Link2, Plug, RefreshCw, Database,
  Activity, Plus, AlertTriangle, AlertCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import { PageWrapper, Card, Grid } from '@ui/layout';
import type { DashboardKPI } from '@/types';
import { formatDate } from '@/utils/formatters';
import { CONNECTOR_CATEGORIES } from '../types';
import {
  useIntegrationStats, useConnections, useExecutions, useConflicts
} from '../hooks';
import {
  ConnectionStatusBadge, HealthStatusBadge, SyncStatusBadge, getCategoryIcon
} from './StatusBadges';

export interface IntegrationDashboardProps {
  onNavigateToConnectors: () => void;
  onNavigateToConnections: () => void;
  onNavigateToExecutions: () => void;
  onNavigateToConflicts: () => void;
  onSelectConnection: (id: string) => void;
  onCreateConnection: () => void;
}

export const IntegrationDashboard: React.FC<IntegrationDashboardProps> = ({
  onNavigateToConnectors,
  onNavigateToConnections,
  onNavigateToExecutions,
  onNavigateToConflicts,
  onSelectConnection,
  onCreateConnection,
}) => {
  const { data: stats } = useIntegrationStats();
  const { data: connections } = useConnections(1, 5);
  const { data: executions } = useExecutions(1, 5);
  const { data: conflicts } = useConflicts(1, 5, false);

  const kpis: DashboardKPI[] = stats ? [
    {
      id: 'connections',
      label: 'Connexions actives',
      value: `${stats.active_connections}/${stats.total_connections}`,
      icon: <Link2 size={20} />,
    },
    {
      id: 'executions',
      label: 'Sync. aujourd\'hui',
      value: stats.executions_today,
      icon: <RefreshCw size={20} />,
    },
    {
      id: 'records',
      label: 'Enregistrements sync.',
      value: new Intl.NumberFormat().format(stats.records_synced_today),
      icon: <Database size={20} />,
    },
    {
      id: 'success_rate',
      label: 'Taux de succes',
      value: `${stats.success_rate_today.toFixed(1)}%`,
      icon: <Activity size={20} />,
    },
  ] : [];

  return (
    <PageWrapper
      title="Integration Hub"
      subtitle="Gestion des integrations tierces"
      actions={
        <Button leftIcon={<Plus size={16} />} onClick={onCreateConnection}>
          Nouvelle connexion
        </Button>
      }
    >
      <section className="azals-section">
        <Grid cols={4} gap="md">
          {kpis.map(kpi => <KPICard key={kpi.id} kpi={kpi} />)}
        </Grid>
      </section>

      {stats && stats.error_connections > 0 && (
        <section className="azals-section">
          <Card className="azals-alert azals-alert--warning">
            <div className="azals-alert__content">
              <AlertTriangle size={20} />
              <span>
                <strong>{stats.error_connections}</strong> connexion(s) en erreur et{' '}
                <strong>{stats.pending_conflicts}</strong> conflit(s) en attente
              </span>
            </div>
            <Button variant="ghost" size="sm" onClick={onNavigateToConflicts}>
              Voir les conflits
            </Button>
          </Card>
        </section>
      )}

      <section className="azals-section">
        <Grid cols={2} gap="lg">
          <Card
            title="Connexions recentes"
            icon={<Link2 size={18} />}
            actions={
              <Button variant="ghost" size="sm" onClick={onNavigateToConnections}>
                Voir tout
              </Button>
            }
          >
            {connections?.items && connections.items.length > 0 ? (
              <ul className="azals-simple-list">
                {connections.items.map(conn => (
                  <li
                    key={conn.id}
                    onClick={() => onSelectConnection(conn.id)}
                    className="azals-clickable"
                  >
                    <div className="azals-list-item__main">
                      <strong>{conn.name}</strong>
                      <span className="text-muted ml-2">{conn.connector_type}</span>
                    </div>
                    <div className="azals-list-item__meta">
                      <ConnectionStatusBadge status={conn.status} />
                      <HealthStatusBadge status={conn.health_status} />
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted text-center py-4">Aucune connexion</p>
            )}
          </Card>

          <Card
            title="Dernieres synchronisations"
            icon={<RefreshCw size={18} />}
            actions={
              <Button variant="ghost" size="sm" onClick={onNavigateToExecutions}>
                Voir tout
              </Button>
            }
          >
            {executions?.items && executions.items.length > 0 ? (
              <ul className="azals-simple-list">
                {executions.items.map(exec => (
                  <li key={exec.id} className="azals-list-item">
                    <div className="azals-list-item__main">
                      <strong>{exec.execution_number}</strong>
                      <span className="text-muted ml-2">
                        {exec.processed_records}/{exec.total_records} enr.
                      </span>
                    </div>
                    <div className="azals-list-item__meta">
                      <SyncStatusBadge status={exec.status} />
                      <span className="text-muted ml-2">
                        {formatDate(exec.started_at)}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted text-center py-4">Aucune synchronisation</p>
            )}
          </Card>
        </Grid>
      </section>

      <section className="azals-section">
        <Card
          title="Connecteurs disponibles"
          icon={<Plug size={18} />}
          actions={
            <Button variant="ghost" size="sm" onClick={onNavigateToConnectors}>
              Explorer
            </Button>
          }
        >
          <div className="azals-connector-categories">
            {Object.entries(CONNECTOR_CATEGORIES).map(([key, label]) => (
              <div
                key={key}
                className="azals-connector-category"
                onClick={onNavigateToConnectors}
              >
                <div className="azals-connector-category__icon">
                  {getCategoryIcon(key)}
                </div>
                <span className="azals-connector-category__label">{label}</span>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {conflicts?.items && conflicts.items.length > 0 && (
        <section className="azals-section">
          <Card
            title="Conflits en attente"
            icon={<AlertCircle size={18} />}
            actions={
              <Button variant="ghost" size="sm" onClick={onNavigateToConflicts}>
                Voir tout ({conflicts.total})
              </Button>
            }
          >
            <ul className="azals-simple-list">
              {conflicts.items.slice(0, 3).map(conflict => (
                <li key={conflict.id} className="azals-list-item">
                  <div className="azals-list-item__main">
                    <AlertTriangle size={16} className="text-warning mr-2" />
                    <span>{conflict.entity_type}: {conflict.source_id}</span>
                  </div>
                  <div className="azals-list-item__meta">
                    <span className="text-muted">
                      {conflict.conflicting_fields.length} champ(s) en conflit
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </Card>
        </section>
      )}
    </PageWrapper>
  );
};

export default IntegrationDashboard;
