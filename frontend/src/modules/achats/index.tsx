import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import type { TableColumn } from '@/types';
import { ClipboardList, Package, Inbox, CreditCard, BarChart3, TrendingUp } from 'lucide-react';

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

interface Supplier {
  id: string;
  code: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  payment_terms?: number;
  is_active: boolean;
  created_at: string;
}

interface Requisition {
  id: string;
  number: string;
  requester_id: string;
  requester_name?: string;
  date: string;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'CONVERTED';
  lines: RequisitionLine[];
  total_amount: number;
  notes?: string;
  created_at: string;
}

interface RequisitionLine {
  id: string;
  product_id: string;
  product_name?: string;
  quantity: number;
  unit_price: number;
  amount: number;
}

interface PurchaseOrder {
  id: string;
  number: string;
  supplier_id: string;
  supplier_name?: string;
  date: string;
  expected_date?: string;
  status: 'DRAFT' | 'SENT' | 'CONFIRMED' | 'RECEIVED' | 'CANCELLED';
  lines: PurchaseOrderLine[];
  total_ht: number;
  total_tva: number;
  total_ttc: number;
  requisition_id?: string;
  created_at: string;
}

interface PurchaseOrderLine {
  id: string;
  product_id: string;
  product_name?: string;
  quantity: number;
  received_quantity: number;
  unit_price: number;
  tva_rate: number;
  amount_ht: number;
}

interface GoodsReceipt {
  id: string;
  number: string;
  order_id: string;
  order_number?: string;
  supplier_id: string;
  supplier_name?: string;
  date: string;
  status: 'DRAFT' | 'VALIDATED' | 'CANCELLED';
  lines: GoodsReceiptLine[];
  notes?: string;
  created_at: string;
}

interface GoodsReceiptLine {
  id: string;
  product_id: string;
  product_name?: string;
  quantity_expected: number;
  quantity_received: number;
  warehouse_id?: string;
  location_id?: string;
}

interface PurchaseInvoice {
  id: string;
  number: string;
  supplier_id: string;
  supplier_name?: string;
  supplier_invoice_number?: string;
  date: string;
  due_date?: string;
  status: 'DRAFT' | 'VALIDATED' | 'PAID' | 'CANCELLED';
  lines: PurchaseInvoiceLine[];
  total_ht: number;
  total_tva: number;
  total_ttc: number;
  amount_paid: number;
  order_id?: string;
  created_at: string;
}

interface PurchaseInvoiceLine {
  id: string;
  product_id?: string;
  product_name?: string;
  description: string;
  quantity: number;
  unit_price: number;
  tva_rate: number;
  amount_ht: number;
}

interface ProcurementDashboard {
  pending_requisitions: number;
  open_orders: number;
  pending_receipts: number;
  unpaid_invoices: number;
  total_purchases_month: number;
  total_purchases_year: number;
  top_suppliers: { supplier_name: string; amount: number }[];
}

// ============================================================================
// CONSTANTES
// ============================================================================

const REQUISITION_STATUSES = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'SUBMITTED', label: 'Soumise', color: 'blue' },
  { value: 'APPROVED', label: 'Approuvee', color: 'green' },
  { value: 'REJECTED', label: 'Rejetee', color: 'red' },
  { value: 'CONVERTED', label: 'Convertie', color: 'purple' }
];

const ORDER_STATUSES = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'SENT', label: 'Envoyee', color: 'blue' },
  { value: 'CONFIRMED', label: 'Confirmee', color: 'green' },
  { value: 'RECEIVED', label: 'Receptionnee', color: 'purple' },
  { value: 'CANCELLED', label: 'Annulee', color: 'red' }
];

const INVOICE_STATUSES = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'VALIDATED', label: 'Validee', color: 'blue' },
  { value: 'PAID', label: 'Payee', color: 'green' },
  { value: 'CANCELLED', label: 'Annulee', color: 'red' }
];

// ============================================================================
// HELPERS
// ============================================================================

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
};

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const getStatusInfo = (statuses: any[], status: string) => {
  return statuses.find(s => s.value === status) || { label: status, color: 'gray' };
};

// Navigation inter-modules
const navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

// ============================================================================
// API HOOKS
// ============================================================================

