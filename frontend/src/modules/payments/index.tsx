/**
 * AZALSCORE Module - Payments
 * Gestion des paiements et transactions
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import { BaseViewStandard, type TabDefinition, type SemanticColor } from '@ui/standards';
import type { TableColumn } from '@/types';
import {
  DollarSign, BarChart2, Clock, AlertCircle, Calendar, TrendingUp, RotateCcw,
  CreditCard, FileText, History, Sparkles, ArrowLeft, Info, Receipt
} from 'lucide-react';
import { LoadingState } from '@ui/components/StateViews';

// Import types from types.ts
import type {
  Payment, Refund, SavedPaymentMethod, PaymentStats,
  PaymentMethod as PaymentMethodType, PaymentStatus
} from './types';
import {
  PAYMENT_METHODS, PAYMENT_STATUS, REFUND_STATUS,
  PAYMENT_STATUS_CONFIG, METHOD_CONFIG,
  getMethodLabel, getMethodIcon
} from './types';
import { formatCurrency, formatDate, formatDateTime } from '@/utils/formatters';

// Import tab components
import {
  PaymentInfoTab,
  PaymentDetailsTab,
  PaymentRefundsTab,
  PaymentDocumentsTab,
  PaymentHistoryTab,
  PaymentIATab
} from './components';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

interface TabNavProps {
  tabs: Array<{ id: string; label: string }>;
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
  PENDING: 'orange',
  PROCESSING: 'blue',
  COMPLETED: 'green',
  FAILED: 'red',
  REFUNDED: 'gray',
  CANCELLED: 'red'
};

// Navigation inter-modules
const navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

// ============================================================================
// API HOOKS
// ============================================================================

const usePaymentStats = () => {
  return useQuery({
    queryKey: ['payments', 'stats'],
    queryFn: async () => {
      const response = await api.get<PaymentStats>('/v3/payments/summary').then(r => r.data);
      return response;
    }
  });
};

const usePayments = (filters?: { status?: string; method?: string; date_from?: string; date_to?: string }) => {
  return useQuery({
    queryKey: ['payments', 'list', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.method) params.append('method', filters.method);
      if (filters?.date_from) params.append('date_from', filters.date_from);
      if (filters?.date_to) params.append('date_to', filters.date_to);
      const queryString = params.toString();
      const url = queryString ? `/v3/payments?${queryString}` : '/v3/payments';
      const response = await api.get<{ items: Payment[] }>(url).then(r => r.data);
      return response?.items || [];
    }
  });
};

const usePayment = (id: string) => {
  return useQuery({
    queryKey: ['payments', 'detail', id],
    queryFn: async () => {
      const response = await api.get<Payment>(`/v3/payments/${id}`).then(r => r.data);
      return response;
    },
    enabled: !!id
  });
};

const useRefunds = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: ['payments', 'refunds', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/v3/payments/refunds?${queryString}` : '/v3/payments/refunds';
      const response = await api.get<Refund[]>(url).then(r => r.data);
      return response;
    }
  });
};

const usePaymentMethods = (filters?: { customer_id?: string }) => {
  return useQuery({
    queryKey: ['payments', 'methods', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.customer_id) params.append('customer_id', filters.customer_id);
      const queryString = params.toString();
      const url = queryString ? `/v3/payments/methods?${queryString}` : '/v3/payments/methods';
      const response = await api.get<SavedPaymentMethod[]>(url).then(r => r.data);
      return response;
    }
  });
};

const useCreateRefund = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { payment_id: string; amount: number; reason: string }) => {
      return api.post('/v3/payments/refunds', data).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
    }
  });
};

const useRetryPayment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (paymentId: string) => {
      return api.post(`/v3/payments/${paymentId}/retry`).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
    }
  });
};

// ============================================================================
// PAYMENT DETAIL VIEW (BaseViewStandard)
// ============================================================================

interface PaymentDetailViewProps {
  paymentId: string;
  onBack: () => void;
}

const PaymentDetailView: React.FC<PaymentDetailViewProps> = ({ paymentId, onBack }) => {
  const { data: payment, isLoading, refetch } = usePayment(paymentId);

  if (isLoading) {
    return <LoadingState onRetry={() => refetch()} message="Chargement du paiement..." />;
  }

  if (!payment) {
    return (
      <Card>
        <div className="text-center py-8">
          <AlertCircle size={48} className="text-danger mx-auto mb-4" />
          <h3 className="text-lg font-medium">Paiement non trouve</h3>
          <p className="text-muted mt-2">Le paiement demande n'existe pas.</p>
          <Button variant="secondary" onClick={onBack} className="mt-4">
            Retour
          </Button>
        </div>
      </Card>
    );
  }

  const statusConfig = PAYMENT_STATUS_CONFIG[payment.status];
  const methodConfig = METHOD_CONFIG[payment.method];
  const refundCount = payment.refunds?.length || 0;

  // Tabs definition
  const tabs: TabDefinition<Payment>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <Info size={16} />,
      component: PaymentInfoTab
    },
    {
      id: 'details',
      label: 'Details techniques',
      icon: <CreditCard size={16} />,
      component: PaymentDetailsTab
    },
    {
      id: 'refunds',
      label: 'Remboursements',
      icon: <RotateCcw size={16} />,
      badge: refundCount > 0 ? refundCount : undefined,
      component: PaymentRefundsTab
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={16} />,
      component: PaymentDocumentsTab
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <History size={16} />,
      component: PaymentHistoryTab
    },
    {
      id: 'ia',
      label: 'IA',
      icon: <Sparkles size={16} />,
      component: PaymentIATab
    }
  ];

  // InfoBar items
  const infoBarItems = [
    {
      id: 'amount',
      label: 'Montant',
      value: formatCurrency(payment.amount, payment.currency),
      valueColor: 'primary' as SemanticColor
    },
    {
      id: 'method',
      label: 'Methode',
      value: `${methodConfig.icon} ${methodConfig.label}`
    },
    {
      id: 'status',
      label: 'Statut',
      value: statusConfig.label,
      valueColor: statusConfig.color as SemanticColor
    },
    {
      id: 'date',
      label: 'Date',
      value: formatDate(payment.created_at)
    }
  ];

  // Sidebar sections
  const sidebarSections = [
    {
      id: 'summary',
      title: 'Resume',
      items: [
        { id: 'ref', label: 'Reference', value: payment.reference },
        { id: 'amount', label: 'Montant', value: formatCurrency(payment.amount, payment.currency), highlight: true },
        { id: 'status', label: 'Statut', value: statusConfig.label },
        { id: 'method', label: 'Methode', value: methodConfig.label }
      ]
    },
    {
      id: 'client',
      title: 'Client',
      items: payment.customer_name ? [
        { id: 'name', label: 'Nom', value: payment.customer_name },
        ...(payment.customer_email ? [{ id: 'email', label: 'Email', value: payment.customer_email }] : [])
      ] : [
        { id: 'none', label: '', value: 'Pas de client associe' }
      ]
    },
    {
      id: 'dates',
      title: 'Dates',
      items: [
        { id: 'created', label: 'Creation', value: formatDateTime(payment.created_at) },
        ...(payment.processed_at ? [{ id: 'processed', label: 'Traitement', value: formatDateTime(payment.processed_at) }] : [])
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
    <BaseViewStandard<Payment>
      title={`Paiement ${payment.reference}`}
      subtitle={`${methodConfig.label} - ${payment.customer_name || 'Client anonyme'}`}
      status={{
        label: statusConfig.label,
        color: statusConfig.color as SemanticColor
      }}
      data={payment}
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

interface TransactionsViewProps {
  onViewPayment: (payment: Payment) => void;
}

const TransactionsView: React.FC<TransactionsViewProps> = ({ onViewPayment }) => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterMethod, setFilterMethod] = useState<string>('');
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [showRefundModal, setShowRefundModal] = useState(false);
  const { data: payments = [], isLoading } = usePayments({
    status: filterStatus || undefined,
    method: filterMethod || undefined
  });
  const retryPayment = useRetryPayment();
  const createRefund = useCreateRefund();

  const columns: TableColumn<Payment>[] = [
    { id: 'reference', header: 'Reference', accessor: 'reference', render: (v) => (
      <code className="font-mono text-sm">{v as string}</code>
    )},
    { id: 'method', header: 'Methode', accessor: 'method', render: (v) => {
      const val = v as PaymentMethodType;
      const config = METHOD_CONFIG[val];
      return <span>{config?.icon} {config?.label || val}</span>;
    }},
    { id: 'customer_name', header: 'Client', accessor: 'customer_name', render: (v) => (v as string) || '-' },
    { id: 'invoice_number', header: 'Facture', accessor: 'invoice_number', render: (v) => (v as string) ? (
      <code className="font-mono text-sm">{v as string}</code>
    ) : '-' },
    { id: 'amount', header: 'Montant', accessor: 'amount', render: (v, row) => formatCurrency(v as number, (row as Payment).currency) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const val = v as PaymentStatus;
      const config = PAYMENT_STATUS_CONFIG[val];
      return <Badge color={config?.color || 'gray'}>{config?.label || val}</Badge>;
    }},
    { id: 'created_at', header: 'Date', accessor: 'created_at', render: (v) => formatDateTime(v as string) },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => {
      const payment = row as Payment;
      return (
        <div className="flex gap-1">
          <Button size="sm" variant="secondary" onClick={() => onViewPayment(payment)}>Detail</Button>
          {payment.status === 'FAILED' && (
            <Button size="sm" variant="warning" onClick={() => retryPayment.mutate(payment.id)}>Reessayer</Button>
          )}
          {payment.status === 'COMPLETED' && (
            <Button size="sm" variant="secondary" onClick={() => { setSelectedPayment(payment); setShowRefundModal(true); }}>Rembourser</Button>
          )}
        </div>
      );
    }}
  ];

  return (
    <>
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Transactions</h3>
          <div className="flex gap-2">
            <div className="azals-field">
              <Select
                value={filterMethod}
                onChange={(v) => setFilterMethod(v)}
                options={[{ value: '', label: 'Toutes methodes' }, ...PAYMENT_METHODS.map(m => ({ value: m.value, label: m.label }))]}
                className="w-40"
              />
            </div>
            <div className="azals-field">
              <Select
                value={filterStatus}
                onChange={(v) => setFilterStatus(v)}
                options={[{ value: '', label: 'Tous statuts' }, ...PAYMENT_STATUS]}
                className="w-36"
              />
            </div>
          </div>
        </div>
        <DataTable columns={columns} data={payments} isLoading={isLoading} keyField="id" filterable />
      </Card>

      {/* Modal de remboursement */}
      {showRefundModal && selectedPayment && (
        <Modal
          isOpen={true}
          onClose={() => { setShowRefundModal(false); setSelectedPayment(null); }}
          title={`Rembourser ${selectedPayment.reference}`}
        >
          <form onSubmit={(e) => {
            e.preventDefault();
            const form = e.target as HTMLFormElement;
            const formData = new FormData(form);
            createRefund.mutate({
              payment_id: selectedPayment.id,
              amount: parseFloat(formData.get('amount') as string),
              reason: formData.get('reason') as string
            }, {
              onSuccess: () => {
                setShowRefundModal(false);
                setSelectedPayment(null);
              }
            });
          }}>
            <div className="space-y-4">
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Montant a rembourser</label>
                <input
                  type="number"
                  name="amount"
                  defaultValue={selectedPayment.amount}
                  max={selectedPayment.amount}
                  step="0.01"
                  required
                  className="azals-input"
                />
                <div className="text-sm text-gray-500 mt-1">Maximum: {formatCurrency(selectedPayment.amount)}</div>
              </div>
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Raison du remboursement</label>
                <textarea
                  name="reason"
                  placeholder="Expliquez la raison du remboursement..."
                  className="azals-input"
                  rows={4}
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="secondary" onClick={() => { setShowRefundModal(false); setSelectedPayment(null); }}>Annuler</Button>
                <Button type="submit" variant="danger" disabled={createRefund.isPending}>Rembourser</Button>
              </div>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
};

const RefundsView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: refunds = [], isLoading } = useRefunds({
    status: filterStatus || undefined
  });

  const columns: TableColumn<Refund>[] = [
    { id: 'payment_reference', header: 'Paiement', accessor: 'payment_reference', render: (v) => (
      <code className="font-mono text-sm">{v as string}</code>
    )},
    { id: 'amount', header: 'Montant', accessor: 'amount', render: (v, row) => formatCurrency(v as number, (row as Refund).currency) },
    { id: 'reason', header: 'Raison', accessor: 'reason', render: (v) => {
      const val = v as string;
      return <span className="text-sm">{val.length > 50 ? val.substring(0, 50) + '...' : val}</span>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const val = v as string;
      const info = REFUND_STATUS.find(s => s.value === val);
      return <Badge color={STATUS_COLORS[val] || 'gray'}>{info?.label || val}</Badge>;
    }},
    { id: 'created_at', header: 'Demande le', accessor: 'created_at', render: (v) => formatDateTime(v as string) },
    { id: 'processed_at', header: 'Traite le', accessor: 'processed_at', render: (v) => (v as string) ? formatDateTime(v as string) : '-' }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Remboursements</h3>
        <div className="azals-field">
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...REFUND_STATUS]}
            className="w-36"
          />
        </div>
      </div>
      <DataTable columns={columns} data={refunds} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

