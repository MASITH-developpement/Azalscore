/**
 * Reconciliation View - Comptabilité Automatisée
 *
 * Gestion du rapprochement bancaire automatique et manuel.
 *
 * PRINCIPES:
 * - Auto-rapprochement par IA (>90% confiance = auto)
 * - L'expert ne fait que valider/corriger les exceptions
 * - Création de règles pour améliorer l'auto-rapprochement
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Link2,
  Unlink,
  Check,
  X,
  Search,
  Filter,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  CreditCard,
  Building2,
  Calendar,
  Hash,
  Plus,
  RefreshCw,
  Settings,
  Eye,
  ArrowRight,
  Zap,
  Target,
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, ButtonGroup } from '@ui/actions';
import { StatusBadge } from '@ui/dashboards';
import { Modal, Input, Select, TextArea } from '@ui/forms';
import type { TableColumn } from '@/types';

// ============================================================
// TYPES
// ============================================================

interface UnreconciledTransaction {
  id: string;
  bank_account_name: string;
  transaction_date: string;
  value_date: string;
  description: string;
  amount: number;
  currency: string;
  transaction_type: 'CREDIT' | 'DEBIT';
  counterparty_name: string | null;
  counterparty_iban: string | null;
  reference: string | null;
  suggested_matches: SuggestedMatch[];
}

interface SuggestedMatch {
  document_id: string;
  document_type: string;
  reference: string | null;
  partner_name: string | null;
  amount: number;
  document_date: string | null;
  confidence_score: number;
  match_reasons: string[];
}

interface ReconciliationRule {
  id: string;
  name: string;
  pattern_type: 'EXACT' | 'CONTAINS' | 'REGEX';
  pattern_field: string;
  pattern_value: string;
  target_type: 'DOCUMENT' | 'ACCOUNT' | 'JOURNAL';
  target_value: string;
  priority: number;
  matches_count: number;
  is_active: boolean;
  created_at: string;
}

interface ReconciliationStats {
  total_transactions: number;
  reconciled: number;
  pending: number;
  auto_reconciled_rate: number;
  avg_reconciliation_time_hours: number;
  rules_count: number;
}

interface ReconciliationHistory {
  id: string;
  transaction_id: string;
  document_id: string | null;
  reconciliation_type: 'AUTO' | 'MANUAL' | 'RULE';
  confidence_score: number | null;
  reconciled_by: string | null;
  reconciled_at: string;
  notes: string | null;
}

interface ReconciliationViewData {
  stats: ReconciliationStats;
  unreconciled_transactions: UnreconciledTransaction[];
  recent_reconciliations: ReconciliationHistory[];
  rules: ReconciliationRule[];
}

// ============================================================
// API HOOKS
// ============================================================

const useReconciliationData = () => {
  return useQuery({
    queryKey: ['accounting', 'reconciliation'],
    queryFn: async () => {
      const response = await api.get<ReconciliationViewData>(
        '/accounting/reconciliation'
      );
      return response.data;
    },
    staleTime: 30000,
  });
};

const useAutoReconcile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await api.post('/accounting/reconciliation/auto');
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

const useManualReconcile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      transactionId,
      documentId,
      notes,
    }: {
      transactionId: string;
      documentId: string;
      notes?: string;
    }) => {
      const response = await api.post('/accounting/reconciliation/manual', {
        transaction_id: transactionId,
        document_id: documentId,
        notes,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

const useCreateRule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (rule: Omit<ReconciliationRule, 'id' | 'matches_count' | 'created_at'>) => {
      const response = await api.post('/accounting/reconciliation/rules', rule);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

const useDeleteRule = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ ruleId }: { ruleId: string }) => {
      const response = await api.delete(
        `/accounting/reconciliation/rules/${ruleId}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

const useUnreconcile = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ transactionId }: { transactionId: string }) => {
      const response = await api.post(
        `/accounting/reconciliation/unreconcile/${transactionId}`
      );
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

const formatCurrency = (value: number, currency = 'EUR') =>
  new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
  }).format(value);

const formatDate = (dateStr: string | null) =>
  dateStr ? new Date(dateStr).toLocaleDateString('fr-FR') : '-';

const formatDateTime = (dateStr: string) =>
  new Date(dateStr).toLocaleString('fr-FR');

const formatPercent = (value: number) =>
  new Intl.NumberFormat('fr-FR', {
    style: 'percent',
    minimumFractionDigits: 1,
  }).format(value / 100);

const getConfidenceVariant = (
  score: number
): 'success' | 'warning' | 'danger' => {
  if (score >= 90) return 'success';
  if (score >= 70) return 'warning';
  return 'danger';
};

const getTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    INVOICE_RECEIVED: 'Facture fournisseur',
    INVOICE_SENT: 'Facture client',
    EXPENSE_NOTE: 'Note de frais',
    CREDIT_NOTE_RECEIVED: 'Avoir reçu',
    CREDIT_NOTE_SENT: 'Avoir émis',
  };
  return labels[type] || type;
};

// ============================================================
// SUB-COMPONENTS
// ============================================================

const StatsCards: React.FC<{ stats: ReconciliationStats }> = ({ stats }) => {
  return (
    <div className="azals-auto-accounting__reconciliation-stats">
      <div className="azals-auto-accounting__stat-card">
        <div className="azals-auto-accounting__stat-icon azals-bg--success">
          <CheckCircle size={20} />
        </div>
        <div className="azals-auto-accounting__stat-content">
          <span className="azals-auto-accounting__stat-value">
            {stats.reconciled}
          </span>
          <span className="azals-auto-accounting__stat-label">Rapprochés</span>
        </div>
      </div>

      <div className="azals-auto-accounting__stat-card">
        <div className="azals-auto-accounting__stat-icon azals-bg--warning">
          <Clock size={20} />
        </div>
        <div className="azals-auto-accounting__stat-content">
          <span className="azals-auto-accounting__stat-value">
            {stats.pending}
          </span>
          <span className="azals-auto-accounting__stat-label">En attente</span>
        </div>
      </div>

      <div className="azals-auto-accounting__stat-card">
        <div className="azals-auto-accounting__stat-icon azals-bg--info">
          <Target size={20} />
        </div>
        <div className="azals-auto-accounting__stat-content">
          <span className="azals-auto-accounting__stat-value">
            {formatPercent(stats.auto_reconciled_rate)}
          </span>
          <span className="azals-auto-accounting__stat-label">Taux auto</span>
        </div>
      </div>

      <div className="azals-auto-accounting__stat-card">
        <div className="azals-auto-accounting__stat-icon azals-bg--default">
          <Settings size={20} />
        </div>
        <div className="azals-auto-accounting__stat-content">
          <span className="azals-auto-accounting__stat-value">
            {stats.rules_count}
          </span>
          <span className="azals-auto-accounting__stat-label">Règles</span>
        </div>
      </div>
    </div>
  );
};

const TransactionCard: React.FC<{
  transaction: UnreconciledTransaction;
  onReconcile: (documentId: string) => void;
  onViewDocument: (documentId: string) => void;
}> = ({ transaction, onReconcile, onViewDocument }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="azals-auto-accounting__transaction-card">
      <div
        className="azals-auto-accounting__transaction-header"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="azals-auto-accounting__transaction-main">
          <div
            className={`azals-auto-accounting__transaction-amount ${
              transaction.transaction_type === 'CREDIT'
                ? 'azals-text--success'
                : 'azals-text--danger'
            }`}
          >
            {transaction.transaction_type === 'CREDIT' ? '+' : '-'}
            {formatCurrency(Math.abs(transaction.amount), transaction.currency)}
          </div>
          <div className="azals-auto-accounting__transaction-info">
            <span className="azals-auto-accounting__transaction-desc">
              {transaction.description}
            </span>
            <span className="azals-auto-accounting__transaction-meta">
              <CreditCard size={12} />
              {transaction.bank_account_name}
              <Calendar size={12} />
              {formatDate(transaction.transaction_date)}
              {transaction.counterparty_name && (
                <>
                  <Building2 size={12} />
                  {transaction.counterparty_name}
                </>
              )}
            </span>
          </div>
        </div>

        <div className="azals-auto-accounting__transaction-actions">
          {transaction.suggested_matches.length > 0 && (
            <StatusBadge variant="info" size="sm" status={`${transaction.suggested_matches.length} suggestion(s)`} />
          )}
          <Button variant="ghost" size="sm">
            {expanded ? 'Masquer' : 'Voir suggestions'}
          </Button>
        </div>
      </div>

      {expanded && (
        <div className="azals-auto-accounting__transaction-matches">
          {transaction.suggested_matches.length > 0 ? (
            transaction.suggested_matches.map((match) => (
              <div
                key={match.document_id}
                className="azals-auto-accounting__match-card"
              >
                <div className="azals-auto-accounting__match-info">
                  <div className="azals-auto-accounting__match-header">
                    <FileText size={16} />
                    <span className="azals-auto-accounting__match-type">
                      {getTypeLabel(match.document_type)}
                    </span>
                    <StatusBadge
                      variant={getConfidenceVariant(match.confidence_score)}
                      size="sm"
                      status={`${match.confidence_score.toFixed(0)}%`}
                    />
                  </div>

                  <div className="azals-auto-accounting__match-details">
                    {match.reference && (
                      <span>
                        <Hash size={12} />
                        {match.reference}
                      </span>
                    )}
                    {match.partner_name && (
                      <span>
                        <Building2 size={12} />
                        {match.partner_name}
                      </span>
                    )}
                    <span>
                      <CreditCard size={12} />
                      {formatCurrency(match.amount)}
                    </span>
                  </div>

                  <div className="azals-auto-accounting__match-reasons">
                    {match.match_reasons.map((reason, idx) => (
                      <span key={idx} className="azals-auto-accounting__match-reason">
                        <Check size={12} />
                        {reason}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="azals-auto-accounting__match-actions">
                  <Button
                    variant="ghost"
                    size="sm"
                    leftIcon={<Eye size={14} />}
                    onClick={() => onViewDocument(match.document_id)}
                  >
                    Voir
                  </Button>
                  <Button
                    variant="success"
                    size="sm"
                    leftIcon={<Link2 size={14} />}
                    onClick={() => onReconcile(match.document_id)}
                  >
                    Rapprocher
                  </Button>
                </div>
              </div>
            ))
          ) : (
            <div className="azals-auto-accounting__no-matches">
              <AlertTriangle size={20} />
              <p>Aucune correspondance trouvée automatiquement</p>
              <Button variant="ghost" size="sm">
                Rechercher manuellement
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const RulesWidget: React.FC<{
  rules: ReconciliationRule[];
  onDelete: (ruleId: string) => void;
  onAdd: () => void;
}> = ({ rules, onDelete, onAdd }) => {
  const getPatternTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      EXACT: 'Exact',
      CONTAINS: 'Contient',
      REGEX: 'Regex',
    };
    return labels[type] || type;
  };

  const getFieldLabel = (field: string): string => {
    const labels: Record<string, string> = {
      description: 'Description',
      counterparty_name: 'Contrepartie',
      reference: 'Référence',
      amount: 'Montant',
    };
    return labels[field] || field;
  };

  return (
    <Card
      title="Règles de rapprochement"
      icon={<Settings size={18} />}
      actions={
        <Button variant="ghost" size="sm" leftIcon={<Plus size={14} />} onClick={onAdd}>
          Ajouter
        </Button>
      }
    >
      {rules.length > 0 ? (
        <div className="azals-auto-accounting__rules-list">
          {rules.map((rule) => (
            <div key={rule.id} className="azals-auto-accounting__rule-item">
              <div className="azals-auto-accounting__rule-info">
                <span className="azals-auto-accounting__rule-name">
                  {rule.name}
                </span>
                <span className="azals-auto-accounting__rule-pattern">
                  {getFieldLabel(rule.pattern_field)}{' '}
                  {getPatternTypeLabel(rule.pattern_type).toLowerCase()}{' '}
                  <code>{rule.pattern_value}</code>
                </span>
              </div>

              <div className="azals-auto-accounting__rule-stats">
                <span className="azals-auto-accounting__rule-matches">
                  {rule.matches_count} correspondance(s)
                </span>
                <StatusBadge
                  variant={rule.is_active ? 'success' : 'default'}
                  size="sm"
                  status={rule.is_active ? 'Active' : 'Inactive'}
                />
              </div>

              <Button
                variant="ghost"
                size="sm"
                leftIcon={<X size={14} />}
                onClick={() => onDelete(rule.id)}
              >

              </Button>
            </div>
          ))}
        </div>
      ) : (
        <div className="azals-empty-state azals-empty-state--small">
          <p>Aucune règle configurée</p>
          <p className="azals-text--muted">
            Les règles permettent d'améliorer le rapprochement automatique
          </p>
        </div>
      )}
    </Card>
  );
};

// ============================================================
// MODALS
// ============================================================

const AddRuleModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onCreate: (rule: Omit<ReconciliationRule, 'id' | 'matches_count' | 'created_at'>) => void;
  isLoading: boolean;
}> = ({ isOpen, onClose, onCreate, isLoading }) => {
  const [name, setName] = useState('');
  const [patternType, setPatternType] = useState<'EXACT' | 'CONTAINS' | 'REGEX'>('CONTAINS');
  const [patternField, setPatternField] = useState('description');
  const [patternValue, setPatternValue] = useState('');
  const [targetType, setTargetType] = useState<'DOCUMENT' | 'ACCOUNT' | 'JOURNAL'>('ACCOUNT');
  const [targetValue, setTargetValue] = useState('');
  const [priority, setPriority] = useState(10);

  const handleCreate = () => {
    onCreate({
      name,
      pattern_type: patternType,
      pattern_field: patternField,
      pattern_value: patternValue,
      target_type: targetType,
      target_value: targetValue,
      priority,
      is_active: true,
    });
  };

  const isValid =
    name.trim() !== '' &&
    patternValue.trim() !== '' &&
    targetValue.trim() !== '';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Créer une règle" size="lg">
      <div className="azals-auto-accounting__rule-form">
        <div className="azals-form-group">
          <label className="azals-form-label">Nom de la règle</label>
          <Input
            value={name}
            onChange={(value) => setName(value)}
            placeholder="Ex: Loyer mensuel, Abonnement téléphone..."
          />
        </div>

        <div className="azals-form-row">
          <div className="azals-form-group">
            <label className="azals-form-label">Champ à analyser</label>
            <Select
              value={patternField}
              onChange={(value) => setPatternField(value)}
              options={[
                { value: 'description', label: 'Description' },
                { value: 'counterparty_name', label: 'Contrepartie' },
                { value: 'reference', label: 'Référence' },
              ]}
            />
          </div>

          <div className="azals-form-group">
            <label className="azals-form-label">Type de correspondance</label>
            <Select
              value={patternType}
              onChange={(value) => setPatternType(value as 'EXACT' | 'CONTAINS' | 'REGEX')}
              options={[
                { value: 'CONTAINS', label: 'Contient' },
                { value: 'EXACT', label: 'Exact' },
                { value: 'REGEX', label: 'Expression régulière' },
              ]}
            />
          </div>
        </div>

        <div className="azals-form-group">
          <label className="azals-form-label">Valeur à rechercher</label>
          <Input
            value={patternValue}
            onChange={(value) => setPatternValue(value)}
            placeholder={
              patternType === 'REGEX'
                ? 'Ex: LOYER.*\\d{2}/\\d{4}'
                : 'Ex: LOYER, ORANGE, ...'
            }
          />
        </div>

        <div className="azals-form-row">
          <div className="azals-form-group">
            <label className="azals-form-label">Action</label>
            <Select
              value={targetType}
              onChange={(value) => setTargetType(value as 'DOCUMENT' | 'ACCOUNT' | 'JOURNAL')}
              options={[
                { value: 'ACCOUNT', label: 'Affecter au compte' },
                { value: 'JOURNAL', label: 'Affecter au journal' },
                { value: 'DOCUMENT', label: 'Lier au document' },
              ]}
            />
          </div>

          <div className="azals-form-group">
            <label className="azals-form-label">
              {targetType === 'ACCOUNT'
                ? 'Code compte'
                : targetType === 'JOURNAL'
                ? 'Code journal'
                : 'ID document'}
            </label>
            <Input
              value={targetValue}
              onChange={(value) => setTargetValue(value)}
              placeholder={
                targetType === 'ACCOUNT'
                  ? '613200'
                  : targetType === 'JOURNAL'
                  ? 'ACH'
                  : 'doc_xxx'
              }
            />
          </div>
        </div>

        <div className="azals-form-group">
          <label className="azals-form-label">Priorité (1-100)</label>
          <Input
            type="number"
            value={String(priority)}
            onChange={(value) => setPriority(parseInt(value) || 10)}
            min={1}
            max={100}
          />
          <span className="azals-form-hint">
            Les règles avec une priorité plus élevée sont appliquées en premier
          </span>
        </div>

        <div className="azals-modal__actions">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button onClick={handleCreate} disabled={!isValid || isLoading}>
            {isLoading ? 'Création...' : 'Créer la règle'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

const ReconcileModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  transaction: UnreconciledTransaction | null;
  documentId: string | null;
  onConfirm: (notes: string) => void;
  isLoading: boolean;
}> = ({ isOpen, onClose, transaction, documentId, onConfirm, isLoading }) => {
  const [notes, setNotes] = useState('');

  if (!transaction || !documentId) return null;

  const match = transaction.suggested_matches.find(
    (m) => m.document_id === documentId
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirmer le rapprochement">
      <div className="azals-auto-accounting__reconcile-modal">
        <div className="azals-auto-accounting__reconcile-preview">
          <div className="azals-auto-accounting__reconcile-side">
            <span className="azals-auto-accounting__reconcile-label">
              Transaction bancaire
            </span>
            <div className="azals-auto-accounting__reconcile-item">
              <CreditCard size={16} />
              <span>{transaction.description}</span>
              <strong
                className={
                  transaction.transaction_type === 'CREDIT'
                    ? 'azals-text--success'
                    : 'azals-text--danger'
                }
              >
                {formatCurrency(transaction.amount, transaction.currency)}
              </strong>
            </div>
          </div>

          <ArrowRight size={24} className="azals-auto-accounting__reconcile-arrow" />

          <div className="azals-auto-accounting__reconcile-side">
            <span className="azals-auto-accounting__reconcile-label">
              Document comptable
            </span>
            <div className="azals-auto-accounting__reconcile-item">
              <FileText size={16} />
              <span>
                {match?.reference || match?.partner_name || 'Document'}
              </span>
              <strong>{match && formatCurrency(match.amount)}</strong>
            </div>
          </div>
        </div>

        {match && Math.abs(transaction.amount) !== match.amount && (
          <div className="azals-auto-accounting__reconcile-warning">
            <AlertTriangle size={16} />
            <span>
              Écart de montant:{' '}
              {formatCurrency(
                Math.abs(Math.abs(transaction.amount) - match.amount)
              )}
            </span>
          </div>
        )}

        <div className="azals-form-group">
          <label className="azals-form-label">Notes (optionnel)</label>
          <TextArea
            value={notes}
            onChange={(value) => setNotes(value)}
            placeholder="Commentaire sur ce rapprochement..."
            rows={2}
          />
        </div>

        <div className="azals-modal__actions">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button
            variant="success"
            leftIcon={<Link2 size={16} />}
            onClick={() => onConfirm(notes)}
            disabled={isLoading}
          >
            {isLoading ? 'Rapprochement...' : 'Confirmer'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

export const ReconciliationView: React.FC = () => {
  const navigate = useNavigate();

  const [showAddRuleModal, setShowAddRuleModal] = useState(false);
  const [reconcileTarget, setReconcileTarget] = useState<{
    transaction: UnreconciledTransaction;
    documentId: string;
  } | null>(null);
  const [filter, setFilter] = useState<'all' | 'with_suggestions' | 'no_suggestions'>('all');

  const { data, isLoading } = useReconciliationData();
  const autoReconcile = useAutoReconcile();
  const manualReconcile = useManualReconcile();
  const createRule = useCreateRule();
  const deleteRule = useDeleteRule();

  const handleAutoReconcile = async () => {
    try {
      await autoReconcile.mutateAsync();
    } catch (error) {
      console.error('Auto reconcile failed:', error);
    }
  };

  const handleManualReconcile = async (notes: string) => {
    if (!reconcileTarget) return;

    try {
      await manualReconcile.mutateAsync({
        transactionId: reconcileTarget.transaction.id,
        documentId: reconcileTarget.documentId,
        notes: notes || undefined,
      });
      setReconcileTarget(null);
    } catch (error) {
      console.error('Manual reconcile failed:', error);
    }
  };

  const handleCreateRule = async (
    rule: Omit<ReconciliationRule, 'id' | 'matches_count' | 'created_at'>
  ) => {
    try {
      await createRule.mutateAsync(rule);
      setShowAddRuleModal(false);
    } catch (error) {
      console.error('Create rule failed:', error);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    try {
      await deleteRule.mutateAsync({ ruleId });
    } catch (error) {
      console.error('Delete rule failed:', error);
    }
  };

  const filteredTransactions = data?.unreconciled_transactions.filter((t) => {
    if (filter === 'with_suggestions') return t.suggested_matches.length > 0;
    if (filter === 'no_suggestions') return t.suggested_matches.length === 0;
    return true;
  });

  if (isLoading) {
    return (
      <PageWrapper title="Rapprochement bancaire">
        <div className="azals-loading">
          <div className="azals-spinner" />
          <p>Chargement...</p>
        </div>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title="Rapprochement bancaire"
      subtitle="Associez vos transactions bancaires à vos documents comptables"
      actions={
        <ButtonGroup>
          <Button
            variant="primary"
            leftIcon={<Zap size={16} />}
            onClick={handleAutoReconcile}
            disabled={autoReconcile.isPending}
          >
            {autoReconcile.isPending
              ? 'Rapprochement...'
              : 'Auto-rapprochement'}
          </Button>
        </ButtonGroup>
      }
    >
      {/* Statistiques */}
      {data && (
        <section className="azals-section">
          <StatsCards stats={data.stats} />
        </section>
      )}

      {/* Transactions non rapprochées */}
      <section className="azals-section">
        <Card
          title={`Transactions en attente (${filteredTransactions?.length || 0})`}
          icon={<Clock size={18} />}
          actions={
            <Select
              value={filter}
              onChange={(value) => setFilter(value as typeof filter)}
              options={[
                { value: 'all', label: 'Toutes' },
                { value: 'with_suggestions', label: 'Avec suggestions' },
                { value: 'no_suggestions', label: 'Sans suggestion' },
              ]}
            />
          }
        >
          {filteredTransactions && filteredTransactions.length > 0 ? (
            <div className="azals-auto-accounting__transactions-list">
              {filteredTransactions.map((transaction) => (
                <TransactionCard
                  key={transaction.id}
                  transaction={transaction}
                  onReconcile={(documentId) =>
                    setReconcileTarget({ transaction, documentId })
                  }
                  onViewDocument={(documentId) =>
                    navigate(`/auto-accounting/documents/${documentId}`)
                  }
                />
              ))}
            </div>
          ) : (
            <div className="azals-empty-state">
              <CheckCircle size={48} className="azals-text--success" />
              <h3>Tout est rapproché</h3>
              <p>Aucune transaction en attente de rapprochement</p>
            </div>
          )}
        </Card>
      </section>

      {/* Règles de rapprochement */}
      {data && (
        <section className="azals-section">
          <RulesWidget
            rules={data.rules}
            onDelete={handleDeleteRule}
            onAdd={() => setShowAddRuleModal(true)}
          />
        </section>
      )}

      {/* Modal création règle */}
      {showAddRuleModal && (
        <AddRuleModal
          isOpen={true}
          onClose={() => setShowAddRuleModal(false)}
          onCreate={handleCreateRule}
          isLoading={createRule.isPending}
        />
      )}

      {/* Modal rapprochement manuel */}
      {reconcileTarget && (
        <ReconcileModal
          isOpen={true}
          onClose={() => setReconcileTarget(null)}
          transaction={reconcileTarget.transaction}
          documentId={reconcileTarget.documentId}
          onConfirm={handleManualReconcile}
          isLoading={manualReconcile.isPending}
        />
      )}
    </PageWrapper>
  );
};

export default ReconciliationView;
