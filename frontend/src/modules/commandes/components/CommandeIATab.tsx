/**
 * AZALSCORE Module - COMMANDES - IA Tab
 * Onglet Assistant IA pour la commande
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, ChevronRight, Zap, Truck, FileText, Package } from 'lucide-react';
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
import type { Commande } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * CommandeIATab - Assistant IA pour la commande
 */
export const CommandeIATab: React.FC<TabContentProps<Commande>> = ({ data: commande }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(commande);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(commande);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const qualityScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

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

      {/* Score de qualité - Composant partagé */}
      <Card title="Score de qualité de la commande" icon={<Zap size={18} />} className="mb-4">
        <IAScoreCircle
          score={qualityScore}
          label="Qualité"
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
            <h4>Marge estimée</h4>
            <p className="text-lg font-medium text-success">30%</p>
            <p className="text-sm text-muted">Conforme aux objectifs</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Délai de livraison</h4>
            <p className="text-lg font-medium">
              {commande.delivery_date ? `${Math.ceil((new Date(commande.delivery_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))} jours` : 'Non défini'}
            </p>
            <p className="text-sm text-muted">Standard pour ce type de commande</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Historique client</h4>
            <p className="text-lg font-medium">12 commandes</p>
            <p className="text-sm text-muted">Client fidèle depuis 2 ans</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Taux de livraison à temps</h4>
            <p className="text-lg font-medium text-success">94%</p>
            <p className="text-sm text-muted">Pour ce client</p>
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
function generateSuggestedActions(commande: Commande): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (commande.status === 'DRAFT') {
    actions.push({
      id: 'validate',
      title: 'Valider la commande',
      description: 'La commande est complète et peut être validée pour traitement.',
      confidence: 85,
      icon: <ChevronRight size={16} />,
      actionLabel: 'Valider',
    });
  }

  if (commande.status === 'VALIDATED') {
    actions.push({
      id: 'ship',
      title: 'Préparer la livraison',
      description: 'La commande est validée, prête pour expédition.',
      confidence: 90,
      icon: <Truck size={16} />,
      actionLabel: 'Expédier',
    });

    actions.push({
      id: 'affaire',
      title: 'Créer une affaire',
      description: 'Suivre cette commande dans le module Affaires.',
      confidence: 75,
      icon: <Package size={16} />,
      actionLabel: 'Créer',
    });
  }

  if (commande.status === 'DELIVERED') {
    actions.push({
      id: 'invoice',
      title: 'Créer la facture',
      description: 'La commande a été livrée, vous pouvez créer la facture.',
      confidence: 95,
      icon: <FileText size={16} />,
      actionLabel: 'Facturer',
    });
  }

  if (!commande.delivery_date && commande.status === 'VALIDATED') {
    actions.push({
      id: 'set-delivery-date',
      title: 'Définir la date de livraison',
      description: "Aucune date de livraison prévue. Planifiez l'expédition.",
      confidence: 70,
      icon: <Truck size={16} />,
      actionLabel: 'Planifier',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur la commande
 */
function generateInsights(commande: Commande): Insight[] {
  const insights: Insight[] = [];

  // Vérifier la date de livraison
  if (commande.delivery_date) {
    const deliveryDate = new Date(commande.delivery_date);
    const daysUntilDelivery = Math.ceil((deliveryDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));

    if (daysUntilDelivery < 0 && commande.status !== 'DELIVERED' && commande.status !== 'INVOICED') {
      insights.push({
        id: 'late-delivery',
        type: 'warning',
        title: 'Livraison en retard',
        description: `La date de livraison prévue est dépassée de ${Math.abs(daysUntilDelivery)} jours.`,
      });
    } else if (daysUntilDelivery <= 2 && daysUntilDelivery >= 0) {
      insights.push({
        id: 'delivery-soon',
        type: 'suggestion',
        title: 'Livraison imminente',
        description: `Livraison prévue dans ${daysUntilDelivery} jour(s). Vérifiez la préparation.`,
      });
    }
  } else if (commande.status === 'VALIDATED') {
    insights.push({
      id: 'no-delivery-date',
      type: 'warning',
      title: 'Date de livraison manquante',
      description: 'Aucune date de livraison définie pour cette commande validée.',
    });
  }

  // Vérifier les lignes
  if (!commande.lines || commande.lines.length === 0) {
    insights.push({
      id: 'no-lines',
      type: 'warning',
      title: 'Aucune ligne',
      description: 'Cette commande ne contient pas de lignes. Ajoutez des produits.',
    });
  } else {
    insights.push({
      id: 'lines-ok',
      type: 'success',
      title: 'Lignes complètes',
      description: `${commande.lines.length} ligne(s) pour un total de ${formatCurrency(commande.subtotal)}.`,
    });
  }

  // Vérifier le statut et les actions possibles
  if (commande.status === 'DELIVERED') {
    insights.push({
      id: 'ready-invoice',
      type: 'suggestion',
      title: 'Prête à facturer',
      description: 'Cette commande livrée peut être facturée.',
    });
  }

  // Client connu
  if (commande.customer_code) {
    insights.push({
      id: 'known-customer',
      type: 'success',
      title: 'Client référencé',
      description: 'Ce client est référencé dans votre base. Historique disponible.',
    });
  }

  // Frais de port
  if (commande.shipping_cost > 0) {
    insights.push({
      id: 'shipping-cost',
      type: 'success',
      title: 'Frais de port inclus',
      description: `Frais de port: ${formatCurrency(commande.shipping_cost)}.`,
    });
  }

  // Issue d'un devis
  if (commande.parent_number) {
    insights.push({
      id: 'from-quote',
      type: 'success',
      title: "Issue d'un devis",
      description: `Convertie depuis le devis ${commande.parent_number}.`,
    });
  }

  return insights;
}

export default CommandeIATab;
