/**
 * AZALSCORE Module - STOCK - Product IA Tab
 * Onglet Assistant IA pour l'article
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, Package, ShoppingCart, Truck, BarChart3, AlertTriangle } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Product } from '../types';
import { formatCurrency } from '@/utils/formatters';
import {
  formatQuantity, isLowStock, isOutOfStock,
  isOverstock, getStockLevel, getStockLevelLabel, isLotExpiringSoon
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
 * ProductIATab - Assistant IA pour l'article
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
  const gestionScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cet article et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de gestion - Composant partagé */}
      <Card title="Score de gestion" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={gestionScore}
          label="Gestion"
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur l'article
 */
function generateSuggestedActions(product: Product): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (isOutOfStock(product)) {
    actions.push({
      id: 'order-urgent',
      title: 'Commander en urgence',
      description: 'Le stock est épuisé. Passez une commande fournisseur.',
      confidence: 98,
      icon: <ShoppingCart size={16} />,
      actionLabel: 'Commander',
    });
  }

  if (isLowStock(product) && !isOutOfStock(product)) {
    actions.push({
      id: 'restock',
      title: 'Réapprovisionner',
      description: `Stock sous le seuil minimum (${product.min_stock} ${product.unit}).`,
      confidence: 90,
      icon: <Truck size={16} />,
      actionLabel: 'Commander',
    });
  }

  if (isOverstock(product)) {
    actions.push({
      id: 'optimize',
      title: 'Optimiser le stock',
      description: 'Stock au-dessus du maximum. Envisagez une promotion.',
      confidence: 75,
      icon: <BarChart3 size={16} />,
      actionLabel: 'Analyser',
    });
  }

  if (product.is_lot_tracked && product.lots?.some(l => isLotExpiringSoon(l))) {
    actions.push({
      id: 'manage-lots',
      title: 'Gérer les lots expirables',
      description: 'Certains lots expirent bientôt. Priorisez leur utilisation.',
      confidence: 85,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Voir lots',
    });
  }

  if (!isLowStock(product) && !isOverstock(product) && !isOutOfStock(product)) {
    actions.push({
      id: 'stock-ok',
      title: 'Stock optimal',
      description: 'Le niveau de stock est correct. Aucune action requise.',
      confidence: 95,
      icon: <Package size={16} />,
    });
  }

  return actions;
}

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
