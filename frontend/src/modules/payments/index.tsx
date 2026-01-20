import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import type { TableColumn } from '@/types';
import { DollarSign, BarChart2, Clock, AlertCircle, Calendar, TrendingUp, RotateCcw } from 'lucide-react';

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
// TYPES
// ============================================================================

interface Payment {
  id: string;
  reference: string;
  amount: number;
  currency: string;
  method: 'CARD' | 'BANK_TRANSFER' | 'TAP_TO_PAY' | 'CASH' | 'CHECK' | 'OTHER';
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED' | 'REFUNDED' | 'CANCELLED';
  customer_id?: string;
  customer_name?: string;
  customer_email?: string;
  invoice_id?: string;
  invoice_number?: string;
  description?: string;
  metadata?: Record<string, any>;
  error_message?: string;
  processed_at?: string;
  created_at: string;
}

interface Refund {
  id: string;
  payment_id: string;
  payment_reference: string;
  amount: number;
  currency: string;
  reason: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  processed_at?: string;
  created_at: string;
}

interface PaymentMethod {
  id: string;
  customer_id: string;
  customer_name: string;
  type: 'CARD' | 'BANK_ACCOUNT' | 'SEPA';
  last_four?: string;
  brand?: string;
  expiry_month?: number;
  expiry_year?: number;
  is_default: boolean;
  is_active: boolean;
  created_at: string;
}

interface PaymentStats {
  total_today: number;
  transactions_today: number;
  total_this_week: number;
  transactions_this_week: number;
  total_this_month: number;
  transactions_this_month: number;
  pending_count: number;
  failed_count: number;
  refunded_amount_month: number;
  average_transaction: number;
}

// ============================================================================
// CONSTANTES
// ============================================================================

const PAYMENT_METHODS = [
  { value: 'CARD', label: 'Carte bancaire' },
  { value: 'BANK_TRANSFER', label: 'Virement' },
  { value: 'TAP_TO_PAY', label: 'Tap-to-Pay' },
  { value: 'CASH', label: 'Especes' },
  { value: 'CHECK', label: 'Cheque' },
  { value: 'OTHER', label: 'Autre' }
];

const PAYMENT_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'PROCESSING', label: 'En cours' },
  { value: 'COMPLETED', label: 'Complete' },
  { value: 'FAILED', label: 'Echoue' },
  { value: 'REFUNDED', label: 'Rembourse' },
  { value: 'CANCELLED', label: 'Annule' }
];

const REFUND_STATUS = [
  { value: 'PENDING', label: 'En attente' },
  { value: 'PROCESSING', label: 'En cours' },
  { value: 'COMPLETED', label: 'Effectue' },
  { value: 'FAILED', label: 'Echoue' }
];

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'orange',
  PROCESSING: 'blue',
  COMPLETED: 'green',
  FAILED: 'red',
  REFUNDED: 'gray',
  CANCELLED: 'red'
};

const METHOD_ICONS: Record<string, string> = {
  CARD: '',
  BANK_TRANSFER: '',
  TAP_TO_PAY: '',
  CASH: '',
  CHECK: '',
  OTHER: ''
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

const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
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
      const response = await api.get<PaymentStats>('/v1/payments/summary').then(r => r.data);
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
      const url = queryString ? `/v1/payments?${queryString}` : '/v1/payments';
      const response = await api.get<{ items: Payment[] }>(url).then(r => r.data);
      return response?.items || [];
    }
  });
};

const useRefunds = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: ['payments', 'refunds', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const url = queryString ? `/v1/payments/refunds?${queryString}` : '/v1/payments/refunds';
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
      const url = queryString ? `/v1/payments/methods?${queryString}` : '/v1/payments/methods';
      const response = await api.get<PaymentMethod[]>(url).then(r => r.data);
      return response;
    }
  });
};

