/**
 * AZALSCORE Module - Cache - Audit View
 * Journal d'audit du cache
 */

import React from 'react';
import { RefreshCw, Check, X } from 'lucide-react';
import { Button } from '@ui/actions';
import { Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import type { CacheAuditLog } from '../types';
import { useAuditLogs } from '../hooks';
import { Badge, formatDateTime } from './helpers';

export const AuditView: React.FC = () => {
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

export default AuditView;
