/**
 * AZALSCORE Module - Achats
 * Commandes, Réceptions, Factures fournisseurs
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Plus, ShoppingCart, Package, FileText } from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

interface PurchaseOrder {
  id: string;
  number: string;
  supplier_id: string;
  supplier_name: string;
  date: string;
  expected_date?: string;
  status: 'draft' | 'sent' | 'confirmed' | 'received' | 'cancelled';
  total_ht: number;
  total_ttc: number;
  currency: string;
}

interface PurchaseSummary {
  pending_orders: number;
  pending_value: number;
  received_this_month: number;
  pending_invoices: number;
}

const usePurchaseSummary = () => {
  return useQuery({
    queryKey: ['purchases', 'summary'],
    queryFn: async () => {
      const response = await api.get<PurchaseSummary>('/v1/purchases/summary');
      return response.data;
    },
  });
};

const usePurchaseOrders = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['purchases', 'orders', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PurchaseOrder>>(
        `/v1/purchases/orders?page=${page}&page_size=${pageSize}`
      );
      return response.data;
    },
  });
};

const STATUS_LABELS: Record<string, string> = {
  draft: 'Brouillon',
  sent: 'Envoyée',
  confirmed: 'Confirmée',
  received: 'Reçue',
  cancelled: 'Annulée',
};

const STATUS_COLORS: Record<string, string> = {
  draft: 'gray',
  sent: 'blue',
  confirmed: 'orange',
  received: 'green',
  cancelled: 'red',
};

export const PurchasesDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = usePurchaseSummary();

  const kpis: DashboardKPI[] = summary
    ? [
        { id: 'pending', label: 'Commandes en cours', value: summary.pending_orders },
        {
          id: 'value',
          label: 'Valeur en attente',
          value: new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
            summary.pending_value
          ),
        },
        { id: 'received', label: 'Reçues ce mois', value: summary.received_this_month },
        { id: 'invoices', label: 'Factures à traiter', value: summary.pending_invoices },
      ]
    : [];

  return (
    <PageWrapper title="Achats" subtitle="Gestion des achats fournisseurs">
      {isLoading ? (
        <div className="azals-loading"><div className="azals-spinner" /></div>
      ) : (
        <>
          <section className="azals-section">
            <Grid cols={4} gap="md">
              {kpis.map((kpi) => <KPICard key={kpi.id} kpi={kpi} />)}
            </Grid>
          </section>

          <section className="azals-section">
            <Grid cols={3} gap="md">
              <Card
                title="Commandes"
                actions={<Button variant="ghost" size="sm" onClick={() => navigate('/purchases/orders')}>Gérer</Button>}
              >
                <ShoppingCart size={32} className="azals-text--primary" />
                <p>Commandes fournisseurs</p>
              </Card>

              <Card
                title="Réceptions"
                actions={<Button variant="ghost" size="sm" onClick={() => navigate('/purchases/receipts')}>Gérer</Button>}
              >
                <Package size={32} className="azals-text--primary" />
                <p>Réception des marchandises</p>
              </Card>

              <Card
                title="Factures"
                actions={<Button variant="ghost" size="sm" onClick={() => navigate('/purchases/invoices')}>Gérer</Button>}
              >
                <FileText size={32} className="azals-text--primary" />
                <p>Factures fournisseurs</p>
              </Card>
            </Grid>
          </section>
        </>
      )}
    </PageWrapper>
  );
};

export const PurchaseOrdersPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const { data, isLoading, refetch } = usePurchaseOrders(page, pageSize);

  const columns: TableColumn<PurchaseOrder>[] = [
    { id: 'number', header: 'N°', accessor: 'number', sortable: true },
    { id: 'supplier_name', header: 'Fournisseur', accessor: 'supplier_name' },
    {
      id: 'date',
      header: 'Date',
      accessor: 'date',
      render: (value) => new Date(value as string).toLocaleDateString('fr-FR'),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => (
        <span className={`azals-badge azals-badge--${STATUS_COLORS[value as string]}`}>
          {STATUS_LABELS[value as string]}
        </span>
      ),
    },
    {
      id: 'total_ttc',
      header: 'Total TTC',
      accessor: 'total_ttc',
      align: 'right',
      render: (value, row) =>
        new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(value as number),
    },
  ];

  return (
    <PageWrapper
      title="Commandes Fournisseurs"
      actions={
        <CapabilityGuard capability="purchases.orders.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/purchases/orders/new')}>
            Nouvelle commande
          </Button>
        </CapabilityGuard>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          isLoading={isLoading}
          pagination={{ page, pageSize, total: data?.total || 0, onPageChange: setPage, onPageSizeChange: setPageSize }}
          onRefresh={refetch}
        />
      </Card>
    </PageWrapper>
  );
};

export const PurchasesRoutes: React.FC = () => (
  <Routes>
    <Route index element={<PurchasesDashboard />} />
    <Route path="orders" element={<PurchaseOrdersPage />} />
  </Routes>
);

export default PurchasesRoutes;
