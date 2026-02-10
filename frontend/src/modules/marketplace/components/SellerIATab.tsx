/**
 * AZALSCORE Module - Marketplace - Seller IA Tab
 * Onglet Assistant IA pour le vendeur
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  TrendingUp, AlertTriangle, ThumbsUp, UserCheck, Package, Wallet
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Seller } from '../types';
import {
  canApproveSeller, canSuspendSeller, canReactivateSeller,
  formatRating, SELLER_STATUS_CONFIG
} from '../types';
import { formatCurrency, formatPercent } from '@/utils/formatters';

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
 * SellerIATab - Assistant IA
 */
export const SellerIATab: React.FC<TabContentProps<Seller>> = ({ data: seller }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(seller);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(seller);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const sellerScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce vendeur et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score vendeur - Composant partagé */}
      <Card title="Score vendeur" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={sellerScore}
          label="Vendeur"
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
            <h4>Produits</h4>
            <p className="text-lg font-medium text-primary">{seller.products_count}</p>
            <p className="text-sm text-muted">au catalogue</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Ventes</h4>
            <p className="text-lg font-medium text-blue-600">{seller.total_sales}</p>
            <p className="text-sm text-muted">commandes</p>
          </div>
          <div className="azals-analysis-item">
            <h4>CA Total</h4>
            <p className="text-lg font-medium text-green-600">
              {formatCurrency(seller.total_revenue)}
            </p>
            <p className="text-sm text-muted">genere</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Commission</h4>
            <p className="text-lg font-medium text-orange-600">
              {formatPercent(seller.commission_rate)}
            </p>
            <p className="text-sm text-muted">taux applique</p>
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
 * Générer les actions suggérées basées sur le vendeur
 */
function generateSuggestedActions(seller: Seller): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (canApproveSeller(seller)) {
    actions.push({
      id: 'approve',
      title: 'Approuver le vendeur',
      description: 'Ce vendeur est en attente de validation.',
      confidence: seller.is_verified ? 90 : 70,
      icon: <UserCheck size={16} />,
      actionLabel: 'Approuver',
    });
  }

  if (canSuspendSeller(seller) && seller.rating !== undefined && seller.rating < 3) {
    actions.push({
      id: 'examine',
      title: 'Examiner le vendeur',
      description: 'Note moyenne faible, vérification recommandée.',
      confidence: 75,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Examiner',
    });
  }

  if (canReactivateSeller(seller)) {
    actions.push({
      id: 'reactivate',
      title: 'Réactiver le compte',
      description: 'Ce vendeur est actuellement suspendu.',
      confidence: 60,
      icon: <UserCheck size={16} />,
      actionLabel: 'Réactiver',
    });
  }

  if (!seller.is_verified && seller.status === 'ACTIVE') {
    actions.push({
      id: 'verify',
      title: 'Vérifier le vendeur',
      description: "Ce vendeur actif n'est pas encore vérifié.",
      confidence: 85,
      icon: <UserCheck size={16} />,
      actionLabel: 'Vérifier',
    });
  }

  if (seller.products_count === 0 && seller.status === 'ACTIVE') {
    actions.push({
      id: 'contact',
      title: 'Contacter le vendeur',
      description: 'Aucun produit enregistré.',
      confidence: 80,
      icon: <Package size={16} />,
      actionLabel: 'Contacter',
    });
  }

  if (seller.pending_payout && seller.pending_payout > 0) {
    actions.push({
      id: 'payout',
      title: 'Traiter le paiement',
      description: `${formatCurrency(seller.pending_payout)} en attente.`,
      confidence: 90,
      icon: <Wallet size={16} />,
      actionLabel: 'Payer',
    });
  }

  if (seller.status === 'ACTIVE' && seller.total_sales > 0) {
    actions.push({
      id: 'performant',
      title: 'Vendeur performant',
      description: 'Ce vendeur est actif et génère des ventes.',
      confidence: 100,
      icon: <ThumbsUp size={16} />,
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le vendeur
 */
function generateInsights(seller: Seller): Insight[] {
  const insights: Insight[] = [];

  // Statut vendeur
  if (seller.status === 'ACTIVE') {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Vendeur actif',
      description: 'Le compte vendeur est actif et operationnel.',
    });
  } else if (seller.status === 'PENDING') {
    insights.push({
      id: 'pending',
      type: 'suggestion',
      title: 'En attente de validation',
      description: 'Ce vendeur attend une approbation.',
    });
  } else if (seller.status === 'SUSPENDED') {
    insights.push({
      id: 'suspended',
      type: 'warning',
      title: 'Compte suspendu',
      description: 'Ce compte vendeur est suspendu.',
    });
  } else if (seller.status === 'REJECTED') {
    insights.push({
      id: 'rejected',
      type: 'warning',
      title: 'Inscription refusee',
      description: 'La demande d\'inscription a ete refusee.',
    });
  }

  // Verification
  if (seller.is_verified) {
    insights.push({
      id: 'verified',
      type: 'success',
      title: 'Compte verifie',
      description: 'L\'identite du vendeur a ete verifiee.',
    });
  } else if (seller.status === 'ACTIVE') {
    insights.push({
      id: 'not-verified',
      type: 'suggestion',
      title: 'Non verifie',
      description: 'Ce vendeur actif n\'est pas encore verifie.',
    });
  }

  // Produits
  if (seller.products_count > 0) {
    insights.push({
      id: 'has-products',
      type: 'success',
      title: 'Catalogue actif',
      description: `${seller.products_count} produit(s) au catalogue.`,
    });
  } else if (seller.status === 'ACTIVE') {
    insights.push({
      id: 'no-products',
      type: 'warning',
      title: 'Catalogue vide',
      description: 'Aucun produit enregistre.',
    });
  }

  // Ventes
  if (seller.total_sales > 0) {
    insights.push({
      id: 'has-sales',
      type: 'success',
      title: 'Ventes realisees',
      description: `${seller.total_sales} commande(s) traitee(s).`,
    });
  }

  // Note
  if (seller.rating !== undefined) {
    if (seller.rating >= 4) {
      insights.push({
        id: 'good-rating',
        type: 'success',
        title: 'Excellente note',
        description: `Note moyenne de ${formatRating(seller.rating)}.`,
      });
    } else if (seller.rating >= 3) {
      insights.push({
        id: 'avg-rating',
        type: 'suggestion',
        title: 'Note correcte',
        description: `Note moyenne de ${formatRating(seller.rating)}.`,
      });
    } else {
      insights.push({
        id: 'low-rating',
        type: 'warning',
        title: 'Note faible',
        description: `Note moyenne de ${formatRating(seller.rating)}.`,
      });
    }
  }

  // Coordonnees bancaires
  if (seller.bank_iban) {
    insights.push({
      id: 'has-bank',
      type: 'success',
      title: 'Coordonnees bancaires',
      description: 'Les coordonnees de paiement sont renseignees.',
    });
  } else if (seller.status === 'ACTIVE') {
    insights.push({
      id: 'no-bank',
      type: 'warning',
      title: 'IBAN manquant',
      description: 'Les coordonnees bancaires ne sont pas renseignees.',
    });
  }

  // Paiements en attente
  if (seller.pending_payout && seller.pending_payout > 0) {
    insights.push({
      id: 'pending-payout',
      type: 'suggestion',
      title: 'Paiement en attente',
      description: `${formatCurrency(seller.pending_payout)} a verser.`,
    });
  }

  return insights;
}

export default SellerIATab;
