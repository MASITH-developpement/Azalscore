import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, AlertCircle, Search, CheckCircle } from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input, TextArea } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
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

interface NonConformance {
  id: string;
  number: string;
  type: 'INTERNAL' | 'SUPPLIER' | 'CUSTOMER';
  origin: 'PRODUCTION' | 'RECEPTION' | 'FIELD' | 'AUDIT';
  product_id?: string;
  product_name?: string;
  lot_number?: string;
  description: string;
  severity: 'MINOR' | 'MAJOR' | 'CRITICAL';
  status: 'OPEN' | 'IN_ANALYSIS' | 'ACTION_PLANNED' | 'CLOSED' | 'CANCELLED';
  root_cause?: string;
  corrective_action?: string;
  responsible_id?: string;
  responsible_name?: string;
  detected_date: string;
  closed_date?: string;
  created_at: string;
}

interface QCRule {
  id: string;
  code: string;
  name: string;
  type: 'INCOMING' | 'IN_PROCESS' | 'FINAL';
  product_id?: string;
  product_name?: string;
  category_id?: string;
  category_name?: string;
  parameters: QCParameter[];
  is_active: boolean;
}

interface QCParameter {
  id: string;
  name: string;
  type: 'NUMERIC' | 'BOOLEAN' | 'TEXT' | 'SELECT';
  unit?: string;
  min_value?: number;
  max_value?: number;
  target_value?: number;
  options?: string[];
  is_critical: boolean;
}

interface QCInspection {
  id: string;
  number: string;
  rule_id: string;
  rule_name?: string;
  type: 'INCOMING' | 'IN_PROCESS' | 'FINAL';
  reference_type: 'RECEIPT' | 'PRODUCTION_ORDER' | 'PICKING';
  reference_id: string;
  reference_number?: string;
  product_id: string;
  product_name?: string;
  lot_number?: string;
  quantity_inspected: number;
  quantity_accepted: number;
  quantity_rejected: number;
  status: 'PENDING' | 'IN_PROGRESS' | 'PASSED' | 'FAILED' | 'PARTIAL';
  results: QCResult[];
  inspector_id?: string;
  inspector_name?: string;
  inspection_date: string;
  created_at: string;
}

interface QCResult {
  id: string;
  parameter_id: string;
  parameter_name?: string;
  value: string | number | boolean;
  is_conformant: boolean;
  comment?: string;
}

interface QualityDashboard {
  open_non_conformances: number;
  pending_inspections: number;
  inspections_today: number;
  pass_rate: number;
  critical_nc_count: number;
  nc_by_type: { type: string; count: number }[];
  nc_by_origin: { origin: string; count: number }[];
}

// ============================================================================
// CONSTANTES
// ============================================================================

const NC_TYPES = [
  { value: 'INTERNAL', label: 'Interne' },
  { value: 'SUPPLIER', label: 'Fournisseur' },
  { value: 'CUSTOMER', label: 'Client' }
];

const NC_ORIGINS = [
  { value: 'PRODUCTION', label: 'Production' },
  { value: 'RECEPTION', label: 'Réception' },
  { value: 'FIELD', label: 'Terrain' },
  { value: 'AUDIT', label: 'Audit' }
];

const SEVERITIES = [
  { value: 'MINOR', label: 'Mineure', color: 'yellow' },
  { value: 'MAJOR', label: 'Majeure', color: 'orange' },
  { value: 'CRITICAL', label: 'Critique', color: 'red' }
];

const NC_STATUSES = [
  { value: 'OPEN', label: 'Ouverte', color: 'red' },
  { value: 'IN_ANALYSIS', label: 'En analyse', color: 'orange' },
  { value: 'ACTION_PLANNED', label: 'Action planifiée', color: 'blue' },
  { value: 'CLOSED', label: 'Clôturée', color: 'green' },
  { value: 'CANCELLED', label: 'Annulée', color: 'gray' }
];

const QC_TYPES = [
  { value: 'INCOMING', label: 'Réception' },
  { value: 'IN_PROCESS', label: 'En cours' },
  { value: 'FINAL', label: 'Final' }
];

const INSPECTION_STATUSES = [
  { value: 'PENDING', label: 'En attente', color: 'gray' },
  { value: 'IN_PROGRESS', label: 'En cours', color: 'blue' },
  { value: 'PASSED', label: 'Conforme', color: 'green' },
  { value: 'FAILED', label: 'Non conforme', color: 'red' },
  { value: 'PARTIAL', label: 'Partiel', color: 'orange' }
];

// ============================================================================
// HELPERS
// ============================================================================

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
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

const useQualityDashboard = () => {
  return useQuery({
    queryKey: ['quality', 'dashboard'],
    queryFn: async () => {
      return api.get<QualityDashboard>('/v1/quality/dashboard').then(r => r.data);
    }
  });
};

