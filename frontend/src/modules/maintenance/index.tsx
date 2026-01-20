import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import type { TableColumn } from '@/types';
import { Check, Wrench, X, Cog, AlertTriangle, Calendar, BarChart3, Clock } from 'lucide-react';

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

interface Asset {
  id: string;
  code: string;
  name: string;
  type: 'EQUIPMENT' | 'VEHICLE' | 'TOOL' | 'BUILDING' | 'IT';
  category_id?: string;
  category_name?: string;
  location?: string;
  serial_number?: string;
  manufacturer?: string;
  model?: string;
  purchase_date?: string;
  warranty_end_date?: string;
  status: 'OPERATIONAL' | 'UNDER_MAINTENANCE' | 'OUT_OF_SERVICE' | 'SCRAPPED';
  criticality: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  last_maintenance_date?: string;
  next_maintenance_date?: string;
  created_at: string;
}

interface MaintenanceOrder {
  id: string;
  number: string;
  asset_id: string;
  asset_name?: string;
  asset_code?: string;
  type: 'PREVENTIVE' | 'CORRECTIVE' | 'PREDICTIVE' | 'CONDITION_BASED';
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  status: 'DRAFT' | 'PLANNED' | 'IN_PROGRESS' | 'ON_HOLD' | 'COMPLETED' | 'CANCELLED';
  description: string;
  planned_start_date?: string;
  planned_end_date?: string;
  actual_start_date?: string;
  actual_end_date?: string;
  assigned_to_id?: string;
  assigned_to_name?: string;
  parts_used: PartUsage[];
  labor_hours: number;
  total_cost: number;
  failure_cause?: string;
  resolution?: string;
  created_at: string;
}

interface PartUsage {
  id: string;
  product_id: string;
  product_name?: string;
  quantity: number;
  unit_cost: number;
}

interface MaintenancePlan {
  id: string;
  code: string;
  name: string;
  asset_id?: string;
  asset_name?: string;
  asset_type?: string;
  frequency: 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'QUARTERLY' | 'YEARLY' | 'HOURS_BASED' | 'CYCLES_BASED';
  frequency_value: number;
  tasks: MaintenanceTask[];
  last_execution_date?: string;
  next_execution_date?: string;
  is_active: boolean;
}

interface MaintenanceTask {
  id: string;
  sequence: number;
  description: string;
  duration_minutes: number;
  parts_required: { product_id: string; product_name?: string; quantity: number }[];
}

interface MaintenanceDashboard {
  assets_operational: number;
  assets_under_maintenance: number;
  assets_out_of_service: number;
  orders_in_progress: number;
  orders_overdue: number;
  upcoming_preventive: number;
  mtbf: number;
  mttr: number;
}

// ============================================================================
// CONSTANTES
// ============================================================================

const ASSET_TYPES = [
  { value: 'EQUIPMENT', label: 'Equipement' },
  { value: 'VEHICLE', label: 'Vehicule' },
  { value: 'TOOL', label: 'Outil' },
  { value: 'BUILDING', label: 'Batiment' },
  { value: 'IT', label: 'IT' }
];

const ASSET_STATUSES = [
  { value: 'OPERATIONAL', label: 'Operationnel', color: 'green' },
  { value: 'UNDER_MAINTENANCE', label: 'En maintenance', color: 'orange' },
  { value: 'OUT_OF_SERVICE', label: 'Hors service', color: 'red' },
  { value: 'SCRAPPED', label: 'Mis au rebut', color: 'gray' }
];

const CRITICALITIES = [
  { value: 'LOW', label: 'Faible', color: 'gray' },
  { value: 'MEDIUM', label: 'Moyenne', color: 'blue' },
  { value: 'HIGH', label: 'Haute', color: 'orange' },
  { value: 'CRITICAL', label: 'Critique', color: 'red' }
];

const ORDER_TYPES = [
  { value: 'PREVENTIVE', label: 'Preventive' },
  { value: 'CORRECTIVE', label: 'Corrective' },
  { value: 'PREDICTIVE', label: 'Predictive' },
  { value: 'CONDITION_BASED', label: 'Conditionnelle' }
];

const ORDER_PRIORITIES = [
  { value: 'LOW', label: 'Basse', color: 'gray' },
  { value: 'NORMAL', label: 'Normale', color: 'blue' },
  { value: 'HIGH', label: 'Haute', color: 'orange' },
  { value: 'URGENT', label: 'Urgente', color: 'red' }
];

