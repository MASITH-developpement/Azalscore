/**
 * AZALSCORE Module - Trésorerie
 * Comptes bancaires, Transactions, Rapprochement, Prévisions
 * Données fournies par API - AUCUNE logique métier
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Building2,
  ArrowUpRight,
  ArrowDownLeft,
  RefreshCw,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { DynamicForm } from '@ui/forms';
import { Button, ButtonGroup, Modal, ConfirmDialog } from '@ui/actions';
import { KPICard, MetricComparison, ProgressBar } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

// ============================================================
// TYPES
// ============================================================

interface BankAccount {
  id: string;
  name: string;
  bank_name: string;
  iban: string;
  bic: string;
  balance: number;
  currency: string;
  is_default: boolean;
  is_active: boolean;
  last_sync?: string;
}

interface Transaction {
  id: string;
  account_id: string;
  account_name: string;
  date: string;
  value_date: string;
  description: string;
  amount: number;
  currency: string;
  type: 'credit' | 'debit';
  category?: string;
  reconciled: boolean;
  linked_document?: {
    type: string;
    id: string;
    number: string;
  };
}

interface TreasurySummary {
  total_balance: number;
  total_pending_in: number;
  total_pending_out: number;
  forecast_7d: number;
  forecast_30d: number;
  accounts: BankAccount[];
}

interface ForecastData {
  date: string;
  projected_balance: number;
  pending_in: number;
  pending_out: number;
}

// ============================================================
// API HOOKS
// ============================================================

const useTreasurySummary = () => {
  return useQuery({
    queryKey: ['treasury', 'summary'],
    queryFn: async () => {
      const response = await api.get<TreasurySummary>('/v1/treasury/summary');
      return response.data;
    },
  });
};

const useBankAccounts = () => {
  return useQuery({
    queryKey: ['treasury', 'accounts'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<BankAccount>>('/v1/treasury/accounts');
      return response.data;
    },
  });
};

const useTransactions = (accountId?: string, page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['treasury', 'transactions', accountId, page, pageSize],
    queryFn: async () => {
      const url = accountId
        ? `/v1/treasury/accounts/${accountId}/transactions?page=${page}&page_size=${pageSize}`
        : `/v1/treasury/transactions?page=${page}&page_size=${pageSize}`;
      const response = await api.get<PaginatedResponse<Transaction>>(url);
      return response.data;
    },
  });
};

const useForecast = (days = 30) => {
  return useQuery({
    queryKey: ['treasury', 'forecast', days],
    queryFn: async () => {
      const response = await api.get<ForecastData[]>(`/v1/treasury/forecast?days=${days}`);
      return response.data;
    },
  });
};

const useReconcileTransaction = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ transactionId, documentType, documentId }: {
      transactionId: string;
      documentType: string;
      documentId: string;
    }) => {
      await api.post(`/v1/treasury/transactions/${transactionId}/reconcile`, {
        document_type: documentType,
        document_id: documentId,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['treasury'] });
    },
  });
};

// ============================================================
// TREASURY DASHBOARD
// ============================================================

export const TreasuryDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = useTreasurySummary();

  if (isLoading || !summary) {
    return (
      <PageWrapper title="Trésorerie">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  const kpis: DashboardKPI[] = [
    {
      id: 'balance',
      label: 'Solde total',
      value: new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
        summary.total_balance
      ),
      severity: summary.total_balance < 0 ? 'RED' : summary.total_balance < 10000 ? 'ORANGE' : 'GREEN',
    },
    {
      id: 'pending_in',
      label: 'Encaissements attendus',
      value: new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
        summary.total_pending_in
      ),
      trend: 'up',
    },
    {
      id: 'pending_out',
      label: 'Décaissements prévus',
      value: new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
        summary.total_pending_out
      ),
      trend: 'down',
    },
    {
      id: 'forecast',
      label: 'Prévision 30j',
      value: new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
        summary.forecast_30d
      ),
      severity: summary.forecast_30d < 0 ? 'RED' : 'GREEN',
    },
  ];

  return (
    <PageWrapper
      title="Trésorerie"
      subtitle="Vue d'ensemble de votre trésorerie"
      actions={
        <ButtonGroup>
          <Button variant="ghost" onClick={() => navigate('/treasury/reconciliation')}>
            Rapprochement
          </Button>
          <Button variant="ghost" onClick={() => navigate('/treasury/forecast')}>
            Prévisions
          </Button>
        </ButtonGroup>
      }
    >
      {/* KPIs */}
      <section className="azals-section">
        <Grid cols={4} gap="md">
          {kpis.map((kpi) => (
            <KPICard key={kpi.id} kpi={kpi} />
          ))}
        </Grid>
      </section>

      {/* Comptes bancaires */}
      <section className="azals-section">
        <Card
          title="Comptes bancaires"
          actions={
            <CapabilityGuard capability="treasury.accounts.create">
              <Button
                variant="ghost"
                size="sm"
                leftIcon={<Plus size={16} />}
                onClick={() => navigate('/treasury/accounts/new')}
              >
                Ajouter
              </Button>
            </CapabilityGuard>
          }
        >
          <div className="azals-treasury__accounts">
            {summary.accounts.map((account) => (
              <div
                key={account.id}
                className="azals-treasury__account-card"
                onClick={() => navigate(`/treasury/accounts/${account.id}`)}
              >
                <div className="azals-treasury__account-header">
                  <Building2 size={20} />
                  <div>
                    <h4>{account.name}</h4>
                    <span className="azals-treasury__account-bank">{account.bank_name}</span>
                  </div>
                </div>
                <div className="azals-treasury__account-balance">
                  <span
                    className={account.balance < 0 ? 'azals-text--danger' : 'azals-text--success'}
                  >
                    {new Intl.NumberFormat('fr-FR', {
                      style: 'currency',
                      currency: account.currency,
                    }).format(account.balance)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {/* Dernières transactions */}
      <section className="azals-section">
        <TransactionsList maxItems={10} />
      </section>
    </PageWrapper>
  );
};

// ============================================================
// BANK ACCOUNTS LIST
// ============================================================

export const BankAccountsPage: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading } = useBankAccounts();

  const columns: TableColumn<BankAccount>[] = [
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      sortable: true,
    },
    {
      id: 'bank_name',
      header: 'Banque',
      accessor: 'bank_name',
    },
    {
      id: 'iban',
      header: 'IBAN',
      accessor: 'iban',
      render: (value) => {
        const iban = value as string;
        return `${iban.slice(0, 4)} **** ${iban.slice(-4)}`;
      },
    },
    {
      id: 'balance',
      header: 'Solde',
      accessor: 'balance',
      align: 'right',
      render: (value, row) =>
        new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(
          value as number
        ),
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (value) =>
        value ? (
          <span className="azals-badge azals-badge--green">Actif</span>
        ) : (
          <span className="azals-badge azals-badge--gray">Inactif</span>
        ),
    },
  ];

  const actions = [
    {
      id: 'view',
      label: 'Voir les transactions',
      onClick: (row: BankAccount) => navigate(`/treasury/accounts/${row.id}`),
    },
    {
      id: 'edit',
      label: 'Modifier',
      capability: 'treasury.accounts.edit',
      onClick: (row: BankAccount) => navigate(`/treasury/accounts/${row.id}/edit`),
    },
  ];

  return (
    <PageWrapper
      title="Comptes bancaires"
      actions={
        <CapabilityGuard capability="treasury.accounts.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/treasury/accounts/new')}>
            Nouveau compte
          </Button>
        </CapabilityGuard>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          actions={actions}
          isLoading={isLoading}
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// TRANSACTIONS LIST
// ============================================================

interface TransactionsListProps {
  accountId?: string;
  maxItems?: number;
}

const TransactionsList: React.FC<TransactionsListProps> = ({ accountId, maxItems }) => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(maxItems || 25);

  const { data, isLoading, refetch } = useTransactions(accountId, page, pageSize);

  const columns: TableColumn<Transaction>[] = [
    {
      id: 'date',
      header: 'Date',
      accessor: 'date',
      sortable: true,
      render: (value) => new Date(value as string).toLocaleDateString('fr-FR'),
    },
    {
      id: 'description',
      header: 'Description',
      accessor: 'description',
    },
    {
      id: 'type',
      header: '',
      accessor: 'type',
      width: '40px',
      render: (value) =>
        value === 'credit' ? (
          <ArrowDownLeft className="azals-text--success" size={16} />
        ) : (
          <ArrowUpRight className="azals-text--danger" size={16} />
        ),
    },
    {
      id: 'amount',
      header: 'Montant',
      accessor: 'amount',
      align: 'right',
      render: (value, row) => {
        const amount = value as number;
        const formatted = new Intl.NumberFormat('fr-FR', {
          style: 'currency',
          currency: row.currency,
        }).format(Math.abs(amount));
        return (
          <span className={row.type === 'credit' ? 'azals-text--success' : 'azals-text--danger'}>
            {row.type === 'credit' ? '+' : '-'}{formatted}
          </span>
        );
      },
    },
    {
      id: 'reconciled',
      header: 'Rapproché',
      accessor: 'reconciled',
      render: (value, row) =>
        value ? (
          <CheckCircle className="azals-text--success" size={16} />
        ) : (
          <XCircle className="azals-text--gray" size={16} />
        ),
    },
  ];

  return (
    <Card
      title="Transactions"
      noPadding
      actions={
        <Button variant="ghost" size="sm" onClick={() => navigate('/treasury/transactions')}>
          Voir tout
        </Button>
      }
    >
      <DataTable
        columns={columns}
        data={data?.items.slice(0, maxItems) || []}
        keyField="id"
        isLoading={isLoading}
        pagination={
          !maxItems
            ? {
                page,
                pageSize,
                total: data?.total || 0,
                onPageChange: setPage,
                onPageSizeChange: setPageSize,
              }
            : undefined
        }
        onRefresh={refetch}
        emptyMessage="Aucune transaction"
      />
    </Card>
  );
};

export const TransactionsPage: React.FC = () => {
  return (
    <PageWrapper title="Transactions">
      <TransactionsList />
    </PageWrapper>
  );
};

// ============================================================
// FORECAST PAGE
// ============================================================

export const ForecastPage: React.FC = () => {
  const { data: forecast, isLoading } = useForecast(30);
  const { data: summary } = useTreasurySummary();

  if (isLoading) {
    return (
      <PageWrapper title="Prévisions de trésorerie">
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper title="Prévisions de trésorerie" subtitle="Projection sur les 30 prochains jours">
      <Grid cols={2} gap="md">
        <Card title="Résumé des prévisions">
          {summary && (
            <div className="azals-forecast__summary">
              <MetricComparison
                label="Solde actuel → Prévision 30j"
                current={summary.forecast_30d}
                previous={summary.total_balance}
                format="currency"
              />
              <div className="azals-forecast__row">
                <div>
                  <span>Encaissements attendus</span>
                  <strong className="azals-text--success">
                    +{new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
                      summary.total_pending_in
                    )}
                  </strong>
                </div>
                <div>
                  <span>Décaissements prévus</span>
                  <strong className="azals-text--danger">
                    -{new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
                      summary.total_pending_out
                    )}
                  </strong>
                </div>
              </div>
            </div>
          )}
        </Card>

        <Card title="Alertes">
          {summary && summary.forecast_30d < 0 && (
            <div className="azals-forecast__alert azals-forecast__alert--danger">
              <AlertTriangle size={20} />
              <p>
                Attention : votre solde prévisionnel devient négatif dans les 30 prochains jours.
              </p>
            </div>
          )}
          {summary && summary.forecast_30d >= 0 && summary.forecast_30d < 10000 && (
            <div className="azals-forecast__alert azals-forecast__alert--warning">
              <AlertTriangle size={20} />
              <p>
                Votre solde prévisionnel sera bas dans les 30 prochains jours.
              </p>
            </div>
          )}
          {summary && summary.forecast_30d >= 10000 && (
            <div className="azals-forecast__alert azals-forecast__alert--success">
              <CheckCircle size={20} />
              <p>
                Votre trésorerie est saine pour les 30 prochains jours.
              </p>
            </div>
          )}
        </Card>
      </Grid>

      <Card title="Évolution journalière" className="azals-mt-4">
        <div className="azals-forecast__table">
          <table className="azals-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Encaissements</th>
                <th>Décaissements</th>
                <th>Solde projeté</th>
              </tr>
            </thead>
            <tbody>
              {forecast?.map((day) => (
                <tr key={day.date}>
                  <td>{new Date(day.date).toLocaleDateString('fr-FR')}</td>
                  <td className="azals-text--success">
                    +{new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
                      day.pending_in
                    )}
                  </td>
                  <td className="azals-text--danger">
                    -{new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
                      day.pending_out
                    )}
                  </td>
                  <td className={day.projected_balance < 0 ? 'azals-text--danger' : ''}>
                    {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(
                      day.projected_balance
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// MODULE ROUTER
// ============================================================

export const TreasuryRoutes: React.FC = () => (
  <Routes>
    <Route index element={<TreasuryDashboard />} />
    <Route path="accounts" element={<BankAccountsPage />} />
    <Route path="accounts/:id" element={<TransactionsPage />} />
    <Route path="transactions" element={<TransactionsPage />} />
    <Route path="forecast" element={<ForecastPage />} />
  </Routes>
);

export default TreasuryRoutes;
