/**
 * AZALSCORE Module - Production
 * Gestion de la production et fabrication
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings, ClipboardList, CheckCircle, BarChart3, Factory, Clock,
  Package, Layers, FileText, History, Sparkles, ArrowLeft,
  Play, Edit, X, Eye
} from 'lucide-react';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import { Button, Modal } from '@ui/actions';
import { StatCard } from '@ui/dashboards';
import { Select, Input } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { BaseViewStandard } from '@ui/standards';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate, formatCurrency, formatDuration, formatPercent } from '@/utils/formatters';
import {
  OrderInfoTab, OrderOperationsTab, OrderMaterialsTab,
  OrderDocsTab, OrderHistoryTab, OrderIATab
} from './components';
import {
  formatQuantity,
  ORDER_STATUS_CONFIG,
  ORDER_PRIORITY_CONFIG,
  getCompletionRate, isDraft, canConfirm, canStart, canComplete
} from './types';
import type {
  WorkCenter, BillOfMaterials, BOMLine, BOMOperation,
  ProductionOrder, WorkOrder, ProductionDashboard
} from './types';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition, SemanticColor } from '@ui/standards';

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
// CONSTANTES
// ============================================================================

const WORK_CENTER_TYPES = [
  { value: 'MACHINE', label: 'Machine' },
  { value: 'WORKSTATION', label: 'Poste de travail' },
  { value: 'LINE', label: 'Ligne' },
  { value: 'AREA', label: 'Zone' }
];

const BOM_STATUSES = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'ACTIVE', label: 'Actif', color: 'green' },
  { value: 'OBSOLETE', label: 'Obsolete', color: 'red' }
];

const ORDER_STATUSES = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'CONFIRMED', label: 'Confirme', color: 'blue' },
  { value: 'IN_PROGRESS', label: 'En cours', color: 'orange' },
  { value: 'DONE', label: 'Termine', color: 'green' },
  { value: 'CANCELLED', label: 'Annule', color: 'red' }
];

const PRIORITIES = [
  { value: 'LOW', label: 'Basse', color: 'gray' },
  { value: 'NORMAL', label: 'Normale', color: 'blue' },
  { value: 'HIGH', label: 'Haute', color: 'orange' },
  { value: 'URGENT', label: 'Urgente', color: 'red' }
];

const WORK_ORDER_STATUSES = [
  { value: 'PENDING', label: 'En attente', color: 'gray' },
  { value: 'READY', label: 'Pret', color: 'blue' },
  { value: 'IN_PROGRESS', label: 'En cours', color: 'orange' },
  { value: 'DONE', label: 'Termine', color: 'green' },
  { value: 'CANCELLED', label: 'Annule', color: 'red' }
];

// ============================================================================
// HELPERS
// ============================================================================

const getStatusInfo = (statuses: { value: string; label: string; color: string }[], status: string) => {
  return statuses.find(s => s.value === status) || { label: status, color: 'gray' };
};

const navigateTo = (view: string, params?: Record<string, unknown>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

// ============================================================================
// API HOOKS
// ============================================================================

const useProductionDashboard = () => {
  return useQuery({
    queryKey: ['production', 'dashboard'],
    queryFn: async () => {
      return api.get<ProductionDashboard>('/production/dashboard').then(r => r.data);
    }
  });
};

const useWorkCenters = () => {
  return useQuery({
    queryKey: ['production', 'work-centers'],
    queryFn: async () => {
      const response = await api.get<WorkCenter[] | { items: WorkCenter[] }>('/production/work-centers').then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

const useBOMs = () => {
  return useQuery({
    queryKey: ['production', 'boms'],
    queryFn: async () => {
      const response = await api.get<BillOfMaterials[] | { items: BillOfMaterials[] }>('/production/boms').then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

const useProductionOrders = (filters?: { status?: string; priority?: string }) => {
  return useQuery({
    queryKey: ['production', 'orders', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.priority) params.append('priority', filters.priority);
      const queryString = params.toString();
      const url = queryString ? `/production/orders?${queryString}` : '/production/orders';
      const response = await api.get<ProductionOrder[] | { items: ProductionOrder[] }>(url).then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

const useProductionOrder = (id: string) => {
  return useQuery({
    queryKey: ['production', 'order', id],
    queryFn: async () => {
      return api.get<ProductionOrder>(`/production/orders/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

const useWorkOrders = (productionOrderId?: string) => {
  return useQuery({
    queryKey: ['production', 'work-orders', productionOrderId],
    queryFn: async () => {
      const url = productionOrderId
        ? `/production/work-orders?production_order_id=${encodeURIComponent(productionOrderId)}`
        : '/production/work-orders';
      const response = await api.get<WorkOrder[] | { items: WorkOrder[] }>(url).then(r => r.data);
      return Array.isArray(response) ? response : (response?.items || []);
    }
  });
};

const useCreateWorkCenter = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<WorkCenter>) => {
      return api.post('/production/work-centers', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['production', 'work-centers'] })
  });
};

const useCreateProductionOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<ProductionOrder>) => {
      return api.post('/production/orders', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['production'] })
  });
};

const useConfirmOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/production/orders/${id}/confirm`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['production'] })
  });
};

const useStartOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/production/orders/${id}/start`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['production'] })
  });
};

const useCompleteOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/production/orders/${id}/complete`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['production'] })
  });
};

const useCancelOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/production/orders/${id}/cancel`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['production'] })
  });
};

// ============================================================================
// VUE DETAIL - PRODUCTION ORDER
// ============================================================================

interface ProductionOrderDetailViewProps {
  orderId: string;
  onBack: () => void;
  onEdit?: () => void;
}

const ProductionOrderDetailView: React.FC<ProductionOrderDetailViewProps> = ({ orderId, onBack, onEdit }) => {
  const { data: order, isLoading, error, refetch } = useProductionOrder(orderId);
  const confirmOrder = useConfirmOrder();
  const startOrder = useStartOrder();
  const completeOrder = useCompleteOrder();
  const cancelOrder = useCancelOrder();

  if (isLoading) {
    return (
      <div className="azals-loading">
        <div className="azals-loading__spinner" />
        <p>Chargement de l'ordre de fabrication...</p>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="azals-error">
        <p>Erreur lors du chargement de l'ordre.</p>
        <Button onClick={onBack} leftIcon={<ArrowLeft size={16} />}>Retour</Button>
      </div>
    );
  }

  // Configuration des onglets
  const tabs: TabDefinition<ProductionOrder>[] = [
    { id: 'info', label: 'Informations', icon: <Factory size={16} />, component: OrderInfoTab },
    { id: 'operations', label: 'Operations', icon: <Settings size={16} />, badge: order.work_orders?.length, component: OrderOperationsTab },
    { id: 'materials', label: 'Materiaux', icon: <Layers size={16} />, badge: order.material_consumptions?.length, component: OrderMaterialsTab },
    { id: 'docs', label: 'Documents', icon: <FileText size={16} />, component: OrderDocsTab },
    { id: 'history', label: 'Historique', icon: <History size={16} />, component: OrderHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: OrderIATab }
  ];

  // Configuration InfoBar
  const statusConfig = ORDER_STATUS_CONFIG[order.status];
  const priorityConfig = ORDER_PRIORITY_CONFIG[order.priority];
  const completionRate = getCompletionRate(order);

  const infoBarItems: InfoBarItem[] = [
    {
      id: 'product',
      label: 'Produit',
      value: order.product_name || order.product_code || '-',
      icon: <Package size={16} />
    },
    {
      id: 'quantity',
      label: 'Quantite',
      value: `${order.quantity_produced} / ${order.quantity_planned}`,
      icon: <BarChart3 size={16} />
    },
    {
      id: 'progress',
      label: 'Avancement',
      value: formatPercent(completionRate),
      valueColor: completionRate >= 1 ? 'green' : completionRate >= 0.5 ? 'orange' : 'gray'
    },
    {
      id: 'priority',
      label: 'Priorite',
      value: priorityConfig.label,
      valueColor: priorityConfig.color as SemanticColor
    }
  ];

  // Configuration Sidebar
  const sidebarSections: SidebarSection[] = [
    {
      id: 'summary',
      title: 'Resume',
      items: [
        { id: 'status', label: 'Statut', value: statusConfig.label },
        { id: 'planned', label: 'Qte planifiee', value: formatQuantity(order.quantity_planned, order.unit) },
        { id: 'produced', label: 'Qte produite', value: formatQuantity(order.quantity_produced, order.unit), highlight: completionRate >= 1 },
        { id: 'progress', label: 'Avancement', value: formatPercent(completionRate) }
      ]
    },
    {
      id: 'dates',
      title: 'Dates',
      items: [
        { id: 'start', label: 'Date debut', value: formatDate(order.start_date) },
        { id: 'due', label: 'Echeance', value: order.due_date ? formatDate(order.due_date) : '-' },
        ...(order.actual_end ? [{ id: 'end', label: 'Fin reelle', value: formatDate(order.actual_end) }] : [])
      ]
    },
    {
      id: 'costs',
      title: 'Couts',
      items: [
        { id: 'planned-cost', label: 'Cout prevu', value: order.cost_planned ? formatCurrency(order.cost_planned) : '-' },
        { id: 'actual-cost', label: 'Cout reel', value: order.cost_actual ? formatCurrency(order.cost_actual) : '-', format: 'currency' }
      ]
    }
  ];

  // Actions header
  const headerActions: ActionDefinition[] = [
    { id: 'back', label: 'Retour', icon: <ArrowLeft size={16} />, variant: 'ghost', onClick: onBack },
    ...(onEdit ? [{ id: 'edit', label: 'Modifier', icon: <Edit size={16} />, variant: 'secondary' as const, onClick: onEdit }] : [])
  ];

  // Actions primaires
  const primaryActions: ActionDefinition[] = [];

  if (canConfirm(order)) {
    primaryActions.push({
      id: 'confirm',
      label: 'Confirmer',
      icon: <CheckCircle size={16} />,
      variant: 'primary',
      onClick: () => confirmOrder.mutate(order.id)
    });
  }

  if (canStart(order)) {
    primaryActions.push({
      id: 'start',
      label: 'Demarrer',
      icon: <Play size={16} />,
      variant: 'primary',
      onClick: () => startOrder.mutate(order.id)
    });
  }

  if (canComplete(order)) {
    primaryActions.push({
      id: 'complete',
      label: 'Terminer',
      icon: <CheckCircle size={16} />,
      variant: 'primary',
      onClick: () => completeOrder.mutate(order.id)
    });
  }

  if (isDraft(order)) {
    primaryActions.push({
      id: 'cancel',
      label: 'Annuler',
      icon: <X size={16} />,
      variant: 'danger',
      onClick: () => cancelOrder.mutate(order.id)
    });
  }

  // Mapping couleurs
  const statusColorMap: Record<string, SemanticColor> = {
    gray: 'gray',
    blue: 'blue',
    orange: 'orange',
    green: 'green',
    red: 'red'
  };

  return (
    <BaseViewStandard<ProductionOrder>
      title={`OF ${order.number}`}
      subtitle={order.product_name || order.product_code}
      status={{
        label: statusConfig.label,
        color: statusColorMap[statusConfig.color] || 'gray'
      }}
      data={order}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      primaryActions={primaryActions}
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
    />
  );
};

// ============================================================================
// VUES LISTE
// ============================================================================

const WorkCentersView: React.FC = () => {
  const { data: workCenters = [], isLoading, error, refetch } = useWorkCenters();
  const createWorkCenter = useCreateWorkCenter();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<WorkCenter>>({});
  const [filterType, setFilterType] = useState<string>('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createWorkCenter.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const filteredData = filterType
    ? workCenters.filter(wc => wc.type === filterType)
    : workCenters;

  const columns: TableColumn<WorkCenter>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = WORK_CENTER_TYPES.find(t => t.value === v);
      return info?.label || (v as string);
    }},
    { id: 'capacity', header: 'Capacite', accessor: 'capacity', render: (v) => `${v as number} unites/h` },
    { id: 'efficiency', header: 'Efficacite', accessor: 'efficiency', render: (v) => `${((v as number) * 100).toFixed(0)}%` },
    { id: 'cost_per_hour', header: 'Cout/h', accessor: 'cost_per_hour', render: (v) => formatCurrency(v as number) },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Postes de travail</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous les types' }, ...WORK_CENTER_TYPES]}
            className="w-48"
          />
          <Button onClick={() => setShowModal(true)}>Nouveau poste</Button>
        </div>
      </div>
      <DataTable columns={columns} data={filteredData} isLoading={isLoading} keyField="id" filterable error={error && typeof error === 'object' && 'message' in error ? error as Error : null} onRetry={() => refetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouveau poste de travail">
        <form onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field">
              <label className="azals-field__label">Code</label>
              <Input
                value={formData.code || ''}
                onChange={(v) => setFormData({ ...formData, code: v })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Nom</label>
              <Input
                value={formData.name || ''}
                onChange={(v) => setFormData({ ...formData, name: v })}
              />
            </div>
          </Grid>
          <div className="azals-field">
            <label className="azals-field__label">Type</label>
            <Select
              value={formData.type || ''}
              onChange={(v) => setFormData({ ...formData, type: v as WorkCenter['type'] })}
              options={WORK_CENTER_TYPES}
            />
          </div>
          <Grid cols={3}>
            <div className="azals-field">
              <label className="azals-field__label">Capacite (unites/h)</label>
              <Input
                type="number"
                value={formData.capacity || ''}
                onChange={(v) => setFormData({ ...formData, capacity: parseFloat(v) })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Efficacite (%)</label>
              <Input
                type="number"
                value={formData.efficiency || ''}
                onChange={(v) => setFormData({ ...formData, efficiency: parseFloat(v) })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Cout horaire</label>
              <Input
                type="number"
                value={formData.cost_per_hour || ''}
                onChange={(v) => setFormData({ ...formData, cost_per_hour: parseFloat(v) })}
              />
            </div>
          </Grid>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createWorkCenter.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const BOMsView: React.FC = () => {
  const { data: boms = [], isLoading, error, refetch } = useBOMs();
  const [filterStatus, setFilterStatus] = useState<string>('');

  const filteredData = filterStatus
    ? boms.filter(b => b.status === filterStatus)
    : boms;

  const columns: TableColumn<BillOfMaterials>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'product_name', header: 'Produit fini', accessor: 'product_name', render: (v, row) => (
      <button
        className="text-blue-600 hover:underline"
        onClick={() => navigateTo('stock', { view: 'products', id: row.product_id })}
      >
        {v as string}
      </button>
    )},
    { id: 'version', header: 'Version', accessor: 'version' },
    { id: 'lines', header: 'Composants', accessor: 'lines', render: (v) => <Badge color="blue">{(v as BOMLine[])?.length || 0}</Badge> },
    { id: 'operations', header: 'Operations', accessor: 'operations', render: (v) => <Badge color="purple">{(v as BOMOperation[])?.length || 0}</Badge> },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(BOM_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Nomenclatures</h3>
        <div className="flex gap-2">
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous les statuts' }, ...BOM_STATUSES]}
            className="w-48"
          />
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createBOM' } })); }}>Nouvelle nomenclature</Button>
        </div>
      </div>
      <DataTable columns={columns} data={filteredData} isLoading={isLoading} keyField="id" filterable error={error && typeof error === 'object' && 'message' in error ? error as Error : null} onRetry={() => refetch()} />
    </Card>
  );
};

interface ProductionOrdersViewProps {
  onSelectOrder: (id: string) => void;
}

const ProductionOrdersView: React.FC<ProductionOrdersViewProps> = ({ onSelectOrder }) => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterPriority, setFilterPriority] = useState<string>('');
  const { data: orders = [], isLoading, error, refetch } = useProductionOrders({
    status: filterStatus || undefined,
    priority: filterPriority || undefined
  });
  const { data: boms = [] } = useBOMs();
  const createOrder = useCreateProductionOrder();
  const confirmOrder = useConfirmOrder();
  const startOrder = useStartOrder();
  const completeOrder = useCompleteOrder();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<ProductionOrder>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createOrder.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<ProductionOrder>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v, row) => (
      <button
        className="font-mono text-blue-600 hover:underline"
        onClick={() => onSelectOrder(row.id)}
      >
        {v as string}
      </button>
    )},
    { id: 'product_name', header: 'Produit', accessor: 'product_name' },
    { id: 'quantity_planned', header: 'Qte planifiee', accessor: 'quantity_planned' },
    { id: 'quantity_produced', header: 'Qte produite', accessor: 'quantity_produced', render: (v, row) => (
      <span className={(v as number) < row.quantity_planned ? 'text-orange-600' : 'text-green-600'}>
        {v as number} / {row.quantity_planned}
      </span>
    )},
    { id: 'start_date', header: 'Date debut', accessor: 'start_date', render: (v) => formatDate(v as string) },
    { id: 'priority', header: 'Priorite', accessor: 'priority', render: (v) => {
      const info = getStatusInfo(PRIORITIES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(ORDER_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        <Button size="sm" variant="ghost" onClick={() => onSelectOrder(row.id)}>
          <Eye size={14} />
        </Button>
        {row.status === 'DRAFT' && (
          <Button size="sm" onClick={() => confirmOrder.mutate(row.id)}>Confirmer</Button>
        )}
        {row.status === 'CONFIRMED' && (
          <Button size="sm" onClick={() => startOrder.mutate(row.id)}>Demarrer</Button>
        )}
        {row.status === 'IN_PROGRESS' && (
          <Button size="sm" onClick={() => completeOrder.mutate(row.id)}>Terminer</Button>
        )}
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Ordres de fabrication</h3>
        <div className="flex gap-2">
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous les statuts' }, ...ORDER_STATUSES]}
            className="w-40"
          />
          <Select
            value={filterPriority}
            onChange={(v) => setFilterPriority(v)}
            options={[{ value: '', label: 'Toutes priorites' }, ...PRIORITIES]}
            className="w-40"
          />
          <Button onClick={() => setShowModal(true)}>Nouvel OF</Button>
        </div>
      </div>
      <DataTable columns={columns} data={orders} isLoading={isLoading} keyField="id" filterable error={error && typeof error === 'object' && 'message' in error ? error as Error : null} onRetry={() => refetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvel ordre de fabrication">
        <form onSubmit={handleSubmit}>
          <div className="azals-field">
            <label className="azals-field__label">Nomenclature</label>
            <Select
              value={formData.bom_id || ''}
              onChange={(v) => setFormData({ ...formData, bom_id: v })}
              options={boms.filter(b => b.status === 'ACTIVE').map(b => ({
                value: b.id,
                label: `${b.code} - ${b.product_name}`
              }))}
            />
          </div>
          <Grid cols={2}>
            <div className="azals-field">
              <label className="azals-field__label">Quantite a produire</label>
              <Input
                type="number"
                value={formData.quantity_planned || ''}
                onChange={(v) => setFormData({ ...formData, quantity_planned: parseInt(v) })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Date de debut</label>
              <input
                type="date"
                className="azals-input"
                value={formData.start_date || ''}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
              />
            </div>
          </Grid>
          <div className="azals-field">
            <label className="azals-field__label">Priorite</label>
            <Select
              value={formData.priority || 'NORMAL'}
              onChange={(v) => setFormData({ ...formData, priority: v as ProductionOrder['priority'] })}
              options={PRIORITIES}
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createOrder.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const WorkOrdersView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: workOrders = [], isLoading, error, refetch } = useWorkOrders();

  const filteredData = filterStatus
    ? workOrders.filter(wo => wo.status === filterStatus)
    : workOrders;

  const columns: TableColumn<WorkOrder>[] = [
    { id: 'work_center_name', header: 'Poste de travail', accessor: 'work_center_name' },
    { id: 'name', header: 'Operation', accessor: 'name' },
    { id: 'sequence', header: 'Sequence', accessor: 'sequence' },
    { id: 'duration_planned', header: 'Duree prevue', accessor: 'duration_planned', render: (v) => formatDuration(v as number) },
    { id: 'duration_actual', header: 'Duree reelle', accessor: 'duration_actual', render: (v) => (v as number) ? formatDuration(v as number) : '-' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(WORK_ORDER_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Ordres de travail</h3>
        <Select
          value={filterStatus}
          onChange={(v) => setFilterStatus(v)}
          options={[{ value: '', label: 'Tous les statuts' }, ...WORK_ORDER_STATUSES]}
          className="w-48"
        />
      </div>
      <DataTable columns={columns} data={filteredData} isLoading={isLoading} keyField="id" filterable error={error && typeof error === 'object' && 'message' in error ? error as Error : null} onRetry={() => refetch()} />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'work-centers' | 'boms' | 'orders' | 'work-orders' | 'order-detail';

const ProductionModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const { data: dashboard } = useProductionDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'work-centers', label: 'Postes de travail' },
    { id: 'boms', label: 'Nomenclatures' },
    { id: 'orders', label: 'Ordres de fab.' },
    { id: 'work-orders', label: 'Ordres de travail' }
  ];

  const handleSelectOrder = (id: string) => {
    setSelectedOrderId(id);
    setCurrentView('order-detail');
  };

  const handleBackFromDetail = () => {
    setSelectedOrderId(null);
    setCurrentView('orders');
  };

  // Vue detail d'un ordre
  if (currentView === 'order-detail' && selectedOrderId) {
    return (
      <ProductionOrderDetailView
        orderId={selectedOrderId}
        onBack={handleBackFromDetail}
      />
    );
  }

  const renderContent = () => {
    switch (currentView) {
      case 'work-centers':
        return <WorkCentersView />;
      case 'boms':
        return <BOMsView />;
      case 'orders':
        return <ProductionOrdersView onSelectOrder={handleSelectOrder} />;
      case 'work-orders':
        return <WorkOrdersView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="OF en cours"
                value={String(dashboard?.orders_in_progress || 0)}
                icon={<Settings className="w-5 h-5" />}
                variant="warning"
                onClick={() => setCurrentView('orders')}
              />
              <StatCard
                title="OF planifies"
                value={String(dashboard?.orders_planned || 0)}
                icon={<ClipboardList className="w-5 h-5" />}
                variant="default"
                onClick={() => setCurrentView('orders')}
              />
              <StatCard
                title="Termines aujourd'hui"
                value={String(dashboard?.orders_completed_today || 0)}
                icon={<CheckCircle className="w-5 h-5" />}
                variant="success"
              />
              <StatCard
                title="Taux d'efficacite"
                value={`${((dashboard?.efficiency_rate || 0) * 100).toFixed(0)}%`}
                icon={<BarChart3 className="w-5 h-5" />}
                variant="default"
              />
            </Grid>
            <Grid cols={2}>
              <StatCard
                title="Postes actifs"
                value={`${dashboard?.work_centers_active || 0} / ${dashboard?.work_centers_total || 0}`}
                icon={<Factory className="w-5 h-5" />}
                variant="default"
                onClick={() => setCurrentView('work-centers')}
              />
              <StatCard
                title="OT en attente"
                value={String(dashboard?.pending_work_orders || 0)}
                icon={<Clock className="w-5 h-5" />}
                variant="warning"
                onClick={() => setCurrentView('work-orders')}
              />
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper
      title="Production"
      subtitle="Gestion de la production et fabrication"
    >
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

export default ProductionModule;
