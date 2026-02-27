/**
 * AZALSCORE Module - Cache - Config View
 * Configuration du cache
 */

import React from 'react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { EVICTION_POLICIES, formatBytes } from '../types';
import { useCacheDashboard, useCreateCacheConfig } from '../hooks';
import { Badge } from './helpers';

export const ConfigView: React.FC = () => {
  const { data: dashboard } = useCacheDashboard();
  const config = dashboard?.config;
  const createConfigMutation = useCreateCacheConfig();

  if (!config) {
    return (
      <Card>
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">Aucune configuration cache trouvee</p>
          <Button onClick={() => createConfigMutation.mutate()}>
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

export default ConfigView;
