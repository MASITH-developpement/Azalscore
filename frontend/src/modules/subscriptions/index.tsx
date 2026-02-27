// @ts-nocheck
/**
 * AZALSCORE Module - Subscriptions
 * Gestion des abonnements et revenus recurrents
 */

import React, { useState } from 'react';
import {
  List, Users, DollarSign, TrendingDown, Gift, PlusCircle,
  ArrowLeft, Info, Package, Receipt, FileText, History, Sparkles,
  AlertCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { StatCard } from '@ui/dashboards';
import { Select } from '@ui/forms';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { BaseViewStandard, type TabDefinition, type SemanticColor } from '@ui/standards';
import { DataTable } from '@ui/tables';
import type { TableColumn } from '@/types';

// Import types
import { formatCurrency, formatDate, formatPercent } from '@/utils/formatters';

// Import hooks
import {
  subscriptionsKeys,
  useSubscriptionStats,
  usePlans,
  useSubscriptions,
  useSubscription,
  useInvoices,
  useCancelSubscription
} from './hooks';

// Import tab components
import {
  SubscriptionInfoTab,
  SubscriptionPlanTab,
  SubscriptionBillingTab,
  SubscriptionDocumentsTab,
  SubscriptionHistoryTab,
  SubscriptionIATab
} from './components';
import {
  INTERVALS, SUBSCRIPTION_STATUS, INVOICE_STATUS,
  SUBSCRIPTION_STATUS_CONFIG, INTERVAL_CONFIG,
  getDaysUntilRenewal, willCancel, getPaidInvoicesCount,
  getPlanPrice, getInvoiceNumber, getInvoiceAmount
} from './types';
import type {
  Plan, Subscription, SubscriptionInvoice, SubscriptionStats,
  SubscriptionStatus, PlanInterval
} from './types';

// Helper pour convertir string | number en number
const toNum = (val: string | number | null | undefined): number => {
  if (val === null || val === undefined) return 0;
  if (typeof val === 'number') return val;
  const parsed = parseFloat(val);
  return isNaN(parsed) ? 0 : parsed;
};

// Helpers pour Subscription
const getSubPlanName = (sub: Subscription): string => sub.plan_name || sub.plan_code || 'Plan';
const getSubStartDate = (sub: Subscription): string => sub.start_date || sub.started_at || sub.created_at;
const getSubAmount = (sub: Subscription): number => sub.amount ?? toNum(sub.mrr);
const getSubCurrency = (sub: Subscription): string => sub.currency || 'EUR';
const getSubPlanInterval = (sub: Subscription): PlanInterval => (sub.plan_code as PlanInterval) || 'MONTHLY';

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
// CONSTANTES LOCALES
// ============================================================================

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

// Navigation inter-modules
const _navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

// ============================================================================
// SUBSCRIPTION DETAIL VIEW (BaseViewStandard)
// ============================================================================

interface SubscriptionDetailViewProps {
  subscriptionId: string;
  onBack: () => void;
}

const SubscriptionDetailView: React.FC<SubscriptionDetailViewProps> = ({ subscriptionId, onBack }) => {
  const { data: subscription, isLoading } = useSubscription(subscriptionId);

  if (isLoading) {
    return (
      <div className="azals-loading-container">
        <div className="azals-spinner" />
        <p>Chargement de l'abonnement...</p>
      </div>
    );
  }

  if (!subscription) {
    return (
      <Card>
        <div className="text-center py-8">
          <AlertCircle size={48} className="text-danger mx-auto mb-4" />
          <h3 className="text-lg font-medium">Abonnement non trouve</h3>
          <p className="text-muted mt-2">L'abonnement demande n'existe pas.</p>
          <Button variant="secondary" onClick={onBack} className="mt-4">
            Retour
          </Button>
        </div>
      </Card>
    );
  }

  const statusConfig = SUBSCRIPTION_STATUS_CONFIG[subscription.status];
  const intervalConfig = INTERVAL_CONFIG[getSubPlanInterval(subscription)] || INTERVAL_CONFIG.MONTHLY;
  const invoicesCount = getPaidInvoicesCount(subscription);
  const daysUntilRenewal = getDaysUntilRenewal(subscription);
  const planName = getSubPlanName(subscription);
  const amount = getSubAmount(subscription);
  const currency = getSubCurrency(subscription);
  const startDate = getSubStartDate(subscription);

  // Tabs definition
  const tabs: TabDefinition<Subscription>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <Info size={16} />,
      component: SubscriptionInfoTab
    },
    {
      id: 'plan',
      label: 'Plan',
      icon: <Package size={16} />,
      component: SubscriptionPlanTab
    },
    {
      id: 'billing',
      label: 'Facturation',
      icon: <Receipt size={16} />,
      badge: invoicesCount > 0 ? invoicesCount : undefined,
      component: SubscriptionBillingTab
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={16} />,
      component: SubscriptionDocumentsTab
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <History size={16} />,
      component: SubscriptionHistoryTab
    },
    {
      id: 'ia',
      label: 'IA',
      icon: <Sparkles size={16} />,
      component: SubscriptionIATab
    }
  ];

  // InfoBar items
  const infoBarItems = [
    {
      id: 'plan',
      label: 'Plan',
      value: planName
    },
    {
      id: 'amount',
      label: 'Montant',
      value: `${formatCurrency(amount, currency)} ${intervalConfig.shortLabel}`,
      valueColor: 'primary' as SemanticColor
    },
    {
      id: 'status',
      label: 'Statut',
      value: statusConfig.label,
      valueColor: statusConfig.color as SemanticColor
    },
    {
      id: 'renewal',
      label: 'Renouvellement',
      value: willCancel(subscription) ? 'Annulation' : `${daysUntilRenewal}j`,
      valueColor: (willCancel(subscription) ? 'red' : daysUntilRenewal <= 7 ? 'orange' : undefined) as SemanticColor
    }
  ];

  // Sidebar sections
  const sidebarSections = [
    {
      id: 'summary',
      title: 'Resume',
      items: [
        { id: 'plan', label: 'Plan', value: planName },
        { id: 'amount', label: 'Montant', value: `${formatCurrency(amount, currency)} ${intervalConfig.shortLabel}`, highlight: true },
        { id: 'status', label: 'Statut', value: statusConfig.label },
        { id: 'start', label: 'Debut', value: formatDate(startDate) }
      ]
    },
    {
      id: 'client',
      title: 'Client',
      items: [
        { id: 'name', label: 'Nom', value: subscription.customer_name },
        { id: 'email', label: 'Email', value: subscription.customer_email }
      ]
    },
    {
      id: 'period',
      title: 'Periode en cours',
      items: [
        { id: 'end', label: 'Fin de periode', value: formatDate(subscription.current_period_end) },
        { id: 'renewal', label: 'Renouvellement', value: `Dans ${daysUntilRenewal} jours` }
      ]
    }
  ];

  // Header actions
  const headerActions = [
    {
      id: 'back',
      label: 'Retour',
      icon: <ArrowLeft size={16} />,
      onClick: onBack,
      variant: 'ghost' as const
    }
  ];

  return (
    <BaseViewStandard<Subscription>
      title={`Abonnement - ${subscription.customer_name || 'Client'}`}
      subtitle={`${planName} - ${intervalConfig.label}`}
      status={{
        label: statusConfig.label,
        color: statusConfig.color as SemanticColor
      }}
      data={subscription}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
    />
  );
};

