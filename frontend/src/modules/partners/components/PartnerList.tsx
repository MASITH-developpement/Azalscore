/**
 * AZALSCORE Module - Partners - PartnerList Component
 * Composant générique pour lister clients/fournisseurs/contacts
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { z } from 'zod';
import { CapabilityGuard } from '@core/capabilities';
import { Button, Modal } from '@ui/actions';
import { DynamicForm } from '@ui/forms';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { usePartners, useCreatePartner } from '../hooks';
import type { PartnerLegacy } from '../types';

export interface PartnerListProps {
  type: 'client' | 'supplier' | 'contact';
  title: string;
}

export const PartnerList: React.FC<PartnerListProps> = ({ type, title }) => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [showCreate, setShowCreate] = useState(false);

  const { data, isLoading, error, refetch } = usePartners(type, page, pageSize);
  const createPartner = useCreatePartner(type);

  const columns: TableColumn<PartnerLegacy>[] = [
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
      onClick: (row: PartnerLegacy) => navigate(`/partners/${type}s/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      capability: `partners.${type}s.edit`,
      onClick: (row: PartnerLegacy) => navigate(`/partners/${type}s/${row.id}/edit`),
    },
  ];

  const partnerSchema = z.object({
    name: z.string().min(2, 'Nom requis'),
    email: z.string().email('Email invalide').optional().or(z.literal('')),
    phone: z.string().optional(),
    address: z.string().optional(),
    city: z.string().optional(),
    postal_code: z.string().optional(),
    country: z.string().optional(),
  });

  const fields = [
    { name: 'name', label: 'Nom', type: 'text' as const, required: true },
    { name: 'email', label: 'Email', type: 'email' as const },
    { name: 'phone', label: 'Téléphone', type: 'text' as const },
    { name: 'address', label: 'Adresse', type: 'text' as const },
    { name: 'city', label: 'Ville', type: 'text' as const },
    { name: 'postal_code', label: 'Code postal', type: 'text' as const },
    { name: 'country', label: 'Pays', type: 'text' as const },
  ];

  return (
    <PageWrapper
      title={title}
      actions={
        <CapabilityGuard capability={`partners.${type}s.create`}>
          <Button leftIcon={<Plus size={16} />} onClick={() => setShowCreate(true)}>
            Ajouter
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

      {showCreate && (
        <Modal isOpen onClose={() => setShowCreate(false)} title={`Nouveau ${type}`} size="md">
          <DynamicForm
            fields={fields}
            schema={partnerSchema}
            onSubmit={async (data) => {
              await createPartner.mutateAsync({ ...data, type });
              setShowCreate(false);
            }}
            onCancel={() => setShowCreate(false)}
            isLoading={createPartner.isPending}
          />
        </Modal>
      )}
    </PageWrapper>
  );
};

export default PartnerList;
