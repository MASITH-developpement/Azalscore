import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import { List, Users, DollarSign, TrendingDown, Gift, PlusCircle } from 'lucide-react';
import type { TableColumn } from '@/types';

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

interface Plan {
  id: string;
  code: string;
  name: string;
  description?: string;
  price: number;
  currency: string;
  interval: 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
  features: string[];
  trial_days: number;
  is_active: boolean;
  subscribers_count: number;
  created_at: string;
}

interface Subscription {
  id: string;
  plan_id: string;
  plan_name: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  status: 'ACTIVE' | 'TRIAL' | 'PAST_DUE' | 'CANCELLED' | 'EXPIRED';
  start_date: string;
  current_period_end: string;
  trial_end?: string;
  cancel_at_period_end: boolean;
  amount: number;
  currency: string;
  created_at: string;
}

interface Invoice {
  id: string;
  subscription_id: string;
  customer_name: string;
  number: string;
  status: 'DRAFT' | 'OPEN' | 'PAID' | 'VOID' | 'UNCOLLECTIBLE';
  amount: number;
  currency: string;
  period_start: string;
  period_end: string;
  due_date: string;
  paid_at?: string;
  created_at: string;
}

interface SubscriptionStats {
  total_plans: number;
  active_subscriptions: number;
  trial_subscriptions: number;
  mrr: number;
  arr: number;
  churn_rate: number;
  new_subscribers_month: number;
  revenue_this_month: number;
}

// ============================================================================
// CONSTANTES
// ============================================================================

const INTERVALS = [
  { value: 'MONTHLY', label: 'Mensuel' },
  { value: 'QUARTERLY', label: 'Trimestriel' },
  { value: 'YEARLY', label: 'Annuel' }
];

const SUBSCRIPTION_STATUS = [
  { value: 'ACTIVE', label: 'Actif' },
  { value: 'TRIAL', label: 'Essai' },
  { value: 'PAST_DUE', label: 'En retard' },
  { value: 'CANCELLED', label: 'Annule' },
  { value: 'EXPIRED', label: 'Expire' }
];

const INVOICE_STATUS = [
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'OPEN', label: 'Ouverte' },
  { value: 'PAID', label: 'Payee' },
  { value: 'VOID', label: 'Annulee' },
  { value: 'UNCOLLECTIBLE', label: 'Irrecouvrable' }
];

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'green',
  TRIAL: 'blue',
  PAST_DUE: 'orange',
  CANCELLED: 'red',
  EXPIRED: 'gray',
  DRAFT: 'gray',
  OPEN: 'blue',
  PAID: 'green',
  VOID: 'red',
  UNCOLLECTIBLE: 'red'
};

// ============================================================================
// HELPERS
// ============================================================================

const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);
};

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const formatPercent = (value: number): string => {
  return `${value.toFixed(1)}%`;
};

// Navigation inter-modules
const navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

// ============================================================================
// API HOOKS
// ============================================================================

const useSubscriptionStats = () => {
  return useQuery({
    queryKey: ['subscriptions', 'stats'],
    queryFn: async () => {
      return api.get<SubscriptionStats>('/v1/subscriptions/stats').then(r => r.data);
    }
  });
};

const usePlans = (filters?: { is_active?: boolean }) => {
  return useQuery({
    queryKey: ['subscriptions', 'plans', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
      const queryString = params.toString();
      const url = queryString ? `/v1/subscriptions/plans?${queryString}` : '/v1/subscriptions/plans';
      return api.get<Plan[]>(url).then(r => r.data);
    }
  });
};

const useSubscriptions = (filters?: { status?: string; plan_id?: string }) => {
  return useQuery({
    queryKey: ['subscriptions', 'list', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.plan_id) params.append('plan_id', filters.plan_id);
      const queryString = params.toString();
      const url = queryString ? `/v1/subscriptions?${queryString}` : '/v1/subscriptions';
      return api.get<Subscription[]>(url).then(r => r.data);
    }
  });
};

