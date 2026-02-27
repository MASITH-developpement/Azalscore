/**
 * AZALSCORE Module - Partners - ContactsPage
 * Page liste des contacts avec formulaire de création
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { z } from 'zod';
import { CapabilityGuard } from '@core/capabilities';
import { Button, Modal } from '@ui/actions';
import { DynamicForm } from '@ui/forms';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import type { TableColumn, ApiMutationError } from '@/types';
import { useContacts, useClientsForSelect, useCreateContact } from '../hooks';
import type { Contact, PartnerLegacy } from '../types';

export const ContactsPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [showCreate, setShowCreate] = useState(false);

  // Récupérer la liste des clients pour le select
  const { data: clientsData, isLoading: loadingClients } = useClientsForSelect();

  // Récupérer les contacts
  const { data, isLoading, error, refetch } = useContacts(page, pageSize);

  // Mutation pour créer un contact
  const createContact = useCreateContact();

  const handleCreateError = (error: ApiMutationError) => {
    console.error('Erreur création contact:', error);
    alert('Erreur lors de la création du contact: ' + (error.response?.data?.detail || error.message));
  };

  const columns: TableColumn<Contact>[] = [
    {
      id: 'name',
      header: 'Nom',
      accessor: (row: Contact) => `${row.first_name || ''} ${row.last_name || ''}`.trim() || '-',
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
      onClick: (row: Contact) => navigate(`/partners/contacts/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      capability: 'partners.contacts.edit',
      onClick: (row: Contact) => navigate(`/partners/contacts/${row.id}/edit`),
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
                try {
                  await createContact.mutateAsync(formData);
                  setShowCreate(false);
                } catch (err) {
                  handleCreateError(err as ApiMutationError);
                }
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

export default ContactsPage;
