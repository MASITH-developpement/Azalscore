/**
 * AZALSCORE Module - Purchases - Supplier IA Tab
 * Onglet Assistant IA pour le fournisseur
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, CheckCircle2, Building2, ShoppingCart } from 'lucide-react';
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
import { SUPPLIER_STATUS_CONFIG } from '../types';
import type { Supplier } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * SupplierIATab - Assistant IA pour le fournisseur
 */
export const SupplierIATab: React.FC<TabContentProps<Supplier>> = ({ data: supplier }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(supplier);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(supplier);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const fiabilityScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce fournisseur et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de fiabilité - Composant partagé */}
      <Card title="Score de fiabilité" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={fiabilityScore}
          label="Fiabilité"
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
            <p className="text-sm text-muted">Total dépensé</p>
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
 * Générer les actions suggérées basées sur le fournisseur
 */
function generateSuggestedActions(supplier: Supplier): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (supplier.status === 'PROSPECT') {
    actions.push({
      id: 'evaluate',
      title: 'Évaluer le fournisseur',
      description: "Complétez l'évaluation pour approuver ce fournisseur.",
      confidence: 95,
      icon: <CheckCircle2 size={16} />,
      actionLabel: 'Évaluer',
    });
  }

  if (supplier.status === 'APPROVED') {
    actions.push({
      id: 'order',
      title: 'Commander',
      description: 'Ce fournisseur est approuvé pour les achats.',
      confidence: 90,
      icon: <ShoppingCart size={16} />,
      actionLabel: 'Commander',
    });
  }

  if (!supplier.email) {
    actions.push({
      id: 'complete-contact',
      title: 'Compléter les coordonnées',
      description: "Ajoutez l'email pour faciliter la communication.",
      confidence: 80,
      icon: <Building2 size={16} />,
      actionLabel: 'Modifier',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le fournisseur
 */
function generateInsights(supplier: Supplier): Insight[] {
  const insights: Insight[] = [];

  // Statut
  if (supplier.status === 'APPROVED') {
    insights.push({
      id: 'approved',
      type: 'success',
      title: 'Fournisseur approuvé',
      description: 'Ce fournisseur est validé pour les achats.',
    });
  } else if (supplier.status === 'BLOCKED') {
    insights.push({
      id: 'blocked',
      type: 'warning',
      title: 'Fournisseur bloqué',
      description: 'Ce fournisseur ne peut plus recevoir de commandes.',
    });
  } else if (supplier.status === 'PROSPECT') {
    insights.push({
      id: 'prospect',
      type: 'suggestion',
      title: 'Fournisseur prospect',
      description: "Évaluez ce fournisseur pour l'approuver.",
    });
  }

  // Coordonnées
  if (supplier.email) {
    insights.push({
      id: 'has-email',
      type: 'success',
      title: 'Email renseigné',
      description: 'Communication électronique possible.',
    });
  } else {
    insights.push({
      id: 'no-email',
      type: 'suggestion',
      title: 'Email manquant',
      description: "Ajoutez l'email pour faciliter les échanges.",
    });
  }

  if (supplier.phone) {
    insights.push({
      id: 'has-phone',
      type: 'success',
      title: 'Téléphone renseigné',
      description: 'Contact téléphonique disponible.',
    });
  }

  // Adresse
  if (supplier.address && supplier.city) {
    insights.push({
      id: 'has-address',
      type: 'success',
      title: 'Adresse complète',
      description: 'Adresse de livraison disponible.',
    });
  } else {
    insights.push({
      id: 'incomplete-address',
      type: 'suggestion',
      title: 'Adresse incomplète',
      description: "Complétez l'adresse pour les livraisons.",
    });
  }

  // TVA
  if (supplier.tax_id) {
    insights.push({
      id: 'has-tax-id',
      type: 'success',
      title: 'N° TVA renseigné',
      description: 'Identification fiscale complète.',
    });
  }

  // Conditions de paiement
  if (supplier.payment_terms) {
    insights.push({
      id: 'has-payment-terms',
      type: 'success',
      title: 'Conditions de paiement',
      description: 'Conditions négociées avec le fournisseur.',
    });
  }

  return insights;
}

export default SupplierIATab;
