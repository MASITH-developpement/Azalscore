/**
 * AZALSCORE Module - DEVIS
 * Gestion des devis clients
 * Flux : CRM → [DEV] → COM/ODS → AFF → FAC/AVO → CPT
 * Numérotation : DEV-YY-MM-XXXX
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText, Plus, Edit, Trash2, Search, Send, Check, X,
  Euro, Calendar, User, Building2, Copy, ChevronRight,
  Download, Printer, Eye, Clock, AlertTriangle, CheckCircle2
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

// ============================================================
// TYPES
// ============================================================

type DocumentStatus = 'DRAFT' | 'PENDING' | 'VALIDATED' | 'SENT' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED';

interface DocumentLine {
  id: string;
  line_number: number;
  product_id?: string;
  product_code?: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount_percent: number;
  discount_amount: number;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
}

interface Devis {
  id: string;
  number: string; // DEV-YY-MM-XXXX
  reference?: string;
  status: DocumentStatus;
  customer_id: string;
  customer_name?: string;
  customer_code?: string;
  opportunity_id?: string;
  date: string;
  validity_date?: string;
  billing_address?: Record<string, string>;
  shipping_address?: Record<string, string>;
  subtotal: number;
  discount_amount: number;
  discount_percent: number;
  tax_amount: number;
  total: number;
  currency: string;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  lines: DocumentLine[];
  pdf_url?: string;
  assigned_to?: string;
  validated_by?: string;
  validated_at?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

interface DevisFormData {
  customer_id: string;
  reference?: string;
  validity_date?: string;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  discount_percent?: number;
}

interface Customer {
  id: string;
  code: string;
  name: string;
  legal_name?: string;
  email?: string;
  phone?: string;
  address_line1?: string;
  city?: string;
  postal_code?: string;
}

// ============================================================
// CONSTANTS
// ============================================================

const STATUS_CONFIG: Record<DocumentStatus, { label: string; color: string; icon: React.ReactNode }> = {
  DRAFT: { label: 'Brouillon', color: 'gray', icon: <Edit size={14} /> },
  PENDING: { label: 'En attente', color: 'yellow', icon: <Clock size={14} /> },
  VALIDATED: { label: 'Validé', color: 'blue', icon: <Check size={14} /> },
  SENT: { label: 'Envoyé', color: 'purple', icon: <Send size={14} /> },
  ACCEPTED: { label: 'Accepté', color: 'green', icon: <CheckCircle2 size={14} /> },
  REJECTED: { label: 'Refusé', color: 'red', icon: <X size={14} /> },
  CANCELLED: { label: 'Annulé', color: 'gray', icon: <X size={14} /> },
};

// ============================================================
// HELPERS
// ============================================================

const formatCurrency = (value: number, currency = 'EUR'): string =>
  new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(value);

const formatDate = (date: string): string =>
  new Date(date).toLocaleDateString('fr-FR');

const generateDevisNumber = (): string => {
  const now = new Date();
  const yy = now.getFullYear().toString().slice(-2);
  const mm = (now.getMonth() + 1).toString().padStart(2, '0');
  const xxxx = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
  return `DEV-${yy}-${mm}-${xxxx}`;
};

// ============================================================
// API HOOKS
// ============================================================

const useDevisList = (page = 1, pageSize = 25, filters?: { status?: string; customer_id?: string; search?: string }) => {
  return useQuery({
    queryKey: ['commercial', 'documents', 'QUOTE', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        type: 'QUOTE',
      });
      if (filters?.status) params.append('status', filters.status);
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      const response = await api.get<PaginatedResponse<Devis>>(`/v1/commercial/documents?${params}`);
      return response.data;
    },
  });
};

const useDevis = (id: string) => {
  return useQuery({
    queryKey: ['commercial', 'documents', id],
    queryFn: async () => {
      const response = await api.get<Devis>(`/v1/commercial/documents/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

const useCustomers = (search?: string) => {
  return useQuery({
    queryKey: ['commercial', 'customers', 'search', search],
    queryFn: async () => {
      const params = new URLSearchParams({ page: '1', page_size: '50' });
      if (search) params.append('search', search);
      const response = await api.get<PaginatedResponse<Customer>>(`/v1/commercial/customers?${params}`);
      return response.data.items;
    },
  });
};

const useCreateDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: DevisFormData) => {
      const response = await api.post<Devis>('/v1/commercial/documents', {
        ...data,
        type: 'QUOTE',
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useUpdateDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<DevisFormData> }) => {
      const response = await api.put<Devis>(`/v1/commercial/documents/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useValidateDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Devis>(`/v1/commercial/documents/${id}/validate`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useSendDevis = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Devis>(`/v1/commercial/documents/${id}/send`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useConvertToOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (quoteId: string) => {
      const response = await api.post<Devis>(`/v1/commercial/quotes/${quoteId}/convert`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useAddLine = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, data }: { documentId: string; data: Partial<DocumentLine> }) => {
      const response = await api.post<DocumentLine>(`/v1/commercial/documents/${documentId}/lines`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useDeleteLine = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (lineId: string) => {
      await api.delete(`/v1/commercial/lines/${lineId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

// ============================================================
// COMPONENTS
// ============================================================

const StatusBadge: React.FC<{ status: DocumentStatus }> = ({ status }) => {
  const config = STATUS_CONFIG[status];
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.icon}
      <span className="ml-1">{config.label}</span>
    </span>
  );
};

const DevisStats: React.FC = () => {
  const { data: devisData } = useDevisList(1, 1000);

  const stats = useMemo(() => {
    const items = devisData?.items || [];
    const brouillons = items.filter(d => d.status === 'DRAFT').length;
    const enAttente = items.filter(d => ['PENDING', 'VALIDATED', 'SENT'].includes(d.status)).length;
    const acceptes = items.filter(d => d.status === 'ACCEPTED').length;
    const totalEnCours = items
      .filter(d => !['ACCEPTED', 'REJECTED', 'CANCELLED'].includes(d.status))
      .reduce((sum, d) => sum + d.total, 0);
    return { brouillons, enAttente, acceptes, totalEnCours };
  }, [devisData]);

  const kpis: DashboardKPI[] = [
    { id: 'brouillons', label: 'Brouillons', value: stats.brouillons, icon: <Edit size={20} /> },
    { id: 'attente', label: 'En attente', value: stats.enAttente, icon: <Clock size={20} /> },
    { id: 'acceptes', label: 'Acceptés', value: stats.acceptes, icon: <CheckCircle2 size={20} /> },
    { id: 'total', label: 'En cours', value: formatCurrency(stats.totalEnCours), icon: <Euro size={20} /> },
  ];

  return (
    <Grid cols={4} gap="md">
      {kpis.map(kpi => <KPICard key={kpi.id} kpi={kpi} />)}
    </Grid>
  );
};

// ============================================================
// NAVIGATION
// ============================================================

type DevisView = 'list' | 'detail' | 'form';

interface DevisNavState {
  view: DevisView;
  devisId?: string;
  customerId?: string;
  isNew?: boolean;
}

// ============================================================
// LIST
// ============================================================

const DevisListInternal: React.FC<{
  onSelectDevis: (id: string) => void;
  onCreateDevis: (customerId?: string) => void;
}> = ({ onSelectDevis, onCreateDevis }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{ status?: string; search?: string }>({});

  const { data, isLoading, refetch } = useDevisList(page, pageSize, filters);

  const columns: TableColumn<Devis>[] = [
    {
      id: 'number',
      header: 'N° Devis',
      accessor: 'number',
      sortable: true,
      render: (value, row) => (
        <span className="azals-link" onClick={() => onSelectDevis(row.id)}>{value as string}</span>
      ),
    },
    {
      id: 'date',
      header: 'Date',
      accessor: 'date',
      sortable: true,
      render: (value) => formatDate(value as string),
    },
    {
      id: 'customer',
      header: 'Client',
      accessor: 'customer_name',
      render: (value, row) => (
        <div>
          <div>{value as string}</div>
          <div className="text-muted text-sm">{row.customer_code}</div>
        </div>
      ),
    },
    {
      id: 'reference',
      header: 'Référence',
      accessor: 'reference',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <StatusBadge status={value as DocumentStatus} />,
    },
    {
      id: 'validity',
      header: 'Validité',
      accessor: 'validity_date',
      render: (value) => {
        if (!value) return '-';
        const date = new Date(value as string);
        const isExpired = date < new Date();
        return (
          <span className={isExpired ? 'text-danger' : ''}>
            {isExpired && <AlertTriangle size={14} className="mr-1" />}
            {formatDate(value as string)}
          </span>
        );
      },
    },
    {
      id: 'total',
      header: 'Total TTC',
      accessor: 'total',
      align: 'right',
      render: (value, row) => formatCurrency(value as number, row.currency),
    },
  ];

  return (
    <PageWrapper
      title="Devis"
      subtitle="Gestion des devis clients"
      actions={<Button leftIcon={<Plus size={16} />} onClick={() => onCreateDevis()}>Nouveau devis</Button>}
    >
      <section className="azals-section">
        <DevisStats />
      </section>

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
            value={filters.status || ''}
            onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined })}
          >
            <option value="">Tous les statuts</option>
            {Object.entries(STATUS_CONFIG).map(([key, config]) => (
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
          emptyMessage="Aucun devis"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// DETAIL
// ============================================================

const DevisDetailInternal: React.FC<{
  devisId: string;
  onBack: () => void;
  onEdit: () => void;
}> = ({ devisId, onBack, onEdit }) => {
  const { data: devis, isLoading } = useDevis(devisId);
  const validateDevis = useValidateDevis();
  const sendDevis = useSendDevis();
  const convertToOrder = useConvertToOrder();

  const handleValidate = async () => {
    if (window.confirm('Valider ce devis ?')) {
      await validateDevis.mutateAsync(devisId);
    }
  };

  const handleSend = async () => {
    if (window.confirm('Marquer ce devis comme envoyé ?')) {
      await sendDevis.mutateAsync(devisId);
    }
  };

  const handleConvert = async () => {
    if (window.confirm('Convertir ce devis en commande ?')) {
      try {
        const order = await convertToOrder.mutateAsync(devisId);
        window.dispatchEvent(new CustomEvent('azals:navigate', {
          detail: { view: 'commandes', params: { id: order.id } }
        }));
      } catch (error) {
        console.error('Erreur conversion:', error);
      }
    }
  };

  if (isLoading) {
    return <PageWrapper title="Chargement..."><div className="azals-loading">Chargement...</div></PageWrapper>;
  }

  if (!devis) {
    return (
      <PageWrapper title="Devis non trouvé">
        <Card><p>Ce devis n'existe pas.</p><Button onClick={onBack}>Retour</Button></Card>
      </PageWrapper>
    );
  }

  const canEdit = devis.status === 'DRAFT';
  const canValidate = devis.status === 'DRAFT';
  const canSend = devis.status === 'VALIDATED';
  const canConvert = devis.status === 'ACCEPTED';

  return (
    <PageWrapper
      title={devis.number}
      subtitle={devis.customer_name}
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={
        <ButtonGroup>
          {canConvert && (
            <Button leftIcon={<ChevronRight size={16} />} onClick={handleConvert} isLoading={convertToOrder.isPending}>
              Convertir en commande
            </Button>
          )}
          {canSend && (
            <Button variant="secondary" leftIcon={<Send size={16} />} onClick={handleSend} isLoading={sendDevis.isPending}>
              Marquer envoyé
            </Button>
          )}
          {canValidate && (
            <Button variant="secondary" leftIcon={<Check size={16} />} onClick={handleValidate} isLoading={validateDevis.isPending}>
              Valider
            </Button>
          )}
          {canEdit && (
            <Button variant="ghost" leftIcon={<Edit size={16} />} onClick={onEdit}>Modifier</Button>
          )}
          <Button variant="ghost" leftIcon={<Download size={16} />}>PDF</Button>
          <Button variant="ghost" leftIcon={<Printer size={16} />}>Imprimer</Button>
        </ButtonGroup>
      }
    >
      <Grid cols={4} gap="md" className="mb-4">
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Statut</span>
            <StatusBadge status={devis.status} />
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Date</span>
            <span className="azals-stat__value">{formatDate(devis.date)}</span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Validité</span>
            <span className="azals-stat__value">{devis.validity_date ? formatDate(devis.validity_date) : '-'}</span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Total TTC</span>
            <span className="azals-stat__value azals-stat__value--large">{formatCurrency(devis.total)}</span>
          </div>
        </Card>
      </Grid>

      <Grid cols={2} gap="lg" className="mb-4">
        <Card title="Client">
          <dl className="azals-dl">
            <dt><Building2 size={14} /> Client</dt>
            <dd>
              <strong>{devis.customer_name}</strong>
              {devis.customer_code && <span className="text-muted"> ({devis.customer_code})</span>}
            </dd>
            {devis.billing_address && (
              <>
                <dt>Adresse facturation</dt>
                <dd>
                  {devis.billing_address.line1 && <div>{devis.billing_address.line1}</div>}
                  {devis.billing_address.city && <div>{devis.billing_address.postal_code} {devis.billing_address.city}</div>}
                </dd>
              </>
            )}
          </dl>
        </Card>

        <Card title="Informations">
          <dl className="azals-dl">
            {devis.reference && <><dt>Référence client</dt><dd>{devis.reference}</dd></>}
            <dt>Créé le</dt><dd>{formatDate(devis.created_at)}</dd>
            {devis.validated_at && <><dt>Validé le</dt><dd>{formatDate(devis.validated_at)}</dd></>}
          </dl>
        </Card>
      </Grid>

      <Card title="Lignes du devis">
        {devis.lines && devis.lines.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>#</th>
                <th>Description</th>
                <th className="text-right">Qté</th>
                <th className="text-right">P.U. HT</th>
                <th className="text-right">Remise</th>
                <th className="text-right">Total HT</th>
              </tr>
            </thead>
            <tbody>
              {devis.lines.map(line => (
                <tr key={line.id}>
                  <td>{line.line_number}</td>
                  <td>
                    {line.product_code && <span className="text-muted">[{line.product_code}] </span>}
                    {line.description}
                  </td>
                  <td className="text-right">{line.quantity} {line.unit}</td>
                  <td className="text-right">{formatCurrency(line.unit_price)}</td>
                  <td className="text-right">{line.discount_percent > 0 ? `${line.discount_percent}%` : '-'}</td>
                  <td className="text-right">{formatCurrency(line.subtotal)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={5} className="text-right"><strong>Sous-total HT</strong></td>
                <td className="text-right">{formatCurrency(devis.subtotal)}</td>
              </tr>
              {devis.discount_amount > 0 && (
                <tr>
                  <td colSpan={5} className="text-right">Remise {devis.discount_percent > 0 && `(${devis.discount_percent}%)`}</td>
                  <td className="text-right">-{formatCurrency(devis.discount_amount)}</td>
                </tr>
              )}
              <tr>
                <td colSpan={5} className="text-right">TVA</td>
                <td className="text-right">{formatCurrency(devis.tax_amount)}</td>
              </tr>
              <tr className="azals-table__total">
                <td colSpan={5} className="text-right"><strong>Total TTC</strong></td>
                <td className="text-right"><strong>{formatCurrency(devis.total)}</strong></td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <p className="text-muted text-center py-4">Aucune ligne</p>
        )}
      </Card>

      {(devis.notes || devis.terms) && (
        <Grid cols={2} gap="lg" className="mt-4">
          {devis.notes && (
            <Card title="Notes">
              <p className="text-muted">{devis.notes}</p>
            </Card>
          )}
          {devis.terms && (
            <Card title="Conditions">
              <p className="text-muted">{devis.terms}</p>
            </Card>
          )}
        </Grid>
      )}

      {canConvert && (
        <Card className="mt-4">
          <div className="azals-action-card">
            <div>
              <h4>Prochaine étape</h4>
              <p className="text-muted">Ce devis est accepté, vous pouvez le convertir en commande</p>
            </div>
            <Button leftIcon={<ChevronRight size={16} />} onClick={handleConvert}>
              Convertir en commande
            </Button>
          </div>
        </Card>
      )}
    </PageWrapper>
  );
};

// ============================================================
// FORM
// ============================================================

const DevisFormInternal: React.FC<{
  devisId?: string;
  customerId?: string;
  onBack: () => void;
  onSaved: (id: string) => void;
}> = ({ devisId, customerId, onBack, onSaved }) => {
  const isNew = !devisId;
  const { data: devis } = useDevis(devisId || '');
  const { data: customers } = useCustomers();
  const createDevis = useCreateDevis();
  const updateDevis = useUpdateDevis();
  const addLine = useAddLine();
  const deleteLine = useDeleteLine();

  const [form, setForm] = useState<DevisFormData>({
    customer_id: customerId || '',
    reference: '',
    validity_date: '',
    notes: '',
    internal_notes: '',
    terms: '',
    discount_percent: 0,
  });

  const [lines, setLines] = useState<Partial<DocumentLine>[]>([]);
  const [newLine, setNewLine] = useState<Partial<DocumentLine>>({
    description: '',
    quantity: 1,
    unit: 'pce',
    unit_price: 0,
    discount_percent: 0,
    tax_rate: 20,
  });

  React.useEffect(() => {
    if (devis) {
      setForm({
        customer_id: devis.customer_id,
        reference: devis.reference || '',
        validity_date: devis.validity_date || '',
        notes: devis.notes || '',
        internal_notes: devis.internal_notes || '',
        terms: devis.terms || '',
        discount_percent: devis.discount_percent,
      });
      setLines(devis.lines || []);
    }
  }, [devis]);

  const handleAddLine = () => {
    if (!newLine.description) return;
    setLines([...lines, { ...newLine, line_number: lines.length + 1 }]);
    setNewLine({
      description: '',
      quantity: 1,
      unit: 'pce',
      unit_price: 0,
      discount_percent: 0,
      tax_rate: 20,
    });
  };

  const handleRemoveLine = (index: number) => {
    setLines(lines.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.customer_id) {
      alert('Veuillez sélectionner un client');
      return;
    }
    try {
      if (isNew) {
        const result = await createDevis.mutateAsync(form);
        // Ajouter les lignes
        for (const line of lines) {
          await addLine.mutateAsync({ documentId: result.id, data: line });
        }
        onSaved(result.id);
      } else {
        await updateDevis.mutateAsync({ id: devisId!, data: form });
        onSaved(devisId!);
      }
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    }
  };

  const isSubmitting = createDevis.isPending || updateDevis.isPending;

  const calculateTotals = () => {
    const subtotal = lines.reduce((sum, line) => {
      const lineTotal = (line.quantity || 0) * (line.unit_price || 0) * (1 - (line.discount_percent || 0) / 100);
      return sum + lineTotal;
    }, 0);
    const discountAmount = subtotal * (form.discount_percent || 0) / 100;
    const taxBase = subtotal - discountAmount;
    const taxAmount = lines.reduce((sum, line) => {
      const lineTotal = (line.quantity || 0) * (line.unit_price || 0) * (1 - (line.discount_percent || 0) / 100);
      return sum + lineTotal * (line.tax_rate || 20) / 100;
    }, 0) * (1 - (form.discount_percent || 0) / 100);
    const total = taxBase + taxAmount;
    return { subtotal, discountAmount, taxAmount, total };
  };

  const totals = calculateTotals();

  return (
    <PageWrapper
      title={isNew ? 'Nouveau devis' : `Modifier ${devis?.number}`}
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <form onSubmit={handleSubmit}>
        <Grid cols={2} gap="lg">
          <Card title="Client">
            <div className="azals-form-field">
              <label>Client *</label>
              <select
                className="azals-select"
                value={form.customer_id}
                onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
                required
              >
                <option value="">-- Sélectionner un client --</option>
                {customers?.map(c => (
                  <option key={c.id} value={c.id}>{c.name} ({c.code})</option>
                ))}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Référence client</label>
              <input
                type="text"
                className="azals-input"
                value={form.reference}
                onChange={(e) => setForm({ ...form, reference: e.target.value })}
                placeholder="Votre référence..."
              />
            </div>
          </Card>

          <Card title="Dates">
            <div className="azals-form-field">
              <label>Date de validité</label>
              <input
                type="date"
                className="azals-input"
                value={form.validity_date}
                onChange={(e) => setForm({ ...form, validity_date: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>Remise globale (%)</label>
              <input
                type="number"
                className="azals-input"
                value={form.discount_percent}
                onChange={(e) => setForm({ ...form, discount_percent: parseFloat(e.target.value) || 0 })}
                min="0"
                max="100"
                step="0.5"
              />
            </div>
          </Card>
        </Grid>

        <Card title="Lignes" className="mt-4">
          {lines.length > 0 && (
            <table className="azals-table azals-table--simple mb-4">
              <thead>
                <tr>
                  <th>Description</th>
                  <th className="text-right">Qté</th>
                  <th className="text-right">P.U. HT</th>
                  <th className="text-right">Remise</th>
                  <th className="text-right">TVA</th>
                  <th className="text-right">Total HT</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line, index) => (
                  <tr key={index}>
                    <td>{line.description}</td>
                    <td className="text-right">{line.quantity} {line.unit}</td>
                    <td className="text-right">{formatCurrency(line.unit_price || 0)}</td>
                    <td className="text-right">{line.discount_percent}%</td>
                    <td className="text-right">{line.tax_rate}%</td>
                    <td className="text-right">
                      {formatCurrency((line.quantity || 0) * (line.unit_price || 0) * (1 - (line.discount_percent || 0) / 100))}
                    </td>
                    <td>
                      <Button variant="ghost" size="sm" onClick={() => handleRemoveLine(index)}>
                        <Trash2 size={14} />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="azals-add-line">
            <Grid cols={4} gap="sm">
              <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
                <input
                  type="text"
                  className="azals-input"
                  placeholder="Description..."
                  value={newLine.description}
                  onChange={(e) => setNewLine({ ...newLine, description: e.target.value })}
                />
              </div>
              <div className="azals-form-field">
                <input
                  type="number"
                  className="azals-input"
                  placeholder="Qté"
                  value={newLine.quantity}
                  onChange={(e) => setNewLine({ ...newLine, quantity: parseFloat(e.target.value) || 1 })}
                  min="0"
                  step="0.01"
                />
              </div>
              <div className="azals-form-field">
                <input
                  type="number"
                  className="azals-input"
                  placeholder="P.U. HT"
                  value={newLine.unit_price}
                  onChange={(e) => setNewLine({ ...newLine, unit_price: parseFloat(e.target.value) || 0 })}
                  min="0"
                  step="0.01"
                />
              </div>
              <div className="azals-form-field">
                <select
                  className="azals-select"
                  value={newLine.tax_rate}
                  onChange={(e) => setNewLine({ ...newLine, tax_rate: parseFloat(e.target.value) })}
                >
                  <option value="20">20%</option>
                  <option value="10">10%</option>
                  <option value="5.5">5.5%</option>
                  <option value="0">0%</option>
                </select>
              </div>
              <div>
                <Button type="button" variant="secondary" onClick={handleAddLine}>
                  <Plus size={16} />
                </Button>
              </div>
            </Grid>
          </div>

          <div className="azals-totals mt-4">
            <div className="azals-totals__row">
              <span>Sous-total HT</span>
              <span>{formatCurrency(totals.subtotal)}</span>
            </div>
            {totals.discountAmount > 0 && (
              <div className="azals-totals__row">
                <span>Remise ({form.discount_percent}%)</span>
                <span>-{formatCurrency(totals.discountAmount)}</span>
              </div>
            )}
            <div className="azals-totals__row">
              <span>TVA</span>
              <span>{formatCurrency(totals.taxAmount)}</span>
            </div>
            <div className="azals-totals__row azals-totals__row--total">
              <span>Total TTC</span>
              <span>{formatCurrency(totals.total)}</span>
            </div>
          </div>
        </Card>

        <Card title="Notes" className="mt-4">
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>Notes (visibles sur le devis)</label>
              <textarea
                className="azals-textarea"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                rows={3}
              />
            </div>
            <div className="azals-form-field">
              <label>Conditions</label>
              <textarea
                className="azals-textarea"
                value={form.terms}
                onChange={(e) => setForm({ ...form, terms: e.target.value })}
                rows={3}
                placeholder="Conditions de paiement, délais..."
              />
            </div>
          </Grid>
        </Card>

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onBack}>Annuler</Button>
          <Button type="submit" isLoading={isSubmitting}>{isNew ? 'Créer le devis' : 'Enregistrer'}</Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================
// MODULE PRINCIPAL
// ============================================================

export const DevisModule: React.FC = () => {
  const [navState, setNavState] = useState<DevisNavState>({ view: 'list' });

  // Écouter les événements de navigation
  React.useEffect(() => {
    const handleNavigate = (event: CustomEvent) => {
      const { params } = event.detail || {};
      if (params?.customerId && params?.action === 'new') {
        setNavState({ view: 'form', customerId: params.customerId, isNew: true });
      } else if (params?.id) {
        setNavState({ view: 'detail', devisId: params.id });
      }
    };
    window.addEventListener('azals:navigate:devis', handleNavigate as EventListener);
    return () => window.removeEventListener('azals:navigate:devis', handleNavigate as EventListener);
  }, []);

  const navigateToList = useCallback(() => setNavState({ view: 'list' }), []);
  const navigateToDetail = useCallback((id: string) => setNavState({ view: 'detail', devisId: id }), []);
  const navigateToForm = useCallback((id?: string, customerId?: string) =>
    setNavState({ view: 'form', devisId: id, customerId, isNew: !id }), []);

  switch (navState.view) {
    case 'detail':
      return (
        <DevisDetailInternal
          devisId={navState.devisId!}
          onBack={navigateToList}
          onEdit={() => navigateToForm(navState.devisId)}
        />
      );
    case 'form':
      return (
        <DevisFormInternal
          devisId={navState.devisId}
          customerId={navState.customerId}
          onBack={navState.isNew ? navigateToList : () => navigateToDetail(navState.devisId!)}
          onSaved={navigateToDetail}
        />
      );
    default:
      return (
        <DevisListInternal
          onSelectDevis={navigateToDetail}
          onCreateDevis={(customerId) => navigateToForm(undefined, customerId)}
        />
      );
  }
};

export default DevisModule;
