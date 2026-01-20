import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import type { TableColumn } from '@/types';
import { Store, Hourglass, Package, ClipboardList, ShoppingCart, Banknote, DollarSign, Wallet, BarChart3 } from 'lucide-react';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavItem {
  id: string;
  label: string;
}

interface TabNavProps {
  tabs: TabNavItem[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <nav className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </nav>
);

// ============================================================================
// TYPES
// ============================================================================

interface Seller {
  id: string;
  code: string;
  name: string;
  email: string;
  phone?: string;
  company_name?: string;
  status: 'PENDING' | 'ACTIVE' | 'SUSPENDED' | 'REJECTED';
  commission_rate: number;
  products_count: number;
  total_sales: number;
  total_revenue: number;
  rating?: number;
  joined_at: string;
  is_verified: boolean;
}

interface MarketplaceProduct {
  id: string;
  seller_id: string;
  seller_name: string;
  name: string;
  sku: string;
  price: number;
  currency: string;
  stock: number;
  status: 'DRAFT' | 'PENDING' | 'ACTIVE' | 'REJECTED' | 'SUSPENDED';
  category: string;
  created_at: string;
}

interface MarketplaceOrder {
  id: string;
  number: string;
  seller_id: string;
  seller_name: string;
  customer_name: string;
  status: 'PENDING' | 'CONFIRMED' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED' | 'DISPUTED';
  total: number;
  commission: number;
  net_amount: number;
  currency: string;
  created_at: string;
}

interface Payout {
  id: string;
  seller_id: string;
  seller_name: string;
  amount: number;
  currency: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  period_start: string;
  period_end: string;
  created_at: string;
  paid_at?: string;
}

interface MarketplaceStats {
  total_sellers: number;
  active_sellers: number;
  pending_sellers: number;
  total_products: number;
  active_products: number;
  pending_products: number;
  orders_today: number;
  orders_this_month: number;
  revenue_today: number;
  revenue_this_month: number;
  commission_this_month: number;
  pending_payouts: number;
}

// ============================================================================
// CONSTANTES
// ============================================================================

const SELLER_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'ACTIVE', label: 'Actif' },
  { value: 'SUSPENDED', label: 'Suspendu' },
  { value: 'REJECTED', label: 'Refuse' }
];

const PRODUCT_STATUS = [
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'PENDING', label: 'En attente' },
  { value: 'ACTIVE', label: 'Actif' },
  { value: 'REJECTED', label: 'Refuse' },
  { value: 'SUSPENDED', label: 'Suspendu' }
];

const ORDER_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'CONFIRMED', label: 'Confirmee' },
  { value: 'SHIPPED', label: 'Expediee' },
  { value: 'DELIVERED', label: 'Livree' },
  { value: 'CANCELLED', label: 'Annulee' },
  { value: 'DISPUTED', label: 'Litige' }
];

const PAYOUT_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'PROCESSING', label: 'En cours' },
  { value: 'COMPLETED', label: 'Effectue' },
  { value: 'FAILED', label: 'Echoue' }
];

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'orange',
  ACTIVE: 'green',
  SUSPENDED: 'red',
  REJECTED: 'red',
  DRAFT: 'gray',
  CONFIRMED: 'blue',
  SHIPPED: 'purple',
  DELIVERED: 'green',
  CANCELLED: 'red',
  DISPUTED: 'orange',
  PROCESSING: 'blue',
  COMPLETED: 'green',
  FAILED: 'red'
};

// ============================================================================
// HELPERS
// ============================================================================

const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);
};

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const formatPercent = (value: number): string => {
  return `${value.toFixed(1)}%`;
};

// ============================================================================
// API HOOKS
// ============================================================================

const useMarketplaceStats = () => {
  return useQuery({
    queryKey: ['marketplace', 'stats'],
    queryFn: async () => {
      return api.get<MarketplaceStats>('/v1/marketplace/stats').then(r => r.data);
    }
  });
};

