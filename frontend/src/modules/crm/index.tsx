/**
 * AZALSCORE Module - CRM
 * Gestion des prospects, clients et opportunités
 * Point d'entrée du flux : CRM → DEV → COM/ODS → AFF → FAC/AVO → CPT
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Users, UserPlus, Phone, Mail, Building2, MapPin,
  TrendingUp, Target, Calendar, Clock, Euro,
  ChevronRight, Plus, Edit, Trash2, Search,
  CheckCircle2, XCircle, AlertCircle, FileText, Star
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

// ============================================================
// TYPES (alignés sur le backend)
// ============================================================

type CustomerType = 'PROSPECT' | 'LEAD' | 'CUSTOMER' | 'VIP' | 'PARTNER' | 'CHURNED';
type OpportunityStatus = 'NEW' | 'QUALIFIED' | 'PROPOSAL' | 'NEGOTIATION' | 'WON' | 'LOST';

interface Customer {
  id: string;
  code: string;
  name: string;
  legal_name?: string;
  type: CustomerType;
  email?: string;
  phone?: string;
  mobile?: string;
  address_line1?: string;
  city?: string;
  postal_code?: string;
  country_code?: string;
  tax_id?: string;
  registration_number?: string;
  assigned_to?: string;
  industry?: string;
  source?: string;
  lead_score?: number;
  total_revenue?: number;
  order_count?: number;
  notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface Opportunity {
  id: string;
  code: string;
  name: string;
  description?: string;
  customer_id: string;
  customer_name?: string;
  status: OpportunityStatus;
  probability: number;
  amount: number;
  currency: string;
  expected_close_date?: string;
  assigned_to?: string;
  source?: string;
  notes?: string;
  created_at: string;
}

interface PipelineStats {
  total_opportunities: number;
  total_value: number;
  weighted_value: number;
  won_count: number;
  won_value: number;
  lost_count: number;
  conversion_rate: number;
  by_stage: Array<{ stage: string; count: number; value: number }>;
}

interface SalesDashboard {
  revenue_mtd: number;
  revenue_ytd: number;
  orders_mtd: number;
  orders_ytd: number;
  new_customers_mtd: number;
  pipeline_value: number;
  pending_quotes: number;
  pending_invoices: number;
  overdue_invoices: number;
}

// ============================================================
// CONSTANTS
// ============================================================

const CUSTOMER_TYPE_CONFIG: Record<CustomerType, { label: string; color: string; icon: React.ReactNode }> = {
  PROSPECT: { label: 'Prospect', color: 'gray', icon: <UserPlus size={14} /> },
  LEAD: { label: 'Lead', color: 'blue', icon: <Target size={14} /> },
  CUSTOMER: { label: 'Client', color: 'green', icon: <Users size={14} /> },
  VIP: { label: 'VIP', color: 'yellow', icon: <Star size={14} /> },
  PARTNER: { label: 'Partenaire', color: 'purple', icon: <Building2 size={14} /> },
  CHURNED: { label: 'Perdu', color: 'red', icon: <XCircle size={14} /> },
};

const OPPORTUNITY_STATUS_CONFIG: Record<OpportunityStatus, { label: string; color: string; probability: number }> = {
  NEW: { label: 'Nouveau', color: 'blue', probability: 10 },
  QUALIFIED: { label: 'Qualifié', color: 'yellow', probability: 30 },
  PROPOSAL: { label: 'Proposition', color: 'orange', probability: 50 },
  NEGOTIATION: { label: 'Négociation', color: 'purple', probability: 70 },
  WON: { label: 'Gagné', color: 'green', probability: 100 },
  LOST: { label: 'Perdu', color: 'red', probability: 0 },
};

// ============================================================
// HELPERS
// ============================================================

const formatCurrency = (value: number, currency = 'EUR'): string =>
  new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(value);

const formatDate = (date: string): string =>
  new Date(date).toLocaleDateString('fr-FR');

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
      const response = await api.get<PaginatedResponse<Customer>>(`/v1/commercial/customers?${params}`);
      return response.data;
    },
  });
};

const useCustomer = (id: string) => {
  return useQuery({
    queryKey: ['commercial', 'customers', id],
    queryFn: async () => {
      const response = await api.get<Customer>(`/v1/commercial/customers/${id}`);
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
      const response = await api.get<PaginatedResponse<Opportunity>>(`/v1/commercial/opportunities?${params}`);
      return response.data;
    },
  });
};

const useOpportunity = (id: string) => {
  return useQuery({
    queryKey: ['commercial', 'opportunities', id],
    queryFn: async () => {
      const response = await api.get<Opportunity>(`/v1/commercial/opportunities/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

const usePipelineStats = () => {
  return useQuery({
    queryKey: ['commercial', 'pipeline', 'stats'],
    queryFn: async () => {
      const response = await api.get<PipelineStats>('/v1/commercial/pipeline/stats');
      return response.data;
    },
  });
};

const useSalesDashboard = () => {
  return useQuery({
    queryKey: ['commercial', 'dashboard'],
    queryFn: async () => {
      const response = await api.get<SalesDashboard>('/v1/commercial/dashboard');
      return response.data;
    },
  });
};

const useCreateCustomer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Customer>) => {
      const response = await api.post<Customer>('/v1/commercial/customers', data);
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
      const response = await api.put<Customer>(`/v1/commercial/customers/${id}`, data);
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
      await api.delete(`/v1/commercial/customers/${id}`);
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
      const response = await api.post<Customer>(`/v1/commercial/customers/${customerId}/convert`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'customers'] });
    },
  });
};

const useCreateOpportunity = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Opportunity>) => {
      const response = await api.post<Opportunity>('/v1/commercial/opportunities', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'opportunities'] });
      queryClient.invalidateQueries({ queryKey: ['commercial', 'pipeline'] });
    },
  });
};

const useWinOpportunity = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      const response = await api.post<Opportunity>(`/v1/commercial/opportunities/${id}/win`, { win_reason: reason });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'opportunities'] });
      queryClient.invalidateQueries({ queryKey: ['commercial', 'pipeline'] });
    },
  });
};

const useLoseOpportunity = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason?: string }) => {
      const response = await api.post<Opportunity>(`/v1/commercial/opportunities/${id}/lose`, { loss_reason: reason });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'opportunities'] });
      queryClient.invalidateQueries({ queryKey: ['commercial', 'pipeline'] });
    },
  });
};

// ============================================================
// COMPONENTS
// ============================================================

const CustomerTypeBadge: React.FC<{ type: CustomerType }> = ({ type }) => {
  const config = CUSTOMER_TYPE_CONFIG[type];
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.icon}
      <span className="ml-1">{config.label}</span>
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
// NAVIGATION
// ============================================================

type CRMView = 'dashboard' | 'customers' | 'customer-detail' | 'customer-form' | 'opportunities' | 'opportunity-detail';

interface CRMNavState {
  view: CRMView;
  customerId?: string;
  opportunityId?: string;
  isNew?: boolean;
}

// ============================================================
// DASHBOARD
// ============================================================

const CRMDashboardInternal: React.FC<{
  onNavigateToCustomers: () => void;
  onNavigateToOpportunities: () => void;
  onSelectCustomer: (id: string) => void;
  onSelectOpportunity: (id: string) => void;
  onCreateCustomer: () => void;
}> = ({ onNavigateToCustomers, onNavigateToOpportunities, onSelectCustomer, onSelectOpportunity, onCreateCustomer }) => {
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

const CustomersListInternal: React.FC<{
  onSelectCustomer: (id: string) => void;
  onCreateCustomer: () => void;
  onBack: () => void;
}> = ({ onSelectCustomer, onCreateCustomer, onBack }) => {
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
// CUSTOMER DETAIL
// ============================================================

const CustomerDetailInternal: React.FC<{
  customerId: string;
  onBack: () => void;
  onEdit: () => void;
  onCreateOpportunity: () => void;
}> = ({ customerId, onBack, onEdit, onCreateOpportunity }) => {
  const { data: customer, isLoading } = useCustomer(customerId);
  const { data: opportunities } = useOpportunities(1, 10, { customer_id: customerId });
  const convertProspect = useConvertProspect();
  const deleteCustomer = useDeleteCustomer();

  const handleConvert = async () => {
    if (window.confirm('Convertir ce prospect en client ?')) {
      await convertProspect.mutateAsync(customerId);
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

  if (isLoading) {
    return <PageWrapper title="Chargement..."><div className="azals-loading">Chargement...</div></PageWrapper>;
  }

  if (!customer) {
    return (
      <PageWrapper title="Client non trouvé">
        <Card><p>Ce client n'existe pas.</p><Button onClick={onBack}>Retour</Button></Card>
      </PageWrapper>
    );
  }

  const isProspect = customer.type === 'PROSPECT' || customer.type === 'LEAD';

  return (
    <PageWrapper
      title={customer.name}
      subtitle={customer.legal_name || customer.code}
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={
        <ButtonGroup>
          {isProspect && (
            <Button leftIcon={<CheckCircle2 size={16} />} onClick={handleConvert} isLoading={convertProspect.isPending}>
              Convertir en client
            </Button>
          )}
          <Button variant="secondary" leftIcon={<FileText size={16} />} onClick={handleCreateDevis}>
            Créer devis
          </Button>
          <Button variant="ghost" leftIcon={<Edit size={16} />} onClick={onEdit}>Modifier</Button>
          <Button variant="ghost" leftIcon={<Trash2 size={16} />} onClick={handleDelete}>Supprimer</Button>
        </ButtonGroup>
      }
    >
      <Grid cols={3} gap="md" className="mb-4">
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Type</span>
            <CustomerTypeBadge type={customer.type} />
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">CA Total</span>
            <span className="azals-stat__value">{customer.total_revenue ? formatCurrency(customer.total_revenue) : '-'}</span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Commandes</span>
            <span className="azals-stat__value">{customer.order_count || 0}</span>
          </div>
        </Card>
      </Grid>

      <Grid cols={2} gap="lg">
        <Card title="Contact">
          <dl className="azals-dl">
            {customer.email && <><dt><Mail size={14} /> Email</dt><dd><a href={`mailto:${customer.email}`}>{customer.email}</a></dd></>}
            {customer.phone && <><dt><Phone size={14} /> Téléphone</dt><dd><a href={`tel:${customer.phone}`}>{customer.phone}</a></dd></>}
            {customer.mobile && <><dt><Phone size={14} /> Mobile</dt><dd><a href={`tel:${customer.mobile}`}>{customer.mobile}</a></dd></>}
            {(customer.address_line1 || customer.city) && (
              <>
                <dt><MapPin size={14} /> Adresse</dt>
                <dd>
                  {customer.address_line1 && <div>{customer.address_line1}</div>}
                  {customer.city && <div>{customer.postal_code} {customer.city}</div>}
                </dd>
              </>
            )}
          </dl>
        </Card>

        <Card title="Informations">
          <dl className="azals-dl">
            <dt>Code</dt><dd>{customer.code}</dd>
            {customer.tax_id && <><dt>N° TVA</dt><dd>{customer.tax_id}</dd></>}
            {customer.registration_number && <><dt>SIRET</dt><dd>{customer.registration_number}</dd></>}
            {customer.industry && <><dt>Secteur</dt><dd>{customer.industry}</dd></>}
            {customer.source && <><dt>Source</dt><dd>{customer.source}</dd></>}
          </dl>
        </Card>
      </Grid>

      {opportunities && opportunities.items.length > 0 && (
        <Card title="Opportunités" className="mt-4">
          <ul className="azals-simple-list">
            {opportunities.items.map(o => (
              <li key={o.id}>
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
        </Card>
      )}

      {customer.notes && (
        <Card title="Notes" className="mt-4">
          <p className="text-muted">{customer.notes}</p>
        </Card>
      )}
    </PageWrapper>
  );
};

// ============================================================
// CUSTOMER FORM
// ============================================================

const CustomerFormInternal: React.FC<{
  customerId?: string;
  onBack: () => void;
  onSaved: (id: string) => void;
}> = ({ customerId, onBack, onSaved }) => {
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

const OpportunitiesListInternal: React.FC<{
  onSelectOpportunity: (id: string) => void;
  onBack: () => void;
}> = ({ onSelectOpportunity, onBack }) => {
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
        <CustomersListInternal
          onSelectCustomer={navigateToCustomerDetail}
          onCreateCustomer={() => navigateToCustomerForm()}
          onBack={navigateToDashboard}
        />
      );
    case 'customer-detail':
      return (
        <CustomerDetailInternal
          customerId={navState.customerId!}
          onBack={navigateToCustomers}
          onEdit={() => navigateToCustomerForm(navState.customerId)}
          onCreateOpportunity={() => {}}
        />
      );
    case 'customer-form':
      return (
        <CustomerFormInternal
          customerId={navState.customerId}
          onBack={navState.isNew ? navigateToDashboard : () => navigateToCustomerDetail(navState.customerId!)}
          onSaved={navigateToCustomerDetail}
        />
      );
    case 'opportunities':
      return (
        <OpportunitiesListInternal
          onSelectOpportunity={navigateToOpportunityDetail}
          onBack={navigateToDashboard}
        />
      );
    default:
      return (
        <CRMDashboardInternal
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
