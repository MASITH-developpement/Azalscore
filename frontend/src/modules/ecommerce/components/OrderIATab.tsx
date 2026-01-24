/**
 * AZALSCORE Module - E-commerce - Order IA Tab
 * Onglet Assistant IA pour la commande
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ChevronRight, Truck, CreditCard, XCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Order } from '../types';
import {
  canShipOrder, canCancelOrder, canRefundOrder,
  formatCurrency, getNextOrderStatus, ORDER_STATUS_CONFIG
} from '../types';

/**
 * OrderIATab - Assistant IA
 */
export const OrderIATab: React.FC<TabContentProps<Order>> = ({ data: order }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(order);

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
            J'ai analyse cette commande et identifie{' '}
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

      {/* Score de la commande */}
      <Card title="Score de traitement" icon={<TrendingUp size={18} />} className="mb-4">
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
            {canShipOrder(order) && (
              <SuggestedAction
                title="Expedier la commande"
                description="La commande est prete a etre expediee."
                confidence={95}
                icon={<Truck size={16} />}
              />
            )}
            {order.payment_status === 'PENDING' && (
              <SuggestedAction
                title="Relancer le paiement"
                description="Le paiement est en attente."
                confidence={85}
                icon={<CreditCard size={16} />}
              />
            )}
            {getNextOrderStatus(order.status) && (
              <SuggestedAction
                title={`Passer en "${ORDER_STATUS_CONFIG[getNextOrderStatus(order.status)!].label}"`}
                description="Prochaine etape du workflow."
                confidence={90}
                icon={<ChevronRight size={16} />}
              />
            )}
            {canCancelOrder(order) && order.payment_status !== 'PAID' && (
              <SuggestedAction
                title="Annuler la commande"
                description="Cette commande peut etre annulee."
                confidence={60}
                icon={<XCircle size={16} />}
              />
            )}
            {canRefundOrder(order) && (
              <SuggestedAction
                title="Traiter un remboursement"
                description="Cette commande est eligible au remboursement."
                confidence={70}
                icon={<CreditCard size={16} />}
              />
            )}
            {order.status === 'DELIVERED' && (
              <SuggestedAction
                title="Commande terminee"
                description="Cette commande est livree avec succes."
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
            <h4>Articles</h4>
            <p className="text-lg font-medium text-primary">{order.items.length}</p>
            <p className="text-sm text-muted">produit(s)</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Quantite</h4>
            <p className="text-lg font-medium text-blue-600">
              {order.items.reduce((sum, item) => sum + item.quantity, 0)}
            </p>
            <p className="text-sm text-muted">unite(s)</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Total</h4>
            <p className="text-lg font-medium text-green-600">
              {formatCurrency(order.total, order.currency)}
            </p>
            <p className="text-sm text-muted">TTC</p>
          </div>
          {order.discount > 0 && (
            <div className="azals-analysis-item">
              <h4>Remise</h4>
              <p className="text-lg font-medium text-orange-600">
                -{formatCurrency(order.discount, order.currency)}
              </p>
              <p className="text-sm text-muted">appliquee</p>
            </div>
          )}
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
 * Generer les insights bases sur la commande
 */
function generateInsights(order: Order): Insight[] {
  const insights: Insight[] = [];

  // Statut commande
  if (order.status === 'DELIVERED') {
    insights.push({
      id: 'delivered',
      type: 'success',
      title: 'Commande livree',
      description: 'La commande a ete livree avec succes.',
    });
  } else if (order.status === 'SHIPPED') {
    insights.push({
      id: 'shipped',
      type: 'success',
      title: 'Commande expediee',
      description: 'Le colis est en cours de livraison.',
    });
  } else if (order.status === 'CANCELLED') {
    insights.push({
      id: 'cancelled',
      type: 'warning',
      title: 'Commande annulee',
      description: 'Cette commande a ete annulee.',
    });
  } else if (order.status === 'PENDING') {
    insights.push({
      id: 'pending',
      type: 'suggestion',
      title: 'En attente',
      description: 'La commande attend une confirmation.',
    });
  }

  // Paiement
  if (order.payment_status === 'PAID') {
    insights.push({
      id: 'paid',
      type: 'success',
      title: 'Paiement recu',
      description: 'Le paiement a ete effectue.',
    });
  } else if (order.payment_status === 'PENDING') {
    insights.push({
      id: 'payment-pending',
      type: 'warning',
      title: 'Paiement en attente',
      description: 'Le paiement n\'a pas encore ete recu.',
    });
  } else if (order.payment_status === 'FAILED') {
    insights.push({
      id: 'payment-failed',
      type: 'warning',
      title: 'Paiement echoue',
      description: 'Le paiement a echoue.',
    });
  }

  // Expedition
  if (order.tracking_number) {
    insights.push({
      id: 'has-tracking',
      type: 'success',
      title: 'Suivi disponible',
      description: 'Le numero de suivi est disponible.',
    });
  } else if (order.status === 'SHIPPED') {
    insights.push({
      id: 'no-tracking',
      type: 'suggestion',
      title: 'Suivi manquant',
      description: 'Ajoutez un numero de suivi.',
    });
  }

  // Adresse
  if (order.shipping_address) {
    insights.push({
      id: 'has-address',
      type: 'success',
      title: 'Adresse complete',
      description: 'L\'adresse de livraison est renseignee.',
    });
  } else {
    insights.push({
      id: 'no-address',
      type: 'warning',
      title: 'Adresse manquante',
      description: 'L\'adresse de livraison n\'est pas renseignee.',
    });
  }

  // Articles
  if (order.items.length > 0) {
    insights.push({
      id: 'has-items',
      type: 'success',
      title: 'Articles presents',
      description: `${order.items.length} article(s) commande(s).`,
    });
  }

  // Remise
  if (order.discount > 0) {
    insights.push({
      id: 'has-discount',
      type: 'success',
      title: 'Remise appliquee',
      description: order.discount_code ? `Code: ${order.discount_code}` : 'Reduction active.',
    });
  }

  return insights;
}

export default OrderIATab;
