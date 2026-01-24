/**
 * AZALSCORE Module - E-commerce - Product IA Tab
 * Onglet Assistant IA pour le produit
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ChevronRight, Package, Tag
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Product } from '../types';
import {
  isLowStock, isOutOfStock, isProductAvailable,
  calculateMargin, formatCurrency, getConversionRate
} from '../types';

/**
 * ProductIATab - Assistant IA
 */
export const ProductIATab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(product);

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
            J'ai analyse ce produit et identifie{' '}
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

      {/* Score de sante produit */}
      <Card title="Score de sante" icon={<TrendingUp size={18} />} className="mb-4">
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
            {isOutOfStock(product) && (
              <SuggestedAction
                title="Reapprovisionner"
                description="Ce produit est en rupture de stock."
                confidence={100}
                icon={<Package size={16} />}
              />
            )}
            {isLowStock(product) && !isOutOfStock(product) && (
              <SuggestedAction
                title="Commander du stock"
                description="Le niveau de stock est faible."
                confidence={90}
                icon={<Package size={16} />}
              />
            )}
            {product.status === 'DRAFT' && (
              <SuggestedAction
                title="Publier le produit"
                description="Ce produit est en brouillon et non visible."
                confidence={95}
                icon={<Tag size={16} />}
              />
            )}
            {!product.image_url && (
              <SuggestedAction
                title="Ajouter une image"
                description="Les produits avec images vendent mieux."
                confidence={85}
                icon={<Lightbulb size={16} />}
              />
            )}
            {product.cost && calculateMargin(product.price, product.cost) < 15 && (
              <SuggestedAction
                title="Revoir la tarification"
                description="La marge est inferieure a 15%."
                confidence={80}
                icon={<Tag size={16} />}
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
            <h4>Stock</h4>
            <p className={`text-lg font-medium ${isOutOfStock(product) ? 'text-red-600' : isLowStock(product) ? 'text-orange-600' : 'text-green-600'}`}>
              {product.stock}
            </p>
            <p className="text-sm text-muted">unites</p>
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
 * Generer les insights bases sur le produit
 */
function generateInsights(product: Product): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (product.status === 'ACTIVE') {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Produit actif',
      description: 'Le produit est visible et disponible a la vente.',
    });
  } else if (product.status === 'DRAFT') {
    insights.push({
      id: 'draft',
      type: 'warning',
      title: 'Produit en brouillon',
      description: 'Ce produit n\'est pas encore publie.',
    });
  } else if (product.status === 'ARCHIVED') {
    insights.push({
      id: 'archived',
      type: 'suggestion',
      title: 'Produit archive',
      description: 'Ce produit a ete archive.',
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
      description: `${product.stock} unites en stock.`,
    });
  }

  // Image
  if (product.image_url) {
    insights.push({
      id: 'has-image',
      type: 'success',
      title: 'Image presente',
      description: 'Le produit a une image principale.',
    });
  } else {
    insights.push({
      id: 'no-image',
      type: 'suggestion',
      title: 'Image manquante',
      description: 'Ajoutez une image pour ameliorer les ventes.',
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
      title: 'Description complete',
      description: 'Le produit a une description.',
    });
  } else {
    insights.push({
      id: 'no-description',
      type: 'suggestion',
      title: 'Description manquante',
      description: 'Ajoutez une description detaillee.',
    });
  }

  // Categorie
  if (product.category_id) {
    insights.push({
      id: 'has-category',
      type: 'success',
      title: 'Categorise',
      description: `Dans la categorie "${product.category_name}".`,
    });
  } else {
    insights.push({
      id: 'no-category',
      type: 'suggestion',
      title: 'Non categorise',
      description: 'Assignez une categorie au produit.',
    });
  }

  return insights;
}

export default ProductIATab;
