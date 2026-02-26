/**
 * AZALSCORE Module - Purchases - Suppliers List
 * ==============================================
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn, TableAction } from '@/types';
import { useSuppliers, useDeleteSupplier } from '../../hooks';
import { FilterBar, SupplierStatusBadge, type FilterState } from '../../components';
import { SUPPLIER_STATUS_CONFIG, type Supplier } from '../../types';

// ============================================================================
// Component
// ============================================================================

export const SuppliersListPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<FilterState>({});

  const { data, isLoading, error: suppliersError, refetch } = useSuppliers({
    page,
    page_size: pageSize,
    search: filters.search,
    status: filters.status as Supplier['status'],
  });
  const deleteMutation = useDeleteSupplier();

  const handleDelete = async (supplier: Supplier) => {
    if (window.confirm(`Supprimer le fournisseur "${supplier.name}" ?`)) {
      await deleteMutation.mutateAsync(supplier.id);
    }
  };

  const columns: TableColumn<Supplier>[] = [
    { id: 'code', header: 'Code', accessor: 'code', sortable: true },
    { id: 'name', header: 'Nom', accessor: 'name', sortable: true },
    { id: 'contact_name', header: 'Contact', accessor: 'contact_name' },
    { id: 'email', header: 'Email', accessor: 'email' },
    { id: 'phone', header: 'Telephone', accessor: 'phone' },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <SupplierStatusBadge status={value as string} />,
    },
  ];

  const actions: TableAction<Supplier>[] = [
    {
      id: 'view',
      label: 'Voir',
      onClick: (row) => navigate(`/purchases/suppliers/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      onClick: (row) => navigate(`/purchases/suppliers/${row.id}/edit`),
      capability: 'purchases.edit',
    },
    {
      id: 'delete',
      label: 'Supprimer',
      onClick: (row) => handleDelete(row),
      capability: 'purchases.delete',
      variant: 'danger',
    },
  ];

  const statusOptions = Object.entries(SUPPLIER_STATUS_CONFIG).map(([value, config]) => ({
    value,
    label: config.label,
  }));

  return (
    <PageWrapper
      title="Fournisseurs"
      actions={
        <CapabilityGuard capability="purchases.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/purchases/suppliers/new')}>
            Nouveau fournisseur
          </Button>
        </CapabilityGuard>
      }
    >
      <FilterBar
        filters={filters}
        onChange={setFilters}
        statusOptions={statusOptions}
        showSupplierFilter={false}
      />
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
          error={suppliersError instanceof Error ? suppliersError : null}
          onRetry={() => refetch()}
        />
      </Card>
    </PageWrapper>
  );
};

export default SuppliersListPage;
