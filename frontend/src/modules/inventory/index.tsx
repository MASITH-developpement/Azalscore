// @ts-nocheck
/**
 * AZALSCORE Module - STOCK
 * Gestion des stocks, entrepôts et mouvements
 * Architecture BaseViewStandard pour la vue détail article
 */

import React, { useState } from 'react';
import {
  Box, AlertTriangle, DollarSign, BarChart3, Clock, ClipboardList,
  Package, Tag, MapPin, ArrowLeft, Edit, Eye, Printer,
  RefreshCw, Hash, Sparkles
} from 'lucide-react';
import { Button, Modal } from '@ui/actions';
import { StatCard } from '@ui/dashboards';
import { Select, Input } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import {
  BaseViewStandard,
  type TabDefinition,
  type InfoBarItem,
  type SidebarSection,
  type ActionDefinition,
  SemanticColor
} from '@ui/standards';
import { DataTable } from '@ui/tables';
import { BarcodeLookup } from '@/modules/enrichment';
import type { EnrichedProductFields } from '@/modules/enrichment';
import type { TableColumn } from '@/types';
import { formatCurrency, formatDate } from '@/utils/formatters';

// Module imports
import {
  useInventoryDashboard,
  useCategories,
  useWarehouses,
  useLocations,
  useProducts,
  useProduct,
  useMovements,
  usePickings,
  useInventoryCounts,
  useCreateProduct,
  useCreateMovement,
  useValidateMovement,
} from './hooks';
import {
  ProductInfoTab,
  ProductStockTab,
  ProductFinancialTab,
  ProductDocsTab,
  ProductHistoryTab,
  ProductIATab
} from './components';
import {
  formatQuantity,
  MOVEMENT_TYPE_CONFIG, MOVEMENT_STATUS_CONFIG,
  PICKING_TYPE_CONFIG, PICKING_STATUS_CONFIG,
  isLowStock, isOutOfStock, getStockLevel, getStockLevelLabel
} from './types';
import type {
  Category, Warehouse, Location, Product,
  Movement, InventoryCount, Picking,
  MovementType, MovementStatus
} from './types';

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
      <button key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}>
        {tab.label}
      </button>
    ))}
  </div>
);

// ============================================================================
// VUE DÉTAIL ARTICLE
// ============================================================================

interface ProductDetailViewProps {
  productId: string;
  onBack: () => void;
}

