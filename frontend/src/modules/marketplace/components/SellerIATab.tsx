/**
 * AZALSCORE Module - Marketplace - Seller IA Tab
 * Onglet Assistant IA pour le vendeur
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ChevronRight, UserCheck, UserX,
  Package, Wallet, Star
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Seller } from '../types';
import {
  canApproveSeller, canSuspendSeller, canReactivateSeller,
  formatCurrency, formatPercent, formatRating, SELLER_STATUS_CONFIG
} from '../types';

/**
 * SellerIATab - Assistant IA
 */
export const SellerIATab: React.FC<TabContentProps<Seller>> = ({ data: seller }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(seller);

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
            J'ai analyse ce vendeur et identifie{' '}
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

      {/* Score du vendeur */}
      <Card title="Score vendeur" icon={<TrendingUp size={18} />} className="mb-4">
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
            {canApproveSeller(seller) && (
              <SuggestedAction
                title="Approuver le vendeur"
                description="Ce vendeur est en attente de validation."
                confidence={seller.is_verified ? 90 : 70}
                icon={<UserCheck size={16} />}
              />
            )}
            {canSuspendSeller(seller) && seller.rating !== undefined && seller.rating < 3 && (
              <SuggestedAction
                title="Examiner le vendeur"
                description="Note moyenne faible, verification recommandee."
                confidence={75}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {canReactivateSeller(seller) && (
              <SuggestedAction
                title="Reactiver le compte"
                description="Ce vendeur est actuellement suspendu."
                confidence={60}
                icon={<UserCheck size={16} />}
              />
            )}
            {!seller.is_verified && seller.status === 'ACTIVE' && (
              <SuggestedAction
                title="Verifier le vendeur"
                description="Ce vendeur actif n'est pas encore verifie."
                confidence={85}
                icon={<UserCheck size={16} />}
              />
            )}
            {seller.products_count === 0 && seller.status === 'ACTIVE' && (
              <SuggestedAction
                title="Contacter le vendeur"
                description="Aucun produit enregistre."
                confidence={80}
                icon={<Package size={16} />}
              />
            )}
            {seller.pending_payout && seller.pending_payout > 0 && (
              <SuggestedAction
                title="Traiter le paiement"
                description={`${formatCurrency(seller.pending_payout)} en attente.`}
                confidence={90}
                icon={<Wallet size={16} />}
              />
            )}
            {seller.status === 'ACTIVE' && seller.total_sales > 0 && (
              <SuggestedAction
                title="Vendeur performant"
                description="Ce vendeur est actif et genere des ventes."
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
 * Generer les insights bases sur le vendeur
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
