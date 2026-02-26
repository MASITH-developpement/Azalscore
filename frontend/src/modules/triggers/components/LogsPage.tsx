/**
 * AZALSCORE Module - Triggers - Logs Page
 * Historique des actions du systeme de triggers
 */

import React from 'react';
import { RefreshCw } from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import type { TriggerLog } from '../types';
import { useTriggerLogs } from '../hooks';

export const LogsPage: React.FC = () => {
  const { data, isLoading, error, refetch } = useTriggerLogs({ limit: 200 });

  const columns: TableColumn<TriggerLog>[] = [
    {
      id: 'created_at',
      header: 'Date',
      accessor: 'created_at',
      sortable: true,
      render: (value) => formatDate(value as string),
    },
    {
      id: 'action',
      header: 'Action',
      accessor: 'action',
    },
    {
      id: 'entity_type',
      header: 'Type',
      accessor: 'entity_type',
    },
    {
      id: 'success',
      header: 'Resultat',
      accessor: 'success',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Succes</span>
        ) : (
          <span className="azals-badge azals-badge--red">Echec</span>
        ),
    },
    {
      id: 'error_message',
      header: 'Erreur',
      accessor: 'error_message',
      render: (value) => (value ? <span className="azals-text--danger">{value as string}</span> : '-'),
    },
  ];

  return (
    <PageWrapper
      title="Logs"
      subtitle="Historique des actions du systeme de triggers"
      actions={
        <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
          Actualiser
        </Button>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.logs || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucun log"
        />
      </Card>
    </PageWrapper>
  );
};

export default LogsPage;
