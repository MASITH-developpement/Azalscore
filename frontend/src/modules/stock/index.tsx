import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import { Box, AlertTriangle, DollarSign, BarChart3, Clock, ClipboardList } from 'lucide-react';
import type { TableColumn } from '@/types';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavProps {
  tabs: { id: string; label: string }[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <div className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

// ============================================================================
// TYPES
// ============================================================================

interface Category {
  id: string;
  code: string;
  name: string;
  parent_id?: string;
  is_active: boolean;
}

interface Warehouse {
  id: string;
  code: string;
  name: string;
  address?: string;
  is_active: boolean;
}

interface Location {
  id: string;
  code: string;
  name: string;
  warehouse_id: string;
  warehouse_name?: string;
  type: 'STORAGE' | 'RECEPTION' | 'SHIPPING' | 'PRODUCTION';
  is_active: boolean;
}

interface Product {
  id: string;
  code: string;
  name: string;
  description?: string;
  category_id?: string;
  category_name?: string;
  unit: string;
  cost_price: number;
  sale_price: number;
  min_stock: number;
  max_stock: number;
  current_stock: number;
  is_active: boolean;
  created_at: string;
}

interface Lot {
  id: string;
  number: string;
  product_id: string;
  product_name?: string;
  quantity: number;
  expiry_date?: string;
  warehouse_id: string;
  location_id?: string;
  created_at: string;
}

interface Serial {
  id: string;
  number: string;
  product_id: string;
  product_name?: string;
  lot_id?: string;
  status: 'AVAILABLE' | 'RESERVED' | 'SOLD' | 'SCRAPPED';
  warehouse_id: string;
  location_id?: string;
}

interface Movement {
  id: string;
  number: string;
  type: 'IN' | 'OUT' | 'TRANSFER' | 'ADJUSTMENT';
  date: string;
  product_id: string;
  product_name?: string;
  quantity: number;
  source_location_id?: string;
  source_location_name?: string;
  dest_location_id?: string;
  dest_location_name?: string;
  reference?: string;
  notes?: string;
  status: 'DRAFT' | 'VALIDATED' | 'CANCELLED';
  created_at: string;
}

interface InventoryCount {
  id: string;
  number: string;
  warehouse_id: string;
  warehouse_name?: string;
  date: string;
  status: 'DRAFT' | 'IN_PROGRESS' | 'VALIDATED' | 'CANCELLED';
  lines: InventoryCountLine[];
  created_at: string;
}

interface InventoryCountLine {
  id: string;
  product_id: string;
  product_name?: string;
  location_id?: string;
  theoretical_qty: number;
  counted_qty: number;
  difference: number;
}

interface Picking {
  id: string;
  number: string;
  type: 'INCOMING' | 'OUTGOING' | 'INTERNAL';
  date: string;
  status: 'DRAFT' | 'READY' | 'IN_PROGRESS' | 'DONE' | 'CANCELLED';
  source_location_id?: string;
  dest_location_id?: string;
  reference?: string;
  lines: PickingLine[];
  created_at: string;
}

interface PickingLine {
  id: string;
  product_id: string;
  product_name?: string;
  quantity_planned: number;
  quantity_done: number;
}

interface InventoryDashboard {
  total_products: number;
  low_stock_products: number;
  total_value: number;
  pending_movements: number;
  pending_pickings: number;
  movements_today: number;
  stock_alerts: { product_name: string; current_stock: number; min_stock: number }[];
}

// ============================================================================
// CONSTANTES
// ============================================================================

const MOVEMENT_TYPES = [
  { value: 'IN', label: 'Entree', color: 'green' },
  { value: 'OUT', label: 'Sortie', color: 'red' },
  { value: 'TRANSFER', label: 'Transfert', color: 'blue' },
  { value: 'ADJUSTMENT', label: 'Ajustement', color: 'orange' }
];

const MOVEMENT_STATUSES = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'VALIDATED', label: 'Valide', color: 'green' },
  { value: 'CANCELLED', label: 'Annule', color: 'red' }
];

const PICKING_TYPES = [
  { value: 'INCOMING', label: 'Reception', color: 'green' },
  { value: 'OUTGOING', label: 'Expedition', color: 'blue' },
  { value: 'INTERNAL', label: 'Interne', color: 'purple' }
];

const PICKING_STATUSES = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'READY', label: 'Pret', color: 'blue' },
  { value: 'IN_PROGRESS', label: 'En cours', color: 'orange' },
  { value: 'DONE', label: 'Termine', color: 'green' },
  { value: 'CANCELLED', label: 'Annule', color: 'red' }
];