const useSellers = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: ['marketplace', 'sellers', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/v1/marketplace/sellers?${queryString}` : '/v1/marketplace/sellers';
      return api.get<Seller[]>(url).then(r => r.data);
    }
  });
};

const useMarketplaceProducts = (filters?: { status?: string; seller_id?: string }) => {
  return useQuery({
    queryKey: ['marketplace', 'products', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.seller_id) params.append('seller_id', filters.seller_id);
      const queryString = params.toString();
      const url = queryString ? `/v1/marketplace/products?${queryString}` : '/v1/marketplace/products';
      return api.get<MarketplaceProduct[]>(url).then(r => r.data);
    }
  });
};

const useMarketplaceOrders = (filters?: { status?: string; seller_id?: string }) => {
  return useQuery({
    queryKey: ['marketplace', 'orders', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.seller_id) params.append('seller_id', filters.seller_id);
      const queryString = params.toString();
      const url = queryString ? `/v1/marketplace/orders?${queryString}` : '/v1/marketplace/orders';
      return api.get<MarketplaceOrder[]>(url).then(r => r.data);
    }
  });
};

const usePayouts = (filters?: { status?: string; seller_id?: string }) => {
  return useQuery({
    queryKey: ['marketplace', 'payouts', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.seller_id) params.append('seller_id', filters.seller_id);
      const queryString = params.toString();
      const url = queryString ? `/v1/marketplace/payouts?${queryString}` : '/v1/marketplace/payouts';
      return api.get<Payout[]>(url).then(r => r.data);
    }
  });
};

const useUpdateSellerStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/v1/marketplace/sellers/${id}/status`, { status }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace', 'sellers'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace', 'stats'] });
    }
  });
};

