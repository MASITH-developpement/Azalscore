/**
 * Vue Expert-Comptable - Dashboard Comptabilité Automatisée
 *
 * Objectif: Valider par exception, JAMAIS saisir
 *
 * INCLUT:
 * - File d'attente validation (confiance IA < seuil)
 * - Statistiques IA (précision, tendances)
 * - Rapprochement bancaire
 * - Validation en masse
 * - Certification des périodes
 *
 * INTERDICTIONS:
 * - Aucune saisie manuelle
 * - Aucune modification directe d'écriture
 * - L'expert valide ou rejette, jamais ne produit
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Brain,
  Target,
  Link2,
  Clock,
  Filter,
  Check,
  X,
  Eye,
  ChevronRight,
  BarChart3,
  RefreshCw,
  Calendar,
  Lock,
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup } from '@ui/actions';
import { StatusBadge, StatCard } from '@ui/dashboards';
import { Modal, Select, TextArea } from '@ui/forms';
import type { TableColumn } from '@/types';

// ============================================================
// TYPES
// ============================================================

interface ValidationQueueItem {
  id: string;
  document_id: string;
  document_type: string;
  reference: string | null;
  partner_name: string | null;
  amount_total: number | null;
  document_date: string | null;
  ai_confidence: string;
  ai_confidence_score: number;
  suggested_account: string | null;
  suggested_journal: string | null;
  issue_type: string;
  received_at: string;
}

interface AIPerformanceStats {
  total_processed: number;
  auto_validated: number;
  manual_validated: number;
  rejected: number;
  auto_validation_rate: number;
  precision_rate: number;
  avg_confidence: number;
  trend_7d: number;
}

interface ReconciliationStats {
  total_transactions: number;
  auto_reconciled: number;
  manual_reconciled: number;
  pending: number;
  auto_reconciliation_rate: number;
  avg_match_time_hours: number;
}

interface PeriodStatus {
  period: string;
  status: 'OPEN' | 'PENDING_CERTIFICATION' | 'CERTIFIED';
  documents_count: number;
  entries_count: number;
  pending_validation: number;
  unreconciled: number;
  certified_at: string | null;
  certified_by: string | null;
}

interface ExpertDashboardData {
  validation_queue: ValidationQueueItem[];
  validation_queue_total: number;
  ai_performance: AIPerformanceStats;
  reconciliation_stats: ReconciliationStats;
  periods: PeriodStatus[];
  last_updated: string;
}

// ============================================================
// API HOOKS
// ============================================================

const useExpertDashboard = () => {
  return useQuery({
    queryKey: ['accounting', 'expert', 'dashboard'],
    queryFn: async () => {
      const response = await api.get<ExpertDashboardData>(
        '/accounting/expert/dashboard'
      );
      return response.data;
    },
    staleTime: 30000,
  });
};

interface ValidationQueueResponse {
  items: ValidationQueueItem[];
  total: number;
}

const useValidationQueue = (
  page = 1,
  pageSize = 20,
  filters: Record<string, string> = {}
) => {
  return useQuery<ValidationQueueResponse>({
    queryKey: ['accounting', 'expert', 'validation-queue', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        ...filters,
      });
      const response = await api.get<ValidationQueueResponse>(
        `/accounting/expert/validation-queue?${params}`
      );
      return response.data;
    },
  });
};

const useBulkValidate = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      entryIds,
      action,
      comment,
    }: {
      entryIds: string[];
      action: 'VALIDATE' | 'REJECT';
      comment?: string;
    }) => {
      const response = await api.post('/accounting/expert/bulk-validate', {
        entry_ids: entryIds,
        action,
        comment,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

const useCertifyPeriod = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ period }: { period: string }) => {
      const response = await api.post(`/accounting/expert/certify-period`, {
        period,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

// ============================================================
// HELPER FUNCTIONS
// ============================================================

const formatCurrency = (value: number | null) =>
  value !== null
    ? new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
      }).format(value)
    : '-';

const formatDate = (dateStr: string | null) =>
  dateStr ? new Date(dateStr).toLocaleDateString('fr-FR') : '-';

const formatPercent = (value: number) =>
  new Intl.NumberFormat('fr-FR', {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(value / 100);

const getConfidenceVariant = (
  confidence: string
): 'success' | 'warning' | 'danger' | 'info' => {
  switch (confidence) {
    case 'HIGH':
      return 'success';
    case 'MEDIUM':
      return 'warning';
    case 'LOW':
    case 'VERY_LOW':
      return 'danger';
    default:
      return 'info';
  }
};

const getConfidenceLabel = (confidence: string): string => {
  const labels: Record<string, string> = {
    HIGH: 'Haute',
    MEDIUM: 'Moyenne',
    LOW: 'Basse',
    VERY_LOW: 'Très basse',
  };
  return labels[confidence] || confidence;
};

const getIssueTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    LOW_CONFIDENCE: 'Confiance IA basse',
    MISSING_INFO: 'Information manquante',
    DUPLICATE_SUSPECT: 'Doublon potentiel',
    AMOUNT_MISMATCH: 'Écart montant',
    ACCOUNT_UNKNOWN: 'Compte inconnu',
    MANUAL_REVIEW: 'Revue manuelle requise',
  };
  return labels[type] || type;
};

const getPeriodStatusVariant = (
  status: string
): 'success' | 'warning' | 'danger' | 'info' | 'default' => {
  switch (status) {
    case 'CERTIFIED':
      return 'success';
    case 'PENDING_CERTIFICATION':
      return 'warning';
    case 'OPEN':
      return 'info';
    default:
      return 'default';
  }
};

const getPeriodStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    OPEN: 'Ouvert',
    PENDING_CERTIFICATION: 'À certifier',
    CERTIFIED: 'Certifié',
  };
  return labels[status] || status;
};

// ============================================================
// WIDGETS
// ============================================================

const AIPerformanceWidget: React.FC<{ stats: AIPerformanceStats }> = ({
  stats,
}) => {
  const TrendIcon = stats.trend_7d >= 0 ? TrendingUp : TrendingDown;
  const trendColor = stats.trend_7d >= 0 ? 'success' : 'danger';

  return (
    <Card title="Performance IA" icon={<Brain size={18} />}>
      <div className="azals-auto-accounting__ai-stats">
        <div className="azals-auto-accounting__ai-stat-row">
          <div className="azals-auto-accounting__ai-stat">
            <Target size={16} className="azals-text--success" />
            <div className="azals-auto-accounting__ai-stat-content">
              <span className="azals-auto-accounting__ai-stat-value">
                {formatPercent(stats.precision_rate)}
              </span>
              <span className="azals-auto-accounting__ai-stat-label">
                Précision
              </span>
            </div>
          </div>

          <div className="azals-auto-accounting__ai-stat">
            <CheckCircle size={16} className="azals-text--info" />
            <div className="azals-auto-accounting__ai-stat-content">
              <span className="azals-auto-accounting__ai-stat-value">
                {formatPercent(stats.auto_validation_rate)}
              </span>
              <span className="azals-auto-accounting__ai-stat-label">
                Auto-validé
              </span>
            </div>
          </div>

          <div className="azals-auto-accounting__ai-stat">
            <BarChart3 size={16} className="azals-text--warning" />
            <div className="azals-auto-accounting__ai-stat-content">
              <span className="azals-auto-accounting__ai-stat-value">
                {stats.avg_confidence.toFixed(0)}%
              </span>
              <span className="azals-auto-accounting__ai-stat-label">
                Confiance moy.
              </span>
            </div>
          </div>

          <div className="azals-auto-accounting__ai-stat">
            <TrendIcon size={16} className={`azals-text--${trendColor}`} />
            <div className="azals-auto-accounting__ai-stat-content">
              <span className="azals-auto-accounting__ai-stat-value">
                {stats.trend_7d >= 0 ? '+' : ''}
                {stats.trend_7d.toFixed(1)}%
              </span>
              <span className="azals-auto-accounting__ai-stat-label">
                Tendance 7j
              </span>
            </div>
          </div>
        </div>

        <div className="azals-auto-accounting__ai-breakdown">
          <div className="azals-auto-accounting__ai-breakdown-item">
            <span>Traités</span>
            <strong>{stats.total_processed}</strong>
          </div>
          <div className="azals-auto-accounting__ai-breakdown-item">
            <span>Auto-validés</span>
            <strong className="azals-text--success">
              {stats.auto_validated}
            </strong>
          </div>
          <div className="azals-auto-accounting__ai-breakdown-item">
            <span>Validés manuellement</span>
            <strong className="azals-text--warning">
              {stats.manual_validated}
            </strong>
          </div>
          <div className="azals-auto-accounting__ai-breakdown-item">
            <span>Rejetés</span>
            <strong className="azals-text--danger">{stats.rejected}</strong>
          </div>
        </div>
      </div>
    </Card>
  );
};

const ReconciliationStatsWidget: React.FC<{ stats: ReconciliationStats }> = ({
  stats,
}) => {
  return (
    <Card title="Rapprochement bancaire" icon={<Link2 size={18} />}>
      <div className="azals-auto-accounting__reconciliation-stats">
        <div className="azals-auto-accounting__reconciliation-main">
          <div className="azals-auto-accounting__reconciliation-rate">
            <span className="azals-auto-accounting__reconciliation-rate-value">
              {formatPercent(stats.auto_reconciliation_rate)}
            </span>
            <span className="azals-auto-accounting__reconciliation-rate-label">
              Taux de rapprochement auto
            </span>
          </div>

          <div className="azals-auto-accounting__reconciliation-pending">
            {stats.pending > 0 ? (
              <>
                <AlertTriangle size={20} className="azals-text--warning" />
                <span>
                  <strong>{stats.pending}</strong> transactions en attente
                </span>
              </>
            ) : (
              <>
                <CheckCircle size={20} className="azals-text--success" />
                <span>Tout est rapproché</span>
              </>
            )}
          </div>
        </div>

        <div className="azals-auto-accounting__reconciliation-breakdown">
          <div className="azals-auto-accounting__reconciliation-item">
            <span>Total transactions</span>
            <strong>{stats.total_transactions}</strong>
          </div>
          <div className="azals-auto-accounting__reconciliation-item">
            <span>Auto-rapprochés</span>
            <strong className="azals-text--success">
              {stats.auto_reconciled}
            </strong>
          </div>
          <div className="azals-auto-accounting__reconciliation-item">
            <span>Manuels</span>
            <strong className="azals-text--warning">
              {stats.manual_reconciled}
            </strong>
          </div>
          <div className="azals-auto-accounting__reconciliation-item">
            <span>Temps moyen</span>
            <strong>{stats.avg_match_time_hours.toFixed(1)}h</strong>
          </div>
        </div>
      </div>
    </Card>
  );
};

const PeriodsWidget: React.FC<{
  periods: PeriodStatus[];
  onCertify: (period: string) => void;
  isLoading: boolean;
}> = ({ periods, onCertify, isLoading }) => {
  return (
    <Card title="Périodes comptables" icon={<Calendar size={18} />}>
      <div className="azals-auto-accounting__periods">
        {periods.map((period) => (
          <div key={period.period} className="azals-auto-accounting__period">
            <div className="azals-auto-accounting__period-header">
              <span className="azals-auto-accounting__period-name">
                {period.period}
              </span>
              <StatusBadge
                variant={getPeriodStatusVariant(period.status)}
                size="sm"
                status={getPeriodStatusLabel(period.status)}
              />
            </div>

            <div className="azals-auto-accounting__period-stats">
              <span>{period.documents_count} documents</span>
              <span>{period.entries_count} écritures</span>
              {period.pending_validation > 0 && (
                <span className="azals-text--warning">
                  {period.pending_validation} à valider
                </span>
              )}
              {period.unreconciled > 0 && (
                <span className="azals-text--danger">
                  {period.unreconciled} non rapprochés
                </span>
              )}
            </div>

            {period.status === 'PENDING_CERTIFICATION' &&
              period.pending_validation === 0 &&
              period.unreconciled === 0 && (
                <Button
                  variant="primary"
                  size="sm"
                  leftIcon={<Lock size={14} />}
                  onClick={() => onCertify(period.period)}
                  disabled={isLoading}
                >
                  Certifier
                </Button>
              )}

            {period.certified_at && (
              <div className="azals-auto-accounting__period-certified">
                Certifié le {formatDate(period.certified_at)}
                {period.certified_by && ` par ${period.certified_by}`}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

// ============================================================
// VALIDATION MODAL
// ============================================================

const ValidationModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  selectedItems: ValidationQueueItem[];
  action: 'VALIDATE' | 'REJECT';
  onConfirm: (comment: string) => void;
  isLoading: boolean;
}> = ({ isOpen, onClose, selectedItems, action, onConfirm, isLoading }) => {
  const [comment, setComment] = useState('');

  const handleConfirm = () => {
    onConfirm(comment);
    setComment('');
  };

  const totalAmount = selectedItems.reduce(
    (sum, item) => sum + (item.amount_total || 0),
    0
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        action === 'VALIDATE'
          ? `Valider ${selectedItems.length} écriture(s)`
          : `Rejeter ${selectedItems.length} écriture(s)`
      }
    >
      <div className="azals-auto-accounting__validation-modal">
        <div className="azals-auto-accounting__validation-summary">
          <div className="azals-auto-accounting__validation-count">
            <strong>{selectedItems.length}</strong> écriture(s) sélectionnée(s)
          </div>
          <div className="azals-auto-accounting__validation-amount">
            Montant total: <strong>{formatCurrency(totalAmount)}</strong>
          </div>
        </div>

        {selectedItems.length <= 5 && (
          <div className="azals-auto-accounting__validation-list">
            {selectedItems.map((item) => (
              <div
                key={item.id}
                className="azals-auto-accounting__validation-item"
              >
                <span>{item.reference || item.partner_name || 'Sans réf.'}</span>
                <span>{formatCurrency(item.amount_total)}</span>
                <StatusBadge
                  variant={getConfidenceVariant(item.ai_confidence)}
                  size="sm"
                  status={`${item.ai_confidence_score.toFixed(0)}%`}
                />
              </div>
            ))}
          </div>
        )}

        <div className="azals-form-group">
          <label className="azals-form-label">
            Commentaire {action === 'REJECT' && '(obligatoire)'}
          </label>
          <TextArea
            value={comment}
            onChange={(value) => setComment(value)}
            placeholder={
              action === 'VALIDATE'
                ? 'Commentaire optionnel...'
                : 'Motif du rejet...'
            }
            rows={3}
          />
        </div>

        <div className="azals-modal__actions">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button
            variant={action === 'VALIDATE' ? 'primary' : 'danger'}
            onClick={handleConfirm}
            disabled={
              isLoading || (action === 'REJECT' && comment.trim() === '')
            }
          >
            {isLoading
              ? 'En cours...'
              : action === 'VALIDATE'
              ? 'Valider'
              : 'Rejeter'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

export const ExpertDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [confidenceFilter, setConfidenceFilter] = useState<string | null>(null);
  const [validationAction, setValidationAction] = useState<
    'VALIDATE' | 'REJECT' | null
  >(null);

  const { data: dashboard, isLoading: dashboardLoading } = useExpertDashboard();
  const { data: validationQueue, isLoading: queueLoading } = useValidationQueue(
    page,
    20,
    confidenceFilter ? { confidence: confidenceFilter } : {}
  );

  const bulkValidate = useBulkValidate();
  const certifyPeriod = useCertifyPeriod();

  const selectedItems =
    dashboard?.validation_queue.filter((item) =>
      selectedIds.includes(item.id)
    ) || [];

  const handleBulkAction = (action: 'VALIDATE' | 'REJECT') => {
    if (selectedIds.length === 0) return;
    setValidationAction(action);
  };

  const handleConfirmValidation = async (comment: string) => {
    if (!validationAction) return;

    try {
      await bulkValidate.mutateAsync({
        entryIds: selectedIds,
        action: validationAction,
        comment: comment || undefined,
      });
      setSelectedIds([]);
      setValidationAction(null);
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const handleCertifyPeriod = async (period: string) => {
    try {
      await certifyPeriod.mutateAsync({ period });
    } catch (error) {
      console.error('Certification failed:', error);
    }
  };

  const handleSelectAll = () => {
    if (selectedIds.length === (validationQueue?.items?.length || 0)) {
      setSelectedIds([]);
    } else {
      setSelectedIds(validationQueue?.items?.map((item: ValidationQueueItem) => item.id) || []);
    }
  };

  const handleSelectItem = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const columns: TableColumn<ValidationQueueItem>[] = [
    {
      id: 'select',
      header: (
        <input
          type="checkbox"
          checked={
            selectedIds.length > 0 &&
            selectedIds.length === (validationQueue?.items?.length || 0)
          }
          onChange={handleSelectAll}
        />
      ),
      accessor: 'id',
      width: '40px',
      render: (_, row) => (
        <input
          type="checkbox"
          checked={selectedIds.includes(row.id)}
          onChange={() => handleSelectItem(row.id)}
          onClick={(e) => e.stopPropagation()}
        />
      ),
    },
    {
      id: 'confidence',
      header: 'Confiance',
      accessor: 'ai_confidence',
      width: '100px',
      render: (value, row) => (
        <StatusBadge
          variant={getConfidenceVariant(value as string)}
          size="sm"
          status={`${row.ai_confidence_score.toFixed(0)}%`}
        />
      ),
    },
    {
      id: 'issue_type',
      header: 'Problème',
      accessor: 'issue_type',
      render: (value) => <span>{getIssueTypeLabel(value as string)}</span>,
    },
    {
      id: 'reference',
      header: 'Référence',
      accessor: 'reference',
      render: (value, row) => <span>{(value as string) || row.partner_name || '-'}</span>,
    },
    {
      id: 'amount_total',
      header: 'Montant',
      accessor: 'amount_total',
      align: 'right',
      render: (value) => formatCurrency(value as number | null),
    },
    {
      id: 'suggested_account',
      header: 'Compte suggéré',
      accessor: 'suggested_account',
      render: (value) => <span>{(value as string) || '-'}</span>,
    },
    {
      id: 'document_date',
      header: 'Date',
      accessor: 'document_date',
      render: (value) => formatDate(value as string | null),
    },
  ];

  const rowActions = [
    {
      id: 'view',
      label: 'Voir',
      icon: <Eye size={16} />,
      onClick: (row: ValidationQueueItem) =>
        navigate(`/auto-accounting/documents/${row.document_id}`),
    },
    {
      id: 'validate',
      label: 'Valider',
      icon: <Check size={16} />,
      onClick: (row: ValidationQueueItem) => {
        setSelectedIds([row.id]);
        setValidationAction('VALIDATE');
      },
    },
    {
      id: 'reject',
      label: 'Rejeter',
      icon: <X size={16} />,
      variant: 'danger' as const,
      onClick: (row: ValidationQueueItem) => {
        setSelectedIds([row.id]);
        setValidationAction('REJECT');
      },
    },
  ];

  if (dashboardLoading) {
    return (
      <PageWrapper title="Validation & Supervision">
        <div className="azals-loading">
          <div className="azals-spinner" />
          <p>Chargement...</p>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title="Validation & Supervision"
      subtitle="Validez par exception, l'IA fait le reste"
      actions={
        <ButtonGroup>
          <Button
            variant="ghost"
            leftIcon={<Link2 size={16} />}
            onClick={() => navigate('/auto-accounting/reconciliation')}
          >
            Rapprochement
          </Button>
        </ButtonGroup>
      }
    >
      {/* Statistiques IA et Rapprochement */}
      {dashboard && (
        <section className="azals-section">
          <Grid columns={2}>
            <AIPerformanceWidget stats={dashboard.ai_performance} />
            <ReconciliationStatsWidget stats={dashboard.reconciliation_stats} />
          </Grid>
        </section>
      )}

      {/* File de validation */}
      <section className="azals-section">
        <Card
          title={`File de validation (${dashboard?.validation_queue_total || 0})`}
          icon={<AlertTriangle size={18} />}
          noPadding
          actions={
            <ButtonGroup>
              {selectedIds.length > 0 && (
                <>
                  <Button
                    variant="success"
                    size="sm"
                    leftIcon={<Check size={14} />}
                    onClick={() => handleBulkAction('VALIDATE')}
                  >
                    Valider ({selectedIds.length})
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    leftIcon={<X size={14} />}
                    onClick={() => handleBulkAction('REJECT')}
                  >
                    Rejeter ({selectedIds.length})
                  </Button>
                </>
              )}
              <Select
                value={confidenceFilter || ''}
                onChange={(value) => {
                  setConfidenceFilter(value || null);
                  setPage(1);
                }}
                options={[
                  { value: '', label: 'Tous niveaux' },
                  { value: 'VERY_LOW', label: 'Très basse' },
                  { value: 'LOW', label: 'Basse' },
                  { value: 'MEDIUM', label: 'Moyenne' },
                ]}
              />
            </ButtonGroup>
          }
        >
          <DataTable
            columns={columns}
            data={validationQueue?.items || dashboard?.validation_queue || []}
            keyField="id"
            isLoading={queueLoading}
            actions={rowActions}
            pagination={{
              page,
              pageSize: 20,
              total: validationQueue?.total || dashboard?.validation_queue_total || 0,
              onPageChange: setPage,
              onPageSizeChange: () => {},
            }}
            emptyMessage="Aucune écriture en attente de validation"
          />
        </Card>
      </section>

      {/* Périodes comptables */}
      {dashboard && dashboard.periods.length > 0 && (
        <section className="azals-section">
          <PeriodsWidget
            periods={dashboard.periods}
            onCertify={handleCertifyPeriod}
            isLoading={certifyPeriod.isPending}
          />
        </section>
      )}

      {/* Modal de validation */}
      {validationAction && (
        <ValidationModal
          isOpen={true}
          onClose={() => setValidationAction(null)}
          selectedItems={selectedItems}
          action={validationAction}
          onConfirm={handleConfirmValidation}
          isLoading={bulkValidate.isPending}
        />
      )}
    </PageWrapper>
  );
};

export default ExpertDashboard;
