// @ts-nocheck
/**
 * AZALSCORE Module - BUDGET
 * =========================
 * Interface de gestion budgetaire
 */

import React, { useState } from 'react';
import {
  Wallet, LayoutDashboard, TrendingUp, TrendingDown,
  AlertTriangle, FolderTree, Plus, RefreshCw,
  Check, X, Eye, ChevronRight, ArrowUpRight, ArrowDownRight,
} from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { KPICard } from '@ui/dashboards';
import { DataTable } from '@ui/tables';
import { Badge } from '@ui/simple';
import { Modal, Input, TextArea, Select } from '@ui/forms';
import { formatDate, formatCurrency, formatPercent } from '@/utils/formatters';
import type { TableColumn, DashboardKPI } from '@/types';

import {
  useBudgetDashboard,
  useBudgets,
  useBudgetCategories,
  useBudgetAlerts,
  useCreateBudget,
  useSubmitBudget,
  useApproveBudget,
  useAcknowledgeAlert,
} from './hooks';
import type {
  Budget, BudgetCategory, BudgetAlert, BudgetVariance,
  BudgetType, BudgetStatus, AlertSeverity,
} from './types';
import {
  BUDGET_TYPE_CONFIG,
  BUDGET_STATUS_CONFIG,
  ALERT_SEVERITY_CONFIG,
  VARIANCE_TYPE_CONFIG,
} from './types';

// ============================================================================
// BADGES
// ============================================================================

const TypeBadge: React.FC<{ type: BudgetType }> = ({ type }) => {
  const config = BUDGET_TYPE_CONFIG[type];
  return <Badge variant="default">{config?.label || type}</Badge>;
};

const StatusBadge: React.FC<{ status: BudgetStatus }> = ({ status }) => {
  const config = BUDGET_STATUS_CONFIG[status];
  const variant = config?.color === 'green' ? 'success' :
    config?.color === 'red' ? 'destructive' :
    config?.color === 'blue' ? 'info' : 'default';
  return <Badge variant={variant}>{config?.label || status}</Badge>;
};