const useInvoices = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: ['subscriptions', 'invoices', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/v1/subscriptions/invoices?${queryString}` : '/v1/subscriptions/invoices';
      return api.get<Invoice[]>(url).then(r => r.data);
    }
  });
};

const useCancelSubscription = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, immediately }: { id: string; immediately?: boolean }) => {
      return api.post<void>(`/v1/subscriptions/${id}/cancel`, { immediately }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    }
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const PlansView: React.FC = () => {
  const [showInactive, setShowInactive] = useState(false);
  const { data: plans = [], isLoading } = usePlans({
    is_active: showInactive ? undefined : true
  });

  const columns: TableColumn<Plan>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'price', header: 'Prix', accessor: 'price', render: (v, row) => formatCurrency(v as number, row.currency) },
    { id: 'interval', header: 'Periode', accessor: 'interval', render: (v) => {
      const info = INTERVALS.find(i => i.value === v);
      return info?.label || (v as string);
    }},
    { id: 'trial_days', header: 'Essai', accessor: 'trial_days', render: (v) => (v as number) > 0 ? `${v} jours` : '-' },
    { id: 'subscribers_count', header: 'Abonnes', accessor: 'subscribers_count', render: (v) => <Badge color="blue">{v as number}</Badge> },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )},
    { id: 'actions', header: 'Actions', accessor: 'id', render: () => (
      <Button size="sm" variant="secondary">Modifier</Button>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Plans d'abonnement</h3>
        <div className="flex gap-2 items-center">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
            />
            Afficher inactifs
          </label>
          <Button>Nouveau plan</Button>
        </div>
      </div>
      <DataTable columns={columns} data={plans} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const SubscriptionsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterPlan, setFilterPlan] = useState<string>('');
  const { data: subscriptions = [], isLoading } = useSubscriptions({
    status: filterStatus || undefined,
    plan_id: filterPlan || undefined
  });
  const { data: plans = [] } = usePlans();
  const cancelSubscription = useCancelSubscription();

  const columns: TableColumn<Subscription>[] = [
    { id: 'customer_name', header: 'Client', accessor: 'customer_name' },
    { id: 'customer_email', header: 'Email', accessor: 'customer_email', render: (v) => (
      <span className="text-sm text-gray-600">{v as string}</span>
    )},
    { id: 'plan_name', header: 'Plan', accessor: 'plan_name' },
    { id: 'amount', header: 'Montant', accessor: 'amount', render: (v, row) => formatCurrency(v as number, row.currency) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = SUBSCRIPTION_STATUS.find(s => s.value === v);
      return <Badge color={STATUS_COLORS[v as string] || 'gray'}>{info?.label || (v as string)}</Badge>;
    }},
    { id: 'start_date', header: 'Debut', accessor: 'start_date', render: (v) => formatDate(v as string) },
    { id: 'current_period_end', header: 'Fin periode', accessor: 'current_period_end', render: (v) => formatDate(v as string) },
    { id: 'cancel_at_period_end', header: 'Annulation', accessor: 'cancel_at_period_end', render: (v) => (v as boolean) ? (
      <Badge color="orange">Fin de periode</Badge>
    ) : null },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        <Button size="sm" variant="secondary">Detail</Button>
        {row.status === 'ACTIVE' && !row.cancel_at_period_end && (
          <Button
            size="sm"
            variant="danger"
            onClick={() => {
              if (confirm('Annuler cet abonnement a la fin de la periode?')) {
                cancelSubscription.mutate({ id: row.id, immediately: false });
              }
            }}
          >
            Annuler
          </Button>
        )}
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Abonnements</h3>
        <div className="flex gap-2">
          <Select
            value={filterPlan}
            onChange={(v) => setFilterPlan(v)}
            options={[
              { value: '', label: 'Tous les plans' },
              ...plans.map(p => ({ value: p.id, label: p.name }))
            ]}
            className="w-40"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...SUBSCRIPTION_STATUS]}
            className="w-36"
          />
        </div>
      </div>
      <DataTable columns={columns} data={subscriptions} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const InvoicesView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: invoices = [], isLoading } = useInvoices({
    status: filterStatus || undefined
  });

  const columns: TableColumn<Invoice>[] = [
    { id: 'number', header: 'N Facture', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'customer_name', header: 'Client', accessor: 'customer_name' },
    { id: 'period_start', header: 'Periode', accessor: 'period_start', render: (v, row) => (
      `${formatDate(v as string)} - ${formatDate(row.period_end)}`
    )},
    { id: 'amount', header: 'Montant', accessor: 'amount', render: (v, row) => formatCurrency(v as number, row.currency) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = INVOICE_STATUS.find(s => s.value === v);
      return <Badge color={STATUS_COLORS[v as string] || 'gray'}>{info?.label || (v as string)}</Badge>;
    }},
    { id: 'due_date', header: 'Echeance', accessor: 'due_date', render: (v) => formatDate(v as string) },
    { id: 'paid_at', header: 'Payee le', accessor: 'paid_at', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: () => (
      <div className="flex gap-1">
        <Button size="sm" variant="secondary">Voir</Button>
        <Button size="sm" variant="secondary">PDF</Button>
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Factures recurrentes</h3>
        <Select
          value={filterStatus}
          onChange={(v) => setFilterStatus(v)}
          options={[{ value: '', label: 'Tous statuts' }, ...INVOICE_STATUS]}
          className="w-36"
        />
      </div>
      <DataTable columns={columns} data={invoices} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const MetricsView: React.FC = () => {
  const { data: stats, isLoading } = useSubscriptionStats();

  if (isLoading) {
    return <Card><div className="text-center py-8">Chargement des metriques...</div></Card>;
  }

  return (
    <div className="space-y-4">
      <Grid cols={4}>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{formatCurrency(stats?.mrr || 0)}</div>
            <div className="text-sm text-gray-500 mt-1">MRR (Revenu Mensuel Recurrent)</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{formatCurrency(stats?.arr || 0)}</div>
            <div className="text-sm text-gray-500 mt-1">ARR (Revenu Annuel Recurrent)</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-600">{formatPercent(stats?.churn_rate || 0)}</div>
            <div className="text-sm text-gray-500 mt-1">Taux de Churn</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600">{stats?.new_subscribers_month || 0}</div>
            <div className="text-sm text-gray-500 mt-1">Nouveaux abonnes (mois)</div>
          </div>
        </Card>
      </Grid>

      <Card>
        <h3 className="text-lg font-semibold mb-4">Repartition des abonnements</h3>
        <Grid cols={3}>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{stats?.active_subscriptions || 0}</div>
            <div className="text-sm text-gray-600">Actifs</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{stats?.trial_subscriptions || 0}</div>
            <div className="text-sm text-gray-600">En essai</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-600">{stats?.total_plans || 0}</div>
            <div className="text-sm text-gray-600">Plans disponibles</div>
          </div>
        </Grid>
      </Card>

      <Card>
        <h3 className="text-lg font-semibold mb-4">Revenu ce mois</h3>
        <div className="text-4xl font-bold text-center py-8 text-green-600">
          {formatCurrency(stats?.revenue_this_month || 0)}
        </div>
      </Card>
    </div>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'plans' | 'subscriptions' | 'invoices' | 'metrics';

const SubscriptionsModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats } = useSubscriptionStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'plans', label: 'Plans' },
    { id: 'subscriptions', label: 'Abonnements' },
    { id: 'invoices', label: 'Factures' },
    { id: 'metrics', label: 'Metriques SaaS' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'plans':
        return <PlansView />;
      case 'subscriptions':
        return <SubscriptionsView />;
      case 'invoices':
        return <InvoicesView />;
      case 'metrics':
        return <MetricsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Plans actifs"
                value={String(stats?.total_plans || 0)}
                icon={<List />}
                variant="default"
                onClick={() => setCurrentView('plans')}
              />
              <StatCard
                title="Abonnes actifs"
                value={String(stats?.active_subscriptions || 0)}
                icon={<Users />}
                variant="success"
                onClick={() => setCurrentView('subscriptions')}
              />
              <StatCard
                title="MRR"
                value={formatCurrency(stats?.mrr || 0)}
                icon={<DollarSign />}
                variant="default"
                onClick={() => setCurrentView('metrics')}
              />
              <StatCard
                title="Taux churn"
                value={formatPercent(stats?.churn_rate || 0)}
                icon={<TrendingDown />}
                variant={stats?.churn_rate && stats.churn_rate > 5 ? 'danger' : 'success'}
              />
            </Grid>

            <Grid cols={2}>
              <StatCard
                title="En essai"
                value={String(stats?.trial_subscriptions || 0)}
                icon={<Gift />}
                variant="default"
              />
              <StatCard
                title="Nouveaux ce mois"
                value={String(stats?.new_subscribers_month || 0)}
                icon={<PlusCircle />}
                variant="success"
              />
            </Grid>

            <Card>
              <h3 className="text-lg font-semibold mb-2">Revenu Annuel Recurrent (ARR)</h3>
              <div className="text-4xl font-bold text-green-600">{formatCurrency(stats?.arr || 0)}</div>
            </Card>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Abonnements" subtitle="Gestion des revenus recurrents">
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

export default SubscriptionsModule;
