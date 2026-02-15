/**
 * AZALSCORE Module - CRM
 * Gestion des prospects, clients et opportunités
 * Architecture BaseViewStandard pour la vue détail client
 */

import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedQuery } from '@/ui-engine/hooks';
import {
  Users, UserPlus, Phone, Mail, Building2, MapPin,
  TrendingUp, Target, Calendar, Clock, Euro,
  ChevronRight, Plus, Edit, Trash2, Search,
  CheckCircle2, XCircle, FileText, Star, AlertTriangle,
  Sparkles, ArrowLeft, Printer, Shield
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';
import type { SemanticColor } from '@ui/standards';
import {
  BaseViewStandard,
  type TabDefinition,
  type InfoBarItem,
  type SidebarSection,
  type ActionDefinition
} from '@ui/standards';

// Types et helpers
import type {
  Customer, Opportunity, PipelineStats, SalesDashboard,
  CustomerType, OpportunityStatus
} from './types';
import {
  CUSTOMER_TYPE_CONFIG, OPPORTUNITY_STATUS_CONFIG,
  isProspect, isActiveCustomer, canConvert, getCustomerValue
} from './types';
import { formatCurrency, formatDate } from '@/utils/formatters';

// Composants tabs
import {
  CustomerInfoTab,
  CustomerOpportunitiesTab,
  CustomerFinancialTab,
  CustomerDocsTab,
  CustomerHistoryTab,
  CustomerIATab,
  CustomerRiskTab
} from './components';

// ============================================================
// COMPONENTS LOCAUX
// ============================================================

const CustomerTypeBadge: React.FC<{ type: CustomerType }> = ({ type }) => {
  const config = CUSTOMER_TYPE_CONFIG[type];
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.label}
    </span>
  );
};

const OpportunityStatusBadge: React.FC<{ status: OpportunityStatus }> = ({ status }) => {
  const config = OPPORTUNITY_STATUS_CONFIG[status];
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.label}
    </span>
  );
};

// ============================================================
// API HOOKS
// ============================================================

const useCustomers = (page = 1, pageSize = 25, filters?: { type?: string; search?: string; is_active?: boolean }) => {
  return useQuery({
    queryKey: ['commercial', 'customers', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
      if (filters?.type) params.append('type', filters.type);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const response = await api.get<PaginatedResponse<Customer>>(`/v3/commercial/customers?${params}`);
      return response.data;
    },
  });
};

const useCustomer = (id: string) => {
  return useQuery({
    queryKey: ['commercial', 'customers', id],
    queryFn: async () => {
      const response = await api.get<Customer>(`/v3/commercial/customers/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

const useOpportunities = (page = 1, pageSize = 25, filters?: { status?: string; customer_id?: string }) => {
  return useQuery({
    queryKey: ['commercial', 'opportunities', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
      if (filters?.status) params.append('status', filters.status);
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      const response = await api.get<PaginatedResponse<Opportunity>>(`/v3/commercial/opportunities?${params}`);
      return response.data;
    },
  });
};

const usePipelineStats = () => {
  return useQuery({
    queryKey: ['commercial', 'pipeline', 'stats'],
    queryFn: async () => {
      const response = await api.get<PipelineStats>('/v3/commercial/pipeline/stats');
      return response.data;
    },
  });
};

const useSalesDashboard = () => {
  return useQuery({
    queryKey: ['commercial', 'dashboard'],
    queryFn: async () => {
      const response = await api.get<SalesDashboard>('/v3/commercial/dashboard');
      return response.data;
    },
  });
};

const useCreateCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Customer>) => {
      const response = await api.post<Customer>('/v3/commercial/customers', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'customers'] });
    },
  });
};

const useUpdateCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Customer> }) => {
      const response = await api.put<Customer>(`/v3/commercial/customers/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'customers'] });
    },
  });
};

const useDeleteCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v3/commercial/customers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'customers'] });
    },
  });
};

const useConvertProspect = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (customerId: string) => {
      const response = await api.post<Customer>(`/v3/commercial/customers/${customerId}/convert`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'customers'] });
    },
  });
};

