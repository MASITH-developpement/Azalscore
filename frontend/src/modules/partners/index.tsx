/**
 * AZALSCORE Module - Partenaires (Clients, Fournisseurs, Contacts)
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Users, Building, Contact as ContactIcon,
  User, FileText, Clock, ShoppingCart, Sparkles
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
  PartnerIATab
} from './components';

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
        `/v1/partners/${type}s?page=${page}&page_size=${pageSize}`
      );
      return response as unknown as PaginatedResponse<PartnerLegacy>;
    },
  });
};

const usePartner = (type: 'client' | 'supplier' | 'contact', id: string | undefined) => {
  return useQuery({
    queryKey: ['partner', type, id],
    queryFn: async () => {
      const response = await api.get<Partner>(`/v1/partners/${type}s/${id}`);
      return response as unknown as Partner;
    },
    enabled: !!id,
  });
};

const useCreatePartner = (type: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<PartnerLegacy>) => {
      const response = await api.post<PartnerLegacy>(`/v1/partners/${type}s`, data);
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
// Clients Page - Schéma spécifique pour les clients
export const ClientsPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [showCreate, setShowCreate] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['partners', 'clients', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PartnerLegacy>>(`/v1/partners/clients?page=${page}&page_size=${pageSize}`);
      // api.get retourne déjà response.data, pas besoin de .data
      return response as unknown as PaginatedResponse<PartnerLegacy>;
    },
  });

  const createClient = useMutation({
    mutationFn: async (clientData: any) => {
      const response = await api.post('/v1/partners/clients', clientData);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['partners', 'clients'] });
      setShowCreate(false);
    },
    onError: (error: any) => {
      console.error('Erreur création client:', error);
      alert('Erreur lors de la création du client: ' + (error.response?.data?.detail || error.message));
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

  // Le code client est auto-généré par le backend (CLI001, CLI002, etc.)
  const clientSchema = z.object({
    name: z.string().min(2, 'Nom requis').max(255),
    type: z.enum(['PROSPECT', 'LEAD', 'CUSTOMER', 'VIP', 'PARTNER', 'CHURNED']).default('CUSTOMER'),
    email: z.string().email('Email invalide').optional().or(z.literal('')),
    phone: z.string().optional(),
    address_line1: z.string().optional(),
    city: z.string().optional(),
    postal_code: z.string().optional(),
    country_code: z.string().default('FR'),
    tax_id: z.string().optional(),
  });

  const fields = [
    { name: 'name', label: 'Nom / Raison sociale', type: 'text' as const, required: true },
    {
      name: 'type',
      label: 'Type',
      type: 'select' as const,
      options: [
        { value: 'PROSPECT', label: 'Prospect' },
        { value: 'LEAD', label: 'Lead' },
        { value: 'CUSTOMER', label: 'Client' },
        { value: 'VIP', label: 'VIP' },
        { value: 'PARTNER', label: 'Partenaire' },
      ],
      defaultValue: 'CUSTOMER'
    },
    { name: 'email', label: 'Email', type: 'email' as const },
    { name: 'phone', label: 'Téléphone', type: 'text' as const },
    { name: 'address_line1', label: 'Adresse', type: 'text' as const },
    { name: 'city', label: 'Ville', type: 'text' as const },
    { name: 'postal_code', label: 'Code postal', type: 'text' as const },
    { name: 'country_code', label: 'Pays', type: 'text' as const, defaultValue: 'FR' },
    { name: 'tax_id', label: 'N° TVA', type: 'text' as const },
  ];

  return (
    <PageWrapper
      title="Clients"
      actions={
        <CapabilityGuard capability="partners.clients.create">
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
        <Modal isOpen onClose={() => setShowCreate(false)} title="Nouveau client" size="md">
          <DynamicForm
            fields={fields}
            schema={clientSchema}
            defaultValues={{ type: 'CUSTOMER', country_code: 'FR' }}
            onSubmit={async (data) => {
              await createClient.mutateAsync(data);
            }}
            onCancel={() => setShowCreate(false)}
            isLoading={createClient.isPending}
          />
        </Modal>
      )}
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
      const response = await api.get<PaginatedResponse<PartnerLegacy>>('/v1/partners/clients?page=1&page_size=100&is_active=true');
      return response as unknown as PaginatedResponse<PartnerLegacy>;
    },
  });

  // Récupérer les contacts
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['partners', 'contacts', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<any>>(`/v1/partners/contacts?page=${page}&page_size=${pageSize}`);
      return response as unknown as PaginatedResponse<any>;
    },
  });

  // Mutation pour créer un contact
  const createContact = useMutation({
    mutationFn: async (contactData: any) => {
      const response = await api.post('/v1/partners/contacts', contactData);
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
                console.log('Contact form data:', formData);
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

// Composants detail par type
const ClientDetailView: React.FC = () => <PartnerDetailView partnerType="client" />;
const SupplierDetailView: React.FC = () => <PartnerDetailView partnerType="supplier" />;
const ContactDetailView: React.FC = () => <PartnerDetailView partnerType="contact" />;

// Router
export const PartnersRoutes: React.FC = () => (
  <Routes>
    <Route index element={<PartnersDashboard />} />
    <Route path="clients" element={<ClientsPage />} />
    <Route path="clients/:id" element={<ClientDetailView />} />
    <Route path="suppliers" element={<SuppliersPage />} />
    <Route path="suppliers/:id" element={<SupplierDetailView />} />
    <Route path="contacts" element={<ContactsPage />} />
    <Route path="contacts/:id" element={<ContactDetailView />} />
  </Routes>
);

export default PartnersRoutes;