const PaymentMethodsView: React.FC = () => {
  const { data: methods = [], isLoading } = usePaymentMethods();

  const columns: TableColumn<SavedPaymentMethod>[] = [
    { id: 'customer_name', header: 'Client', accessor: 'customer_name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const val = v as string;
      const labels: Record<string, string> = { CARD: 'Carte', BANK_ACCOUNT: 'Compte bancaire', SEPA: 'SEPA' };
      return labels[val] || val;
    }},
    { id: 'last_four', header: 'Numero', accessor: 'last_four', render: (v, row) => {
      const val = v as string;
      const method = row as SavedPaymentMethod;
      if (!val) return '-';
      return <span>.... {val} {method.brand && <Badge color="blue">{method.brand}</Badge>}</span>;
    }},
    { id: 'expiry', header: 'Expiration', accessor: 'expiry_month', render: (v, row) => {
      const val = v as number;
      const method = row as SavedPaymentMethod;
      if (!val) return '-';
      return `${String(val).padStart(2, '0')}/${method.expiry_year}`;
    }},
    { id: 'is_default', header: 'Par defaut', accessor: 'is_default', render: (v) => (v as boolean) ? <Badge color="green">Oui</Badge> : null },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => {
      const val = v as boolean;
      return <Badge color={val ? 'green' : 'gray'}>{val ? 'Oui' : 'Non'}</Badge>;
    }},
    { id: 'created_at', header: 'Ajoute le', accessor: 'created_at', render: (v) => formatDate(v as string) }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Moyens de paiement enregistres</h3>
      </div>
      <DataTable columns={columns} data={methods} isLoading={isLoading} keyField="id" filterable />
    </Card>
  );
};

