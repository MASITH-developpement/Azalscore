/**
 * AZALSCORE Module - Cache - Preload View
 * Gestion des taches de prechargement
 */

import React from 'react';
import { RefreshCw, Play } from 'lucide-react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import type { PreloadTask } from '../types';
import { usePreloadTasks, useRunPreloadTask } from '../hooks';
import { Badge, formatDateTime } from './helpers';

export const PreloadView: React.FC = () => {
  const { data: tasks = [], isLoading, refetch } = usePreloadTasks();
  const runTaskMutation = useRunPreloadTask();

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

export default PreloadView;