// ============================================================================
// HELPERS
// ============================================================================

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
};

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const getStatusInfo = (statuses: any[], status: string) => {
  return statuses.find(s => s.value === status) || { label: status, color: 'gray' };
};

// Navigation inter-modules
const navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

// ============================================================================
// API HOOKS
// ============================================================================

const useInventoryDashboard = () => {
  return useQuery({
    queryKey: ['inventory', 'dashboard'],
    queryFn: async () => {
      return api.get<InventoryDashboard>('/v1/inventory/dashboard').then(r => r.data);
    }
  });
};

const useCategories = () => {
  return useQuery({
    queryKey: ['inventory', 'categories'],
    queryFn: async () => {
      const response = await api.get<{ items: Category[] }>('/v1/inventory/categories').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useWarehouses = () => {
  return useQuery({
    queryKey: ['inventory', 'warehouses'],
    queryFn: async () => {
      const response = await api.get<{ items: Warehouse[] }>('/v1/inventory/warehouses').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useLocations = (warehouseId?: string) => {
  return useQuery({
    queryKey: ['inventory', 'locations', warehouseId],
    queryFn: async () => {
      const url = warehouseId
        ? `/v1/inventory/locations?warehouse_id=${encodeURIComponent(warehouseId)}`
        : '/v1/inventory/locations';
      const response = await api.get<{ items: Location[] }>(url).then(r => r.data);
      return response?.items || [];
    }
  });
};

const useProducts = () => {
  return useQuery({
    queryKey: ['inventory', 'products'],
    queryFn: async () => {
      const response = await api.get<{ items: Product[] }>('/v1/inventory/products').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useLots = (productId?: string) => {
  return useQuery({
    queryKey: ['inventory', 'lots', productId],
    queryFn: async () => {
      const url = productId
        ? `/v1/inventory/lots?product_id=${encodeURIComponent(productId)}`
        : '/v1/inventory/lots';
      const response = await api.get<{ items: Lot[] }>(url).then(r => r.data);
      return response?.items || [];
    }
  });
};

const useMovements = () => {
  return useQuery({
    queryKey: ['inventory', 'movements'],
    queryFn: async () => {
      const response = await api.get<{ items: Movement[] }>('/v1/inventory/movements').then(r => r.data);
      return response?.items || [];
    }
  });
};

const usePickings = () => {
  return useQuery({
    queryKey: ['inventory', 'pickings'],
    queryFn: async () => {
      const response = await api.get<{ items: Picking[] }>('/v1/inventory/pickings').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useInventoryCounts = () => {
  return useQuery({
    queryKey: ['inventory', 'counts'],
    queryFn: async () => {
      const response = await api.get<{ items: InventoryCount[] }>('/v1/inventory/counts').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useCreateProduct = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Product>) => {
      return api.post('/v1/inventory/products', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inventory', 'products'] })
  });
};

const useCreateMovement = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Movement>) => {
      return api.post('/v1/inventory/movements', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inventory'] })
  });
};

const useValidateMovement = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/v1/inventory/movements/${id}/validate`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['inventory'] })
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const ProductsView: React.FC = () => {
  const { data: products = [], isLoading } = useProducts();
  const { data: categories = [] } = useCategories();
  const createProduct = useCreateProduct();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<Product>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createProduct.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<Product>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Designation', accessor: 'name' },
    { id: 'category_name', header: 'Categorie', accessor: 'category_name', render: (v) => (v as string) || '-' },
    { id: 'unit', header: 'Unite', accessor: 'unit' },
    { id: 'current_stock', header: 'Stock', accessor: 'current_stock', render: (v, row: Product) => (
      <span className={(v as number) < row.min_stock ? 'text-red-600 font-semibold' : ''}>
        {v as number} {row.unit}
      </span>
    )},
    { id: 'cost_price', header: 'Prix achat', accessor: 'cost_price', render: (v) => formatCurrency(v as number) },
    { id: 'sale_price', header: 'Prix vente', accessor: 'sale_price', render: (v) => formatCurrency(v as number) },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Articles</h3>
        <Button onClick={() => setShowModal(true)}>Nouvel article</Button>
      </div>
      <DataTable columns={columns} data={products} isLoading={isLoading} keyField="id" />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvel article">
        <form onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Code</label>
              <Input
                value={formData.code || ''}
                onChange={(v) => setFormData({ ...formData, code: v })}
              />
            </div>
            <div className="azals-field">
              <label>Designation</label>
              <Input
                value={formData.name || ''}
                onChange={(v) => setFormData({ ...formData, name: v })}
              />
            </div>
          </Grid>
          <div className="azals-field">
            <label>Description</label>
            <Input
              value={formData.description || ''}
              onChange={(v) => setFormData({ ...formData, description: v })}
            />
          </div>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Categorie</label>
              <Select
                value={formData.category_id || ''}
                onChange={(v) => setFormData({ ...formData, category_id: v })}
                options={categories.map(c => ({ value: c.id, label: c.name }))}
              />
            </div>
            <div className="azals-field">
              <label>Unite</label>
              <Input
                value={formData.unit || ''}
                onChange={(v) => setFormData({ ...formData, unit: v })}
                placeholder="pcs, kg, m..."
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Prix d'achat</label>
              <Input
                type="number"
                value={formData.cost_price !== undefined ? String(formData.cost_price) : ''}
                onChange={(v) => setFormData({ ...formData, cost_price: parseFloat(v) })}
              />
            </div>
            <div className="azals-field">
              <label>Prix de vente</label>
              <Input
                type="number"
                value={formData.sale_price !== undefined ? String(formData.sale_price) : ''}
                onChange={(v) => setFormData({ ...formData, sale_price: parseFloat(v) })}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Stock minimum</label>
              <Input
                type="number"
                value={formData.min_stock !== undefined ? String(formData.min_stock) : ''}
                onChange={(v) => setFormData({ ...formData, min_stock: parseInt(v) })}
              />
            </div>
            <div className="azals-field">
              <label>Stock maximum</label>
              <Input
                type="number"
                value={formData.max_stock !== undefined ? String(formData.max_stock) : ''}
                onChange={(v) => setFormData({ ...formData, max_stock: parseInt(v) })}
              />
            </div>
          </Grid>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createProduct.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const WarehousesView: React.FC = () => {
  const { data: warehouses = [], isLoading } = useWarehouses();
  const { data: locations = [] } = useLocations();

  const columns: TableColumn<Warehouse>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'address', header: 'Adresse', accessor: 'address', render: (v) => (v as string) || '-' },
    { id: 'locations_count', header: 'Emplacements', accessor: 'id', render: (_, row: Warehouse) => {
      const count = locations.filter(l => l.warehouse_id === row.id).length;
      return <Badge color="blue">{count}</Badge>;
    }},
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Entrepots</h3>
        <Button>Nouvel entrepot</Button>
      </div>
      <DataTable columns={columns} data={warehouses} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const MovementsView: React.FC = () => {
  const { data: movements = [], isLoading } = useMovements();
  const { data: products = [] } = useProducts();
  const { data: locations = [] } = useLocations();
  const createMovement = useCreateMovement();
  const validateMovement = useValidateMovement();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<Movement>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createMovement.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<Movement>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = getStatusInfo(MOVEMENT_TYPES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'product_name', header: 'Article', accessor: 'product_name' },
    { id: 'quantity', header: 'Quantite', accessor: 'quantity' },
    { id: 'source_location_name', header: 'Source', accessor: 'source_location_name', render: (v) => (v as string) || '-' },
    { id: 'dest_location_name', header: 'Destination', accessor: 'dest_location_name', render: (v) => (v as string) || '-' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(MOVEMENT_STATUSES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row: Movement) => (
      row.status === 'DRAFT' ? (
        <Button size="sm" onClick={() => validateMovement.mutate(row.id)}>Valider</Button>
      ) : null
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Mouvements de stock</h3>
        <Button onClick={() => setShowModal(true)}>Nouveau mouvement</Button>
      </div>
      <DataTable columns={columns} data={movements} isLoading={isLoading} keyField="id" />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouveau mouvement">
        <form onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Type</label>
              <Select
                value={formData.type || ''}
                onChange={(v) => setFormData({ ...formData, type: v as Movement['type'] })}
                options={MOVEMENT_TYPES}
              />
            </div>
            <div className="azals-field">
              <label>Date</label>
              <input
                type="date"
                className="azals-input"
                value={formData.date || ''}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                required
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Article</label>
              <Select
                value={formData.product_id || ''}
                onChange={(v) => setFormData({ ...formData, product_id: v })}
                options={products.map(p => ({ value: p.id, label: `${p.code} - ${p.name}` }))}
              />
            </div>
            <div className="azals-field">
              <label>Quantite</label>
              <Input
                type="number"
                value={formData.quantity !== undefined ? String(formData.quantity) : ''}
                onChange={(v) => setFormData({ ...formData, quantity: parseFloat(v) })}
              />
            </div>
          </Grid>
          {(formData.type === 'OUT' || formData.type === 'TRANSFER') && (
            <div className="azals-field">
              <label>Emplacement source</label>
              <Select
                value={formData.source_location_id || ''}
                onChange={(v) => setFormData({ ...formData, source_location_id: v })}
                options={locations.map(l => ({ value: l.id, label: `${l.warehouse_name} / ${l.name}` }))}
              />
            </div>
          )}
          {(formData.type === 'IN' || formData.type === 'TRANSFER') && (
            <div className="azals-field">
              <label>Emplacement destination</label>
              <Select
                value={formData.dest_location_id || ''}
                onChange={(v) => setFormData({ ...formData, dest_location_id: v })}
                options={locations.map(l => ({ value: l.id, label: `${l.warehouse_name} / ${l.name}` }))}
              />
            </div>
          )}
          <div className="azals-field">
            <label>Notes</label>
            <Input
              value={formData.notes || ''}
              onChange={(v) => setFormData({ ...formData, notes: v })}
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createMovement.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const PickingsView: React.FC = () => {
  const { data: pickings = [], isLoading } = usePickings();

  const columns: TableColumn<Picking>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = getStatusInfo(PICKING_TYPES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'reference', header: 'Reference', accessor: 'reference', render: (v) => (v as string) || '-' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(PICKING_STATUSES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Preparations</h3>
      </div>
      <DataTable columns={columns} data={pickings} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const InventoryCountsView: React.FC = () => {
  const { data: counts = [], isLoading } = useInventoryCounts();

  const columns: TableColumn<InventoryCount>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'warehouse_name', header: 'Entrepot', accessor: 'warehouse_name' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo([
        { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
        { value: 'IN_PROGRESS', label: 'En cours', color: 'orange' },
        { value: 'VALIDATED', label: 'Valide', color: 'green' },
        { value: 'CANCELLED', label: 'Annule', color: 'red' }
      ], v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Inventaires</h3>
        <Button>Nouvel inventaire</Button>
      </div>
      <DataTable columns={columns} data={counts} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'products' | 'warehouses' | 'movements' | 'pickings' | 'counts';

const StockModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: dashboard, isLoading } = useInventoryDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'products', label: 'Articles' },
    { id: 'warehouses', label: 'Entrepots' },
    { id: 'movements', label: 'Mouvements' },
    { id: 'pickings', label: 'Preparations' },
    { id: 'counts', label: 'Inventaires' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'products':
        return <ProductsView />;
      case 'warehouses':
        return <WarehousesView />;
      case 'movements':
        return <MovementsView />;
      case 'pickings':
        return <PickingsView />;
      case 'counts':
        return <InventoryCountsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Articles"
                value={String(dashboard?.total_products || 0)}
                icon={<Box size={24} />}
                variant="default"
                onClick={() => setCurrentView('products')}
              />
              <StatCard
                title="Ruptures de stock"
                value={String(dashboard?.low_stock_products || 0)}
                icon={<AlertTriangle size={24} />}
                variant="danger"
                onClick={() => setCurrentView('products')}
              />
              <StatCard
                title="Valeur du stock"
                value={formatCurrency(dashboard?.total_value || 0)}
                icon={<DollarSign size={24} />}
                variant="success"
              />
              <StatCard
                title="Mouvements du jour"
                value={String(dashboard?.movements_today || 0)}
                icon={<BarChart3 size={24} />}
                variant="default"
                onClick={() => setCurrentView('movements')}
              />
            </Grid>
            <Grid cols={2}>
              <StatCard
                title="Mouvements en attente"
                value={String(dashboard?.pending_movements || 0)}
                icon={<Clock size={24} />}
                variant="warning"
                onClick={() => setCurrentView('movements')}
              />
              <StatCard
                title="Preparations en attente"
                value={String(dashboard?.pending_pickings || 0)}
                icon={<ClipboardList size={24} />}
                variant="default"
                onClick={() => setCurrentView('pickings')}
              />
            </Grid>
            {dashboard?.stock_alerts && dashboard.stock_alerts.length > 0 && (
              <Card>
                <h3 className="text-lg font-semibold mb-4 text-red-600">Alertes de stock</h3>
                <div className="space-y-2">
                  {dashboard.stock_alerts.map((alert, i) => (
                    <div key={i} className="flex justify-between items-center p-2 bg-red-50 rounded border border-red-200">
                      <span>{alert.product_name}</span>
                      <span className="text-red-600 font-semibold">
                        {alert.current_stock} / min: {alert.min_stock}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Stock" subtitle="Gestion des stocks et entrepots">
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default StockModule;
