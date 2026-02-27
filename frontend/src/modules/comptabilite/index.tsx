/**
 * AZALSCORE Module - Comptabilite
 * Gestion comptable et financiere
 */

import React, { useState } from 'react';
import {
  BarChart3, TrendingDown, TrendingUp, Diamond, Landmark, DollarSign,
  FileText, List, PieChart, Paperclip, Clock, Sparkles, ArrowLeft,
  CheckCircle2, XCircle, BookOpen, Edit as EditIcon
} from 'lucide-react';
import { Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { Button, Modal } from '@ui/actions';
import { LoadingState, ErrorState } from '@ui/components/StateViews';
import { StatCard } from '@ui/dashboards';
import { Select, Input } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { BaseViewStandard } from '@ui/standards';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';
import { formatCurrency, formatDate } from '@/utils/formatters';

// Module imports
import {
  useFinanceDashboard,
  useAccounts,
  useJournals,
  useEntries,
  useEntry,
  useBankAccounts,
  useBankTransactions,
  useCashForecasts,
  useCreateAccount,
  useCreateJournal,
  useCreateEntry,
  useValidateEntry,
  usePostEntry,
} from './hooks';
import {
  EntryInfoTab, EntryLinesTab, EntryAnalyticsTab,
  EntryDocumentsTab, EntryHistoryTab, EntryIATab
} from './components';
import {
  ACCOUNT_TYPE_CONFIG, JOURNAL_TYPE_CONFIG, ENTRY_STATUS_CONFIG,
  isEntryBalanced
} from './types';
import type {
  Account, Journal, Entry, EntryLine, BankAccount, BankTransaction, CashForecast,
  AccountType, JournalType
} from './types';
import type { InfoBarItem, SidebarSection, TabDefinition } from '@ui/standards';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

const TabNav: React.FC<{ tabs: { id: string; label: string }[]; activeTab: string; onChange: (id: string) => void }> = ({ tabs, activeTab, onChange }) => (
  <nav className="azals-tab-nav">
    {tabs.map((tab) => (
      <button key={tab.id} className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`} onClick={() => onChange(tab.id)}>{tab.label}</button>
    ))}
  </nav>
);

// ============================================================================
// VIEWS
// ============================================================================

const AccountsView: React.FC = () => {
  const { data: accounts = [], isLoading, error, refetch } = useAccounts();
  const createAccount = useCreateAccount();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<Account>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createAccount.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<Account>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Libelle', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v): React.ReactNode => {
      const info = ACCOUNT_TYPE_CONFIG[v as AccountType];
      return <Badge color={info?.color || 'gray'}>{info?.label || String(v)}</Badge>;
    }},
    { id: 'balance', header: 'Solde', accessor: 'balance', render: (v) => formatCurrency(v as number) },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => <Badge color={v ? 'green' : 'gray'}>{v ? 'Oui' : 'Non'}</Badge> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Plan Comptable</h3>
        <Button onClick={() => setShowModal(true)}>Nouveau compte</Button>
      </div>
      <DataTable columns={columns} data={accounts} isLoading={isLoading} keyField="id" filterable error={error instanceof Error ? error : null} onRetry={() => refetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouveau compte">
        <form onSubmit={handleSubmit}>
          <div className="azals-field"><label>Code</label><Input value={formData.code || ''} onChange={(v) => setFormData({ ...formData, code: v })} /></div>
          <div className="azals-field"><label>Libelle</label><Input value={formData.name || ''} onChange={(v) => setFormData({ ...formData, name: v })} /></div>
          <div className="azals-field"><label>Type</label>
            <Select value={formData.type || ''} onChange={(v) => setFormData({ ...formData, type: v as AccountType })}
              options={Object.entries(ACCOUNT_TYPE_CONFIG).map(([value, cfg]) => ({ value, label: cfg.label }))} /></div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createAccount.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const JournalsView: React.FC = () => {
  const { data: journals = [], isLoading, error, refetch } = useJournals();
  const createJournal = useCreateJournal();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<Journal>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createJournal.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<Journal>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Libelle', accessor: 'name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v): React.ReactNode => JOURNAL_TYPE_CONFIG[v as JournalType]?.label || String(v) },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => <Badge color={v ? 'green' : 'gray'}>{v ? 'Oui' : 'Non'}</Badge> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Journaux</h3>
        <Button onClick={() => setShowModal(true)}>Nouveau journal</Button>
      </div>
      <DataTable columns={columns} data={journals} isLoading={isLoading} keyField="id" filterable error={error instanceof Error ? error : null} onRetry={() => refetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouveau journal">
        <form onSubmit={handleSubmit}>
          <div className="azals-field"><label>Code</label><Input value={formData.code || ''} onChange={(v) => setFormData({ ...formData, code: v })} /></div>
          <div className="azals-field"><label>Libelle</label><Input value={formData.name || ''} onChange={(v) => setFormData({ ...formData, name: v })} /></div>
          <div className="azals-field"><label>Type</label>
            <Select value={formData.type || ''} onChange={(v) => setFormData({ ...formData, type: v as JournalType })}
              options={Object.entries(JOURNAL_TYPE_CONFIG).map(([value, cfg]) => ({ value, label: cfg.label }))} /></div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createJournal.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const EntriesView: React.FC = () => {
  const navigate = useNavigate();
  const { data: entries = [], isLoading, error, refetch } = useEntries();
  const { data: journals = [] } = useJournals();
  const { data: accounts = [] } = useAccounts();
  const createEntry = useCreateEntry();
  const validateEntry = useValidateEntry();
  const postEntry = usePostEntry();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<Entry>>({ lines: [] });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createEntry.mutateAsync(formData);
    setShowModal(false);
    setFormData({ lines: [] });
  };

  const addLine = () => {
    const lines = [...(formData.lines || []), { id: '', account_id: '', debit: 0, credit: 0 }];
    setFormData({ ...formData, lines });
  };

  const updateLine = (index: number, field: string, value: string | number) => {
    const lines = [...(formData.lines || [])];
    lines[index] = { ...lines[index], [field]: value };
    setFormData({ ...formData, lines });
  };

  const columns: TableColumn<Entry>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v, row) => <button className="font-mono text-primary hover:underline" onClick={() => navigate(`/comptabilite/entries/${row.id}`)}>{v as string}</button> },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'description', header: 'Libelle', accessor: 'description' },
    { id: 'total_debit', header: 'Debit', accessor: 'total_debit', render: (v) => formatCurrency(v as number) },
    { id: 'total_credit', header: 'Credit', accessor: 'total_credit', render: (v) => formatCurrency(v as number) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v): React.ReactNode => { const info = ENTRY_STATUS_CONFIG[v as keyof typeof ENTRY_STATUS_CONFIG]; return <Badge color={info?.color || 'gray'}>{info?.label || String(v)}</Badge>; }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        <Button size="sm" variant="ghost" onClick={() => navigate(`/comptabilite/entries/${row.id}`)}>Voir</Button>
        {row.status === 'DRAFT' && <Button size="sm" onClick={() => validateEntry.mutate(row.id)}>Valider</Button>}
        {row.status === 'VALIDATED' && <Button size="sm" onClick={() => postEntry.mutate(row.id)}>Comptabiliser</Button>}
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Ecritures comptables</h3>
        <Button onClick={() => setShowModal(true)}>Nouvelle ecriture</Button>
      </div>
      <DataTable columns={columns} data={entries} isLoading={isLoading} keyField="id" filterable error={error instanceof Error ? error : null} onRetry={() => refetch()} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvelle ecriture" size="lg">
        <form onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field"><label>Journal</label><Select value={formData.journal_id || ''} onChange={(v) => setFormData({ ...formData, journal_id: v })} options={journals.map(j => ({ value: j.id, label: `${j.code} - ${j.name}` }))} /></div>
            <div className="azals-field"><label>Date</label><input type="date" className="azals-input" value={formData.date || ''} onChange={(e) => setFormData({ ...formData, date: e.target.value })} required /></div>
          </Grid>
          <div className="azals-field"><label>Libelle</label><Input value={formData.description || ''} onChange={(v) => setFormData({ ...formData, description: v })} /></div>
          <div className="mt-4">
            <div className="flex justify-between items-center mb-2"><h4 className="font-medium">Lignes</h4><Button size="sm" onClick={addLine}>Ajouter ligne</Button></div>
            {(formData.lines || []).map((line, idx) => (
              <Grid cols={3} key={idx} className="mb-2">
                <Select value={line.account_id} onChange={(v) => updateLine(idx, 'account_id', v)} options={accounts.map(a => ({ value: a.id, label: `${a.code} - ${a.name}` }))} placeholder="Compte" />
                <Input type="number" value={line.debit || ''} onChange={(v) => updateLine(idx, 'debit', parseFloat(v) || 0)} placeholder="Debit" />
                <Input type="number" value={line.credit || ''} onChange={(v) => updateLine(idx, 'credit', parseFloat(v) || 0)} placeholder="Credit" />
              </Grid>
            ))}
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createEntry.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const BankView: React.FC = () => {
  const { data: bankAccounts = [], isLoading, error, refetch } = useBankAccounts();
  const [selectedBank, setSelectedBank] = useState<string | null>(null);
  const { data: transactions = [] } = useBankTransactions(selectedBank || undefined);

  const bankColumns: TableColumn<BankAccount>[] = [
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'bank_name', header: 'Banque', accessor: 'bank_name' },
    { id: 'iban', header: 'IBAN', accessor: 'iban', render: (v) => v ? <code className="font-mono text-xs">{v as string}</code> : '-' },
    { id: 'balance', header: 'Solde', accessor: 'balance', render: (v) => formatCurrency(v as number) },
    { id: 'actions', header: '', accessor: 'id', render: (_, row) => <Button size="sm" variant="secondary" onClick={() => setSelectedBank(row.id)}>Voir mouvements</Button> }
  ];

  const transactionColumns: TableColumn<BankTransaction>[] = [
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => <Badge color={v === 'CREDIT' ? 'green' : 'red'}>{v === 'CREDIT' ? 'Credit' : 'Debit'}</Badge> },
    { id: 'amount', header: 'Montant', accessor: 'amount', render: (v) => formatCurrency(v as number) },
    { id: 'reference', header: 'Reference', accessor: 'reference' },
    { id: 'description', header: 'Description', accessor: 'description' },
    { id: 'is_reconciled', header: 'Rapproche', accessor: 'is_reconciled', render: (v) => <Badge color={v ? 'green' : 'gray'}>{v ? 'Oui' : 'Non'}</Badge> }
  ];

  return (
    <div className="space-y-4">
      <Card>
        <h3 className="text-lg font-semibold mb-4">Comptes bancaires</h3>
        <DataTable columns={bankColumns} data={bankAccounts} isLoading={isLoading} keyField="id" filterable error={error instanceof Error ? error : null} onRetry={() => refetch()} />
      </Card>
      {selectedBank && (
        <Card>
          <div className="flex justify-between items-center mb-4"><h3 className="text-lg font-semibold">Mouvements bancaires</h3><Button variant="secondary" onClick={() => setSelectedBank(null)}>Fermer</Button></div>
          <DataTable columns={transactionColumns} data={transactions} keyField="id" filterable />
        </Card>
      )}
    </div>
  );
};

const CashForecastView: React.FC = () => {
  const { data: forecasts = [], isLoading, error, refetch } = useCashForecasts();

  const columns: TableColumn<CashForecast>[] = [
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => <Badge color={v === 'INCOME' ? 'green' : 'red'}>{v === 'INCOME' ? 'Encaissement' : 'Decaissement'}</Badge> },
    { id: 'amount', header: 'Montant', accessor: 'amount', render: (v) => formatCurrency(v as number) },
    { id: 'description', header: 'Description', accessor: 'description' },
    { id: 'is_realized', header: 'Realise', accessor: 'is_realized', render: (v) => <Badge color={v ? 'green' : 'gray'}>{v ? 'Oui' : 'Non'}</Badge> }
  ];

  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">Previsions de tresorerie</h3>
      <DataTable columns={columns} data={forecasts} isLoading={isLoading} keyField="id" filterable error={error instanceof Error ? error : null} onRetry={() => refetch()} />
    </Card>
  );
};

// ============================================================================
// ENTRY DETAIL VIEW
// ============================================================================

const EntryDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: entry, isLoading, error, refetch } = useEntry(id || '');
  const validateEntry = useValidateEntry();
  const postEntry = usePostEntry();

  if (isLoading) return <PageWrapper title="Chargement..."><LoadingState onRetry={() => refetch()} message="Chargement de l'ecriture..." /></PageWrapper>;
  if (error || !entry) return <PageWrapper title="Erreur"><ErrorState message="Ecriture non trouvee" onRetry={() => refetch()} onBack={() => navigate('/comptabilite')} /></PageWrapper>;

  const statusConfig = ENTRY_STATUS_CONFIG[entry.status] || { label: entry.status, color: 'gray' };
  const balanced = isEntryBalanced(entry);

  const tabs: TabDefinition<Entry>[] = [
    { id: 'info', label: 'Informations', icon: <FileText size={16} />, component: EntryInfoTab },
    { id: 'lines', label: 'Lignes', icon: <List size={16} />, badge: entry.lines?.length || 0, component: EntryLinesTab },
    { id: 'analytics', label: 'Analytique', icon: <PieChart size={16} />, component: EntryAnalyticsTab },
    { id: 'documents', label: 'Documents', icon: <Paperclip size={16} />, component: EntryDocumentsTab },
    { id: 'history', label: 'Historique', icon: <Clock size={16} />, component: EntryHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: EntryIATab }
  ];

  const infoBarItems: InfoBarItem[] = [
    { id: 'status', label: 'Statut', value: statusConfig.label, valueColor: statusConfig.color as 'gray' | 'blue' | 'green' | 'red' },
    { id: 'journal', label: 'Journal', value: entry.journal_code || '-' },
    { id: 'date', label: 'Date', value: formatDate(entry.date) },
    { id: 'balance', label: 'Equilibre', value: balanced ? 'Oui' : 'Non', valueColor: balanced ? 'green' : 'red' }
  ];

  const sidebarSections: SidebarSection[] = [
    { id: 'totals', title: 'Totaux', items: [
      { id: 'debit', label: 'Total Debit', value: formatCurrency(entry.total_debit), highlight: true },
      { id: 'credit', label: 'Total Credit', value: formatCurrency(entry.total_credit), highlight: true },
      { id: 'balance', label: 'Ecart', value: formatCurrency(Math.abs(entry.total_debit - entry.total_credit)) }
    ]},
    { id: 'details', title: 'Details', items: [
      { id: 'lines', label: 'Lignes', value: `${entry.lines?.length || 0}` },
      { id: 'accounts', label: 'Comptes', value: `${new Set(entry.lines?.map(l => l.account_id) || []).size}` },
      { id: 'reference', label: 'Reference', value: entry.reference || '-' }
    ]}
  ];

  const headerActions = [
    { id: 'back', label: 'Retour', icon: <ArrowLeft size={16} />, variant: 'ghost' as const, onClick: () => navigate('/comptabilite') },
    ...(entry.status === 'DRAFT' ? [{ id: 'edit', label: 'Modifier', icon: <EditIcon size={16} />, variant: 'secondary' as const }] : []),
    ...(entry.status === 'DRAFT' && balanced ? [{ id: 'validate', label: 'Valider', icon: <CheckCircle2 size={16} />, variant: 'primary' as const, onClick: () => validateEntry.mutate(entry.id) }] : []),
    ...(entry.status === 'VALIDATED' ? [{ id: 'post', label: 'Comptabiliser', icon: <BookOpen size={16} />, variant: 'primary' as const, onClick: () => postEntry.mutate(entry.id) }] : []),
    ...(entry.status === 'DRAFT' ? [{ id: 'cancel', label: 'Annuler', icon: <XCircle size={16} />, variant: 'danger' as const }] : [])
  ];

  return (
    <BaseViewStandard<Entry>
      title={`Ecriture ${entry.number}`} subtitle={entry.description}
      status={{ label: statusConfig.label, color: statusConfig.color }}
      data={entry} view="detail" tabs={tabs} infoBarItems={infoBarItems}
      sidebarSections={sidebarSections} headerActions={headerActions}
      error={error ? new Error(String(error)) : null} onRetry={() => refetch()}
    />
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'accounts' | 'journals' | 'entries' | 'bank' | 'forecasts';

const ComptabiliteModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: dashboard } = useFinanceDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'accounts', label: 'Plan comptable' },
    { id: 'journals', label: 'Journaux' },
    { id: 'entries', label: 'Ecritures' },
    { id: 'bank', label: 'Banque' },
    { id: 'forecasts', label: 'Tresorerie' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'accounts': return <AccountsView />;
      case 'journals': return <JournalsView />;
      case 'entries': return <EntriesView />;
      case 'bank': return <BankView />;
      case 'forecasts': return <CashForecastView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard title="Actifs" value={formatCurrency(dashboard?.total_assets || 0)} icon={<BarChart3 />} variant="default" />
              <StatCard title="Passifs" value={formatCurrency(dashboard?.total_liabilities || 0)} icon={<TrendingDown />} variant="danger" />
              <StatCard title="Capitaux propres" value={formatCurrency(dashboard?.total_equity || 0)} icon={<Diamond />} variant="default" />
              <StatCard title="Solde bancaire" value={formatCurrency(dashboard?.bank_balance || 0)} icon={<Landmark />} variant="success" />
            </Grid>
            <Grid cols={3}>
              <StatCard title="Produits" value={formatCurrency(dashboard?.total_revenue || 0)} icon={<TrendingUp />} variant="success" />
              <StatCard title="Charges" value={formatCurrency(dashboard?.total_expenses || 0)} icon={<TrendingDown />} variant="warning" />
              <StatCard title="Resultat net" value={formatCurrency(dashboard?.net_income || 0)} icon={<DollarSign />} variant={(dashboard?.net_income || 0) >= 0 ? 'success' : 'danger'} />
            </Grid>
            <Card><h3 className="text-lg font-semibold mb-2">Ecritures en attente</h3><p className="text-2xl font-bold">{dashboard?.pending_entries || 0}</p></Card>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Comptabilite" subtitle="Gestion comptable et financiere">
      <TabNav tabs={tabs} activeTab={currentView} onChange={(id) => setCurrentView(id as View)} />
      <div className="mt-4">{renderContent()}</div>
    </PageWrapper>
  );
};

// ============================================================================
// ROUTES EXPORT
// ============================================================================

const ComptabiliteRoutes: React.FC = () => (
  <Routes>
    <Route path="entries/:id" element={<EntryDetailView />} />
    <Route path="*" element={<ComptabiliteModule />} />
  </Routes>
);

export default ComptabiliteRoutes;

// Re-exports
export * from './hooks';
export * from './types';
