/**
 * AZALSCORE Module - Purchases - Orders List
 * ==========================================
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import { Button } from '@ui/actions';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn, TableAction } from '@/types';
import { usePurchaseOrders, useSuppliersLookup, useDeletePurchaseOrder, useValidatePurchaseOrder } from '../../hooks';
import { FilterBar, OrderStatusBadge, type FilterState } from '../../components';
import { ORDER_STATUS_CONFIG, type PurchaseOrder, type PurchaseOrderStatus } from '../../types';

// ============================================================================
// Helpers
// ============================================================================

const formatCurrency = (value: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(value);
};

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString('fr-FR');
};

// ============================================================================
// Component
// ============================================================================

export const OrdersListPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<FilterState>({});

  const { data, isLoading, error: ordersError, refetch } = usePurchaseOrders({
    page,
    page_size: pageSize,
    search: filters.search,
    status: filters.status as PurchaseOrderStatus,
    supplier_id: filters.supplier_id,
    date_from: filters.date_from,
    date_to: filters.date_to,
  });
  const { data: suppliers } = useSuppliersLookup();
  const deleteMutation = useDeletePurchaseOrder();
  const validateMutation = useValidatePurchaseOrder();

  const handleDelete = async (order: PurchaseOrder) => {
    if (order.status !== 'DRAFT') {
      alert('Seules les commandes en brouillon peuvent etre supprimees');
      return;
    }
    if (window.confirm(`Supprimer la commande "${order.number}" ?`)) {
      await deleteMutation.mutateAsync(order.id);
    }
  };

  const handleValidate = async (order: PurchaseOrder) => {
    if (order.status !== 'DRAFT') {
      alert('Seules les commandes en brouillon peuvent etre validees');
      return;
    }
    if (window.confirm(`Valider la commande "${order.number}" ? Cette action est irreversible.`)) {
      await validateMutation.mutateAsync(order.id);
    }
  };

  const columns: TableColumn<PurchaseOrder>[] = [
    { id: 'number', header: 'N', accessor: 'number', sortable: true },
    {
      id: 'supplier',
      header: 'Fournisseur',
      accessor: 'supplier_name',
      render: (_, row) => `${row.supplier_code} - ${row.supplier_name}`,
    },
    {
      id: 'date',
      header: 'Date',
      accessor: 'date',
      render: (value) => formatDate(value as string),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <OrderStatusBadge status={value as string} />,
    },
    {
      id: 'total_ttc',
      header: 'Total TTC',
      accessor: 'total_ttc',
      align: 'right',
      render: (value, row) => formatCurrency(value as number, row.currency),
    },
  ];

  const actions: TableAction<PurchaseOrder>[] = [
    {
      id: 'view',
      label: 'Voir',
      onClick: (row) => navigate(`/purchases/orders/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      onClick: (row) => navigate(`/purchases/orders/${row.id}/edit`),
      capability: 'purchases.edit',
      isDisabled: (row) => row.status !== 'DRAFT',
    },
    {
      id: 'validate',
      label: 'Valider',
      onClick: (row) => handleValidate(row),
      capability: 'purchases.validate',
      isDisabled: (row) => row.status !== 'DRAFT',
    },
    {
      id: 'delete',
      label: 'Supprimer',
      onClick: (row) => handleDelete(row),
      capability: 'purchases.delete',
      variant: 'danger',
      isDisabled: (row) => row.status !== 'DRAFT',
    },
  ];

  const statusOptions = Object.entries(ORDER_STATUS_CONFIG).map(([value, config]) => ({
    value,
    label: config.label,
  }));

  return (
    <PageWrapper
      title="Commandes Fournisseurs"
      actions={
        <CapabilityGuard capability="purchases.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/purchases/orders/new')}>
            Nouvelle commande
          </Button>
        </CapabilityGuard>
      }
    >
      <FilterBar
        filters={filters}
        onChange={setFilters}
        suppliers={suppliers || []}
        statusOptions={statusOptions}
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
          error={ordersError instanceof Error ? ordersError : null}
          onRetry={() => refetch()}
        />
      </Card>
    </PageWrapper>
  );
};

export default OrdersListPage;