const ProductDetailView: React.FC<ProductDetailViewProps> = ({ productId, onBack }) => {
  const { data: product, isLoading, error, refetch } = useProduct(productId);

  if (isLoading) {
    return (
      <div className="azals-loading-container">
        <div className="azals-spinner" />
        <p>Chargement de l'article...</p>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="azals-error-container">
        <AlertTriangle size={48} className="text-danger" />
        <p>Erreur lors du chargement de l'article</p>
        <Button variant="secondary" onClick={onBack}>Retour à la liste</Button>
      </div>
    );
  }

  const tabs: TabDefinition<Product>[] = [
    { id: 'info', label: 'Informations', icon: <Package size={16} />, component: ProductInfoTab },
    { id: 'stock', label: 'Stock', icon: <MapPin size={16} />, badge: product.stock_by_location?.length || 0, component: ProductStockTab },
    { id: 'financial', label: 'Financier', icon: <DollarSign size={16} />, component: ProductFinancialTab },
    { id: 'docs', label: 'Documents', icon: <ClipboardList size={16} />, badge: product.documents?.length || 0, component: ProductDocsTab },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: ProductHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: ProductIATab }
  ];

  const stockLevel = getStockLevel(product);
  const stockColorMap: Record<string, SemanticColor> = { danger: 'red', warning: 'orange', success: 'green', info: 'blue' };

  const infoBarItems: InfoBarItem[] = [
    { id: 'code', label: 'Code', value: product.code, icon: <Hash size={14} /> },
    { id: 'category', label: 'Catégorie', value: product.category_name || '-', icon: <Tag size={14} /> },
    { id: 'stock', label: 'Stock', value: formatQuantity(product.current_stock, product.unit), icon: <Package size={14} />, valueColor: stockColorMap[stockLevel] },
    { id: 'status', label: 'Niveau', value: getStockLevelLabel(product), valueColor: stockColorMap[stockLevel] }
  ];

  const sidebarSections: SidebarSection[] = [
    {
      id: 'stock', title: 'Stock',
      items: [
        { id: 'current', label: 'Stock actuel', value: formatQuantity(product.current_stock, product.unit), highlight: isLowStock(product) || isOutOfStock(product) },
        { id: 'reserved', label: 'Réservé', value: formatQuantity(product.reserved_stock || 0, product.unit) },
        { id: 'available', label: 'Disponible', value: formatQuantity(product.available_stock ?? product.current_stock, product.unit), highlight: true }
      ]
    },
    {
      id: 'valorisation', title: 'Valorisation',
      items: [
        { id: 'cost', label: 'Prix achat', value: formatCurrency(product.cost_price), format: 'currency' },
        { id: 'sale', label: 'Prix vente', value: formatCurrency(product.sale_price), format: 'currency' },
        { id: 'value', label: 'Valeur stock', value: formatCurrency(product.current_stock * product.cost_price), format: 'currency', highlight: true }
      ]
    }
  ];

  const headerActions: ActionDefinition[] = [
    { id: 'back', label: 'Retour', icon: <ArrowLeft size={16} />, variant: 'ghost', onClick: onBack },
    { id: 'print', label: 'Imprimer', icon: <Printer size={16} />, variant: 'secondary', onClick: () => { window.print(); } }
  ];

  const primaryActions: ActionDefinition[] = [
    { id: 'edit', label: 'Modifier', icon: <Edit size={16} />, variant: 'secondary', onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'editProduct', productId: product.id } })); } },
    { id: 'movement', label: 'Nouveau mouvement', icon: <RefreshCw size={16} />, variant: 'primary', onClick: () => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createMovement', productId: product.id } })); } }
  ];

  return (
    <BaseViewStandard<Product>
      title={product.name} subtitle={`Article ${product.code}`}
      status={{ label: getStockLevelLabel(product), color: stockColorMap[stockLevel] }}
      data={product} view="detail" tabs={tabs} infoBarItems={infoBarItems}
      sidebarSections={sidebarSections} headerActions={headerActions} primaryActions={primaryActions}
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
    />
  );
};

// ============================================================================
// VUES LISTE
// ============================================================================

interface ProductsViewProps {
  onSelectProduct: (id: string) => void;
}

