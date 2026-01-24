/**
 * AZALSCORE Module - Purchases - Order IA Tab
 * Onglet Assistant IA pour la commande
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ThumbsDown, ChevronRight,
  CheckCircle2, Send, Package, FileText
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { PurchaseOrder } from '../types';
import {
  ORDER_STATUS_CONFIG, formatCurrency,
  canValidateOrder, canCreateInvoiceFromOrder
} from '../types';

/**
 * OrderIATab - Assistant IA
 */
export const OrderIATab: React.FC<TabContentProps<PurchaseOrder>> = ({ data: order }) => {
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

      {/* Score de conformite */}
      <Card title="Score de conformite" icon={<TrendingUp size={18} />} className="mb-4">
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
            {order.status === 'DRAFT' && canValidateOrder(order) && (
              <SuggestedAction
                title="Valider la commande"
                description="La commande est complete et peut etre validee."
                confidence={95}
                icon={<CheckCircle2 size={16} />}
              />
            )}
            {order.status === 'DRAFT' && order.lines.length === 0 && (
              <SuggestedAction
                title="Ajouter des lignes"
                description="La commande ne contient aucune ligne."
                confidence={100}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {order.status === 'SENT' && (
              <SuggestedAction
                title="Suivre la commande"
                description="Relancez le fournisseur pour confirmation."
                confidence={80}
                icon={<Send size={16} />}
              />
            )}
            {order.status === 'CONFIRMED' && (
              <SuggestedAction
                title="Preparer la reception"
                description="La commande est confirmee, preparez la reception."
                confidence={85}
                icon={<Package size={16} />}
              />
            )}
            {canCreateInvoiceFromOrder(order) && (
              <SuggestedAction
                title="Creer la facture"
                description="La commande peut etre facturee."
                confidence={90}
                icon={<FileText size={16} />}
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
            <h4>Lignes</h4>
            <p className="text-lg font-medium text-primary">{order.lines.length}</p>
            <p className="text-sm text-muted">Lignes de commande</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Total HT</h4>
            <p className="text-lg font-medium text-blue-600">
              {formatCurrency(order.total_ht, order.currency)}
            </p>
            <p className="text-sm text-muted">Montant hors taxes</p>
          </div>
          <div className="azals-analysis-item">
            <h4>TVA</h4>
            <p className="text-lg font-medium text-orange-600">
              {formatCurrency(order.total_tax, order.currency)}
            </p>
            <p className="text-sm text-muted">Montant TVA</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Total TTC</h4>
            <p className="text-lg font-medium text-green-600">
              {formatCurrency(order.total_ttc, order.currency)}
            </p>
            <p className="text-sm text-muted">Montant total</p>
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
 * Generer les insights bases sur la commande
 */
function generateInsights(order: PurchaseOrder): Insight[] {
  const insights: Insight[] = [];
  const statusConfig = ORDER_STATUS_CONFIG[order.status];

  // Statut
  if (order.status === 'DRAFT') {
    insights.push({
      id: 'draft',
      type: 'suggestion',
      title: 'Commande en brouillon',
      description: 'Validez la commande pour l\'envoyer au fournisseur.',
    });
  } else if (order.status === 'SENT') {
    insights.push({
      id: 'sent',
      type: 'success',
      title: 'Commande envoyee',
      description: 'En attente de confirmation fournisseur.',
    });
  } else if (order.status === 'CONFIRMED') {
    insights.push({
      id: 'confirmed',
      type: 'success',
      title: 'Commande confirmee',
      description: 'Le fournisseur a confirme la commande.',
    });
  } else if (order.status === 'RECEIVED') {
    insights.push({
      id: 'received',
      type: 'success',
      title: 'Commande recue',
      description: 'La marchandise a ete receptionnee.',
    });
  } else if (order.status === 'CANCELLED') {
    insights.push({
      id: 'cancelled',
      type: 'warning',
      title: 'Commande annulee',
      description: 'Cette commande a ete annulee.',
    });
  }

  // Lignes
  if (order.lines.length > 0) {
    insights.push({
      id: 'has-lines',
      type: 'success',
      title: 'Lignes presentes',
      description: `${order.lines.length} ligne(s) de commande.`,
    });
  } else {
    insights.push({
      id: 'no-lines',
      type: 'warning',
      title: 'Aucune ligne',
      description: 'Ajoutez au moins une ligne de commande.',
    });
  }

  // Fournisseur
  insights.push({
    id: 'has-supplier',
    type: 'success',
    title: 'Fournisseur identifie',
    description: `${order.supplier_code} - ${order.supplier_name}`,
  });

  // Date de livraison
  if (order.expected_date) {
    insights.push({
      id: 'has-delivery-date',
      type: 'success',
      title: 'Date de livraison prevue',
      description: 'Livraison planifiee.',
    });
  } else {
    insights.push({
      id: 'no-delivery-date',
      type: 'suggestion',
      title: 'Date de livraison manquante',
      description: 'Ajoutez une date de livraison prevue.',
    });
  }

  // Reference
  if (order.reference) {
    insights.push({
      id: 'has-reference',
      type: 'success',
      title: 'Reference renseignee',
      description: 'Reference fournisseur disponible.',
    });
  }

  return insights;
}

export default OrderIATab;
