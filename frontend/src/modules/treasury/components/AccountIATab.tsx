/**
 * AZALSCORE Module - Treasury - Account IA Tab
 * Onglet Assistant IA pour le compte bancaire
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ChevronRight, CheckCircle2,
  Link2, XCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { BankAccount } from '../types';
import {
  formatCurrency, hasNegativeBalance, hasLowBalance,
  hasUnreconciledTransactions, getProjectedBalance, isTransactionReconciled
} from '../types';

/**
 * AccountIATab - Assistant IA
 */
export const AccountIATab: React.FC<TabContentProps<BankAccount>> = ({ data: account }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(account);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  return (
    <div className="azals-std-tab-content">
      {/* En-tete IA (mode AZALSCORE) */}
      <div className="azals-std-ia-panel azals-std-azalscore-only">
        <div className="azals-std-ia-panel__header">
          <Sparkles size={24} className="azals-std-ia-panel__icon" />
          <h3 className="azals-std-ia-panel__title">Assistant AZALSCORE IA</h3>
        </div>
        <div className="azals-std-ia-panel__content">
          <p>
            J'ai analyse ce compte bancaire et identifie{' '}
            <strong>{insights.length} points d'attention</strong>.
            {insights.filter(i => i.type === 'warning').length > 0 && (
              <span className="text-warning ml-1">
                ({insights.filter(i => i.type === 'warning').length} alertes)
              </span>
            )}
          </p>
        </div>
        <div className="azals-std-ia-panel__actions">
          <Button
            variant="secondary"
            leftIcon={<RefreshCw size={16} className={isAnalyzing ? 'azals-spin' : ''} />}
            onClick={handleRefreshAnalysis}
            disabled={isAnalyzing}
          >
            Relancer l'analyse
          </Button>
        </div>
      </div>

      {/* Score du compte */}
      <Card title="Score sante financiere" icon={<TrendingUp size={18} />} className="mb-4">
        <div className="azals-score-display">
          <div className="azals-score-display__circle">
            <svg viewBox="0 0 36 36" className="azals-score-display__svg">
              <path
                className="azals-score-display__bg"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="3"
              />
              <path
                className="azals-score-display__fg"
                strokeDasharray={`${insights.filter(i => i.type !== 'warning').length * 20}, 100`}
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="var(--azals-primary-500)"
                strokeWidth="3"
                strokeLinecap="round"
              />
            </svg>
            <span className="azals-score-display__value">
              {Math.round((insights.filter(i => i.type !== 'warning').length / Math.max(insights.length, 1)) * 100)}%
            </span>
          </div>
          <div className="azals-score-display__details">
            <p>
              {insights.filter(i => i.type === 'success').length} points positifs,{' '}
              {insights.filter(i => i.type === 'warning').length} alertes,{' '}
              {insights.filter(i => i.type === 'suggestion').length} suggestions
            </p>
          </div>
        </div>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Insights */}
        <Card title="Insights IA" icon={<Lightbulb size={18} />}>
          <div className="azals-insights-list">
            {insights.map((insight) => (
              <InsightItem key={insight.id} insight={insight} />
            ))}
          </div>
        </Card>

        {/* Actions suggerees */}
        <Card title="Actions suggerees" icon={<ChevronRight size={18} />}>
          <div className="azals-suggested-actions">
            {hasUnreconciledTransactions(account) && (
              <SuggestedAction
                title="Rapprocher les transactions"
                description={`${account.unreconciled_count || 0} transaction(s) a rapprocher.`}
                confidence={95}
                icon={<Link2 size={16} />}
              />
            )}
            {hasNegativeBalance(account) && (
              <SuggestedAction
                title="Attention au decouvert"
                description="Le solde est negatif, verifiez les encaissements."
                confidence={90}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {hasLowBalance(account) && !hasNegativeBalance(account) && (
              <SuggestedAction
                title="Surveiller le solde"
                description="Le solde est bas, anticipez les decaissements."
                confidence={75}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {!account.last_sync && (
              <SuggestedAction
                title="Synchroniser le compte"
                description="Aucune synchronisation recente detectee."
                confidence={85}
                icon={<RefreshCw size={16} />}
              />
            )}
            {account.is_active && !hasNegativeBalance(account) && !hasUnreconciledTransactions(account) && (
              <SuggestedAction
                title="Compte en ordre"
                description="Ce compte est bien gere."
                confidence={100}
                icon={<ThumbsUp size={16} />}
              />
            )}
          </div>
        </Card>
      </Grid>

      {/* Analyse detaillee (ERP only) */}
      <Card
        title="Analyse detaillee"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-analysis-grid">
          <div className="azals-analysis-item">
            <h4>Solde actuel</h4>
            <p className={`text-lg font-medium ${account.balance < 0 ? 'text-red-600' : 'text-green-600'}`}>
              {formatCurrency(account.balance, account.currency)}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Solde projete</h4>
            <p className={`text-lg font-medium ${getProjectedBalance(account) < 0 ? 'text-red-600' : 'text-blue-600'}`}>
              {formatCurrency(getProjectedBalance(account), account.currency)}
            </p>
            <p className="text-sm text-muted">avec encours</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Transactions</h4>
            <p className="text-lg font-medium text-primary">
              {account.transactions_count || 0}
            </p>
            <p className="text-sm text-muted">ce mois</p>
          </div>
          <div className="azals-analysis-item">
            <h4>A rapprocher</h4>
            <p className={`text-lg font-medium ${(account.unreconciled_count || 0) > 0 ? 'text-orange-600' : 'text-green-600'}`}>
              {account.unreconciled_count || 0}
            </p>
            <p className="text-sm text-muted">transaction(s)</p>
          </div>
        </div>
      </Card>
    </div>
  );
};

/**
 * Types pour les insights
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Composant item d'insight
 */
const InsightItem: React.FC<{ insight: Insight }> = ({ insight }) => {
  const getIcon = () => {
    switch (insight.type) {
      case 'success':
        return <ThumbsUp size={16} className="text-success" />;
      case 'warning':
        return <AlertTriangle size={16} className="text-warning" />;
      case 'suggestion':
        return <Lightbulb size={16} className="text-primary" />;
    }
  };

  return (
    <div className={`azals-insight azals-insight--${insight.type}`}>
      <div className="azals-insight__icon">{getIcon()}</div>
      <div className="azals-insight__content">
        <h4 className="azals-insight__title">{insight.title}</h4>
        <p className="azals-insight__description">{insight.description}</p>
      </div>
    </div>
  );
};

/**
 * Composant action suggeree
 */
interface SuggestedActionProps {
  title: string;
  description: string;
  confidence: number;
  icon?: React.ReactNode;
}

const SuggestedAction: React.FC<SuggestedActionProps> = ({ title, description, confidence, icon }) => {
  return (
    <div className="azals-suggested-action">
      <div className="azals-suggested-action__content">
        <h4>
          {icon && <span className="mr-2">{icon}</span>}
          {title}
        </h4>
        <p className="text-muted text-sm">{description}</p>
      </div>
      <div className="azals-suggested-action__confidence">
        <span className={`azals-confidence azals-confidence--${confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low'}`}>
          {confidence}%
        </span>
      </div>
    </div>
  );
};

/**
 * Generer les insights bases sur le compte
 */
function generateInsights(account: BankAccount): Insight[] {
  const insights: Insight[] = [];

  // Statut compte
  if (account.is_active) {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Compte actif',
      description: 'Le compte bancaire est actif et operationnel.',
    });
  } else {
    insights.push({
      id: 'inactive',
      type: 'warning',
      title: 'Compte inactif',
      description: 'Ce compte est desactive.',
    });
  }

  // Solde
  if (hasNegativeBalance(account)) {
    insights.push({
      id: 'negative-balance',
      type: 'warning',
      title: 'Solde negatif',
      description: `Le compte est a decouvert (${formatCurrency(account.balance, account.currency)}).`,
    });
  } else if (hasLowBalance(account)) {
    insights.push({
      id: 'low-balance',
      type: 'suggestion',
      title: 'Solde bas',
      description: 'Le solde est inferieur au seuil recommande.',
    });
  } else {
    insights.push({
      id: 'healthy-balance',
      type: 'success',
      title: 'Solde sain',
      description: 'Le solde du compte est satisfaisant.',
    });
  }

  // Rapprochement
  if (hasUnreconciledTransactions(account)) {
    insights.push({
      id: 'unreconciled',
      type: 'suggestion',
      title: 'Rapprochement en attente',
      description: `${account.unreconciled_count || 0} transaction(s) a rapprocher.`,
    });
  } else if (account.transactions_count && account.transactions_count > 0) {
    insights.push({
      id: 'reconciled',
      type: 'success',
      title: 'Rapprochement a jour',
      description: 'Toutes les transactions sont rapprochees.',
    });
  }

  // Synchronisation
  if (account.last_sync) {
    const lastSyncDate = new Date(account.last_sync);
    const daysSinceSync = Math.floor((Date.now() - lastSyncDate.getTime()) / (1000 * 60 * 60 * 24));

    if (daysSinceSync <= 1) {
      insights.push({
        id: 'recent-sync',
        type: 'success',
        title: 'Synchronisation recente',
        description: 'Les donnees sont a jour.',
      });
    } else if (daysSinceSync > 7) {
      insights.push({
        id: 'old-sync',
        type: 'warning',
        title: 'Synchronisation ancienne',
        description: `Derniere synchronisation il y a ${daysSinceSync} jours.`,
      });
    }
  } else {
    insights.push({
      id: 'no-sync',
      type: 'suggestion',
      title: 'Pas de synchronisation',
      description: 'Connectez ce compte a votre banque.',
    });
  }

  // Compte par defaut
  if (account.is_default) {
    insights.push({
      id: 'default',
      type: 'success',
      title: 'Compte principal',
      description: 'Ce compte est defini comme compte par defaut.',
    });
  }

  // Mouvements en attente
  if ((account.pending_in || 0) > 0 || (account.pending_out || 0) > 0) {
    const pending_in = account.pending_in || 0;
    const pending_out = account.pending_out || 0;

    if (pending_in > pending_out) {
      insights.push({
        id: 'pending-positive',
        type: 'success',
        title: 'Encaissements attendus',
        description: `+${formatCurrency(pending_in - pending_out, account.currency)} net a recevoir.`,
      });
    } else if (pending_out > pending_in) {
      insights.push({
        id: 'pending-negative',
        type: 'suggestion',
        title: 'Decaissements prevus',
        description: `-${formatCurrency(pending_out - pending_in, account.currency)} net a payer.`,
      });
    }
  }

  return insights;
}

export default AccountIATab;