// ============================================================
// VUE DÉTAIL CLIENT - BaseViewStandard
// ============================================================

interface CustomerDetailViewProps {
  customerId: string;
  onBack: () => void;
  onEdit: () => void;
}

const CustomerDetailView: React.FC<CustomerDetailViewProps> = ({ customerId, onBack, onEdit }) => {
  const { data: customer, isLoading, error } = useCustomer(customerId);
  const convertProspect = useConvertProspect();
  const deleteCustomer = useDeleteCustomer();
  const queryClient = useQueryClient();

  if (isLoading) {
    return (
      <div className="azals-loading-container">
        <div className="azals-spinner" />
        <p>Chargement du client...</p>
      </div>
    );
  }

  if (error || !customer) {
    return (
      <div className="azals-error-container">
        <AlertTriangle size={48} className="text-danger" />
        <p>Erreur lors du chargement du client</p>
        <Button variant="secondary" onClick={onBack}>Retour à la liste</Button>
      </div>
    );
  }

  const handleConvert = async () => {
    if (window.confirm('Convertir ce prospect en client ?')) {
      await convertProspect.mutateAsync(customerId);
      queryClient.invalidateQueries({ queryKey: ['commercial', 'customers', customerId] });
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Supprimer ce contact ?')) {
      await deleteCustomer.mutateAsync(customerId);
      onBack();
    }
  };

  const handleCreateDevis = () => {
    window.dispatchEvent(new CustomEvent('azals:navigate', {
      detail: { view: 'devis', params: { customerId, action: 'new' } }
    }));
  };

  // Définition des onglets
  const tabs: TabDefinition<Customer>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <Building2 size={16} />,
      component: CustomerInfoTab
    },
    {
      id: 'opportunities',
      label: 'Opportunités',
      icon: <Target size={16} />,
      badge: customer.opportunities?.length || 0,
      component: CustomerOpportunitiesTab
    },
    {
      id: 'financial',
      label: 'Financier',
      icon: <Euro size={16} />,
      component: CustomerFinancialTab
    },
    {
      id: 'docs',
      label: 'Documents',
      icon: <FileText size={16} />,
      badge: customer.documents?.length || 0,
      component: CustomerDocsTab
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <Clock size={16} />,
      component: CustomerHistoryTab
    },
    {
      id: 'risk',
      label: 'Risque',
      icon: <Shield size={16} />,
      component: CustomerRiskTab
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: CustomerIATab
    }
  ];

  // Barre d'info
  const typeConfig = CUSTOMER_TYPE_CONFIG[customer.type];
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'code',
      label: 'Code',
      value: customer.code,
      icon: <Building2 size={14} />
    },
    {
      id: 'type',
      label: 'Type',
      value: typeConfig.label,
      valueColor: typeConfig.color as SemanticColor
    },
    {
      id: 'city',
      label: 'Ville',
      value: customer.city || '-',
      icon: <MapPin size={14} />
    },
    {
      id: 'ca',
      label: 'CA Total',
      value: formatCurrency(customer.total_revenue || 0),
      valueColor: customer.total_revenue && customer.total_revenue > 10000 ? 'green' : undefined
    }
  ];

  // Sidebar
  const sidebarSections: SidebarSection[] = [
    {
      id: 'contact',
      title: 'Contact',
      items: [
        {
          id: 'email',
          label: 'Email',
          value: customer.email || '-'
        },
        {
          id: 'phone',
          label: 'Téléphone',
          value: customer.phone || '-'
        },
        {
          id: 'mobile',
          label: 'Mobile',
          value: customer.mobile || '-'
        }
      ]
    },
    {
      id: 'commercial',
      title: 'Commercial',
      items: [
        {
          id: 'orders',
          label: 'Commandes',
          value: String(customer.order_count || 0)
        },
        {
          id: 'revenue',
          label: 'CA Total',
          value: formatCurrency(customer.total_revenue || 0),
          highlight: true
        },
        {
          id: 'last_order',
          label: 'Dernière commande',
          value: customer.last_order_date ? formatDate(customer.last_order_date) : '-'
        }
      ]
    }
  ];

  // Actions header
  const headerActions: ActionDefinition[] = [
    {
      id: 'back',
      label: 'Retour',
      icon: <ArrowLeft size={16} />,
      variant: 'ghost',
      onClick: onBack
    },
    {
      id: 'print',
      label: 'Imprimer',
      icon: <Printer size={16} />,
      variant: 'secondary'
    }
  ];

  // Actions primaires
  const primaryActions: ActionDefinition[] = [];

  if (canConvert(customer)) {
    primaryActions.push({
      id: 'convert',
      label: 'Convertir en client',
      icon: <CheckCircle2 size={16} />,
      variant: 'primary',
      onClick: handleConvert
    });
  }

  primaryActions.push({
    id: 'devis',
    label: 'Créer devis',
    icon: <FileText size={16} />,
    variant: 'secondary',
    onClick: handleCreateDevis
  });

  primaryActions.push({
    id: 'edit',
    label: 'Modifier',
    icon: <Edit size={16} />,
    variant: 'ghost',
    onClick: onEdit
  });

  // Statut
  const statusColorMap: Record<string, SemanticColor> = {
    gray: 'gray',
    blue: 'blue',
    green: 'green',
    yellow: 'yellow',
    purple: 'purple',
    red: 'red'
  };

  return (
    <BaseViewStandard<Customer>
      title={customer.name}
      subtitle={customer.legal_name || customer.code}
      status={{
        label: typeConfig.label,
        color: statusColorMap[typeConfig.color] || 'gray'
      }}
      data={customer}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      primaryActions={primaryActions}
    />
  );
};

