/**
 * Vue Dirigeant - Dashboard Comptabilité Automatisée
 *
 * Objectif: Piloter & décider
 *
 * INCLUT:
 * - Trésorerie actuelle (via banque en PULL)
 * - Prévision de cash
 * - Factures à payer / encaisser
 * - Résultat estimé
 * - Alertes intelligentes par exception
 *
 * INTERDICTIONS:
 * - Aucune saisie comptable
 * - Aucun choix de compte
 * - Aucun export
 * - Aucun jargon comptable
 */

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  Clock,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '@core/api-client';
import { Button, ButtonGroup } from '@ui/actions';
import { ProgressBar } from '@ui/dashboards';
import { PageWrapper, Card, Grid } from '@ui/layout';

// ============================================================
// TYPES
// ============================================================

interface CashPosition {
  total_balance: number;
  available_balance: number;
  currency: string;
  accounts: Array<{
    name: string;
    balance: number;
    currency: string;
  }>;
  last_sync_at: string | null;
  freshness_score: number;
}

interface CashForecastItem {
  date: string;
  opening_balance: number;
  expected_receipts: number;
  expected_payments: number;
  expected_closing: number;
}

interface CashForecast {
  current_balance: number;
  forecast_items: CashForecastItem[];
  period_start: string;
  period_end: string;
  warning_threshold: number;
  alert_threshold: number;
}

interface InvoicesSummary {
  to_pay_count: number;
  to_pay_amount: number;
  overdue_to_pay_count: number;
  overdue_to_pay_amount: number;
  to_collect_count: number;
  to_collect_amount: number;
  overdue_to_collect_count: number;
  overdue_to_collect_amount: number;
}

interface ResultSummary {
  revenue: number;
  expenses: number;
  result: number;
  period: string;
  period_start: string;
  period_end: string;
}

interface Alert {
  id: string;
  alert_type: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  title: string;
  message: string;
  document_id?: string;
  is_resolved: boolean;
  created_at: string;
}

interface DirigeantDashboardData {
  cash_position: CashPosition;
  cash_forecast: CashForecast;
  invoices_summary: InvoicesSummary;
  result_summary: ResultSummary;
  alerts: Alert[];
  data_freshness: number;
  last_updated: string;
}

// ============================================================
// API HOOKS
// ============================================================

const useDirigeantDashboard = (syncBank = true) => {
  return useQuery({
    queryKey: ['accounting', 'dirigeant', 'dashboard', syncBank],
    queryFn: async () => {
      const response = await api.get<DirigeantDashboardData>(
        `/accounting/dirigeant/dashboard?sync_bank=${syncBank}`
      );
      return response.data;
    },
    staleTime: 60000, // 1 minute
  });
};

const useBankSync = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await api.post('/accounting/bank/sync');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting', 'dirigeant'] });
    },
  });
};

// ============================================================
// HELPER FUNCTIONS
// ============================================================

const formatCurrency = (value: number, currency = 'EUR') =>
  new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);

const formatDate = (dateStr: string) =>
  new Date(dateStr).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
  });

// ============================================================
// WIDGETS
// ============================================================

const CashPositionWidget: React.FC<{ data: CashPosition }> = ({ data }) => {
  const navigate = useNavigate();

  return (
    <Card
      title="Ma trésorerie"
      actions={
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/auto-accounting/bank')}
        >
          Voir les comptes
        </Button>
      }
    >
      <div className="azals-auto-accounting__cash">
        <div className="azals-auto-accounting__cash-main">
          <span className="azals-auto-accounting__cash-label">
            Solde disponible
          </span>
          <span className="azals-auto-accounting__cash-value">
            {formatCurrency(data.total_balance, data.currency)}
          </span>
        </div>

        {data.accounts.length > 1 && (
          <div className="azals-auto-accounting__cash-accounts">
            {data.accounts.slice(0, 3).map((account, index) => (
              <div key={index} className="azals-auto-accounting__cash-account">
                <span className="azals-auto-accounting__cash-account-name">
                  {account.name}
                </span>
                <span className="azals-auto-accounting__cash-account-balance">
                  {formatCurrency(account.balance, account.currency)}
                </span>
              </div>
            ))}
          </div>
        )}

        <div className="azals-auto-accounting__cash-freshness">
          <span
            className={`azals-freshness-indicator azals-freshness-indicator--${
              data.freshness_score >= 90
                ? 'good'
                : data.freshness_score >= 70
                ? 'warning'
                : 'stale'
            }`}
          />
          <span className="azals-auto-accounting__cash-freshness-text">
            {data.freshness_score >= 90
              ? 'Données à jour'
              : data.freshness_score >= 70
              ? 'Données récentes'
              : 'Actualisation recommandée'}
          </span>
        </div>
      </div>
    </Card>
  );
};