// ============================================================================
// COMPOSANTS DE VUES (Lists)
// ============================================================================

const PlansView: React.FC = () => {
  const [showInactive, setShowInactive] = useState(false);
  const { data: plans = [], isLoading } = usePlans({
    is_active: showInactive ? undefined : true
  });

  const columns: TableColumn<Plan>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'price', header: 'Prix', accessor: 'base_price', render: (_, row) => formatCurrency(getPlanPrice(row as Plan), (row as Plan).currency) },
    { id: 'interval', header: 'Periode', accessor: 'interval', render: (v) => {
      const info = INTERVALS.find(i => i.value === v);
      return info?.label || (v as string);
    }},
    { id: 'trial_days', header: 'Essai', accessor: 'trial_days', render: (v) => (v as number) > 0 ? `${v} jours` : '-' },
    { id: 'subscribers_count', header: 'Abonnes', accessor: 'subscribers_count', render: (v) => <Badge color="blue">{(v as number) || 0}</Badge> },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <Button size="sm" variant="secondary" onClick={() => { window.dispatchEvent(new CustomEvent('azals:edit', { detail: { module: 'subscriptions', type: 'plan', id: (row as Plan).id } })); }}>Modifier</Button>
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
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:create', { detail: { module: 'subscriptions', type: 'plan' } })); }}>Nouveau plan</Button>
        </div>
      </div>
      <DataTable columns={columns} data={plans} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

