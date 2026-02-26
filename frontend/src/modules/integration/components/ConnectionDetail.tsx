/**
 * AZALS MODULE GAP-086 - Integration Hub - Connection Detail
 * Vue detail d'une connexion
 */

import React from 'react';
import {
  RefreshCw, Clock, Database, CheckCircle,
  Edit, Activity, AlertTriangle, Settings,
  Webhook as WebhookIcon
} from 'lucide-react';
import { Button } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { DashboardKPI } from '@/types';
import { formatDate } from '@/utils/formatters';
import type { SyncStatus } from '../types';
import {
  useConnection, useConnectionStats, useExecutions, useWebhooks, useTestConnection
} from '../hooks';
import { ConnectionStatusBadge, HealthStatusBadge, SyncStatusBadge } from './StatusBadges';

export interface ConnectionDetailProps {
  connectionId: string;
  onBack: () => void;
  onEdit: () => void;
}

export const ConnectionDetail: React.FC<ConnectionDetailProps> = ({
  connectionId,
  onBack,
  onEdit,
}) => {
  const { data: connection, isLoading, error } = useConnection(connectionId);
  const { data: stats } = useConnectionStats(connectionId);
  const { data: executions } = useExecutions(1, 10, { connection_id: connectionId });
  const { data: webhooks } = useWebhooks(connectionId);

  const testConnection = useTestConnection();

  const handleTest = async () => {
    await testConnection.mutateAsync(connectionId);
  };

  if (isLoading) {
    return (
      <div className="azals-loading-container">
        <div className="azals-spinner" />
        <p>Chargement de la connexion...</p>
      </div>
    );
  }

  if (error || !connection) {
    return (
      <div className="azals-error-container">
        <AlertTriangle size={48} className="text-danger" />
        <p>Erreur lors du chargement de la connexion</p>
        <Button variant="secondary" onClick={onBack}>
          Retour a la liste
        </Button>
      </div>
    );
  }

  const connectionKpis: DashboardKPI[] = stats ? [
    {
      id: 'executions',
      label: 'Executions totales',
      value: stats.total_executions,
      icon: <RefreshCw size={20} />,
    },
    {
      id: 'success_rate',
      label: 'Taux de succes',
      value: `${stats.success_rate.toFixed(1)}%`,
      icon: <CheckCircle size={20} />,
    },
    {
      id: 'records',
      label: 'Enregistrements sync.',
      value: new Intl.NumberFormat().format(stats.total_records_synced),
      icon: <Database size={20} />,
    },
    {
      id: 'avg_time',
      label: 'Temps moyen',
      value: `${stats.avg_execution_time_seconds.toFixed(1)}s`,
      icon: <Clock size={20} />,
    },
  ] : [];

  return (
    <PageWrapper
      title={connection.name}
      subtitle={`${connection.connector_type} - ${connection.code}`}
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={
        <>
          <Button
            variant="secondary"
            leftIcon={<Activity size={16} />}
            onClick={handleTest}
            isLoading={testConnection.isPending}
          >
            Tester
          </Button>
          <Button leftIcon={<Edit size={16} />} onClick={onEdit}>
            Modifier
          </Button>
        </>
      }
    >
      <section className="azals-section">
        <div className="azals-connection-header">
          <div className="azals-connection-status">
            <ConnectionStatusBadge status={connection.status} />
            <HealthStatusBadge status={connection.health_status} />
          </div>
          {connection.last_error && (
            <div className="azals-alert azals-alert--error">
              <AlertTriangle size={16} />
              <span>{connection.last_error}</span>
            </div>
          )}
        </div>
      </section>

      {stats && (
        <section className="azals-section">
          <Grid cols={4} gap="md">
            {connectionKpis.map(kpi => <KPICard key={kpi.id} kpi={kpi} />)}
          </Grid>
        </section>
      )}

      <section className="azals-section">
        <Grid cols={2} gap="lg">
          <Card title="Informations" icon={<Settings size={18} />}>
            <dl className="azals-description-list">
              <div>
                <dt>Code</dt>
                <dd>{connection.code}</dd>
              </div>
              <div>
                <dt>Type d'authentification</dt>
                <dd>{connection.auth_type}</dd>
              </div>
              <div>
                <dt>Version API</dt>
                <dd>{connection.api_version || '-'}</dd>
              </div>
              <div>
                <dt>URL de base</dt>
                <dd>{connection.base_url || '-'}</dd>
              </div>
              <div>
                <dt>Derniere connexion</dt>
                <dd>
                  {connection.last_connected_at
                    ? formatDate(connection.last_connected_at)
                    : '-'}
                </dd>
              </div>
              <div>
                <dt>Dernier health check</dt>
                <dd>
                  {connection.last_health_check
                    ? formatDate(connection.last_health_check)
                    : '-'}
                </dd>
              </div>
              <div>
                <dt>Taux de succes (24h)</dt>
                <dd>
                  {connection.success_rate_24h
                    ? `${connection.success_rate_24h.toFixed(1)}%`
                    : '-'}
                </dd>
              </div>
              <div>
                <dt>Temps de reponse moyen</dt>
                <dd>
                  {connection.avg_response_time_ms
                    ? `${connection.avg_response_time_ms}ms`
                    : '-'}
                </dd>
              </div>
            </dl>
          </Card>

          <Card title="Webhooks" icon={<WebhookIcon size={18} />}>
            {webhooks?.items && webhooks.items.length > 0 ? (
              <ul className="azals-simple-list">
                {webhooks.items.map(wh => (
                  <li key={wh.id} className="azals-list-item">
                    <div className="azals-list-item__main">
                      <span className="azals-badge azals-badge--blue">{wh.direction}</span>
                      <strong className="ml-2">{wh.name}</strong>
                    </div>
                    <div className="azals-list-item__meta">
                      <span className={`azals-badge azals-badge--${wh.status === 'active' ? 'green' : 'gray'}`}>
                        {wh.status}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted text-center py-4">Aucun webhook configure</p>
            )}
          </Card>
        </Grid>
      </section>

      <section className="azals-section">
        <Card title="Dernieres synchronisations" icon={<RefreshCw size={18} />}>
          {executions?.items && executions.items.length > 0 ? (
            <DataTable
              columns={[
                { id: 'execution_number', header: 'N', accessor: 'execution_number', width: '120px' },
                { id: 'direction', header: 'Direction', accessor: 'direction' },
                { id: 'entity_type', header: 'Entite', accessor: 'entity_type' },
                {
                  id: 'status',
                  header: 'Statut',
                  accessor: 'status',
                  render: (v) => <SyncStatusBadge status={v as SyncStatus} />,
                },
                {
                  id: 'progress',
                  header: 'Progression',
                  accessor: 'progress_percent',
                  render: (v, row) => `${row.processed_records}/${row.total_records} (${v}%)`,
                },
                {
                  id: 'started_at',
                  header: 'Debut',
                  accessor: 'started_at',
                  render: (v) => formatDate(v as string),
                },
                {
                  id: 'duration',
                  header: 'Duree',
                  accessor: 'duration_seconds',
                  render: (v) => v ? `${v}s` : '-',
                },
              ]}
              data={executions.items}
              keyField="id"
              emptyMessage="Aucune synchronisation"
            />
          ) : (
            <p className="text-muted text-center py-4">Aucune synchronisation</p>
          )}
        </Card>
      </section>
    </PageWrapper>
  );
};

export default ConnectionDetail;
