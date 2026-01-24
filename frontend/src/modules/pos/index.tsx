import React, { useState } from 'react';
import { Routes, Route, useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import { BaseViewStandard } from '@ui/standards';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition, SemanticColor } from '@ui/standards';
import type { TableColumn } from '@/types';
import {
  Monitor, DollarSign, Receipt, ShoppingCart, Sparkles, Clock,
  Banknote, ArrowLeft, Edit, Printer, Play, CheckCircle2
} from 'lucide-react';
import type { POSSession as POSSessionType } from './types';
import {
  formatCurrency as formatCurrencyTyped, formatDateTime as formatDateTimeTyped,
  formatSessionDuration, SESSION_STATUS_CONFIG,
  isSessionOpen, isSessionClosed, hasCashDifference
} from './types';
import {
  SessionInfoTab, SessionTransactionsTab, SessionCashTab,
  SessionHistoryTab, SessionIATab
} from './components';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavProps {
  tabs: { id: string; label: string }[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <nav className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </nav>
);

// ============================================================================
// TYPES
// ============================================================================

interface POSStore {
  id: string;
  code: string;
  name: string;
  address?: string;
  is_active: boolean;
}

interface POSTerminal {
  id: string;
  code: string;
  name: string;
  store_id: string;
  store_name?: string;
  status: 'OFFLINE' | 'ONLINE' | 'IN_USE';
  last_activity?: string;
}

interface POSSession {
  id: string;
  terminal_id: string;
  terminal_name?: string;
  store_name?: string;
  cashier_id: string;
  cashier_name?: string;
  opened_at: string;
  closed_at?: string;
  status: 'OPEN' | 'CLOSED';
  opening_balance: number;
  closing_balance: number;
  total_sales: number;
  total_transactions: number;
}

interface POSTransaction {
  id: string;
  number: string;
  session_id: string;
  type: 'SALE' | 'RETURN' | 'EXCHANGE';
  customer_id?: string;
  customer_name?: string;
  items: POSTransactionItem[];
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  payment_method: 'CASH' | 'CARD' | 'CHECK' | 'VOUCHER' | 'MIXED';
  amount_paid: number;
  change: number;
  status: 'COMPLETED' | 'VOIDED' | 'REFUNDED';
  created_at: string;
}

interface POSTransactionItem {
  id: string;
  product_id: string;
  product_name?: string;
  quantity: number;
  unit_price: number;
  discount: number;
  total: number;
}

interface POSDashboard {
  active_sessions: number;
  sales_today: number;
  transactions_today: number;
  average_ticket: number;
  top_products: { product_name: string; quantity: number; amount: number }[];
  sales_by_hour: { hour: number; amount: number }[];
}

// ============================================================================
// CONSTANTES
// ============================================================================

const TERMINAL_STATUSES = [
  { value: 'OFFLINE', label: 'Hors ligne', color: 'gray' },
  { value: 'ONLINE', label: 'En ligne', color: 'green' },
  { value: 'IN_USE', label: 'En cours', color: 'blue' }
];

const SESSION_STATUSES = [
  { value: 'OPEN', label: 'Ouverte', color: 'green' },
  { value: 'CLOSED', label: 'Fermee', color: 'gray' }
];

const TRANSACTION_TYPES = [
  { value: 'SALE', label: 'Vente', color: 'green' },
  { value: 'RETURN', label: 'Retour', color: 'red' },
  { value: 'EXCHANGE', label: 'Echange', color: 'blue' }
];

const PAYMENT_METHODS = [
  { value: 'CASH', label: 'Especes' },
  { value: 'CARD', label: 'Carte' },
  { value: 'CHECK', label: 'Cheque' },
  { value: 'VOUCHER', label: 'Bon' },
  { value: 'MIXED', label: 'Mixte' }
];

// ============================================================================
// HELPERS
// ============================================================================

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
};

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