const TapToPayView: React.FC = () => {
  return (
    <div className="space-y-4">
      <Card>
        <div className="text-center py-8">
          <div className="text-6xl mb-4">📱</div>
          <h3 className="text-2xl font-bold mb-2">Tap-to-Pay</h3>
          <p className="text-gray-600 mb-6">
            Encaissez directement avec votre smartphone grace au paiement sans contact NFC.
          </p>
          <Button size="lg" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'configureTapToPay' } })); }}>Configurer Tap-to-Pay</Button>
        </div>
      </Card>

      <Grid cols={2}>
        <Card>
          <h4 className="font-semibold mb-3">Compatible avec</h4>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center gap-2"><Badge color="blue">Visa</Badge> Cartes Visa</li>
            <li className="flex items-center gap-2"><Badge color="orange">Mastercard</Badge> Cartes Mastercard</li>
            <li className="flex items-center gap-2"><Badge color="green">CB</Badge> Cartes bancaires francaises</li>
            <li className="flex items-center gap-2"><Badge color="purple">Apple Pay</Badge> Apple Pay</li>
            <li className="flex items-center gap-2"><Badge color="green">Google Pay</Badge> Google Pay</li>
          </ul>
        </Card>
        <Card>
          <h4 className="font-semibold mb-3">Configuration requise</h4>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>- Smartphone avec NFC active</li>
            <li>- iOS 15.4+ ou Android 9+</li>
            <li>- Application AZALSCORE mobile installee</li>
            <li>- Compte marchand verifie</li>
          </ul>
        </Card>
      </Grid>
    </div>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'transactions' | 'refunds' | 'methods' | 'tap-to-pay' | 'detail';

