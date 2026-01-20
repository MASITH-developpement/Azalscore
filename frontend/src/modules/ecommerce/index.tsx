/**
 * AZALSCORE Module - E-commerce
 * Gestion de la vente en ligne - Produits, commandes, catégories et expéditions
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Package, ShoppingCart, Truck, Tag, Euro, TrendingUp, AlertTriangle } from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import type { TableColumn } from '@/types';

// ============================================================================
// TYPES
// ============================================================================

interface Product {
  id: string;
  sku: string;
  name: string;
  description?: string;
  price: number;
  compare_price?: number;
  cost?: number;
  stock: number;
  status: 'ACTIVE' | 'DRAFT' | 'ARCHIVED';
  category_id?: string;
  category_name?: string;
  currency: string;
  image_url?: string;
  weight?: number;
  is_featured: boolean;
  created_at: string;
}

interface Order {
  id: string;
  number: string;
  customer_id?: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  shipping_address?: string;
  billing_address?: string;
  status: OrderStatus;
  payment_status: PaymentStatus;
  subtotal: number;
  shipping_cost: number;
  tax: number;
  total: number;
  currency: string;
  items: OrderItem[];
  tracking_number?: string;
  notes?: string;
  created_at: string;
}

type OrderStatus = 'PENDING' | 'CONFIRMED' | 'PROCESSING' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED' | 'REFUNDED';
type PaymentStatus = 'PENDING' | 'PAID' | 'FAILED' | 'REFUNDED';

interface OrderItem {
  product_id: string;
  product_name: string;
  sku: string;
  quantity: number;
  unit_price: number;
  total: number;
}

interface Category {
  id: string;
  code: string;
  name: string;
  parent_id?: string;
  products_count: number;
  is_active: boolean;
}

interface Shipping {
  id: string;
  order_id: string;
  order_number: string;
  carrier: string;
  tracking_number: string;
  status: 'PENDING' | 'PICKED_UP' | 'IN_TRANSIT' | 'DELIVERED' | 'RETURNED';
  estimated_delivery?: string;
  shipped_at?: string;
  delivered_at?: string;
}

interface EcommerceStats {
  total_products: number;
  active_products: number;
  pending_orders: number;
  orders_today: number;
  orders_this_month: number;
  revenue_today: number;
  revenue_this_month: number;
  low_stock_count: number;
}

// ============================================================================
// CONSTANTES
// ============================================================================

const PRODUCT_STATUS = [
  { value: 'ACTIVE', label: 'Actif' },
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'ARCHIVED', label: 'Archivé' }
];

const ORDER_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'CONFIRMED', label: 'Confirmée' },
  { value: 'PROCESSING', label: 'En préparation' },
  { value: 'SHIPPED', label: 'Expédiée' },
  { value: 'DELIVERED', label: 'Livrée' },
  { value: 'CANCELLED', label: 'Annulée' },
  { value: 'REFUNDED', label: 'Remboursée' }
];

const PAYMENT_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'PAID', label: 'Payé' },
  { value: 'FAILED', label: 'Échoué' },
  { value: 'REFUNDED', label: 'Remboursé' }
];

const SHIPPING_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'PICKED_UP', label: 'Enlevé' },
  { value: 'IN_TRANSIT', label: 'En transit' },
  { value: 'DELIVERED', label: 'Livré' },
  { value: 'RETURNED', label: 'Retourné' }
];

const ORDER_STATUS_COLORS: Record<string, string> = {
  PENDING: 'orange', CONFIRMED: 'blue', PROCESSING: 'blue',
  SHIPPED: 'purple', DELIVERED: 'green', CANCELLED: 'red', REFUNDED: 'gray'
};

const PAYMENT_STATUS_COLORS: Record<string, string> = {
  PENDING: 'orange', PAID: 'green', FAILED: 'red', REFUNDED: 'gray'
};

// ============================================================================
// HELPERS
// ============================================================================

const formatCurrency = (amount: number, currency = 'EUR'): string =>
  new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);

const formatDate = (date: string): string =>
  new Date(date).toLocaleDateString('fr-FR');

const formatDateTime = (date: string): string =>
  new Date(date).toLocaleString('fr-FR');

// ============================================================================
// COMPOSANTS UI
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

const TabNav: React.FC<{
  tabs: { id: string; label: string }[];
  activeTab: string;
  onChange: (id: string) => void;
}> = ({ tabs, activeTab, onChange }) => (
  <div className="azals-tabs">
    {tabs.map(tab => (
      <button
        key={tab.id}
        className={`azals-tab ${activeTab === tab.id ? 'azals-tab--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

// ============================================================================
// API HOOKS
// ============================================================================

const useEcommerceStats = () => {
  return useQuery({
    queryKey: ['ecommerce', 'stats'],
    queryFn: async () => {
      const response = await api.get<EcommerceStats>('/v1/ecommerce/summary');
      return response.data;
    }
  });
};

const useProducts = (filters?: { status?: string; category_id?: string }) => {
  return useQuery({
    queryKey: ['ecommerce', 'products', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.category_id) params.append('category_id', filters.category_id);
      const response = await api.get<{ items: Product[] } | Product[]>(`/v1/ecommerce/products?${params}`);
      const data = response.data;
      return Array.isArray(data) ? data : data.items || [];
    }
  });
};

const useOrders = (filters?: { status?: string; payment_status?: string }) => {
  return useQuery({
    queryKey: ['ecommerce', 'orders', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.payment_status) params.append('payment_status', filters.payment_status);
      const response = await api.get<{ items: Order[] } | Order[]>(`/v1/ecommerce/orders?${params}`);
      const data = response.data;
      return Array.isArray(data) ? data : data.items || [];
    }
  });
};

const useCategories = () => {
  return useQuery({
    queryKey: ['ecommerce', 'categories'],
    queryFn: async () => {
      const response = await api.get<Category[]>('/v1/ecommerce/categories');
      return response.data;
    }
  });
};

const useShippings = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: ['ecommerce', 'shippings', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const response = await api.get<Shipping[]>(`/v1/ecommerce/shippings?${params}`);
      return response.data;
    }
  });
};

const useUpdateOrderStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/v1/ecommerce/orders/${id}/status`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ecommerce', 'orders'] });
      queryClient.invalidateQueries({ queryKey: ['ecommerce', 'stats'] });
    }
  });
};

// ============================================================================
// VUES
// ============================================================================

const ProductsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterCategory, setFilterCategory] = useState<string>('');
  const { data: products = [], isLoading, refetch } = useProducts({
    status: filterStatus || undefined,
    category_id: filterCategory || undefined
  });
  const { data: categories = [] } = useCategories();

  const columns: TableColumn<Product>[] = [
    { id: 'sku', header: 'SKU', accessor: 'sku', render: (v) => <code className="font-mono text-sm">{v as string}</code> },
    { id: 'name', header: 'Produit', accessor: 'name' },
    { id: 'category_name', header: 'Catégorie', accessor: 'category_name', render: (v) => (v as string) || '-' },
    { id: 'price', header: 'Prix', accessor: 'price', align: 'right', render: (v, row) => formatCurrency(v as number, row.currency) },
    { id: 'stock', header: 'Stock', accessor: 'stock', align: 'right', render: (v) => {
      const stock = v as number;
      return <Badge color={stock > 10 ? 'green' : stock > 0 ? 'orange' : 'red'}>{stock}</Badge>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const status = v as string;
      const info = PRODUCT_STATUS.find(s => s.value === status);
      const color = status === 'ACTIVE' ? 'green' : status === 'DRAFT' ? 'orange' : 'gray';
      return <Badge color={color}>{info?.label || status}</Badge>;
    }},
    { id: 'is_featured', header: 'Vedette', accessor: 'is_featured', render: (v) => (v as boolean) ? <Badge color="purple">Oui</Badge> : '-' }
  ];

  return (
    <Card title="Produits" actions={<Button>Nouveau produit</Button>}>
      <div className="azals-filter-bar mb-4">
        <Select
          value={filterCategory}
          onChange={(v) => setFilterCategory(v)}
          options={[{ value: '', label: 'Toutes catégories' }, ...categories.map(c => ({ value: c.id, label: c.name }))]}
          placeholder="Catégorie"
        />
        <Select
          value={filterStatus}
          onChange={(v) => setFilterStatus(v)}
          options={[{ value: '', label: 'Tous statuts' }, ...PRODUCT_STATUS]}
          placeholder="Statut"
        />
      </div>
      <DataTable columns={columns} data={products} keyField="id" isLoading={isLoading} onRefresh={refetch} emptyMessage="Aucun produit" />
    </Card>
  );
};

const OrdersView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterPayment, setFilterPayment] = useState<string>('');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const { data: orders = [], isLoading, refetch } = useOrders({
    status: filterStatus || undefined,
    payment_status: filterPayment || undefined
  });
  const updateStatus = useUpdateOrderStatus();

  const columns: TableColumn<Order>[] = [
    { id: 'number', header: 'N° Commande', accessor: 'number', render: (v) => <code className="font-mono text-sm">{v as string}</code> },
    { id: 'customer_name', header: 'Client', accessor: 'customer_name' },
    { id: 'created_at', header: 'Date', accessor: 'created_at', render: (v) => formatDateTime(v as string) },
    { id: 'items', header: 'Articles', accessor: 'items', render: (v) => <Badge color="blue">{(v as OrderItem[])?.length || 0}</Badge> },
    { id: 'total', header: 'Total', accessor: 'total', align: 'right', render: (v, row) => formatCurrency(v as number, row.currency) },
    { id: 'payment_status', header: 'Paiement', accessor: 'payment_status', render: (v) => {
      const status = v as string;
      const info = PAYMENT_STATUS.find(s => s.value === status);
      return <Badge color={PAYMENT_STATUS_COLORS[status] || 'gray'}>{info?.label || status}</Badge>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const status = v as string;
      const info = ORDER_STATUS.find(s => s.value === status);
      return <Badge color={ORDER_STATUS_COLORS[status] || 'gray'}>{info?.label || status}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: (row) => row, render: (_, row) => (
      <Button variant="ghost" size="sm" onClick={() => setSelectedOrder(row)}>Détail</Button>
    )}
  ];

  return (
    <>
      <Card title="Commandes">
        <div className="azals-filter-bar mb-4">
          <Select
            value={filterPayment}
            onChange={(v) => setFilterPayment(v)}
            options={[{ value: '', label: 'Tous paiements' }, ...PAYMENT_STATUS]}
            placeholder="Paiement"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...ORDER_STATUS]}
            placeholder="Statut"
          />
        </div>
        <DataTable columns={columns} data={orders} keyField="id" isLoading={isLoading} onRefresh={refetch} emptyMessage="Aucune commande" />
      </Card>

      <Modal isOpen={!!selectedOrder} onClose={() => setSelectedOrder(null)} title={`Commande ${selectedOrder?.number}`} size="lg">
        {selectedOrder && (
          <div className="space-y-4">
            <Grid cols={2}>
              <div>
                <h4 className="font-semibold mb-2">Client</h4>
                <p>{selectedOrder.customer_name}</p>
                <p className="text-sm text-muted">{selectedOrder.customer_email}</p>
                {selectedOrder.customer_phone && <p className="text-sm text-muted">{selectedOrder.customer_phone}</p>}
              </div>
              <div>
                <h4 className="font-semibold mb-2">Adresse de livraison</h4>
                <p className="text-sm">{selectedOrder.shipping_address || 'Non renseignée'}</p>
              </div>
            </Grid>

            <div>
              <h4 className="font-semibold mb-2">Articles</h4>
              <table className="azals-table w-full text-sm">
                <thead><tr><th>Produit</th><th className="text-right">Qté</th><th className="text-right">Prix unit.</th><th className="text-right">Total</th></tr></thead>
                <tbody>
                  {selectedOrder.items?.map((item, i) => (
                    <tr key={i}><td>{item.product_name}</td><td className="text-right">{item.quantity}</td><td className="text-right">{formatCurrency(item.unit_price)}</td><td className="text-right">{formatCurrency(item.total)}</td></tr>
                  ))}
                </tbody>
                <tfoot className="font-semibold">
                  <tr><td colSpan={3} className="text-right">Sous-total</td><td className="text-right">{formatCurrency(selectedOrder.subtotal)}</td></tr>
                  <tr><td colSpan={3} className="text-right">Livraison</td><td className="text-right">{formatCurrency(selectedOrder.shipping_cost)}</td></tr>
                  <tr><td colSpan={3} className="text-right">TVA</td><td className="text-right">{formatCurrency(selectedOrder.tax)}</td></tr>
                  <tr className="text-lg"><td colSpan={3} className="text-right">Total</td><td className="text-right">{formatCurrency(selectedOrder.total)}</td></tr>
                </tfoot>
              </table>
            </div>

            <div className="flex justify-between items-center pt-4 border-t">
              <div className="flex gap-2 items-center">
                <span className="font-semibold">Changer statut:</span>
                <Select
                  value={selectedOrder.status}
                  onChange={(v) => {
                    updateStatus.mutate({ id: selectedOrder.id, status: v });
                    setSelectedOrder({ ...selectedOrder, status: v as OrderStatus });
                  }}
                  options={ORDER_STATUS}
                />
              </div>
              <Button onClick={() => setSelectedOrder(null)}>Fermer</Button>
            </div>
          </div>
        )}
      </Modal>
    </>
  );
};

const CategoriesView: React.FC = () => {
  const { data: categories = [], isLoading, refetch } = useCategories();

  const columns: TableColumn<Category>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'products_count', header: 'Produits', accessor: 'products_count', render: (v) => <Badge color="blue">{v as number}</Badge> },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge> }
  ];

  return (
    <Card title="Catégories" actions={<Button>Nouvelle catégorie</Button>}>
      <DataTable columns={columns} data={categories} keyField="id" isLoading={isLoading} onRefresh={refetch} emptyMessage="Aucune catégorie" />
    </Card>
  );
};

const ShippingsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: shippings = [], isLoading, refetch } = useShippings({ status: filterStatus || undefined });

  const columns: TableColumn<Shipping>[] = [
    { id: 'order_number', header: 'Commande', accessor: 'order_number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'carrier', header: 'Transporteur', accessor: 'carrier' },
    { id: 'tracking_number', header: 'N° Suivi', accessor: 'tracking_number', render: (v) => <code className="font-mono text-sm">{(v as string) || '-'}</code> },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const status = v as string;
      const info = SHIPPING_STATUS.find(s => s.value === status);
      const colors: Record<string, string> = { PENDING: 'orange', PICKED_UP: 'blue', IN_TRANSIT: 'purple', DELIVERED: 'green', RETURNED: 'red' };
      return <Badge color={colors[status] || 'gray'}>{info?.label || status}</Badge>;
    }},
    { id: 'estimated_delivery', header: 'Livraison prévue', accessor: 'estimated_delivery', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'shipped_at', header: 'Expédié le', accessor: 'shipped_at', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'delivered_at', header: 'Livré le', accessor: 'delivered_at', render: (v) => (v as string) ? formatDate(v as string) : '-' }
  ];

  return (
    <Card title="Expéditions">
      <div className="azals-filter-bar mb-4">
        <Select
          value={filterStatus}
          onChange={(v) => setFilterStatus(v)}
          options={[{ value: '', label: 'Tous statuts' }, ...SHIPPING_STATUS]}
          placeholder="Statut"
        />
      </div>
      <DataTable columns={columns} data={shippings} keyField="id" isLoading={isLoading} onRefresh={refetch} emptyMessage="Aucune expédition" />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'products' | 'orders' | 'categories' | 'shippings';

const EcommerceModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats } = useEcommerceStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'products', label: 'Produits' },
    { id: 'orders', label: 'Commandes' },
    { id: 'categories', label: 'Catégories' },
    { id: 'shippings', label: 'Expéditions' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'products': return <ProductsView />;
      case 'orders': return <OrdersView />;
      case 'categories': return <CategoriesView />;
      case 'shippings': return <ShippingsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard title="Produits actifs" value={String(stats?.active_products || 0)} icon={<Package size={20} />} onClick={() => setCurrentView('products')} />
              <StatCard title="Commandes en attente" value={String(stats?.pending_orders || 0)} icon={<ShoppingCart size={20} />} variant="warning" onClick={() => setCurrentView('orders')} />
              <StatCard title="CA aujourd'hui" value={formatCurrency(stats?.revenue_today || 0)} icon={<Euro size={20} />} variant="success" />
              <StatCard title="CA ce mois" value={formatCurrency(stats?.revenue_this_month || 0)} icon={<TrendingUp size={20} />} />
            </Grid>
            <Grid cols={2}>
              <StatCard title="Commandes aujourd'hui" value={String(stats?.orders_today || 0)} icon={<ShoppingCart size={20} />} />
              <StatCard title="Stock faible" value={String(stats?.low_stock_count || 0)} icon={<AlertTriangle size={20} />} variant={stats?.low_stock_count ? 'danger' : 'success'} />
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="E-commerce" subtitle="Vente en ligne - Produits, commandes et expéditions">
      <TabNav tabs={tabs} activeTab={currentView} onChange={(id) => setCurrentView(id as View)} />
      <div className="mt-4">{renderContent()}</div>
    </PageWrapper>
  );
};

export default EcommerceModule;