const getStatusInfo = (statuses: { value: string; label: string; color: string }[], status: string) => {
  return statuses.find(s => s.value === status) || { label: status, color: 'gray' };
};

// ============================================================================
// API HOOKS
// ============================================================================

const usePOSDashboard = () => {
  return useQuery({
    queryKey: ['pos', 'dashboard'],
    queryFn: async () => {
      return api.get<POSDashboard>('/v1/pos/dashboard').then(r => r.data);
    }
  });
};

const useStores = () => {
  return useQuery({
    queryKey: ['pos', 'stores'],
    queryFn: async () => {
      return api.get<POSStore[]>('/v1/pos/stores').then(r => r.data);
    }
  });
};

const useTerminals = (storeId?: string) => {
  return useQuery({
    queryKey: ['pos', 'terminals', storeId],
    queryFn: async () => {
      const url = storeId ? `/v1/pos/terminals?store_id=${storeId}` : '/v1/pos/terminals';
      return api.get<POSTerminal[]>(url).then(r => r.data);
    }
  });
};

const useSessions = (filters?: { status?: string; store_id?: string }) => {
  return useQuery({
    queryKey: ['pos', 'sessions', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.store_id) params.append('store_id', filters.store_id);
      const queryString = params.toString();
      const url = queryString ? `/v1/pos/sessions?${queryString}` : '/v1/pos/sessions';
      return api.get<POSSession[]>(url).then(r => r.data);
    }
  });
};

const useTransactions = (sessionId?: string) => {
  return useQuery({
    queryKey: ['pos', 'transactions', sessionId],
    queryFn: async () => {
      const url = sessionId ? `/v1/pos/transactions?session_id=${sessionId}` : '/v1/pos/transactions';
      return api.get<POSTransaction[]>(url).then(r => r.data);
    }
  });
};

const useOpenSession = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { terminal_id: string; opening_balance: number }) => {
      return api.post('/v1/pos/sessions', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pos'] })
  });
};

const useCloseSession = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, closing_balance }: { id: string; closing_balance: number }) => {
      return api.post(`/v1/pos/sessions/${id}/close`, { closing_balance }).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pos'] })
  });
};

