/**
 * AZALSCORE Module - E-commerce - Product IA Tab
 * Onglet Assistant IA pour le produit
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, Package, Tag, Lightbulb } from 'lucide-react';
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
  isLowStock, isOutOfStock,
  calculateMargin
} from '../types';
import type { Product } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * ProductIATab - Assistant IA
 */
export const ProductIATab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(product);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(product);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const healthScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce produit et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

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
      <Card title="Score de santé" icon={<TrendingUp size={18} />} className="mb-4">
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
            <h4>Stock</h4>
            <p className={`text-lg font-medium ${isOutOfStock(product) ? 'text-red-600' : isLowStock(product) ? 'text-orange-600' : 'text-green-600'}`}>
              {product.stock}
            </p>
            <p className="text-sm text-muted">unités</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Prix</h4>
            <p className="text-lg font-medium text-blue-600">
              {formatCurrency(product.price, product.currency)}
            </p>
            <p className="text-sm text-muted">prix de vente</p>
          </div>
          {product.cost && (
            <div className="azals-analysis-item">
              <h4>Marge</h4>
              <p className={`text-lg font-medium ${calculateMargin(product.price, product.cost) >= 30 ? 'text-green-600' : 'text-orange-600'}`}>
                {calculateMargin(product.price, product.cost).toFixed(1)}%
              </p>
              <p className="text-sm text-muted">taux de marge</p>
            </div>
          )}
          {product.total_sales !== undefined && (
            <div className="azals-analysis-item">
              <h4>Ventes</h4>
              <p className="text-lg font-medium text-primary">
                {product.total_sales}
              </p>
              <p className="text-sm text-muted">total vendu</p>
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
 * Générer les actions suggérées basées sur le produit
 */
function generateSuggestedActions(product: Product): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isOutOfStock(product)) {
    actions.push({
      id: 'restock',
      title: 'Réapprovisionner',
      description: 'Ce produit est en rupture de stock.',
      confidence: 100,
      icon: <Package size={16} />,
      actionLabel: 'Commander',
    });
  }

  if (isLowStock(product) && !isOutOfStock(product)) {
    actions.push({
      id: 'order-stock',
      title: 'Commander du stock',
      description: 'Le niveau de stock est faible.',
      confidence: 90,
      icon: <Package size={16} />,
      actionLabel: 'Commander',
    });
  }

  if (product.status === 'DRAFT') {
    actions.push({
      id: 'publish',
      title: 'Publier le produit',
      description: 'Ce produit est en brouillon et non visible.',
      confidence: 95,
      icon: <Tag size={16} />,
      actionLabel: 'Publier',
    });
  }

  if (!product.image_url) {
    actions.push({
      id: 'add-image',
      title: 'Ajouter une image',
      description: 'Les produits avec images vendent mieux.',
      confidence: 85,
      icon: <Lightbulb size={16} />,
      actionLabel: 'Ajouter',
    });
  }

  if (product.cost && calculateMargin(product.price, product.cost) < 15) {
    actions.push({
      id: 'review-pricing',
      title: 'Revoir la tarification',
      description: 'La marge est inférieure à 15%.',
      confidence: 80,
      icon: <Tag size={16} />,
      actionLabel: 'Modifier',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le produit
 */
function generateInsights(product: Product): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (product.status === 'ACTIVE') {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Produit actif',
      description: 'Le produit est visible et disponible à la vente.',
    });
  } else if (product.status === 'DRAFT') {
    insights.push({
      id: 'draft',
      type: 'warning',
      title: 'Produit en brouillon',
      description: "Ce produit n'est pas encore publié.",
    });
  } else if (product.status === 'ARCHIVED') {
    insights.push({
      id: 'archived',
      type: 'suggestion',
      title: 'Produit archivé',
      description: 'Ce produit a été archivé.',
    });
  }

  // Stock
  if (isOutOfStock(product)) {
    insights.push({
      id: 'out-of-stock',
      type: 'warning',
      title: 'Rupture de stock',
      description: 'Le produit est indisponible.',
    });
  } else if (isLowStock(product)) {
    insights.push({
      id: 'low-stock',
      type: 'warning',
      title: 'Stock faible',
      description: 'Le stock approche du seuil minimum.',
    });
  } else {
    insights.push({
      id: 'stock-ok',
      type: 'success',
      title: 'Stock suffisant',
      description: `${product.stock} unités en stock.`,
    });
  }

  // Image
  if (product.image_url) {
    insights.push({
      id: 'has-image',
      type: 'success',
      title: 'Image présente',
      description: 'Le produit a une image principale.',
    });
  } else {
    insights.push({
      id: 'no-image',
      type: 'suggestion',
      title: 'Image manquante',
      description: 'Ajoutez une image pour améliorer les ventes.',
    });
  }

  // Marge
  if (product.cost) {
    const margin = calculateMargin(product.price, product.cost);
    if (margin >= 30) {
      insights.push({
        id: 'good-margin',
        type: 'success',
        title: 'Bonne marge',
        description: `Marge de ${margin.toFixed(1)}%.`,
      });
    } else if (margin < 15) {
      insights.push({
        id: 'low-margin',
        type: 'warning',
        title: 'Marge faible',
        description: `Marge de seulement ${margin.toFixed(1)}%.`,
      });
    }
  }

  // Description
  if (product.description) {
    insights.push({
      id: 'has-description',
      type: 'success',
      title: 'Description complète',
      description: 'Le produit a une description.',
    });
  } else {
    insights.push({
      id: 'no-description',
      type: 'suggestion',
      title: 'Description manquante',
      description: 'Ajoutez une description détaillée.',
    });
  }

  // Catégorie
  if (product.category_id) {
    insights.push({
      id: 'has-category',
      type: 'success',
      title: 'Catégorisé',
      description: `Dans la catégorie "${product.category_name}".`,
    });
  } else {
    insights.push({
      id: 'no-category',
      type: 'suggestion',
      title: 'Non catégorisé',
      description: 'Assignez une catégorie au produit.',
    });
  }

  return insights;
}

export default ProductIATab;