const ProductsView: React.FC<ProductsViewProps> = ({ onSelectProduct }) => {
  const { data: products = [], isLoading, error, refetch } = useProducts();
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

  const handleBarcodeEnrich = (fields: EnrichedProductFields) => {
    setFormData((prev) => ({
      ...prev, name: fields.name || prev.name,
      description: fields.description || prev.description,
      barcode: fields.barcode || prev.barcode,
    }));
  };

  const columns: TableColumn<Product>[] = [
    { id: 'code', header: 'Code', accessor: 'code',
      render: (v, row: Product) => <button className="text-primary hover:underline font-mono" onClick={() => onSelectProduct(row.id)}>{v as string}</button> },
    { id: 'name', header: 'Désignation', accessor: 'name' },
    { id: 'category_name', header: 'Catégorie', accessor: 'category_name', render: (v) => (v as string) || '-' },
    { id: 'unit', header: 'Unité', accessor: 'unit' },
    { id: 'current_stock', header: 'Stock', accessor: 'current_stock',
      render: (v, row: Product) => <span className={isOutOfStock(row) ? 'text-red-600 font-semibold' : isLowStock(row) ? 'text-orange-600 font-semibold' : ''}>{v as number} {row.unit}</span> },
    { id: 'cost_price', header: 'Prix achat', accessor: 'cost_price', render: (v) => formatCurrency(v as number) },
    { id: 'sale_price', header: 'Prix vente', accessor: 'sale_price', render: (v) => formatCurrency(v as number) },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge> },
    { id: 'actions', header: '', accessor: 'id', render: (_, row: Product) => <Button size="sm" variant="ghost" leftIcon={<Eye size={14} />} onClick={() => onSelectProduct(row.id)}>Voir</Button> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Articles</h3>
        <Button onClick={() => setShowModal(true)}>Nouvel article</Button>
      </div>
      <DataTable columns={columns} data={products} isLoading={isLoading} keyField="id" filterable error={error instanceof Error ? error : null} onRetry={() => refetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvel article" size="lg">
        <form onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field"><label>Code</label><Input value={formData.code || ''} onChange={(v) => setFormData({ ...formData, code: v })} /></div>
            <div className="azals-field"><label>Désignation</label><Input value={formData.name || ''} onChange={(v) => setFormData({ ...formData, name: v })} /></div>
          </Grid>
          <div className="azals-field"><label>Description</label><Input value={formData.description || ''} onChange={(v) => setFormData({ ...formData, description: v })} /></div>
          <div className="azals-field">
            <label>Code-barres (EAN/UPC) - Remplissage auto depuis Open Food Facts</label>
            <BarcodeLookup value={formData.barcode || ''} onEnrich={handleBarcodeEnrich} />
          </div>
          <Grid cols={2}>
            <div className="azals-field"><label>Catégorie</label><Select value={formData.category_id || ''} onChange={(v) => setFormData({ ...formData, category_id: v })} options={categories.map(c => ({ value: c.id, label: c.name }))} /></div>
            <div className="azals-field"><label>Unité</label><Input value={formData.unit || ''} onChange={(v) => setFormData({ ...formData, unit: v })} placeholder="pcs, kg, m..." /></div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field"><label>Prix d'achat</label><Input type="number" value={formData.cost_price !== undefined ? String(formData.cost_price) : ''} onChange={(v) => setFormData({ ...formData, cost_price: parseFloat(v) })} /></div>
            <div className="azals-field"><label>Prix de vente</label><Input type="number" value={formData.sale_price !== undefined ? String(formData.sale_price) : ''} onChange={(v) => setFormData({ ...formData, sale_price: parseFloat(v) })} /></div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field"><label>Stock minimum</label><Input type="number" value={formData.min_stock !== undefined ? String(formData.min_stock) : ''} onChange={(v) => setFormData({ ...formData, min_stock: parseInt(v) })} /></div>
            <div className="azals-field"><label>Stock maximum</label><Input type="number" value={formData.max_stock !== undefined ? String(formData.max_stock) : ''} onChange={(v) => setFormData({ ...formData, max_stock: parseInt(v) })} /></div>
          </Grid>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createProduct.isPending}>Créer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const WarehousesView: React.FC = () => {
  const { data: warehouses = [], isLoading, error, refetch } = useWarehouses();
  const { data: locations = [] } = useLocations();

  const columns: TableColumn<Warehouse>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'address', header: 'Adresse', accessor: 'address', render: (v) => (v as string) || '-' },
    { id: 'locations_count', header: 'Emplacements', accessor: 'id', render: (_, row: Warehouse) => <Badge color="blue">{locations.filter(l => l.warehouse_id === row.id).length}</Badge> },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Entrepôts</h3>
        <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createWarehouse' } })); }}>Nouvel entrepôt</Button>
      </div>
      <DataTable columns={columns} data={warehouses} isLoading={isLoading} keyField="id" filterable error={error instanceof Error ? error : null} onRetry={() => refetch()} />
    </Card>
  );
};

