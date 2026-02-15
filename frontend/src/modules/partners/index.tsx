/**
 * AZALSCORE Module - Partenaires (Clients, Fournisseurs, Contacts)
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Users, Building, Contact as ContactIcon,
  User, FileText, Clock, ShoppingCart, Sparkles, Shield
} from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { DynamicForm } from '@ui/forms';
import { Button, Modal } from '@ui/actions';
import {
  BaseViewStandard,
  type TabDefinition,
  type InfoBarItem,
  type SidebarSection,
  type ActionDefinition,
  type SemanticColor
} from '@ui/standards';
import { z } from 'zod';
import type { PaginatedResponse, TableColumn } from '@/types';
import { unwrapApiResponse } from '@/types';
import type { Partner, Client } from './types';
import {
  PARTNER_TYPE_CONFIG, CLIENT_TYPE_CONFIG,
  getPartnerAgeDays, hasContacts, getContactsCount
} from './types';
import { formatCurrency, formatDate } from '@/utils/formatters';
import {
  PartnerInfoTab,
  PartnerContactsTab,
  PartnerTransactionsTab,
  PartnerDocumentsTab,
  PartnerHistoryTab,
  PartnerIATab,
  PartnerRiskTab
} from './components';
import { ArrowLeft } from 'lucide-react';

// Auto-enrichissement (SIRET + Adresse + Analyse de risque)
import { CompanyAutocomplete, AddressAutocomplete, useRiskAnalysis, useInternalScore, ScoreGauge } from '@/modules/enrichment';
import type { EnrichedContactFields, AddressSuggestion } from '@/modules/enrichment';
import { ShieldCheck, ShieldAlert, ShieldX, AlertCircle, Loader2, TrendingUp, TrendingDown, History } from 'lucide-react';

// Legacy Partner interface for list views (backward compatibility)
interface PartnerLegacy {
  id: string;
  type: 'client' | 'supplier' | 'contact';
  code?: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  vat_number?: string;
  is_active: boolean;
  created_at: string;
}

// API Hooks
const usePartners = (type: 'client' | 'supplier' | 'contact', page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['partners', type, page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PartnerLegacy>>(
        `/v3/partners/${type}s?page=${page}&page_size=${pageSize}`
      );
      return response as unknown as PaginatedResponse<PartnerLegacy>;
    },
  });
};

const usePartner = (type: 'client' | 'supplier' | 'contact', id: string | undefined) => {
  return useQuery({
    queryKey: ['partner', type, id],
    queryFn: async () => {
      const response = await api.get<Partner>(`/v3/partners/${type}s/${id}`);
      return response as unknown as Partner;
    },
    enabled: !!id,
  });
};

const useCreatePartner = (type: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<PartnerLegacy>) => {
      const response = await api.post<PartnerLegacy>(`/v3/partners/${type}s`, data);
      return response as unknown as PartnerLegacy;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners', type] });
    },
  });
};

// Partner List Component
interface PartnerListProps {
  type: 'client' | 'supplier' | 'contact';
  title: string;
}

const PartnerList: React.FC<PartnerListProps> = ({ type, title }) => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [showCreate, setShowCreate] = useState(false);

  const { data, isLoading, error, refetch } = usePartners(type, page, pageSize);
  const createPartner = useCreatePartner(type);

  const columns: TableColumn<PartnerLegacy>[] = [
    { id: 'name', header: 'Nom', accessor: 'name', sortable: true },
    { id: 'email', header: 'Email', accessor: 'email' },
    { id: 'phone', header: 'Téléphone', accessor: 'phone' },
    { id: 'city', header: 'Ville', accessor: 'city' },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Actif</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Inactif</span>
        ),
    },
  ];

  const actions = [
    {
      id: 'view',
      label: 'Voir',
      onClick: (row: PartnerLegacy) => navigate(`/partners/${type}s/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      capability: `partners.${type}s.edit`,
      onClick: (row: PartnerLegacy) => navigate(`/partners/${type}s/${row.id}/edit`),
    },
  ];

  const partnerSchema = z.object({
    name: z.string().min(2, 'Nom requis'),
    email: z.string().email('Email invalide').optional().or(z.literal('')),
    phone: z.string().optional(),
    address: z.string().optional(),
    city: z.string().optional(),
    postal_code: z.string().optional(),
    country: z.string().optional(),
  });

  const fields = [
    { name: 'name', label: 'Nom', type: 'text' as const, required: true },
    { name: 'email', label: 'Email', type: 'email' as const },
    { name: 'phone', label: 'Téléphone', type: 'text' as const },
    { name: 'address', label: 'Adresse', type: 'text' as const },
    { name: 'city', label: 'Ville', type: 'text' as const },
    { name: 'postal_code', label: 'Code postal', type: 'text' as const },
    { name: 'country', label: 'Pays', type: 'text' as const },
  ];

  return (
    <PageWrapper
      title={title}
      actions={
        <CapabilityGuard capability={`partners.${type}s.create`}>
          <Button leftIcon={<Plus size={16} />} onClick={() => setShowCreate(true)}>
            Ajouter
          </Button>
        </CapabilityGuard>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          actions={actions}
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
          onRetry={() => refetch()}
        />
      </Card>

      {showCreate && (
        <Modal isOpen onClose={() => setShowCreate(false)} title={`Nouveau ${type}`} size="md">
          <DynamicForm
            fields={fields}
            schema={partnerSchema}
            onSubmit={async (data) => {
              await createPartner.mutateAsync({ ...data, type });
              setShowCreate(false);
            }}
            onCancel={() => setShowCreate(false)}
            isLoading={createPartner.isPending}
          />
        </Modal>
      )}
    </PageWrapper>
  );
};

// Pages
// Clients Page - Liste des clients avec navigation vers formulaire
export const ClientsPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['partners', 'clients', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PartnerLegacy>>(`/v3/partners/clients?page=${page}&page_size=${pageSize}`);
      return response as unknown as PaginatedResponse<PartnerLegacy>;
    },
  });

  const columns: TableColumn<PartnerLegacy>[] = [
    { id: 'code', header: 'Code', accessor: 'code', sortable: true },
    { id: 'name', header: 'Nom', accessor: 'name', sortable: true },
    { id: 'email', header: 'Email', accessor: 'email' },
    { id: 'phone', header: 'Téléphone', accessor: 'phone' },
    { id: 'city', header: 'Ville', accessor: 'city' },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Actif</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Inactif</span>
        ),
    },
  ];

  const actions = [
    {
      id: 'view',
      label: 'Voir',
      onClick: (row: PartnerLegacy) => navigate(`/partners/clients/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      capability: 'partners.clients.edit',
      onClick: (row: PartnerLegacy) => navigate(`/partners/clients/${row.id}/edit`),
    },
  ];

  return (
    <PageWrapper
      title="Clients"
      actions={
        <CapabilityGuard capability="partners.clients.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/partners/clients/new')}>
            Nouveau client
          </Button>
        </CapabilityGuard>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          actions={actions}
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
          onRetry={() => refetch()}
        />
      </Card>
    </PageWrapper>
  );
};

export const SuppliersPage: React.FC = () => <PartnerList type="supplier" title="Fournisseurs" />;

// Contacts Page - Schéma différent des clients/fournisseurs
export const ContactsPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [showCreate, setShowCreate] = useState(false);
  const queryClient = useQueryClient();

  // Récupérer la liste des clients pour le select
  const { data: clientsData, isLoading: loadingClients } = useQuery({
    queryKey: ['partners', 'clients-for-select'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PartnerLegacy>>('/v3/partners/clients?page=1&page_size=100&is_active=true');
      return response as unknown as PaginatedResponse<PartnerLegacy>;
    },
  });

  // Récupérer les contacts
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['partners', 'contacts', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<any>>(`/v3/partners/contacts?page=${page}&page_size=${pageSize}`);
      return response as unknown as PaginatedResponse<any>;
    },
  });

  // Mutation pour créer un contact
  const createContact = useMutation({
    mutationFn: async (contactData: any) => {
      const response = await api.post('/v3/partners/contacts', contactData);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners', 'contacts'] });
      setShowCreate(false);
    },
    onError: (error: any) => {
      console.error('Erreur création contact:', error);
      alert('Erreur lors de la création du contact: ' + (error.response?.data?.detail || error.message));
    },
  });

  const columns: TableColumn<any>[] = [
    {
      id: 'name',
      header: 'Nom',
      accessor: (row: any) => `${row.first_name || ''} ${row.last_name || ''}`.trim() || row.name || '-',
      sortable: true
    },
    { id: 'email', header: 'Email', accessor: 'email' },
    { id: 'phone', header: 'Téléphone', accessor: 'phone' },
    { id: 'job_title', header: 'Fonction', accessor: 'job_title' },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Actif</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Inactif</span>
        ),
    },
  ];

  const actions = [
    {
      id: 'view',
      label: 'Voir',
      onClick: (row: any) => navigate(`/partners/contacts/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      capability: 'partners.contacts.edit',
      onClick: (row: any) => navigate(`/partners/contacts/${row.id}/edit`),
    },
  ];

  const contactSchema = z.object({
    first_name: z.string().min(1, 'Prénom requis'),
    last_name: z.string().min(1, 'Nom requis'),
    customer_id: z.string().uuid('Client requis'),
    email: z.string().email('Email invalide').optional().or(z.literal('')),
    phone: z.string().optional(),
    mobile: z.string().optional(),
    job_title: z.string().optional(),
    department: z.string().optional(),
  });

  const contactFields = [
    {
      name: 'customer_id',
      label: 'Client',
      type: 'select' as const,
      required: true,
      placeholder: 'Sélectionner un client',
      options: (clientsData?.items || []).map((c: PartnerLegacy) => ({ value: c.id, label: c.name }))
    },
    { name: 'first_name', label: 'Prénom', type: 'text' as const, required: true },
    { name: 'last_name', label: 'Nom', type: 'text' as const, required: true },
    { name: 'email', label: 'Email', type: 'email' as const },
    { name: 'phone', label: 'Téléphone', type: 'text' as const },
    { name: 'mobile', label: 'Mobile', type: 'text' as const },
    { name: 'job_title', label: 'Fonction', type: 'text' as const },
    { name: 'department', label: 'Service', type: 'text' as const },
  ];

  return (
    <PageWrapper
      title="Contacts"
      actions={
        <CapabilityGuard capability="partners.contacts.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => setShowCreate(true)}>
            Ajouter
          </Button>
        </CapabilityGuard>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          actions={actions}
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
          onRetry={() => refetch()}
        />
      </Card>

      {showCreate && (
        <Modal isOpen onClose={() => setShowCreate(false)} title="Nouveau contact" size="md">
          {loadingClients ? (
            <div className="azals-loading">
              <p>Chargement des clients...</p>
            </div>
          ) : clientsData?.items?.length === 0 ? (
            <div className="azals-alert azals-alert--warning">
              <p>Aucun client disponible. Veuillez d'abord créer un client.</p>
            </div>
          ) : (
            <DynamicForm
              fields={contactFields}
              schema={contactSchema}
              onSubmit={async (formData) => {
                await createContact.mutateAsync(formData);
              }}
              onCancel={() => setShowCreate(false)}
              isLoading={createContact.isPending}
            />
          )}
        </Modal>
      )}
    </PageWrapper>
  );
};

export const PartnersDashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageWrapper title="Partenaires">
      <Grid cols={3} gap="md">
        <Card
          title="Clients"
          actions={
            <Button variant="ghost" size="sm" onClick={() => navigate('/partners/clients')}>
              Gérer
            </Button>
          }
        >
          <Users size={32} className="azals-text--primary" />
          <p>Gérer vos clients et prospects</p>
        </Card>

        <Card
          title="Fournisseurs"
          actions={
            <Button variant="ghost" size="sm" onClick={() => navigate('/partners/suppliers')}>
              Gérer
            </Button>
          }
        >
          <Building size={32} className="azals-text--primary" />
          <p>Gérer vos fournisseurs</p>
        </Card>

        <Card
          title="Contacts"
          actions={
            <Button variant="ghost" size="sm" onClick={() => navigate('/partners/contacts')}>
              Gérer
            </Button>
          }
        >
          <ContactIcon size={32} className="azals-text--primary" />
          <p>Carnet d'adresses</p>
        </Card>
      </Grid>
    </PageWrapper>
  );
};

/**
 * PartnerDetailView - Vue detail standardisee BaseViewStandard
 */