// ============================================================
// DASHBOARD
// ============================================================

interface DashboardProps {
  onNavigateToCustomers: () => void;
  onNavigateToOpportunities: () => void;
  onSelectCustomer: (id: string) => void;
  onSelectOpportunity: (id: string) => void;
  onCreateCustomer: () => void;
}

const CRMDashboard: React.FC<DashboardProps> = ({
  onNavigateToCustomers,
  onNavigateToOpportunities,
  onSelectCustomer,
  onSelectOpportunity,
  onCreateCustomer
}) => {
  const { data: dashboard } = useSalesDashboard();
  const { data: pipeline } = usePipelineStats();
  const { data: customers } = useCustomers(1, 5, { type: 'PROSPECT' });
  const { data: opportunities } = useOpportunities(1, 5);

  const kpis: DashboardKPI[] = dashboard ? [
    { id: 'pipeline', label: 'Pipeline', value: formatCurrency(dashboard.pipeline_value), icon: <Euro size={20} /> },
    { id: 'revenue', label: 'CA Mois', value: formatCurrency(dashboard.revenue_mtd), icon: <TrendingUp size={20} /> },
    { id: 'orders', label: 'Commandes', value: dashboard.orders_mtd, icon: <FileText size={20} /> },
    { id: 'customers', label: 'Nouveaux clients', value: dashboard.new_customers_mtd, icon: <UserPlus size={20} /> },
  ] : [];

  return (
    <PageWrapper
      title="CRM"
      subtitle="Prospects, clients et opportunités"
      actions={
        <Button leftIcon={<Plus size={16} />} onClick={onCreateCustomer}>
          Nouveau prospect
        </Button>
      }
    >
      <section className="azals-section">
        <Grid cols={4} gap="md">
          {kpis.map(kpi => <KPICard key={kpi.id} kpi={kpi} />)}
        </Grid>
      </section>

      <section className="azals-section">
        <Grid cols={2} gap="lg">
          <Card
            title="Prospects récents"
            actions={<Button variant="ghost" size="sm" onClick={onNavigateToCustomers}>Voir tout</Button>}
          >
            {customers?.items && customers.items.length > 0 ? (
              <ul className="azals-simple-list">
                {customers.items.map(c => (
                  <li key={c.id} onClick={() => onSelectCustomer(c.id)} className="azals-clickable">
                    <div className="azals-list-item__main">
                      <strong>{c.name}</strong>
                      {c.legal_name && <span className="text-muted"> - {c.legal_name}</span>}
                    </div>
                    <CustomerTypeBadge type={c.type} />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted text-center py-4">Aucun prospect</p>
            )}
          </Card>

          <Card
            title="Opportunités en cours"
            actions={<Button variant="ghost" size="sm" onClick={onNavigateToOpportunities}>Voir tout</Button>}
          >
            {opportunities?.items && opportunities.items.length > 0 ? (
              <ul className="azals-simple-list">
                {opportunities.items.filter(o => !['WON', 'LOST'].includes(o.status)).slice(0, 5).map(o => (
                  <li key={o.id} onClick={() => onSelectOpportunity(o.id)} className="azals-clickable">
                    <div className="azals-list-item__main">
                      <strong>{o.name}</strong>
                    </div>
                    <div className="azals-list-item__meta">
                      <OpportunityStatusBadge status={o.status} />
                      <span className="ml-2">{formatCurrency(o.amount)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted text-center py-4">Aucune opportunité</p>
            )}
          </Card>
        </Grid>
      </section>

      {pipeline && (
        <section className="azals-section">
          <Card title="Pipeline commercial">
            <div className="azals-pipeline">
              {pipeline.by_stage?.map((stage, i) => (
                <div key={i} className="azals-pipeline__stage">
                  <div className="azals-pipeline__stage-header">
                    <span className="azals-pipeline__stage-name">{stage.stage}</span>
                    <span className="azals-pipeline__stage-count">{stage.count}</span>
                  </div>
                  <div className="azals-pipeline__stage-value">{formatCurrency(stage.value)}</div>
                </div>
              ))}
            </div>
            <div className="azals-pipeline__summary mt-4">
              <div><strong>Taux de conversion:</strong> {pipeline.conversion_rate?.toFixed(1)}%</div>
              <div><strong>Valeur pondérée:</strong> {formatCurrency(pipeline.weighted_value || 0)}</div>
            </div>
          </Card>
        </section>
      )}
    </PageWrapper>
  );
};

// ============================================================
// CUSTOMERS LIST
// ============================================================

interface CustomersListProps {
  onSelectCustomer: (id: string) => void;
  onCreateCustomer: () => void;
  onBack: () => void;
}

const CustomersList: React.FC<CustomersListProps> = ({ onSelectCustomer, onCreateCustomer, onBack }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{ type?: string; search?: string }>({});

  const { data, isLoading, refetch } = useCustomers(page, pageSize, filters);

  const columns: TableColumn<Customer>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      sortable: true,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      sortable: true,
      render: (value, row) => (
        <span className="azals-link" onClick={() => onSelectCustomer(row.id)}>{value as string}</span>
      ),
    },
    { id: 'legal_name', header: 'Raison sociale', accessor: 'legal_name' },
    { id: 'city', header: 'Ville', accessor: 'city' },
    { id: 'phone', header: 'Téléphone', accessor: 'phone' },
    {
      id: 'type',
      header: 'Type',
      accessor: 'type',
      render: (value) => <CustomerTypeBadge type={value as CustomerType} />,
    },
    {
      id: 'total_revenue',
      header: 'CA Total',
      accessor: 'total_revenue',
      align: 'right',
      render: (value) => value ? formatCurrency(value as number) : '-',
    },
  ];

  return (
    <PageWrapper
      title="Clients & Prospects"
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={<Button leftIcon={<Plus size={16} />} onClick={onCreateCustomer}>Nouveau</Button>}
    >
      <Card noPadding>
        <div className="azals-filter-bar">
          <div className="azals-filter-bar__search">
            <Search size={16} />
            <input
              type="text"
              placeholder="Rechercher..."
              value={filters.search || ''}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="azals-input"
            />
          </div>
          <select
            className="azals-select"
            value={filters.type || ''}
            onChange={(e) => setFilters({ ...filters, type: e.target.value || undefined })}
          >
            <option value="">Tous les types</option>
            {Object.entries(CUSTOMER_TYPE_CONFIG).map(([key, config]) => (
              <option key={key} value={key}>{config.label}</option>
            ))}
          </select>
        </div>

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage="Aucun client"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// CUSTOMER FORM
// ============================================================

interface CustomerFormProps {
  customerId?: string;
  onBack: () => void;
  onSaved: (id: string) => void;
}

const CustomerForm: React.FC<CustomerFormProps> = ({ customerId, onBack, onSaved }) => {
  const isNew = !customerId;
  const { data: customer } = useCustomer(customerId || '');
  const createCustomer = useCreateCustomer();
  const updateCustomer = useUpdateCustomer();

  const [form, setForm] = useState({
    code: '',
    name: '',
    legal_name: '',
    type: 'PROSPECT' as CustomerType,
    email: '',
    phone: '',
    mobile: '',
    address_line1: '',
    city: '',
    postal_code: '',
    country_code: 'FR',
    tax_id: '',
    registration_number: '',
    industry: '',
    source: '',
    notes: '',
  });

  React.useEffect(() => {
    if (customer) {
      setForm({
        code: customer.code || '',
        name: customer.name || '',
        legal_name: customer.legal_name || '',
        type: customer.type,
        email: customer.email || '',
        phone: customer.phone || '',
        mobile: customer.mobile || '',
        address_line1: customer.address_line1 || '',
        city: customer.city || '',
        postal_code: customer.postal_code || '',
        country_code: customer.country_code || 'FR',
        tax_id: customer.tax_id || '',
        registration_number: customer.registration_number || '',
        industry: customer.industry || '',
        source: customer.source || '',
        notes: customer.notes || '',
      });
    }
  }, [customer]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isNew) {
        const result = await createCustomer.mutateAsync(form);
        onSaved(result.id);
      } else {
        await updateCustomer.mutateAsync({ id: customerId!, data: form });
        onSaved(customerId!);
      }
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    }
  };

  const isSubmitting = createCustomer.isPending || updateCustomer.isPending;

  return (
    <PageWrapper
      title={isNew ? 'Nouveau prospect' : 'Modifier'}
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <form onSubmit={handleSubmit}>
        <Card title="Informations">
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>Code *</label>
              <input type="text" className="azals-input" value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} required />
            </div>
            <div className="azals-form-field">
              <label>Type</label>
              <select className="azals-select" value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value as CustomerType })}>
                {Object.entries(CUSTOMER_TYPE_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Nom *</label>
              <input type="text" className="azals-input" value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="azals-form-field">
              <label>Raison sociale</label>
              <input type="text" className="azals-input" value={form.legal_name}
                onChange={(e) => setForm({ ...form, legal_name: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Email</label>
              <input type="email" className="azals-input" value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Téléphone</label>
              <input type="tel" className="azals-input" value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
          </Grid>
        </Card>

        <Card title="Adresse">
          <Grid cols={3} gap="md">
            <div className="azals-form-field" style={{ gridColumn: 'span 3' }}>
              <label>Adresse</label>
              <input type="text" className="azals-input" value={form.address_line1}
                onChange={(e) => setForm({ ...form, address_line1: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Code postal</label>
              <input type="text" className="azals-input" value={form.postal_code}
                onChange={(e) => setForm({ ...form, postal_code: e.target.value })} />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Ville</label>
              <input type="text" className="azals-input" value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })} />
            </div>
          </Grid>
        </Card>

        <Card title="Informations légales">
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>N° TVA</label>
              <input type="text" className="azals-input" value={form.tax_id}
                onChange={(e) => setForm({ ...form, tax_id: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>SIRET</label>
              <input type="text" className="azals-input" value={form.registration_number}
                onChange={(e) => setForm({ ...form, registration_number: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Secteur d'activité</label>
              <input type="text" className="azals-input" value={form.industry}
                onChange={(e) => setForm({ ...form, industry: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Source</label>
              <input type="text" className="azals-input" value={form.source}
                onChange={(e) => setForm({ ...form, source: e.target.value })} placeholder="Site web, salon, recommandation..." />
            </div>
          </Grid>
        </Card>

        <Card title="Notes">
          <textarea className="azals-textarea" value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={4} />
        </Card>

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onBack}>Annuler</Button>
          <Button type="submit" isLoading={isSubmitting}>{isNew ? 'Créer' : 'Enregistrer'}</Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================
// OPPORTUNITIES LIST
// ============================================================

interface OpportunitiesListProps {
  onSelectOpportunity: (id: string) => void;
  onBack: () => void;
}

const OpportunitiesList: React.FC<OpportunitiesListProps> = ({ onSelectOpportunity, onBack }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data, isLoading, refetch } = useOpportunities(page, pageSize, { status: statusFilter || undefined });

  const columns: TableColumn<Opportunity>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      sortable: true,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      sortable: true,
      render: (value, row) => (
        <span className="azals-link" onClick={() => onSelectOpportunity(row.id)}>{value as string}</span>
      ),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <OpportunityStatusBadge status={value as OpportunityStatus} />,
    },
    {
      id: 'amount',
      header: 'Montant',
      accessor: 'amount',
      align: 'right',
      render: (value, row) => formatCurrency(value as number, row.currency),
    },
    {
      id: 'probability',
      header: 'Probabilité',
      accessor: 'probability',
      align: 'right',
      render: (value) => `${value}%`,
    },
    {
      id: 'expected_close_date',
      header: 'Clôture prévue',
      accessor: 'expected_close_date',
      render: (value) => value ? formatDate(value as string) : '-',
    },
  ];

  return (
    <PageWrapper
      title="Opportunités"
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <Card noPadding>
        <div className="azals-filter-bar">
          <select
            className="azals-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">Tous les statuts</option>
            {Object.entries(OPPORTUNITY_STATUS_CONFIG).map(([key, config]) => (
              <option key={key} value={key}>{config.label}</option>
            ))}
          </select>
        </div>

        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage="Aucune opportunité"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// MODULE PRINCIPAL
// ============================================================

type CRMView = 'dashboard' | 'customers' | 'customer-detail' | 'customer-form' | 'opportunities' | 'opportunity-detail';

interface CRMNavState {
  view: CRMView;
  customerId?: string;
  opportunityId?: string;
  isNew?: boolean;
}

export const CRMModule: React.FC = () => {
  const [navState, setNavState] = useState<CRMNavState>({ view: 'dashboard' });

  const navigateToDashboard = useCallback(() => setNavState({ view: 'dashboard' }), []);
  const navigateToCustomers = useCallback(() => setNavState({ view: 'customers' }), []);
  const navigateToOpportunities = useCallback(() => setNavState({ view: 'opportunities' }), []);
  const navigateToCustomerDetail = useCallback((id: string) => setNavState({ view: 'customer-detail', customerId: id }), []);
  const navigateToCustomerForm = useCallback((id?: string) => setNavState({ view: 'customer-form', customerId: id, isNew: !id }), []);
  const navigateToOpportunityDetail = useCallback((id: string) => setNavState({ view: 'opportunity-detail', opportunityId: id }), []);

  switch (navState.view) {
    case 'customers':
      return (
        <CustomersList
          onSelectCustomer={navigateToCustomerDetail}
          onCreateCustomer={() => navigateToCustomerForm()}
          onBack={navigateToDashboard}
        />
      );
    case 'customer-detail':
      return (
        <CustomerDetailView
          customerId={navState.customerId!}
          onBack={navigateToCustomers}
          onEdit={() => navigateToCustomerForm(navState.customerId)}
        />
      );
    case 'customer-form':
      return (
        <CustomerForm
          customerId={navState.customerId}
          onBack={navState.isNew ? navigateToDashboard : () => navigateToCustomerDetail(navState.customerId!)}
          onSaved={navigateToCustomerDetail}
        />
      );
    case 'opportunities':
      return (
        <OpportunitiesList
          onSelectOpportunity={navigateToOpportunityDetail}
          onBack={navigateToDashboard}
        />
      );
    default:
      return (
        <CRMDashboard
          onNavigateToCustomers={navigateToCustomers}
          onNavigateToOpportunities={navigateToOpportunities}
          onSelectCustomer={navigateToCustomerDetail}
          onSelectOpportunity={navigateToOpportunityDetail}
          onCreateCustomer={() => navigateToCustomerForm()}
        />
      );
  }
};

export default CRMModule;
