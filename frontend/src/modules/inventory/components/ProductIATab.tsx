/**
 * AZALSCORE Module - STOCK - Product IA Tab
 * Onglet Assistant IA pour l'article
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Package, ShoppingCart, Truck, BarChart3
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Product } from '../types';
import {
  formatCurrency, formatQuantity, isLowStock, isOutOfStock,
  isOverstock, getStockLevel, getStockLevelLabel, isLotExpiringSoon
} from '../types';

/**
 * ProductIATab - Assistant IA pour l'article
 */
export const ProductIATab: React.FC<TabContentProps<Product>> = ({ data: product }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(product);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA (mode AZALSCORE) */}
      <div className="azals-std-ia-panel azals-std-azalscore-only">
        <div className="azals-std-ia-panel__header">
          <Sparkles size={24} className="azals-std-ia-panel__icon" />
          <h3 className="azals-std-ia-panel__title">Assistant AZALSCORE IA</h3>
        </div>
        <div className="azals-std-ia-panel__content">
          <p>
            J'ai analysé cet article et identifié{' '}
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
          <Button variant="ghost" leftIcon={<MessageSquare size={16} />}>
            Poser une question
          </Button>
        </div>
      </div>

      {/* Score de gestion */}
      <Card title="Score de gestion" icon={<TrendingUp size={18} />} className="mb-4">
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

        {/* Actions suggérées */}
        <Card title="Actions suggérées" icon={<ChevronRight size={18} />}>
          <div className="azals-suggested-actions">
            {isOutOfStock(product) && (
              <SuggestedAction
                title="Commander en urgence"
                description="Le stock est épuisé. Passez une commande fournisseur."
                confidence={98}
                icon={<ShoppingCart size={16} />}
              />
            )}
            {isLowStock(product) && !isOutOfStock(product) && (
              <SuggestedAction
                title="Réapprovisionner"
                description={`Stock sous le seuil minimum (${product.min_stock} ${product.unit}).`}
                confidence={90}
                icon={<Truck size={16} />}
              />
            )}
            {isOverstock(product) && (
              <SuggestedAction
                title="Optimiser le stock"
                description="Stock au-dessus du maximum. Envisagez une promotion."
                confidence={75}
                icon={<BarChart3 size={16} />}
              />
            )}
            {product.is_lot_tracked && product.lots?.some(l => isLotExpiringSoon(l)) && (
              <SuggestedAction
                title="Gérer les lots expirables"
                description="Certains lots expirent bientôt. Priorisez leur utilisation."
                confidence={85}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {!isLowStock(product) && !isOverstock(product) && (
              <SuggestedAction
                title="Stock optimal"
                description="Le niveau de stock est correct. Aucune action requise."
                confidence={95}
                icon={<Package size={16} />}
              />
            )}
          </div>
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
            <h4>Niveau de stock</h4>
            <p className={`text-lg font-medium ${
              getStockLevel(product) === 'danger' ? 'text-danger' :
              getStockLevel(product) === 'warning' ? 'text-warning' :
              getStockLevel(product) === 'info' ? 'text-blue' : 'text-success'
            }`}>
              {getStockLevelLabel(product)}
            </p>
            <p className="text-sm text-muted">
              {formatQuantity(product.current_stock, product.unit)} en stock
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Valorisation</h4>
            <p className="text-lg font-medium">
              {formatCurrency(product.current_stock * product.cost_price)}
            </p>
            <p className="text-sm text-muted">
              Coût unitaire: {formatCurrency(product.cost_price)}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Marge</h4>
            <p className={`text-lg font-medium ${product.sale_price > product.cost_price ? 'text-success' : 'text-danger'}`}>
              {((product.sale_price - product.cost_price) / product.cost_price * 100).toFixed(1)}%
            </p>
            <p className="text-sm text-muted">
              {formatCurrency(product.sale_price - product.cost_price)} / unité
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Traçabilité</h4>
            <p className="text-lg font-medium">
              {product.is_lot_tracked ? 'Par lot' : product.is_serialized ? 'Par N° série' : 'Simple'}
            </p>
            <p className="text-sm text-muted">
              {product.lots?.length || 0} lots, {product.serials?.length || 0} N° série
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
 * Composant action suggérée
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
 * Générer les insights basés sur l'article
 */
function generateInsights(product: Product): Insight[] {
  const insights: Insight[] = [];

  // Vérifier le stock
  if (isOutOfStock(product)) {
    insights.push({
      id: 'out-of-stock',
      type: 'warning',
      title: 'Rupture de stock',
      description: 'Le stock est à zéro. Commande urgente recommandée.',
    });
  } else if (isLowStock(product)) {
    insights.push({
      id: 'low-stock',
      type: 'warning',
      title: 'Stock bas',
      description: `Le stock (${product.current_stock}) est sous le seuil minimum (${product.min_stock}).`,
    });
  } else if (isOverstock(product)) {
    insights.push({
      id: 'overstock',
      type: 'suggestion',
      title: 'Surstock',
      description: `Le stock dépasse le maximum recommandé (${product.max_stock}).`,
    });
  } else {
    insights.push({
      id: 'stock-ok',
      type: 'success',
      title: 'Stock optimal',
      description: 'Le niveau de stock est dans la plage recommandée.',
    });
  }

  // Vérifier la marge
  const margin = product.sale_price - product.cost_price;
  const marginPercent = product.cost_price > 0 ? (margin / product.cost_price) * 100 : 0;
  if (marginPercent < 10) {
    insights.push({
      id: 'low-margin',
      type: 'warning',
      title: 'Marge faible',
      description: `La marge est de ${marginPercent.toFixed(1)}%, sous le seuil recommandé.`,
    });
  } else if (marginPercent >= 30) {
    insights.push({
      id: 'good-margin',
      type: 'success',
      title: 'Bonne marge',
      description: `La marge de ${marginPercent.toFixed(1)}% est excellente.`,
    });
  }

  // Vérifier les lots expirables
  if (product.is_lot_tracked && product.lots) {
    const expiringLots = product.lots.filter(l => isLotExpiringSoon(l));
    if (expiringLots.length > 0) {
      insights.push({
        id: 'expiring-lots',
        type: 'warning',
        title: 'Lots à surveiller',
        description: `${expiringLots.length} lot(s) expire(nt) dans les 30 prochains jours.`,
      });
    }
  }

  // Vérifier l'activité
  if (product.is_active) {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Article actif',
      description: 'L\'article est actif et peut être commandé.',
    });
  } else {
    insights.push({
      id: 'inactive',
      type: 'suggestion',
      title: 'Article inactif',
      description: 'L\'article est désactivé et ne peut pas être commandé.',
    });
  }

  // Vérifier le fournisseur
  if (product.supplier_name) {
    insights.push({
      id: 'supplier-ok',
      type: 'success',
      title: 'Fournisseur défini',
      description: `Fournisseur principal: ${product.supplier_name}.`,
    });
  } else {
    insights.push({
      id: 'no-supplier',
      type: 'suggestion',
      title: 'Fournisseur non défini',
      description: 'Définissez un fournisseur principal pour faciliter les commandes.',
    });
  }

  // Vérifier le code-barres
  if (product.barcode) {
    insights.push({
      id: 'barcode-ok',
      type: 'success',
      title: 'Code-barres défini',
      description: 'L\'article peut être scanné pour les opérations.',
    });
  }

  return insights;
}

export default ProductIATab;
