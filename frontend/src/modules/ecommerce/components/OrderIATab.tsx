/**
 * AZALSCORE Module - E-commerce - Order IA Tab
 * Onglet Assistant IA pour la commande
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, Truck, CreditCard, XCircle, ChevronRight, ThumbsUp } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Order } from '../types';
import { formatCurrency } from '@/utils/formatters';
import {
  canShipOrder, canCancelOrder, canRefundOrder,
  getNextOrderStatus, ORDER_STATUS_CONFIG
} from '../types';

// Composants partagés IA (AZA-NF-REUSE)
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';

/**
 * OrderIATab - Assistant IA
 */
export const OrderIATab: React.FC<TabContentProps<Order>> = ({ data: order }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(order);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(order);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const processingScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cette commande et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de traitement - Composant partagé */}
      <Card title="Score de traitement" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={processingScore}
          label="Traitement"
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
            <h4>Articles</h4>
            <p className="text-lg font-medium text-primary">{order.items.length}</p>
            <p className="text-sm text-muted">produit(s)</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Quantité</h4>
            <p className="text-lg font-medium text-blue-600">
              {order.items.reduce((sum, item) => sum + item.quantity, 0)}
            </p>
            <p className="text-sm text-muted">unité(s)</p>
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
              <p className="text-sm text-muted">appliquée</p>
            </div>
          )}
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
 * Générer les actions suggérées basées sur la commande
 */
function generateSuggestedActions(order: Order): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (canShipOrder(order)) {
    actions.push({
      id: 'ship',
      title: 'Expédier la commande',
      description: 'La commande est prête à être expédiée.',
      confidence: 95,
      icon: <Truck size={16} />,
      actionLabel: 'Expédier',
    });
  }

  if (order.payment_status === 'PENDING') {
    actions.push({
      id: 'payment-reminder',
      title: 'Relancer le paiement',
      description: 'Le paiement est en attente.',
      confidence: 85,
      icon: <CreditCard size={16} />,
      actionLabel: 'Relancer',
    });
  }

  if (getNextOrderStatus(order.status)) {
    actions.push({
      id: 'next-status',
      title: `Passer en "${ORDER_STATUS_CONFIG[getNextOrderStatus(order.status)!].label}"`,
      description: 'Prochaine étape du workflow.',
      confidence: 90,
      icon: <ChevronRight size={16} />,
      actionLabel: 'Avancer',
    });
  }

  if (canCancelOrder(order) && order.payment_status !== 'PAID') {
    actions.push({
      id: 'cancel',
      title: 'Annuler la commande',
      description: 'Cette commande peut être annulée.',
      confidence: 60,
      icon: <XCircle size={16} />,
      actionLabel: 'Annuler',
    });
  }

  if (canRefundOrder(order)) {
    actions.push({
      id: 'refund',
      title: 'Traiter un remboursement',
      description: 'Cette commande est éligible au remboursement.',
      confidence: 70,
      icon: <CreditCard size={16} />,
      actionLabel: 'Rembourser',
    });
  }

  if (order.status === 'DELIVERED') {
    actions.push({
      id: 'completed',
      title: 'Commande terminée',
      description: 'Cette commande est livrée avec succès.',
      confidence: 100,
      icon: <ThumbsUp size={16} />,
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur la commande
 */
function generateInsights(order: Order): Insight[] {
  const insights: Insight[] = [];

  // Statut commande
  if (order.status === 'DELIVERED') {
    insights.push({
      id: 'delivered',
      type: 'success',
      title: 'Commande livrée',
      description: 'La commande a été livrée avec succès.',
    });
  } else if (order.status === 'SHIPPED') {
    insights.push({
      id: 'shipped',
      type: 'success',
      title: 'Commande expédiée',
      description: 'Le colis est en cours de livraison.',
    });
  } else if (order.status === 'CANCELLED') {
    insights.push({
      id: 'cancelled',
      type: 'warning',
      title: 'Commande annulée',
      description: 'Cette commande a été annulée.',
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
      title: 'Paiement reçu',
      description: 'Le paiement a été effectué.',
    });
  } else if (order.payment_status === 'PENDING') {
    insights.push({
      id: 'payment-pending',
      type: 'warning',
      title: 'Paiement en attente',
      description: "Le paiement n'a pas encore été reçu.",
    });
  } else if (order.payment_status === 'FAILED') {
    insights.push({
      id: 'payment-failed',
      type: 'warning',
      title: 'Paiement échoué',
      description: 'Le paiement a échoué.',
    });
  }

  // Expédition
  if (order.tracking_number) {
    insights.push({
      id: 'has-tracking',
      type: 'success',
      title: 'Suivi disponible',
      description: 'Le numéro de suivi est disponible.',
    });
  } else if (order.status === 'SHIPPED') {
    insights.push({
      id: 'no-tracking',
      type: 'suggestion',
      title: 'Suivi manquant',
      description: 'Ajoutez un numéro de suivi.',
    });
  }

  // Adresse
  if (order.shipping_address) {
    insights.push({
      id: 'has-address',
      type: 'success',
      title: 'Adresse complète',
      description: "L'adresse de livraison est renseignée.",
    });
  } else {
    insights.push({
      id: 'no-address',
      type: 'warning',
      title: 'Adresse manquante',
      description: "L'adresse de livraison n'est pas renseignée.",
    });
  }

  // Articles
  if (order.items.length > 0) {
    insights.push({
      id: 'has-items',
      type: 'success',
      title: 'Articles présents',
      description: `${order.items.length} article(s) commandé(s).`,
    });
  }

  // Remise
  if (order.discount > 0) {
    insights.push({
      id: 'has-discount',
      type: 'success',
      title: 'Remise appliquée',
      description: order.discount_code ? `Code: ${order.discount_code}` : 'Réduction active.',
    });
  }

  return insights;
}

export default OrderIATab;
