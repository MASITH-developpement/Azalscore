/**
 * AZALSCORE Module - E-commerce
 * Gestion de la vente en ligne - Produits, commandes, categories et expeditions
 */

import React, { useState } from 'react';
import {
  Package, ShoppingCart, Truck, Tag, Euro, TrendingUp, AlertTriangle,
  ArrowLeft, Edit, Printer, Clock, FileText, Sparkles
} from 'lucide-react';
import { Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { Button } from '@ui/actions';
import { LoadingState, ErrorState } from '@ui/components/StateViews';
import { StatCard } from '@ui/dashboards';
import { Select } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import {
  BaseViewStandard,
  type TabDefinition,
  type InfoBarItem,
  type SidebarSection,
  type ActionDefinition,
  type SemanticColor
} from '@ui/standards';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';

// Types et helpers
import { formatCurrency, formatDate, formatDateTime } from '@/utils/formatters';

// Hooks
import {
  ecommerceKeys,
  useEcommerceStats,
  useProducts,
  useProduct,
  useOrders,
  useOrder,
  useCategories,
  useShippings
} from './hooks';

// Composants tabs
import {
  ProductInfoTab, ProductStockTab, ProductDocumentsTab, ProductHistoryTab, ProductIATab,
  OrderInfoTab, OrderItemsTab, OrderShippingTab, OrderDocumentsTab, OrderHistoryTab, OrderIATab
} from './components';
import {
  PRODUCT_STATUS_CONFIG, ORDER_STATUS_CONFIG, PAYMENT_STATUS_CONFIG, SHIPPING_STATUS_CONFIG,
  isLowStock, isOutOfStock, calculateMargin
} from './types';
import type { Product, Order, Category, Shipping, OrderItem } from './types';

// ============================================================================
// CONSTANTES LOCALES
// ============================================================================

const PRODUCT_STATUS = [
  { value: 'ACTIVE', label: 'Actif' },
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'ARCHIVED', label: 'Archive' }
];

const ORDER_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'CONFIRMED', label: 'Confirmee' },
  { value: 'PROCESSING', label: 'En preparation' },
  { value: 'SHIPPED', label: 'Expediee' },
  { value: 'DELIVERED', label: 'Livree' },
  { value: 'CANCELLED', label: 'Annulee' },
  { value: 'REFUNDED', label: 'Remboursee' }
];

const PAYMENT_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'PAID', label: 'Paye' },
  { value: 'FAILED', label: 'Echoue' },
  { value: 'REFUNDED', label: 'Rembourse' }
];

const SHIPPING_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'PICKED_UP', label: 'Enleve' },
  { value: 'IN_TRANSIT', label: 'En transit' },
  { value: 'DELIVERED', label: 'Livre' },
  { value: 'RETURNED', label: 'Retourne' }
];

// ============================================================================
// COMPOSANTS UI LOCAUX
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
// DETAIL VIEWS (BaseViewStandard)
// ============================================================================

/**
 * ProductDetailView - Vue detail produit avec BaseViewStandard
 */
const ProductDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: product, isLoading, error, refetch } = useProduct(id || '');

  if (isLoading) {
    return <LoadingState onRetry={() => refetch()} message="Chargement du produit..." />;
  }

  if (error || !product) {
    return (
      <ErrorState
        message="Erreur lors du chargement du produit"
        onRetry={() => refetch()}
        onBack={() => navigate('/ecommerce')}
      />
    );
  }

  const statusConfig = PRODUCT_STATUS_CONFIG[product.status];
  const statusColorMap: Record<string, SemanticColor> = {
    green: 'green', orange: 'orange', gray: 'gray', red: 'red', blue: 'blue', purple: 'purple'
  };

  const lowStock = isLowStock(product);
  const outStock = isOutOfStock(product);
  const margin = product.cost ? calculateMargin(product.price, product.cost) : null;

  // Tabs
  const tabs: TabDefinition<Product>[] = [
    { id: 'info', label: 'Informations', icon: <Package size={16} />, component: ProductInfoTab },
    { id: 'stock', label: 'Stock', icon: <Tag size={16} />, badge: outStock ? 1 : lowStock ? 1 : undefined, component: ProductStockTab },
    { id: 'documents', label: 'Documents', icon: <FileText size={16} />, component: ProductDocumentsTab },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: ProductHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: ProductIATab }
  ];

  // Info bar
  const infoBarItems: InfoBarItem[] = [
    { id: 'status', label: 'Statut', value: statusConfig.label, valueColor: statusColorMap[statusConfig.color] || 'gray' },
    { id: 'stock', label: 'Stock', value: String(product.stock), valueColor: outStock ? 'red' : lowStock ? 'orange' : 'green' },
    { id: 'price', label: 'Prix', value: formatCurrency(product.price, product.currency), valueColor: 'blue' },
    { id: 'margin', label: 'Marge', value: margin !== null ? `${margin.toFixed(0)}%` : '-', valueColor: margin && margin >= 30 ? 'green' : margin && margin >= 15 ? 'orange' : 'gray' }
  ];

  // Sidebar
  const sidebarSections: SidebarSection[] = [
    {
      id: 'identification',
      title: 'Identification',
      items: [
        { id: 'sku', label: 'SKU', value: product.sku },
        { id: 'category', label: 'Categorie', value: product.category_name || '-' },
        { id: 'barcode', label: 'Code-barres', value: product.barcode || '-' }
      ]
    },
    {
      id: 'tarification',
      title: 'Tarification',
      items: [
        { id: 'price', label: 'Prix vente', value: formatCurrency(product.price, product.currency) },
        { id: 'cost', label: 'Prix achat', value: product.cost ? formatCurrency(product.cost, product.currency) : '-' },
        { id: 'compare', label: 'Prix barre', value: product.compare_price ? formatCurrency(product.compare_price, product.currency) : '-' }
      ]
    },
    {
      id: 'stock',
      title: 'Stock',
      items: [
        { id: 'qty', label: 'Quantite', value: String(product.stock), highlight: outStock || lowStock },
        { id: 'featured', label: 'Vedette', value: product.is_featured ? 'Oui' : 'Non' }
      ]
    }
  ];

  // Actions
  const headerActions: ActionDefinition[] = [
    { id: 'back', label: 'Retour', icon: <ArrowLeft size={16} />, variant: 'ghost', onClick: () => navigate('/ecommerce') },
    { id: 'edit', label: 'Modifier', icon: <Edit size={16} />, variant: 'secondary', onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'editProduct', productId: product.id } })); } }
  ];

  return (
    <BaseViewStandard<Product>
      title={product.name}
      subtitle={`SKU: ${product.sku}`}
      status={{ label: statusConfig.label, color: statusColorMap[statusConfig.color] || 'gray' }}
      data={product}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
    />
  );
};

/**
 * OrderDetailView - Vue detail commande avec BaseViewStandard
 */
const OrderDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: order, isLoading, error, refetch } = useOrder(id || '');

  if (isLoading) {
    return <LoadingState onRetry={() => refetch()} message="Chargement de la commande..." />;
  }

  if (error || !order) {
    return (
      <ErrorState
        message="Erreur lors du chargement de la commande"
        onRetry={() => refetch()}
        onBack={() => navigate('/ecommerce')}
      />
    );
  }

  const statusConfig = ORDER_STATUS_CONFIG[order.status];
  const paymentConfig = PAYMENT_STATUS_CONFIG[order.payment_status];
  const statusColorMap: Record<string, SemanticColor> = {
    green: 'green', orange: 'orange', gray: 'gray', red: 'red', blue: 'blue', purple: 'purple'
  };

  // Tabs
  const tabs: TabDefinition<Order>[] = [
    { id: 'info', label: 'Informations', icon: <ShoppingCart size={16} />, component: OrderInfoTab },
    { id: 'items', label: 'Articles', icon: <Package size={16} />, badge: order.items.length, component: OrderItemsTab },
    { id: 'shipping', label: 'Expedition', icon: <Truck size={16} />, component: OrderShippingTab },
    { id: 'documents', label: 'Documents', icon: <FileText size={16} />, component: OrderDocumentsTab },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: OrderHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: OrderIATab }
  ];

  // Info bar
  const infoBarItems: InfoBarItem[] = [
    { id: 'status', label: 'Statut', value: statusConfig.label, valueColor: statusColorMap[statusConfig.color] || 'gray' },
    { id: 'payment', label: 'Paiement', value: paymentConfig.label, valueColor: statusColorMap[paymentConfig.color] || 'gray' },
    { id: 'total', label: 'Total', value: formatCurrency(order.total, order.currency), valueColor: 'blue' },
    { id: 'items', label: 'Articles', value: String(order.items.length), valueColor: 'gray' }
  ];

  // Sidebar
  const sidebarSections: SidebarSection[] = [
    {
      id: 'commande',
      title: 'Commande',
      items: [
        { id: 'number', label: 'Numero', value: order.number },
        { id: 'date', label: 'Date', value: formatDateTime(order.created_at) },
        { id: 'source', label: 'Source', value: order.source || '-' }
      ]
    },
    {
      id: 'client',
      title: 'Client',
      items: [
        { id: 'name', label: 'Nom', value: order.customer_name },
        { id: 'email', label: 'Email', value: order.customer_email },
        { id: 'phone', label: 'Telephone', value: order.customer_phone || '-' }
      ]
    },
    {
      id: 'montants',
      title: 'Montants',
      items: [
        { id: 'subtotal', label: 'Sous-total', value: formatCurrency(order.subtotal, order.currency) },
        { id: 'shipping', label: 'Livraison', value: formatCurrency(order.shipping_cost, order.currency) },
        { id: 'tax', label: 'TVA', value: formatCurrency(order.tax, order.currency) },
        { id: 'total', label: 'Total TTC', value: formatCurrency(order.total, order.currency), highlight: true }
      ]
    },
    {
      id: 'expedition',
      title: 'Expedition',
      items: [
        { id: 'tracking', label: 'N° suivi', value: order.tracking_number || '-' },
        { id: 'carrier', label: 'Transporteur', value: order.carrier || '-' }
      ]
    }
  ];

  // Actions
  const headerActions: ActionDefinition[] = [
    { id: 'back', label: 'Retour', icon: <ArrowLeft size={16} />, variant: 'ghost', onClick: () => navigate('/ecommerce') },
    { id: 'print', label: 'Imprimer', icon: <Printer size={16} />, variant: 'secondary', onClick: () => { window.print(); } }
  ];

  return (
    <BaseViewStandard<Order>
      title={`Commande ${order.number}`}
      subtitle={`${order.customer_name} - ${formatDate(order.created_at)}`}
      status={{ label: statusConfig.label, color: statusColorMap[statusConfig.color] || 'gray' }}
      data={order}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
    />
  );
};