const useNonConformances = (filters?: { type?: string; status?: string; severity?: string }) => {
  return useQuery({
    queryKey: ['quality', 'non-conformances', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.severity) params.append('severity', filters.severity);
      const query = params.toString();
      return api.get<NonConformance[]>(`/v1/quality/non-conformances${query ? `?${query}` : ''}`).then(r => r.data);
    }
  });
};

const useQCRules = (filters?: { type?: string }) => {
  return useQuery({
    queryKey: ['qc', 'rules', filters],
    queryFn: async () => {
      const query = filters?.type ? `?type=${encodeURIComponent(filters.type)}` : '';
      return api.get<QCRule[]>(`/v1/qc/rules${query}`).then(r => r.data);
    }
  });
};

const useQCInspections = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: ['qc', 'inspections', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const query = params.toString();
      return api.get<QCInspection[]>(`/v1/qc/inspections${query ? `?${query}` : ''}`).then(r => r.data);
    }
  });
};

const useCreateNonConformance = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<NonConformance>) => {
      return api.post('/v1/quality/non-conformances', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['quality'] })
  });
};

const useUpdateNCStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/v1/quality/non-conformances/${id}`, { status }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['quality'] })
  });
};

const useCreateInspection = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<QCInspection>) => {
      return api.post('/v1/qc/inspections', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['qc'] })
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const NonConformancesView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterSeverity, setFilterSeverity] = useState<string>('');
  const { data: ncs = [], isLoading } = useNonConformances({
    type: filterType || undefined,
    status: filterStatus || undefined,
    severity: filterSeverity || undefined
  });
  const createNC = useCreateNonConformance();
  const updateStatus = useUpdateNCStatus();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<NonConformance>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createNC.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<NonConformance>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'detected_date', header: 'Date', accessor: 'detected_date', render: (v) => formatDate(v as string) },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = NC_TYPES.find(t => t.value === v);
      return info?.label || (v as string);
    }},
    { id: 'origin', header: 'Origine', accessor: 'origin', render: (v) => {
      const info = NC_ORIGINS.find(o => o.value === v);
      return info?.label || (v as string);
    }},
    { id: 'product_name', header: 'Produit', accessor: 'product_name', render: (v, row: NonConformance) => (v as string) ? (
      <button
        className="text-blue-600 hover:underline"
        onClick={() => navigateTo('stock', { view: 'products', id: row.product_id })}
      >
        {v as string}
      </button>
    ) : '-' },
    { id: 'severity', header: 'Gravite', accessor: 'severity', render: (v) => {
      const info = getStatusInfo(SEVERITIES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(NC_STATUSES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row: NonConformance) => (
      <Select
        value={row.status}
        onChange={(v) => updateStatus.mutate({ id: row.id, status: v })}
        options={NC_STATUSES}
        className="w-36"
      />
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Non-conformites</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous types' }, ...NC_TYPES]}
            className="w-32"
          />
          <Select
            value={filterSeverity}
            onChange={(v) => setFilterSeverity(v)}
            options={[{ value: '', label: 'Toutes gravites' }, ...SEVERITIES]}
            className="w-36"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...NC_STATUSES]}
            className="w-40"
          />
          <Button onClick={() => setShowModal(true)}>Nouvelle NC</Button>
        </div>
      </div>
      <DataTable columns={columns} data={ncs} isLoading={isLoading} keyField="id" />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvelle non-conformite" size="lg">
        <form onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Type</label>
              <Select
                value={formData.type || ''}
                onChange={(v) => setFormData({ ...formData, type: v as NonConformance['type'] })}
                options={NC_TYPES}
              />
            </div>
            <div className="azals-field">
              <label>Origine</label>
              <Select
                value={formData.origin || ''}
                onChange={(v) => setFormData({ ...formData, origin: v as NonConformance['origin'] })}
                options={NC_ORIGINS}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Gravite</label>
              <Select
                value={formData.severity || ''}
                onChange={(v) => setFormData({ ...formData, severity: v as NonConformance['severity'] })}
                options={SEVERITIES}
              />
            </div>
            <div className="azals-field">
              <label>Date de detection</label>
              <input
                type="date"
                className="azals-input"
                value={formData.detected_date || ''}
                onChange={(e) => setFormData({ ...formData, detected_date: e.target.value })}
                required
              />
            </div>
          </Grid>
          <div className="azals-field">
            <label>N de lot (optionnel)</label>
            <Input
              value={formData.lot_number || ''}
              onChange={(v) => setFormData({ ...formData, lot_number: v })}
            />
          </div>
          <div className="azals-field">
            <label className="block text-sm font-medium mb-1">Description *</label>
            <TextArea
              value={formData.description || ''}
              onChange={(v) => setFormData({ ...formData, description: v })}
              rows={3}
            />
          </div>
          <div className="azals-field">
            <label className="block text-sm font-medium mb-1">Cause racine (optionnel)</label>
            <TextArea
              value={formData.root_cause || ''}
              onChange={(v) => setFormData({ ...formData, root_cause: v })}
              rows={2}
            />
          </div>
          <div className="azals-field">
            <label className="block text-sm font-medium mb-1">Action corrective (optionnel)</label>
            <TextArea
              value={formData.corrective_action || ''}
              onChange={(v) => setFormData({ ...formData, corrective_action: v })}
              rows={2}
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createNC.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const QCRulesView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const { data: rules = [], isLoading } = useQCRules({ type: filterType || undefined });

  const columns: TableColumn<QCRule>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = QC_TYPES.find(t => t.value === v);
      return <Badge color="blue">{info?.label || (v as string)}</Badge>;
    }},
    { id: 'product_name', header: 'Produit', accessor: 'product_name', render: (v) => (v as string) || 'Tous' },
    { id: 'parameters', header: 'Parametres', accessor: 'parameters', render: (v) => (
      <Badge color="purple">{(v as QCParameter[])?.length || 0}</Badge>
    )},
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Regles de controle</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous les types' }, ...QC_TYPES]}
            className="w-40"
          />
          <Button>Nouvelle regle</Button>
        </div>
      </div>
      <DataTable columns={columns} data={rules} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const InspectionsView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: inspections = [], isLoading } = useQCInspections({
    type: filterType || undefined,
    status: filterStatus || undefined
  });

  const columns: TableColumn<QCInspection>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'inspection_date', header: 'Date', accessor: 'inspection_date', render: (v) => formatDate(v as string) },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = QC_TYPES.find(t => t.value === v);
      return info?.label || (v as string);
    }},
    { id: 'product_name', header: 'Produit', accessor: 'product_name' },
    { id: 'lot_number', header: 'Lot', accessor: 'lot_number', render: (v) => (v as string) || '-' },
    { id: 'quantity_inspected', header: 'Qte inspectee', accessor: 'quantity_inspected' },
    { id: 'quantity_accepted', header: 'Acceptee', accessor: 'quantity_accepted', render: (v, row: QCInspection) => (
      <span className={(v as number) === row.quantity_inspected ? 'text-green-600' : 'text-orange-600'}>
        {v as number}
      </span>
    )},
    { id: 'status', header: 'Resultat', accessor: 'status', render: (v) => {
      const info = getStatusInfo(INSPECTION_STATUSES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'inspector_name', header: 'Inspecteur', accessor: 'inspector_name', render: (v) => (v as string) || '-' }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Inspections</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous les types' }, ...QC_TYPES]}
            className="w-36"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous les statuts' }, ...INSPECTION_STATUSES]}
            className="w-40"
          />
          <Button>Nouvelle inspection</Button>
        </div>
      </div>
      <DataTable columns={columns} data={inspections} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'non-conformances' | 'rules' | 'inspections';

const QualiteModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: dashboard } = useQualityDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'non-conformances', label: 'Non-conformites' },
    { id: 'rules', label: 'Regles QC' },
    { id: 'inspections', label: 'Inspections' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'non-conformances':
        return <NonConformancesView />;
      case 'rules':
        return <QCRulesView />;
      case 'inspections':
        return <InspectionsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="NC ouvertes"
                value={String(dashboard?.open_non_conformances || 0)}
                icon={<AlertTriangle className="w-5 h-5" />}
                variant="danger"
                onClick={() => setCurrentView('non-conformances')}
              />
              <StatCard
                title="NC critiques"
                value={String(dashboard?.critical_nc_count || 0)}
                icon={<AlertCircle className="w-5 h-5" />}
                variant="danger"
              />
              <StatCard
                title="Inspections en attente"
                value={String(dashboard?.pending_inspections || 0)}
                icon={<Search className="w-5 h-5" />}
                variant="warning"
                onClick={() => setCurrentView('inspections')}
              />
              <StatCard
                title="Taux de conformite"
                value={`${((dashboard?.pass_rate || 0) * 100).toFixed(0)}%`}
                icon={<CheckCircle className="w-5 h-5" />}
                variant="success"
              />
            </Grid>
            <Grid cols={2}>
              {dashboard?.nc_by_type && dashboard.nc_by_type.length > 0 && (
                <Card>
                  <h3 className="text-lg font-semibold mb-4">NC par type</h3>
                  <div className="space-y-2">
                    {dashboard.nc_by_type.map((item, i) => {
                      const typeInfo = NC_TYPES.find(t => t.value === item.type);
                      return (
                        <div key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span>{typeInfo?.label || item.type}</span>
                          <Badge color="red">{item.count}</Badge>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}
              {dashboard?.nc_by_origin && dashboard.nc_by_origin.length > 0 && (
                <Card>
                  <h3 className="text-lg font-semibold mb-4">NC par origine</h3>
                  <div className="space-y-2">
                    {dashboard.nc_by_origin.map((item, i) => {
                      const originInfo = NC_ORIGINS.find(o => o.value === item.origin);
                      return (
                        <div key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span>{originInfo?.label || item.origin}</span>
                          <Badge color="orange">{item.count}</Badge>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Qualite" subtitle="Gestion de la qualite et controles">
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

export default QualiteModule;
