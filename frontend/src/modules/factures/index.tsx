/**
 * AZALSCORE Module - FACTURES & AVOIRS
 * Gestion de la facturation clients avec BaseViewStandard
 * Flux : CRM → DEV → COM/ODS → AFF → [FAC/AVO] → CPT
 * Numérotation : FAC-YY-MM-XXXX / AVO-YY-MM-XXXX
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText, Plus, Edit, Trash2, Search, Check, X, Send,
  Euro, Calendar, Building2, CreditCard, ChevronRight,
  Download, Printer, Clock, CheckCircle2, AlertTriangle,
  ArrowLeftRight, Ban, Package, History, FileArchive, Sparkles
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import {
  BaseViewStandard,
  type TabDefinition,
  type InfoBarItem,
  type SidebarSection,
  type ActionDefinition,
  type StatusDefinition,
  type SemanticColor,
} from '@ui/standards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

// Import types et composants tabs
import type {
  Facture, FactureFormData, Customer, FactureType, FactureStatus,
  PaymentMethod, Payment, PaymentFormData, DocumentLine
} from './types';
import {
  STATUS_CONFIG, TYPE_CONFIG, PAYMENT_METHODS,
  isOverdue, getDaysUntilDue
} from './types';
import { formatCurrency, formatDate } from '@/utils/formatters';
import {
  FactureInfoTab,
  FactureLinesTab,
  FactureFinancialTab,
  FactureDocsTab,
  FactureHistoryTab,
  FactureIATab,
} from './components';

// ============================================================
// API HOOKS
// ============================================================

const useFacturesList = (page = 1, pageSize = 25, filters?: { type?: FactureType; status?: string; search?: string }) => {
  return useQuery({
    queryKey: ['commercial', 'documents', 'factures', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      if (filters?.type) {
        params.append('type', filters.type);
      } else {
        params.append('type', 'INVOICE');
      }
      if (filters?.status) params.append('status', filters.status);
      if (filters?.search) params.append('search', filters.search);
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

const useCreateFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: FactureFormData) => {
      const response = await api.post<Facture>('/v1/commercial/documents', data);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
  });
};

const useValidateFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Facture>(`/v1/commercial/documents/${id}/validate`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
  });
};

const useSendFacture = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Facture>(`/v1/commercial/documents/${id}/send`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
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
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
  });
};

const useCreateAvoir = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (factureId: string) => {
      const response = await api.post<Facture>(`/v1/commercial/documents/${factureId}/credit-note`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
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
// LIST VIEW
// ============================================================

const FactureListView: React.FC<{
  onSelectFacture: (id: string) => void;
  onCreateFacture: (type: FactureType) => void;
}> = ({ onSelectFacture, onCreateFacture }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{ type?: FactureType; status?: string; search?: string }>({});
  const [activeTab, setActiveTab] = useState<'INVOICE' | 'CREDIT_NOTE' | 'ALL'>('INVOICE');

  const { data, isLoading, error, refetch } = useFacturesList(page, pageSize, {
    type: activeTab === 'ALL' ? undefined : activeTab,
    status: filters.status,
    search: filters.search,
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
          {row.type === 'CREDIT_NOTE' && <span className="ml-2"><TypeBadge type={row.type} /></span>}
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
        const factureIsOverdue = isOverdue(row);
        return (
          <span className={factureIsOverdue ? 'text-danger' : ''}>
            {factureIsOverdue && <AlertTriangle size={14} className="mr-1" />}
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
        if (row.status === 'PAID' || row.status === 'CANCELLED' || row.type === 'CREDIT_NOTE') return '-';
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
          error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
          onRetry={() => refetch()}
          emptyMessage="Aucune facture"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// DETAIL VIEW - BaseViewStandard
// ============================================================

const FactureDetailView: React.FC<{
  factureId: string;
  onBack: () => void;
  onEdit: () => void;
  onAddPayment: () => void;
}> = ({ factureId, onBack, onEdit, onAddPayment }) => {
  const { data: facture, isLoading, error, refetch } = useFacture(factureId);
  const { data: payments } = useFacturePayments(factureId);
  const validateFacture = useValidateFacture();
  const sendFacture = useSendFacture();
  const createAvoir = useCreateAvoir();

  // Merge payments into facture data
  const factureWithPayments = useMemo(() => {
    if (!facture) return null;
    return { ...facture, payments: payments || facture.payments };
  }, [facture, payments]);

  const isCreditNote = facture?.type === 'CREDIT_NOTE';
  const isFactureOverdue = facture ? isOverdue(facture) : false;

  // Tab definitions
  const tabs: TabDefinition<Facture>[] = useMemo(() => [
    {
      id: 'info',
      label: 'Informations',
      icon: <FileText size={18} />,
      component: FactureInfoTab,
    },
    {
      id: 'lines',
      label: 'Lignes',
      icon: <Package size={18} />,
      badge: facture?.lines?.length || 0,
      component: FactureLinesTab,
    },
    {
      id: 'financial',
      label: 'Financier',
      icon: <Euro size={18} />,
      component: FactureFinancialTab,
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileArchive size={18} />,
      component: FactureDocsTab,
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <History size={18} />,
      component: FactureHistoryTab,
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={18} />,
      isIA: true,
      component: FactureIATab,
    },
  ], [facture?.lines?.length]);

  // Status mapping
  const statusDef: StatusDefinition | undefined = facture ? {
    label: STATUS_CONFIG[facture.status].label,
    color: STATUS_CONFIG[facture.status].color as SemanticColor,
  } : undefined;

  // Info bar items (KPIs)
  const infoBarItems: InfoBarItem[] = useMemo(() => {
    if (!facture) return [];
    const daysUntilDue = getDaysUntilDue(facture.due_date);

    return [
      {
        id: 'type',
        label: 'Type',
        value: TYPE_CONFIG[facture.type].label,
        icon: <FileText size={16} />,
      },
      {
        id: 'date',
        label: 'Date',
        value: formatDate(facture.date),
        icon: <Calendar size={16} />,
      },
      {
        id: 'due',
        label: 'Échéance',
        value: facture.due_date ? formatDate(facture.due_date) : 'Non définie',
        valueColor: isFactureOverdue ? 'negative' : (daysUntilDue !== null && daysUntilDue <= 7 ? 'warning' : undefined),
        icon: <Clock size={16} />,
      },
      {
        id: 'total',
        label: 'Total TTC',
        value: `${isCreditNote ? '-' : ''}${formatCurrency(facture.total, facture.currency)}`,
        valueColor: isCreditNote ? 'negative' : undefined,
        icon: <Euro size={16} />,
      },
    ];
  }, [facture, isFactureOverdue, isCreditNote]);

  // Sidebar sections
  const sidebarSections: SidebarSection[] = useMemo(() => {
    if (!facture) return [];
    return [
      {
        id: 'totaux',
        title: 'Récapitulatif',
        items: [
          { id: 'subtotal', label: 'Sous-total HT', value: isCreditNote ? -facture.subtotal : facture.subtotal, format: 'currency' },
          ...(facture.discount_amount > 0 ? [{
            id: 'discount',
            label: `Remise (${facture.discount_percent}%)`,
            value: -facture.discount_amount,
            format: 'currency' as const,
          }] : []),
          { id: 'tax', label: 'TVA', value: isCreditNote ? -facture.tax_amount : facture.tax_amount, format: 'currency' },
        ],
        total: { label: 'Total TTC', value: isCreditNote ? -facture.total : facture.total },
      },
      ...(!isCreditNote ? [{
        id: 'paiement',
        title: 'Paiement',
        items: [
          { id: 'paid', label: 'Montant payé', value: facture.paid_amount, format: 'currency' as const },
          { id: 'remaining', label: 'Reste à payer', value: facture.remaining_amount, format: 'currency' as const },
        ],
      }] : []),
      {
        id: 'client',
        title: 'Client',
        items: [
          { id: 'name', label: 'Nom', value: facture.customer_name || '-' },
          { id: 'code', label: 'Code', value: facture.customer_code || '-', secondary: true },
        ],
      },
    ];
  }, [facture, isCreditNote]);

  // Header actions
  const headerActions: ActionDefinition[] = useMemo(() => {
    if (!facture) return [];
    const actions: ActionDefinition[] = [];

    if (facture.status === 'DRAFT') {
      actions.push({
        id: 'edit',
        label: 'Modifier',
        icon: <Edit size={16} />,
        variant: 'ghost',
        onClick: onEdit,
      });
    }

    actions.push({
      id: 'pdf',
      label: 'PDF',
      icon: <Download size={16} />,
      variant: 'ghost',
    });

    actions.push({
      id: 'print',
      label: 'Imprimer',
      icon: <Printer size={16} />,
      variant: 'ghost',
    });

    return actions;
  }, [facture, onEdit]);

  // Primary actions (footer)
  const primaryActions: ActionDefinition[] = useMemo(() => {
    if (!facture) return [];
    const actions: ActionDefinition[] = [];
    const isInvoice = facture.type === 'INVOICE';

    // Encaisser
    if (isInvoice && ['VALIDATED', 'SENT', 'PARTIAL', 'OVERDUE'].includes(facture.status)) {
      actions.push({
        id: 'payment',
        label: 'Encaisser',
        icon: <CreditCard size={16} />,
        variant: 'primary',
        onClick: onAddPayment,
      });
    }

    // Comptabiliser
    if (facture.status === 'PAID') {
      actions.push({
        id: 'comptabiliser',
        label: 'Comptabiliser',
        icon: <ChevronRight size={16} />,
        variant: 'secondary',
        onClick: () => {
          window.dispatchEvent(new CustomEvent('azals:navigate', {
            detail: { view: 'comptabilite', params: { factureId, action: 'comptabiliser' } }
          }));
        },
      });
    }

    // Envoyer
    if (facture.status === 'VALIDATED') {
      actions.push({
        id: 'send',
        label: 'Marquer envoyée',
        icon: <Send size={16} />,
        variant: 'secondary',
        loading: sendFacture.isPending,
        onClick: async () => {
          if (window.confirm('Marquer comme envoyée ?')) {
            await sendFacture.mutateAsync(factureId);
          }
        },
      });
    }

    // Valider
    if (facture.status === 'DRAFT') {
      actions.push({
        id: 'validate',
        label: 'Valider',
        icon: <Check size={16} />,
        variant: 'primary',
        loading: validateFacture.isPending,
        onClick: async () => {
          if (window.confirm('Valider ce document ?')) {
            await validateFacture.mutateAsync(factureId);
          }
        },
      });
    }

    return actions;
  }, [facture, factureId, validateFacture, sendFacture, onAddPayment]);

  // Secondary actions (footer)
  const secondaryActions: ActionDefinition[] = useMemo(() => {
    if (!facture) return [];
    const actions: ActionDefinition[] = [];

    // Créer avoir
    if (facture.type === 'INVOICE' && facture.status === 'PAID') {
      actions.push({
        id: 'avoir',
        label: 'Créer avoir',
        icon: <ArrowLeftRight size={16} />,
        variant: 'ghost',
        loading: createAvoir.isPending,
        onClick: async () => {
          if (window.confirm('Créer un avoir pour cette facture ?')) {
            const avoir = await createAvoir.mutateAsync(factureId);
            window.dispatchEvent(new CustomEvent('azals:navigate', {
              detail: { view: 'factures', params: { id: avoir.id } }
            }));
          }
        },
      });
    }

    actions.push({
      id: 'back',
      label: 'Retour à la liste',
      variant: 'ghost',
      onClick: onBack,
    });

    return actions;
  }, [facture, factureId, createAvoir, onBack]);

  if (!facture && !isLoading) {
    return (
      <PageWrapper title="Document non trouvé">
        <Card>
          <p>Ce document n'existe pas.</p>
          <Button onClick={onBack}>Retour</Button>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <BaseViewStandard<Facture>
      title={facture?.number || 'Chargement...'}
      subtitle={`${facture ? TYPE_CONFIG[facture.type].label : ''} - ${facture?.customer_name || ''}`}
      status={statusDef}
      data={factureWithPayments!}
      view="detail"
      tabs={tabs}
      defaultTab="info"
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      primaryActions={primaryActions}
      secondaryActions={secondaryActions}
      backAction={{ label: 'Retour', onClick: onBack }}
      isLoading={isLoading}
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
    />
  );
};

// ============================================================
// PAYMENT FORM VIEW
// ============================================================

const PaymentFormView: React.FC<{
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
                {Object.entries(PAYMENT_METHODS).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
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

  // Écouter les événements de navigation
  React.useEffect(() => {
    const handleNavigate = (event: CustomEvent) => {
      const { params } = event.detail || {};
      if (params?.id) {
        setNavState({ view: 'detail', factureId: params.id });
      } else if (params?.interventionId && params?.action === 'new') {
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
        <FactureDetailView
          factureId={navState.factureId!}
          onBack={navigateToList}
          onEdit={() => navigateToForm(navState.factureType || 'INVOICE', navState.factureId)}
          onAddPayment={() => navigateToPayment(navState.factureId!)}
        />
      );
    case 'payment':
      return (
        <PaymentFormView
          factureId={navState.factureId!}
          onBack={() => navigateToDetail(navState.factureId!)}
          onSaved={() => navigateToDetail(navState.factureId!)}
        />
      );
    default:
      return (
        <FactureListView
          onSelectFacture={navigateToDetail}
          onCreateFacture={navigateToForm}
        />
      );
  }
};

export default FacturesModule;
