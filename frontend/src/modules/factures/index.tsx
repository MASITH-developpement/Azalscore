/**
 * AZALSCORE Module - FACTURES & AVOIRS
 * Gestion de la facturation clients
 * Flux : CRM → DEV → COM/ODS → AFF → [FAC/AVO] → CPT
 * Numérotation : FAC-YY-MM-XXXX / AVO-YY-MM-XXXX
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText, Plus, Edit, Trash2, Search, Check, X, Send,
  Euro, Calendar, Building2, CreditCard, ChevronRight,
  Download, Printer, Clock, CheckCircle2, AlertTriangle,
  ArrowLeftRight, Ban
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

type FactureType = 'INVOICE' | 'CREDIT_NOTE';
type FactureStatus = 'DRAFT' | 'VALIDATED' | 'SENT' | 'PAID' | 'PARTIAL' | 'OVERDUE' | 'CANCELLED';
type PaymentMethod = 'BANK_TRANSFER' | 'CHECK' | 'CREDIT_CARD' | 'CASH' | 'DIRECT_DEBIT' | 'OTHER';

interface DocumentLine {
  id: string;
  line_number: number;
  product_code?: string;
  description: string;
  quantity: number;
  unit?: string;
  unit_price: number;
  discount_percent: number;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
}

interface Payment {
  id: string;
  reference?: string;
  method: PaymentMethod;
  amount: number;
  date: string;
  notes?: string;
}

interface Facture {
  id: string;
  type: FactureType;
  number: string; // FAC-YY-MM-XXXX ou AVO-YY-MM-XXXX
  reference?: string;
  status: FactureStatus;
  customer_id: string;
  customer_name?: string;
  customer_code?: string;
  parent_id?: string; // Commande ou intervention source
  parent_number?: string;
  date: string;
  due_date?: string;
  billing_address?: Record<string, string>;
  subtotal: number;
  discount_amount: number;
  discount_percent: number;
  tax_amount: number;
  total: number;
  currency: string;
  payment_terms?: string;
  payment_method?: PaymentMethod;
  paid_amount: number;
  remaining_amount: number;
  lines: DocumentLine[];
  payments?: Payment[];
  notes?: string;
  internal_notes?: string;
  pdf_url?: string;
  validated_by?: string;
  validated_at?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

interface FactureFormData {
  customer_id: string;
  type: FactureType;
  reference?: string;
  due_date?: string;
  payment_terms?: string;
  notes?: string;
}

interface PaymentFormData {
  method: PaymentMethod;
  amount: number;
  date: string;
  reference?: string;
  notes?: string;
}

// ============================================================
// CONSTANTS
// ============================================================

const TYPE_CONFIG: Record<FactureType, { label: string; prefix: string; color: string }> = {
  INVOICE: { label: 'Facture', prefix: 'FAC', color: 'blue' },
  CREDIT_NOTE: { label: 'Avoir', prefix: 'AVO', color: 'orange' },
};

const STATUS_CONFIG: Record<FactureStatus, { label: string; color: string; icon: React.ReactNode }> = {
  DRAFT: { label: 'Brouillon', color: 'gray', icon: <Edit size={14} /> },
  VALIDATED: { label: 'Validée', color: 'blue', icon: <Check size={14} /> },
  SENT: { label: 'Envoyée', color: 'purple', icon: <Send size={14} /> },
  PAID: { label: 'Payée', color: 'green', icon: <CheckCircle2 size={14} /> },
  PARTIAL: { label: 'Partielle', color: 'yellow', icon: <Clock size={14} /> },
  OVERDUE: { label: 'En retard', color: 'red', icon: <AlertTriangle size={14} /> },
  CANCELLED: { label: 'Annulée', color: 'gray', icon: <Ban size={14} /> },
};

const PAYMENT_METHODS: Record<PaymentMethod, string> = {
  BANK_TRANSFER: 'Virement',
  CHECK: 'Chèque',
  CREDIT_CARD: 'Carte bancaire',
  CASH: 'Espèces',
  DIRECT_DEBIT: 'Prélèvement',
  OTHER: 'Autre',
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

const useFacturesList = (page = 1, pageSize = 25, filters?: { type?: FactureType; status?: string }) => {
  return useQuery({
    queryKey: ['commercial', 'documents', 'factures', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      // Fetch both invoices and credit notes
      if (filters?.type) {
        params.append('type', filters.type);
      } else {
        // Par défaut: factures et avoirs
        params.append('type', 'INVOICE');
      }
      if (filters?.status) params.append('status', filters.status);

      const response = await api.get<PaginatedResponse<Facture>>(`/v1/commercial/documents?${params}`);
      return response.data;
    },
  });
};

const useFacture = (id: string) => {
  return useQuery({
    queryKey: ['commercial', 'documents', id],
    queryFn: async () => {
      const response = await api.get<Facture>(`/v1/commercial/documents/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
};

const useFacturePayments = (documentId: string) => {
  return useQuery({
    queryKey: ['commercial', 'documents', documentId, 'payments'],
    queryFn: async () => {
      const response = await api.get<Payment[]>(`/v1/commercial/documents/${documentId}/payments`);
      return response.data;
    },
    enabled: !!documentId,
  });
};

const useCustomers = () => {
  return useQuery({
    queryKey: ['commercial', 'customers', 'all'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<{ id: string; code: string; name: string }>>('/v1/commercial/customers?page_size=100');
      return response.data.items;
    },
  });
};

const useCreateFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: FactureFormData) => {
      const response = await api.post<Facture>('/v1/commercial/documents', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useValidateFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Facture>(`/v1/commercial/documents/${id}/validate`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useSendFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Facture>(`/v1/commercial/documents/${id}/send`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useCreatePayment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ documentId, data }: { documentId: string; data: PaymentFormData }) => {
      const response = await api.post<Payment>('/v1/commercial/payments', {
        document_id: documentId,
        ...data,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useCreateAvoir = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (factureId: string) => {
      // Créer un avoir à partir d'une facture
      const response = await api.post<Facture>(`/v1/commercial/documents/${factureId}/credit-note`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

// ============================================================
// COMPONENTS
// ============================================================

const TypeBadge: React.FC<{ type: FactureType }> = ({ type }) => {
  const config = TYPE_CONFIG[type];
  return (
    <span className={`azals-badge azals-badge--${config.color} azals-badge--outline`}>
      {config.label}
    </span>
  );
};

const StatusBadge: React.FC<{ status: FactureStatus }> = ({ status }) => {
  const config = STATUS_CONFIG[status];
  return (
    <span className={`azals-badge azals-badge--${config.color}`}>
      {config.icon}
      <span className="ml-1">{config.label}</span>
    </span>
  );
};

const FacturesStats: React.FC = () => {
  const { data: invoices } = useFacturesList(1, 1000, { type: 'INVOICE' });

  const stats = useMemo(() => {
    const items = invoices?.items || [];
    const enAttente = items.filter(f => ['DRAFT', 'VALIDATED', 'SENT'].includes(f.status)).length;
    const enRetard = items.filter(f => f.status === 'OVERDUE').length;
    const caEncaisse = items.filter(f => f.status === 'PAID').reduce((sum, f) => sum + f.total, 0);
    const aEncaisser = items.filter(f => ['VALIDATED', 'SENT', 'PARTIAL', 'OVERDUE'].includes(f.status))
      .reduce((sum, f) => sum + f.remaining_amount, 0);
    return { enAttente, enRetard, caEncaisse, aEncaisser };
  }, [invoices]);

  const kpis: DashboardKPI[] = [
    { id: 'attente', label: 'En attente', value: stats.enAttente, icon: <Clock size={20} /> },
    { id: 'retard', label: 'En retard', value: stats.enRetard, icon: <AlertTriangle size={20} />, variant: stats.enRetard > 0 ? 'danger' : undefined },
    { id: 'encaisse', label: 'Encaissé', value: formatCurrency(stats.caEncaisse), icon: <CheckCircle2 size={20} /> },
    { id: 'aencaisser', label: 'À encaisser', value: formatCurrency(stats.aEncaisser), icon: <Euro size={20} /> },
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

type FactureView = 'list' | 'detail' | 'form' | 'payment';

interface FactureNavState {
  view: FactureView;
  factureId?: string;
  factureType?: FactureType;
  isNew?: boolean;
}

// ============================================================
// LIST
// ============================================================

const FacturesListInternal: React.FC<{
  onSelectFacture: (id: string) => void;
  onCreateFacture: (type: FactureType) => void;
}> = ({ onSelectFacture, onCreateFacture }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{ type?: FactureType; status?: string }>({});
  const [activeTab, setActiveTab] = useState<'INVOICE' | 'CREDIT_NOTE' | 'ALL'>('INVOICE');

  const { data, isLoading, refetch } = useFacturesList(page, pageSize, {
    type: activeTab === 'ALL' ? undefined : activeTab,
    status: filters.status,
  });

  const columns: TableColumn<Facture>[] = [
    {
      id: 'number',
      header: 'Numéro',
      accessor: 'number',
      sortable: true,
      render: (value, row) => (
        <div>
          <span className="azals-link" onClick={() => onSelectFacture(row.id)}>{value as string}</span>
          {row.type === 'CREDIT_NOTE' && <TypeBadge type={row.type} />}
        </div>
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
      id: 'due_date',
      header: 'Échéance',
      accessor: 'due_date',
      render: (value, row) => {
        if (!value) return '-';
        const isOverdue = new Date(value as string) < new Date() && !['PAID', 'CANCELLED'].includes(row.status);
        return (
          <span className={isOverdue ? 'text-danger' : ''}>
            {isOverdue && <AlertTriangle size={14} className="mr-1" />}
            {formatDate(value as string)}
          </span>
        );
      },
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <StatusBadge status={value as FactureStatus} />,
    },
    {
      id: 'total',
      header: 'Total TTC',
      accessor: 'total',
      align: 'right',
      render: (value, row) => (
        <span className={row.type === 'CREDIT_NOTE' ? 'text-danger' : ''}>
          {row.type === 'CREDIT_NOTE' && '-'}
          {formatCurrency(value as number, row.currency)}
        </span>
      ),
    },
    {
      id: 'remaining',
      header: 'Reste dû',
      accessor: 'remaining_amount',
      align: 'right',
      render: (value, row) => {
        if (row.status === 'PAID' || row.status === 'CANCELLED') return '-';
        return <span className="text-warning">{formatCurrency(value as number)}</span>;
      },
    },
  ];

  return (
    <PageWrapper
      title="Factures & Avoirs"
      subtitle="Gestion de la facturation"
      actions={
        <ButtonGroup>
          <Button leftIcon={<Plus size={16} />} onClick={() => onCreateFacture('INVOICE')}>
            Nouvelle facture
          </Button>
          <Button variant="secondary" leftIcon={<ArrowLeftRight size={16} />} onClick={() => onCreateFacture('CREDIT_NOTE')}>
            Nouvel avoir
          </Button>
        </ButtonGroup>
      }
    >
      <section className="azals-section">
        <FacturesStats />
      </section>

      <Card noPadding>
        <div className="azals-tabs">
          <button
            className={`azals-tab ${activeTab === 'INVOICE' ? 'azals-tab--active' : ''}`}
            onClick={() => setActiveTab('INVOICE')}
          >
            Factures
          </button>
          <button
            className={`azals-tab ${activeTab === 'CREDIT_NOTE' ? 'azals-tab--active' : ''}`}
            onClick={() => setActiveTab('CREDIT_NOTE')}
          >
            Avoirs
          </button>
          <button
            className={`azals-tab ${activeTab === 'ALL' ? 'azals-tab--active' : ''}`}
            onClick={() => setActiveTab('ALL')}
          >
            Tout
          </button>
        </div>

        <div className="azals-filter-bar">
          <div className="azals-filter-bar__search">
            <Search size={16} />
            <input type="text" placeholder="Rechercher..." className="azals-input" />
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
          emptyMessage="Aucune facture"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// DETAIL
// ============================================================

const FactureDetailInternal: React.FC<{
  factureId: string;
  onBack: () => void;
  onEdit: () => void;
  onAddPayment: () => void;
}> = ({ factureId, onBack, onEdit, onAddPayment }) => {
  const { data: facture, isLoading } = useFacture(factureId);
  const { data: payments } = useFacturePayments(factureId);
  const validateFacture = useValidateFacture();
  const sendFacture = useSendFacture();
  const createAvoir = useCreateAvoir();

  const handleValidate = async () => {
    if (window.confirm('Valider cette facture ?')) {
      await validateFacture.mutateAsync(factureId);
    }
  };

  const handleSend = async () => {
    if (window.confirm('Marquer comme envoyée ?')) {
      await sendFacture.mutateAsync(factureId);
    }
  };

  const handleCreateAvoir = async () => {
    if (window.confirm('Créer un avoir pour cette facture ?')) {
      try {
        const avoir = await createAvoir.mutateAsync(factureId);
        window.dispatchEvent(new CustomEvent('azals:navigate', {
          detail: { view: 'factures', params: { id: avoir.id } }
        }));
      } catch (error) {
        console.error('Erreur création avoir:', error);
      }
    }
  };

  const handleComptabiliser = () => {
    window.dispatchEvent(new CustomEvent('azals:navigate', {
      detail: { view: 'comptabilite', params: { factureId, action: 'comptabiliser' } }
    }));
  };

  if (isLoading) {
    return <PageWrapper title="Chargement..."><div className="azals-loading">Chargement...</div></PageWrapper>;
  }

  if (!facture) {
    return (
      <PageWrapper title="Facture non trouvée">
        <Card><p>Cette facture n'existe pas.</p><Button onClick={onBack}>Retour</Button></Card>
      </PageWrapper>
    );
  }

  const isInvoice = facture.type === 'INVOICE';
  const canEdit = facture.status === 'DRAFT';
  const canValidate = facture.status === 'DRAFT';
  const canSend = facture.status === 'VALIDATED';
  const canPay = isInvoice && ['VALIDATED', 'SENT', 'PARTIAL', 'OVERDUE'].includes(facture.status);
  const canCreateAvoir = isInvoice && facture.status === 'PAID';
  const canComptabiliser = facture.status === 'PAID';

  return (
    <PageWrapper
      title={facture.number}
      subtitle={`${TYPE_CONFIG[facture.type].label} - ${facture.customer_name}`}
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={
        <ButtonGroup>
          {canPay && (
            <Button leftIcon={<CreditCard size={16} />} onClick={onAddPayment}>
              Encaisser
            </Button>
          )}
          {canComptabiliser && (
            <Button variant="secondary" leftIcon={<ChevronRight size={16} />} onClick={handleComptabiliser}>
              Comptabiliser
            </Button>
          )}
          {canCreateAvoir && (
            <Button variant="secondary" leftIcon={<ArrowLeftRight size={16} />} onClick={handleCreateAvoir} isLoading={createAvoir.isPending}>
              Créer avoir
            </Button>
          )}
          {canSend && (
            <Button variant="secondary" leftIcon={<Send size={16} />} onClick={handleSend} isLoading={sendFacture.isPending}>
              Marquer envoyée
            </Button>
          )}
          {canValidate && (
            <Button variant="secondary" leftIcon={<Check size={16} />} onClick={handleValidate} isLoading={validateFacture.isPending}>
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
            <span className="azals-stat__label">Type</span>
            <TypeBadge type={facture.type} />
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Statut</span>
            <StatusBadge status={facture.status} />
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Échéance</span>
            <span className="azals-stat__value">{facture.due_date ? formatDate(facture.due_date) : '-'}</span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Total TTC</span>
            <span className={`azals-stat__value azals-stat__value--large ${facture.type === 'CREDIT_NOTE' ? 'text-danger' : ''}`}>
              {facture.type === 'CREDIT_NOTE' && '-'}
              {formatCurrency(facture.total)}
            </span>
          </div>
        </Card>
      </Grid>

      {facture.parent_number && (
        <div className="azals-alert azals-alert--info mb-4">
          <FileText size={20} />
          <div>
            <strong>Document source</strong>
            <p>{facture.parent_number}</p>
          </div>
        </div>
      )}

      <Grid cols={2} gap="lg" className="mb-4">
        <Card title="Client">
          <dl className="azals-dl">
            <dt><Building2 size={14} /> Client</dt>
            <dd>
              <strong>{facture.customer_name}</strong>
              {facture.customer_code && <span className="text-muted"> ({facture.customer_code})</span>}
            </dd>
            {facture.billing_address && (
              <>
                <dt>Adresse facturation</dt>
                <dd>
                  {facture.billing_address.line1 && <div>{facture.billing_address.line1}</div>}
                  {facture.billing_address.city && <div>{facture.billing_address.postal_code} {facture.billing_address.city}</div>}
                </dd>
              </>
            )}
          </dl>
        </Card>

        <Card title="Paiement">
          <dl className="azals-dl">
            <dt>Conditions</dt><dd>{facture.payment_terms || 'Net 30'}</dd>
            <dt>Mode de paiement</dt><dd>{facture.payment_method ? PAYMENT_METHODS[facture.payment_method] : '-'}</dd>
            {isInvoice && (
              <>
                <dt>Payé</dt><dd>{formatCurrency(facture.paid_amount)}</dd>
                <dt>Reste dû</dt>
                <dd className={facture.remaining_amount > 0 ? 'text-warning' : 'text-success'}>
                  {formatCurrency(facture.remaining_amount)}
                </dd>
              </>
            )}
          </dl>
        </Card>
      </Grid>

      <Card title="Lignes">
        {facture.lines && facture.lines.length > 0 ? (
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>#</th>
                <th>Description</th>
                <th className="text-right">Qté</th>
                <th className="text-right">P.U. HT</th>
                <th className="text-right">Total HT</th>
              </tr>
            </thead>
            <tbody>
              {facture.lines.map(line => (
                <tr key={line.id}>
                  <td>{line.line_number}</td>
                  <td>
                    {line.product_code && <span className="text-muted">[{line.product_code}] </span>}
                    {line.description}
                  </td>
                  <td className="text-right">{line.quantity} {line.unit}</td>
                  <td className="text-right">{formatCurrency(line.unit_price)}</td>
                  <td className="text-right">{formatCurrency(line.subtotal)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan={4} className="text-right"><strong>Sous-total HT</strong></td>
                <td className="text-right">{formatCurrency(facture.subtotal)}</td>
              </tr>
              <tr>
                <td colSpan={4} className="text-right">TVA</td>
                <td className="text-right">{formatCurrency(facture.tax_amount)}</td>
              </tr>
              <tr className="azals-table__total">
                <td colSpan={4} className="text-right"><strong>Total TTC</strong></td>
                <td className="text-right"><strong>{formatCurrency(facture.total)}</strong></td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <p className="text-muted text-center py-4">Aucune ligne</p>
        )}
      </Card>

      {payments && payments.length > 0 && (
        <Card title="Paiements reçus" className="mt-4">
          <table className="azals-table azals-table--simple">
            <thead>
              <tr>
                <th>Date</th>
                <th>Référence</th>
                <th>Mode</th>
                <th className="text-right">Montant</th>
              </tr>
            </thead>
            <tbody>
              {payments.map(p => (
                <tr key={p.id}>
                  <td>{formatDate(p.date)}</td>
                  <td>{p.reference || '-'}</td>
                  <td>{PAYMENT_METHODS[p.method]}</td>
                  <td className="text-right text-success">{formatCurrency(p.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {canPay && facture.remaining_amount > 0 && (
        <Card className="mt-4">
          <div className="azals-action-card">
            <div>
              <h4>Encaissement</h4>
              <p className="text-muted">Reste à encaisser: {formatCurrency(facture.remaining_amount)}</p>
            </div>
            <Button leftIcon={<CreditCard size={16} />} onClick={onAddPayment}>
              Enregistrer un paiement
            </Button>
          </div>
        </Card>
      )}

      {canComptabiliser && (
        <Card className="mt-4">
          <div className="azals-action-card">
            <div>
              <h4>Prochaine étape</h4>
              <p className="text-muted">Cette facture est soldée, vous pouvez la comptabiliser</p>
            </div>
            <Button leftIcon={<ChevronRight size={16} />} onClick={handleComptabiliser}>
              Comptabiliser
            </Button>
          </div>
        </Card>
      )}
    </PageWrapper>
  );
};

// ============================================================
// PAYMENT FORM
// ============================================================

const PaymentFormInternal: React.FC<{
  factureId: string;
  onBack: () => void;
  onSaved: () => void;
}> = ({ factureId, onBack, onSaved }) => {
  const { data: facture } = useFacture(factureId);
  const createPayment = useCreatePayment();

  const [form, setForm] = useState<PaymentFormData>({
    method: 'BANK_TRANSFER',
    amount: 0,
    date: new Date().toISOString().split('T')[0],
    reference: '',
    notes: '',
  });

  React.useEffect(() => {
    if (facture) {
      setForm(f => ({ ...f, amount: facture.remaining_amount }));
    }
  }, [facture]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.amount <= 0) {
      alert('Le montant doit être supérieur à 0');
      return;
    }
    try {
      await createPayment.mutateAsync({ documentId: factureId, data: form });
      onSaved();
    } catch (error) {
      console.error('Erreur paiement:', error);
    }
  };

  return (
    <PageWrapper
      title="Enregistrer un paiement"
      subtitle={facture?.number}
      backAction={{ label: 'Retour', onClick: onBack }}
    >
      <form onSubmit={handleSubmit}>
        <Card>
          {facture && (
            <div className="azals-alert azals-alert--info mb-4">
              <Euro size={20} />
              <div>
                <strong>Reste à encaisser</strong>
                <p>{formatCurrency(facture.remaining_amount)}</p>
              </div>
            </div>
          )}

          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>Montant *</label>
              <input
                type="number"
                className="azals-input"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: parseFloat(e.target.value) || 0 })}
                min="0"
                step="0.01"
                required
              />
            </div>
            <div className="azals-form-field">
              <label>Date *</label>
              <input
                type="date"
                className="azals-input"
                value={form.date}
                onChange={(e) => setForm({ ...form, date: e.target.value })}
                required
              />
            </div>
            <div className="azals-form-field">
              <label>Mode de paiement</label>
              <select
                className="azals-select"
                value={form.method}
                onChange={(e) => setForm({ ...form, method: e.target.value as PaymentMethod })}
              >
                {Object.entries(PAYMENT_METHODS).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
            <div className="azals-form-field">
              <label>Référence</label>
              <input
                type="text"
                className="azals-input"
                value={form.reference}
                onChange={(e) => setForm({ ...form, reference: e.target.value })}
                placeholder="N° chèque, virement..."
              />
            </div>
            <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
              <label>Notes</label>
              <textarea
                className="azals-textarea"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                rows={2}
              />
            </div>
          </Grid>
        </Card>

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onBack}>Annuler</Button>
          <Button type="submit" isLoading={createPayment.isPending}>Enregistrer le paiement</Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================
// MODULE PRINCIPAL
// ============================================================

export const FacturesModule: React.FC = () => {
  const [navState, setNavState] = useState<FactureNavState>({ view: 'list' });

  React.useEffect(() => {
    const handleNavigate = (event: CustomEvent) => {
      const { params } = event.detail || {};
      if (params?.id) {
        setNavState({ view: 'detail', factureId: params.id });
      } else if (params?.interventionId && params?.action === 'new') {
        // Créer facture depuis intervention
        setNavState({ view: 'form', factureType: 'INVOICE', isNew: true });
      }
    };
    window.addEventListener('azals:navigate:factures', handleNavigate as EventListener);
    return () => window.removeEventListener('azals:navigate:factures', handleNavigate as EventListener);
  }, []);

  const navigateToList = useCallback(() => setNavState({ view: 'list' }), []);
  const navigateToDetail = useCallback((id: string) => setNavState({ view: 'detail', factureId: id }), []);
  const navigateToForm = useCallback((type: FactureType, id?: string) =>
    setNavState({ view: 'form', factureId: id, factureType: type, isNew: !id }), []);
  const navigateToPayment = useCallback((factureId: string) =>
    setNavState({ view: 'payment', factureId }), []);

  switch (navState.view) {
    case 'detail':
      return (
        <FactureDetailInternal
          factureId={navState.factureId!}
          onBack={navigateToList}
          onEdit={() => navigateToForm(navState.factureType || 'INVOICE', navState.factureId)}
          onAddPayment={() => navigateToPayment(navState.factureId!)}
        />
      );
    case 'payment':
      return (
        <PaymentFormInternal
          factureId={navState.factureId!}
          onBack={() => navigateToDetail(navState.factureId!)}
          onSaved={() => navigateToDetail(navState.factureId!)}
        />
      );
    default:
      return (
        <FacturesListInternal
          onSelectFacture={navigateToDetail}
          onCreateFacture={navigateToForm}
        />
      );
  }
};

export default FacturesModule;
