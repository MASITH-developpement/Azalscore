/**
 * AZALSCORE Module - Payments - Payment IA Tab
 * Onglet Assistant IA pour le paiement
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ThumbsDown, ChevronRight,
  CheckCircle, XCircle, RotateCcw, Clock, Shield
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Payment } from '../types';
import {
  formatCurrency, getPaymentAgeDays,
  isPaymentPending, isPaymentCompleted, isPaymentFailed,
  canRefund, canRetry, hasPartialRefund, hasFullRefund,
  getRefundTotal, getNetAmount,
  PAYMENT_STATUS_CONFIG
} from '../types';

/**
 * PaymentIATab - Assistant IA
 */
export const PaymentIATab: React.FC<TabContentProps<Payment>> = ({ data: payment }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Generer les insights
  const insights = generateInsights(payment);

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
            J'ai analyse ce paiement et identifie{' '}
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

      {/* Score de sante */}
      <Card title="Sante du paiement" icon={<TrendingUp size={18} />} className="mb-4">
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
                strokeDasharray={`${insights.filter(i => i.type !== 'warning').length * 25}, 100`}
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
            {isPaymentFailed(payment) && canRetry(payment) && (
              <SuggestedAction
                title="Relancer le paiement"
                description="Tentez de nouveau le paiement apres correction."
                confidence={95}
                icon={<RefreshCw size={16} />}
              />
            )}
            {isPaymentCompleted(payment) && !payment.invoice_id && (
              <SuggestedAction
                title="Associer une facture"
                description="Liez ce paiement a une facture pour la comptabilite."
                confidence={90}
                icon={<Shield size={16} />}
              />
            )}
            {hasPartialRefund(payment) && (
              <SuggestedAction
                title="Verifier le solde"
                description="Remboursement partiel detecte, verifier le montant restant."
                confidence={85}
                icon={<RotateCcw size={16} />}
              />
            )}
            {isPaymentPending(payment) && getPaymentAgeDays(payment) > 1 && (
              <SuggestedAction
                title="Paiement en attente"
                description="Ce paiement est en attente depuis plus de 24h."
                confidence={80}
                icon={<Clock size={16} />}
              />
            )}
            {canRefund(payment) && !hasFullRefund(payment) && (
              <SuggestedAction
                title="Remboursement possible"
                description="Ce paiement peut etre rembourse si necessaire."
                confidence={75}
                icon={<RotateCcw size={16} />}
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
              Apres remboursements
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Age</h4>
            <p className="text-lg font-medium text-primary">
              {getPaymentAgeDays(payment)}j
            </p>
            <p className="text-sm text-muted">
              Depuis la creation
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Remboursements</h4>
            <p className="text-lg font-medium">
              {formatCurrency(getRefundTotal(payment), payment.currency)}
            </p>
            <p className="text-sm text-muted">
              Total rembourse
            </p>
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
 * Generer les insights bases sur le paiement
 */
function generateInsights(payment: Payment): Insight[] {
  const insights: Insight[] = [];

  // Statut du paiement
  if (isPaymentCompleted(payment)) {
    insights.push({
      id: 'completed',
      type: 'success',
      title: 'Paiement reussi',
      description: 'Le paiement a ete effectue avec succes.',
    });
  } else if (isPaymentFailed(payment)) {
    insights.push({
      id: 'failed',
      type: 'warning',
      title: 'Paiement echoue',
      description: payment.error_message || 'Le paiement n\'a pas abouti.',
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
      title: 'Integralement rembourse',
      description: 'Ce paiement a ete entierement rembourse.',
    });
  } else if (hasPartialRefund(payment)) {
    insights.push({
      id: 'partial-refund',
      type: 'suggestion',
      title: 'Remboursement partiel',
      description: `${formatCurrency(getRefundTotal(payment), payment.currency)} rembourse.`,
    });
  }

  // Facture
  if (payment.invoice_id) {
    insights.push({
      id: 'invoice-linked',
      type: 'success',
      title: 'Facture liee',
      description: `Associe a la facture ${payment.invoice_number || payment.invoice_id}.`,
    });
  } else if (isPaymentCompleted(payment)) {
    insights.push({
      id: 'no-invoice',
      type: 'suggestion',
      title: 'Sans facture',
      description: 'Paiement sans facture associee.',
    });
  }

  // Client
  if (payment.customer_name) {
    insights.push({
      id: 'customer',
      type: 'success',
      title: 'Client identifie',
      description: `Paiement de ${payment.customer_name}.`,
    });
  }

  // Age du paiement en attente
  const ageDays = getPaymentAgeDays(payment);
  if (isPaymentPending(payment) && ageDays > 1) {
    insights.push({
      id: 'old-pending',
      type: 'warning',
      title: 'Attente prolongee',
      description: `En attente depuis ${ageDays} jour(s).`,
    });
  }

  // Methode de paiement securisee
  if (payment.method === 'CARD' && payment.metadata?.['3ds_authenticated']) {
    insights.push({
      id: '3ds',
      type: 'success',
      title: '3D Secure',
      description: 'Authentification 3D Secure validee.',
    });
  }

  return insights;
}

export default PaymentIATab;
