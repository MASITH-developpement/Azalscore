/**
 * AZALSCORE Module - Facturation
 * Devis, Factures, Avoirs
 * Données fournies par API - AUCUNE logique métier
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, FileText, Send, Download, Eye, Edit, Trash2 } from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { DynamicForm } from '@ui/forms';
import { Button, ButtonGroup, Modal, ConfirmDialog } from '@ui/actions';
import { SeverityBadge } from '@ui/dashboards';
import { z } from 'zod';
import type { PaginatedResponse, TableColumn, TableAction } from '@/types';

// ============================================================
// TYPES
// ============================================================

interface Invoice {
  id: string;
  number: string;
  type: 'quote' | 'invoice' | 'credit';
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  client_id: string;
  client_name: string;
  date: string;
  due_date?: string;
  total_ht: number;
  total_ttc: number;
  currency: string;
  created_at: string;
}

interface InvoiceDetail extends Invoice {
  lines: InvoiceLine[];
  notes?: string;
  payment_terms?: string;
}

interface InvoiceLine {
  id: string;
  description: string;
  quantity: number;
  unit_price: number;
  vat_rate: number;
  total_ht: number;
}

interface Client {
  id: string;
  name: string;
}

// ============================================================
// API HOOKS
// ============================================================

const useInvoices = (type: 'quote' | 'invoice' | 'credit', page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['invoicing', type, page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Invoice>>(
        `/v1/invoicing/${type}s?page=${page}&page_size=${pageSize}`
      );
      return response.data;
    },
  });
};

const useInvoiceDetail = (type: string, id: string) => {
  return useQuery({
    queryKey: ['invoicing', type, id],
    queryFn: async () => {
      const response = await api.get<InvoiceDetail>(`/v1/invoicing/${type}s/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

const useClients = () => {
  return useQuery({
    queryKey: ['clients', 'list'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Client>>('/v1/partners/clients?page_size=1000');
      return response.data.items;
    },
  });
};

const useCreateInvoice = (type: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<InvoiceDetail>) => {
      const response = await api.post<Invoice>(`/v1/invoicing/${type}s`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoicing', type] });
    },
  });
};

const useUpdateInvoice = (type: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<InvoiceDetail> }) => {
      const response = await api.put<Invoice>(`/v1/invoicing/${type}s/${id}`, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['invoicing', type] });
      queryClient.invalidateQueries({ queryKey: ['invoicing', type, variables.id] });
    },
  });
};

const useDeleteInvoice = (type: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/v1/invoicing/${type}s/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoicing', type] });
    },
  });
};

const useSendInvoice = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ type, id }: { type: string; id: string }) => {
      await api.post(`/v1/invoicing/${type}s/${id}/send`);
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['invoicing', variables.type] });
    },
  });
};

// ============================================================
// STATUS HELPERS
// ============================================================

const STATUS_LABELS: Record<string, string> = {
  draft: 'Brouillon',
  sent: 'Envoyé',
  paid: 'Payé',
  overdue: 'En retard',
  cancelled: 'Annulé',
};

const STATUS_COLORS: Record<string, 'gray' | 'blue' | 'green' | 'red' | 'orange'> = {
  draft: 'gray',
  sent: 'blue',
  paid: 'green',
  overdue: 'red',
  cancelled: 'orange',
};

const TYPE_LABELS: Record<string, string> = {
  quote: 'Devis',
  invoice: 'Facture',
  credit: 'Avoir',
};

// ============================================================
// INVOICE LIST
// ============================================================

interface InvoiceListProps {
  type: 'quote' | 'invoice' | 'credit';
}

const InvoiceList: React.FC<InvoiceListProps> = ({ type }) => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const { data, isLoading, refetch } = useInvoices(type, page, pageSize);
  const deleteInvoice = useDeleteInvoice(type);
  const sendInvoice = useSendInvoice();

  const columns: TableColumn<Invoice>[] = [
    {
      id: 'number',
      header: 'Numéro',
      accessor: 'number',
      sortable: true,
    },
    {
      id: 'client_name',
      header: 'Client',
      accessor: 'client_name',
      sortable: true,
    },
    {
      id: 'date',
      header: 'Date',
      accessor: 'date',
      sortable: true,
      render: (value) => new Date(value as string).toLocaleDateString('fr-FR'),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => (
        <span className={`azals-badge azals-badge--${STATUS_COLORS[value as string]}`}>
          {STATUS_LABELS[value as string]}
        </span>
      ),
    },
    {
      id: 'total_ttc',
      header: 'Total TTC',
      accessor: 'total_ttc',
      align: 'right',
      render: (value, row) =>
        new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(
          value as number
        ),
    },
  ];

  const actions: TableAction<Invoice>[] = [
    {
      id: 'view',
      label: 'Voir',
      icon: 'eye',
      onClick: (row) => navigate(`/${type}s/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      icon: 'edit',
      capability: `invoicing.${type}s.edit`,
      onClick: (row) => navigate(`/${type}s/${row.id}/edit`),
      isHidden: (row) => row.status !== 'draft',
    },
    {
      id: 'send',
      label: 'Envoyer',
      icon: 'send',
      capability: `invoicing.${type}s.send`,
      onClick: (row) => sendInvoice.mutate({ type, id: row.id }),
      isHidden: (row) => row.status !== 'draft',
    },
    {
      id: 'download',
      label: 'Télécharger PDF',
      icon: 'download',
      onClick: (row) => window.open(`/api/v1/invoicing/${type}s/${row.id}/pdf`, '_blank'),
    },
    {
      id: 'delete',
      label: 'Supprimer',
      icon: 'trash',
      variant: 'danger',
      capability: `invoicing.${type}s.delete`,
      onClick: (row) => setDeleteId(row.id),
      isHidden: (row) => row.status !== 'draft',
    },
  ];

  return (
    <PageWrapper
      title={TYPE_LABELS[type] + 's'}
      actions={
        <CapabilityGuard capability={`invoicing.${type}s.create`}>
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate(`/${type}s/new`)}>
            Nouveau {TYPE_LABELS[type].toLowerCase()}
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
          emptyMessage={`Aucun ${TYPE_LABELS[type].toLowerCase()}`}
        />
      </Card>

      {deleteId && (
        <ConfirmDialog
          title="Confirmer la suppression"
          message={`Êtes-vous sûr de vouloir supprimer ce ${TYPE_LABELS[type].toLowerCase()} ?`}
          variant="danger"
          onConfirm={() => {
            deleteInvoice.mutate(deleteId);
            setDeleteId(null);
          }}
          onCancel={() => setDeleteId(null)}
          isLoading={deleteInvoice.isPending}
        />
      )}
    </PageWrapper>
  );
};

// ============================================================
// INVOICE FORM
// ============================================================

const invoiceSchema = z.object({
  client_id: z.string().min(1, 'Client requis'),
  date: z.string().min(1, 'Date requise'),
  due_date: z.string().optional(),
  notes: z.string().optional(),
});

interface InvoiceFormProps {
  type: 'quote' | 'invoice' | 'credit';
}

const InvoiceForm: React.FC<InvoiceFormProps> = ({ type }) => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id && id !== 'new';

  const { data: clients } = useClients();
  const { data: invoice } = useInvoiceDetail(type, id || '');
  const createInvoice = useCreateInvoice(type);
  const updateInvoice = useUpdateInvoice(type);

  const fields = [
    {
      name: 'client_id',
      label: 'Client',
      type: 'select' as const,
      required: true,
      options: clients?.map((c) => ({ value: c.id, label: c.name })) || [],
    },
    {
      name: 'date',
      label: 'Date',
      type: 'date' as const,
      required: true,
    },
    {
      name: 'due_date',
      label: 'Date d\'échéance',
      type: 'date' as const,
    },
    {
      name: 'notes',
      label: 'Notes',
      type: 'textarea' as const,
    },
  ];

  const handleSubmit = async (data: z.infer<typeof invoiceSchema>) => {
    if (isEdit) {
      await updateInvoice.mutateAsync({ id: id!, data });
    } else {
      await createInvoice.mutateAsync(data);
    }
    navigate(`/${type}s`);
  };

  return (
    <PageWrapper title={isEdit ? `Modifier ${TYPE_LABELS[type]}` : `Nouveau ${TYPE_LABELS[type]}`}>
      <Card>
        <DynamicForm
          fields={fields}
          schema={invoiceSchema}
          defaultValues={invoice}
          onSubmit={handleSubmit}
          onCancel={() => navigate(`/${type}s`)}
          isLoading={createInvoice.isPending || updateInvoice.isPending}
          submitLabel={isEdit ? 'Enregistrer' : 'Créer'}
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// INVOICE DETAIL
// ============================================================

interface InvoiceDetailPageProps {
  type: 'quote' | 'invoice' | 'credit';
}

const InvoiceDetailPage: React.FC<InvoiceDetailPageProps> = ({ type }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: invoice, isLoading } = useInvoiceDetail(type, id || '');

  if (isLoading) {
    return (
      <PageWrapper title={TYPE_LABELS[type]}>
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (!invoice) {
    return (
      <PageWrapper title={TYPE_LABELS[type]}>
        <Card>
          <p>Document non trouvé</p>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={`${TYPE_LABELS[type]} ${invoice.number}`}
      actions={
        <ButtonGroup>
          <Button
            variant="ghost"
            leftIcon={<Download size={16} />}
            onClick={() => { window.open(`/api/v1/invoicing/${type}s/${id}/pdf`, '_blank'); }}
          >
            Télécharger PDF
          </Button>
          {invoice.status === 'draft' && (
            <CapabilityGuard capability={`invoicing.${type}s.edit`}>
              <Button leftIcon={<Edit size={16} />} onClick={() => navigate(`/${type}s/${id}/edit`)}>
                Modifier
              </Button>
            </CapabilityGuard>
          )}
        </ButtonGroup>
      }
    >
      <Card>
        <div className="azals-invoice-detail">
          <div className="azals-invoice-detail__header">
            <div>
              <h2>{invoice.client_name}</h2>
              <p>Date: {new Date(invoice.date).toLocaleDateString('fr-FR')}</p>
              {invoice.due_date && (
                <p>Échéance: {new Date(invoice.due_date).toLocaleDateString('fr-FR')}</p>
              )}
            </div>
            <div>
              <span className={`azals-badge azals-badge--${STATUS_COLORS[invoice.status]}`}>
                {STATUS_LABELS[invoice.status]}
              </span>
            </div>
          </div>

          <table className="azals-invoice-detail__lines">
            <thead>
              <tr>
                <th>Description</th>
                <th>Quantité</th>
                <th>Prix unitaire</th>
                <th>TVA</th>
                <th>Total HT</th>
              </tr>
            </thead>
            <tbody>
              {invoice.lines.map((line) => (
                <tr key={line.id}>
                  <td>{line.description}</td>
                  <td>{line.quantity}</td>
                  <td>
                    {new Intl.NumberFormat('fr-FR', {
                      style: 'currency',
                      currency: invoice.currency,
                    }).format(line.unit_price)}
                  </td>
                  <td>{line.vat_rate}%</td>
                  <td>
                    {new Intl.NumberFormat('fr-FR', {
                      style: 'currency',
                      currency: invoice.currency,
                    }).format(line.total_ht)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="azals-invoice-detail__totals">
            <div className="azals-invoice-detail__total-row">
              <span>Total HT</span>
              <span>
                {new Intl.NumberFormat('fr-FR', {
                  style: 'currency',
                  currency: invoice.currency,
                }).format(invoice.total_ht)}
              </span>
            </div>
            <div className="azals-invoice-detail__total-row azals-invoice-detail__total-row--main">
              <span>Total TTC</span>
              <span>
                {new Intl.NumberFormat('fr-FR', {
                  style: 'currency',
                  currency: invoice.currency,
                }).format(invoice.total_ttc)}
              </span>
            </div>
          </div>
        </div>
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// MODULE ROUTER
// ============================================================

export const QuotesPage: React.FC = () => <InvoiceList type="quote" />;
export const InvoicesPage: React.FC = () => <InvoiceList type="invoice" />;
export const CreditsPage: React.FC = () => <InvoiceList type="credit" />;

export const QuoteFormPage: React.FC = () => <InvoiceForm type="quote" />;
export const InvoiceFormPage: React.FC = () => <InvoiceForm type="invoice" />;
export const CreditFormPage: React.FC = () => <InvoiceForm type="credit" />;

export const QuoteDetailPage: React.FC = () => <InvoiceDetailPage type="quote" />;
export const InvoiceDetailPageComponent: React.FC = () => <InvoiceDetailPage type="invoice" />;
export const CreditDetailPage: React.FC = () => <InvoiceDetailPage type="credit" />;

export const InvoicingRoutes: React.FC = () => (
  <Routes>
    <Route path="quotes" element={<QuotesPage />} />
    <Route path="quotes/new" element={<QuoteFormPage />} />
    <Route path="quotes/:id" element={<QuoteDetailPage />} />
    <Route path="quotes/:id/edit" element={<QuoteFormPage />} />

    <Route path="invoices" element={<InvoicesPage />} />
    <Route path="invoices/new" element={<InvoiceFormPage />} />
    <Route path="invoices/:id" element={<InvoiceDetailPageComponent />} />
    <Route path="invoices/:id/edit" element={<InvoiceFormPage />} />

    <Route path="credits" element={<CreditsPage />} />
    <Route path="credits/new" element={<CreditFormPage />} />
    <Route path="credits/:id" element={<CreditDetailPage />} />
    <Route path="credits/:id/edit" element={<CreditFormPage />} />
  </Routes>
);

export default InvoicingRoutes;
