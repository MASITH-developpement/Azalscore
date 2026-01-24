/**
 * AZALSCORE Module - Purchases - Supplier IA Tab
 * Onglet Assistant IA pour le fournisseur
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ThumbsDown, ChevronRight,
  CheckCircle2, Building2, ShoppingCart
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Supplier } from '../types';
import { SUPPLIER_STATUS_CONFIG, formatCurrency } from '../types';

/**
 * SupplierIATab - Assistant IA
 */
export const SupplierIATab: React.FC<TabContentProps<Supplier>> = ({ data: supplier }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(supplier);

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
            J'ai analyse ce fournisseur et identifie{' '}
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

      {/* Score de fiabilite */}
      <Card title="Score de fiabilite" icon={<TrendingUp size={18} />} className="mb-4">
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
            {supplier.status === 'PROSPECT' && (
              <SuggestedAction
                title="Evaluer le fournisseur"
                description="Completez l'evaluation pour approuver ce fournisseur."
                confidence={95}
                icon={<CheckCircle2 size={16} />}
              />
            )}
            {supplier.status === 'APPROVED' && (
              <SuggestedAction
                title="Commander"
                description="Ce fournisseur est approuve pour les achats."
                confidence={90}
                icon={<ShoppingCart size={16} />}
              />
            )}
            {!supplier.email && (
              <SuggestedAction
                title="Completer les coordonnees"
                description="Ajoutez l'email pour faciliter la communication."
                confidence={80}
                icon={<Building2 size={16} />}
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
            <p className="text-lg font-medium text-primary">
              {SUPPLIER_STATUS_CONFIG[supplier.status].label}
            </p>
            <p className="text-sm text-muted">Statut actuel</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Commandes</h4>
            <p className="text-lg font-medium">{supplier.total_orders || 0}</p>
            <p className="text-sm text-muted">Total commandes</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Factures</h4>
            <p className="text-lg font-medium">{supplier.total_invoices || 0}</p>
            <p className="text-sm text-muted">Total factures</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Volume</h4>
            <p className="text-lg font-medium text-blue-600">
              {formatCurrency(supplier.total_spent || 0)}
            </p>
            <p className="text-sm text-muted">Total depense</p>
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
 * Generer les insights bases sur le fournisseur
 */
function generateInsights(supplier: Supplier): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (supplier.status === 'APPROVED') {
    insights.push({
      id: 'approved',
      type: 'success',
      title: 'Fournisseur approuve',
      description: 'Ce fournisseur est valide pour les achats.',
    });
  } else if (supplier.status === 'BLOCKED') {
    insights.push({
      id: 'blocked',
      type: 'warning',
      title: 'Fournisseur bloque',
      description: 'Ce fournisseur ne peut plus recevoir de commandes.',
    });
  } else if (supplier.status === 'PROSPECT') {
    insights.push({
      id: 'prospect',
      type: 'suggestion',
      title: 'Fournisseur prospect',
      description: 'Evaluez ce fournisseur pour l\'approuver.',
    });
  }

  // Coordonnees
  if (supplier.email) {
    insights.push({
      id: 'has-email',
      type: 'success',
      title: 'Email renseigne',
      description: 'Communication electronique possible.',
    });
  } else {
    insights.push({
      id: 'no-email',
      type: 'suggestion',
      title: 'Email manquant',
      description: 'Ajoutez l\'email pour faciliter les echanges.',
    });
  }

  if (supplier.phone) {
    insights.push({
      id: 'has-phone',
      type: 'success',
      title: 'Telephone renseigne',
      description: 'Contact telephonique disponible.',
    });
  }

  // Adresse
  if (supplier.address && supplier.city) {
    insights.push({
      id: 'has-address',
      type: 'success',
      title: 'Adresse complete',
      description: 'Adresse de livraison disponible.',
    });
  } else {
    insights.push({
      id: 'incomplete-address',
      type: 'suggestion',
      title: 'Adresse incomplete',
      description: 'Completez l\'adresse pour les livraisons.',
    });
  }

  // TVA
  if (supplier.tax_id) {
    insights.push({
      id: 'has-tax-id',
      type: 'success',
      title: 'N° TVA renseigne',
      description: 'Identification fiscale complete.',
    });
  }

  // Conditions de paiement
  if (supplier.payment_terms) {
    insights.push({
      id: 'has-payment-terms',
      type: 'success',
      title: 'Conditions de paiement',
      description: 'Conditions negociees avec le fournisseur.',
    });
  }

  return insights;
}

export default SupplierIATab;
