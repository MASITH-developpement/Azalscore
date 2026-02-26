/**
 * AZALSCORE Module - Triggers - Webhooks Page
 * Endpoints de notification externes
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import type { WebhookEndpoint } from '../types';
import { useWebhooks } from '../hooks';

export const WebhooksPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useWebhooks();

  const columns: TableColumn<WebhookEndpoint>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      render: (value) => <code className="azals-code">{value as string}</code>,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
    },
    {
      id: 'url',
      header: 'URL',
      accessor: 'url',
      render: (value) => (
        <span className="azals-text--muted azals-text--truncate" style={{ maxWidth: 200 }}>
          {value as string}
        </span>
      ),
    },
    {
      id: 'method',
      header: 'Methode',
      accessor: 'method',
    },
    {
      id: 'consecutive_failures',
      header: 'Echecs',
      accessor: 'consecutive_failures',
      align: 'right',
      render: (value) =>
        (value as number) > 0 ? (
          <span className="azals-text--danger">{value as number}</span>
        ) : (
          <span>0</span>
        ),
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Actif</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Inactif</span>
        ),
    },
  ];

  return (
    <PageWrapper
      title="Webhooks"
      subtitle="Endpoints de notification externes"
      actions={
        <CapabilityGuard capability="triggers.webhooks.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/triggers/webhooks/new')}>
            Nouveau
          </Button>
        </CapabilityGuard>
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
          emptyMessage="Aucun webhook"
        />
      </Card>
    </PageWrapper>
  );
};

export default WebhooksPage;
