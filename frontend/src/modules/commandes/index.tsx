/**
 * AZALSCORE Module - COMMANDES
 * Gestion des commandes clients avec BaseViewStandard
 * Flux : CRM → DEV → [COM] → AFF → FAC/AVO → CPT
 * Numérotation : COM-YY-MM-XXXX
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ShoppingCart, Plus, Edit, Trash2, Search, Check, X,
  Euro, Calendar, Building2, ChevronRight, FileText,
  Download, Printer, Clock, CheckCircle2, Truck, Package,
  History, FileArchive, Sparkles
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
import type { Commande, CommandeFormData, Customer, DocumentStatus, DocumentLine } from './types';
import { STATUS_CONFIG, formatCurrency, formatDate } from './types';
import {
  CommandeInfoTab,
  CommandeLinesTab,
  CommandeFinancialTab,
  CommandeDocsTab,
  CommandeHistoryTab,
  CommandeIATab,
} from './components';

// ============================================================
// API HOOKS
// ============================================================

const useCommandesList = (page = 1, pageSize = 25, filters?: { status?: string; customer_id?: string; search?: string }) => {
  return useQuery({
    queryKey: ['commercial', 'documents', 'ORDER', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
        type: 'ORDER',
      });
      if (filters?.status) params.append('status', filters.status);
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      if (filters?.search) params.append('search', filters.search);
      const response = await api.get<PaginatedResponse<Commande>>(`/v1/commercial/documents?${params}`);
      return response.data;
    },
  });
};

const useCommande = (id: string) => {
  return useQuery({
    queryKey: ['commercial', 'documents', id],
    queryFn: async () => {
      const response = await api.get<Commande>(`/v1/commercial/documents/${id}`);
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

const useCreateCommande = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: CommandeFormData) => {
      const response = await api.post<Commande>('/v1/commercial/documents', { ...data, type: 'ORDER' });
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
  });
};

const useUpdateCommande = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<CommandeFormData> }) => {
      const response = await api.put<Commande>(`/v1/commercial/documents/${id}`, data);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
  });
};

const useValidateCommande = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Commande>(`/v1/commercial/documents/${id}/validate`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
  });
};

const useMarkDelivered = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Commande>(`/v1/commercial/documents/${id}/deliver`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
  });
};

const useCreateInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (orderId: string) => {
      const response = await api.post<{ id: string; number: string }>(`/v1/commercial/orders/${orderId}/invoice`);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
  });
};

const useCreateAffaire = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (orderId: string) => {
      const response = await api.post<{ id: string; reference: string }>(`/v1/commercial/orders/${orderId}/affaire`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
      queryClient.invalidateQueries({ queryKey: ['affaires'] });
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
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] }),
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

const CommandeStats: React.FC = () => {
  const { data } = useCommandesList(1, 1000);

  const stats = useMemo(() => {
    const items = data?.items || [];
    const enCours = items.filter(c => ['DRAFT', 'PENDING', 'VALIDATED'].includes(c.status)).length;
    const livrees = items.filter(c => c.status === 'DELIVERED').length;
    const facturees = items.filter(c => c.status === 'INVOICED').length;
    const caTotal = items
      .filter(c => !['CANCELLED'].includes(c.status))
      .reduce((sum, c) => sum + c.total, 0);
    return { enCours, livrees, facturees, caTotal };
  }, [data]);

  const kpis: DashboardKPI[] = [
    { id: 'encours', label: 'En cours', value: stats.enCours, icon: <Clock size={20} /> },
    { id: 'livrees', label: 'Livrées', value: stats.livrees, icon: <Truck size={20} /> },
    { id: 'facturees', label: 'Facturées', value: stats.facturees, icon: <FileText size={20} /> },
    { id: 'ca', label: 'CA Total', value: formatCurrency(stats.caTotal), icon: <Euro size={20} /> },
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

type CommandeView = 'list' | 'detail' | 'form';

interface CommandeNavState {
  view: CommandeView;
  commandeId?: string;
  customerId?: string;
  isNew?: boolean;
}

// ============================================================
// LIST VIEW
// ============================================================

const CommandeListView: React.FC<{
  onSelectCommande: (id: string) => void;
  onCreateCommande: (customerId?: string) => void;
}> = ({ onSelectCommande, onCreateCommande }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{ status?: string; search?: string }>({});

  const { data, isLoading, refetch } = useCommandesList(page, pageSize, filters);

  const columns: TableColumn<Commande>[] = [
    {
      id: 'number',
      header: 'N° Commande',
      accessor: 'number',
      sortable: true,
      render: (value, row) => (
        <span className="azals-link" onClick={() => onSelectCommande(row.id)}>{value as string}</span>
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
      id: 'parent',
      header: 'Devis',
      accessor: 'parent_number',
      render: (value) => value ? <span className="text-muted">{value as string}</span> : '-',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => <StatusBadge status={value as DocumentStatus} />,
    },
    {
      id: 'delivery',
      header: 'Livraison',
      accessor: 'delivery_date',
      render: (value) => value ? formatDate(value as string) : '-',
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
      title="Commandes"
      subtitle="Gestion des commandes clients"
      actions={<Button leftIcon={<Plus size={16} />} onClick={() => onCreateCommande()}>Nouvelle commande</Button>}
    >
      <section className="azals-section">
        <CommandeStats />
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
          emptyMessage="Aucune commande"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// DETAIL VIEW - BaseViewStandard
// ============================================================

const CommandeDetailView: React.FC<{
  commandeId: string;
  onBack: () => void;
  onEdit: () => void;
}> = ({ commandeId, onBack, onEdit }) => {
  const { data: commande, isLoading } = useCommande(commandeId);
  const validateCommande = useValidateCommande();
  const markDelivered = useMarkDelivered();
  const createInvoice = useCreateInvoice();
  const createAffaire = useCreateAffaire();

  // Tab definitions
  const tabs: TabDefinition<Commande>[] = useMemo(() => [
    {
      id: 'info',
      label: 'Informations',
      icon: <FileText size={18} />,
      component: CommandeInfoTab,
    },
    {
      id: 'lines',
      label: 'Lignes',
      icon: <Package size={18} />,
      badge: commande?.lines?.length || 0,
      component: CommandeLinesTab,
    },
    {
      id: 'financial',
      label: 'Financier',
      icon: <Euro size={18} />,
      component: CommandeFinancialTab,
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileArchive size={18} />,
      component: CommandeDocsTab,
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <History size={18} />,
      component: CommandeHistoryTab,
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={18} />,
      isIA: true,
      component: CommandeIATab,
    },
  ], [commande?.lines?.length]);

  // Status mapping
  const statusDef: StatusDefinition | undefined = commande ? {
    label: STATUS_CONFIG[commande.status].label,
    color: STATUS_CONFIG[commande.status].color as SemanticColor,
  } : undefined;

  // Info bar items (KPIs)
  const infoBarItems: InfoBarItem[] = useMemo(() => {
    if (!commande) return [];
    return [
      {
        id: 'date',
        label: 'Date',
        value: formatDate(commande.date),
        icon: <Calendar size={16} />,
      },
      {
        id: 'delivery',
        label: 'Livraison',
        value: commande.delivery_date ? formatDate(commande.delivery_date) : 'Non définie',
        valueColor: !commande.delivery_date && commande.status === 'VALIDATED' ? 'warning' : undefined,
        icon: <Truck size={16} />,
      },
      {
        id: 'lines',
        label: 'Lignes',
        value: commande.lines?.length || 0,
        icon: <Package size={16} />,
        secondary: true,
      },
      {
        id: 'total',
        label: 'Total TTC',
        value: formatCurrency(commande.total, commande.currency),
        icon: <Euro size={16} />,
      },
    ];
  }, [commande]);

  // Sidebar sections
  const sidebarSections: SidebarSection[] = useMemo(() => {
    if (!commande) return [];
    return [
      {
        id: 'totaux',
        title: 'Récapitulatif',
        items: [
          { id: 'subtotal', label: 'Sous-total HT', value: commande.subtotal, format: 'currency' },
          ...(commande.shipping_cost > 0 ? [{
            id: 'shipping',
            label: 'Frais de port',
            value: commande.shipping_cost,
            format: 'currency' as const,
          }] : []),
          ...(commande.discount_amount > 0 ? [{
            id: 'discount',
            label: `Remise (${commande.discount_percent}%)`,
            value: -commande.discount_amount,
            format: 'currency' as const,
          }] : []),
          { id: 'tax', label: 'TVA', value: commande.tax_amount, format: 'currency' },
        ],
        total: { label: 'Total TTC', value: commande.total },
      },
      {
        id: 'client',
        title: 'Client',
        items: [
          { id: 'name', label: 'Nom', value: commande.customer_name || '-' },
          { id: 'code', label: 'Code', value: commande.customer_code || '-', secondary: true },
        ],
      },
      ...(commande.parent_number ? [{
        id: 'origine',
        title: 'Origine',
        items: [
          { id: 'devis', label: 'Devis source', value: commande.parent_number },
        ],
      }] : []),
    ];
  }, [commande]);

  // Header actions
  const headerActions: ActionDefinition[] = useMemo(() => {
    if (!commande) return [];
    const actions: ActionDefinition[] = [];

    if (commande.status === 'DRAFT') {
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
  }, [commande, onEdit]);

  // Primary actions (footer)
  const primaryActions: ActionDefinition[] = useMemo(() => {
    if (!commande) return [];
    const actions: ActionDefinition[] = [];

    // Créer facture
    if (['VALIDATED', 'DELIVERED'].includes(commande.status)) {
      actions.push({
        id: 'invoice',
        label: 'Créer facture',
        icon: <FileText size={16} />,
        variant: 'primary',
        loading: createInvoice.isPending,
        onClick: async () => {
          if (window.confirm('Créer une facture pour cette commande ?')) {
            const invoice = await createInvoice.mutateAsync(commandeId);
            window.dispatchEvent(new CustomEvent('azals:navigate', {
              detail: { view: 'factures', params: { id: invoice.id } }
            }));
          }
        },
      });
    }

    // Marquer livrée
    if (commande.status === 'VALIDATED') {
      actions.push({
        id: 'deliver',
        label: 'Marquer livrée',
        icon: <Truck size={16} />,
        variant: 'secondary',
        loading: markDelivered.isPending,
        onClick: async () => {
          if (window.confirm('Marquer cette commande comme livrée ?')) {
            await markDelivered.mutateAsync(commandeId);
          }
        },
      });
    }

    // Valider
    if (commande.status === 'DRAFT') {
      actions.push({
        id: 'validate',
        label: 'Valider',
        icon: <Check size={16} />,
        variant: 'primary',
        loading: validateCommande.isPending,
        onClick: async () => {
          if (window.confirm('Valider cette commande ?')) {
            await validateCommande.mutateAsync(commandeId);
          }
        },
      });
    }

    return actions;
  }, [commande, commandeId, validateCommande, markDelivered, createInvoice]);

  // Secondary actions (footer)
  const secondaryActions: ActionDefinition[] = useMemo(() => {
    if (!commande) return [];
    const actions: ActionDefinition[] = [];

    // Créer affaire
    if (commande.status === 'VALIDATED') {
      actions.push({
        id: 'affaire',
        label: 'Créer affaire',
        icon: <Package size={16} />,
        variant: 'ghost',
        loading: createAffaire.isPending,
        onClick: async () => {
          if (window.confirm('Créer une affaire pour cette commande ?')) {
            const affaire = await createAffaire.mutateAsync(commandeId);
            window.dispatchEvent(new CustomEvent('azals:navigate', {
              detail: { view: 'affaires', params: { id: affaire.id } }
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
  }, [commande, commandeId, createAffaire, onBack]);

  if (!commande && !isLoading) {
    return (
      <PageWrapper title="Commande non trouvée">
        <Card>
          <p>Cette commande n'existe pas.</p>
          <Button onClick={onBack}>Retour</Button>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <BaseViewStandard<Commande>
      title={commande?.number || 'Chargement...'}
      subtitle={commande?.customer_name}
      status={statusDef}
      data={commande!}
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
    />
  );
};

// ============================================================
// FORM VIEW
// ============================================================

const CommandeFormView: React.FC<{
  commandeId?: string;
  customerId?: string;
  onBack: () => void;
  onSaved: (id: string) => void;
}> = ({ commandeId, customerId, onBack, onSaved }) => {
  const isNew = !commandeId;
  const { data: commande } = useCommande(commandeId || '');
  const { data: customers } = useCustomers();
  const createCommande = useCreateCommande();
  const updateCommande = useUpdateCommande();
  const addLine = useAddLine();

  const [form, setForm] = useState<CommandeFormData>({
    customer_id: customerId || '',
    reference: '',
    delivery_date: '',
    shipping_method: '',
    shipping_cost: 0,
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
    if (commande) {
      setForm({
        customer_id: commande.customer_id,
        reference: commande.reference || '',
        delivery_date: commande.delivery_date || '',
        shipping_method: commande.shipping_method || '',
        shipping_cost: commande.shipping_cost || 0,
        notes: commande.notes || '',
        internal_notes: commande.internal_notes || '',
        terms: commande.terms || '',
        discount_percent: commande.discount_percent,
      });
      setLines(commande.lines || []);
    }
  }, [commande]);

  const handleAddLine = () => {
    if (!newLine.description) return;
    setLines([...lines, { ...newLine, line_number: lines.length + 1 }]);
    setNewLine({ description: '', quantity: 1, unit: 'pce', unit_price: 0, discount_percent: 0, tax_rate: 20 });
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
        const result = await createCommande.mutateAsync(form);
        for (const line of lines) {
          await addLine.mutateAsync({ documentId: result.id, data: line });
        }
        onSaved(result.id);
      } else {
        await updateCommande.mutateAsync({ id: commandeId!, data: form });
        onSaved(commandeId!);
      }
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    }
  };

  const isSubmitting = createCommande.isPending || updateCommande.isPending;

  const calculateTotals = () => {
    const subtotal = lines.reduce((sum, line) => {
      const lineTotal = (line.quantity || 0) * (line.unit_price || 0) * (1 - (line.discount_percent || 0) / 100);
      return sum + lineTotal;
    }, 0);
    const shippingCost = form.shipping_cost || 0;
    const discountAmount = subtotal * (form.discount_percent || 0) / 100;
    const taxAmount = lines.reduce((sum, line) => {
      const lineTotal = (line.quantity || 0) * (line.unit_price || 0) * (1 - (line.discount_percent || 0) / 100);
      return sum + lineTotal * (line.tax_rate || 20) / 100;
    }, 0) * (1 - (form.discount_percent || 0) / 100);
    const total = subtotal + shippingCost - discountAmount + taxAmount;
    return { subtotal, shippingCost, discountAmount, taxAmount, total };
  };

  const totals = calculateTotals();

  return (
    <PageWrapper
      title={isNew ? 'Nouvelle commande' : `Modifier ${commande?.number}`}
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

          <Card title="Livraison">
            <div className="azals-form-field">
              <label>Date de livraison</label>
              <input
                type="date"
                className="azals-input"
                value={form.delivery_date}
                onChange={(e) => setForm({ ...form, delivery_date: e.target.value })}
              />
            </div>
            <div className="azals-form-field">
              <label>Mode de livraison</label>
              <input
                type="text"
                className="azals-input"
                value={form.shipping_method}
                onChange={(e) => setForm({ ...form, shipping_method: e.target.value })}
                placeholder="Transporteur, retrait..."
              />
            </div>
            <div className="azals-form-field">
              <label>Frais de port</label>
              <input
                type="number"
                className="azals-input"
                value={form.shipping_cost}
                onChange={(e) => setForm({ ...form, shipping_cost: parseFloat(e.target.value) || 0 })}
                min="0"
                step="0.01"
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
            {totals.shippingCost > 0 && (
              <div className="azals-totals__row">
                <span>Frais de port</span>
                <span>{formatCurrency(totals.shippingCost)}</span>
              </div>
            )}
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
              <label>Notes (visibles sur la commande)</label>
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
          <Button type="submit" isLoading={isSubmitting}>{isNew ? 'Créer la commande' : 'Enregistrer'}</Button>
        </div>
      </form>
    </PageWrapper>
  );
};

// ============================================================
// MODULE PRINCIPAL
// ============================================================

export const CommandesModule: React.FC = () => {
  const [navState, setNavState] = useState<CommandeNavState>({ view: 'list' });

  // Écouter les événements de navigation
  React.useEffect(() => {
    const handleNavigate = (event: CustomEvent) => {
      const { params } = event.detail || {};
      if (params?.customerId && params?.action === 'new') {
        setNavState({ view: 'form', customerId: params.customerId, isNew: true });
      } else if (params?.id) {
        setNavState({ view: 'detail', commandeId: params.id });
      }
    };
    window.addEventListener('azals:navigate:commandes', handleNavigate as EventListener);
    return () => window.removeEventListener('azals:navigate:commandes', handleNavigate as EventListener);
  }, []);

  const navigateToList = useCallback(() => setNavState({ view: 'list' }), []);
  const navigateToDetail = useCallback((id: string) => setNavState({ view: 'detail', commandeId: id }), []);
  const navigateToForm = useCallback((id?: string, customerId?: string) =>
    setNavState({ view: 'form', commandeId: id, customerId, isNew: !id }), []);

  switch (navState.view) {
    case 'detail':
      return (
        <CommandeDetailView
          commandeId={navState.commandeId!}
          onBack={navigateToList}
          onEdit={() => navigateToForm(navState.commandeId)}
        />
      );
    case 'form':
      return (
        <CommandeFormView
          commandeId={navState.commandeId}
          customerId={navState.customerId}
          onBack={navState.isNew ? navigateToList : () => navigateToDetail(navState.commandeId!)}
          onSaved={navigateToDetail}
        />
      );
    default:
      return (
        <CommandeListView
          onSelectCommande={navigateToDetail}
          onCreateCommande={(customerId) => navigateToForm(undefined, customerId)}
        />
      );
  }
};

export default CommandesModule;