// ============================================================================
// LIST VIEWS
// ============================================================================

const ProductsView: React.FC = () => {
  const navigate = useNavigate();
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterCategory, setFilterCategory] = useState<string>('');
  const { data: products = [], isLoading, refetch } = useProducts({
    status: filterStatus || undefined,
    category_id: filterCategory || undefined
  });
  const { data: categories = [] } = useCategories();

  const columns: TableColumn<Product>[] = [
    {
      id: 'sku',
      header: 'SKU',
      accessor: 'sku',
      render: (v, row) => (
        <button
          className="font-mono text-sm text-primary hover:underline"
          onClick={() => navigate(`/ecommerce/products/${row.id}`)}
        >
          {v as string}
        </button>
      )
    },
    { id: 'name', header: 'Produit', accessor: 'name' },
    { id: 'category_name', header: 'Categorie', accessor: 'category_name', render: (v) => (v as string) || '-' },
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
    { id: 'is_featured', header: 'Vedette', accessor: 'is_featured', render: (v) => (v as boolean) ? <Badge color="purple">Oui</Badge> : '-' },
    { id: 'actions', header: '', accessor: 'id', render: (_, row) => (
      <Button variant="ghost" size="sm" onClick={() => navigate(`/ecommerce/products/${row.id}`)}>Detail</Button>
    )}
  ];

  return (
    <Card title="Produits" actions={<Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createProduct' } })); }}>Nouveau produit</Button>}>
      <div className="azals-filter-bar mb-4">
        <Select
          value={filterCategory}
          onChange={(v) => setFilterCategory(v)}
          options={[{ value: '', label: 'Toutes categories' }, ...categories.map(c => ({ value: c.id, label: c.name }))]}
          placeholder="Categorie"
        />
        <Select
          value={filterStatus}
          onChange={(v) => setFilterStatus(v)}
          options={[{ value: '', label: 'Tous statuts' }, ...PRODUCT_STATUS]}
          placeholder="Statut"
        />
      </div>
      <DataTable columns={columns} data={products} keyField="id" filterable isLoading={isLoading} onRefresh={refetch} emptyMessage="Aucun produit" />
    </Card>
  );
};

