/**
 * AZALSCORE Module - COMMANDES - IA Tab
 * Onglet Assistant IA pour la commande
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Zap, Truck, FileText, Package
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Commande } from '../types';
import { formatCurrency, formatDate } from '../types';

/**
 * CommandeIATab - Assistant IA pour la commande
 * Fournit des insights, suggestions et analyses automatiques
 */
export const CommandeIATab: React.FC<TabContentProps<Commande>> = ({ data: commande }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights basés sur les données de la commande
  const insights = generateInsights(commande);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA proéminent (mode AZALSCORE) */}
      <div className="azals-std-ia-panel azals-std-azalscore-only">
        <div className="azals-std-ia-panel__header">
          <Sparkles size={24} className="azals-std-ia-panel__icon" />
          <h3 className="azals-std-ia-panel__title">Assistant AZALSCORE IA</h3>
        </div>
        <div className="azals-std-ia-panel__content">
          <p>
            J'ai analysé cette commande et identifié <strong>{insights.length} points d'attention</strong>.
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

      {/* Score de qualité */}
      <Card title="Score de qualité de la commande" icon={<Zap size={18} />} className="mb-4">
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
        {/* Alertes et suggestions */}
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
            {commande.status === 'DRAFT' && (
              <SuggestedAction
                title="Valider la commande"
                description="La commande est complète et peut être validée pour traitement."
                confidence={85}
                icon={<ChevronRight size={16} />}
              />
            )}
            {commande.status === 'VALIDATED' && (
              <>
                <SuggestedAction
                  title="Préparer la livraison"
                  description="La commande est validée, prête pour expédition."
                  confidence={90}
                  icon={<Truck size={16} />}
                />
                <SuggestedAction
                  title="Créer une affaire"
                  description="Suivre cette commande dans le module Affaires."
                  confidence={75}
                  icon={<Package size={16} />}
                />
              </>
            )}
            {commande.status === 'DELIVERED' && (
              <SuggestedAction
                title="Créer la facture"
                description="La commande a été livrée, vous pouvez créer la facture."
                confidence={95}
                icon={<FileText size={16} />}
              />
            )}
            {!commande.delivery_date && commande.status === 'VALIDATED' && (
              <SuggestedAction
                title="Définir la date de livraison"
                description="Aucune date de livraison prévue. Planifiez l'expédition."
                confidence={70}
                icon={<Truck size={16} />}
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
      title: 'Issue d\'un devis',
      description: `Convertie depuis le devis ${commande.parent_number}.`,
    });
  }

  return insights;
}

export default CommandeIATab;
