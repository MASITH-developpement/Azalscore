/**
 * AZALS MODULE GAP-086 - Integration Hub - Executions List
 * Liste des synchronisations
 */

import React, { useState } from 'react';
import { XCircle, RotateCcw } from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import type { SyncExecution, SyncStatus } from '../types';
import { useExecutions, useCancelExecution, useRetryExecution } from '../hooks';
import { SyncStatusBadge } from './StatusBadges';

export interface ExecutionsListProps {
  onBack: () => void;
}

export const ExecutionsList: React.FC<ExecutionsListProps> = ({ onBack }) => {
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

export default ExecutionsList;
