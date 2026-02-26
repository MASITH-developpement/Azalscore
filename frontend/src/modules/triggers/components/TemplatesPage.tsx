/**
 * AZALSCORE Module - Triggers - Templates Page
 * Modeles de notification
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import type { NotificationTemplate } from '../types';
import { useTemplates } from '../hooks';

export const TemplatesPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useTemplates();

  const columns: TableColumn<NotificationTemplate>[] = [
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
      id: 'is_system',
      header: 'Type',
      accessor: 'is_system',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--blue">Systeme</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Personnalise</span>
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
      title="Templates"
      subtitle="Modeles de notification"
      actions={
        <CapabilityGuard capability="triggers.templates.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/triggers/templates/new')}>
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
          emptyMessage="Aucun template"
        />
      </Card>
    </PageWrapper>
  );
};

export default TemplatesPage;
