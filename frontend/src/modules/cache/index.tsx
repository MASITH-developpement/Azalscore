/**
 * AZALSCORE - Module Cache Admin Panel
 * =====================================
 * Interface d'administration pour la gestion du cache applicatif.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Database,
  Trash2,
  RefreshCw,
  Settings,
  AlertTriangle,
  BarChart3,
  Layers,
  Clock,
  Zap,
  Play,
  Check,
  X,
} from 'lucide-react';
import { Button } from '@ui/actions';
import { StatCard } from '@ui/dashboards';
import { Select, Input } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { cacheApi } from './api';
import type {
  CacheDashboard,
  CacheRegion,
  CacheAlert,
  PreloadTask,
  CacheAuditLog,
  TopKey,
  RecentInvalidation,
  CacheLevel,
} from './types';
import {
  formatBytes,
  formatHitRate,
  formatDuration,
  EVICTION_POLICIES,
  CACHE_LEVELS,
  ALERT_SEVERITIES,
} from './types';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
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
        {tab.icon && <span className="mr-2">{tab.icon}</span>}
        {tab.label}
      </button>
    ))}
  </nav>
);

const ProgressBar: React.FC<{ value: number; max: number; color?: string }> = ({
  value,
  max,
  color = 'blue',
}) => {
  const percent = max > 0 ? (value / max) * 100 : 0;
  const barColor = percent > 90 ? 'red' : percent > 70 ? 'yellow' : color;

  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div
        className={`h-2 rounded-full bg-${barColor}-500`}
        style={{ width: `${Math.min(percent, 100)}%` }}
      />
    </div>
  );
};

// ============================================================================
// HELPERS
// ============================================================================

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

// ============================================================================
// API HOOKS
// ============================================================================

const useCacheDashboard = () => {
  return useQuery({
    queryKey: ['cache', 'dashboard'],
    queryFn: async () => {
      const response = await cacheApi.getDashboard();
      return response.data;
    },
    refetchInterval: 30000, // Refresh toutes les 30s
  });
};

const useCacheRegions = () => {
  return useQuery({
    queryKey: ['cache', 'regions'],
    queryFn: async () => {
      const response = await cacheApi.listRegions();
      return response.data;
    },
  });
};

const useCacheAlerts = () => {
  return useQuery({
    queryKey: ['cache', 'alerts'],
    queryFn: async () => {
      const response = await cacheApi.listAlerts();
      return response.data;
    },
  });
};

const usePreloadTasks = () => {
  return useQuery({
    queryKey: ['cache', 'preload'],
    queryFn: async () => {
      const response = await cacheApi.listPreloadTasks();
      return response.data;
    },
  });
};

const useAuditLogs = () => {
  return useQuery({
    queryKey: ['cache', 'audit'],
    queryFn: async () => {
      const response = await cacheApi.getAuditLogs();
      return response.data;
    },
  });
};

// ============================================================================
// DASHBOARD VIEW
// ============================================================================

const DashboardView: React.FC = () => {
  const { data: dashboard, isLoading, refetch } = useCacheDashboard();
  const queryClient = useQueryClient();

  const invalidateAllMutation = useMutation({
    mutationFn: () => cacheApi.invalidateAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cache'] });
    },
  });

  const purgeMutation = useMutation({
    mutationFn: () => cacheApi.purge({ expired_only: true, confirm: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cache'] });
    },
  });

  if (isLoading) {
    return <div className="p-4">Chargement...</div>;
  }

  if (!dashboard) {
    return <div className="p-4">Aucune donnee disponible</div>;
  }

  const { stats, config, top_keys, recent_invalidations, active_alerts } = dashboard;

  return (
    <div className="space-y-6">
      {/* Stats principales */}
      <Grid cols={4}>
        <StatCard
          title="Taux de hit"
          value={formatHitRate(stats.overall_hit_rate)}
          icon={<Zap />}
          variant={stats.overall_hit_rate >= 0.8 ? 'success' : stats.overall_hit_rate >= 0.5 ? 'warning' : 'danger'}
        />
        <StatCard
          title="Entrees en cache"
          value={String(stats.total_items)}
          icon={<Database />}
          variant="default"
        />
        <StatCard
          title="Taille totale"
          value={formatBytes(stats.total_size_bytes)}
          icon={<Layers />}
          variant="default"
        />
        <StatCard
          title="Alertes actives"
          value={String(active_alerts?.length || 0)}
          icon={<AlertTriangle />}
          variant={active_alerts?.length > 0 ? 'danger' : 'success'}
        />
      </Grid>

      {/* Stats par niveau */}
      <Grid cols={3}>
        {stats.l1_stats && (
          <Card>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Badge color="green">L1</Badge> Cache Memoire
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Hits/Misses</span>
                <span>{stats.l1_stats.hits} / {stats.l1_stats.misses}</span>
              </div>
              <div className="flex justify-between">
                <span>Taux de hit</span>
                <span>{formatHitRate(stats.l1_stats.hit_rate)}</span>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>Remplissage</span>
                  <span>{(stats.l1_stats.fill_rate * 100).toFixed(1)}%</span>
                </div>
                <ProgressBar
                  value={stats.l1_stats.current_items}
                  max={stats.l1_stats.max_items}
                />
              </div>
              <div className="flex justify-between">
                <span>Temps moyen GET</span>
                <span>{formatDuration(stats.l1_stats.avg_get_time_ms)}</span>
              </div>
              <div className="flex justify-between">
                <span>Evictions</span>
                <span>{stats.l1_stats.total_evictions}</span>
              </div>
            </div>
          </Card>
        )}

        {stats.l2_stats && (
          <Card>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Badge color="blue">L2</Badge> Cache Redis
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Hits/Misses</span>
                <span>{stats.l2_stats.hits} / {stats.l2_stats.misses}</span>
              </div>
              <div className="flex justify-between">
                <span>Taux de hit</span>
                <span>{formatHitRate(stats.l2_stats.hit_rate)}</span>
              </div>
              <div className="flex justify-between">
                <span>Taille</span>
                <span>{formatBytes(stats.l2_stats.current_size_bytes)}</span>
              </div>
            </div>
          </Card>
        )}

        {stats.l3_stats && (
          <Card>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Badge color="purple">L3</Badge> Cache Persistant
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span>Entrees</span>
                <span>{stats.l3_stats.current_items}</span>
              </div>
              <div className="flex justify-between">
                <span>Taille</span>
                <span>{formatBytes(stats.l3_stats.current_size_bytes)}</span>
              </div>
            </div>
          </Card>
        )}
      </Grid>

      {/* Actions rapides */}
      <Card>
        <h3 className="text-lg font-semibold mb-4">Actions rapides</h3>
        <div className="flex gap-4">
          <Button
            onClick={() => { void refetch(); }}
            variant="secondary"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Rafraichir stats
          </Button>
          <Button
            onClick={() => purgeMutation.mutate()}
            variant="secondary"
            disabled={purgeMutation.isPending}
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Purger expires
          </Button>
          <Button
            onClick={() => {
              if (window.confirm('Invalider tout le cache ? Cette action ne peut pas etre annulee.')) {
                invalidateAllMutation.mutate();
              }
            }}
            variant="danger"
            disabled={invalidateAllMutation.isPending}
          >
            <X className="w-4 h-4 mr-2" />
            Invalider tout
          </Button>
        </div>
      </Card>

      {/* Top keys et invalidations recentes */}
      <Grid cols={2}>
        <Card>
          <h3 className="text-lg font-semibold mb-4">Cles les plus utilisees</h3>
          {top_keys && top_keys.length > 0 ? (
            <div className="space-y-2">
              {top_keys.map((key: TopKey, i: number) => (
                <div key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <div className="flex flex-col">
                    <code className="text-sm font-mono truncate max-w-xs">{key.key}</code>
                    <span className="text-xs text-gray-500">
                      {key.region_code && <Badge color="blue">{key.region_code}</Badge>}
                      {key.entity_type && <span className="ml-2">{key.entity_type}</span>}
                    </span>
                  </div>
                  <Badge color="green">{key.hit_count} hits</Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">Aucune donnee</p>
          )}
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Invalidations recentes</h3>
          {recent_invalidations && recent_invalidations.length > 0 ? (
            <div className="space-y-2">
              {recent_invalidations.map((inv: RecentInvalidation) => (
                <div key={inv.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <div>
                    <Badge color="purple">{inv.invalidation_type}</Badge>
                    <span className="ml-2 text-sm">{inv.keys_invalidated} cles</span>
                  </div>
                  <span className="text-xs text-gray-500">{formatDateTime(inv.created_at)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">Aucune invalidation recente</p>
          )}
        </Card>
      </Grid>

      {/* Alertes actives */}
      {active_alerts && active_alerts.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold mb-4 text-red-600">
            <AlertTriangle className="w-5 h-5 inline mr-2" />
            Alertes actives
          </h3>
          <div className="space-y-2">
            {active_alerts.map((alert: CacheAlert) => (
              <div
                key={alert.id}
                className={`p-4 rounded border-l-4 ${
                  alert.severity === 'CRITICAL'
                    ? 'bg-red-50 border-red-500'
                    : alert.severity === 'WARNING'
                    ? 'bg-yellow-50 border-yellow-500'
                    : 'bg-blue-50 border-blue-500'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-semibold">{alert.title}</h4>
                    <p className="text-sm text-gray-600">{alert.message}</p>
                  </div>
                  <Badge color={alert.severity === 'CRITICAL' ? 'red' : alert.severity === 'WARNING' ? 'yellow' : 'blue'}>
                    {alert.severity}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

// ============================================================================
// REGIONS VIEW
// ============================================================================

const RegionsView: React.FC = () => {
  const { data: regions = [], isLoading, refetch } = useCacheRegions();
  const queryClient = useQueryClient();

  const deleteRegionMutation = useMutation({
    mutationFn: (regionId: string) => cacheApi.deleteRegion(regionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cache', 'regions'] });
    },
  });

  const columns: TableColumn<CacheRegion>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      render: (v) => <code className="font-mono">{v as string}</code>,
    },
    { id: 'name', header: 'Nom', accessor: 'name' },
    {
      id: 'ttl_seconds',
      header: 'TTL',
      accessor: 'ttl_seconds',
      render: (v) => `${v as number}s`,
    },
    {
      id: 'max_items',
      header: 'Max Items',
      accessor: 'max_items',
      render: (v) => (v as number).toLocaleString(),
    },
    {
      id: 'entity_types',
      header: 'Entites',
      accessor: 'entity_types',
      render: (v) => {
        const types = v as string[];
        return types.length > 0 ? types.join(', ') : '-';
      },
    },
    {
      id: 'preload_enabled',
      header: 'Prechargement',
      accessor: 'preload_enabled',
      render: (v) => (v as boolean) ? <Check className="w-4 h-4 text-green-500" /> : <X className="w-4 h-4 text-gray-400" />,
    },
    {
      id: 'is_active',
      header: 'Actif',
      accessor: 'is_active',
      render: (v) => <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>,
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_v, row) => (
        <Button
          size="sm"
          variant="danger"
          onClick={() => {
            if (window.confirm('Supprimer cette region ?')) {
              deleteRegionMutation.mutate((row as CacheRegion).id);
            }
          }}
        >
          Supprimer
        </Button>
      ),
    },
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Regions de cache</h3>
        <div className="flex gap-2">
          <Button onClick={() => { void refetch(); }} variant="secondary">
            <RefreshCw className="w-4 h-4 mr-2" />
            Rafraichir
          </Button>
          <Button
            onClick={() => {
              window.dispatchEvent(
                new CustomEvent('azals:create', { detail: { module: 'cache', type: 'region' } })
              );
            }}
          >
            Nouvelle region
          </Button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={regions}
        isLoading={isLoading}
        keyField="id"
        filterable
      />
    </Card>
  );
};

// ============================================================================
// ALERTS VIEW
// ============================================================================

const AlertsView: React.FC = () => {
  const { data: alerts = [], isLoading, refetch } = useCacheAlerts();
  const queryClient = useQueryClient();

  const acknowledgeAlertMutation = useMutation({
    mutationFn: (alertId: string) => cacheApi.acknowledgeAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cache', 'alerts'] });
    },
  });

  const resolveAlertMutation = useMutation({
    mutationFn: (alertId: string) => cacheApi.resolveAlert(alertId, 'Resolu via admin'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cache', 'alerts'] });
    },
  });

  const checkThresholdsMutation = useMutation({
    mutationFn: () => cacheApi.checkThresholds(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cache', 'alerts'] });
    },
  });

  const columns: TableColumn<CacheAlert>[] = [
    {
      id: 'severity',
      header: 'Severite',
      accessor: 'severity',
      render: (v) => {
        const severity = v as string;
        const color = severity === 'CRITICAL' ? 'red' : severity === 'WARNING' ? 'yellow' : 'blue';
        return <Badge color={color}>{severity}</Badge>;
      },
    },
    { id: 'title', header: 'Titre', accessor: 'title' },
    { id: 'alert_type', header: 'Type', accessor: 'alert_type' },
    {
      id: 'actual_value',
      header: 'Valeur',
      accessor: 'actual_value',
      render: (v, row) => {
        const alert = row as CacheAlert;
        if (v === null || v === undefined) return '-';
        return `${(v as number).toFixed(2)} (seuil: ${alert.threshold_value?.toFixed(2) || '-'})`;
      },
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v) => {
        const status = v as string;
        const color = status === 'ACTIVE' ? 'red' : status === 'ACKNOWLEDGED' ? 'yellow' : 'green';
        return <Badge color={color}>{status}</Badge>;
      },
    },
    {
      id: 'triggered_at',
      header: 'Declenchee',
      accessor: 'triggered_at',
      render: (v) => formatDateTime(v as string),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_v, row) => {
        const alert = row as CacheAlert;
        return (
          <div className="flex gap-2">
            {alert.status === 'ACTIVE' && (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => acknowledgeAlertMutation.mutate(alert.id)}
              >
                Acquitter
              </Button>
            )}
            {alert.status !== 'RESOLVED' && (
              <Button
                size="sm"
                variant="success"
                onClick={() => resolveAlertMutation.mutate(alert.id)}
              >
                Resoudre
              </Button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Alertes</h3>
        <div className="flex gap-2">
          <Button onClick={() => { void refetch(); }} variant="secondary">
            <RefreshCw className="w-4 h-4 mr-2" />
            Rafraichir
          </Button>
          <Button onClick={() => checkThresholdsMutation.mutate()} variant="secondary">
            Verifier seuils
          </Button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={alerts}
        isLoading={isLoading}
        keyField="id"
        filterable
      />
    </Card>
  );
};

// ============================================================================
// PRELOAD VIEW
// ============================================================================

const PreloadView: React.FC = () => {
  const { data: tasks = [], isLoading, refetch } = usePreloadTasks();
  const queryClient = useQueryClient();

  const runTaskMutation = useMutation({
    mutationFn: (taskId: string) => cacheApi.runPreloadTask(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cache', 'preload'] });
    },
  });

  const columns: TableColumn<PreloadTask>[] = [
    { id: 'name', header: 'Nom', accessor: 'name' },
    {
      id: 'region_code',
      header: 'Region',
      accessor: 'region_code',
      render: (v) => v ? <Badge color="blue">{v as string}</Badge> : '-',
    },
    { id: 'loader_type', header: 'Type', accessor: 'loader_type' },
    {
      id: 'schedule_cron',
      header: 'Planification',
      accessor: 'schedule_cron',
      render: (v) => v ? <code className="text-xs">{v as string}</code> : 'Manuel',
    },
    {
      id: 'last_run_status',
      header: 'Dernier statut',
      accessor: 'last_run_status',
      render: (v) => {
        if (!v) return '-';
        const status = v as string;
        const color = status === 'SUCCESS' ? 'green' : status === 'FAILED' ? 'red' : 'yellow';
        return <Badge color={color}>{status}</Badge>;
      },
    },
    {
      id: 'last_run_keys_loaded',
      header: 'Cles chargees',
      accessor: 'last_run_keys_loaded',
      render: (v) => (v as number).toLocaleString(),
    },
    {
      id: 'last_run_at',
      header: 'Derniere exec.',
      accessor: 'last_run_at',
      render: (v) => v ? formatDateTime(v as string) : '-',
    },
    {
      id: 'is_active',
      header: 'Actif',
      accessor: 'is_active',
      render: (v) => <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>,
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_v, row) => (
        <Button
          size="sm"
          onClick={() => runTaskMutation.mutate((row as PreloadTask).id)}
          disabled={runTaskMutation.isPending}
        >
          <Play className="w-4 h-4 mr-1" />
          Executer
        </Button>
      ),
    },
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Taches de prechargement</h3>
        <div className="flex gap-2">
          <Button onClick={() => { void refetch(); }} variant="secondary">
            <RefreshCw className="w-4 h-4 mr-2" />
            Rafraichir
          </Button>
          <Button
            onClick={() => {
              window.dispatchEvent(
                new CustomEvent('azals:create', { detail: { module: 'cache', type: 'preload' } })
              );
            }}
          >
            Nouvelle tache
          </Button>
        </div>
      </div>
      <DataTable
        columns={columns}
        data={tasks}
        isLoading={isLoading}
        keyField="id"
        filterable
      />
    </Card>
  );
};

// ============================================================================
// INVALIDATION VIEW
// ============================================================================

const InvalidationView: React.FC = () => {
  const [invalidationType, setInvalidationType] = useState<'key' | 'pattern' | 'tag' | 'entity'>('key');
  const [inputValue, setInputValue] = useState('');
  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');
  const queryClient = useQueryClient();

  const invalidateMutation = useMutation({
    mutationFn: async () => {
      switch (invalidationType) {
        case 'key':
          return cacheApi.invalidateByKey(inputValue);
        case 'pattern':
          return cacheApi.invalidateByPattern(inputValue);
        case 'tag':
          return cacheApi.invalidateByTag(inputValue);
        case 'entity':
          return cacheApi.invalidateByEntity(entityType, entityId || undefined);
        default:
          throw new Error('Type invalide');
      }
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['cache'] });
      alert(`Invalidation reussie: ${result.data.keys_invalidated} cles invalidees`);
      setInputValue('');
      setEntityType('');
      setEntityId('');
    },
    onError: (error) => {
      alert(`Erreur: ${error}`);
    },
  });

  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">Invalidation de cache</h3>

      <div className="space-y-4">
        <div className="flex gap-4">
          <Select
            value={invalidationType}
            onChange={(v) => setInvalidationType(v as typeof invalidationType)}
            options={[
              { value: 'key', label: 'Par cle' },
              { value: 'pattern', label: 'Par pattern' },
              { value: 'tag', label: 'Par tag' },
              { value: 'entity', label: 'Par entite' },
            ]}
            className="w-40"
          />
        </div>

        {invalidationType === 'entity' ? (
          <div className="flex gap-4">
            <Input
              value={entityType}
              onChange={setEntityType}
              placeholder="Type d'entite (ex: User)"
              className="flex-1"
            />
            <Input
              value={entityId}
              onChange={setEntityId}
              placeholder="ID entite (optionnel)"
              className="flex-1"
            />
          </div>
        ) : (
          <Input
            value={inputValue}
            onChange={setInputValue}
            placeholder={
              invalidationType === 'key'
                ? 'Cle a invalider (ex: user:123)'
                : invalidationType === 'pattern'
                ? 'Pattern (ex: user:*)'
                : 'Tag (ex: users)'
            }
            className="w-full"
          />
        )}

        <Button
          onClick={() => invalidateMutation.mutate()}
          disabled={
            invalidateMutation.isPending ||
            (invalidationType === 'entity' ? !entityType : !inputValue)
          }
        >
          {invalidateMutation.isPending ? 'Invalidation...' : 'Invalider'}
        </Button>
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded">
        <h4 className="font-semibold mb-2">Aide</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li><strong>Par cle:</strong> Invalide une cle specifique</li>
          <li><strong>Par pattern:</strong> Utilise * comme wildcard (ex: user:* invalide user:1, user:2, etc.)</li>
          <li><strong>Par tag:</strong> Invalide toutes les cles avec ce tag</li>
          <li><strong>Par entite:</strong> Invalide les cles liees a une entite metier</li>
        </ul>
      </div>
    </Card>
  );
};

// ============================================================================
// AUDIT VIEW
// ============================================================================

const AuditView: React.FC = () => {
  const { data: logs = [], isLoading, refetch } = useAuditLogs();

  const columns: TableColumn<CacheAuditLog>[] = [
    {
      id: 'created_at',
      header: 'Date',
      accessor: 'created_at',
      render: (v) => formatDateTime(v as string),
    },
    {
      id: 'action',
      header: 'Action',
      accessor: 'action',
      render: (v) => <Badge color="blue">{v as string}</Badge>,
    },
    { id: 'entity_type', header: 'Type', accessor: 'entity_type' },
    { id: 'entity_id', header: 'ID', accessor: 'entity_id', render: (v) => String(v || '-') },
    { id: 'description', header: 'Description', accessor: 'description', render: (v) => String(v || '-') },
    {
      id: 'success',
      header: 'Succes',
      accessor: 'success',
      render: (v) =>
        (v as boolean) ? (
          <Check className="w-4 h-4 text-green-500" />
        ) : (
          <X className="w-4 h-4 text-red-500" />
        ),
    },
    { id: 'user_email', header: 'Utilisateur', accessor: 'user_email', render: (v) => String(v || '-') },
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Journal d'audit</h3>
        <Button onClick={() => { void refetch(); }} variant="secondary">
          <RefreshCw className="w-4 h-4 mr-2" />
          Rafraichir
        </Button>
      </div>
      <DataTable
        columns={columns}
        data={logs}
        isLoading={isLoading}
        keyField="id"
        filterable
      />
    </Card>
  );
};

// ============================================================================
// CONFIG VIEW
// ============================================================================

const ConfigView: React.FC = () => {
  const { data: dashboard } = useCacheDashboard();
  const config = dashboard?.config;
  const queryClient = useQueryClient();

  const updateConfigMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => cacheApi.updateConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cache', 'dashboard'] });
    },
  });

  if (!config) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">Aucune configuration cache trouvee</p>
          <Button
            onClick={() =>
              cacheApi.createConfig({}).then(() => {
                queryClient.invalidateQueries({ queryKey: ['cache'] });
              })
            }
          >
            Creer la configuration
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <h3 className="text-lg font-semibold mb-4">Configuration generale</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">TTL par defaut (secondes)</label>
            <div className="text-lg">{config.default_ttl_seconds}s</div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">TTL stale (secondes)</label>
            <div className="text-lg">{config.stale_ttl_seconds}s</div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Politique d'eviction</label>
            <div className="text-lg">
              {EVICTION_POLICIES.find((p) => p.value === config.eviction_policy)?.label ||
                config.eviction_policy}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Compression</label>
            <div className="text-lg">
              {config.compression_enabled ? (
                <span className="text-green-600">Active (seuil: {formatBytes(config.compression_threshold_bytes)})</span>
              ) : (
                <span className="text-gray-500">Desactivee</span>
              )}
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="text-lg font-semibold mb-4">Niveaux de cache</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
            <div className="flex items-center gap-4">
              <Badge color="green">L1</Badge>
              <span>Cache Memoire</span>
            </div>
            <div className="flex items-center gap-4">
              <span>{config.l1_enabled ? 'Active' : 'Desactive'}</span>
              <span>{config.l1_max_items.toLocaleString()} items max</span>
              <span>{config.l1_max_size_mb} MB max</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
            <div className="flex items-center gap-4">
              <Badge color="blue">L2</Badge>
              <span>Cache Redis</span>
            </div>
            <div className="flex items-center gap-4">
              <span>{config.l2_enabled ? 'Active' : 'Desactive'}</span>
              <span>{config.l2_max_size_mb} MB max</span>
            </div>
          </div>
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
            <div className="flex items-center gap-4">
              <Badge color="purple">L3</Badge>
              <span>Cache Persistant</span>
            </div>
            <div className="flex items-center gap-4">
              <span>{config.l3_enabled ? 'Active' : 'Desactive'}</span>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="text-lg font-semibold mb-4">Seuils d'alerte</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Taux de hit minimum</label>
            <div className="text-lg">{(config.alert_hit_rate_threshold * 100).toFixed(0)}%</div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Seuil memoire</label>
            <div className="text-lg">{config.alert_memory_threshold_percent}%</div>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Evictions par heure max</label>
            <div className="text-lg">{config.alert_eviction_rate_threshold}</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'regions' | 'invalidation' | 'preload' | 'alerts' | 'audit' | 'config';

const CacheModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  const tabs: TabNavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'regions', label: 'Regions', icon: <Layers className="w-4 h-4" /> },
    { id: 'invalidation', label: 'Invalidation', icon: <Trash2 className="w-4 h-4" /> },
    { id: 'preload', label: 'Prechargement', icon: <RefreshCw className="w-4 h-4" /> },
    { id: 'alerts', label: 'Alertes', icon: <AlertTriangle className="w-4 h-4" /> },
    { id: 'audit', label: 'Audit', icon: <Clock className="w-4 h-4" /> },
    { id: 'config', label: 'Configuration', icon: <Settings className="w-4 h-4" /> },
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'regions':
        return <RegionsView />;
      case 'invalidation':
        return <InvalidationView />;
      case 'preload':
        return <PreloadView />;
      case 'alerts':
        return <AlertsView />;
      case 'audit':
        return <AuditView />;
      case 'config':
        return <ConfigView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <PageWrapper
      title="Gestion du Cache"
      subtitle="Administration du cache applicatif multi-niveau"
    >
      <TabNav tabs={tabs} activeTab={currentView} onChange={(id) => setCurrentView(id as View)} />
      <div className="mt-4">{renderContent()}</div>
    </PageWrapper>
  );
};

export default CacheModule;
