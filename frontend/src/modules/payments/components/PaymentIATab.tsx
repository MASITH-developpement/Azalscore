/**
 * AZALSCORE Module - Payments - Payment IA Tab
 * Onglet Assistant IA pour le paiement
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, RefreshCw, Shield, RotateCcw, Clock } from 'lucide-react';
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
  getPaymentAgeDays,
  isPaymentPending, isPaymentCompleted, isPaymentFailed,
  canRefund, canRetry, hasPartialRefund, hasFullRefund,
  getRefundTotal, getNetAmount,
  PAYMENT_STATUS_CONFIG
} from '../types';
import type { Payment } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * PaymentIATab - Assistant IA
 */
export const PaymentIATab: React.FC<TabContentProps<Payment>> = ({ data: payment }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(payment);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(payment);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const healthScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce paiement et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de santé - Composant partagé */}
      <Card title="Santé du paiement" icon={<TrendingUp size={18} />} className="mb-4">
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

      {/* Analyse détaillée (ERP only) */}
      <Card
        title="Analyse détaillée"
        icon={<TrendingUp size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-analysis-grid">
          <div className="azals-analysis-item">
            <h4>Statut</h4>
            <p className={`text-lg font-medium text-${PAYMENT_STATUS_CONFIG[payment.status].color}`}>
              {PAYMENT_STATUS_CONFIG[payment.status].label}
            </p>
            <p className="text-sm text-muted">
              {PAYMENT_STATUS_CONFIG[payment.status].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Montant net</h4>
            <p className="text-lg font-medium text-primary">
              {formatCurrency(getNetAmount(payment), payment.currency)}
            </p>
            <p className="text-sm text-muted">
              Après remboursements
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Âge</h4>
            <p className="text-lg font-medium text-primary">
              {getPaymentAgeDays(payment)}j
            </p>
            <p className="text-sm text-muted">
              Depuis la création
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Remboursements</h4>
            <p className="text-lg font-medium">
              {formatCurrency(getRefundTotal(payment), payment.currency)}
            </p>
            <p className="text-sm text-muted">
              Total remboursé
            </p>
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
 * Générer les actions suggérées basées sur le paiement
 */
function generateSuggestedActions(payment: Payment): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isPaymentFailed(payment) && canRetry(payment)) {
    actions.push({
      id: 'retry',
      title: 'Relancer le paiement',
      description: 'Tentez de nouveau le paiement après correction.',
      confidence: 95,
      icon: <RefreshCw size={16} />,
      actionLabel: 'Relancer',
    });
  }

  if (isPaymentCompleted(payment) && !payment.invoice_id) {
    actions.push({
      id: 'link-invoice',
      title: 'Associer une facture',
      description: 'Liez ce paiement à une facture pour la comptabilité.',
      confidence: 90,
      icon: <Shield size={16} />,
      actionLabel: 'Associer',
    });
  }

  if (hasPartialRefund(payment)) {
    actions.push({
      id: 'check-balance',
      title: 'Vérifier le solde',
      description: 'Remboursement partiel détecté, vérifier le montant restant.',
      confidence: 85,
      icon: <RotateCcw size={16} />,
      actionLabel: 'Vérifier',
    });
  }

  if (isPaymentPending(payment) && getPaymentAgeDays(payment) > 1) {
    actions.push({
      id: 'pending-alert',
      title: 'Paiement en attente',
      description: 'Ce paiement est en attente depuis plus de 24h.',
      confidence: 80,
      icon: <Clock size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (canRefund(payment) && !hasFullRefund(payment)) {
    actions.push({
      id: 'refund-possible',
      title: 'Remboursement possible',
      description: 'Ce paiement peut être remboursé si nécessaire.',
      confidence: 75,
      icon: <RotateCcw size={16} />,
      actionLabel: 'Rembourser',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le paiement
 */
function generateInsights(payment: Payment): Insight[] {
  const insights: Insight[] = [];

  // Statut du paiement
  if (isPaymentCompleted(payment)) {
    insights.push({
      id: 'completed',
      type: 'success',
      title: 'Paiement réussi',
      description: 'Le paiement a été effectué avec succès.',
    });
  } else if (isPaymentFailed(payment)) {
    insights.push({
      id: 'failed',
      type: 'warning',
      title: 'Paiement échoué',
      description: payment.error_message || "Le paiement n'a pas abouti.",
    });
  } else if (isPaymentPending(payment)) {
    insights.push({
      id: 'pending',
      type: 'suggestion',
      title: 'En attente',
      description: 'Le paiement est en cours de traitement.',
    });
  }

  // Remboursements
  if (hasFullRefund(payment)) {
    insights.push({
      id: 'full-refund',
      type: 'warning',
      title: 'Intégralement remboursé',
      description: 'Ce paiement a été entièrement remboursé.',
    });
  } else if (hasPartialRefund(payment)) {
    insights.push({
      id: 'partial-refund',
      type: 'suggestion',
      title: 'Remboursement partiel',
      description: `${formatCurrency(getRefundTotal(payment), payment.currency)} remboursé.`,
    });
  }

  // Facture
  if (payment.invoice_id) {
    insights.push({
      id: 'invoice-linked',
      type: 'success',
      title: 'Facture liée',
      description: `Associé à la facture ${payment.invoice_number || payment.invoice_id}.`,
    });
  } else if (isPaymentCompleted(payment)) {
    insights.push({
      id: 'no-invoice',
      type: 'suggestion',
      title: 'Sans facture',
      description: 'Paiement sans facture associée.',
    });
  }

  // Client
  if (payment.customer_name) {
    insights.push({
      id: 'customer',
      type: 'success',
      title: 'Client identifié',
      description: `Paiement de ${payment.customer_name}.`,
    });
  }

  // Âge du paiement en attente
  const ageDays = getPaymentAgeDays(payment);
  if (isPaymentPending(payment) && ageDays > 1) {
    insights.push({
      id: 'old-pending',
      type: 'warning',
      title: 'Attente prolongée',
      description: `En attente depuis ${ageDays} jour(s).`,
    });
  }

  // Méthode de paiement sécurisée
  if (payment.method === 'CARD' && payment.metadata?.['3ds_authenticated']) {
    insights.push({
      id: '3ds',
      type: 'success',
      title: '3D Secure',
      description: 'Authentification 3D Secure validée.',
    });
  }

  return insights;
}

export default PaymentIATab;