const useApproveProduct = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, approved }: { id: string; approved: boolean }) => {
      return api.patch(`/v1/marketplace/products/${id}/review`, { approved }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace', 'products'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace', 'stats'] });
    }
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const SellersView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: sellers = [], isLoading } = useSellers({
    status: filterStatus || undefined
  });
  const updateStatus = useUpdateSellerStatus();

  const columns: TableColumn<Seller>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Vendeur', accessor: 'name' },
    { id: 'company_name', header: 'Societe', accessor: 'company_name', render: (v) => (v as string) || '-' },
    { id: 'email', header: 'Email', accessor: 'email', render: (v) => <span className="text-sm">{v as string}</span> },
    { id: 'products_count', header: 'Produits', accessor: 'products_count', render: (v) => <Badge color="blue">{v as number}</Badge> },
    { id: 'commission_rate', header: 'Commission', accessor: 'commission_rate', render: (v) => formatPercent(v as number) },
    { id: 'total_revenue', header: 'CA Total', accessor: 'total_revenue', render: (v) => formatCurrency(v as number) },
    { id: 'rating', header: 'Note', accessor: 'rating', render: (v) => (v as number) ? `${(v as number).toFixed(1)}/5` : '-' },
    { id: 'is_verified', header: 'Verifie', accessor: 'is_verified', render: (v) => (v as boolean) ? <Badge color="green">Oui</Badge> : <Badge color="gray">Non</Badge> },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = SELLER_STATUS.find(s => s.value === (v as string));
      return <Badge color={STATUS_COLORS[v as string] || 'gray'}>{info?.label || (v as string)}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        {(row as Seller).status === 'PENDING' && (
          <>
            <Button size="sm" variant="success" onClick={() => updateStatus.mutate({ id: (row as Seller).id, status: 'ACTIVE' })}>Approuver</Button>
            <Button size="sm" variant="danger" onClick={() => updateStatus.mutate({ id: (row as Seller).id, status: 'REJECTED' })}>Refuser</Button>
          </>
        )}
        {(row as Seller).status === 'ACTIVE' && (
          <Button size="sm" variant="warning" onClick={() => updateStatus.mutate({ id: (row as Seller).id, status: 'SUSPENDED' })}>Suspendre</Button>
        )}
        {(row as Seller).status === 'SUSPENDED' && (
          <Button size="sm" variant="success" onClick={() => updateStatus.mutate({ id: (row as Seller).id, status: 'ACTIVE' })}>Reactiver</Button>
        )}
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Vendeurs</h3>
        <div className="flex gap-2">
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...SELLER_STATUS]}
            className="w-36"
          />
        </div>
      </div>
      <DataTable columns={columns} data={sellers} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const ProductsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterSeller, setFilterSeller] = useState<string>('');
  const { data: products = [], isLoading } = useMarketplaceProducts({
    status: filterStatus || undefined,
    seller_id: filterSeller || undefined
  });
  const { data: sellers = [] } = useSellers();
  const approveProduct = useApproveProduct();

  const columns: TableColumn<MarketplaceProduct>[] = [
    { id: 'sku', header: 'SKU', accessor: 'sku', render: (v) => <code className="font-mono text-sm">{v as string}</code> },
    { id: 'name', header: 'Produit', accessor: 'name' },
    { id: 'seller_name', header: 'Vendeur', accessor: 'seller_name' },
    { id: 'category', header: 'Categorie', accessor: 'category' },
    { id: 'price', header: 'Prix', accessor: 'price', render: (v, row) => formatCurrency(v as number, (row as MarketplaceProduct).currency) },
    { id: 'stock', header: 'Stock', accessor: 'stock', render: (v) => (
      <Badge color={(v as number) > 10 ? 'green' : (v as number) > 0 ? 'orange' : 'red'}>{v as number}</Badge>
    )},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = PRODUCT_STATUS.find(s => s.value === (v as string));
      return <Badge color={STATUS_COLORS[v as string] || 'gray'}>{info?.label || (v as string)}</Badge>;
    }},
    { id: 'created_at', header: 'Cree le', accessor: 'created_at', render: (v) => formatDate(v as string) },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        {(row as MarketplaceProduct).status === 'PENDING' && (
          <>
            <Button size="sm" variant="success" onClick={() => approveProduct.mutate({ id: (row as MarketplaceProduct).id, approved: true })}>Approuver</Button>
            <Button size="sm" variant="danger" onClick={() => approveProduct.mutate({ id: (row as MarketplaceProduct).id, approved: false })}>Refuser</Button>
          </>
        )}
        <Button size="sm" variant="secondary">Voir</Button>
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Catalogue Marketplace</h3>
        <div className="flex gap-2">
          <Select
            value={filterSeller}
            onChange={(v) => setFilterSeller(v)}
            options={[
              { value: '', label: 'Tous vendeurs' },
              ...sellers.map(s => ({ value: s.id, label: s.name }))
            ]}
            className="w-40"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...PRODUCT_STATUS]}
            className="w-36"
          />
        </div>
      </div>
      <DataTable columns={columns} data={products} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const OrdersView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterSeller, setFilterSeller] = useState<string>('');
  const { data: orders = [], isLoading } = useMarketplaceOrders({
    status: filterStatus || undefined,
    seller_id: filterSeller || undefined
  });
  const { data: sellers = [] } = useSellers();

  const columns: TableColumn<MarketplaceOrder>[] = [
    { id: 'number', header: 'N Commande', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'seller_name', header: 'Vendeur', accessor: 'seller_name' },
    { id: 'customer_name', header: 'Client', accessor: 'customer_name' },
    { id: 'total', header: 'Total', accessor: 'total', render: (v, row) => formatCurrency(v as number, (row as MarketplaceOrder).currency) },
    { id: 'commission', header: 'Commission', accessor: 'commission', render: (v, row) => formatCurrency(v as number, (row as MarketplaceOrder).currency) },
    { id: 'net_amount', header: 'Net vendeur', accessor: 'net_amount', render: (v, row) => formatCurrency(v as number, (row as MarketplaceOrder).currency) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = ORDER_STATUS.find(s => s.value === (v as string));
      return <Badge color={STATUS_COLORS[v as string] || 'gray'}>{info?.label || (v as string)}</Badge>;
    }},
    { id: 'created_at', header: 'Date', accessor: 'created_at', render: (v) => formatDate(v as string) },
    { id: 'actions', header: 'Actions', accessor: 'id', render: () => <Button size="sm" variant="secondary">Detail</Button> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Commandes Marketplace</h3>
        <div className="flex gap-2">
          <Select
            value={filterSeller}
            onChange={(v) => setFilterSeller(v)}
            options={[
              { value: '', label: 'Tous vendeurs' },
              ...sellers.map(s => ({ value: s.id, label: s.name }))
            ]}
            className="w-40"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...ORDER_STATUS]}
            className="w-36"
          />
        </div>
      </div>
      <DataTable columns={columns} data={orders} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const PayoutsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterSeller, setFilterSeller] = useState<string>('');
  const { data: payouts = [], isLoading } = usePayouts({
    status: filterStatus || undefined,
    seller_id: filterSeller || undefined
  });
  const { data: sellers = [] } = useSellers();

  const columns: TableColumn<Payout>[] = [
    { id: 'seller_name', header: 'Vendeur', accessor: 'seller_name' },
    { id: 'period', header: 'Periode', accessor: 'period_start', render: (v, row) => (
      `${formatDate(v as string)} - ${formatDate((row as Payout).period_end)}`
    )},
    { id: 'amount', header: 'Montant', accessor: 'amount', render: (v, row) => formatCurrency(v as number, (row as Payout).currency) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = PAYOUT_STATUS.find(s => s.value === (v as string));
      return <Badge color={STATUS_COLORS[v as string] || 'gray'}>{info?.label || (v as string)}</Badge>;
    }},
    { id: 'created_at', header: 'Cree le', accessor: 'created_at', render: (v) => formatDate(v as string) },
    { id: 'paid_at', header: 'Paye le', accessor: 'paid_at', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        {(row as Payout).status === 'PENDING' && (
          <Button size="sm" variant="success">Valider</Button>
        )}
        <Button size="sm" variant="secondary">Detail</Button>
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Paiements vendeurs</h3>
        <div className="flex gap-2">
          <Select
            value={filterSeller}
            onChange={(v) => setFilterSeller(v)}
            options={[
              { value: '', label: 'Tous vendeurs' },
              ...sellers.map(s => ({ value: s.id, label: s.name }))
            ]}
            className="w-40"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...PAYOUT_STATUS]}
            className="w-36"
          />
        </div>
      </div>
      <DataTable columns={columns} data={payouts} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'sellers' | 'products' | 'orders' | 'payouts';

const MarketplaceModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats } = useMarketplaceStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'sellers', label: 'Vendeurs' },
    { id: 'products', label: 'Catalogue' },
    { id: 'orders', label: 'Commandes' },
    { id: 'payouts', label: 'Paiements' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'sellers':
        return <SellersView />;
      case 'products':
        return <ProductsView />;
      case 'orders':
        return <OrdersView />;
      case 'payouts':
        return <PayoutsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Vendeurs actifs"
                value={String(stats?.active_sellers || 0)}
                icon={<Store />}
                variant="success"
                onClick={() => setCurrentView('sellers')}
              />
              <StatCard
                title="Vendeurs en attente"
                value={String(stats?.pending_sellers || 0)}
                icon={<Hourglass />}
                variant="warning"
                onClick={() => setCurrentView('sellers')}
              />
              <StatCard
                title="Produits actifs"
                value={String(stats?.active_products || 0)}
                icon={<Package />}
                variant="default"
                onClick={() => setCurrentView('products')}
              />
              <StatCard
                title="Produits en attente"
                value={String(stats?.pending_products || 0)}
                icon={<ClipboardList />}
                variant="warning"
                onClick={() => setCurrentView('products')}
              />
            </Grid>

            <Grid cols={3}>
              <StatCard
                title="Commandes aujourd'hui"
                value={String(stats?.orders_today || 0)}
                icon={<ShoppingCart />}
                variant="default"
                onClick={() => setCurrentView('orders')}
              />
              <StatCard
                title="CA ce mois"
                value={formatCurrency(stats?.revenue_this_month || 0)}
                icon={<Banknote />}
                variant="success"
              />
              <StatCard
                title="Commission ce mois"
                value={formatCurrency(stats?.commission_this_month || 0)}
                icon={<DollarSign />}
                variant="default"
              />
            </Grid>

            <Grid cols={2}>
              <StatCard
                title="Paiements en attente"
                value={String(stats?.pending_payouts || 0)}
                icon={<Wallet />}
                variant={stats?.pending_payouts ? 'warning' : 'success'}
                onClick={() => setCurrentView('payouts')}
              />
              <StatCard
                title="Commandes ce mois"
                value={String(stats?.orders_this_month || 0)}
                icon={<BarChart3 />}
                variant="default"
              />
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Marketplace" subtitle="Place de marche multi-vendeurs">
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

export default MarketplaceModule;
