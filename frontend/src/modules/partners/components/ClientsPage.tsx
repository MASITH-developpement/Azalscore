/**
 * AZALSCORE Module - Partners - ClientsPage
 * Page liste des clients avec navigation vers formulaire enrichi
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { useClients } from '../hooks';
import type { PartnerLegacy } from '../types';

export const ClientsPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const { data, isLoading, error, refetch } = useClients(page, pageSize);

  const columns: TableColumn<PartnerLegacy>[] = [
    { id: 'code', header: 'Code', accessor: 'code', sortable: true },
    { id: 'name', header: 'Nom', accessor: 'name', sortable: true },
    { id: 'email', header: 'Email', accessor: 'email' },
    { id: 'phone', header: 'Téléphone', accessor: 'phone' },
    { id: 'city', header: 'Ville', accessor: 'city' },
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

  const actions = [
    {
      id: 'view',
      label: 'Voir',
      onClick: (row: PartnerLegacy) => navigate(`/partners/clients/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      capability: 'partners.clients.edit',
      onClick: (row: PartnerLegacy) => navigate(`/partners/clients/${row.id}/edit`),
    },
  ];

  return (
    <PageWrapper
      title="Clients"
      actions={
        <CapabilityGuard capability="partners.clients.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/partners/clients/new')}>
            Nouveau client
          </Button>
        </CapabilityGuard>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          actions={actions}
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
          onRetry={() => refetch()}
        />
      </Card>
    </PageWrapper>
  );
};

export default ClientsPage;