const CashForecastWidget: React.FC<{ data: CashForecast }> = ({ data }) => {
  const minBalance = Math.min(
    ...data.forecast_items.map((item) => item.expected_closing)
  );
  const isWarning =
    minBalance < data.warning_threshold && minBalance > data.alert_threshold;
  const isAlert = minBalance <= data.alert_threshold;

  return (
    <Card title="Prévision de trésorerie">
      <div className="azals-auto-accounting__forecast">
        <div className="azals-auto-accounting__forecast-chart">
          {data.forecast_items.map((item, index) => {
            const maxBalance = Math.max(
              ...data.forecast_items.map((i) => i.expected_closing)
            );
            const heightPercent = (item.expected_closing / maxBalance) * 100;

            return (
              <div
                key={index}
                className="azals-auto-accounting__forecast-bar-container"
              >
                <div
                  className={`azals-auto-accounting__forecast-bar ${
                    item.expected_closing <= data.alert_threshold
                      ? 'azals-auto-accounting__forecast-bar--danger'
                      : item.expected_closing <= data.warning_threshold
                      ? 'azals-auto-accounting__forecast-bar--warning'
                      : ''
                  }`}
                  style={{ height: `${Math.max(10, heightPercent)}%` }}
                />
                <span className="azals-auto-accounting__forecast-date">
                  {formatDate(item.date)}
                </span>
              </div>
            );
          })}
        </div>

        {(isWarning || isAlert) && (
          <div
            className={`azals-auto-accounting__forecast-alert ${
              isAlert ? 'azals-auto-accounting__forecast-alert--danger' : ''
            }`}
          >
            <AlertTriangle size={16} />
            <span>
              {isAlert
                ? 'Attention : trésorerie critique prévue'
                : 'Vigilance : trésorerie basse prévue'}
            </span>
          </div>
        )}
      </div>
    </Card>
  );
};

