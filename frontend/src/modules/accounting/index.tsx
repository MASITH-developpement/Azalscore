/**
 * AZALSCORE Module - Comptabilité
 * Journal, Grand livre, Balance, États financiers
 * Données fournies par API - AUCUNE logique métier
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, FileSpreadsheet, BarChart3, FileText, Download, Filter } from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup } from '@ui/actions';
import { KPICard, MetricComparison } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

// ============================================================
// TYPES
// ============================================================

interface JournalEntry {
  id: string;
  date: string;
  journal_code: string;
  piece_number: string;
  account_number: string;
  account_label: string;
  label: string;
  debit: number;
  credit: number;
  currency: string;
  document_type?: string;
  document_id?: string;
}

interface LedgerAccount {
  account_number: string;
  account_label: string;
  debit_total: number;
  credit_total: number;
  balance: number;
  currency: string;
}

interface BalanceEntry {
  account_number: string;
  account_label: string;
  opening_debit: number;
  opening_credit: number;
  period_debit: number;
  period_credit: number;
  closing_debit: number;
  closing_credit: number;
}

interface AccountingSummary {
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
  revenue: number;
  expenses: number;
  net_income: number;
  currency: string;
}

// ============================================================
// API HOOKS
// ============================================================

const useAccountingSummary = (period?: string) => {
  return useQuery({
    queryKey: ['accounting', 'summary', period],
    queryFn: async () => {
      const url = period
        ? `/v1/accounting/summary?period=${period}`
        : '/v1/accounting/summary';
      const response = await api.get<AccountingSummary>(url);
      return response.data;
    },
  });
};

const useJournalEntries = (page = 1, pageSize = 50, filters?: Record<string, string>) => {
  return useQuery({
    queryKey: ['accounting', 'journal', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        ...filters,
      });
      const response = await api.get<PaginatedResponse<JournalEntry>>(
        `/v1/accounting/journal?${params}`
      );
      return response.data;
    },
  });
};

const useLedger = (accountNumber?: string) => {
  return useQuery({
    queryKey: ['accounting', 'ledger', accountNumber],
    queryFn: async () => {
      const url = accountNumber
        ? `/v1/accounting/ledger/${accountNumber}`
        : '/v1/accounting/ledger';
      const response = await api.get<PaginatedResponse<LedgerAccount>>(url);
      return response.data;
    },
  });
};

const useBalance = (period?: string) => {
  return useQuery({
    queryKey: ['accounting', 'balance', period],
    queryFn: async () => {
      const url = period
        ? `/v1/accounting/balance?period=${period}`
        : '/v1/accounting/balance';
      const response = await api.get<PaginatedResponse<BalanceEntry>>(url);
      return response.data;
    },
  });
};

// ============================================================
// ACCOUNTING DASHBOARD
// ============================================================

export const AccountingDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = useAccountingSummary();

  const formatCurrency = (value: number, currency = 'EUR') =>
    new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(value);

  const kpis: DashboardKPI[] = summary
    ? [
        {
          id: 'assets',
          label: 'Actif total',
          value: formatCurrency(summary.total_assets, summary.currency),
        },
        {
          id: 'liabilities',
          label: 'Passif total',
          value: formatCurrency(summary.total_liabilities, summary.currency),
        },
        {
          id: 'revenue',
          label: 'Chiffre d\'affaires',
          value: formatCurrency(summary.revenue, summary.currency),
          trend: 'up',
        },
        {
          id: 'net_income',
          label: 'Résultat net',
          value: formatCurrency(summary.net_income, summary.currency),
          severity: summary.net_income >= 0 ? 'GREEN' : 'RED',
        },
      ]
    : [];

  return (
    <PageWrapper
      title="Comptabilité"
      subtitle="Vue d'ensemble comptable"
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<Download size={16} />}>
            Exporter
          </Button>
        </ButtonGroup>
      }
    >
      {isLoading ? (
        <div className="azals-loading">
          <div className="azals-spinner" />
        </div>
      ) : (
        <>
          <section className="azals-section">
            <Grid cols={4} gap="md">
              {kpis.map((kpi) => (
                <KPICard key={kpi.id} kpi={kpi} />
              ))}
            </Grid>
          </section>

          <section className="azals-section">
            <Grid cols={2} gap="md">
              <Card
                title="Journal"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/accounting/journal')}>
                    Voir tout
                  </Button>
                }
              >
                <div className="azals-accounting__card-icon">
                  <BookOpen size={32} />
                </div>
                <p>Consulter et saisir les écritures comptables</p>
              </Card>

              <Card
                title="Grand Livre"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/accounting/ledger')}>
                    Voir tout
                  </Button>
                }
              >
                <div className="azals-accounting__card-icon">
                  <FileSpreadsheet size={32} />
                </div>
                <p>Détail par compte comptable</p>
              </Card>

              <Card
                title="Balance"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/accounting/balance')}>
                    Voir tout
                  </Button>
                }
              >
                <div className="azals-accounting__card-icon">
                  <BarChart3 size={32} />
                </div>
                <p>Balance générale et auxiliaire</p>
              </Card>

              <Card
                title="États Financiers"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/accounting/reports')}>
                    Voir tout
                  </Button>
                }
              >
                <div className="azals-accounting__card-icon">
                  <FileText size={32} />
                </div>
                <p>Bilan, compte de résultat, annexes</p>
              </Card>
            </Grid>
          </section>
        </>
      )}
    </PageWrapper>
  );
};

// ============================================================
// JOURNAL PAGE
// ============================================================

export const JournalPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  const { data, isLoading, refetch } = useJournalEntries(page, pageSize);

  const columns: TableColumn<JournalEntry>[] = [
    {
      id: 'date',
      header: 'Date',
      accessor: 'date',
      sortable: true,
      render: (value) => new Date(value as string).toLocaleDateString('fr-FR'),
    },
    {
      id: 'journal_code',
      header: 'Journal',
      accessor: 'journal_code',
    },
    {
      id: 'piece_number',
      header: 'Pièce',
      accessor: 'piece_number',
    },
    {
      id: 'account_number',
      header: 'Compte',
      accessor: 'account_number',
    },
    {
      id: 'label',
      header: 'Libellé',
      accessor: 'label',
    },
    {
      id: 'debit',
      header: 'Débit',
      accessor: 'debit',
      align: 'right',
      render: (value, row) =>
        (value as number) > 0
          ? new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(
              value as number
            )
          : '',
    },
    {
      id: 'credit',
      header: 'Crédit',
      accessor: 'credit',
      align: 'right',
      render: (value, row) =>
        (value as number) > 0
          ? new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(
              value as number
            )
          : '',
    },
  ];

  return (
    <PageWrapper
      title="Journal Comptable"
      actions={
        <ButtonGroup>
          <Button variant="ghost" leftIcon={<Filter size={16} />}>
            Filtrer
          </Button>
          <Button variant="ghost" leftIcon={<Download size={16} />}>
            Exporter
          </Button>
        </ButtonGroup>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          isLoading={isLoading}
          pagination={{
            page,
            pageSize,
            total: data?.total || 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
          }}
          onRefresh={refetch}
          emptyMessage="Aucune écriture"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// LEDGER PAGE
// ============================================================

export const LedgerPage: React.FC = () => {
  const { data, isLoading } = useLedger();

  const columns: TableColumn<LedgerAccount>[] = [
    {
      id: 'account_number',
      header: 'N° Compte',
      accessor: 'account_number',
      sortable: true,
    },
    {
      id: 'account_label',
      header: 'Libellé',
      accessor: 'account_label',
    },
    {
      id: 'debit_total',
      header: 'Total Débit',
      accessor: 'debit_total',
      align: 'right',
      render: (value, row) =>
        new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(
          value as number
        ),
    },
    {
      id: 'credit_total',
      header: 'Total Crédit',
      accessor: 'credit_total',
      align: 'right',
      render: (value, row) =>
        new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(
          value as number
        ),
    },
    {
      id: 'balance',
      header: 'Solde',
      accessor: 'balance',
      align: 'right',
      render: (value, row) => (
        <span className={(value as number) < 0 ? 'azals-text--danger' : ''}>
          {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: row.currency }).format(
            value as number
          )}
        </span>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Grand Livre"
      actions={
        <Button variant="ghost" leftIcon={<Download size={16} />}>
          Exporter
        </Button>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="account_number"
          isLoading={isLoading}
          emptyMessage="Aucun compte"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// BALANCE PAGE
// ============================================================

export const BalancePage: React.FC = () => {
  const { data, isLoading } = useBalance();

  const columns: TableColumn<BalanceEntry>[] = [
    {
      id: 'account_number',
      header: 'N° Compte',
      accessor: 'account_number',
      sortable: true,
    },
    {
      id: 'account_label',
      header: 'Libellé',
      accessor: 'account_label',
    },
    {
      id: 'opening_debit',
      header: 'Ouv. Débit',
      accessor: 'opening_debit',
      align: 'right',
    },
    {
      id: 'opening_credit',
      header: 'Ouv. Crédit',
      accessor: 'opening_credit',
      align: 'right',
    },
    {
      id: 'period_debit',
      header: 'Mvt Débit',
      accessor: 'period_debit',
      align: 'right',
    },
    {
      id: 'period_credit',
      header: 'Mvt Crédit',
      accessor: 'period_credit',
      align: 'right',
    },
    {
      id: 'closing_debit',
      header: 'Clôt. Débit',
      accessor: 'closing_debit',
      align: 'right',
    },
    {
      id: 'closing_credit',
      header: 'Clôt. Crédit',
      accessor: 'closing_credit',
      align: 'right',
    },
  ];

  return (
    <PageWrapper
      title="Balance Générale"
      actions={
        <Button variant="ghost" leftIcon={<Download size={16} />}>
          Exporter
        </Button>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="account_number"
          isLoading={isLoading}
          emptyMessage="Aucune donnée"
        />
      </Card>
    </PageWrapper>
  );
};

// ============================================================
// REPORTS PAGE
// ============================================================

export const ReportsPage: React.FC = () => {
  return (
    <PageWrapper title="États Financiers">
      <Grid cols={2} gap="md">
        <Card title="Bilan">
          <p>Génération du bilan comptable</p>
          <Button variant="secondary" className="azals-mt-4">
            Générer le bilan
          </Button>
        </Card>

        <Card title="Compte de Résultat">
          <p>Génération du compte de résultat</p>
          <Button variant="secondary" className="azals-mt-4">
            Générer le compte de résultat
          </Button>
        </Card>

        <Card title="Annexes">
          <p>Documents annexes réglementaires</p>
          <Button variant="secondary" className="azals-mt-4">
            Générer les annexes
          </Button>
        </Card>

        <Card title="Liasse Fiscale">
          <p>Préparation de la liasse fiscale</p>
          <Button variant="secondary" className="azals-mt-4">
            Préparer la liasse
          </Button>
        </Card>
      </Grid>
    </PageWrapper>
  );
};

// ============================================================
// MODULE ROUTER
// ============================================================

export const AccountingRoutes: React.FC = () => (
  <Routes>
    <Route index element={<AccountingDashboard />} />
    <Route path="journal" element={<JournalPage />} />
    <Route path="ledger" element={<LedgerPage />} />
    <Route path="balance" element={<BalancePage />} />
    <Route path="reports" element={<ReportsPage />} />
  </Routes>
);

export default AccountingRoutes;
