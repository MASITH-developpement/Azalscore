/**
 * AZALSCORE Module - COMMANDES
 * Gestion des commandes clients
 * Flux : CRM → DEV → [COM] → AFF → FAC/AVO → CPT
 * Numérotation : COM-YY-MM-XXXX
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ShoppingCart, Plus, Edit, Trash2, Search, Check, X,
  Euro, Calendar, Building2, ChevronRight, FileText,
  Download, Printer, Clock, CheckCircle2, Truck, Package
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

type DocumentStatus = 'DRAFT' | 'PENDING' | 'VALIDATED' | 'DELIVERED' | 'INVOICED' | 'CANCELLED';

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

interface Commande {
  id: string;
  number: string; // COM-YY-MM-XXXX
  reference?: string;
  status: DocumentStatus;
  customer_id: string;
  customer_name?: string;
  customer_code?: string;
  parent_id?: string; // ID du devis source
  parent_number?: string;
  date: string;
  delivery_date?: string;
  billing_address?: Record<string, string>;
  shipping_address?: Record<string, string>;
  subtotal: number;
  discount_amount: number;
  discount_percent: number;
  tax_amount: number;
  total: number;
  currency: string;
  shipping_method?: string;
  shipping_cost: number;
  tracking_number?: string;
  notes?: string;
  internal_notes?: string;
  lines: DocumentLine[];
  pdf_url?: string;
  assigned_to?: string;
  validated_by?: string;
  validated_at?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

interface Customer {
  id: string;
  code: string;
  name: string;
  legal_name?: string;
  email?: string;
  phone?: string;
}

// ============================================================
// CONSTANTS
// ============================================================

const STATUS_CONFIG: Record<DocumentStatus, { label: string; color: string; icon: React.ReactNode }> = {
  DRAFT: { label: 'Brouillon', color: 'gray', icon: <Edit size={14} /> },
  PENDING: { label: 'En attente', color: 'yellow', icon: <Clock size={14} /> },
  VALIDATED: { label: 'Validée', color: 'blue', icon: <Check size={14} /> },
  DELIVERED: { label: 'Livrée', color: 'green', icon: <Truck size={14} /> },
  INVOICED: { label: 'Facturée', color: 'purple', icon: <FileText size={14} /> },
  CANCELLED: { label: 'Annulée', color: 'red', icon: <X size={14} /> },
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

const useCommandesList = (page = 1, pageSize = 25, filters?: { status?: string; customer_id?: string }) => {
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

const useCustomers = () => {
  return useQuery({
    queryKey: ['commercial', 'customers', 'all'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Customer>>('/v1/commercial/customers?page_size=100');
      return response.data.items;
    },
  });
};

const useCreateCommande = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Commande>) => {
      const response = await api.post<Commande>('/v1/commercial/documents', {
        ...data,
        type: 'ORDER',
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useUpdateCommande = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: Partial<Commande> }) => {
      const response = await api.put<Commande>(`/v1/commercial/documents/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useValidateCommande = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await api.post<Commande>(`/v1/commercial/documents/${id}/validate`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
  });
};

const useCreateInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (orderId: string) => {
      const response = await api.post<{ id: string; number: string }>(`/v1/commercial/orders/${orderId}/invoice`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commercial', 'documents'] });
    },
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
// LIST
// ============================================================

const CommandesListInternal: React.FC<{
  onSelectCommande: (id: string) => void;
  onCreateCommande: () => void;
}> = ({ onSelectCommande, onCreateCommande }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data, isLoading, refetch } = useCommandesList(page, pageSize, { status: statusFilter || undefined });

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
      actions={<Button leftIcon={<Plus size={16} />} onClick={onCreateCommande}>Nouvelle commande</Button>}
    >
      <section className="azals-section">
        <CommandeStats />
      </section>

      <Card noPadding>
        <div className="azals-filter-bar">
          <div className="azals-filter-bar__search">
            <Search size={16} />
            <input type="text" placeholder="Rechercher..." className="azals-input" />
          </div>
          <select
            className="azals-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
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
// DETAIL
// ============================================================

const CommandeDetailInternal: React.FC<{
  commandeId: string;
  onBack: () => void;
  onEdit: () => void;
}> = ({ commandeId, onBack, onEdit }) => {
  const { data: commande, isLoading } = useCommande(commandeId);
  const validateCommande = useValidateCommande();
  const createInvoice = useCreateInvoice();
  const createAffaire = useCreateAffaire();

  const handleValidate = async () => {
    if (window.confirm('Valider cette commande ?')) {
      await validateCommande.mutateAsync(commandeId);
    }
  };

  const handleCreateInvoice = async () => {
    if (window.confirm('Créer une facture pour cette commande ?')) {
      try {
        const invoice = await createInvoice.mutateAsync(commandeId);
        window.dispatchEvent(new CustomEvent('azals:navigate', {
          detail: { view: 'factures', params: { id: invoice.id } }
        }));
      } catch (error) {
        console.error('Erreur création facture:', error);
      }
    }
  };

  const handleCreateAffaire = async () => {
    if (window.confirm('Créer une affaire pour cette commande ?')) {
      try {
        const affaire = await createAffaire.mutateAsync(commandeId);
        window.dispatchEvent(new CustomEvent('azals:navigate', {
          detail: { view: 'affaires', params: { id: affaire.id } }
        }));
      } catch (error) {
        console.error('Erreur création affaire:', error);
      }
    }
  };

  if (isLoading) {
    return <PageWrapper title="Chargement..."><div className="azals-loading">Chargement...</div></PageWrapper>;
  }

  if (!commande) {
    return (
      <PageWrapper title="Commande non trouvée">
        <Card><p>Cette commande n'existe pas.</p><Button onClick={onBack}>Retour</Button></Card>
      </PageWrapper>
    );
  }

  const canEdit = commande.status === 'DRAFT';
  const canValidate = commande.status === 'DRAFT';
  const canInvoice = ['VALIDATED', 'DELIVERED'].includes(commande.status);
  const canCreateAffaire = commande.status === 'VALIDATED';

  return (
    <PageWrapper
      title={commande.number}
      subtitle={commande.customer_name}
      backAction={{ label: 'Retour', onClick: onBack }}
      actions={
        <ButtonGroup>
          {canInvoice && (
            <Button leftIcon={<FileText size={16} />} onClick={handleCreateInvoice} isLoading={createInvoice.isPending}>
              Créer facture
            </Button>
          )}
          {canCreateAffaire && (
            <Button variant="secondary" leftIcon={<Package size={16} />} onClick={handleCreateAffaire} isLoading={createAffaire.isPending}>
              Créer affaire
            </Button>
          )}
          {canValidate && (
            <Button variant="secondary" leftIcon={<Check size={16} />} onClick={handleValidate} isLoading={validateCommande.isPending}>
              Valider
            </Button>
          )}
          {canEdit && (
            <Button variant="ghost" leftIcon={<Edit size={16} />} onClick={onEdit}>Modifier</Button>
          )}
          <Button variant="ghost" leftIcon={<Download size={16} />}>PDF</Button>
        </ButtonGroup>
      }
    >
      <Grid cols={4} gap="md" className="mb-4">
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Statut</span>
            <StatusBadge status={commande.status} />
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Date</span>
            <span className="azals-stat__value">{formatDate(commande.date)}</span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Livraison prévue</span>
            <span className="azals-stat__value">{commande.delivery_date ? formatDate(commande.delivery_date) : '-'}</span>
          </div>
        </Card>
        <Card>
          <div className="azals-stat">
            <span className="azals-stat__label">Total TTC</span>
            <span className="azals-stat__value azals-stat__value--large">{formatCurrency(commande.total)}</span>
          </div>
        </Card>
      </Grid>

      {commande.parent_number && (
        <div className="azals-alert azals-alert--info mb-4">
          <FileText size={20} />
          <div>
            <strong>Issue du devis</strong>
            <p>{commande.parent_number}</p>
          </div>
        </div>
      )}

      <Grid cols={2} gap="lg" className="mb-4">
        <Card title="Client">
          <dl className="azals-dl">
            <dt><Building2 size={14} /> Client</dt>
            <dd>
              <strong>{commande.customer_name}</strong>
              {commande.customer_code && <span className="text-muted"> ({commande.customer_code})</span>}
            </dd>
            {commande.shipping_address && (
              <>
                <dt><Truck size={14} /> Adresse livraison</dt>
                <dd>
                  {commande.shipping_address.line1 && <div>{commande.shipping_address.line1}</div>}
                  {commande.shipping_address.city && <div>{commande.shipping_address.postal_code} {commande.shipping_address.city}</div>}
                </dd>
              </>
            )}
          </dl>
        </Card>

        <Card title="Livraison">
          <dl className="azals-dl">
            {commande.shipping_method && <><dt>Mode</dt><dd>{commande.shipping_method}</dd></>}
            {commande.tracking_number && <><dt>N° suivi</dt><dd>{commande.tracking_number}</dd></>}
            {commande.shipping_cost > 0 && <><dt>Frais de port</dt><dd>{formatCurrency(commande.shipping_cost)}</dd></>}
          </dl>
        </Card>
      </Grid>

      <Card title="Lignes de commande">
        {commande.lines && commande.lines.length > 0 ? (
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
              {commande.lines.map(line => (
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
                <td className="text-right">{formatCurrency(commande.subtotal)}</td>
              </tr>
              {commande.shipping_cost > 0 && (
                <tr>
                  <td colSpan={4} className="text-right">Frais de port</td>
                  <td className="text-right">{formatCurrency(commande.shipping_cost)}</td>
                </tr>
              )}
              <tr>
                <td colSpan={4} className="text-right">TVA</td>
                <td className="text-right">{formatCurrency(commande.tax_amount)}</td>
              </tr>
              <tr className="azals-table__total">
                <td colSpan={4} className="text-right"><strong>Total TTC</strong></td>
                <td className="text-right"><strong>{formatCurrency(commande.total)}</strong></td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <p className="text-muted text-center py-4">Aucune ligne</p>
        )}
      </Card>

      {canInvoice && (
        <Card className="mt-4">
          <div className="azals-action-card">
            <div>
              <h4>Prochaine étape</h4>
              <p className="text-muted">Cette commande peut être facturée</p>
            </div>
            <ButtonGroup>
              <Button leftIcon={<FileText size={16} />} onClick={handleCreateInvoice}>
                Créer facture
              </Button>
              {canCreateAffaire && (
                <Button variant="secondary" leftIcon={<Package size={16} />} onClick={handleCreateAffaire}>
                  Créer affaire
                </Button>
              )}
            </ButtonGroup>
          </div>
        </Card>
      )}
    </PageWrapper>
  );
};

// ============================================================
// FORM
// ============================================================

const CommandeFormInternal: React.FC<{
  commandeId?: string;
  onBack: () => void;
  onSaved: (id: string) => void;
}> = ({ commandeId, onBack, onSaved }) => {
  const isNew = !commandeId;
  const { data: commande } = useCommande(commandeId || '');
  const { data: customers } = useCustomers();
  const createCommande = useCreateCommande();
  const updateCommande = useUpdateCommande();

  const [form, setForm] = useState({
    customer_id: '',
    reference: '',
    delivery_date: '',
    shipping_method: '',
    notes: '',
  });

  const [lines, setLines] = useState<Partial<DocumentLine>[]>([]);
  const [newLine, setNewLine] = useState({
    description: '',
    quantity: 1,
    unit: 'pce',
    unit_price: 0,
    tax_rate: 20,
  });

  React.useEffect(() => {
    if (commande) {
      setForm({
        customer_id: commande.customer_id,
        reference: commande.reference || '',
        delivery_date: commande.delivery_date || '',
        shipping_method: commande.shipping_method || '',
        notes: commande.notes || '',
      });
      setLines(commande.lines || []);
    }
  }, [commande]);

  const handleAddLine = () => {
    if (!newLine.description) return;
    setLines([...lines, { ...newLine, line_number: lines.length + 1 }]);
    setNewLine({ description: '', quantity: 1, unit: 'pce', unit_price: 0, tax_rate: 20 });
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
        const result = await createCommande.mutateAsync(form as any);
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

  const totals = useMemo(() => {
    const subtotal = lines.reduce((sum, line) => sum + (line.quantity || 0) * (line.unit_price || 0), 0);
    const taxAmount = lines.reduce((sum, line) => {
      const lineTotal = (line.quantity || 0) * (line.unit_price || 0);
      return sum + lineTotal * (line.tax_rate || 20) / 100;
    }, 0);
    return { subtotal, taxAmount, total: subtotal + taxAmount };
  }, [lines]);

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
                <option value="">-- Sélectionner --</option>
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
                  <th className="text-right">TVA</th>
                  <th className="text-right">Total HT</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {lines.map((line, index) => (
                  <tr key={index}>
                    <td>{line.description}</td>
                    <td className="text-right">{line.quantity}</td>
                    <td className="text-right">{formatCurrency(line.unit_price || 0)}</td>
                    <td className="text-right">{line.tax_rate}%</td>
                    <td className="text-right">{formatCurrency((line.quantity || 0) * (line.unit_price || 0))}</td>
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
                />
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

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onBack}>Annuler</Button>
          <Button type="submit" isLoading={isSubmitting}>{isNew ? 'Créer' : 'Enregistrer'}</Button>
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

  React.useEffect(() => {
    const handleNavigate = (event: CustomEvent) => {
      const { params } = event.detail || {};
      if (params?.id) {
        setNavState({ view: 'detail', commandeId: params.id });
      }
    };
    window.addEventListener('azals:navigate:commandes', handleNavigate as EventListener);
    return () => window.removeEventListener('azals:navigate:commandes', handleNavigate as EventListener);
  }, []);

  const navigateToList = useCallback(() => setNavState({ view: 'list' }), []);
  const navigateToDetail = useCallback((id: string) => setNavState({ view: 'detail', commandeId: id }), []);
  const navigateToForm = useCallback((id?: string) => setNavState({ view: 'form', commandeId: id, isNew: !id }), []);

  switch (navState.view) {
    case 'detail':
      return (
        <CommandeDetailInternal
          commandeId={navState.commandeId!}
          onBack={navigateToList}
          onEdit={() => navigateToForm(navState.commandeId)}
        />
      );
    case 'form':
      return (
        <CommandeFormInternal
          commandeId={navState.commandeId}
          onBack={navState.isNew ? navigateToList : () => navigateToDetail(navState.commandeId!)}
          onSaved={navigateToDetail}
        />
      );
    default:
      return (
        <CommandesListInternal
          onSelectCommande={navigateToDetail}
          onCreateCommande={() => navigateToForm()}
        />
      );
  }
};

export default CommandesModule;