const SeverityBadge: React.FC<{ severity: AlertSeverity }> = ({ severity }) => {
  const config = ALERT_SEVERITY_CONFIG[severity];
  const variant = config?.color === 'red' ? 'destructive' :
    config?.color === 'orange' ? 'warning' : 'info';
  return <Badge variant={variant}>{config?.label || severity}</Badge>;
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

type View = 'dashboard' | 'budgets' | 'categories' | 'alerts';

const BudgetModule: React.FC = () => {
  const currentYear = new Date().getFullYear();
  const [view, setView] = useState<View>('dashboard');
  const [fiscalYear, setFiscalYear] = useState(currentYear);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [selectedBudget, setSelectedBudget] = useState<Budget | null>(null);
  const [createModal, setCreateModal] = useState(false);
  const [newBudget, setNewBudget] = useState({
    code: '',
    name: '',
    description: '',
    budget_type: 'OPERATING' as BudgetType,
    period_type: 'ANNUAL' as const,
    fiscal_year: currentYear,
    start_date: `${currentYear}-01-01`,
    end_date: `${currentYear}-12-31`,
  });

  const { data: dashboard, isLoading: dashboardLoading, refetch: refetchDashboard } = useBudgetDashboard(fiscalYear);
  const { data: budgets, isLoading: budgetsLoading, refetch: refetchBudgets } = useBudgets({
    fiscal_year: fiscalYear,
    page,
    page_size: pageSize,
  });
  const { data: categories, isLoading: categoriesLoading } = useBudgetCategories();
  const { data: alerts, isLoading: alertsLoading } = useBudgetAlerts({ status: 'ACTIVE' });

  const createBudgetMutation = useCreateBudget();
  const submitBudgetMutation = useSubmitBudget();
  const approveBudgetMutation = useApproveBudget();
  const acknowledgeAlertMutation = useAcknowledgeAlert();

  const handleCreateBudget = async () => {
    await createBudgetMutation.mutateAsync(newBudget);
    setCreateModal(false);
    setNewBudget({
      code: '',
      name: '',
      description: '',
      budget_type: 'OPERATING',
      period_type: 'ANNUAL',
      fiscal_year: currentYear,
      start_date: `${currentYear}-01-01`,
      end_date: `${currentYear}-12-31`,
    });
  };

  const handleRefresh = () => {
    if (view === 'dashboard') refetchDashboard();
    else if (view === 'budgets') refetchBudgets();
  };

  const kpis: DashboardKPI[] = dashboard ? [
    {
      id: 'budgeted_expense',
      label: 'Budget Depenses',
      value: formatCurrency(dashboard.total_budgeted_expense),
      icon: <TrendingDown size={20} />,
      variant: 'default',
    },
    {
      id: 'actual_expense',
      label: 'Realise Depenses',
      value: formatCurrency(dashboard.total_actual_expense),
      icon: <TrendingUp size={20} />,
      variant: dashboard.overall_consumption_rate > 90 ? 'danger' : 'success',
    },
    {
      id: 'consumption',
      label: 'Taux Consommation',
      value: formatPercent(dashboard.overall_consumption_rate / 100),
      icon: <Wallet size={20} />,
      variant: dashboard.overall_consumption_rate > 95 ? 'danger' :
        dashboard.overall_consumption_rate > 80 ? 'warning' : 'success',
    },
    {
      id: 'alerts',
      label: 'Alertes Actives',
      value: dashboard.active_alerts_count,
      icon: <AlertTriangle size={20} />,
      variant: dashboard.critical_alerts_count > 0 ? 'danger' :
        dashboard.active_alerts_count > 0 ? 'warning' : 'success',
    },
  ] : [];

  const budgetColumns: TableColumn<Budget>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      render: (_, row): React.ReactNode => (
        <button
          className="text-left hover:text-primary"
          onClick={() => setSelectedBudget(row)}
        >
          <div className="font-medium">{row.code}</div>
          <div className="text-xs text-gray-500">{row.name}</div>
        </button>
      ),
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'budget_type',
      render: (v): React.ReactNode => <TypeBadge type={v as BudgetType} />,
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (v): React.ReactNode => <StatusBadge status={v as BudgetStatus} />,
    },
    {
      id: 'total_expense',
      header: 'Depenses',
      accessor: 'total_expense',
      render: (_, row): React.ReactNode => formatCurrency(row.total_expense, row.currency),
    },
    {
      id: 'total_revenue',
      header: 'Recettes',
      accessor: 'total_revenue',
      render: (_, row): React.ReactNode => formatCurrency(row.total_revenue, row.currency),
    },
    {
      id: 'net_result',
      header: 'Resultat',
      accessor: 'net_result',
      render: (_, row): React.ReactNode => (
        <span className={row.net_result >= 0 ? 'text-green-600' : 'text-red-600'}>
          {formatCurrency(row.net_result, row.currency)}
        </span>
      ),
    },
    {
      id: 'period',
      header: 'Periode',
      accessor: 'fiscal_year',
      render: (_, row): React.ReactNode => (
        <span className="text-sm text-gray-600">
          {formatDate(row.start_date)} - {formatDate(row.end_date)}
        </span>
      ),
    },
    {
      id: 'actions',
      header: '',
      accessor: 'id',
      width: 120,
      render: (_, row): React.ReactNode => (
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" onClick={() => setSelectedBudget(row)}>
            <Eye size={14} />
          </Button>
          {row.status === 'DRAFT' && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => submitBudgetMutation.mutate({ id: row.id })}
              disabled={submitBudgetMutation.isPending}
            >
              Soumettre
            </Button>
          )}
          {row.status === 'SUBMITTED' && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => approveBudgetMutation.mutate({ id: row.id })}
              disabled={approveBudgetMutation.isPending}
            >
              <Check size={14} />
            </Button>
          )}
        </div>
      ),
    },
  ];

  const categoryColumns: TableColumn<BudgetCategory>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      render: (_, row): React.ReactNode => (
        <div style={{ paddingLeft: `${row.level * 20}px` }}>
          <span className="font-medium">{row.code}</span>
        </div>
      ),
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
    },
    {
      id: 'line_type',
      header: 'Type',
      accessor: 'line_type',
      render: (v): React.ReactNode => (
        <Badge variant={v === 'REVENUE' ? 'success' : v === 'EXPENSE' ? 'destructive' : 'default'}>
          {v === 'REVENUE' ? 'Recette' : v === 'EXPENSE' ? 'Depense' : 'Invest.'}
        </Badge>
      ),
    },
    {
      id: 'account_codes',
      header: 'Comptes',
      accessor: 'account_codes',
      render: (v): React.ReactNode => (v as string[])?.length > 0
        ? <span className="text-xs text-gray-500">{(v as string[]).join(', ')}</span>
        : '-',
    },
    {
      id: 'is_active',
      header: 'Actif',
      accessor: 'is_active',
      render: (v): React.ReactNode => v
        ? <Badge variant="success">Oui</Badge>
        : <Badge variant="default">Non</Badge>,
    },
  ];

  const alertColumns: TableColumn<BudgetAlert>[] = [
    {
      id: 'severity',
      header: 'Severite',
      accessor: 'severity',
      render: (v): React.ReactNode => <SeverityBadge severity={v as AlertSeverity} />,
    },
    {
      id: 'title',
      header: 'Titre',
      accessor: 'title',
      render: (_, row): React.ReactNode => (
        <div>
          <div className="font-medium">{row.title}</div>
          <div className="text-xs text-gray-500">{row.message}</div>
        </div>
      ),
    },
    {
      id: 'threshold',
      header: 'Seuil',
      accessor: 'threshold_percent',
      render: (_, row): React.ReactNode => row.threshold_percent
        ? <span className="text-sm">{row.threshold_percent}% / {row.current_percent}%</span>
        : '-',
    },
    {
      id: 'period',
      header: 'Periode',
      accessor: 'period',
      render: (v): React.ReactNode => (v as string) || '-',
    },
    {
      id: 'triggered_at',
      header: 'Declenchee le',
      accessor: 'triggered_at',
      render: (v): React.ReactNode => formatDate(v as string),
    },
    {
      id: 'actions',
      header: '',
      accessor: 'id',
      width: 100,
      render: (_, row): React.ReactNode => row.status === 'ACTIVE' && (
        <Button
          size="sm"
          variant="secondary"
          onClick={() => acknowledgeAlertMutation.mutate({ alertId: row.id })}
          disabled={acknowledgeAlertMutation.isPending}
        >
          Acquitter
        </Button>
      ),
    },
  ];

  return (
    <PageWrapper
      title="Gestion Budgetaire"
      subtitle={`Exercice ${fiscalYear}`}
      actions={
        <div className="flex gap-2">
          <Select
            value={String(fiscalYear)}
            onChange={(v) => setFiscalYear(Number(v))}
            options={[
              { value: String(currentYear - 1), label: String(currentYear - 1) },
              { value: String(currentYear), label: String(currentYear) },
              { value: String(currentYear + 1), label: String(currentYear + 1) },
            ]}
          />
          {view === 'budgets' && (
            <Button variant="primary" onClick={() => setCreateModal(true)}>
              <Plus size={16} className="mr-2" />
              Nouveau budget
            </Button>
          )}
          <Button variant="secondary" onClick={handleRefresh}>
            <RefreshCw size={16} className="mr-2" />
            Actualiser
          </Button>
        </div>
      }
    >
      {/* KPIs */}
      {view === 'dashboard' && kpis.length > 0 && (
        <Grid cols={4} gap="md" className="mb-6">
          {kpis.map((kpi) => (
            <KPICard key={kpi.id} kpi={kpi} />
          ))}
        </Grid>
      )}

      {/* Tabs */}
      <div className="flex gap-4 mb-6 border-b">
        <button
          onClick={() => setView('dashboard')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${view === 'dashboard' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <LayoutDashboard size={16} className="inline mr-1" />
          Tableau de bord
        </button>
        <button
          onClick={() => setView('budgets')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${view === 'budgets' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <Wallet size={16} className="inline mr-1" />
          Budgets ({budgets?.total || 0})
        </button>
        <button
          onClick={() => setView('categories')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${view === 'categories' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <FolderTree size={16} className="inline mr-1" />
          Categories
        </button>
        <button
          onClick={() => setView('alerts')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${view === 'alerts' ? 'border-primary text-primary' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <AlertTriangle size={16} className="inline mr-1" />
          Alertes ({alerts?.total || 0})
        </button>
      </div>

      {/* Dashboard Content */}
      {view === 'dashboard' && dashboard && (
        <Grid cols={2} gap="md">
          {/* Budgets Summary */}
          <Card title="Budgets actifs">
            <div className="space-y-3">
              {dashboard.budgets_summary.slice(0, 5).map((b) => (
                <div key={b.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium">{b.name}</div>
                    <div className="text-xs text-gray-500">
                      {BUDGET_TYPE_CONFIG[b.budget_type]?.label} - {formatCurrency(b.total_expense)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold">{b.consumption_rate.toFixed(1)}%</div>
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div
                        className={`rounded-full h-2 ${b.consumption_rate > 95 ? 'bg-red-500' : b.consumption_rate > 80 ? 'bg-orange-500' : 'bg-green-500'}`}
                        style={{ width: `${Math.min(b.consumption_rate, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Top Variances */}
          <Card title="Principaux ecarts">
            <div className="space-y-3">
              {dashboard.top_overruns.slice(0, 3).map((v, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-red-50 rounded">
                  <div>
                    <div className="font-medium text-red-800">{v.category_name}</div>
                    <div className="text-xs text-red-600">{v.line_name || 'Total categorie'}</div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center text-red-600">
                      <ArrowUpRight size={16} />
                      <span className="font-semibold">{formatPercent(v.variance_percent / 100)}</span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatCurrency(v.variance_amount)}
                    </div>
                  </div>
                </div>
              ))}
              {dashboard.top_savings.slice(0, 2).map((v, i) => (
                <div key={`s-${i}`} className="flex items-center justify-between p-3 bg-green-50 rounded">
                  <div>
                    <div className="font-medium text-green-800">{v.category_name}</div>
                    <div className="text-xs text-green-600">{v.line_name || 'Total categorie'}</div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center text-green-600">
                      <ArrowDownRight size={16} />
                      <span className="font-semibold">{formatPercent(Math.abs(v.variance_percent) / 100)}</span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatCurrency(Math.abs(v.variance_amount))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Recent Alerts */}
          <Card title="Alertes recentes" className="col-span-2">
            <div className="space-y-2">
              {dashboard.recent_alerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="flex items-center justify-between p-3 border rounded">
                  <div className="flex items-center gap-3">
                    <SeverityBadge severity={alert.severity} />
                    <div>
                      <div className="font-medium">{alert.title}</div>
                      <div className="text-xs text-gray-500">{alert.message}</div>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(alert.triggered_at)}
                  </div>
                </div>
              ))}
              {dashboard.recent_alerts.length === 0 && (
                <div className="text-center py-4 text-gray-500">
                  Aucune alerte recente
                </div>
              )}
            </div>
          </Card>
        </Grid>
      )}

      {/* Budgets List */}
      {view === 'budgets' && (
        <Card noPadding>
          <DataTable
            columns={budgetColumns}
            data={budgets?.items || []}
            keyField="id"
            isLoading={budgetsLoading}
            pagination={{
              page,
              pageSize,
              total: budgets?.total || 0,
              onPageChange: setPage,
              onPageSizeChange: setPageSize,
            }}
            emptyMessage="Aucun budget pour cet exercice"
          />
        </Card>
      )}

      {/* Categories List */}
      {view === 'categories' && (
        <Card noPadding>
          <DataTable
            columns={categoryColumns}
            data={categories?.items || []}
            keyField="id"
            isLoading={categoriesLoading}
            emptyMessage="Aucune categorie configuree"
          />
        </Card>
      )}

      {/* Alerts List */}
      {view === 'alerts' && (
        <Card noPadding>
          <DataTable
            columns={alertColumns}
            data={alerts?.items || []}
            keyField="id"
            isLoading={alertsLoading}
            emptyMessage="Aucune alerte active"
          />
        </Card>
      )}

      {/* Create Budget Modal */}
      <Modal
        isOpen={createModal}
        onClose={() => setCreateModal(false)}
        title="Nouveau budget"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="block text-sm font-medium">Code <span className="text-red-500">*</span></label>
              <Input
                value={newBudget.code}
                onChange={(v) => setNewBudget({ ...newBudget, code: v })}
              />
            </div>
            <div className="space-y-1">
              <label className="block text-sm font-medium">Type</label>
              <Select
                value={newBudget.budget_type}
                onChange={(v) => setNewBudget({ ...newBudget, budget_type: v as BudgetType })}
                options={Object.entries(BUDGET_TYPE_CONFIG).map(([value, config]) => ({
                  value,
                  label: config.label,
                }))}
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="block text-sm font-medium">Nom <span className="text-red-500">*</span></label>
            <Input
              value={newBudget.name}
              onChange={(v) => setNewBudget({ ...newBudget, name: v })}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-sm font-medium">Description</label>
            <TextArea
              value={newBudget.description}
              onChange={(v) => setNewBudget({ ...newBudget, description: v })}
              rows={2}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-1">
              <label className="block text-sm font-medium">Exercice</label>
              <Input
                type="number"
                value={String(newBudget.fiscal_year)}
                onChange={(v) => setNewBudget({ ...newBudget, fiscal_year: Number(v) })}
              />
            </div>
            <div className="space-y-1">
              <label className="block text-sm font-medium">Date debut</label>
              <input
                type="date"
                className="azals-input w-full"
                value={newBudget.start_date}
                onChange={(e) => setNewBudget({ ...newBudget, start_date: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <label className="block text-sm font-medium">Date fin</label>
              <input
                type="date"
                className="azals-input w-full"
                value={newBudget.end_date}
                onChange={(e) => setNewBudget({ ...newBudget, end_date: e.target.value })}
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="secondary" onClick={() => setCreateModal(false)}>
              Annuler
            </Button>
            <Button
              variant="primary"
              onClick={handleCreateBudget}
              disabled={!newBudget.code || !newBudget.name || createBudgetMutation.isPending}
            >
              <Plus size={16} className="mr-2" />
              Creer
            </Button>
          </div>
        </div>
      </Modal>

      {/* Budget Detail Modal */}
      <Modal
        isOpen={!!selectedBudget}
        onClose={() => setSelectedBudget(null)}
        title={selectedBudget?.name || 'Detail'}
      >
        {selectedBudget && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Code:</span>
                <span className="ml-2 font-medium">{selectedBudget.code}</span>
              </div>
              <div>
                <span className="text-gray-500">Type:</span>
                <span className="ml-2"><TypeBadge type={selectedBudget.budget_type} /></span>
              </div>
              <div>
                <span className="text-gray-500">Statut:</span>
                <span className="ml-2"><StatusBadge status={selectedBudget.status} /></span>
              </div>
              <div>
                <span className="text-gray-500">Exercice:</span>
                <span className="ml-2">{selectedBudget.fiscal_year}</span>
              </div>
              <div>
                <span className="text-gray-500">Periode:</span>
                <span className="ml-2">
                  {formatDate(selectedBudget.start_date)} - {formatDate(selectedBudget.end_date)}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Version:</span>
                <span className="ml-2">{selectedBudget.version_number}</span>
              </div>
            </div>

            <div className="border-t pt-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="p-3 bg-green-50 rounded">
                  <div className="text-xs text-gray-500">Recettes</div>
                  <div className="text-lg font-semibold text-green-600">
                    {formatCurrency(selectedBudget.total_revenue, selectedBudget.currency)}
                  </div>
                </div>
                <div className="p-3 bg-red-50 rounded">
                  <div className="text-xs text-gray-500">Depenses</div>
                  <div className="text-lg font-semibold text-red-600">
                    {formatCurrency(selectedBudget.total_expense, selectedBudget.currency)}
                  </div>
                </div>
                <div className={`p-3 rounded ${selectedBudget.net_result >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                  <div className="text-xs text-gray-500">Resultat</div>
                  <div className={`text-lg font-semibold ${selectedBudget.net_result >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(selectedBudget.net_result, selectedBudget.currency)}
                  </div>
                </div>
              </div>
            </div>

            {selectedBudget.description && (
              <div className="border-t pt-4">
                <div className="text-sm text-gray-500 mb-1">Description</div>
                <div className="text-sm">{selectedBudget.description}</div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button variant="secondary" onClick={() => setSelectedBudget(null)}>
                Fermer
              </Button>
              <Button variant="primary">
                <ChevronRight size={16} className="mr-1" />
                Voir details
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </PageWrapper>
  );
};

export default BudgetModule;
