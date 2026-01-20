/**
 * AZALSCORE Module - Stock & Inventaire
 * Gestion des stocks, entrepôts, mouvements
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Plus, Package, Warehouse, ArrowLeftRight } from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

interface InventoryItem {
  id: string;
  sku: string;
  name: string;
  quantity: number;
  unit: string;
  warehouse_id?: string;
  warehouse_name?: string;
  min_stock?: number;
  max_stock?: number;
}

interface InventoryWarehouse {
  id: string;
  name: string;
  code: string;
  address?: string;
  is_active: boolean;
}

const useWarehouses = () => {
  return useQuery({
    queryKey: ['inventory', 'warehouses'],
    queryFn: async () => {
      const response = await api.get<InventoryWarehouse[]>('/v1/inventory/warehouses');
      return response.data || response || [];
    },
  });
};

const useInventoryItems = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['inventory', 'items', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<InventoryItem>>(
        `/v1/inventory/products?page=${page}&page_size=${pageSize}`
      );
      return response.data || { items: [], total: 0 };
    },
  });
};

export const InventoryDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: warehouses } = useWarehouses();
  const { data: items } = useInventoryItems(1, 100);

  const kpis: DashboardKPI[] = [
    { id: 'warehouses', label: 'Entrepôts', value: Array.isArray(warehouses) ? warehouses.length : 0 },
    { id: 'products', label: 'Produits en stock', value: items?.total || 0 },
    { id: 'lowstock', label: 'Stock bas', value: '-' },
    { id: 'movements', label: 'Mouvements aujourd\'hui', value: '-' },
  ];

  return (
    <PageWrapper title="Stock & Inventaire" subtitle="Gestion des stocks et entrepôts">
      <section className="azals-section">
        <Grid cols={4} gap="md">
          {kpis.map((kpi) => <KPICard key={kpi.id} kpi={kpi} />)}
        </Grid>
      </section>

      <section className="azals-section">
        <Grid cols={3} gap="md">
          <Card
            title="Produits"
            actions={<Button variant="ghost" size="sm" onClick={() => navigate('/inventory/products')}>Voir tout</Button>}
          >
            <Package size={32} className="azals-text--primary" />
            <p>Catalogue produits</p>
          </Card>

          <Card
            title="Entrepôts"
            actions={<Button variant="ghost" size="sm" onClick={() => navigate('/inventory/warehouses')}>Gérer</Button>}
          >
            <Warehouse size={32} className="azals-text--primary" />
            <p>Gestion entrepôts</p>
          </Card>

          <Card
            title="Mouvements"
            actions={<Button variant="ghost" size="sm" onClick={() => navigate('/inventory/movements')}>Voir</Button>}
          >
            <ArrowLeftRight size={32} className="azals-text--primary" />
            <p>Historique mouvements</p>
          </Card>
        </Grid>
      </section>
    </PageWrapper>
  );
};

export const WarehousesListPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading, refetch } = useWarehouses();

  const columns: TableColumn<InventoryWarehouse>[] = [
    { id: 'code', header: 'Code', accessor: 'code', sortable: true },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'address', header: 'Adresse', accessor: 'address' },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) => (
        <span className={`azals-badge azals-badge--${value ? 'green' : 'gray'}`}>
          {value ? 'Actif' : 'Inactif'}
        </span>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Entrepôts"
      actions={
        <CapabilityGuard capability="inventory.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/inventory/warehouses/new')}>
            Nouvel entrepôt
          </Button>
        </CapabilityGuard>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={Array.isArray(data) ? data : []}
          keyField="id"
          isLoading={isLoading}
          onRefresh={refetch}
        />
      </Card>
    </PageWrapper>
  );
};

export const InventoryRoutes: React.FC = () => (
  <Routes>
    <Route index element={<InventoryDashboard />} />
    <Route path="products" element={<InventoryDashboard />} />
    <Route path="warehouses" element={<WarehousesListPage />} />
    <Route path="movements" element={<InventoryDashboard />} />
  </Routes>
);

export default InventoryRoutes;