const MovementsView: React.FC = () => {
  const { data: movements = [], isLoading, error, refetch } = useMovements();
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
    { id: 'number', header: 'N°', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => { const config = MOVEMENT_TYPE_CONFIG[v as MovementType]; return <Badge color={config.color}>{config.label}</Badge>; } },
    { id: 'product_name', header: 'Article', accessor: 'product_name' },
    { id: 'quantity', header: 'Quantité', accessor: 'quantity' },
    { id: 'source_location_name', header: 'Source', accessor: 'source_location_name', render: (v) => (v as string) || '-' },
    { id: 'dest_location_name', header: 'Destination', accessor: 'dest_location_name', render: (v) => (v as string) || '-' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => { const config = MOVEMENT_STATUS_CONFIG[v as MovementStatus]; return <Badge color={config.color}>{config.label}</Badge>; } },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row: Movement) => row.status === 'DRAFT' ? <Button size="sm" onClick={() => validateMovement.mutate(row.id)}>Valider</Button> : null }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Mouvements de stock</h3>
        <Button onClick={() => setShowModal(true)}>Nouveau mouvement</Button>
      </div>
      <DataTable columns={columns} data={movements} isLoading={isLoading} keyField="id" filterable error={error instanceof Error ? error : null} onRetry={() => refetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouveau mouvement" size="lg">
        <form onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field"><label>Type</label>
              <Select value={formData.type || ''} onChange={(v) => setFormData({ ...formData, type: v as MovementType })}
                options={Object.entries(MOVEMENT_TYPE_CONFIG).map(([value, config]) => ({ value, label: config.label }))} /></div>
            <div className="azals-field"><label>Date</label>
              <input type="date" className="azals-input" value={formData.date || ''} onChange={(e) => setFormData({ ...formData, date: e.target.value })} required /></div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field"><label>Article</label>
              <Select value={formData.product_id || ''} onChange={(v) => setFormData({ ...formData, product_id: v })}
                options={products.map(p => ({ value: p.id, label: `${p.code} - ${p.name}` }))} /></div>
            <div className="azals-field"><label>Quantité</label>
              <Input type="number" value={formData.quantity !== undefined ? String(formData.quantity) : ''} onChange={(v) => setFormData({ ...formData, quantity: parseFloat(v) })} /></div>
          </Grid>
          {(formData.type === 'OUT' || formData.type === 'TRANSFER') && (
            <div className="azals-field"><label>Emplacement source</label>
              <Select value={formData.source_location_id || ''} onChange={(v) => setFormData({ ...formData, source_location_id: v })}
                options={locations.map(l => ({ value: l.id, label: `${l.warehouse_name} / ${l.name}` }))} /></div>
          )}
          {(formData.type === 'IN' || formData.type === 'TRANSFER') && (
            <div className="azals-field"><label>Emplacement destination</label>
              <Select value={formData.dest_location_id || ''} onChange={(v) => setFormData({ ...formData, dest_location_id: v })}
                options={locations.map(l => ({ value: l.id, label: `${l.warehouse_name} / ${l.name}` }))} /></div>
          )}
          <div className="azals-field"><label>Notes</label><Input value={formData.notes || ''} onChange={(v) => setFormData({ ...formData, notes: v })} /></div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createMovement.isPending}>Créer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const PickingsView: React.FC = () => {
  const { data: pickings = [], isLoading, error, refetch } = usePickings();

  const columns: TableColumn<Picking>[] = [
    { id: 'number', header: 'N°', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => { const config = PICKING_TYPE_CONFIG[v as keyof typeof PICKING_TYPE_CONFIG]; return <Badge color={config.color}>{config.label}</Badge>; } },
    { id: 'reference', header: 'Référence', accessor: 'reference', render: (v) => (v as string) || '-' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => { const config = PICKING_STATUS_CONFIG[v as keyof typeof PICKING_STATUS_CONFIG]; return <Badge color={config.color}>{config.label}</Badge>; } }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4"><h3 className="text-lg font-semibold">Préparations</h3></div>
      <DataTable columns={columns} data={pickings} isLoading={isLoading} keyField="id" filterable error={error instanceof Error ? error : null} onRetry={() => refetch()} />
    </Card>
  );
};

