/**
 * AZALSCORE Module - Cache - Dashboard View
 * Vue principale du dashboard cache
 */

import React from 'react';
import {
  Database,
  Trash2,
  RefreshCw,
  AlertTriangle,
  Zap,
  Layers,
  X,
} from 'lucide-react';
import { Button } from '@ui/actions';
import { StatCard } from '@ui/dashboards';
import { Card, Grid } from '@ui/layout';
import type { CacheAlert, TopKey, RecentInvalidation } from '../types';
import { formatBytes, formatHitRate, formatDuration } from '../types';
import { useCacheDashboard, useInvalidateAll, usePurgeCache } from '../hooks';
import { Badge, ProgressBar, formatDateTime } from './helpers';

export const DashboardView: React.FC = () => {
  const { data: dashboard, isLoading, refetch } = useCacheDashboard();
  const invalidateAllMutation = useInvalidateAll();
  const purgeMutation = usePurgeCache();

  if (isLoading) {
    return <div className="p-4">Chargement...</div>;
  }

  if (!dashboard) {
    return <div className="p-4">Aucune donnee disponible</div>;
  }

  const { stats, top_keys, recent_invalidations, active_alerts } = dashboard;

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

export default DashboardView;
