/**
 * AZALSCORE Module - Purchases - Order IA Tab
 * Onglet Assistant IA pour la commande
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, AlertTriangle, CheckCircle2, Send, Package, FileText } from 'lucide-react';
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
  ORDER_STATUS_CONFIG,
  canValidateOrder, canCreateInvoiceFromOrder
} from '../types';
import type { PurchaseOrder } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * OrderIATab - Assistant IA
 */
export const OrderIATab: React.FC<TabContentProps<PurchaseOrder>> = ({ data: order }) => {
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
  const conformityScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

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

      {/* Score de conformité - Composant partagé */}
      <Card title="Score de conformité" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={conformityScore}
          label="Conformité"
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
function generateSuggestedActions(order: PurchaseOrder): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (order.status === 'DRAFT' && canValidateOrder(order)) {
    actions.push({
      id: 'validate',
      title: 'Valider la commande',
      description: 'La commande est complète et peut être validée.',
      confidence: 95,
      icon: <CheckCircle2 size={16} />,
      actionLabel: 'Valider',
    });
  }

  if (order.status === 'DRAFT' && order.lines.length === 0) {
    actions.push({
      id: 'add-lines',
      title: 'Ajouter des lignes',
      description: 'La commande ne contient aucune ligne.',
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Ajouter',
    });
  }

  if (order.status === 'SENT') {
    actions.push({
      id: 'follow-up',
      title: 'Suivre la commande',
      description: 'Relancez le fournisseur pour confirmation.',
      confidence: 80,
      icon: <Send size={16} />,
      actionLabel: 'Relancer',
    });
  }

  if (order.status === 'CONFIRMED') {
    actions.push({
      id: 'prepare-reception',
      title: 'Préparer la réception',
      description: 'La commande est confirmée, préparez la réception.',
      confidence: 85,
      icon: <Package size={16} />,
      actionLabel: 'Préparer',
    });
  }

  if (canCreateInvoiceFromOrder(order)) {
    actions.push({
      id: 'create-invoice',
      title: 'Créer la facture',
      description: 'La commande peut être facturée.',
      confidence: 90,
      icon: <FileText size={16} />,
      actionLabel: 'Créer',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur la commande
 */
function generateInsights(order: PurchaseOrder): Insight[] {
  const insights: Insight[] = [];
  const _statusConfig = ORDER_STATUS_CONFIG[order.status];

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