interface PartnerDetailViewProps {
  partnerType: 'client' | 'supplier' | 'contact';
}

const PartnerDetailView: React.FC<PartnerDetailViewProps> = ({ partnerType }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: partner, isLoading, error, refetch } = usePartner(partnerType, id);

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">Chargement du partenaire...</div>
      </PageWrapper>
    );
  }

  if (error || !partner) {
    return (
      <PageWrapper title="Erreur">
        <div className="azals-alert azals-alert--danger">
          Partenaire introuvable
        </div>
      </PageWrapper>
    );
  }

  // Configuration des onglets
  const tabs: TabDefinition<Partner>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <User size={16} />,
      component: PartnerInfoTab
    },
    {
      id: 'contacts',
      label: 'Contacts',
      icon: <Users size={16} />,
      badge: getContactsCount(partner),
      component: PartnerContactsTab
    },
    {
      id: 'transactions',
      label: 'Transactions',
      icon: <ShoppingCart size={16} />,
      component: PartnerTransactionsTab
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={16} />,
      badge: partner.documents?.length,
      component: PartnerDocumentsTab
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <Clock size={16} />,
      component: PartnerHistoryTab
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: PartnerIATab
    },
    {
      id: 'risk',
      label: 'Risque',
      icon: <Shield size={16} />,
      component: PartnerRiskTab
    }
  ];

  // Barre d'info KPIs
  const typeConfig = PARTNER_TYPE_CONFIG[partner.type];
  const clientTypeConfig = partner.type === 'client' && (partner as Client).client_type
    ? CLIENT_TYPE_CONFIG[(partner as Client).client_type]
    : null;

  const infoBarItems: InfoBarItem[] = [
    {
      id: 'type',
      label: 'Type',
      value: typeConfig?.label || partner.type,
      valueColor: (typeConfig?.color || 'gray') as SemanticColor
    },
    {
      id: 'status',
      label: 'Statut',
      value: partner.is_active ? 'Actif' : 'Inactif',
      valueColor: partner.is_active ? 'green' : 'gray'
    }
  ];

  // Ajouter des KPIs specifiques selon le type
  if (partner.type === 'client') {
    const client = partner as Client;
    if (clientTypeConfig) {
      infoBarItems.push({
        id: 'client_type',
        label: 'Categorie',
        value: clientTypeConfig.label,
        valueColor: (clientTypeConfig.color || 'gray') as SemanticColor
      });
    }
    if (client.total_orders !== undefined) {
      infoBarItems.push({
        id: 'orders',
        label: 'Commandes',
        value: String(client.total_orders),
        valueColor: 'blue'
      });
    }
    if (client.total_revenue !== undefined) {
      infoBarItems.push({
        id: 'revenue',
        label: 'CA Total',
        value: formatCurrency(client.total_revenue),
        valueColor: 'green'
      });
    }
  }

  // Ajouter anciennete
  const ageDays = getPartnerAgeDays(partner);
  infoBarItems.push({
    id: 'age',
    label: 'Anciennete',
    value: ageDays > 365 ? `${Math.floor(ageDays / 365)} an(s)` : `${ageDays}j`,
    valueColor: ageDays > 365 ? 'green' : 'gray'
  });

  // Sidebar
  const sidebarSections: SidebarSection[] = [
    {
      id: 'summary',
      title: 'Resume',
      items: [
        { id: 'code', label: 'Code', value: partner.code || '-' },
        { id: 'email', label: 'Email', value: partner.email || '-' },
        { id: 'phone', label: 'Telephone', value: partner.phone || partner.mobile || '-' },
        { id: 'city', label: 'Ville', value: partner.city || '-' }
      ]
    }
  ];

  // Section financiere pour clients
  if (partner.type === 'client') {
    const client = partner as Client;
    sidebarSections.push({
      id: 'financial',
      title: 'Donnees financieres',
      items: [
        { id: 'revenue', label: 'CA Total', value: formatCurrency(client.total_revenue || 0), highlight: true },
        { id: 'orders', label: 'Commandes', value: String(client.total_orders || 0) },
        { id: 'outstanding', label: 'Encours', value: formatCurrency(client.stats?.total_outstanding || 0) }
      ]
    });
  }

  // Actions header
  const headerActions: ActionDefinition[] = [
    {
      id: 'edit',
      label: 'Modifier',
      variant: 'secondary',
      capability: `partners.${partnerType}s.edit`,
      onClick: () => navigate(`/partners/${partnerType}s/${id}/edit`)
    }
  ];

  // Statut du partenaire
  const status = {
    label: partner.is_active ? 'Actif' : 'Inactif',
    color: partner.is_active ? 'green' as const : 'gray' as const
  };

  return (
    <BaseViewStandard<Partner>
      title={partner.name}
      subtitle={partner.code ? `Code: ${partner.code}` : undefined}
      status={status}
      data={partner}
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
// CLIENT FORM PAGE - Formulaire de création/édition client avec enrichissement
// ============================================================================

interface ClientFormData {
  code: string;
  name: string;
  type: string;
  email: string;
  phone: string;
  address_line1: string;
  city: string;
  postal_code: string;
  country_code: string;
  tax_id: string;
  notes: string;
}

const useClient = (id: string) => {
  return useQuery({
    queryKey: ['partners', 'clients', id],
    queryFn: async () => {
      const response = await api.get<Client>(`/v3/partners/clients/${id}`);
      return unwrapApiResponse<Client>(response);
    },
    enabled: !!id && id !== 'new',
  });
};

const useCreateClient = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<ClientFormData>) => {
      const response = await api.post<Client>('/v3/partners/clients', data);
      return unwrapApiResponse<Client>(response);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners', 'clients'] });
    },
  });
};