const OrdersView: React.FC = () => {
  const navigate = useNavigate();
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterPayment, setFilterPayment] = useState<string>('');
  const { data: orders = [], isLoading, refetch } = useOrders({
    status: filterStatus || undefined,
    payment_status: filterPayment || undefined
  });

  const columns: TableColumn<Order>[] = [
    {
      id: 'number',
      header: 'N° Commande',
      accessor: 'number',
      render: (v, row) => (
        <button
          className="font-mono text-sm text-primary hover:underline"
          onClick={() => navigate(`/ecommerce/orders/${row.id}`)}
        >
          {v as string}
        </button>
      )
    },
    { id: 'customer_name', header: 'Client', accessor: 'customer_name' },
    { id: 'created_at', header: 'Date', accessor: 'created_at', render: (v) => formatDateTime(v as string) },
    { id: 'items', header: 'Articles', accessor: 'items', render: (v) => <Badge color="blue">{(v as OrderItem[])?.length || 0}</Badge> },
    { id: 'total', header: 'Total', accessor: 'total', align: 'right', render: (v, row) => formatCurrency(v as number, row.currency) },
    { id: 'payment_status', header: 'Paiement', accessor: 'payment_status', render: (v) => {
      const status = v as string;
      const config = PAYMENT_STATUS_CONFIG[status as keyof typeof PAYMENT_STATUS_CONFIG];
      return <Badge color={config?.color || 'gray'}>{config?.label || status}</Badge>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const status = v as string;
      const config = ORDER_STATUS_CONFIG[status as keyof typeof ORDER_STATUS_CONFIG];
      return <Badge color={config?.color || 'gray'}>{config?.label || status}</Badge>;
    }},
    { id: 'actions', header: '', accessor: 'id', render: (_, row) => (
      <Button variant="ghost" size="sm" onClick={() => navigate(`/ecommerce/orders/${row.id}`)}>Detail</Button>
    )}
  ];

  return (
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
      <DataTable columns={columns} data={orders} keyField="id" filterable isLoading={isLoading} onRefresh={refetch} emptyMessage="Aucune commande" />
    </Card>
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
    <Card title="Categories" actions={<Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createCategory' } })); }}>Nouvelle categorie</Button>}>
      <DataTable columns={columns} data={categories} keyField="id" filterable isLoading={isLoading} onRefresh={refetch} emptyMessage="Aucune categorie" />
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
      const config = SHIPPING_STATUS_CONFIG[status as keyof typeof SHIPPING_STATUS_CONFIG];
      return <Badge color={config?.color || 'gray'}>{config?.label || status}</Badge>;
    }},
    { id: 'estimated_delivery', header: 'Livraison prevue', accessor: 'estimated_delivery', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'shipped_at', header: 'Expedie le', accessor: 'shipped_at', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'delivered_at', header: 'Livre le', accessor: 'delivered_at', render: (v) => (v as string) ? formatDate(v as string) : '-' }
  ];

  return (
    <Card title="Expeditions">
      <div className="azals-filter-bar mb-4">
        <Select
          value={filterStatus}
          onChange={(v) => setFilterStatus(v)}
          options={[{ value: '', label: 'Tous statuts' }, ...SHIPPING_STATUS]}
          placeholder="Statut"
        />
      </div>
      <DataTable columns={columns} data={shippings} keyField="id" filterable isLoading={isLoading} onRefresh={refetch} emptyMessage="Aucune expedition" />
    </Card>
  );
};

// ============================================================================
// DASHBOARD
// ============================================================================

type DashboardView = 'dashboard' | 'products' | 'orders' | 'categories' | 'shippings';

const EcommerceDashboard: React.FC = () => {
  const [currentView, setCurrentView] = useState<DashboardView>('dashboard');
  const { data: stats } = useEcommerceStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'products', label: 'Produits' },
    { id: 'orders', label: 'Commandes' },
    { id: 'categories', label: 'Categories' },
    { id: 'shippings', label: 'Expeditions' }
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
    <PageWrapper title="E-commerce" subtitle="Vente en ligne - Produits, commandes et expeditions">
      <TabNav tabs={tabs} activeTab={currentView} onChange={(id) => setCurrentView(id as DashboardView)} />
      <div className="mt-4">{renderContent()}</div>
    </PageWrapper>
  );
};

// ============================================================================
// MODULE PRINCIPAL AVEC ROUTES
// ============================================================================

const EcommerceRoutes: React.FC = () => (
  <Routes>
    <Route index element={<EcommerceDashboard />} />
    <Route path="products/:id" element={<ProductDetailView />} />
    <Route path="orders/:id" element={<OrderDetailView />} />
  </Routes>
);

export default EcommerceRoutes;

// Re-export hooks for external use
export {
  ecommerceKeys,
  useEcommerceStats,
  useProducts,
  useProduct,
  useOrders,
  useOrder,
  useCategories,
  useShippings
} from './hooks';
