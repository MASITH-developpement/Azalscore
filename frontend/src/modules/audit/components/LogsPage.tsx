/**
 * AZALSCORE Module - Audit - Logs Page
 * Liste des logs d'audit avec filtres
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Filter, RefreshCw, CheckCircle, XCircle } from 'lucide-react';
import { Button, ButtonGroup } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import { useAuditLogs } from '../hooks';
import { AUDIT_ACTION_LABELS, AUDIT_LEVEL_CONFIG } from '../types';
import type { AuditLog } from '../types';

export const LogsPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const { data, isLoading, error, refetch } = useAuditLogs({ page, page_size: pageSize });

  const columns: TableColumn<AuditLog>[] = [
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
      render: (value) => AUDIT_ACTION_LABELS[value as keyof typeof AUDIT_ACTION_LABELS] || String(value),
    },
    {
      id: 'level',
      header: 'Niveau',
      accessor: 'level',
      render: (value) => {
        const config = AUDIT_LEVEL_CONFIG[value as keyof typeof AUDIT_LEVEL_CONFIG];
        return <span className={`azals-badge azals-badge--${config?.color || 'gray'}`}>{config?.label || String(value)}</span>;
      },
    },
    {
      id: 'module',
      header: 'Module',
      accessor: 'module',
    },
    {
      id: 'user_email',
      header: 'Utilisateur',
      accessor: 'user_email',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'success',
      header: 'Resultat',
      accessor: 'success',
      render: (value) =>
        value ? (
          <CheckCircle size={16} className="azals-text--success" />
        ) : (
          <XCircle size={16} className="azals-text--danger" />
        ),
    },
    {
      id: 'description',
      header: 'Description',
      accessor: 'description',
      render: (value) => (
        <span className="azals-text--truncate" style={{ maxWidth: 200 }}>
          {(value as string) || '-'}
        </span>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Logs d'audit"
      subtitle={data ? `${data.total} logs au total` : ''}
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<Filter size={16} />}>
            Filtrer
          </Button>
          <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
            Actualiser
          </Button>
        </ButtonGroup>
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
          onRowClick={(row) => navigate(`/audit/logs/${row.id}`)}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          emptyMessage="Aucun log"
        />
      </Card>
    </PageWrapper>
  );
};

export default LogsPage;
