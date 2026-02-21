/**
 * AZALS MODULE GAP-086 - Integration Hub
 * =======================================
 *
 * Module de gestion des integrations tierces:
 * - Dashboard avec KPIs et statistiques
 * - Liste des connecteurs disponibles
 * - Gestion des connexions actives
 * - Monitoring des synchronisations
 * - Resolution des conflits
 * - Configuration des webhooks
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Link2, Plug, Activity, Zap,
  RefreshCw, Clock, AlertTriangle,
  Plus, Edit, Trash2, Search,
  Play, Pause, RotateCcw, CheckCircle,
  XCircle, ArrowLeft, Settings,
  ArrowRightLeft, Webhook as WebhookIcon, BarChart3,
  Filter, Eye, AlertCircle, Server,
  Cloud, Database, ShoppingCart, CreditCard,
  Building2, Mail, Users, FileText
} from 'lucide-react';
import { Button } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn, DashboardKPI } from '@/types';
import { formatDate } from '@/utils/formatters';

import integrationApi from './api';
import {
  ConnectorDefinition,
  Connection,
  ConnectionCreate,
  ConnectionListItem,
  SyncExecution,
  SyncConflict,
  Webhook,
  IntegrationStats,
  ConnectionStatus,
  HealthStatus,
  SyncStatus,
  CONNECTOR_CATEGORIES,
  CONNECTION_STATUS_COLORS,
  HEALTH_STATUS_COLORS,
  SYNC_STATUS_COLORS,
  PaginatedResponse,
} from './types';

// ============================================================================
// HELPERS & BADGES
// ============================================================================

const ConnectionStatusBadge: React.FC<{ status: ConnectionStatus }> = ({ status }) => {
  const color = CONNECTION_STATUS_COLORS[status] || 'gray';
  const labels: Record<ConnectionStatus, string> = {
    pending: 'En attente',
    configuring: 'Configuration',
    connected: 'Connecte',
    disconnected: 'Deconnecte',
    error: 'Erreur',
    expired: 'Expire',
    rate_limited: 'Limite atteinte',
    maintenance: 'Maintenance',
  };
  return <span className={`azals-badge azals-badge--${color}`}>{labels[status]}</span>;
};

const HealthStatusBadge: React.FC<{ status: HealthStatus }> = ({ status }) => {
  const color = HEALTH_STATUS_COLORS[status] || 'gray';
  const labels: Record<HealthStatus, string> = {
    healthy: 'Sain',
    degraded: 'Degrade',
    unhealthy: 'Non sain',
    unknown: 'Inconnu',
  };
  return <span className={`azals-badge azals-badge--${color}`}>{labels[status]}</span>;
};

const SyncStatusBadge: React.FC<{ status: SyncStatus }> = ({ status }) => {
  const color = SYNC_STATUS_COLORS[status] || 'gray';
  const labels: Record<SyncStatus, string> = {
    pending: 'En attente',
    queued: 'En file',
    running: 'En cours',
    completed: 'Termine',
    partial: 'Partiel',
    failed: 'Echec',
    cancelled: 'Annule',
    timeout: 'Timeout',
    retrying: 'Nouvelle tentative',
  };
  return <span className={`azals-badge azals-badge--${color}`}>{labels[status]}</span>;
};

const getCategoryIcon = (category: string) => {
  const icons: Record<string, React.ReactNode> = {
    productivity: <FileText size={20} />,
    communication: <Mail size={20} />,
    crm: <Users size={20} />,
    accounting: <Building2 size={20} />,
    erp: <Database size={20} />,
    ecommerce: <ShoppingCart size={20} />,
    payment: <CreditCard size={20} />,
    banking: <Building2 size={20} />,
    marketing: <Mail size={20} />,
    storage: <Cloud size={20} />,
    custom: <Server size={20} />,
  };
  return icons[category] || <Plug size={20} />;
};

// ============================================================================
// API HOOKS
// ============================================================================

const useConnectors = (category?: string) => {
  return useQuery({
    queryKey: ['integration', 'connectors', category],
    queryFn: () => integrationApi.listConnectors(category),
  });
};

const useConnections = (page = 1, pageSize = 20, filters?: { search?: string; status?: string }) => {
  const apiFilters = filters ? {
    search: filters.search,
    status: filters.status ? [filters.status as ConnectionStatus] : undefined,
  } : undefined;
  return useQuery({
    queryKey: ['integration', 'connections', page, pageSize, filters],
    queryFn: () => integrationApi.listConnections(apiFilters, page, pageSize),
  });
};

const useConnection = (id: string) => {
  return useQuery({
    queryKey: ['integration', 'connections', id],
    queryFn: () => integrationApi.getConnection(id),
    enabled: !!id,
  });
};

const useConnectionStats = (id: string) => {
  return useQuery({
    queryKey: ['integration', 'connections', id, 'stats'],
    queryFn: () => integrationApi.getConnectionStats(id),
    enabled: !!id,
  });
};

const useExecutions = (page = 1, pageSize = 20, filters?: { connection_id?: string; status?: string }) => {
  const apiFilters = filters ? {
    connection_id: filters.connection_id,
    status: filters.status ? [filters.status as SyncStatus] : undefined,
  } : undefined;
  return useQuery({
    queryKey: ['integration', 'executions', page, pageSize, filters],
    queryFn: () => integrationApi.listExecutions(apiFilters, page, pageSize),
  });
};

const useConflicts = (page = 1, pageSize = 20, isResolved?: boolean) => {
  return useQuery({
    queryKey: ['integration', 'conflicts', page, pageSize, isResolved],
    queryFn: () => integrationApi.listConflicts({ is_resolved: isResolved }, page, pageSize),
  });
};

const useWebhooks = (connectionId?: string) => {
  return useQuery({
    queryKey: ['integration', 'webhooks', connectionId],
    queryFn: () => integrationApi.listWebhooks(connectionId),
  });
};

const useIntegrationStats = () => {
  return useQuery({
    queryKey: ['integration', 'stats'],
    queryFn: () => integrationApi.getStats(),
  });
};

const useDeleteConnection = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: integrationApi.deleteConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'connections'] });
    },
  });
};

const useTestConnection = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: integrationApi.testConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'connections'] });
    },
  });
};

const useCancelExecution = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: integrationApi.cancelExecution,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'executions'] });
    },
  });
};

const useRetryExecution = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: integrationApi.retryExecution,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', 'executions'] });
    },
  });
};

// ============================================================================
// DASHBOARD
// ============================================================================

interface DashboardProps {
  onNavigateToConnectors: () => void;
  onNavigateToConnections: () => void;
  onNavigateToExecutions: () => void;
  onNavigateToConflicts: () => void;
  onSelectConnection: (id: string) => void;
  onCreateConnection: () => void;
}

const IntegrationDashboard: React.FC<DashboardProps> = ({
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

// ============================================================================
// CONNECTORS LIST
// ============================================================================

interface ConnectorsListProps {
  onSelectConnector: (connectorType: string) => void;
  onBack: () => void;
}

const ConnectorsList: React.FC<ConnectorsListProps> = ({ onSelectConnector, onBack }) => {
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  const { data, isLoading } = useConnectors(categoryFilter || undefined);

  const filteredConnectors = data?.items.filter(c =>
    !searchQuery ||
    c.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const connectorsByCategory = filteredConnectors.reduce((acc, connector) => {
    const cat = connector.category || 'custom';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(connector);
    return acc;
  }, {} as Record<string, ConnectorDefinition[]>);

  return (
    <PageWrapper
      title="Connecteurs disponibles"
      subtitle="Explorez les integrations disponibles"
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <section className="azals-section">
        <Card noPadding>
          <div className="azals-filter-bar">
            <div className="azals-filter-bar__search">
              <Search size={16} />
              <input
                type="text"
                placeholder="Rechercher un connecteur..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="azals-input"
              />
            </div>
            <select
              className="azals-select"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="">Toutes les categories</option>
              {Object.entries(CONNECTOR_CATEGORIES).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </Card>
      </section>

      {isLoading ? (
        <div className="azals-loading-container">
          <div className="azals-spinner" />
          <p>Chargement des connecteurs...</p>
        </div>
      ) : (
        Object.entries(connectorsByCategory).map(([category, connectors]) => (
          <section key={category} className="azals-section">
            <h3 className="azals-section-title">
              {getCategoryIcon(category)}
              <span className="ml-2">{CONNECTOR_CATEGORIES[category] || category}</span>
              <span className="azals-badge azals-badge--gray ml-2">{connectors.length}</span>
            </h3>
            <Grid cols={3} gap="md">
              {connectors.map(connector => (
                <Card
                  key={connector.id}
                  className="azals-connector-card azals-clickable"
                  onClick={() => onSelectConnector(connector.connector_type)}
                >
                  <div className="azals-connector-card__header">
                    {connector.logo_url ? (
                      <img
                        src={connector.logo_url}
                        alt={connector.display_name}
                        className="azals-connector-card__logo"
                      />
                    ) : (
                      <div
                        className="azals-connector-card__icon"
                        style={{ backgroundColor: connector.color || '#6b7280' }}
                      >
                        <Plug size={24} />
                      </div>
                    )}
                    <div className="azals-connector-card__info">
                      <h4>{connector.display_name}</h4>
                      {connector.is_beta && (
                        <span className="azals-badge azals-badge--purple">Beta</span>
                      )}
                      {connector.is_premium && (
                        <span className="azals-badge azals-badge--yellow">Premium</span>
                      )}
                    </div>
                  </div>
                  <p className="azals-connector-card__description">
                    {connector.description || 'Integration avec ' + connector.display_name}
                  </p>
                  <div className="azals-connector-card__footer">
                    <span className="text-muted">
                      {connector.supported_entities.length} entites supportees
                    </span>
                    {connector.supports_webhooks && (
                      <WebhookIcon size={14} className="text-primary" />
                    )}
                  </div>
                </Card>
              ))}
            </Grid>
          </section>
        ))
      )}

      {!isLoading && filteredConnectors.length === 0 && (
        <div className="azals-empty-state">
          <Plug size={48} className="text-muted" />
          <p>Aucun connecteur trouve</p>
        </div>
      )}
    </PageWrapper>
  );
};

// ============================================================================
// CONNECTIONS LIST
// ============================================================================

interface ConnectionsListProps {
  onSelectConnection: (id: string) => void;
  onCreateConnection: () => void;
  onBack: () => void;
}

const ConnectionsList: React.FC<ConnectionsListProps> = ({
  onSelectConnection,
  onCreateConnection,
  onBack,
}) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading, refetch } = useConnections(page, pageSize, {
    search: searchQuery || undefined,
    status: statusFilter || undefined,
  });

  const deleteConnection = useDeleteConnection();
  const testConnection = useTestConnection();

  const handleDelete = async (id: string) => {
    if (window.confirm('Supprimer cette connexion ?')) {
      await deleteConnection.mutateAsync(id);
    }
  };

  const handleTest = async (id: string) => {
    await testConnection.mutateAsync(id);
  };

  const columns: TableColumn<ConnectionListItem>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      sortable: true,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      sortable: true,
      render: (value, row) => (
        <span className="azals-link" onClick={() => onSelectConnection(row.id)}>
          {value as string}
        </span>
      ),
    },
    {
      id: 'connector_type',
      header: 'Connecteur',
      accessor: 'connector_type',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <ConnectionStatusBadge status={value as ConnectionStatus} />,
    },
    {
      id: 'health_status',
      header: 'Sante',
      accessor: 'health_status',
      render: (value) => <HealthStatusBadge status={value as HealthStatus} />,
    },
    {
      id: 'last_connected_at',
      header: 'Derniere connexion',
      accessor: 'last_connected_at',
      render: (value) => value ? formatDate(value as string) : '-',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      width: '120px',
      render: (_, row) => (
        <div className="azals-table-actions">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { handleTest(row.id); }}
          >
            <Activity size={14} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { onSelectConnection(row.id); }}
          >
            <Eye size={14} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { handleDelete(row.id); }}
          >
            <Trash2 size={14} />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Connexions"
      subtitle="Gerez vos integrations actives"
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={
        <Button leftIcon={<Plus size={16} />} onClick={onCreateConnection}>
          Nouvelle connexion
        </Button>
      }
    >
      <Card noPadding>
        <div className="azals-filter-bar">
          <div className="azals-filter-bar__search">
            <Search size={16} />
            <input
              type="text"
              placeholder="Rechercher..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="azals-input"
            />
          </div>
          <select
            className="azals-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">Tous les statuts</option>
            <option value="connected">Connecte</option>
            <option value="disconnected">Deconnecte</option>
            <option value="error">En erreur</option>
            <option value="expired">Expire</option>
          </select>
        </div>

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage="Aucune connexion"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================================
// CONNECTION DETAIL
// ============================================================================

interface ConnectionDetailProps {
  connectionId: string;
  onBack: () => void;
  onEdit: () => void;
}

const ConnectionDetail: React.FC<ConnectionDetailProps> = ({
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

// ============================================================================
// EXECUTIONS LIST
// ============================================================================

interface ExecutionsListProps {
  onBack: () => void;
}

const ExecutionsList: React.FC<ExecutionsListProps> = ({ onBack }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading, refetch } = useExecutions(page, pageSize, {
    status: statusFilter || undefined,
  });

  const cancelExecution = useCancelExecution();
  const retryExecution = useRetryExecution();

  const handleCancel = async (id: string) => {
    if (window.confirm('Annuler cette synchronisation ?')) {
      await cancelExecution.mutateAsync(id);
    }
  };

  const handleRetry = async (id: string) => {
    await retryExecution.mutateAsync(id);
  };

  const columns: TableColumn<SyncExecution>[] = [
    {
      id: 'execution_number',
      header: 'N',
      accessor: 'execution_number',
      width: '120px',
      sortable: true,
    },
    {
      id: 'direction',
      header: 'Direction',
      accessor: 'direction',
      render: (v) => (
        <span className="azals-badge azals-badge--blue">
          {v === 'inbound' ? 'Entrant' : v === 'outbound' ? 'Sortant' : 'Bidirectionnel'}
        </span>
      ),
    },
    {
      id: 'entity_type',
      header: 'Entite',
      accessor: 'entity_type',
    },
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
      render: (_, row) => (
        <div className="azals-progress-inline">
          <div className="azals-progress-bar" style={{ width: `${row.progress_percent}%` }} />
          <span>{row.processed_records}/{row.total_records}</span>
        </div>
      ),
    },
    {
      id: 'results',
      header: 'Resultats',
      accessor: 'created_records',
      render: (_, row) => (
        <span className="text-sm">
          <span className="text-success">+{row.created_records}</span>
          {' / '}
          <span className="text-info">~{row.updated_records}</span>
          {' / '}
          <span className="text-danger">-{row.deleted_records}</span>
          {row.failed_records > 0 && (
            <>
              {' / '}
              <span className="text-warning">!{row.failed_records}</span>
            </>
          )}
        </span>
      ),
    },
    {
      id: 'started_at',
      header: 'Debut',
      accessor: 'started_at',
      render: (v) => formatDate(v as string),
    },
    {
      id: 'duration_seconds',
      header: 'Duree',
      accessor: 'duration_seconds',
      render: (v) => v ? `${v}s` : '-',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      width: '100px',
      render: (_, row) => (
        <div className="azals-table-actions">
          {row.status === 'running' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleCancel(row.id)}
            >
              <XCircle size={14} />
            </Button>
          )}
          {row.status === 'failed' && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleRetry(row.id)}
            >
              <RotateCcw size={14} />
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Synchronisations"
      subtitle="Historique et suivi des executions"
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <Card noPadding>
        <div className="azals-filter-bar">
          <select
            className="azals-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">Tous les statuts</option>
            <option value="pending">En attente</option>
            <option value="running">En cours</option>
            <option value="completed">Termine</option>
            <option value="failed">Echec</option>
            <option value="cancelled">Annule</option>
          </select>
        </div>

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage="Aucune synchronisation"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================================
// CONFLICTS LIST
// ============================================================================

interface ConflictsListProps {
  onBack: () => void;
}

const ConflictsList: React.FC<ConflictsListProps> = ({ onBack }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [showResolved, setShowResolved] = useState(false);

  const { data, isLoading, refetch } = useConflicts(page, pageSize, showResolved ? undefined : false);

  const columns: TableColumn<SyncConflict>[] = [
    {
      id: 'entity_type',
      header: 'Type',
      accessor: 'entity_type',
    },
    {
      id: 'source_id',
      header: 'Source',
      accessor: 'source_id',
    },
    {
      id: 'target_id',
      header: 'Cible',
      accessor: 'target_id',
    },
    {
      id: 'conflicting_fields',
      header: 'Champs en conflit',
      accessor: 'conflicting_fields',
      render: (v) => (v as string[]).join(', '),
    },
    {
      id: 'is_resolved',
      header: 'Statut',
      accessor: 'is_resolved',
      render: (v) => (
        <span className={`azals-badge azals-badge--${v ? 'green' : 'yellow'}`}>
          {v ? 'Resolu' : 'En attente'}
        </span>
      ),
    },
    {
      id: 'created_at',
      header: 'Date',
      accessor: 'created_at',
      render: (v) => formatDate(v as string),
    },
  ];

  return (
    <PageWrapper
      title="Conflits de synchronisation"
      subtitle="Gerez les conflits de donnees"
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <Card noPadding>
        <div className="azals-filter-bar">
          <label className="azals-checkbox">
            <input
              type="checkbox"
              checked={showResolved}
              onChange={(e) => setShowResolved(e.target.checked)}
            />
            <span>Afficher les conflits resolus</span>
          </label>
        </div>

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage="Aucun conflit"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================================
// CONNECTION FORM (Simplified)
// ============================================================================

interface ConnectionFormProps {
  connectionId?: string;
  connectorType?: string;
  onBack: () => void;
  onSaved: (id: string) => void;
}

const ConnectionForm: React.FC<ConnectionFormProps> = ({
  connectionId,
  connectorType,
  onBack,
  onSaved,
}) => {
  const isNew = !connectionId;
  const queryClient = useQueryClient();

  const [form, setForm] = useState({
    name: '',
    code: '',
    description: '',
    connector_type: connectorType || 'rest_api',
    auth_type: 'api_key',
    base_url: '',
    api_version: '',
    credentials: {} as Record<string, string>,
    settings: {} as Record<string, unknown>,
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      if (isNew) {
        const result = await integrationApi.createConnection(form as ConnectionCreate);
        queryClient.invalidateQueries({ queryKey: ['integration', 'connections'] });
        onSaved(result.id);
      } else {
        await integrationApi.updateConnection(connectionId!, form);
        queryClient.invalidateQueries({ queryKey: ['integration', 'connections'] });
        onSaved(connectionId!);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la sauvegarde');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageWrapper
      title={isNew ? 'Nouvelle connexion' : 'Modifier la connexion'}
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="azals-alert azals-alert--error mb-4">
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        <Card title="Informations generales">
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>Nom *</label>
              <input
                type="text"
                className="azals-input"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="azals-form-field">
              <label>Code</label>
              <input
                type="text"
                className="azals-input"
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                placeholder="Genere automatiquement"
              />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Description</label>
              <textarea
                className="azals-textarea"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                rows={2}
              />
            </div>
            <div className="azals-form-field">
              <label>Type de connecteur *</label>
              <select
                className="azals-select"
                value={form.connector_type}
                onChange={(e) => setForm({ ...form, connector_type: e.target.value })}
                disabled={!!connectorType}
              >
                <option value="rest_api">API REST</option>
                <option value="graphql">GraphQL</option>
                <option value="webhook">Webhook</option>
                <option value="stripe">Stripe</option>
                <option value="hubspot">HubSpot</option>
                <option value="salesforce">Salesforce</option>
                <option value="slack">Slack</option>
                <option value="google_drive">Google Drive</option>
                <option value="shopify">Shopify</option>
              </select>
            </div>
            <div className="azals-form-field">
              <label>Type d'authentification *</label>
              <select
                className="azals-select"
                value={form.auth_type}
                onChange={(e) => setForm({ ...form, auth_type: e.target.value })}
              >
                <option value="none">Aucune</option>
                <option value="api_key">Cle API</option>
                <option value="oauth2">OAuth 2.0</option>
                <option value="basic">Basic Auth</option>
                <option value="bearer">Bearer Token</option>
              </select>
            </div>
          </Grid>
        </Card>

        <Card title="Configuration API">
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>URL de base</label>
              <input
                type="url"
                className="azals-input"
                value={form.base_url}
                onChange={(e) => setForm({ ...form, base_url: e.target.value })}
                placeholder="https://api.example.com"
              />
            </div>
            <div className="azals-form-field">
              <label>Version API</label>
              <input
                type="text"
                className="azals-input"
                value={form.api_version}
                onChange={(e) => setForm({ ...form, api_version: e.target.value })}
                placeholder="v1"
              />
            </div>
          </Grid>
        </Card>

        {form.auth_type === 'api_key' && (
          <Card title="Credentials">
            <div className="azals-form-field">
              <label>Cle API</label>
              <input
                type="password"
                className="azals-input"
                value={form.credentials.api_key || ''}
                onChange={(e) => setForm({
                  ...form,
                  credentials: { ...form.credentials, api_key: e.target.value }
                })}
                placeholder="sk_..."
              />
            </div>
          </Card>
        )}

        {form.auth_type === 'basic' && (
          <Card title="Credentials">
            <Grid cols={2} gap="md">
              <div className="azals-form-field">
                <label>Nom d'utilisateur</label>
                <input
                  type="text"
                  className="azals-input"
                  value={form.credentials.username || ''}
                  onChange={(e) => setForm({
                    ...form,
                    credentials: { ...form.credentials, username: e.target.value }
                  })}
                />
              </div>
              <div className="azals-form-field">
                <label>Mot de passe</label>
                <input
                  type="password"
                  className="azals-input"
                  value={form.credentials.password || ''}
                  onChange={(e) => setForm({
                    ...form,
                    credentials: { ...form.credentials, password: e.target.value }
                  })}
                />
              </div>
            </Grid>
          </Card>
        )}

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onBack}>
            Annuler
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            {isNew ? 'Creer' : 'Enregistrer'}
          </Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type IntegrationView =
  | 'dashboard'
  | 'connectors'
  | 'connections'
  | 'connection-detail'
  | 'connection-form'
  | 'executions'
  | 'conflicts';

interface IntegrationNavState {
  view: IntegrationView;
  connectionId?: string;
  connectorType?: string;
  isNew?: boolean;
}

export const IntegrationModule: React.FC = () => {
  const [navState, setNavState] = useState<IntegrationNavState>({ view: 'dashboard' });

  const navigateToDashboard = useCallback(() => setNavState({ view: 'dashboard' }), []);
  const navigateToConnectors = useCallback(() => setNavState({ view: 'connectors' }), []);
  const navigateToConnections = useCallback(() => setNavState({ view: 'connections' }), []);
  const navigateToExecutions = useCallback(() => setNavState({ view: 'executions' }), []);
  const navigateToConflicts = useCallback(() => setNavState({ view: 'conflicts' }), []);

  const navigateToConnectionDetail = useCallback((id: string) => {
    setNavState({ view: 'connection-detail', connectionId: id });
  }, []);

  const navigateToConnectionForm = useCallback((id?: string, connectorType?: string) => {
    setNavState({
      view: 'connection-form',
      connectionId: id,
      connectorType,
      isNew: !id,
    });
  }, []);

  const handleSelectConnector = useCallback((connectorType: string) => {
    setNavState({
      view: 'connection-form',
      connectorType,
      isNew: true,
    });
  }, []);

  switch (navState.view) {
    case 'connectors':
      return (
        <ConnectorsList
          onSelectConnector={handleSelectConnector}
          onBack={navigateToDashboard}
        />
      );

    case 'connections':
      return (
        <ConnectionsList
          onSelectConnection={navigateToConnectionDetail}
          onCreateConnection={() => navigateToConnectionForm()}
          onBack={navigateToDashboard}
        />
      );

    case 'connection-detail':
      return (
        <ConnectionDetail
          connectionId={navState.connectionId!}
          onBack={navigateToConnections}
          onEdit={() => navigateToConnectionForm(navState.connectionId)}
        />
      );

    case 'connection-form':
      return (
        <ConnectionForm
          connectionId={navState.connectionId}
          connectorType={navState.connectorType}
          onBack={
            navState.isNew
              ? navState.connectorType
                ? navigateToConnectors
                : navigateToDashboard
              : () => navigateToConnectionDetail(navState.connectionId!)
          }
          onSaved={navigateToConnectionDetail}
        />
      );

    case 'executions':
      return <ExecutionsList onBack={navigateToDashboard} />;

    case 'conflicts':
      return <ConflictsList onBack={navigateToDashboard} />;

    default:
      return (
        <IntegrationDashboard
          onNavigateToConnectors={navigateToConnectors}
          onNavigateToConnections={navigateToConnections}
          onNavigateToExecutions={navigateToExecutions}
          onNavigateToConflicts={navigateToConflicts}
          onSelectConnection={navigateToConnectionDetail}
          onCreateConnection={() => navigateToConnectionForm()}
        />
      );
  }
};

export default IntegrationModule;