const useProcurementDashboard = () => {
  return useQuery({
    queryKey: ['procurement', 'dashboard'],
    queryFn: async () => {
      return api.get<ProcurementDashboard>('/v1/procurement/dashboard').then(r => r.data);
    }
  });
};

const useSuppliers = () => {
  return useQuery({
    queryKey: ['procurement', 'suppliers'],
    queryFn: async () => {
      const response = await api.get<{ items: Supplier[] }>('/v1/procurement/suppliers').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useRequisitions = () => {
  return useQuery({
    queryKey: ['procurement', 'requisitions'],
    queryFn: async () => {
      const response = await api.get<{ items: Requisition[] }>('/v1/procurement/requisitions').then(r => r.data);
      return response?.items || [];
    }
  });
};

const usePurchaseOrders = () => {
  return useQuery({
    queryKey: ['procurement', 'orders'],
    queryFn: async () => {
      const response = await api.get<{ items: PurchaseOrder[] }>('/v1/procurement/orders').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useGoodsReceipts = () => {
  return useQuery({
    queryKey: ['procurement', 'receipts'],
    queryFn: async () => {
      const response = await api.get<{ items: GoodsReceipt[] }>('/v1/procurement/receipts').then(r => r.data);
      return response?.items || [];
    }
  });
};

const usePurchaseInvoices = () => {
  return useQuery({
    queryKey: ['procurement', 'invoices'],
    queryFn: async () => {
      const response = await api.get<{ items: PurchaseInvoice[] }>('/v1/procurement/invoices').then(r => r.data);
      return response?.items || [];
    }
  });
};

const useCreateSupplier = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Supplier>) => {
      return api.post<Supplier>('/v1/procurement/suppliers', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['procurement', 'suppliers'] })
  });
};

const useCreateRequisition = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Requisition>) => {
      return api.post<Requisition>('/v1/procurement/requisitions', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['procurement', 'requisitions'] })
  });
};

const useCreatePurchaseOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<PurchaseOrder>) => {
      return api.post<PurchaseOrder>('/v1/procurement/orders', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['procurement', 'orders'] })
  });
};

const useSendOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<PurchaseOrder>(`/v1/procurement/orders/${id}/send`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['procurement', 'orders'] })
  });
};

const useConfirmOrder = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      return api.post<PurchaseOrder>(`/v1/procurement/orders/${id}/confirm`).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['procurement', 'orders'] })
  });
};