const useCreateRefund = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { payment_id: string; amount: number; reason: string }) => {
      return api.post('/v1/payments/refunds', data).then(r => r.data);
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
      return api.post(`/v1/payments/${paymentId}/retry`).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
    }
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const TransactionsView: React.FC = () => {
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
      const val = v as string;
      const info = PAYMENT_METHODS.find(m => m.value === val);
      return <span>{METHOD_ICONS[val]} {info?.label || val}</span>;
    }},
    { id: 'customer_name', header: 'Client', accessor: 'customer_name', render: (v) => (v as string) || '-' },
    { id: 'invoice_number', header: 'Facture', accessor: 'invoice_number', render: (v) => (v as string) ? (
      <code className="font-mono text-sm">{v as string}</code>
    ) : '-' },
    { id: 'amount', header: 'Montant', accessor: 'amount', render: (v, row) => formatCurrency(v as number, (row as Payment).currency) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const val = v as string;
      const info = PAYMENT_STATUS.find(s => s.value === val);
      return <Badge color={STATUS_COLORS[val] || 'gray'}>{info?.label || val}</Badge>;
    }},
    { id: 'created_at', header: 'Date', accessor: 'created_at', render: (v) => formatDateTime(v as string) },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => {
      const payment = row as Payment;
      return (
        <div className="flex gap-1">
          <Button size="sm" variant="secondary" onClick={() => setSelectedPayment(payment)}>Detail</Button>
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
                options={[{ value: '', label: 'Toutes methodes' }, ...PAYMENT_METHODS]}
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
        <DataTable columns={columns} data={payments} isLoading={isLoading} keyField="id" />
      </Card>

      {/* Detail du paiement */}
      {selectedPayment && !showRefundModal && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedPayment(null)}
          title={`Paiement ${selectedPayment.reference}`}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-500">Montant</div>
                <div className="text-2xl font-bold">{formatCurrency(selectedPayment.amount, selectedPayment.currency)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-500">Statut</div>
                <Badge color={STATUS_COLORS[selectedPayment.status] || 'gray'}>
                  {PAYMENT_STATUS.find(s => s.value === selectedPayment.status)?.label}
                </Badge>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-gray-500">Methode</div>
                <div>{METHOD_ICONS[selectedPayment.method]} {PAYMENT_METHODS.find(m => m.value === selectedPayment.method)?.label}</div>
              </div>
              <div>
                <div className="text-gray-500">Date</div>
                <div>{formatDateTime(selectedPayment.created_at)}</div>
              </div>
              {selectedPayment.customer_name && (
                <div>
                  <div className="text-gray-500">Client</div>
                  <div>{selectedPayment.customer_name}</div>
                </div>
              )}
              {selectedPayment.customer_email && (
                <div>
                  <div className="text-gray-500">Email</div>
                  <div>{selectedPayment.customer_email}</div>
                </div>
              )}
              {selectedPayment.invoice_number && (
                <div>
                  <div className="text-gray-500">Facture</div>
                  <div><code>{selectedPayment.invoice_number}</code></div>
                </div>
              )}
              {selectedPayment.processed_at && (
                <div>
                  <div className="text-gray-500">Traite le</div>
                  <div>{formatDateTime(selectedPayment.processed_at)}</div>
                </div>
              )}
            </div>

            {selectedPayment.description && (
              <div>
                <div className="text-sm text-gray-500">Description</div>
                <div>{selectedPayment.description}</div>
              </div>
            )}

            {selectedPayment.error_message && (
              <div className="p-3 bg-red-50 border border-red-200 rounded">
                <div className="text-sm font-medium text-red-700">Erreur</div>
                <div className="text-sm text-red-600">{selectedPayment.error_message}</div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button variant="secondary" onClick={() => setSelectedPayment(null)}>Fermer</Button>
            </div>
          </div>
        </Modal>
      )}

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
      <DataTable columns={columns} data={refunds} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const PaymentMethodsView: React.FC = () => {
  const { data: methods = [], isLoading } = usePaymentMethods();

  const columns: TableColumn<PaymentMethod>[] = [
    { id: 'customer_name', header: 'Client', accessor: 'customer_name' },
    { id: 'type', header: 'Type', accessor: 'type', render: (v) => {
      const val = v as string;
      const labels: Record<string, string> = { CARD: 'Carte', BANK_ACCOUNT: 'Compte bancaire', SEPA: 'SEPA' };
      return labels[val] || val;
    }},
    { id: 'last_four', header: 'Numero', accessor: 'last_four', render: (v, row) => {
      const val = v as string;
      const method = row as PaymentMethod;
      if (!val) return '-';
      return <span>.... {val} {method.brand && <Badge color="blue">{method.brand}</Badge>}</span>;
    }},
    { id: 'expiry', header: 'Expiration', accessor: 'expiry_month', render: (v, row) => {
      const val = v as number;
      const method = row as PaymentMethod;
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
      <DataTable columns={columns} data={methods} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const TapToPayView: React.FC = () => {
  return (
    <div className="space-y-4">
      <Card>
        <div className="text-center py-8">
          <div className="text-6xl mb-4">Tap-to-Pay</div>
          <h3 className="text-2xl font-bold mb-2">Tap-to-Pay</h3>
          <p className="text-gray-600 mb-6">
            Encaissez directement avec votre smartphone grace au paiement sans contact NFC.
          </p>
          <Button size="lg">Configurer Tap-to-Pay</Button>
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

type View = 'dashboard' | 'transactions' | 'refunds' | 'methods' | 'tap-to-pay';

const PaymentsModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats } = usePaymentStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'transactions', label: 'Transactions' },
    { id: 'refunds', label: 'Remboursements' },
    { id: 'methods', label: 'Moyens de paiement' },
    { id: 'tap-to-pay', label: 'Tap-to-Pay' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'transactions':
        return <TransactionsView />;
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
                onClick={() => setCurrentView('transactions')}
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
                onClick={() => setCurrentView('refunds')}
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
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default PaymentsModule;
