/**
 * AZALSCORE Module - COMMANDES
 * Gestion des commandes clients avec BaseViewStandard
 * Flux : CRM → DEV → [COM] → AFF → FAC/AVO → CPT
 * Numérotation : COM-YY-MM-XXXX
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  Plus, Edit, Trash2, Check,
  Euro, Calendar, FileText,
  Download, Printer, Clock, Truck, Package,
  History, FileArchive, Sparkles
} from 'lucide-react';
import { Button } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import { PageWrapper, Card, Grid } from '@ui/layout';
import {
  BaseViewStandard,
  type TabDefinition,
  type InfoBarItem,
  type SidebarSection,
  type ActionDefinition,
  type StatusDefinition,
  type SemanticColor,
} from '@ui/standards';
import { DataTable } from '@ui/tables';
import { SmartSelector } from '@/components/SmartSelector';
import type { TableColumn, DashboardKPI } from '@/types';

// Internal imports
import { formatCurrency, formatDate } from '@/utils/formatters';
import {
  CommandeInfoTab,
  CommandeLinesTab,
  CommandeFinancialTab,
  CommandeDocsTab,
  CommandeHistoryTab,
  CommandeIATab,
} from './components';
import { STATUS_CONFIG } from './types';
import type { Commande, CommandeFormData, DocumentStatus, DocumentLine } from './types';

// Hooks
import {
  useCommandesList,
  useCommande,
  useCustomers,
  useCreateCommande,
  useUpdateCommande,
  useValidateCommande,
  useMarkDelivered,
  useCreateInvoice,
  useCreateAffaire,
  useAddLine,
} from './hooks';

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
    { id: 'livrees', label: 'Livrees', value: stats.livrees, icon: <Truck size={20} /> },
    { id: 'facturees', label: 'Facturees', value: stats.facturees, icon: <FileText size={20} /> },
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

  const { data, isLoading, error, refetch } = useCommandesList(page, pageSize, filters);

  const columns: TableColumn<Commande>[] = [
    {
      id: 'number', header: 'N Commande', accessor: 'number', sortable: true,
      render: (value, row) => <span className="azals-link" onClick={() => onSelectCommande(row.id)}>{value as string}</span>,
    },
    { id: 'date', header: 'Date', accessor: 'date', render: (value) => formatDate(value as string) },
    { id: 'customer', header: 'Client', accessor: 'customer_name' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (value) => <StatusBadge status={value as DocumentStatus} /> },
    { id: 'total', header: 'Total TTC', accessor: 'total', align: 'right', render: (value) => formatCurrency(value as number) },
    { id: 'delivery', header: 'Livraison', accessor: 'delivery_date', render: (value) => value ? formatDate(value as string) : '-' },
  ];

  return (
    <PageWrapper
      title="Commandes"
      subtitle="Gestion des commandes clients"
      actions={<Button leftIcon={<Plus size={16} />} onClick={() => onCreateCommande()}>Nouvelle commande</Button>}
    >
      <CommandeStats />
      <Card noPadding className="mt-4">
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          filterable
          isLoading={isLoading}
          error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
          pagination={{ page, pageSize, total: data?.total || 0, onPageChange: setPage, onPageSizeChange: setPageSize }}
          onRefresh={refetch}
          onRetry={() => refetch()}
          emptyMessage="Aucune commande"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// DETAIL VIEW
// ============================================================

const CommandeDetailView: React.FC<{
  commandeId: string;
  onBack: () => void;
  onEdit: () => void;
}> = ({ commandeId, onBack, onEdit }) => {
  const { data: commande, isLoading, error, refetch } = useCommande(commandeId);
  const validateCommande = useValidateCommande();
  const markDelivered = useMarkDelivered();
  const createInvoice = useCreateInvoice();
  const createAffaire = useCreateAffaire();

  const statusDef: StatusDefinition = useMemo(() => {
    if (!commande) return { label: '-', color: 'gray' };
    const config = STATUS_CONFIG[commande.status];
    return { label: config.label, color: config.color as SemanticColor, icon: config.icon };
  }, [commande]);

  const tabs: TabDefinition<Commande>[] = [
    { id: 'info', label: 'Informations', icon: <FileText size={16} />, component: CommandeInfoTab },
    { id: 'lines', label: 'Lignes', icon: <Package size={16} />, badge: commande?.lines?.length, component: CommandeLinesTab },
    { id: 'financial', label: 'Financier', icon: <Euro size={16} />, component: CommandeFinancialTab },
    { id: 'docs', label: 'Documents', icon: <FileArchive size={16} />, badge: commande?.attachments?.length, component: CommandeDocsTab },
    { id: 'history', label: 'Historique', icon: <History size={16} />, component: CommandeHistoryTab },
    { id: 'ia', label: 'IA', icon: <Sparkles size={16} />, component: CommandeIATab },
  ];

  const infoBarItems: InfoBarItem[] = useMemo(() => {
    if (!commande) return [];
    return [
      { id: 'total', label: 'Total TTC', value: formatCurrency(commande.total), valueColor: 'blue' as SemanticColor },
      { id: 'date', label: 'Date', value: formatDate(commande.date), icon: <Calendar size={14} /> },
      { id: 'delivery', label: 'Livraison', value: commande.delivery_date ? formatDate(commande.delivery_date) : 'Non definie', icon: <Truck size={14} /> },
    ];
  }, [commande]);

  const sidebarSections: SidebarSection[] = useMemo(() => {
    if (!commande) return [];
    return [
      {
        id: 'client', title: 'Client',
        items: [
          { id: 'name', label: 'Nom', value: commande.customer_name || '-' },
          { id: 'ref', label: 'Reference', value: commande.reference || '-' },
        ],
      },
      {
        id: 'montants', title: 'Montants',
        items: [
          { id: 'ht', label: 'Total HT', value: formatCurrency(commande.subtotal) },
          { id: 'tva', label: 'TVA', value: formatCurrency(commande.tax_amount) },
          { id: 'ttc', label: 'Total TTC', value: formatCurrency(commande.total), highlight: true },
        ],
      },
    ];
  }, [commande]);

  const primaryActions: ActionDefinition[] = useMemo(() => {
    if (!commande) return [];
    const actions: ActionDefinition[] = [];

    if (commande.status === 'DRAFT') {
      actions.push({
        id: 'validate', label: 'Valider', variant: 'primary', icon: <Check size={16} />,
        onClick: async () => { await validateCommande.mutateAsync(commandeId); },
      });
    }

    if (commande.status === 'VALIDATED') {
      actions.push({
        id: 'deliver', label: 'Marquer livre', variant: 'success', icon: <Truck size={16} />,
        onClick: async () => { await markDelivered.mutateAsync(commandeId); },
      });
    }

    if (commande.status === 'DELIVERED') {
      actions.push({
        id: 'invoice', label: 'Facturer', variant: 'primary', icon: <FileText size={16} />,
        onClick: async () => { await createInvoice.mutateAsync(commandeId); },
      });
    }

    return actions;
  }, [commande, commandeId, validateCommande, markDelivered, createInvoice]);

  const secondaryActions: ActionDefinition[] = useMemo(() => {
    if (!commande) return [];
    const actions: ActionDefinition[] = [
      { id: 'pdf', label: 'Telecharger PDF', icon: <Download size={16} />, onClick: () => {} },
      { id: 'print', label: 'Imprimer', icon: <Printer size={16} />, onClick: () => {} },
    ];

    if (['VALIDATED', 'DELIVERED'].includes(commande.status) && !commande.affaire_id) {
      actions.push({
        id: 'affaire', label: 'Creer affaire', icon: <Package size={16} />,
        onClick: async () => { await createAffaire.mutateAsync(commandeId); },
      });
    }

    return actions;
  }, [commande, commandeId, createAffaire]);

  const headerActions: ActionDefinition[] = useMemo(() => {
    const actions: ActionDefinition[] = [];
    if (commande?.status === 'DRAFT') {
      actions.push({ id: 'edit', label: 'Modifier', icon: <Edit size={16} />, onClick: onEdit });
    }
    actions.push({ id: 'back', label: 'Retour a la liste', variant: 'ghost', onClick: onBack });
    return actions;
  }, [commande, onBack, onEdit]);

  if (!commande && !isLoading) {
    return (
      <PageWrapper title="Commande non trouvee">
        <Card><p>Cette commande n'existe pas.</p><Button onClick={onBack}>Retour</Button></Card>
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
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
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
    description: '', quantity: 1, unit: 'pce', unit_price: 0, discount_percent: 0, tax_rate: 20,
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

  const handleRemoveLine = (index: number) => setLines(lines.filter((_, i) => i !== index));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.customer_id) { alert('Veuillez selectionner un client'); return; }
    try {
      if (isNew) {
        const result = await createCommande.mutateAsync(form);
        for (const line of lines) await addLine.mutateAsync({ documentId: result.id, data: line });
        onSaved(result.id);
      } else {
        await updateCommande.mutateAsync({ id: commandeId!, data: form });
        onSaved(commandeId!);
      }
    } catch (error) { console.error('Erreur sauvegarde:', error); }
  };

  const isSubmitting = createCommande.isPending || updateCommande.isPending;

  const totals = useMemo(() => {
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
  }, [lines, form.shipping_cost, form.discount_percent]);

  return (
    <PageWrapper title={isNew ? 'Nouvelle commande' : `Modifier ${commande?.number}`} backAction={{ label: 'Retour', onClick: onBack }}>
      <form onSubmit={handleSubmit}>
        <Grid cols={2} gap="lg">
          <Card title="Client">
            <SmartSelector
              items={customers || []}
              value={form.customer_id}
              onChange={(id) => setForm({ ...form, customer_id: id })}
              label="Client"
              placeholder="Rechercher un client..."
              entityName="client"
              createEndpoint="/commercial/customers"
              createFields={[
                { key: 'name', label: 'Nom', required: true },
                { key: 'email', label: 'Email', type: 'email' },
                { key: 'phone', label: 'Telephone', type: 'tel' },
              ]}
              queryKeys={['customers']}
              allowCreate={true}
            />
            <div className="azals-form-field">
              <label>Reference client</label>
              <input type="text" className="azals-input" value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} placeholder="Votre reference..." />
            </div>
          </Card>

          <Card title="Livraison">
            <div className="azals-form-field">
              <label>Date de livraison</label>
              <input type="date" className="azals-input" value={form.delivery_date} onChange={(e) => setForm({ ...form, delivery_date: e.target.value })} />
            </div>
            <div className="azals-form-field">
              <label>Mode de livraison</label>
              <input type="text" className="azals-input" value={form.shipping_method} onChange={(e) => setForm({ ...form, shipping_method: e.target.value })} placeholder="Transporteur, retrait..." />
            </div>
            <div className="azals-form-field">
              <label>Frais de port</label>
              <input type="number" className="azals-input" value={form.shipping_cost} onChange={(e) => setForm({ ...form, shipping_cost: parseFloat(e.target.value) || 0 })} min="0" step="0.01" />
            </div>
          </Card>
        </Grid>

        <Card title="Lignes" className="mt-4">
          {lines.length > 0 && (
            <table className="azals-table azals-table--simple mb-4">
              <thead>
                <tr>
                  <th>Description</th>
                  <th className="text-right">Qte</th>
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
                    <td className="text-right">{formatCurrency((line.quantity || 0) * (line.unit_price || 0) * (1 - (line.discount_percent || 0) / 100))}</td>
                    <td><Button variant="ghost" size="sm" onClick={() => handleRemoveLine(index)}><Trash2 size={14} /></Button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="azals-add-line">
            <Grid cols={4} gap="sm">
              <div className="azals-form-field" style={{ gridColumn: 'span 2' }}>
                <input type="text" className="azals-input" placeholder="Description..." value={newLine.description} onChange={(e) => setNewLine({ ...newLine, description: e.target.value })} />
              </div>
              <div className="azals-form-field">
                <input type="number" className="azals-input" placeholder="Qte" value={newLine.quantity} onChange={(e) => setNewLine({ ...newLine, quantity: parseFloat(e.target.value) || 1 })} min="0" step="0.01" />
              </div>
              <div className="azals-form-field">
                <input type="number" className="azals-input" placeholder="P.U. HT" value={newLine.unit_price} onChange={(e) => setNewLine({ ...newLine, unit_price: parseFloat(e.target.value) || 0 })} min="0" step="0.01" />
              </div>
              <div className="azals-form-field">
                <select className="azals-select" value={newLine.tax_rate} onChange={(e) => setNewLine({ ...newLine, tax_rate: parseFloat(e.target.value) })}>
                  <option value="20">20%</option>
                  <option value="10">10%</option>
                  <option value="5.5">5.5%</option>
                  <option value="0">0%</option>
                </select>
              </div>
              <div><Button type="button" variant="secondary" onClick={handleAddLine}><Plus size={16} /></Button></div>
            </Grid>
          </div>

          <div className="azals-totals mt-4">
            <div className="azals-totals__row"><span>Sous-total HT</span><span>{formatCurrency(totals.subtotal)}</span></div>
            {totals.shippingCost > 0 && <div className="azals-totals__row"><span>Frais de port</span><span>{formatCurrency(totals.shippingCost)}</span></div>}
            {totals.discountAmount > 0 && <div className="azals-totals__row"><span>Remise ({form.discount_percent}%)</span><span>-{formatCurrency(totals.discountAmount)}</span></div>}
            <div className="azals-totals__row"><span>TVA</span><span>{formatCurrency(totals.taxAmount)}</span></div>
            <div className="azals-totals__row azals-totals__row--total"><span>Total TTC</span><span>{formatCurrency(totals.total)}</span></div>
          </div>
        </Card>

        <Card title="Notes" className="mt-4">
          <Grid cols={2} gap="md">
            <div className="azals-form-field">
              <label>Notes (visibles sur la commande)</label>
              <textarea className="azals-textarea" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={3} />
            </div>
            <div className="azals-form-field">
              <label>Conditions</label>
              <textarea className="azals-textarea" value={form.terms} onChange={(e) => setForm({ ...form, terms: e.target.value })} rows={3} placeholder="Conditions de paiement, delais..." />
            </div>
          </Grid>
        </Card>

        <div className="azals-form-actions">
          <Button type="button" variant="ghost" onClick={onBack}>Annuler</Button>
          <Button type="submit" isLoading={isSubmitting}>{isNew ? 'Creer la commande' : 'Enregistrer'}</Button>
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
      return <CommandeDetailView commandeId={navState.commandeId!} onBack={navigateToList} onEdit={() => navigateToForm(navState.commandeId)} />;
    case 'form':
      return <CommandeFormView commandeId={navState.commandeId} customerId={navState.customerId} onBack={navState.isNew ? navigateToList : () => navigateToDetail(navState.commandeId!)} onSaved={navigateToDetail} />;
    default:
      return <CommandeListView onSelectCommande={navigateToDetail} onCreateCommande={(customerId) => navigateToForm(undefined, customerId)} />;
  }
};

// Re-exports
export * from './types';
export * from './hooks';
export default CommandesModule;
