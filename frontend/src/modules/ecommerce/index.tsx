/**
 * AZALSCORE Module - E-commerce
 * Produits, Commandes, Expéditions
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Plus, Package, ShoppingBag, Truck, BarChart3 } from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

interface Product {
  id: string;
  sku: string;
  name: string;
  price: number;
  stock: number;
  status: 'active' | 'draft' | 'archived';
  currency: string;
  image_url?: string;
}

interface Order {
  id: string;
  number: string;
  customer_name: string;
  customer_email: string;
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  total: number;
  currency: string;
  created_at: string;
}

interface EcommerceSummary {
  total_products: number;
  active_products: number;
  pending_orders: number;
  revenue_this_month: number;
  orders_this_month: number;
}

const useSummary = () => {
  return useQuery({
    queryKey: ['ecommerce', 'summary'],
    queryFn: async () => {
      const response = await api.get<EcommerceSummary>('/v1/ecommerce/summary');
      return response.data;
    },
  });
};

const useProducts = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['ecommerce', 'products', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Product>>(`/v1/ecommerce/products?page=${page}&page_size=${pageSize}`);
      return response.data;
    },
  });
};

const useOrders = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['ecommerce', 'orders', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Order>>(`/v1/ecommerce/orders?page=${page}&page_size=${pageSize}`);
      return response.data;
    },
  });
};

const ORDER_STATUS: Record<string, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'orange' },
  confirmed: { label: 'Confirmée', color: 'blue' },
  shipped: { label: 'Expédiée', color: 'blue' },
  delivered: { label: 'Livrée', color: 'green' },
  cancelled: { label: 'Annulée', color: 'red' },
};

export const EcommerceDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = useSummary();

  const kpis: DashboardKPI[] = summary ? [
    { id: 'products', label: 'Produits actifs', value: summary.active_products },
    { id: 'orders', label: 'Commandes en attente', value: summary.pending_orders },
    { id: 'orders_month', label: 'Commandes ce mois', value: summary.orders_this_month },
    { id: 'revenue', label: 'CA ce mois', value: new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(summary.revenue_this_month) },
  ] : [];

  return (
    <PageWrapper title="E-commerce" subtitle="Vente en ligne">
      {isLoading ? <div className="azals-loading"><div className="azals-spinner" /></div> : (
        <>
          <section className="azals-section">
            <Grid cols={4} gap="md">{kpis.map((kpi) => <KPICard key={kpi.id} kpi={kpi} />)}</Grid>
          </section>
          <section className="azals-section">
            <Grid cols={3} gap="md">
              <Card title="Produits" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/ecommerce/products')}>Gérer</Button>}>
                <Package size={32} className="azals-text--primary" /><p>Catalogue produits</p>
              </Card>
              <Card title="Commandes" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/ecommerce/orders')}>Gérer</Button>}>
                <ShoppingBag size={32} className="azals-text--primary" /><p>Commandes clients</p>
              </Card>
              <Card title="Expéditions" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/ecommerce/shipping')}>Gérer</Button>}>
                <Truck size={32} className="azals-text--primary" /><p>Gestion des envois</p>
              </Card>
            </Grid>
          </section>
        </>
      )}
    </PageWrapper>
  );
};

export const ProductsPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const { data, isLoading, refetch } = useProducts(page, pageSize);

  const columns: TableColumn<Product>[] = [
    { id: 'sku', header: 'SKU', accessor: 'sku' },
    { id: 'name', header: 'Nom', accessor: 'name', sortable: true },
    { id: 'price', header: 'Prix', accessor: 'price', align: 'right', render: (v, row) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(v as number) },
    { id: 'stock', header: 'Stock', accessor: 'stock', align: 'right' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => <span className={`azals-badge azals-badge--${v === 'active' ? 'green' : 'gray'}`}>{v === 'active' ? 'Actif' : v === 'draft' ? 'Brouillon' : 'Archivé'}</span> },
  ];

  return (
    <PageWrapper title="Produits" actions={<CapabilityGuard capability="ecommerce.products.create"><Button leftIcon={<Plus size={16} />} onClick={() => navigate('/ecommerce/products/new')}>Nouveau produit</Button></CapabilityGuard>}>
      <Card noPadding><DataTable columns={columns} data={data?.items || []} keyField="id" isLoading={isLoading} pagination={{ page, pageSize, total: data?.total || 0, onPageChange: setPage, onPageSizeChange: setPageSize }} onRefresh={refetch} /></Card>
    </PageWrapper>
  );
};

export const OrdersPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const { data, isLoading, refetch } = useOrders(page, pageSize);

  const columns: TableColumn<Order>[] = [
    { id: 'number', header: 'N°', accessor: 'number' },
    { id: 'customer_name', header: 'Client', accessor: 'customer_name' },
    { id: 'created_at', header: 'Date', accessor: 'created_at', render: (v) => new Date(v as string).toLocaleDateString('fr-FR') },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => <span className={`azals-badge azals-badge--${ORDER_STATUS[v as string]?.color}`}>{ORDER_STATUS[v as string]?.label}</span> },
    { id: 'total', header: 'Total', accessor: 'total', align: 'right', render: (v, row) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(v as number) },
  ];

  return (
    <PageWrapper title="Commandes E-commerce">
      <Card noPadding><DataTable columns={columns} data={data?.items || []} keyField="id" isLoading={isLoading} pagination={{ page, pageSize, total: data?.total || 0, onPageChange: setPage, onPageSizeChange: setPageSize }} onRefresh={refetch} /></Card>
    </PageWrapper>
  );
};

export const EcommerceRoutes: React.FC = () => (
  <Routes>
    <Route index element={<EcommerceDashboard />} />
    <Route path="products" element={<ProductsPage />} />
    <Route path="orders" element={<OrdersPage />} />
  </Routes>
);

export default EcommerceRoutes;
