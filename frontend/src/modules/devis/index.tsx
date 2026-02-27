/**
 * AZALSCORE Module - DEVIS
 * Gestion des devis clients avec BaseViewStandard
 * Flux : CRM → [DEV] → COM/ODS → AFF → FAC/AVO → CPT
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  FileText, Plus, Edit, Trash2, Search, Send, Check,
  Euro, Calendar, Clock, AlertTriangle, CheckCircle2,
  ChevronRight, Download, Printer, Package, History,
  FileArchive, Sparkles
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
import { formatCurrency, formatDate } from '@/utils/formatters';

// Module imports
import {
  useDevisList,
  useDevis,
  useCustomers,
  useCreateDevis,
  useUpdateDevis,
  useValidateDevis,
  useSendDevis,
  useConvertToOrder,
  useAddLine,
} from './hooks';
import {
  DevisInfoTab, DevisLinesTab, DevisFinancialTab,
  DevisDocsTab, DevisHistoryTab, DevisIATab,
} from './components';
import { STATUS_CONFIG } from './types';
import type { Devis, DevisFormData, DocumentStatus, DocumentLine } from './types';

// ============================================================
// COMPONENTS
// ============================================================

const StatusBadge: React.FC<{ status: DocumentStatus }> = ({ status }) => {
  const config = STATUS_CONFIG[status] || { label: status, color: 'gray' };
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
    const totalEnCours = items.filter(d => !['ACCEPTED', 'REJECTED', 'CANCELLED'].includes(d.status)).reduce((sum, d) => sum + d.total, 0);
    return { brouillons, enAttente, acceptes, totalEnCours };
  }, [devisData]);

  const kpis: DashboardKPI[] = [
    { id: 'brouillons', label: 'Brouillons', value: stats.brouillons, icon: <Edit size={20} /> },
    { id: 'attente', label: 'En attente', value: stats.enAttente, icon: <Clock size={20} /> },
    { id: 'acceptes', label: 'Acceptés', value: stats.acceptes, icon: <CheckCircle2 size={20} /> },
    { id: 'total', label: 'En cours', value: formatCurrency(stats.totalEnCours), icon: <Euro size={20} /> },
  ];

  return <Grid cols={4} gap="md">{kpis.map(kpi => <KPICard key={kpi.id} kpi={kpi} />)}</Grid>;
};

// ============================================================
// LIST VIEW
// ============================================================

const DevisListView: React.FC<{
  onSelectDevis: (id: string) => void;
  onCreateDevis: (customerId?: string) => void;
}> = ({ onSelectDevis, onCreateDevis }) => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [filters, setFilters] = useState<{ status?: string; search?: string }>({});
  const { data, isLoading, error, refetch } = useDevisList(page, pageSize, filters);

  const columns: TableColumn<Devis>[] = [
    { id: 'number', header: 'N° Devis', accessor: 'number', sortable: true, render: (value, row) => <span className="azals-link" onClick={() => onSelectDevis(row.id)}>{value as string}</span> },
    { id: 'date', header: 'Date', accessor: 'date', sortable: true, render: (value) => formatDate(value as string) },
    { id: 'customer', header: 'Client', accessor: 'customer_name', render: (value, row) => <div><div>{value as string}</div><div className="text-muted text-sm">{row.customer_code}</div></div> },
    { id: 'reference', header: 'Référence', accessor: 'reference' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (value) => <StatusBadge status={value as DocumentStatus} /> },
    { id: 'validity', header: 'Validité', accessor: 'validity_date', render: (value) => {
      if (!value) return '-';
      const date = new Date(value as string);
      const isExpired = date < new Date();
      return <span className={isExpired ? 'text-danger' : ''}>{isExpired && <AlertTriangle size={14} className="mr-1" />}{formatDate(value as string)}</span>;
    }},
    { id: 'total', header: 'Total TTC', accessor: 'total', align: 'right', render: (value, row) => formatCurrency(value as number, row.currency) },
  ];

  return (
    <PageWrapper title="Devis" subtitle="Gestion des devis clients" actions={<Button leftIcon={<Plus size={16} />} onClick={() => onCreateDevis()}>Nouveau devis</Button>}>
      <section className="azals-section"><DevisStats /></section>
      <Card noPadding>
        <div className="azals-filter-bar">
          <div className="azals-filter-bar__search"><Search size={16} /><input type="text" placeholder="Rechercher..." value={filters.search || ''} onChange={(e) => setFilters({ ...filters, search: e.target.value })} className="azals-input" /></div>
          <select className="azals-select" value={filters.status || ''} onChange={(e) => setFilters({ ...filters, status: e.target.value || undefined })}>
            <option value="">Tous les statuts</option>
            {Object.entries(STATUS_CONFIG).map(([key, config]) => <option key={key} value={key}>{config.label}</option>)}
          </select>
        </div>
        <DataTable columns={columns} data={data?.items || []} keyField="id" filterable isLoading={isLoading}
          pagination={{ page, pageSize, total: data?.total || 0, onPageChange: setPage, onPageSizeChange: setPageSize }}
          onRefresh={refetch} error={error instanceof Error ? error : null} onRetry={() => refetch()} emptyMessage="Aucun devis" />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// DETAIL VIEW
// ============================================================

const DevisDetailView: React.FC<{ devisId: string; onBack: () => void; onEdit: () => void }> = ({ devisId, onBack, onEdit }) => {
  const { data: devis, isLoading, error, refetch } = useDevis(devisId);
  const validateDevis = useValidateDevis();
  const sendDevis = useSendDevis();
  const convertToOrder = useConvertToOrder();

  const tabs: TabDefinition<Devis>[] = useMemo(() => [
    { id: 'info', label: 'Informations', icon: <FileText size={18} />, component: DevisInfoTab },
    { id: 'lines', label: 'Lignes', icon: <Package size={18} />, badge: devis?.lines?.length || 0, component: DevisLinesTab },
    { id: 'financial', label: 'Financier', icon: <Euro size={18} />, component: DevisFinancialTab },
    { id: 'documents', label: 'Documents', icon: <FileArchive size={18} />, component: DevisDocsTab },
    { id: 'history', label: 'Historique', icon: <History size={18} />, component: DevisHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={18} />, isIA: true, component: DevisIATab },
  ], [devis?.lines?.length]);

  const statusConfig = devis ? (STATUS_CONFIG[devis.status] || { label: devis.status, color: 'gray' }) : null;
  const statusDef: StatusDefinition | undefined = statusConfig ? { label: statusConfig.label, color: statusConfig.color as SemanticColor } : undefined;

  const infoBarItems: InfoBarItem[] = useMemo(() => {
    if (!devis) return [];
    return [
      { id: 'date', label: 'Date', value: formatDate(devis.date), icon: <Calendar size={16} /> },
      { id: 'validity', label: 'Validité', value: devis.validity_date ? formatDate(devis.validity_date) : '-', valueColor: devis.validity_date && new Date(devis.validity_date) < new Date() ? 'negative' : undefined, icon: <Clock size={16} /> },
      { id: 'lines', label: 'Lignes', value: devis.lines?.length || 0, icon: <Package size={16} />, secondary: true },
      { id: 'total', label: 'Total TTC', value: formatCurrency(devis.total, devis.currency), icon: <Euro size={16} /> },
    ];
  }, [devis]);

  const sidebarSections: SidebarSection[] = useMemo(() => {
    if (!devis) return [];
    return [
      { id: 'totaux', title: 'Récapitulatif', items: [
        { id: 'subtotal', label: 'Sous-total HT', value: devis.subtotal, format: 'currency' },
        ...(devis.discount_amount > 0 ? [{ id: 'discount', label: `Remise (${devis.discount_percent}%)`, value: -devis.discount_amount, format: 'currency' as const }] : []),
        { id: 'tax', label: 'TVA', value: devis.tax_amount, format: 'currency' },
      ], total: { label: 'Total TTC', value: devis.total } },
      { id: 'client', title: 'Client', items: [
        { id: 'name', label: 'Nom', value: devis.customer_name || '-' },
        { id: 'code', label: 'Code', value: devis.customer_code || '-', secondary: true },
      ]},
    ];
  }, [devis]);

  const headerActions: ActionDefinition[] = useMemo(() => {
    if (!devis) return [];
    const actions: ActionDefinition[] = [];
    if (devis.status === 'DRAFT') actions.push({ id: 'edit', label: 'Modifier', icon: <Edit size={16} />, variant: 'ghost', onClick: onEdit });
    actions.push({ id: 'pdf', label: 'PDF', icon: <Download size={16} />, variant: 'ghost' });
    actions.push({ id: 'print', label: 'Imprimer', icon: <Printer size={16} />, variant: 'ghost' });
    return actions;
  }, [devis, onEdit]);

  const primaryActions: ActionDefinition[] = useMemo(() => {
    if (!devis) return [];
    const actions: ActionDefinition[] = [];
    if (devis.status === 'ACCEPTED') {
      actions.push({ id: 'convert', label: 'Convertir en commande', icon: <ChevronRight size={16} />, variant: 'primary', loading: convertToOrder.isPending,
        onClick: async () => { if (window.confirm('Convertir ce devis en commande ?')) { const order = await convertToOrder.mutateAsync(devisId); window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view: 'commandes', params: { id: order.id } } })); }}});
    }
    if (devis.status === 'VALIDATED') {
      actions.push({ id: 'send', label: 'Marquer envoyé', icon: <Send size={16} />, variant: 'secondary', loading: sendDevis.isPending, onClick: async () => { if (window.confirm('Marquer ce devis comme envoyé ?')) await sendDevis.mutateAsync(devisId); }});
    }
    if (devis.status === 'DRAFT') {
      actions.push({ id: 'validate', label: 'Valider', icon: <Check size={16} />, variant: 'primary', loading: validateDevis.isPending, onClick: async () => { if (window.confirm('Valider ce devis ?')) await validateDevis.mutateAsync(devisId); }});
    }
    return actions;
  }, [devis, devisId, validateDevis, sendDevis, convertToOrder]);

  const secondaryActions: ActionDefinition[] = useMemo(() => [{ id: 'back', label: 'Retour à la liste', variant: 'ghost', onClick: onBack }], [onBack]);

  if (!devis && !isLoading) return <PageWrapper title="Devis non trouvé"><Card><p>Ce devis n'existe pas.</p><Button onClick={onBack}>Retour</Button></Card></PageWrapper>;

  return (
    <BaseViewStandard<Devis>
      title={devis?.number || 'Chargement...'} subtitle={devis?.customer_name} status={statusDef}
      data={devis!} view="detail" tabs={tabs} defaultTab="info" infoBarItems={infoBarItems}
      sidebarSections={sidebarSections} headerActions={headerActions} primaryActions={primaryActions}
      secondaryActions={secondaryActions} backAction={{ label: 'Retour', onClick: onBack }}
      isLoading={isLoading} error={error instanceof Error ? error : null} onRetry={() => refetch()}
    />
  );
};

// ============================================================
// FORM VIEW
// ============================================================

const DevisFormView: React.FC<{ devisId?: string; customerId?: string; onBack: () => void; onSaved: (id: string) => void }> = ({ devisId, customerId, onBack, onSaved }) => {
  const isNew = !devisId;
  const { data: devis } = useDevis(devisId || '');
  const { data: customers } = useCustomers();
  const createDevis = useCreateDevis();
  const updateDevis = useUpdateDevis();
  const addLine = useAddLine();

  const [form, setForm] = useState<DevisFormData>({ customer_id: customerId || '', reference: '', validity_date: '', notes: '', internal_notes: '', terms: '', discount_percent: 0 });
  const [lines, setLines] = useState<Partial<DocumentLine>[]>([]);
  const [newLine, setNewLine] = useState<Partial<DocumentLine>>({ description: '', quantity: 1, unit: 'pce', unit_price: 0, discount_percent: 0, tax_rate: 20 });

  React.useEffect(() => {
    if (devis) {
      setForm({ customer_id: devis.customer_id, reference: devis.reference || '', validity_date: devis.validity_date || '', notes: devis.notes || '', internal_notes: devis.internal_notes || '', terms: devis.terms || '', discount_percent: devis.discount_percent });
      setLines(devis.lines || []);
    }
  }, [devis]);

  const handleAddLine = () => {
    if (!newLine.description) return;
    setLines([...lines, { ...newLine, line_number: lines.length + 1 }]);
    setNewLine({ description: '', quantity: 1, unit: 'pce', unit_price: 0, discount_percent: 0, tax_rate: 20 });
  };

  const handleRemoveLine = (index: number) => setLines(lines.filter((_, i) => i !== index));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.customer_id) { alert('Veuillez sélectionner un client'); return; }
    if (isNew) {
      const result = await createDevis.mutateAsync(form);
      for (const line of lines) await addLine.mutateAsync({ documentId: result.id, data: line });
      onSaved(result.id);
    } else {
      await updateDevis.mutateAsync({ id: devisId!, data: form });
      onSaved(devisId!);
    }
  };

  const isSubmitting = createDevis.isPending || updateDevis.isPending;

  const totals = useMemo(() => {
    const subtotal = lines.reduce((sum, line) => sum + (line.quantity || 0) * (line.unit_price || 0) * (1 - (line.discount_percent || 0) / 100), 0);
    const discountAmount = subtotal * (form.discount_percent || 0) / 100;
    const taxAmount = lines.reduce((sum, line) => sum + (line.quantity || 0) * (line.unit_price || 0) * (1 - (line.discount_percent || 0) / 100) * (line.tax_rate || 20) / 100, 0) * (1 - (form.discount_percent || 0) / 100);
    return { subtotal, discountAmount, taxAmount, total: subtotal - discountAmount + taxAmount };
  }, [lines, form.discount_percent]);

  return (
    <PageWrapper title={isNew ? 'Nouveau devis' : `Modifier ${devis?.number}`} backAction={{ label: 'Retour', onClick: onBack }}>
      <form onSubmit={handleSubmit}>
        <Grid cols={2} gap="lg">
          <Card title="Client">
            <SmartSelector items={customers || []} value={form.customer_id} onChange={(id) => setForm({ ...form, customer_id: id })} label="Client" placeholder="Rechercher un client..." entityName="client" createEndpoint="/commercial/customers" createFields={[{ key: 'name', label: 'Nom', required: true }, { key: 'email', label: 'Email', type: 'email' }, { key: 'phone', label: 'Téléphone', type: 'tel' }]} queryKeys={['customers']} allowCreate={true} />
            <div className="azals-form-field"><label>Référence client</label><input type="text" className="azals-input" value={form.reference} onChange={(e) => setForm({ ...form, reference: e.target.value })} placeholder="Votre référence..." /></div>
          </Card>
          <Card title="Dates">
            <div className="azals-form-field"><label>Date de validité</label><input type="date" className="azals-input" value={form.validity_date} onChange={(e) => setForm({ ...form, validity_date: e.target.value })} /></div>
            <div className="azals-form-field"><label>Remise globale (%)</label><input type="number" className="azals-input" value={form.discount_percent} onChange={(e) => setForm({ ...form, discount_percent: parseFloat(e.target.value) || 0 })} min="0" max="100" step="0.5" /></div>
          </Card>
        </Grid>

        <Card title="Lignes" className="mt-4">
          {lines.length > 0 && (
            <table className="azals-table azals-table--simple mb-4">
              <thead><tr><th>Description</th><th className="text-right">Qté</th><th className="text-right">P.U. HT</th><th className="text-right">Remise</th><th className="text-right">TVA</th><th className="text-right">Total HT</th><th></th></tr></thead>
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
              <div className="azals-form-field" style={{ gridColumn: 'span 2' }}><input type="text" className="azals-input" placeholder="Description..." value={newLine.description} onChange={(e) => setNewLine({ ...newLine, description: e.target.value })} /></div>
              <div className="azals-form-field"><input type="number" className="azals-input" placeholder="Qté" value={newLine.quantity} onChange={(e) => setNewLine({ ...newLine, quantity: parseFloat(e.target.value) || 1 })} min="0" step="0.01" /></div>
              <div className="azals-form-field"><input type="number" className="azals-input" placeholder="P.U. HT" value={newLine.unit_price} onChange={(e) => setNewLine({ ...newLine, unit_price: parseFloat(e.target.value) || 0 })} min="0" step="0.01" /></div>
              <div className="azals-form-field"><select className="azals-select" value={newLine.tax_rate} onChange={(e) => setNewLine({ ...newLine, tax_rate: parseFloat(e.target.value) })}><option value="20">20%</option><option value="10">10%</option><option value="5.5">5.5%</option><option value="0">0%</option></select></div>
              <div><Button type="button" variant="secondary" onClick={handleAddLine}><Plus size={16} /></Button></div>
            </Grid>
          </div>

          <div className="azals-totals mt-4">
            <div className="azals-totals__row"><span>Sous-total HT</span><span>{formatCurrency(totals.subtotal)}</span></div>
            {totals.discountAmount > 0 && <div className="azals-totals__row"><span>Remise ({form.discount_percent}%)</span><span>-{formatCurrency(totals.discountAmount)}</span></div>}
            <div className="azals-totals__row"><span>TVA</span><span>{formatCurrency(totals.taxAmount)}</span></div>
            <div className="azals-totals__row azals-totals__row--total"><span>Total TTC</span><span>{formatCurrency(totals.total)}</span></div>
          </div>
        </Card>

        <Card title="Notes" className="mt-4">
          <Grid cols={2} gap="md">
            <div className="azals-form-field"><label>Notes (visibles sur le devis)</label><textarea className="azals-textarea" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={3} /></div>
            <div className="azals-form-field"><label>Conditions</label><textarea className="azals-textarea" value={form.terms} onChange={(e) => setForm({ ...form, terms: e.target.value })} rows={3} placeholder="Conditions de paiement, délais..." /></div>
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

type DevisView = 'list' | 'detail' | 'form';

interface DevisNavState {
  view: DevisView;
  devisId?: string;
  customerId?: string;
  isNew?: boolean;
}

export const DevisModule: React.FC = () => {
  const [navState, setNavState] = useState<DevisNavState>({ view: 'list' });

  React.useEffect(() => {
    const handleNavigate = (event: CustomEvent) => {
      const { params } = event.detail || {};
      if (params?.customerId && params?.action === 'new') setNavState({ view: 'form', customerId: params.customerId, isNew: true });
      else if (params?.id) setNavState({ view: 'detail', devisId: params.id });
    };
    window.addEventListener('azals:navigate:devis', handleNavigate as EventListener);
    return () => window.removeEventListener('azals:navigate:devis', handleNavigate as EventListener);
  }, []);

  const navigateToList = useCallback(() => setNavState({ view: 'list' }), []);
  const navigateToDetail = useCallback((id: string) => setNavState({ view: 'detail', devisId: id }), []);
  const navigateToForm = useCallback((id?: string, customerId?: string) => setNavState({ view: 'form', devisId: id, customerId, isNew: !id }), []);

  switch (navState.view) {
    case 'detail': return <DevisDetailView devisId={navState.devisId!} onBack={navigateToList} onEdit={() => navigateToForm(navState.devisId)} />;
    case 'form': return <DevisFormView devisId={navState.devisId} customerId={navState.customerId} onBack={navState.isNew ? navigateToList : () => navigateToDetail(navState.devisId!)} onSaved={navigateToDetail} />;
    default: return <DevisListView onSelectDevis={navigateToDetail} onCreateDevis={(customerId) => navigateToForm(undefined, customerId)} />;
  }
};

export default DevisModule;

// Re-exports
export * from './hooks';
export * from './types';