interface SubscriptionsViewProps {
  onViewSubscription: (subscription: Subscription) => void;
}

const SubscriptionsView: React.FC<SubscriptionsViewProps> = ({ onViewSubscription }) => {
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
    { id: 'plan_name', header: 'Plan', accessor: 'plan_name', render: (_, row) => getSubPlanName(row as Subscription) },
    { id: 'amount', header: 'Montant', accessor: 'mrr', render: (_, row) => {
      const sub = row as Subscription;
      return formatCurrency(getSubAmount(sub), getSubCurrency(sub));
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const status = v as SubscriptionStatus;
      const config = SUBSCRIPTION_STATUS_CONFIG[status];
      return <Badge color={config?.color || 'gray'}>{config?.label || status}</Badge>;
    }},
    { id: 'start_date', header: 'Debut', accessor: 'started_at', render: (_, row) => formatDate(getSubStartDate(row as Subscription)) },
    { id: 'current_period_end', header: 'Fin periode', accessor: 'current_period_end', render: (v) => formatDate(v as string) },
    { id: 'cancel_at_period_end', header: 'Annulation', accessor: 'cancel_at_period_end', render: (v) => (v as boolean) ? (
      <Badge color="orange">Fin de periode</Badge>
    ) : null },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => {
      const sub = row as Subscription;
      return (
        <div className="flex gap-1">
          <Button size="sm" variant="secondary" onClick={() => onViewSubscription(sub)}>Detail</Button>
          {sub.status === 'ACTIVE' && !sub.cancel_at_period_end && (
            <Button
              size="sm"
              variant="danger"
              onClick={() => {
                if (confirm('Annuler cet abonnement a la fin de la periode?')) {
                  cancelSubscription.mutate({ id: String(sub.id), immediately: false });
                }
              }}
            >
              Annuler
            </Button>
          )}
        </div>
      );
    }}
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
              ...plans.map(p => ({ value: String(p.id), label: p.name }))
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
      <DataTable columns={columns} data={subscriptions} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