const useSession = (id: string) => {
  return useQuery({
    queryKey: ['pos', 'sessions', id],
    queryFn: async () => {
      return api.get<POSSessionType>(`/v1/pos/sessions/${id}`).then(r => r.data);
    },
    enabled: !!id
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const StoresView: React.FC = () => {
  const { data: stores = [], isLoading } = useStores();

  const columns: TableColumn<POSStore>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'address', header: 'Adresse', accessor: 'address', render: (v) => (v as string) || '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Magasins</h3>
        <Button>Nouveau magasin</Button>
      </div>
      <DataTable columns={columns} data={stores} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const TerminalsView: React.FC = () => {
  const { data: stores = [] } = useStores();
  const [filterStore, setFilterStore] = useState<string>('');
  const { data: terminals = [], isLoading } = useTerminals(filterStore || undefined);

  const columns: TableColumn<POSTerminal>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'store_name', header: 'Magasin', accessor: 'store_name' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(TERMINAL_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'last_activity', header: 'Derniere activite', accessor: 'last_activity', render: (v) => (v as string) ? formatDateTime(v as string) : '-' }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Terminaux</h3>
        <div className="flex gap-2">
          <Select
            value={filterStore}
            onChange={(v) => setFilterStore(v)}
            options={[{ value: '', label: 'Tous les magasins' }, ...stores.map(s => ({ value: s.id, label: s.name }))]}
            className="w-48"
          />
          <Button>Nouveau terminal</Button>
        </div>
      </div>
      <DataTable columns={columns} data={terminals} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const SessionsView: React.FC = () => {
  const navigate = useNavigate();
  const { data: stores = [] } = useStores();
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterStore, setFilterStore] = useState<string>('');
  const { data: sessions = [], isLoading } = useSessions({
    status: filterStatus || undefined,
    store_id: filterStore || undefined
  });
  const { data: terminals = [] } = useTerminals();
  const openSession = useOpenSession();
  const closeSession = useCloseSession();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<{ terminal_id: string; opening_balance: number }>({ terminal_id: '', opening_balance: 0 });

  const handleOpenSession = async () => {
    await openSession.mutateAsync(formData);
    setShowModal(false);
    setFormData({ terminal_id: '', opening_balance: 0 });
  };

  const columns: TableColumn<POSSession>[] = [
    { id: 'terminal_name', header: 'Terminal', accessor: 'terminal_name' },
    { id: 'store_name', header: 'Magasin', accessor: 'store_name' },
    { id: 'cashier_name', header: 'Caissier', accessor: 'cashier_name' },
    { id: 'opened_at', header: 'Ouverture', accessor: 'opened_at', render: (v) => formatDateTime(v as string) },
    { id: 'total_sales', header: 'Ventes', accessor: 'total_sales', render: (v) => formatCurrency(v as number) },
    { id: 'total_transactions', header: 'Transactions', accessor: 'total_transactions' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(SESSION_STATUSES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (v, row) => (
      <div className="flex gap-1">
        <Button size="sm" variant="secondary" onClick={() => navigate(`/pos/sessions/${v}`)}>
          Detail
        </Button>
        {(row as POSSession).status === 'OPEN' && (
          <Button size="sm" onClick={() => closeSession.mutate({ id: (row as POSSession).id, closing_balance: 0 })}>
            Cloturer
          </Button>
        )}
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Sessions de caisse</h3>
        <div className="flex gap-2">
          <Select
            value={filterStore}
            onChange={(v) => setFilterStore(v)}
            options={[{ value: '', label: 'Tous les magasins' }, ...stores.map(s => ({ value: s.id, label: s.name }))]}
            className="w-40"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous les statuts' }, ...SESSION_STATUSES]}
            className="w-36"
          />
          <Button onClick={() => setShowModal(true)}>Ouvrir session</Button>
        </div>
      </div>
      <DataTable columns={columns} data={sessions} isLoading={isLoading} keyField="id" />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Ouvrir une session">
        <div className="space-y-4">
          <div className="azals-field">
            <label>Terminal</label>
            <Select
              value={formData.terminal_id}
              onChange={(v) => setFormData({ ...formData, terminal_id: v })}
              options={terminals.filter(t => t.status === 'ONLINE').map(t => ({ value: t.id, label: `${t.code} - ${t.name}` }))}
            />
          </div>
          <div className="azals-field">
            <label>Fond de caisse</label>
            <Input
              type="number"
              value={formData.opening_balance}
              onChange={(v) => setFormData({ ...formData, opening_balance: parseFloat(v) || 0 })}
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button onClick={handleOpenSession} isLoading={openSession.isPending}>Ouvrir</Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
};

const TransactionsView: React.FC = () => {
  const [filterType, setFilterType] = useState<string>('');
  const [filterPayment, setFilterPayment] = useState<string>('');
  const { data: transactions = [], isLoading } = useTransactions();

  const filteredData = transactions.filter(t => {
    if (filterType && t.type !== filterType) return false;
    if (filterPayment && t.payment_method !== filterPayment) return false;
    return true;
  });

  const columns: TableColumn<POSTransaction>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'created_at', header: 'Date', accessor: 'created_at', render: (v) => formatDateTime(v as string) },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const info = getStatusInfo(TRANSACTION_TYPES, v as string);
      return <Badge color={info.color}>{info.label}</Badge>;
    }},
    { id: 'customer_name', header: 'Client', accessor: 'customer_name', render: (v) => (v as string) || '-' },
    { id: 'items', header: 'Articles', accessor: 'items', render: (v) => (v as POSTransactionItem[])?.length || 0 },
    { id: 'total', header: 'Total', accessor: 'total', render: (v) => formatCurrency(v as number) },
    { id: 'payment_method', header: 'Paiement', accessor: 'payment_method', render: (v) => {
      const info = PAYMENT_METHODS.find(p => p.value === (v as string));
      return info?.label || (v as string);
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Transactions</h3>
        <div className="flex gap-2">
          <Select
            value={filterType}
            onChange={(v) => setFilterType(v)}
            options={[{ value: '', label: 'Tous types' }, ...TRANSACTION_TYPES]}
            className="w-32"
          />
          <Select
            value={filterPayment}
            onChange={(v) => setFilterPayment(v)}
            options={[{ value: '', label: 'Tous paiements' }, ...PAYMENT_METHODS]}
            className="w-36"
          />
        </div>
      </div>
      <DataTable columns={columns} data={filteredData} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

// ============================================================================
// SESSION DETAIL VIEW
// ============================================================================

const SessionDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: session, isLoading, error } = useSession(id || '');
  const closeSession = useCloseSession();

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="flex items-center justify-center h-64">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (error || !session) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <div className="text-center py-8">
            <p className="text-red-600">Session non trouvee</p>
            <Button variant="secondary" onClick={() => navigate('/pos')} className="mt-4">
              <ArrowLeft size={16} className="mr-2" />
              Retour
            </Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  // Tabs definition
  const tabs: TabDefinition<POSSessionType>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <Monitor size={16} />,
      component: SessionInfoTab
    },
    {
      id: 'transactions',
      label: 'Transactions',
      icon: <Receipt size={16} />,
      badge: session.total_transactions > 0 ? session.total_transactions : undefined,
      component: SessionTransactionsTab
    },
    {
      id: 'cash',
      label: 'Caisse',
      icon: <Banknote size={16} />,
      component: SessionCashTab
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <Clock size={16} />,
      component: SessionHistoryTab
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: SessionIATab
    }
  ];

  // Info bar items
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'sales',
      label: 'Ventes',
      value: formatCurrencyTyped(session.total_sales),
      valueColor: 'green'
    },
    {
      id: 'transactions',
      label: 'Transactions',
      value: String(session.total_transactions),
      valueColor: 'blue'
    },
    {
      id: 'basket',
      label: 'Panier moyen',
      value: formatCurrencyTyped(session.average_basket),
      valueColor: 'purple'
    },
    {
      id: 'duration',
      label: 'Duree',
      value: formatSessionDuration(session),
      valueColor: 'gray'
    }
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'terminal',
      title: 'Terminal',
      items: [
        { id: 'terminal_name', label: 'Nom', value: session.terminal_name || '-' },
        { id: 'store', label: 'Magasin', value: session.store_name || '-' },
        { id: 'cashier', label: 'Caissier', value: session.cashier_name || '-' }
      ]
    },
    {
      id: 'totals',
      title: 'Totaux',
      items: [
        { id: 'gross_sales', label: 'Ventes brutes', value: formatCurrencyTyped(session.total_sales) },
        { id: 'returns', label: 'Retours', value: formatCurrencyTyped(session.total_returns) },
        {
          id: 'net_sales',
          label: 'Ventes nettes',
          value: formatCurrencyTyped(session.net_sales),
          highlight: true
        }
      ]
    },
    {
      id: 'cash',
      title: 'Caisse',
      items: [
        { id: 'opening', label: 'Ouverture', value: formatCurrencyTyped(session.opening_balance) },
        { id: 'cash_payments', label: 'Especes', value: formatCurrencyTyped(session.cash_payments) },
        {
          id: 'difference',
          label: 'Ecart',
          value: session.cash_difference !== undefined ? formatCurrencyTyped(session.cash_difference) : '-',
          highlight: !hasCashDifference(session)
        }
      ]
    }
  ];

  // Header actions
  const headerActions: ActionDefinition[] = [
    {
      id: 'back',
      label: 'Retour',
      icon: <ArrowLeft size={16} />,
      variant: 'secondary',
      onClick: () => navigate('/pos')
    },
    {
      id: 'edit',
      label: 'Modifier',
      icon: <Edit size={16} />,
      variant: 'secondary',
      onClick: () => console.log('Edit session')
    },
    {
      id: 'print',
      label: 'Imprimer',
      icon: <Printer size={16} />,
      variant: 'secondary',
      onClick: () => window.print()
    }
  ];

  // Primary actions (footer)
  const primaryActions: ActionDefinition[] = [];

  if (isSessionOpen(session)) {
    primaryActions.push({
      id: 'close',
      label: 'Cloturer la session',
      icon: <CheckCircle2 size={16} />,
      variant: 'primary',
      onClick: () => {
        closeSession.mutate({ id: session.id, closing_balance: 0 });
      }
    });
  }

  // Secondary actions
  const secondaryActions: ActionDefinition[] = [];

  if (isSessionClosed(session)) {
    secondaryActions.push({
      id: 'ticket',
      label: 'Ticket de cloture',
      icon: <Receipt size={16} />,
      variant: 'secondary',
      onClick: () => console.log('Print closing ticket')
    });
  }

  return (
    <BaseViewStandard<POSSessionType>
      title={`Session ${session.code}`}
      subtitle={session.terminal_name || session.terminal_code}
      status={{
        label: SESSION_STATUS_CONFIG[session.status]?.label || session.status,
        color: (SESSION_STATUS_CONFIG[session.status]?.color || 'gray') as SemanticColor
      }}
      data={session}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      primaryActions={primaryActions}
      secondaryActions={secondaryActions}
    />
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'stores' | 'terminals' | 'sessions' | 'transactions';

const POSModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: dashboard } = usePOSDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'stores', label: 'Magasins' },
    { id: 'terminals', label: 'Terminaux' },
    { id: 'sessions', label: 'Sessions' },
    { id: 'transactions', label: 'Transactions' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'stores':
        return <StoresView />;
      case 'terminals':
        return <TerminalsView />;
      case 'sessions':
        return <SessionsView />;
      case 'transactions':
        return <TransactionsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Sessions actives"
                value={String(dashboard?.active_sessions || 0)}
                icon={<Monitor size={24} />}
                variant="success"
                onClick={() => setCurrentView('sessions')}
              />
              <StatCard
                title="Ventes du jour"
                value={formatCurrency(dashboard?.sales_today || 0)}
                icon={<DollarSign size={24} />}
                variant="default"
              />
              <StatCard
                title="Transactions"
                value={String(dashboard?.transactions_today || 0)}
                icon={<Receipt size={24} />}
                variant="default"
                onClick={() => setCurrentView('transactions')}
              />
              <StatCard
                title="Panier moyen"
                value={formatCurrency(dashboard?.average_ticket || 0)}
                icon={<ShoppingCart size={24} />}
                variant="warning"
              />
            </Grid>
            {dashboard?.top_products && dashboard.top_products.length > 0 && (
              <Card>
                <h3 className="text-lg font-semibold mb-4">Top produits du jour</h3>
                <div className="space-y-2">
                  {dashboard.top_products.map((p, i) => (
                    <div key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span>{p.product_name}</span>
                      <div className="flex gap-4">
                        <span className="text-gray-500">{p.quantity} vendus</span>
                        <span className="font-semibold">{formatCurrency(p.amount)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        );
    }
  };

  return (
    <PageWrapper
      title="Point de Vente"
      subtitle="Gestion des caisses et ventes"
    >
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

// ============================================================================
// ROUTES WRAPPER
// ============================================================================

const POSRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<POSModule />} />
      <Route path="sessions/:id" element={<SessionDetailView />} />
    </Routes>
  );
};

export default POSRoutes;
