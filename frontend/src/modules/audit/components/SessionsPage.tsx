/**
 * AZALSCORE Module - Audit - Sessions Page
 * Liste des sessions actives
 */

import React from 'react';
import { RefreshCw } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import { useActiveSessions, useTerminateSession } from '../hooks';
import type { AuditSession } from '../types';

export const SessionsPage: React.FC = () => {
  const { data, isLoading, error, refetch } = useActiveSessions();
  const terminateSession = useTerminateSession();

  const columns: TableColumn<AuditSession>[] = [
    {
      id: 'user_email',
      header: 'Utilisateur',
      accessor: 'user_email',
      render: (value) => (value as string) || 'Inconnu',
    },
    {
      id: 'login_at',
      header: 'Connexion',
      accessor: 'login_at',
      render: (value) => formatDate(value as string),
    },
    {
      id: 'last_activity_at',
      header: 'Derniere activite',
      accessor: 'last_activity_at',
      render: (value) => formatDate(value as string),
    },
    {
      id: 'ip_address',
      header: 'IP',
      accessor: 'ip_address',
      render: (value) => (value as string) || '-',
    },
    {
      id: 'browser',
      header: 'Navigateur',
      accessor: 'browser',
      render: (value, row) => `${(value as string) || '?'} / ${row.os || '?'}`,
    },
    {
      id: 'location',
      header: 'Localisation',
      accessor: 'country',
      render: (_, row) => (row.city && row.country ? `${row.city}, ${row.country}` : '-'),
    },
    {
      id: 'actions_count',
      header: 'Actions',
      accessor: 'actions_count',
      align: 'right',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <CapabilityGuard capability="audit.sessions.terminate">
          <Button
            size="sm"
            variant="danger"
            onClick={() => {
              if (window.confirm('Terminer cette session ?')) {
                terminateSession.mutate({ sessionId: row.session_id });
              }
            }}
            disabled={terminateSession.isPending}
          >
            Terminer
          </Button>
        </CapabilityGuard>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Sessions actives"
      subtitle={data ? `${data.length} sessions actives` : ''}
      actions={
        <Button variant="ghost" leftIcon={<RefreshCw size={16} />} onClick={() => { refetch(); }}>
          Actualiser
        </Button>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? (error as Error) : null}
          onRetry={() => { refetch(); }}
          emptyMessage="Aucune session active"
        />
      </Card>
    </PageWrapper>
  );
};

export default SessionsPage;