const InvoicesView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: invoices = [], isLoading } = useInvoices({
    status: filterStatus || undefined
  });

  const columns: TableColumn<SubscriptionInvoice>[] = [
    { id: 'number', header: 'N Facture', accessor: 'invoice_number', render: (_, row) => <code className="font-mono">{getInvoiceNumber(row as SubscriptionInvoice)}</code> },
    { id: 'customer_name', header: 'Client', accessor: 'customer_name' },
    { id: 'period_start', header: 'Periode', accessor: 'period_start', render: (v, row) => (
      `${formatDate(v as string)} - ${formatDate(row.period_end)}`
    )},
    { id: 'amount', header: 'Montant', accessor: 'total', render: (_, row) => {
      const inv = row as SubscriptionInvoice;
      return formatCurrency(getInvoiceAmount(inv), inv.currency);
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = INVOICE_STATUS.find(s => s.value === v);
      return <Badge color={STATUS_COLORS[v as string] || 'gray'}>{info?.label || (v as string)}</Badge>;
    }},
    { id: 'due_date', header: 'Echeance', accessor: 'due_date', render: (v) => formatDate(v as string) },
    { id: 'paid_at', header: 'Payee le', accessor: 'paid_at', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        <Button size="sm" variant="secondary" onClick={() => { window.dispatchEvent(new CustomEvent('azals:view', { detail: { module: 'subscriptions', type: 'invoice', id: (row as SubscriptionInvoice).id } })); }}>Voir</Button>
        <Button size="sm" variant="secondary" onClick={() => { window.dispatchEvent(new CustomEvent('azals:download', { detail: { module: 'subscriptions', type: 'invoice-pdf', id: (row as SubscriptionInvoice).id } })); }}>PDF</Button>
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
      <DataTable columns={columns} data={invoices} isLoading={isLoading} keyField="id" filterable />
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
            <div className="text-3xl font-bold text-blue-600">{formatCurrency(toNum(stats?.mrr))}</div>
            <div className="text-sm text-gray-500 mt-1">MRR (Revenu Mensuel Recurrent)</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{formatCurrency(toNum(stats?.arr))}</div>
            <div className="text-sm text-gray-500 mt-1">ARR (Revenu Annuel Recurrent)</div>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-600">{formatPercent(toNum(stats?.churn_rate))}</div>
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
          {formatCurrency(toNum(stats?.revenue_this_month))}
        </div>
      </Card>
    </div>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'plans' | 'subscriptions' | 'invoices' | 'metrics' | 'detail';

interface ViewState {
  view: View;
  subscriptionId?: string;
}

const SubscriptionsModule: React.FC = () => {
  const [viewState, setViewState] = useState<ViewState>({ view: 'dashboard' });
  const { data: stats } = useSubscriptionStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'plans', label: 'Plans' },
    { id: 'subscriptions', label: 'Abonnements' },
    { id: 'invoices', label: 'Factures' },
    { id: 'metrics', label: 'Metriques SaaS' }
  ];

  const handleViewSubscription = (subscription: Subscription) => {
    setViewState({ view: 'detail', subscriptionId: String(subscription.id) });
  };

  const handleBack = () => {
    setViewState({ view: 'subscriptions' });
  };

  // Detail view
  if (viewState.view === 'detail' && viewState.subscriptionId) {
    return (
      <SubscriptionDetailView subscriptionId={viewState.subscriptionId} onBack={handleBack} />
    );
  }

  const renderContent = () => {
    switch (viewState.view) {
      case 'plans':
        return <PlansView />;
      case 'subscriptions':
        return <SubscriptionsView onViewSubscription={handleViewSubscription} />;
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
                onClick={() => setViewState({ view: 'plans' })}
              />
              <StatCard
                title="Abonnes actifs"
                value={String(stats?.active_subscriptions || 0)}
                icon={<Users />}
                variant="success"
                onClick={() => setViewState({ view: 'subscriptions' })}
              />
              <StatCard
                title="MRR"
                value={formatCurrency(toNum(stats?.mrr))}
                icon={<DollarSign />}
                variant="default"
                onClick={() => setViewState({ view: 'metrics' })}
              />
              <StatCard
                title="Taux churn"
                value={formatPercent(toNum(stats?.churn_rate))}
                icon={<TrendingDown />}
                variant={toNum(stats?.churn_rate) > 5 ? 'danger' : 'success'}
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
              <div className="text-4xl font-bold text-green-600">{formatCurrency(toNum(stats?.arr))}</div>
            </Card>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Abonnements" subtitle="Gestion des revenus recurrents">
      <TabNav
        tabs={tabs}
        activeTab={viewState.view}
        onChange={(id) => setViewState({ view: id as View })}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default SubscriptionsModule;

// Re-export hooks for external use
export {
  subscriptionsKeys,
  useSubscriptionStats,
  usePlans,
  useSubscriptions,
  useSubscription,
  useInvoices,
  useCancelSubscription
} from './hooks';