const ORDER_STATUSES = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'PLANNED', label: 'Planifie', color: 'blue' },
  { value: 'IN_PROGRESS', label: 'En cours', color: 'orange' },
  { value: 'ON_HOLD', label: 'En attente', color: 'yellow' },
  { value: 'COMPLETED', label: 'Termine', color: 'green' },
  { value: 'CANCELLED', label: 'Annule', color: 'red' }
];

const FREQUENCIES = [
  { value: 'DAILY', label: 'Quotidienne' },
  { value: 'WEEKLY', label: 'Hebdomadaire' },
  { value: 'MONTHLY', label: 'Mensuelle' },
  { value: 'QUARTERLY', label: 'Trimestrielle' },
  { value: 'YEARLY', label: 'Annuelle' },
  { value: 'HOURS_BASED', label: 'Par heures' },
  { value: 'CYCLES_BASED', label: 'Par cycles' }
];

// ============================================================================
// HELPERS
// ============================================================================

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
};

const getStatusInfo = (statuses: any[], status: string) => {
  return statuses.find(s => s.value === status) || { label: status, color: 'gray' };
};

const navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

// ============================================================================
// API HOOKS
// ============================================================================

const useMaintenanceDashboard = () => {
  return useQuery({
    queryKey: ['maintenance', 'dashboard'],
    queryFn: async () => {
      return api.get<MaintenanceDashboard>('/v1/maintenance/dashboard').then(r => r.data);
    }
  });
};

const useAssets = (filters?: { type?: string; status?: string; criticality?: string }) => {
  return useQuery({
    queryKey: ['maintenance', 'assets', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.criticality) params.append('criticality', filters.criticality);
      const queryString = params.toString();
      const url = `/v1/maintenance/assets${queryString ? `?${queryString}` : ''}`;
      return api.get<Asset[]>(url).then(r => r.data);
    }
  });
};

const useMaintenanceOrders = (filters?: { type?: string; status?: string; priority?: string }) => {
  return useQuery({
    queryKey: ['maintenance', 'orders', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.priority) params.append('priority', filters.priority);
      const queryString = params.toString();
      const url = `/v1/maintenance/orders${queryString ? `?${queryString}` : ''}`;
      return api.get<MaintenanceOrder[]>(url).then(r => r.data);
    }
  });
};

const useMaintenancePlans = () => {
  return useQuery({
    queryKey: ['maintenance', 'plans'],
    queryFn: async () => {
      return api.get<MaintenancePlan[]>('/v1/maintenance/plans').then(r => r.data);
    }
  });
};

const useCreateAsset = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Asset>) => {
      return api.post('/v1/maintenance/assets', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['maintenance', 'assets'] })
  });
};

const useCreateMaintenanceOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<MaintenanceOrder>) => {
      return api.post('/v1/maintenance/orders', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['maintenance'] })
  });
};

const useUpdateOrderStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/v1/maintenance/orders/${id}`, { status }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['maintenance'] })
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const AssetsView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterCriticality, setFilterCriticality] = useState<string>('');
  const { data: assets = [], isLoading } = useAssets({
    type: filterType || undefined,
    status: filterStatus || undefined,
    criticality: filterCriticality || undefined
  });
  const createAsset = useCreateAsset();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<Asset>>({});

  const handleSubmit = async () => {
    await createAsset.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<Asset>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = ASSET_TYPES.find(t => t.value === v);
      return info?.label || (v as string);
    }},
    { id: 'location', header: 'Emplacement', accessor: 'location', render: (v) => (v as string) || '-' },
    { id: 'criticality', header: 'Criticite', accessor: 'criticality', render: (v) => {
      const info = getStatusInfo(CRITICALITIES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(ASSET_STATUSES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'next_maintenance_date', header: 'Proch. maint.', accessor: 'next_maintenance_date', render: (v) => (v as string) ? formatDate(v as string) : '-' }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Equipements</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous types' }, ...ASSET_TYPES]}
            className="w-32"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...ASSET_STATUSES]}
            className="w-40"
          />
          <Select
            value={filterCriticality}
            onChange={(v) => setFilterCriticality(v)}
            options={[{ value: '', label: 'Toutes criticites' }, ...CRITICALITIES]}
            className="w-40"
          />
          <Button onClick={() => setShowModal(true)}>Nouvel equipement</Button>
        </div>
      </div>
      <DataTable columns={columns} data={assets} isLoading={isLoading} keyField="id" />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvel equipement" size="lg">
        <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Code</label>
              <Input
                value={formData.code || ''}
                onChange={(v) => setFormData({ ...formData, code: v })}
              />
            </div>
            <div className="azals-field">
              <label>Nom</label>
              <Input
                value={formData.name || ''}
                onChange={(v) => setFormData({ ...formData, name: v })}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Type</label>
              <Select
                value={formData.type || ''}
                onChange={(v) => setFormData({ ...formData, type: v as Asset['type'] })}
                options={ASSET_TYPES}
              />
            </div>
            <div className="azals-field">
              <label>Criticite</label>
              <Select
                value={formData.criticality || ''}
                onChange={(v) => setFormData({ ...formData, criticality: v as Asset['criticality'] })}
                options={CRITICALITIES}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Emplacement</label>
              <Input
                value={formData.location || ''}
                onChange={(v) => setFormData({ ...formData, location: v })}
              />
            </div>
            <div className="azals-field">
              <label>N de serie</label>
              <Input
                value={formData.serial_number || ''}
                onChange={(v) => setFormData({ ...formData, serial_number: v })}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Fabricant</label>
              <Input
                value={formData.manufacturer || ''}
                onChange={(v) => setFormData({ ...formData, manufacturer: v })}
              />
            </div>
            <div className="azals-field">
              <label>Modele</label>
              <Input
                value={formData.model || ''}
                onChange={(v) => setFormData({ ...formData, model: v })}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Date d'achat</label>
              <input
                type="date"
                className="azals-input"
                value={formData.purchase_date || ''}
                onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label>Fin de garantie</label>
              <input
                type="date"
                className="azals-input"
                value={formData.warranty_end_date || ''}
                onChange={(e) => setFormData({ ...formData, warranty_end_date: e.target.value })}
              />
            </div>
          </Grid>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createAsset.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const MaintenanceOrdersView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterPriority, setFilterPriority] = useState<string>('');
  const { data: orders = [], isLoading } = useMaintenanceOrders({
    type: filterType || undefined,
    status: filterStatus || undefined,
    priority: filterPriority || undefined
  });
  const { data: assets = [] } = useAssets();
  const createOrder = useCreateMaintenanceOrder();
  const updateStatus = useUpdateOrderStatus();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<MaintenanceOrder>>({});
  const [description, setDescription] = useState('');

  const handleSubmit = async () => {
    await createOrder.mutateAsync({ ...formData, description });
    setShowModal(false);
    setFormData({});
    setDescription('');
  };

  const columns: TableColumn<MaintenanceOrder>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'asset_name', header: 'Equipement', accessor: 'asset_name', render: (v, row: MaintenanceOrder) => (
      <button
        className="text-blue-600 hover:underline"
        onClick={() => navigateTo('maintenance', { view: 'assets', id: row.asset_id })}
      >
        {v as string} ({row.asset_code})
      </button>
    )},
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = ORDER_TYPES.find(t => t.value === v);
      return info?.label || (v as string);
    }},
    { id: 'priority', header: 'Priorite', accessor: 'priority', render: (v) => {
      const info = getStatusInfo(ORDER_PRIORITIES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'planned_start_date', header: 'Date prevue', accessor: 'planned_start_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'assigned_to_name', header: 'Assigne a', accessor: 'assigned_to_name', render: (v) => (v as string) || '-' },
    { id: 'total_cost', header: 'Cout', accessor: 'total_cost', render: (v) => formatCurrency(v as number) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v, row: MaintenanceOrder) => (
      <Select
        value={v as string}
        onChange={(newValue) => updateStatus.mutate({ id: row.id, status: newValue })}
        options={ORDER_STATUSES}
        className="w-36"
      />
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Ordres de maintenance</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous types' }, ...ORDER_TYPES]}
            className="w-36"
          />
          <Select
            value={filterPriority}
            onChange={(v) => setFilterPriority(v)}
            options={[{ value: '', label: 'Toutes priorites' }, ...ORDER_PRIORITIES]}
            className="w-40"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...ORDER_STATUSES]}
            className="w-36"
          />
          <Button onClick={() => setShowModal(true)}>Nouvel ordre</Button>
        </div>
      </div>
      <DataTable columns={columns} data={orders} isLoading={isLoading} keyField="id" />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvel ordre de maintenance" size="lg">
        <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
          <div className="azals-field">
            <label>Equipement</label>
            <Select
              value={formData.asset_id || ''}
              onChange={(v) => setFormData({ ...formData, asset_id: v })}
              options={assets.map(a => ({ value: a.id, label: `${a.code} - ${a.name}` }))}
            />
          </div>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Type</label>
              <Select
                value={formData.type || ''}
                onChange={(v) => setFormData({ ...formData, type: v as MaintenanceOrder['type'] })}
                options={ORDER_TYPES}
              />
            </div>
            <div className="azals-field">
              <label>Priorite</label>
              <Select
                value={formData.priority || 'NORMAL'}
                onChange={(v) => setFormData({ ...formData, priority: v as MaintenanceOrder['priority'] })}
                options={ORDER_PRIORITIES}
              />
            </div>
          </Grid>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-1">Description</label>
            <textarea
              className="w-full border rounded px-3 py-2"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={3}
            />
          </div>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Date de debut prevue</label>
              <input
                type="date"
                className="azals-input"
                value={formData.planned_start_date || ''}
                onChange={(e) => setFormData({ ...formData, planned_start_date: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label>Date de fin prevue</label>
              <input
                type="date"
                className="azals-input"
                value={formData.planned_end_date || ''}
                onChange={(e) => setFormData({ ...formData, planned_end_date: e.target.value })}
              />
            </div>
          </Grid>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createOrder.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const PlansView: React.FC = () => {
  const { data: plans = [], isLoading } = useMaintenancePlans();
  const [filterFrequency, setFilterFrequency] = useState<string>('');

  const filteredData = filterFrequency
    ? plans.filter(p => p.frequency === filterFrequency)
    : plans;

  const columns: TableColumn<MaintenancePlan>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'asset_name', header: 'Equipement', accessor: 'asset_name', render: (v, row: MaintenancePlan) => (v as string) || row.asset_type || 'Tous' },
    { id: 'frequency', header: 'Frequence', accessor: 'frequency', render: (v, row: MaintenancePlan) => {
      const info = FREQUENCIES.find(f => f.value === v);
      return `${info?.label || (v as string)} (${row.frequency_value})`;
    }},
    { id: 'tasks', header: 'Taches', accessor: 'tasks', render: (v) => <Badge color="blue">{(v as MaintenanceTask[])?.length || 0}</Badge> },
    { id: 'next_execution_date', header: 'Proch. execution', accessor: 'next_execution_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Plans de maintenance</h3>
        <div className="flex gap-2">
          <Select
            value={filterFrequency}
            onChange={(v) => setFilterFrequency(v)}
            options={[{ value: '', label: 'Toutes frequences' }, ...FREQUENCIES]}
            className="w-48"
          />
          <Button>Nouveau plan</Button>
        </div>
      </div>
      <DataTable columns={columns} data={filteredData} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'assets' | 'orders' | 'plans';

const MaintenanceModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: dashboard } = useMaintenanceDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'assets', label: 'Equipements' },
    { id: 'orders', label: 'Ordres' },
    { id: 'plans', label: 'Plans preventifs' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'assets':
        return <AssetsView />;
      case 'orders':
        return <MaintenanceOrdersView />;
      case 'plans':
        return <PlansView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Operationnels"
                value={String(dashboard?.assets_operational || 0)}
                icon={<Check />}
                variant="success"
                onClick={() => setCurrentView('assets')}
              />
              <StatCard
                title="En maintenance"
                value={String(dashboard?.assets_under_maintenance || 0)}
                icon={<Wrench />}
                variant="warning"
                onClick={() => setCurrentView('assets')}
              />
              <StatCard
                title="Hors service"
                value={String(dashboard?.assets_out_of_service || 0)}
                icon={<X />}
                variant="danger"
                onClick={() => setCurrentView('assets')}
              />
              <StatCard
                title="Ordres en cours"
                value={String(dashboard?.orders_in_progress || 0)}
                icon={<Cog />}
                variant="default"
                onClick={() => setCurrentView('orders')}
              />
            </Grid>
            <Grid cols={4}>
              <StatCard
                title="Ordres en retard"
                value={String(dashboard?.orders_overdue || 0)}
                icon={<AlertTriangle />}
                variant="danger"
                onClick={() => setCurrentView('orders')}
              />
              <StatCard
                title="Preventives a venir"
                value={String(dashboard?.upcoming_preventive || 0)}
                icon={<Calendar />}
                variant="default"
                onClick={() => setCurrentView('plans')}
              />
              <StatCard
                title="MTBF"
                value={`${dashboard?.mtbf || 0}h`}
                icon={<BarChart3 />}
                variant="default"
              />
              <StatCard
                title="MTTR"
                value={`${dashboard?.mttr || 0}h`}
                icon={<Clock />}
                variant="warning"
              />
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper
      title="Maintenance"
      subtitle="Gestion de la maintenance et des equipements"
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

export default MaintenanceModule;
