/**
 * AZALSCORE Module - QUALITE
 * Gestion de la qualite, non-conformites et controles
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle, AlertCircle, Search, CheckCircle,
  Edit, FileText, Clock, Sparkles
} from 'lucide-react';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import { Button, Modal } from '@ui/actions';
import { StatCard } from '@ui/dashboards';
import { Select, Input, TextArea } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { BaseViewStandard } from '@ui/standards';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatDate } from '@/utils/formatters';
import {
  NCInfoTab,
  NCAnalysisTab,
  NCDocumentsTab,
  NCHistoryTab,
  NCStatsTab,
  NCIATab
} from './components';
import {
  getNCAge, getNCAgeDays, isNCOverdue, canEditNC, canCloseNC, getDocumentCount,
  NC_TYPE_CONFIG, SEVERITY_CONFIG, NC_STATUS_CONFIG,
  NC_TYPES, NC_ORIGINS, SEVERITIES, NC_STATUSES, QC_TYPES, INSPECTION_STATUSES
} from './types';
import { ErrorState } from '../../ui-engine/components/StateViews';
import type {
  NonConformance, QCRule, QCInspection, QCParameter, QualityDashboard,
  NCType, NCOrigin, NCSeverity
} from './types';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition, SemanticColor } from '@ui/standards';

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
// API HOOKS
// ============================================================================

const useQualityDashboard = () => {
  return useQuery({
    queryKey: ['quality', 'dashboard'],
    queryFn: async () => {
      return api.get<QualityDashboard>('/quality/dashboard').then(r => r.data);
    }
  });
};

const useNonConformances = (filters?: { type?: string; status?: string; severity?: string }) => {
  return useQuery({
    queryKey: ['quality', 'non-conformances', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.severity) params.append('severity', filters.severity);
      const query = params.toString();
      return api.get<NonConformance[]>(`/quality/non-conformances${query ? `?${query}` : ''}`).then(r => r.data);
    }
  });
};

const useNonConformance = (id: string) => {
  return useQuery({
    queryKey: ['quality', 'non-conformances', id],
    queryFn: async () => {
      return api.get<NonConformance>(`/quality/non-conformances/${id}`).then(r => r.data);
    },
    enabled: !!id,
  });
};

const useQCRules = (filters?: { type?: string }) => {
  return useQuery({
    queryKey: ['qc', 'rules', serializeFilters(filters)],
    queryFn: async () => {
      const query = filters?.type ? `?type=${encodeURIComponent(filters.type)}` : '';
      return api.get<QCRule[]>(`/qc/rules${query}`).then(r => r.data);
    }
  });
};

const useQCInspections = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: ['qc', 'inspections', serializeFilters(filters)],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const query = params.toString();
      return api.get<QCInspection[]>(`/qc/inspections${query ? `?${query}` : ''}`).then(r => r.data);
    }
  });
};

const useCreateNonConformance = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<NonConformance>) => {
      return api.post<NonConformance>('/quality/non-conformances', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['quality'] })
  });
};

const useUpdateNCStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch(`/quality/non-conformances/${id}`, { status }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['quality'] })
  });
};

const useCloseNC = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post(`/quality/non-conformances/${id}/close`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['quality'] })
  });
};

// ============================================================================
// HELPERS
// ============================================================================

const getStatusInfo = (statuses: any[], status: string) => {
  return statuses.find(s => s.value === status) || { label: status, color: 'gray' };
};

// ============================================================================
// NC DETAIL VIEW (BaseViewStandard)
// ============================================================================

const NCDetailView: React.FC<{
  ncId: string;
  onBack: () => void;
  onEdit: (id: string) => void;
}> = ({ ncId, onBack, onEdit }) => {
  const { data: nc, isLoading, error, refetch } = useNonConformance(ncId);
  const _updateStatus = useUpdateNCStatus();
  const closeNC = useCloseNC();

  if (isLoading) {
    return <PageWrapper title="Chargement..."><div className="azals-loading">Chargement...</div></PageWrapper>;
  }

  if (error) {
    return (
      <PageWrapper title="Erreur">
        <ErrorState message={error instanceof Error ? error.message : undefined} onRetry={() => refetch()} />
      </PageWrapper>
    );
  }

  if (!nc) {
    return (
      <PageWrapper title="NC non trouvee">
        <Card><p>Cette non-conformite n'existe pas.</p><Button onClick={onBack}>Retour</Button></Card>
      </PageWrapper>
    );
  }

  const typeConfig = NC_TYPE_CONFIG[nc.type];
  const severityConfig = SEVERITY_CONFIG[nc.severity];
  const statusConfig = NC_STATUS_CONFIG[nc.status];
  const canEdit = canEditNC(nc);
  const canClose = canCloseNC(nc);

  const handleClose = async () => {
    if (window.confirm('Cloturer cette non-conformite ?')) {
      await closeNC.mutateAsync(ncId);
    }
  };

  // Tab definitions
  const tabs: TabDefinition<NonConformance>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <FileText size={16} />,
      component: NCInfoTab,
    },
    {
      id: 'analysis',
      label: 'Analyse',
      icon: <Search size={16} />,
      component: NCAnalysisTab,
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={16} />,
      badge: getDocumentCount(nc),
      component: NCDocumentsTab,
    },
    {
      id: 'stats',
      label: 'Metriques',
      icon: <Clock size={16} />,
      component: NCStatsTab,
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <Clock size={16} />,
      component: NCHistoryTab,
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: NCIATab,
    },
  ];

  // InfoBar items
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'severity',
      label: 'Gravite',
      value: severityConfig.label,
      valueColor: severityConfig.color as SemanticColor,
    },
    {
      id: 'status',
      label: 'Statut',
      value: statusConfig.label,
      valueColor: statusConfig.color as SemanticColor,
    },
    {
      id: 'age',
      label: 'Age',
      value: getNCAge(nc),
      valueColor: getNCAgeDays(nc) > 30 ? 'orange' as SemanticColor : undefined,
    },
    {
      id: 'type',
      label: 'Type',
      value: typeConfig.label,
    },
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'nc',
      title: 'Non-conformite',
      items: [
        { id: 'number', label: 'Numero', value: nc.number },
        { id: 'detected', label: 'Detectee le', value: formatDate(nc.detected_date) },
        { id: 'target', label: 'Objectif', value: formatDate(nc.target_date), highlight: isNCOverdue(nc) },
      ],
    },
    {
      id: 'product',
      title: 'Produit',
      items: [
        { id: 'product', label: 'Produit', value: nc.product_name || '-' },
        { id: 'lot', label: 'N° lot', value: nc.lot_number || '-' },
      ],
    },
    {
      id: 'responsible',
      title: 'Responsables',
      items: [
        { id: 'detected_by', label: 'Detecte par', value: nc.detected_by_name || '-' },
        { id: 'responsible', label: 'Responsable', value: nc.responsible_name || 'Non assigne', highlight: !nc.responsible_name },
      ],
    },
  ];

  // Header actions
  const headerActions: ActionDefinition[] = [
    {
      id: 'back',
      label: 'Retour',
      variant: 'ghost',
      onClick: onBack,
    },
    ...(canClose ? [{
      id: 'close',
      label: 'Cloturer',
      icon: <CheckCircle size={16} />,
      onClick: handleClose,
    }] : []),
    ...(canEdit ? [{
      id: 'edit',
      label: 'Modifier',
      variant: 'ghost' as const,
      icon: <Edit size={16} />,
      onClick: () => onEdit(ncId),
    }] : []),
  ];

  return (
    <BaseViewStandard<NonConformance>
      title={`NC ${nc.number}`}
      subtitle={nc.description?.substring(0, 60) + (nc.description && nc.description.length > 60 ? '...' : '')}
      status={{
        label: statusConfig.label,
        color: statusConfig.color as SemanticColor,
      }}
      data={nc}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
    />
  );
};

// ============================================================================
// LIST VIEWS
// ============================================================================

const NonConformancesView: React.FC<{ onSelectNC: (id: string) => void }> = ({ onSelectNC }) => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterSeverity, setFilterSeverity] = useState<string>('');
  const { data: ncs = [], isLoading, error: ncsError, refetch: refetchNCs } = useNonConformances({
    type: filterType || undefined,
    status: filterStatus || undefined,
    severity: filterSeverity || undefined
  });
  const createNC = useCreateNonConformance();
  const _updateStatus = useUpdateNCStatus();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<NonConformance>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await createNC.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
    onSelectNC(result.id);
  };

  const columns: TableColumn<NonConformance>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v, row) => (
      <span className="azals-link" onClick={() => onSelectNC(row.id)}>
        <code className="font-mono">{v as string}</code>
      </span>
    )},
    { id: 'detected_date', header: 'Date', accessor: 'detected_date', render: (v) => formatDate(v as string) },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = NC_TYPES.find(t => t.value === v);
      return info?.label || (v as string);
    }},
    { id: 'origin', header: 'Origine', accessor: 'origin', render: (v) => {
      const info = NC_ORIGINS.find(o => o.value === v);
      return info?.label || (v as string);
    }},
    { id: 'product_name', header: 'Produit', accessor: 'product_name', render: (v) => (v as string) || '-' },
    { id: 'severity', header: 'Gravite', accessor: 'severity', render: (v) => {
      const info = getStatusInfo(SEVERITIES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(NC_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
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
      <DataTable columns={columns} data={ncs} isLoading={isLoading} keyField="id" filterable error={ncsError instanceof Error ? ncsError : null} onRetry={() => refetchNCs()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvelle non-conformite" size="lg">
        <form onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Type</label>
              <Select
                value={formData.type || ''}
                onChange={(v) => setFormData({ ...formData, type: v as NCType })}
                options={NC_TYPES}
              />
            </div>
            <div className="azals-field">
              <label>Origine</label>
              <Select
                value={formData.origin || ''}
                onChange={(v) => setFormData({ ...formData, origin: v as NCOrigin })}
                options={NC_ORIGINS}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Gravite</label>
              <Select
                value={formData.severity || ''}
                onChange={(v) => setFormData({ ...formData, severity: v as NCSeverity })}
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
  const { data: rules = [], isLoading, error: rulesError, refetch: refetchRules } = useQCRules({ type: filterType || undefined });

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
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createQCRule' } })); }}>Nouvelle regle</Button>
        </div>
      </div>
      <DataTable columns={columns} data={rules} isLoading={isLoading} keyField="id" filterable error={rulesError instanceof Error ? rulesError : null} onRetry={() => refetchRules()} />
    </Card>
  );
};

const InspectionsView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: inspections = [], isLoading, error: inspectionsError, refetch: refetchInspections } = useQCInspections({
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
    { id: 'quantity_accepted', header: 'Acceptee', accessor: 'quantity_accepted', render: (v, row) => (
      <span className={(v as number) === row.quantity_inspected ? 'text-green-600' : 'text-orange-600'}>
        {v as number}
      </span>
    )},
    { id: 'status', header: 'Resultat', accessor: 'status', render: (v) => {
      const info = getStatusInfo(INSPECTION_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
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
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createInspection' } })); }}>Nouvelle inspection</Button>
        </div>
      </div>
      <DataTable columns={columns} data={inspections} isLoading={isLoading} keyField="id" filterable error={inspectionsError instanceof Error ? inspectionsError : null} onRetry={() => refetchInspections()} />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'non-conformances' | 'nc-detail' | 'rules' | 'inspections';

interface NavState {
  view: View;
  ncId?: string;
}

const QualiteModule: React.FC = () => {
  const [navState, setNavState] = useState<NavState>({ view: 'dashboard' });
  const { data: dashboard } = useQualityDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'non-conformances', label: 'Non-conformites' },
    { id: 'rules', label: 'Regles QC' },
    { id: 'inspections', label: 'Inspections' }
  ];

  const navigateToNCDetail = useCallback((id: string) => {
    setNavState({ view: 'nc-detail', ncId: id });
  }, []);

  const navigateToNCList = useCallback(() => {
    setNavState({ view: 'non-conformances' });
  }, []);

  // NC Detail view
  if (navState.view === 'nc-detail' && navState.ncId) {
    return (
      <NCDetailView
        ncId={navState.ncId}
        onBack={navigateToNCList}
        onEdit={navigateToNCDetail}
      />
    );
  }

  const renderContent = () => {
    switch (navState.view) {
      case 'non-conformances':
        return <NonConformancesView onSelectNC={navigateToNCDetail} />;
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
                onClick={() => setNavState({ view: 'non-conformances' })}
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
                onClick={() => setNavState({ view: 'inspections' })}
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
        activeTab={navState.view === 'nc-detail' ? 'non-conformances' : navState.view}
        onChange={(id) => setNavState({ view: id as View })}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default QualiteModule;
