/**
 * AZALSCORE Module - Cache - Regions View
 * Gestion des regions de cache
 */

import React from 'react';
import { RefreshCw, Check, X } from 'lucide-react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import type { CacheRegion } from '../types';
import { useCacheRegions, useDeleteRegion } from '../hooks';
import { Badge } from './helpers';

export const RegionsView: React.FC = () => {
  const { data: regions = [], isLoading, refetch } = useCacheRegions();
  const deleteRegionMutation = useDeleteRegion();

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

export default RegionsView;