const InvoicesWidget: React.FC<{ data: InvoicesSummary }> = ({ data }) => {
  const _navigate = useNavigate();

  return (
    <Card title="Mes factures">
      <div className="azals-auto-accounting__invoices">
        {/* À payer */}
        <div className="azals-auto-accounting__invoices-section">
          <div className="azals-auto-accounting__invoices-header">
            <TrendingDown
              size={18}
              className="azals-auto-accounting__invoices-icon azals-auto-accounting__invoices-icon--pay"
            />
            <span>À payer</span>
          </div>
          <div className="azals-auto-accounting__invoices-content">
            <div className="azals-auto-accounting__invoices-main">
              <span className="azals-auto-accounting__invoices-amount">
                {formatCurrency(data.to_pay_amount)}
              </span>
              <span className="azals-auto-accounting__invoices-count">
                {data.to_pay_count} facture{data.to_pay_count > 1 ? 's' : ''}
              </span>
            </div>
            {data.overdue_to_pay_count > 0 && (
              <div className="azals-auto-accounting__invoices-overdue">
                <AlertTriangle size={14} />
                <span>
                  {data.overdue_to_pay_count} en retard (
                  {formatCurrency(data.overdue_to_pay_amount)})
                </span>
              </div>
            )}
          </div>
        </div>

        {/* À encaisser */}
        <div className="azals-auto-accounting__invoices-section">
          <div className="azals-auto-accounting__invoices-header">
            <TrendingUp
              size={18}
              className="azals-auto-accounting__invoices-icon azals-auto-accounting__invoices-icon--collect"
            />
            <span>À encaisser</span>
          </div>
          <div className="azals-auto-accounting__invoices-content">
            <div className="azals-auto-accounting__invoices-main">
              <span className="azals-auto-accounting__invoices-amount">
                {formatCurrency(data.to_collect_amount)}
              </span>
              <span className="azals-auto-accounting__invoices-count">
                {data.to_collect_count} facture
                {data.to_collect_count > 1 ? 's' : ''}
              </span>
            </div>
            {data.overdue_to_collect_count > 0 && (
              <div className="azals-auto-accounting__invoices-overdue azals-auto-accounting__invoices-overdue--collect">
                <Clock size={14} />
                <span>
                  {data.overdue_to_collect_count} en retard (
                  {formatCurrency(data.overdue_to_collect_amount)})
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};

const ResultWidget: React.FC<{ data: ResultSummary }> = ({ data }) => {
  const periodLabel =
    data.period === 'MONTH'
      ? 'ce mois'
      : data.period === 'QUARTER'
      ? 'ce trimestre'
      : "cette année";
  const isPositive = data.result >= 0;

  return (
    <Card title={`Mon résultat ${periodLabel}`}>
      <div className="azals-auto-accounting__result">
        <div
          className={`azals-auto-accounting__result-main ${
            isPositive
              ? 'azals-auto-accounting__result-main--positive'
              : 'azals-auto-accounting__result-main--negative'
          }`}
        >
          <span className="azals-auto-accounting__result-value">
            {formatCurrency(data.result)}
          </span>
          <span className="azals-auto-accounting__result-label">
            {isPositive ? 'Bénéfice estimé' : 'Perte estimée'}
          </span>
        </div>

        <div className="azals-auto-accounting__result-details">
          <div className="azals-auto-accounting__result-row">
            <span className="azals-auto-accounting__result-row-label">
              Chiffre d&apos;affaires
            </span>
            <span className="azals-auto-accounting__result-row-value azals-auto-accounting__result-row-value--positive">
              {formatCurrency(data.revenue)}
            </span>
          </div>
          <div className="azals-auto-accounting__result-row">
            <span className="azals-auto-accounting__result-row-label">
              Dépenses
            </span>
            <span className="azals-auto-accounting__result-row-value azals-auto-accounting__result-row-value--negative">
              {formatCurrency(data.expenses)}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

export const DirigeantDashboard: React.FC = () => {
  const { data, isLoading, error, refetch } = useDirigeantDashboard();
  const bankSync = useBankSync();
  const navigate = useNavigate();

  const handleRefresh = async () => {
    await bankSync.mutateAsync();
    void refetch();
  };

  if (isLoading) {
    return (
      <PageWrapper title="Mon entreprise">
        <div className="azals-loading">
          <div className="azals-spinner" />
          <p>Synchronisation de vos données...</p>
        </div>
      </PageWrapper>
    );
  }

  if (error || !data) {
    return (
      <PageWrapper title="Mon entreprise">
        <Card>
          <div className="azals-error">
            <AlertTriangle size={48} />
            <p>Impossible de charger vos données</p>
            <Button onClick={() => { refetch(); }}>Réessayer</Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  // Filter critical alerts only for dirigeant view
  const criticalAlerts = data.alerts.filter(
    (a) => a.severity === 'CRITICAL' || a.severity === 'ERROR'
  );

  return (
    <PageWrapper
      title="Mon entreprise"
      subtitle="Votre situation financière en temps réel"
      actions={
        <ButtonGroup>
          <Button
            variant="ghost"
            leftIcon={<RefreshCw size={16} />}
            onClick={handleRefresh}
            disabled={bankSync.isPending}
          >
            {bankSync.isPending ? 'Actualisation...' : 'Actualiser'}
          </Button>
        </ButtonGroup>
      }
    >
      {/* Alertes critiques (si présentes) */}
      {criticalAlerts.length > 0 && (
        <section className="azals-section azals-section--alerts">
          <Card title="Points d'attention" className="azals-card--warning">
            <div className="azals-auto-accounting__alerts">
              {criticalAlerts.slice(0, 3).map((alert) => (
                <div
                  key={alert.id}
                  className="azals-auto-accounting__alert"
                  onClick={() =>
                    alert.document_id &&
                    navigate(`/auto-accounting/documents/${alert.document_id}`)
                  }
                >
                  <AlertTriangle
                    size={18}
                    className={
                      alert.severity === 'CRITICAL'
                        ? 'azals-text--danger'
                        : 'azals-text--warning'
                    }
                  />
                  <div className="azals-auto-accounting__alert-content">
                    <span className="azals-auto-accounting__alert-title">
                      {alert.title}
                    </span>
                    <span className="azals-auto-accounting__alert-message">
                      {alert.message}
                    </span>
                  </div>
                  <ArrowRight size={16} />
                </div>
              ))}
            </div>
          </Card>
        </section>
      )}

      {/* Widgets principaux */}
      <section className="azals-section">
        <Grid cols={2} gap="md">
          <CashPositionWidget data={data.cash_position} />
          <CashForecastWidget data={data.cash_forecast} />
        </Grid>
      </section>

      <section className="azals-section">
        <Grid cols={2} gap="md">
          <InvoicesWidget data={data.invoices_summary} />
          <ResultWidget data={data.result_summary} />
        </Grid>
      </section>

      {/* Indicateur de fraîcheur des données */}
      <section className="azals-section">
        <div className="azals-auto-accounting__freshness-bar">
          <span className="azals-auto-accounting__freshness-label">
            Fraîcheur des données
          </span>
          <ProgressBar
            value={data.data_freshness}
            max={100}
            variant={
              data.data_freshness >= 90
                ? 'success'
                : data.data_freshness >= 70
                ? 'warning'
                : 'danger'
            }
          />
          <span className="azals-auto-accounting__freshness-time">
            Dernière mise à jour :{' '}
            {new Date(data.last_updated).toLocaleTimeString('fr-FR')}
          </span>
        </div>
      </section>
    </PageWrapper>
  );
};

export default DirigeantDashboard;