const useUpdateClient = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<ClientFormData> }) => {
      const response = await api.put<Client>(`/v3/partners/clients/${id}`, data);
      return unwrapApiResponse<Client>(response);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners', 'clients'] });
    },
  });
};

export const ClientFormPage: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isNew = !id || id === 'new';

  const { data: client, isLoading } = useClient(id || '');
  const createMutation = useCreateClient();
  const updateMutation = useUpdateClient();

  // Hook pour l'analyse de risque externe (SIRET)
  const {
    analysis: riskAnalysis,
    isLoading: riskLoading,
    error: riskError,
    analyze: analyzeRisk,
    reset: resetRisk
  } = useRiskAnalysis();

  // Hook pour le scoring interne (historique client)
  const {
    score: internalScore,
    isLoading: internalLoading,
    error: internalError,
    analyze: analyzeInternal,
    reset: resetInternal
  } = useInternalScore();

  const [form, setForm] = useState<ClientFormData>({
    code: '',
    name: '',
    type: 'CUSTOMER',
    email: '',
    phone: '',
    address_line1: '',
    city: '',
    postal_code: '',
    country_code: 'FR',
    tax_id: '',
    notes: '',
  });

  React.useEffect(() => {
    if (client) {
      setForm({
        code: client.code || '',
        name: client.name || '',
        type: client.client_type || 'CUSTOMER',
        email: client.email || '',
        phone: client.phone || '',
        address_line1: client.address_line1 || client.address || '',
        city: client.city || '',
        postal_code: client.postal_code || '',
        country_code: client.country_code || 'FR',
        tax_id: client.tax_id || '',
        notes: client.notes || '',
      });
    }
  }, [client]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (isNew) {
        const result = await createMutation.mutateAsync(form);
        navigate(`/partners/clients/${result.id}`);
      } else {
        await updateMutation.mutateAsync({ id: id!, data: form });
        navigate(`/partners/clients/${id}`);
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
    }
  };

  // Handler pour l'enrichissement depuis recherche par nom
  const handleCompanySelect = (fields: EnrichedContactFields) => {
    setForm((prev) => ({
      ...prev,
      name: fields.name || fields.company_name || prev.name,
      address_line1: fields.address_line1 || fields.address || prev.address_line1,
      city: fields.city || prev.city,
      postal_code: fields.postal_code || prev.postal_code,
      tax_id: fields.siret || fields.siren || prev.tax_id,
    }));
  };

  // Handler pour l'autocomplete adresse
  const handleAddressSelect = (suggestion: AddressSuggestion) => {
    setForm((prev) => ({
      ...prev,
      address_line1: suggestion.address_line1 || suggestion.label.split(',')[0] || prev.address_line1,
      postal_code: suggestion.postal_code || prev.postal_code,
      city: suggestion.city || prev.city,
    }));
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  if (!isNew && isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={isNew ? 'Nouveau client' : `Modifier ${client?.name}`}
      actions={
        <Button variant="ghost" leftIcon={<ArrowLeft size={16} />} onClick={() => navigate(-1)}>
          Retour
        </Button>
      }
    >
      <form onSubmit={handleSubmit}>
        <Card title="Informations générales">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <label className="azals-field__label">Code (auto-généré)</label>
              <input
                type="text"
                className="azals-input"
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value })}
                maxLength={50}
                placeholder="Généré automatiquement"
                disabled={!form.code}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Type</label>
              <select
                className="azals-input"
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
              >
                <option value="PROSPECT">Prospect</option>
                <option value="LEAD">Lead</option>
                <option value="CUSTOMER">Client</option>
                <option value="VIP">VIP</option>
                <option value="PARTNER">Partenaire</option>
              </select>
            </div>
            <div className="azals-field" style={{ gridColumn: 'span 2' }}>
              <label className="azals-field__label">Nom / Raison sociale * (autocomplete entreprise)</label>
              <CompanyAutocomplete
                value={form.name}
                onChange={(value: string) => setForm({ ...form, name: value })}
                onSelect={handleCompanySelect}
                placeholder="Tapez le nom d'une entreprise..."
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Email</label>
              <input
                type="email"
                className="azals-input"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Téléphone</label>
              <input
                type="text"
                className="azals-input"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Adresse" className="mt-4">
          <Grid cols={2} gap="md">
            <div className="azals-field" style={{ gridColumn: 'span 2' }}>
              <label className="azals-field__label">Adresse (autocomplete)</label>
              <AddressAutocomplete
                value={form.address_line1}
                onChange={(value: string) => setForm({ ...form, address_line1: value })}
                onSelect={handleAddressSelect}
                placeholder="Tapez une adresse..."
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Code postal</label>
              <input
                type="text"
                className="azals-input"
                value={form.postal_code}
                onChange={(e) => setForm({ ...form, postal_code: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Ville</label>
              <input
                type="text"
                className="azals-input"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Pays</label>
              <input
                type="text"
                className="azals-input"
                value={form.country_code}
                onChange={(e) => setForm({ ...form, country_code: e.target.value })}
              />
            </div>
            <div className="azals-field">
              <label className="azals-field__label">N° SIRET / TVA</label>
              <input
                type="text"
                className="azals-input"
                value={form.tax_id}
                onChange={(e) => setForm({ ...form, tax_id: e.target.value })}
              />
            </div>
          </Grid>
        </Card>

        <Card title="Notes" className="mt-4">
          <textarea
            className="azals-input w-full"
            rows={4}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            placeholder="Notes sur ce client..."
          />
        </Card>

        {/* Analyse de Risque - Section combinée */}
        <Card title="Analyse de Risque" className="mt-4" icon={<Shield size={18} />}>
          <Grid cols={2} gap="md">
            {/* Colonne 1: Risque Externe (SIRET) */}
            <div className="border-r pr-4">
              <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <Shield size={16} />
                Risque Entreprise
                <span className="text-xs text-gray-400">(données publiques)</span>
              </h4>

              {!form.tax_id || form.tax_id.length < 9 ? (
                <div className="flex items-center gap-2 text-gray-400 text-sm py-2">
                  <AlertCircle size={16} />
                  <span>SIRET requis</span>
                </div>
              ) : riskLoading ? (
                <div className="flex items-center gap-2 text-blue-600 py-2">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-sm">Analyse...</span>
                </div>
              ) : riskAnalysis ? (
                <div>
                  <div className="flex items-center gap-4 mb-3">
                    <ScoreGauge score={riskAnalysis.score} size="sm" />
                    <div>
                      <div className="flex items-center gap-1">
                        {riskAnalysis.level === 'low' && <ShieldCheck className="text-green-500" size={16} />}
                        {riskAnalysis.level === 'medium' && <Shield className="text-yellow-500" size={16} />}
                        {riskAnalysis.level === 'elevated' && <ShieldAlert className="text-orange-500" size={16} />}
                        {riskAnalysis.level === 'high' && <ShieldX className="text-red-500" size={16} />}
                        <span className="font-medium">{riskAnalysis.level_label}</span>
                      </div>
                      {riskAnalysis.cotation_bdf && (
                        <div className="text-xs text-gray-500">BDF: {riskAnalysis.cotation_bdf}</div>
                      )}
                    </div>
                  </div>

                  {riskAnalysis.alerts && riskAnalysis.alerts.length > 0 && (
                    <div className="text-xs text-red-600 mb-2">
                      {riskAnalysis.alerts.slice(0, 2).map((a, i) => (
                        <div key={i} className="flex items-center gap-1">
                          <AlertCircle size={12} />
                          {a}
                        </div>
                      ))}
                    </div>
                  )}

                  <Button variant="ghost" size="sm" onClick={() => { resetRisk(); analyzeRisk(form.tax_id); }}>
                    Actualiser
                  </Button>
                </div>
              ) : riskError ? (
                <div className="text-sm text-red-500">
                  {riskError}
                  <Button variant="ghost" size="sm" onClick={() => analyzeRisk(form.tax_id)}>Réessayer</Button>
                </div>
              ) : (
                <Button variant="secondary" size="sm" leftIcon={<Shield size={14} />} onClick={() => analyzeRisk(form.tax_id)}>
                  Analyser
                </Button>
              )}
            </div>

            {/* Colonne 2: Scoring Interne (Historique) */}
            <div className="pl-4">
              <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                <History size={16} />
                Score Interne
                <span className="text-xs text-gray-400">(historique client)</span>
              </h4>

              {isNew ? (
                <div className="flex items-center gap-2 text-gray-400 text-sm py-2">
                  <AlertCircle size={16} />
                  <span>Nouveau client - pas d'historique</span>
                </div>
              ) : internalLoading ? (
                <div className="flex items-center gap-2 text-blue-600 py-2">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-sm">Calcul...</span>
                </div>
              ) : internalScore ? (
                <div>
                  <div className="flex items-center gap-4 mb-3">
                    <ScoreGauge score={internalScore.score} size="sm" />
                    <div>
                      <div className="flex items-center gap-1">
                        {internalScore.level === 'low' && <TrendingUp className="text-green-500" size={16} />}
                        {internalScore.level === 'medium' && <History className="text-yellow-500" size={16} />}
                        {internalScore.level === 'elevated' && <TrendingDown className="text-orange-500" size={16} />}
                        {internalScore.level === 'high' && <TrendingDown className="text-red-500" size={16} />}
                        <span className="font-medium">{internalScore.level_label}</span>
                      </div>
                      {internalScore.metrics && (
                        <div className="text-xs text-gray-500">
                          {internalScore.metrics.total_invoices} factures | {internalScore.metrics.overdue_invoices} en retard
                        </div>
                      )}
                    </div>
                  </div>

                  {internalScore.alerts && internalScore.alerts.length > 0 && (
                    <div className="text-xs text-red-600 mb-2">
                      {internalScore.alerts.slice(0, 2).map((a, i) => (
                        <div key={i} className="flex items-center gap-1">
                          <AlertCircle size={12} />
                          {a}
                        </div>
                      ))}
                    </div>
                  )}

                  {internalScore.recommendation && (
                    <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded mb-2">
                      {internalScore.recommendation}
                    </div>
                  )}

                  <Button variant="ghost" size="sm" onClick={() => { resetInternal(); analyzeInternal(id!); }}>
                    Actualiser
                  </Button>
                </div>
              ) : internalError ? (
                <div className="text-sm text-red-500">
                  {internalError}
                  <Button variant="ghost" size="sm" onClick={() => analyzeInternal(id!)}>Réessayer</Button>
                </div>
              ) : (
                <Button variant="secondary" size="sm" leftIcon={<History size={14} />} onClick={() => analyzeInternal(id!)}>
                  Calculer le score
                </Button>
              )}
            </div>
          </Grid>
        </Card>

        <div className="flex justify-end gap-3 mt-6">
          <Button variant="ghost" onClick={() => navigate(-1)} disabled={isSubmitting}>
            Annuler
          </Button>
          <Button type="submit" disabled={isSubmitting || !form.name}>
            {isSubmitting ? 'Enregistrement...' : isNew ? 'Créer le client' : 'Enregistrer'}
          </Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// Composants detail par type
const ClientDetailView: React.FC = () => <PartnerDetailView partnerType="client" />;
const SupplierDetailView: React.FC = () => <PartnerDetailView partnerType="supplier" />;
const ContactDetailView: React.FC = () => <PartnerDetailView partnerType="contact" />;

// Router
export const PartnersRoutes: React.FC = () => (
  <Routes>
    <Route index element={<PartnersDashboard />} />
    <Route path="clients" element={<ClientsPage />} />
    <Route path="clients/new" element={<ClientFormPage />} />
    <Route path="clients/:id" element={<ClientDetailView />} />
    <Route path="clients/:id/edit" element={<ClientFormPage />} />
    <Route path="suppliers" element={<SuppliersPage />} />
    <Route path="suppliers/:id" element={<SupplierDetailView />} />
    <Route path="contacts" element={<ContactsPage />} />
    <Route path="contacts/:id" element={<ContactDetailView />} />
  </Routes>
);

export default PartnersRoutes;
