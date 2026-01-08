/**
 * AZALSCORE Module - Partenaires (Clients, Fournisseurs, Contacts)
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Users, Building, Contact } from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { DynamicForm } from '@ui/forms';
import { Button, Modal } from '@ui/actions';
import { z } from 'zod';
import type { PaginatedResponse, TableColumn } from '@/types';

// Types
interface Partner {
  id: string;
  type: 'client' | 'supplier' | 'contact';
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
      const response = await api.get<PaginatedResponse<Partner>>(
        `/v1/partners/${type}s?page=${page}&page_size=${pageSize}`
      );
      return response.data;
    },
  });
};

const useCreatePartner = (type: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Partner>) => {
      const response = await api.post<Partner>(`/v1/partners/${type}s`, data);
      return response.data;
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

  const { data, isLoading, refetch } = usePartners(type, page, pageSize);
  const createPartner = useCreatePartner(type);

  const columns: TableColumn<Partner>[] = [
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
      onClick: (row: Partner) => navigate(`/partners/${type}s/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      capability: `partners.${type}s.edit`,
      onClick: (row: Partner) => navigate(`/partners/${type}s/${row.id}/edit`),
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
export const ClientsPage: React.FC = () => <PartnerList type="client" title="Clients" />;
export const SuppliersPage: React.FC = () => <PartnerList type="supplier" title="Fournisseurs" />;

// Contacts Page - Schéma différent des clients/fournisseurs
export const ContactsPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [showCreate, setShowCreate] = useState(false);
  const queryClient = useQueryClient();

  // Récupérer la liste des clients pour le select
  const { data: clientsData } = useQuery({
    queryKey: ['partners', 'clients-for-select'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Partner>>('/v1/partners/clients?page=1&page_size=100');
      return response.data;
    },
  });

  // Récupérer les contacts
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['partners', 'contacts', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<any>>(`/v1/partners/contacts?page=${page}&page_size=${pageSize}`);
      return response.data;
    },
  });

  // Mutation pour créer un contact
  const createContact = useMutation({
    mutationFn: async (contactData: any) => {
      const response = await api.post('/v1/partners/contacts', contactData);
      return response.data;
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
      options: (clientsData?.items || []).map((c: Partner) => ({ value: c.id, label: c.name }))
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
        />
      </Card>

      {showCreate && (
        <Modal isOpen onClose={() => setShowCreate(false)} title="Nouveau contact" size="md">
          <DynamicForm
            fields={contactFields}
            schema={contactSchema}
            onSubmit={async (formData) => {
              await createContact.mutateAsync(formData);
            }}
            onCancel={() => setShowCreate(false)}
            isLoading={createContact.isPending}
          />
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
          <Contact size={32} className="azals-text--primary" />
          <p>Carnet d'adresses</p>
        </Card>
      </Grid>
    </PageWrapper>
  );
};

// Router
export const PartnersRoutes: React.FC = () => (
  <Routes>
    <Route index element={<PartnersDashboard />} />
    <Route path="clients" element={<ClientsPage />} />
    <Route path="suppliers" element={<SuppliersPage />} />
    <Route path="contacts" element={<ContactsPage />} />
  </Routes>
);

export default PartnersRoutes;