const InventoryCountsView: React.FC = () => {
  const { data: counts = [], isLoading, error, refetch } = useInventoryCounts();

  const statuses: Record<string, { label: string; color: string }> = {
    DRAFT: { label: 'Brouillon', color: 'gray' },
    IN_PROGRESS: { label: 'En cours', color: 'orange' },
    VALIDATED: { label: 'Validé', color: 'green' },
    CANCELLED: { label: 'Annulé', color: 'red' }
  };

  const columns: TableColumn<InventoryCount>[] = [
    { id: 'number', header: 'N°', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'warehouse_name', header: 'Entrepôt', accessor: 'warehouse_name' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v): React.ReactNode => { const config = statuses[v as string] || { label: String(v), color: 'gray' }; return <Badge color={config.color}>{config.label}</Badge>; } }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Inventaires</h3>
        <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createInventoryCount' } })); }}>Nouvel inventaire</Button>
      </div>
      <DataTable columns={columns} data={counts} isLoading={isLoading} keyField="id" filterable error={error instanceof Error ? error : null} onRetry={() => refetch()} />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'products' | 'warehouses' | 'movements' | 'pickings' | 'counts' | 'product-detail';

const StockModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const { data: dashboard } = useInventoryDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'products', label: 'Articles' },
    { id: 'warehouses', label: 'Entrepôts' },
    { id: 'movements', label: 'Mouvements' },
    { id: 'pickings', label: 'Préparations' },
    { id: 'counts', label: 'Inventaires' }
  ];

  const handleSelectProduct = (id: string) => { setSelectedProductId(id); setCurrentView('product-detail'); };
  const handleBackFromProduct = () => { setSelectedProductId(null); setCurrentView('products'); };

  if (currentView === 'product-detail' && selectedProductId) {
    return <ProductDetailView productId={selectedProductId} onBack={handleBackFromProduct} />;
  }

  const renderContent = () => {
    switch (currentView) {
      case 'products': return <ProductsView onSelectProduct={handleSelectProduct} />;
      case 'warehouses': return <WarehousesView />;
      case 'movements': return <MovementsView />;
      case 'pickings': return <PickingsView />;
      case 'counts': return <InventoryCountsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard title="Articles" value={String(dashboard?.total_products || 0)} icon={<Box size={24} />} variant="default" onClick={() => setCurrentView('products')} />
              <StatCard title="Ruptures de stock" value={String(dashboard?.low_stock_products || 0)} icon={<AlertTriangle size={24} />} variant="danger" onClick={() => setCurrentView('products')} />
              <StatCard title="Valeur du stock" value={formatCurrency(dashboard?.total_value || 0)} icon={<DollarSign size={24} />} variant="success" />
              <StatCard title="Mouvements du jour" value={String(dashboard?.movements_today || 0)} icon={<BarChart3 size={24} />} variant="default" onClick={() => setCurrentView('movements')} />
            </Grid>
            <Grid cols={2}>
              <StatCard title="Mouvements en attente" value={String(dashboard?.pending_movements || 0)} icon={<Clock size={24} />} variant="warning" onClick={() => setCurrentView('movements')} />
              <StatCard title="Préparations en attente" value={String(dashboard?.pending_pickings || 0)} icon={<ClipboardList size={24} />} variant="default" onClick={() => setCurrentView('pickings')} />
            </Grid>
            {dashboard?.stock_alerts && dashboard.stock_alerts.length > 0 && (
              <Card>
                <h3 className="text-lg font-semibold mb-4 text-red-600"><AlertTriangle size={20} className="inline mr-2" />Alertes de stock</h3>
                <div className="space-y-2">
                  {dashboard.stock_alerts.map((alert, i) => (
                    <div key={i} className="flex justify-between items-center p-2 bg-red-50 rounded border border-red-200">
                      <span>{alert.product_name}</span>
                      <span className="text-red-600 font-semibold">{alert.current_stock} / min: {alert.min_stock}</span>
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
    <PageWrapper title="Stock" subtitle="Gestion des stocks et entrepôts">
      <TabNav tabs={tabs} activeTab={currentView} onChange={(id) => setCurrentView(id as View)} />
      <div className="mt-4">{renderContent()}</div>
    </PageWrapper>
  );
};

export default StockModule;

// Re-exports
export * from './hooks';
export * from './types';
