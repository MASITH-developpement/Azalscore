/**
 * AZALSCORE Module - CRM - Customer IA Tab
 * Onglet Assistant IA pour le client
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, Target, Euro, Phone, Mail, FileText, RefreshCw } from 'lucide-react';
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';
import { Card, Grid } from '@ui/layout';
import { formatCurrency, formatDate } from '@/utils/formatters';
import {
  CUSTOMER_TYPE_CONFIG,
  isProspect, isActiveCustomer, isChurned, canConvert,
  getCustomerValue, getLeadScore, getLeadScoreLevel
} from '../types';
import type { Customer } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * CustomerIATab - Assistant IA pour le client
 */
export const CustomerIATab: React.FC<TabContentProps<Customer>> = ({ data: customer }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(customer);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(customer);

  // Calcul du score relationnel
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const relationScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const entityLabel = isProspect(customer) ? 'prospect' : 'client';
  const panelSubtitle = `J'ai analysé ce ${entityLabel} et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score relationnel - Composant partagé */}
      <Card title="Score relationnel" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={relationScore}
          label="Relation"
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
            <h4>Type</h4>
            <p className={`text-lg font-medium text-${CUSTOMER_TYPE_CONFIG[customer.type].color}`}>
              {CUSTOMER_TYPE_CONFIG[customer.type].label}
            </p>
            <p className="text-sm text-muted">
              {CUSTOMER_TYPE_CONFIG[customer.type].description}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Valeur client</h4>
            <p className={`text-lg font-medium ${
              getCustomerValue(customer) === 'high' ? 'text-success' :
              getCustomerValue(customer) === 'medium' ? 'text-warning' : 'text-muted'
            }`}>
              {getCustomerValue(customer) === 'high' ? 'Élevée' :
               getCustomerValue(customer) === 'medium' ? 'Moyenne' : 'Faible'}
            </p>
            <p className="text-sm text-muted">
              CA: {formatCurrency(customer.total_revenue || 0)}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Engagement</h4>
            <p className="text-lg font-medium">
              {customer.order_count || 0} commandes
            </p>
            <p className="text-sm text-muted">
              Dernière: {customer.last_order_date ? formatDate(customer.last_order_date) : 'Jamais'}
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Lead Score</h4>
            <p className={`text-lg font-medium ${
              getLeadScoreLevel(getLeadScore(customer)) === 'hot' ? 'text-danger' :
              getLeadScoreLevel(getLeadScore(customer)) === 'warm' ? 'text-warning' : 'text-blue'
            }`}>
              {getLeadScore(customer)}/100
            </p>
            <p className="text-sm text-muted">
              {getLeadScoreLevel(getLeadScore(customer)) === 'hot' ? 'Chaud' :
               getLeadScoreLevel(getLeadScore(customer)) === 'warm' ? 'Tiède' : 'Froid'}
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
 * Générer les actions suggérées basées sur le client
 */
function generateSuggestedActions(customer: Customer): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (canConvert(customer)) {
    actions.push({
      id: 'convert',
      title: 'Convertir en client',
      description: 'Ce prospect semble qualifié pour devenir client.',
      confidence: getLeadScore(customer) || 70,
      icon: <Target size={16} />,
      actionLabel: 'Convertir',
    });
  }

  if (isProspect(customer)) {
    actions.push({
      id: 'call',
      title: 'Planifier un appel',
      description: 'Maintenir le contact pour faire avancer la relation.',
      confidence: 80,
      icon: <Phone size={16} />,
      actionLabel: 'Appeler',
    });
  }

  if (isActiveCustomer(customer) && !customer.last_order_date) {
    actions.push({
      id: 'quote',
      title: 'Créer un devis',
      description: 'Proposer une offre commerciale.',
      confidence: 85,
      icon: <FileText size={16} />,
      actionLabel: 'Créer',
    });
  }

  if (isActiveCustomer(customer) && customer.last_order_date) {
    actions.push({
      id: 'cross-sell',
      title: 'Proposer des produits complémentaires',
      description: "Opportunité de vente croisée basée sur l'historique.",
      confidence: 75,
      icon: <Euro size={16} />,
      actionLabel: 'Voir',
    });
  }

  if (!customer.email) {
    actions.push({
      id: 'complete-email',
      title: 'Compléter les coordonnées',
      description: "L'email est manquant pour ce contact.",
      confidence: 90,
      icon: <Mail size={16} />,
      actionLabel: 'Modifier',
    });
  }

  if (isChurned(customer)) {
    actions.push({
      id: 'reactivate',
      title: 'Relancer le client',
      description: 'Client perdu - tentative de réactivation recommandée.',
      confidence: 60,
      icon: <RefreshCw size={16} />,
      actionLabel: 'Relancer',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le client
 */
function generateInsights(customer: Customer): Insight[] {
  const insights: Insight[] = [];

  // Type de client
  if (isActiveCustomer(customer)) {
    insights.push({
      id: 'active-customer',
      type: 'success',
      title: 'Client actif',
      description: `Type: ${CUSTOMER_TYPE_CONFIG[customer.type].label}`,
    });
  } else if (isProspect(customer)) {
    insights.push({
      id: 'prospect',
      type: 'suggestion',
      title: 'Prospect à qualifier',
      description: 'Planifiez des actions pour convertir ce prospect.',
    });
  } else if (isChurned(customer)) {
    insights.push({
      id: 'churned',
      type: 'warning',
      title: 'Client perdu',
      description: 'Envisagez une campagne de réactivation.',
    });
  }

  // Coordonnées
  if (customer.email && customer.phone) {
    insights.push({
      id: 'contact-complete',
      type: 'success',
      title: 'Coordonnées complètes',
      description: 'Email et téléphone renseignés.',
    });
  } else if (!customer.email) {
    insights.push({
      id: 'no-email',
      type: 'warning',
      title: 'Email manquant',
      description: 'Ajoutez une adresse email pour les communications.',
    });
  }

  // Chiffre d'affaires
  const revenue = customer.total_revenue || 0;
  if (revenue >= 100000) {
    insights.push({
      id: 'high-value',
      type: 'success',
      title: 'Client à forte valeur',
      description: `CA de ${formatCurrency(revenue)}.`,
    });
  } else if (revenue >= 10000) {
    insights.push({
      id: 'medium-value',
      type: 'success',
      title: 'Client régulier',
      description: `CA de ${formatCurrency(revenue)}.`,
    });
  } else if (isActiveCustomer(customer) && revenue < 1000) {
    insights.push({
      id: 'low-value',
      type: 'suggestion',
      title: 'Potentiel de développement',
      description: 'CA faible - opportunité de croissance.',
    });
  }

  // Dernière commande
  if (customer.last_order_date) {
    const daysSinceOrder = Math.floor(
      (Date.now() - new Date(customer.last_order_date).getTime()) / (1000 * 60 * 60 * 24)
    );
    if (daysSinceOrder > 180) {
      insights.push({
        id: 'inactive-order',
        type: 'warning',
        title: 'Client inactif',
        description: `Aucune commande depuis ${daysSinceOrder} jours.`,
      });
    } else if (daysSinceOrder < 30) {
      insights.push({
        id: 'recent-order',
        type: 'success',
        title: 'Commande récente',
        description: `Dernière commande il y a ${daysSinceOrder} jours.`,
      });
    }
  }

  // Lead score (pour les prospects)
  if (isProspect(customer)) {
    const score = getLeadScore(customer);
    if (score >= 80) {
      insights.push({
        id: 'hot-lead',
        type: 'success',
        title: 'Lead chaud',
        description: `Score de ${score}/100 - Conversion prioritaire.`,
      });
    } else if (score >= 50) {
      insights.push({
        id: 'warm-lead',
        type: 'suggestion',
        title: 'Lead tiède',
        description: `Score de ${score}/100 - Nurturing recommandé.`,
      });
    } else {
      insights.push({
        id: 'cold-lead',
        type: 'suggestion',
        title: 'Lead froid',
        description: `Score de ${score}/100 - Qualification nécessaire.`,
      });
    }
  }

  // Opportunités
  const openOpps = customer.opportunities?.filter(o => !['WON', 'LOST'].includes(o.status)) || [];
  if (openOpps.length > 0) {
    const totalValue = openOpps.reduce((sum, o) => sum + o.amount, 0);
    insights.push({
      id: 'open-opportunities',
      type: 'suggestion',
      title: `${openOpps.length} opportunité(s) en cours`,
      description: `Valeur totale: ${formatCurrency(totalValue)}.`,
    });
  }

  return insights;
}

export default CustomerIATab;
