/**
 * AZALSCORE Module - Cache - Alerts View
 * Gestion des alertes cache
 */

import React from 'react';
import { RefreshCw } from 'lucide-react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import type { CacheAlert } from '../types';
import {
  useCacheAlerts,
  useAcknowledgeAlert,
  useResolveAlert,
  useCheckThresholds,
} from '../hooks';
import { Badge, formatDateTime } from './helpers';

export const AlertsView: React.FC = () => {
  const { data: alerts = [], isLoading, refetch } = useCacheAlerts();
  const acknowledgeAlertMutation = useAcknowledgeAlert();
  const resolveAlertMutation = useResolveAlert();
  const checkThresholdsMutation = useCheckThresholds();

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

export default AlertsView;
