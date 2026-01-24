/**
 * AZALSCORE Module - CRM - Customer IA Tab
 * Onglet Assistant IA pour le client
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Target, Euro, Phone, Mail, FileText
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Customer } from '../types';
import {
  formatCurrency, formatDate,
  CUSTOMER_TYPE_CONFIG,
  isProspect, isActiveCustomer, isChurned, canConvert,
  getCustomerValue, getLeadScore, getLeadScoreLevel
} from '../types';

/**
 * CustomerIATab - Assistant IA pour le client
 */
export const CustomerIATab: React.FC<TabContentProps<Customer>> = ({ data: customer }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(customer);

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
            J'ai analysé ce {isProspect(customer) ? 'prospect' : 'client'} et identifié{' '}
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

      {/* Score client */}
      <Card title="Score relationnel" icon={<TrendingUp size={18} />} className="mb-4">
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
            {canConvert(customer) && (
              <SuggestedAction
                title="Convertir en client"
                description="Ce prospect semble qualifié pour devenir client."
                confidence={getLeadScore(customer) || 70}
                icon={<Target size={16} />}
              />
            )}
            {isProspect(customer) && (
              <SuggestedAction
                title="Planifier un appel"
                description="Maintenir le contact pour faire avancer la relation."
                confidence={80}
                icon={<Phone size={16} />}
              />
            )}
            {isActiveCustomer(customer) && !customer.last_order_date && (
              <SuggestedAction
                title="Créer un devis"
                description="Proposer une offre commerciale."
                confidence={85}
                icon={<FileText size={16} />}
              />
            )}
            {isActiveCustomer(customer) && customer.last_order_date && (
              <SuggestedAction
                title="Proposer des produits complémentaires"
                description="Opportunité de vente croisée basée sur l'historique."
                confidence={75}
                icon={<Euro size={16} />}
              />
            )}
            {!customer.email && (
              <SuggestedAction
                title="Compléter les coordonnées"
                description="L'email est manquant pour ce contact."
                confidence={90}
                icon={<Mail size={16} />}
              />
            )}
            {isChurned(customer) && (
              <SuggestedAction
                title="Relancer le client"
                description="Client perdu - tentative de réactivation recommandée."
                confidence={60}
                icon={<RefreshCw size={16} />}
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
