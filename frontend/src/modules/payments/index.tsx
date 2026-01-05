/**
 * AZALSCORE Module - Paiements
 * Paiements en ligne, Tap-to-Pay, Historique
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { CreditCard, Smartphone, History, Settings, CheckCircle, XCircle, Clock } from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

interface Payment {
  id: string;
  reference: string;
  amount: number;
  currency: string;
  method: 'card' | 'bank_transfer' | 'tap_to_pay' | 'other';
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  customer_name?: string;
  created_at: string;
}

interface PaymentsSummary {
  total_today: number;
  transactions_today: number;
  total_this_month: number;
  pending_count: number;
  failed_count: number;
}

const useSummary = () => {
  return useQuery({
    queryKey: ['payments', 'summary'],
    queryFn: async () => {
      const response = await api.get<PaymentsSummary>('/v1/payments/summary');
      return response.data;
    },
  });
};

const usePayments = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['payments', 'list', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Payment>>(`/v1/payments?page=${page}&page_size=${pageSize}`);
      return response.data;
    },
  });
};

const STATUS_CONFIG: Record<string, { icon: React.FC<{ size: number }>; color: string; label: string }> = {
  pending: { icon: Clock, color: 'orange', label: 'En attente' },
  completed: { icon: CheckCircle, color: 'green', label: 'Complété' },
  failed: { icon: XCircle, color: 'red', label: 'Échoué' },
  refunded: { icon: History, color: 'blue', label: 'Remboursé' },
};

const METHOD_LABELS: Record<string, string> = {
  card: 'Carte bancaire',
  bank_transfer: 'Virement',
  tap_to_pay: 'Tap-to-Pay',
  other: 'Autre',
};

export const PaymentsDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = useSummary();

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(value);

  const kpis: DashboardKPI[] = summary ? [
    { id: 'today', label: 'Encaissé aujourd\'hui', value: formatCurrency(summary.total_today) },
    { id: 'transactions', label: 'Transactions', value: summary.transactions_today },
    { id: 'month', label: 'Total ce mois', value: formatCurrency(summary.total_this_month) },
    { id: 'pending', label: 'En attente', value: summary.pending_count, severity: summary.pending_count > 0 ? 'ORANGE' : 'GREEN' },
  ] : [];

  return (
    <PageWrapper title="Paiements" subtitle="Encaissements et transactions">
      {isLoading ? <div className="azals-loading"><div className="azals-spinner" /></div> : (
        <>
          <section className="azals-section">
            <Grid cols={4} gap="md">{kpis.map((kpi) => <KPICard key={kpi.id} kpi={kpi} />)}</Grid>
          </section>
          <section className="azals-section">
            <Grid cols={3} gap="md">
              <Card title="Paiements en ligne" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/payments/online')}>Gérer</Button>}>
                <CreditCard size={32} className="azals-text--primary" />
                <p>Paiements par carte en ligne</p>
              </Card>
              <Card title="Tap-to-Pay" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/payments/tap-to-pay')}>Configurer</Button>}>
                <Smartphone size={32} className="azals-text--primary" />
                <p>Encaissement mobile NFC</p>
              </Card>
              <Card title="Historique" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/payments/history')}>Voir tout</Button>}>
                <History size={32} className="azals-text--primary" />
                <p>Historique des transactions</p>
              </Card>
            </Grid>
          </section>
        </>
      )}
    </PageWrapper>
  );
};

export const PaymentsHistoryPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const { data, isLoading, refetch } = usePayments(page, pageSize);

  const columns: TableColumn<Payment>[] = [
    { id: 'reference', header: 'Référence', accessor: 'reference' },
    { id: 'customer_name', header: 'Client', accessor: 'customer_name' },
    { id: 'method', header: 'Méthode', accessor: 'method', render: (v) => METHOD_LABELS[v as string] },
    { id: 'amount', header: 'Montant', accessor: 'amount', align: 'right', render: (v, row) => new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(v as number) },
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const config = STATUS_CONFIG[v as string];
      return <span className={`azals-badge azals-badge--${config.color}`}>{config.label}</span>;
    }},
    { id: 'created_at', header: 'Date', accessor: 'created_at', render: (v) => new Date(v as string).toLocaleString('fr-FR') },
  ];

  return (
    <PageWrapper title="Historique des paiements">
      <Card noPadding>
        <DataTable columns={columns} data={data?.items || []} keyField="id" isLoading={isLoading} pagination={{ page, pageSize, total: data?.total || 0, onPageChange: setPage, onPageSizeChange: setPageSize }} onRefresh={refetch} />
      </Card>
    </PageWrapper>
  );
};

export const TapToPayPage: React.FC = () => {
  return (
    <PageWrapper title="Tap-to-Pay" subtitle="Configuration du paiement mobile NFC">
      <Grid cols={2} gap="md">
        <Card title="Configuration">
          <p>Configurez votre terminal de paiement virtuel pour accepter les paiements par carte sans contact directement sur votre smartphone.</p>
          <div className="azals-mt-4">
            <Button variant="primary" leftIcon={<Smartphone size={16} />}>
              Configurer Tap-to-Pay
            </Button>
          </div>
        </Card>
        <Card title="Statut du service">
          <div className="azals-payment-status">
            <CheckCircle size={24} className="azals-text--success" />
            <span>Service actif et opérationnel</span>
          </div>
          <p className="azals-mt-4 azals-text--muted">
            Compatible avec les cartes Visa, Mastercard et cartes sans contact.
          </p>
        </Card>
      </Grid>
    </PageWrapper>
  );
};

export const PaymentsRoutes: React.FC = () => (
  <Routes>
    <Route index element={<PaymentsDashboard />} />
    <Route path="history" element={<PaymentsHistoryPage />} />
    <Route path="tap-to-pay" element={<TapToPayPage />} />
  </Routes>
);

export default PaymentsRoutes;