const useCreateReceipt = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<GoodsReceipt>) => {
      return api.post<GoodsReceipt>('/v1/procurement/receipts', data).then(r => r.data);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['procurement'] })
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const SuppliersView: React.FC = () => {
  const { data: suppliers = [], isLoading } = useSuppliers();
  const createSupplier = useCreateSupplier();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<Supplier>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createSupplier.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<Supplier>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Nom', accessor: 'name' },
    { id: 'email', header: 'Email', accessor: 'email', render: (v) => (v as string) || '-' },
    { id: 'phone', header: 'Telephone', accessor: 'phone', render: (v) => (v as string) || '-' },
    { id: 'payment_terms', header: 'Delai paiement', accessor: 'payment_terms', render: (v) => (v as number) ? `${v} jours` : '-' },
    { id: 'is_active', header: 'Actif', accessor: 'is_active', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Fournisseurs</h3>
        <Button onClick={() => setShowModal(true)}>Nouveau fournisseur</Button>
      </div>
      <DataTable columns={columns} data={suppliers} isLoading={isLoading} keyField="id" />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouveau fournisseur">
        <form onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Code</label>
              <Input
                value={formData.code || ''}
                onChange={(v) => setFormData({ ...formData, code: v })}
              />
            </div>
            <div className="azals-field">
              <label>Nom</label>
              <Input
                value={formData.name || ''}
                onChange={(v) => setFormData({ ...formData, name: v })}
              />
            </div>
          </Grid>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Email</label>
              <Input
                type="email"
                value={formData.email || ''}
                onChange={(v) => setFormData({ ...formData, email: v })}
              />
            </div>
            <div className="azals-field">
              <label>Telephone</label>
              <Input
                value={formData.phone || ''}
                onChange={(v) => setFormData({ ...formData, phone: v })}
              />
            </div>
          </Grid>
          <div className="azals-field">
            <label>Adresse</label>
            <Input
              value={formData.address || ''}
              onChange={(v) => setFormData({ ...formData, address: v })}
            />
          </div>
          <div className="azals-field">
            <label>Delai de paiement (jours)</label>
            <Input
              type="number"
              value={formData.payment_terms?.toString() || ''}
              onChange={(v) => setFormData({ ...formData, payment_terms: parseInt(v) })}
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createSupplier.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const RequisitionsView: React.FC = () => {
  const { data: requisitions = [], isLoading } = useRequisitions();

  const columns: TableColumn<Requisition>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'requester_name', header: 'Demandeur', accessor: 'requester_name' },
    { id: 'total_amount', header: 'Montant', accessor: 'total_amount', render: (v) => formatCurrency(v as number) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(REQUISITION_STATUSES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'notes', header: 'Notes', accessor: 'notes', render: (v) => (v as string) || '-' }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Demandes d'achat</h3>
        <Button>Nouvelle demande</Button>
      </div>
      <DataTable columns={columns} data={requisitions} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const OrdersView: React.FC = () => {
  const { data: orders = [], isLoading } = usePurchaseOrders();
  const { data: suppliers = [] } = useSuppliers();
  const createOrder = useCreatePurchaseOrder();
  const sendOrder = useSendOrder();
  const confirmOrder = useConfirmOrder();
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<PurchaseOrder>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createOrder.mutateAsync(formData);
    setShowModal(false);
    setFormData({});
  };

  const columns: TableColumn<PurchaseOrder>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'supplier_name', header: 'Fournisseur', accessor: 'supplier_name', render: (v, row) => (
      <button
        className="text-blue-600 hover:underline"
        onClick={() => navigateTo('achats', { view: 'suppliers', id: (row as PurchaseOrder).supplier_id })}
      >
        {v as string}
      </button>
    )},
    { id: 'expected_date', header: 'Livraison prevue', accessor: 'expected_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'total_ttc', header: 'Total TTC', accessor: 'total_ttc', render: (v) => formatCurrency(v as number) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(ORDER_STATUSES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        {(row as PurchaseOrder).status === 'DRAFT' && (
          <Button size="sm" onClick={() => sendOrder.mutate((row as PurchaseOrder).id)}>Envoyer</Button>
        )}
        {(row as PurchaseOrder).status === 'SENT' && (
          <Button size="sm" onClick={() => confirmOrder.mutate((row as PurchaseOrder).id)}>Confirmer</Button>
        )}
        {(row as PurchaseOrder).status === 'CONFIRMED' && (
          <Button size="sm" onClick={() => navigateTo('stock', { view: 'receipts', order_id: (row as PurchaseOrder).id })}>
            Receptionner
          </Button>
        )}
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Commandes fournisseurs</h3>
        <Button onClick={() => setShowModal(true)}>Nouvelle commande</Button>
      </div>
      <DataTable columns={columns} data={orders} isLoading={isLoading} keyField="id" />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nouvelle commande">
        <form onSubmit={handleSubmit}>
          <Grid cols={2}>
            <div className="azals-field">
              <label>Fournisseur</label>
              <Select
                value={formData.supplier_id || ''}
                onChange={(v) => setFormData({ ...formData, supplier_id: v })}
                options={suppliers.map(s => ({ value: s.id, label: s.name }))}
              />
            </div>
            <div className="azals-field">
              <label>Date</label>
              <input
                type="date"
                className="azals-input"
                value={formData.date || ''}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                required
              />
            </div>
          </Grid>
          <div className="azals-field">
            <label>Date de livraison prevue</label>
            <input
              type="date"
              className="azals-input"
              value={formData.expected_date || ''}
              onChange={(e) => setFormData({ ...formData, expected_date: e.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" onClick={() => setShowModal(false)}>Annuler</Button>
            <Button type="submit" isLoading={createOrder.isPending}>Creer</Button>
          </div>
        </form>
      </Modal>
    </Card>
  );
};

const ReceiptsView: React.FC = () => {
  const { data: receipts = [], isLoading } = useGoodsReceipts();

  const columns: TableColumn<GoodsReceipt>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'order_number', header: 'Commande', accessor: 'order_number', render: (v, row) => (
      <button
        className="text-blue-600 hover:underline"
        onClick={() => navigateTo('achats', { view: 'orders', id: (row as GoodsReceipt).order_id })}
      >
        {v as string}
      </button>
    )},
    { id: 'supplier_name', header: 'Fournisseur', accessor: 'supplier_name' },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo([
        { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
        { value: 'VALIDATED', label: 'Valide', color: 'green' },
        { value: 'CANCELLED', label: 'Annule', color: 'red' }
      ], v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Bons de reception</h3>
      </div>
      <DataTable columns={columns} data={receipts} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const InvoicesView: React.FC = () => {
  const { data: invoices = [], isLoading } = usePurchaseInvoices();

  const columns: TableColumn<PurchaseInvoice>[] = [
    { id: 'number', header: 'N', accessor: 'number', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'supplier_invoice_number', header: 'N Fournisseur', accessor: 'supplier_invoice_number', render: (v) => (v as string) || '-' },
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'supplier_name', header: 'Fournisseur', accessor: 'supplier_name' },
    { id: 'due_date', header: 'Echeance', accessor: 'due_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'total_ttc', header: 'Total TTC', accessor: 'total_ttc', render: (v) => formatCurrency(v as number) },
    { id: 'amount_paid', header: 'Paye', accessor: 'amount_paid', render: (v) => formatCurrency(v as number) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const info = getStatusInfo(INVOICE_STATUSES, v as string);
      return <Badge color={info.color as any}>{info.label}</Badge>;
    }},
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row) => (
      <div className="flex gap-1">
        {(row as PurchaseInvoice).status === 'VALIDATED' && (row as PurchaseInvoice).amount_paid < (row as PurchaseInvoice).total_ttc && (
          <Button size="sm" onClick={() => navigateTo('comptabilite', { view: 'entries', invoice_id: (row as PurchaseInvoice).id })}>
            Payer
          </Button>
        )}
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Factures fournisseurs</h3>
      </div>
      <DataTable columns={columns} data={invoices} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'suppliers' | 'requisitions' | 'orders' | 'receipts' | 'invoices';

const AchatsModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: dashboard, isLoading } = useProcurementDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'suppliers', label: 'Fournisseurs' },
    { id: 'requisitions', label: 'Demandes' },
    { id: 'orders', label: 'Commandes' },
    { id: 'receipts', label: 'Receptions' },
    { id: 'invoices', label: 'Factures' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'suppliers':
        return <SuppliersView />;
      case 'requisitions':
        return <RequisitionsView />;
      case 'orders':
        return <OrdersView />;
      case 'receipts':
        return <ReceiptsView />;
      case 'invoices':
        return <InvoicesView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Demandes en attente"
                value={String(dashboard?.pending_requisitions || 0)}
                icon={<ClipboardList />}
                variant="default"
                onClick={() => setCurrentView('requisitions')}
              />
              <StatCard
                title="Commandes en cours"
                value={String(dashboard?.open_orders || 0)}
                icon={<Package />}
                variant="warning"
                onClick={() => setCurrentView('orders')}
              />
              <StatCard
                title="Receptions en attente"
                value={String(dashboard?.pending_receipts || 0)}
                icon={<Inbox />}
                variant="default"
                onClick={() => setCurrentView('receipts')}
              />
              <StatCard
                title="Factures impayees"
                value={String(dashboard?.unpaid_invoices || 0)}
                icon={<CreditCard />}
                variant="danger"
                onClick={() => setCurrentView('invoices')}
              />
            </Grid>
            <Grid cols={2}>
              <StatCard
                title="Achats du mois"
                value={formatCurrency(dashboard?.total_purchases_month || 0)}
                icon={<BarChart3 />}
                variant="default"
              />
              <StatCard
                title="Achats de l'annee"
                value={formatCurrency(dashboard?.total_purchases_year || 0)}
                icon={<TrendingUp />}
                variant="success"
              />
            </Grid>
            {dashboard?.top_suppliers && dashboard.top_suppliers.length > 0 && (
              <Card>
                <h3 className="text-lg font-semibold mb-4">Top fournisseurs</h3>
                <div className="space-y-2">
                  {dashboard.top_suppliers.map((s, i) => (
                    <div key={i} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span>{s.supplier_name}</span>
                      <span className="font-semibold">{formatCurrency(s.amount)}</span>
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
    <PageWrapper title="Achats" subtitle="Gestion des achats et approvisionnements">
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

export default AchatsModule;
