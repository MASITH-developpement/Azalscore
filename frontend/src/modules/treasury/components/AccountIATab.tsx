/**
 * AZALSCORE Module - Treasury - Account IA Tab
 * Onglet Assistant IA pour le compte bancaire
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, AlertTriangle, RefreshCw, ThumbsUp, Link2 } from 'lucide-react';
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';
import { Card, Grid } from '@ui/layout';
import { formatCurrency } from '@/utils/formatters';
import {
  hasNegativeBalance, hasLowBalance,
  hasUnreconciledTransactions, getProjectedBalance
} from '../types';
import type { BankAccount } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * AccountIATab - Assistant IA
 */
export const AccountIATab: React.FC<TabContentProps<BankAccount>> = ({ data: account }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(account);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(account);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const healthScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce compte bancaire et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score santé financière - Composant partagé */}
      <Card title="Score santé financière" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={healthScore}
          label="Santé"
          details={`${positiveCount} points positifs, ${warningCount} alertes, ${suggestionCount} suggestions`}
        />
      </Card>

      <Grid cols={2} gap="lg">
        {/* Insights - Composant partagé */}
        <Card title="Insights IA">
          <InsightList insights={sharedInsights} />
        </Card>

        {/* Actions suggérées - Composant partagé */}
        <Card title="Actions suggérées">
          <SuggestedActionList
            actions={suggestedActions}
            emptyMessage="Aucune action suggérée pour le moment"
          />
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur le compte
 */
function generateSuggestedActions(account: BankAccount): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (hasUnreconciledTransactions(account)) {
    actions.push({
      id: 'reconcile',
      title: 'Rapprocher les transactions',
      description: `${account.unreconciled_count || 0} transaction(s) à rapprocher.`,
      confidence: 95,
      icon: <Link2 size={16} />,
      actionLabel: 'Rapprocher',
    });
  }

  if (hasNegativeBalance(account)) {
    actions.push({
      id: 'overdraft',
      title: 'Attention au découvert',
      description: 'Le solde est négatif, vérifiez les encaissements.',
      confidence: 90,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (hasLowBalance(account) && !hasNegativeBalance(account)) {
    actions.push({
      id: 'low-balance',
      title: 'Surveiller le solde',
      description: 'Le solde est bas, anticipez les décaissements.',
      confidence: 75,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (!account.last_sync) {
    actions.push({
      id: 'sync',
      title: 'Synchroniser le compte',
      description: 'Aucune synchronisation récente détectée.',
      confidence: 85,
      icon: <RefreshCw size={16} />,
      actionLabel: 'Synchroniser',
    });
  }

  if (account.is_active && !hasNegativeBalance(account) && !hasUnreconciledTransactions(account)) {
    actions.push({
      id: 'ok',
      title: 'Compte en ordre',
      description: 'Ce compte est bien géré.',
      confidence: 100,
      icon: <ThumbsUp size={16} />,
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le compte
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