interface ViewState {
  view: View;
  paymentId?: string;
}

const PaymentsModule: React.FC = () => {
  const [viewState, setViewState] = useState<ViewState>({ view: 'dashboard' });
  const { data: stats } = usePaymentStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'transactions', label: 'Transactions' },
    { id: 'refunds', label: 'Remboursements' },
    { id: 'methods', label: 'Moyens de paiement' },
    { id: 'tap-to-pay', label: 'Tap-to-Pay' }
  ];

  const handleViewPayment = (payment: Payment) => {
    setViewState({ view: 'detail', paymentId: payment.id });
  };

  const handleBack = () => {
    setViewState({ view: 'transactions' });
  };

  // Detail view
  if (viewState.view === 'detail' && viewState.paymentId) {
    return (
      <PaymentDetailView paymentId={viewState.paymentId} onBack={handleBack} />
    );
  }

  const renderContent = () => {
    switch (viewState.view) {
      case 'transactions':
        return <TransactionsView onViewPayment={handleViewPayment} />;
      case 'refunds':
        return <RefundsView />;
      case 'methods':
        return <PaymentMethodsView />;
      case 'tap-to-pay':
        return <TapToPayView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Encaisse aujourd'hui"
                value={formatCurrency(stats?.total_today || 0)}
                icon={<DollarSign size={20} />}
                variant="success"
                onClick={() => setViewState({ view: 'transactions' })}
              />
              <StatCard
                title="Transactions aujourd'hui"
                value={String(stats?.transactions_today || 0)}
                icon={<BarChart2 size={20} />}
                variant="default"
              />
              <StatCard
                title="En attente"
                value={String(stats?.pending_count || 0)}
                icon={<Clock size={20} />}
                variant={stats?.pending_count ? 'warning' : 'success'}
              />
              <StatCard
                title="Echouees"
                value={String(stats?.failed_count || 0)}
                icon={<AlertCircle size={20} />}
                variant={stats?.failed_count ? 'danger' : 'success'}
              />
            </Grid>

            <Grid cols={3}>
              <StatCard
                title="Cette semaine"
                value={formatCurrency(stats?.total_this_week || 0)}
                icon={<Calendar size={20} />}
                variant="default"
              />
              <StatCard
                title="Ce mois"
                value={formatCurrency(stats?.total_this_month || 0)}
                icon={<TrendingUp size={20} />}
                variant="default"
              />
              <StatCard
                title="Remboursements ce mois"
                value={formatCurrency(stats?.refunded_amount_month || 0)}
                icon={<RotateCcw size={20} />}
                variant="default"
                onClick={() => setViewState({ view: 'refunds' })}
              />
            </Grid>

            <Card>
              <h3 className="text-lg font-semibold mb-4">Panier moyen</h3>
              <div className="text-4xl font-bold text-center py-4 text-blue-600">
                {formatCurrency(stats?.average_transaction || 0)}
              </div>
            </Card>
          </div>
        );
    }
  };

  return (
    <PageWrapper
      title="Paiements"
      subtitle="Encaissements et transactions"
    >
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

export default PaymentsModule;
