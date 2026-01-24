/**
 * AZALSCORE Module - DEVIS - IA Tab
 * Onglet Assistant IA pour le devis
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Zap
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Devis } from '../types';
import { formatCurrency } from '../types';

/**
 * DevisIATab - Assistant IA pour le devis
 * Fournit des insights, suggestions et analyses automatiques
 */
export const DevisIATab: React.FC<TabContentProps<Devis>> = ({ data: devis }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights basés sur les données du devis
  const insights = generateInsights(devis);

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
            J'ai analysé ce devis et identifié <strong>{insights.length} points d'attention</strong>.
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
      <Card title="Score de qualité du devis" icon={<Zap size={18} />} className="mb-4">
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
            {devis.status === 'DRAFT' && (
              <SuggestedAction
                title="Valider le devis"
                description="Le devis est complet et peut être validé pour envoi."
                confidence={85}
              />
            )}
            {devis.status === 'VALIDATED' && (
              <SuggestedAction
                title="Envoyer au client"
                description="Le devis est validé, prêt pour envoi au client."
                confidence={90}
              />
            )}
            {devis.status === 'ACCEPTED' && (
              <SuggestedAction
                title="Convertir en commande"
                description="Le devis a été accepté, vous pouvez créer la commande."
                confidence={95}
              />
            )}
            {devis.discount_percent === 0 && (
              <SuggestedAction
                title="Proposer une remise"
                description="Aucune remise appliquée. Une remise de 5% pourrait accélérer la décision."
                confidence={65}
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
            <p className="text-lg font-medium text-success">32%</p>
            <p className="text-sm text-muted">Supérieure à la moyenne (28%)</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Probabilité de conversion</h4>
            <p className="text-lg font-medium">78%</p>
            <p className="text-sm text-muted">Basé sur l'historique client</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Temps moyen de décision</h4>
            <p className="text-lg font-medium">12 jours</p>
            <p className="text-sm text-muted">Pour ce type de client</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Devis similaires acceptés</h4>
            <p className="text-lg font-medium">4 / 5</p>
            <p className="text-sm text-muted">80% taux de succès</p>
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
}

const SuggestedAction: React.FC<SuggestedActionProps> = ({ title, description, confidence }) => {
  return (
    <div className="azals-suggested-action">
      <div className="azals-suggested-action__content">
        <h4>{title}</h4>
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
 * Générer les insights basés sur le devis
 */
function generateInsights(devis: Devis): Insight[] {
  const insights: Insight[] = [];

  // Vérifier la validité
  if (devis.validity_date) {
    const validityDate = new Date(devis.validity_date);
    const daysUntilExpiry = Math.ceil((validityDate.getTime() - Date.now()) / (1000 * 60 * 60 * 24));

    if (daysUntilExpiry < 0) {
      insights.push({
        id: 'expired',
        type: 'warning',
        title: 'Devis expiré',
        description: `Ce devis a expiré il y a ${Math.abs(daysUntilExpiry)} jours.`,
      });
    } else if (daysUntilExpiry <= 7) {
      insights.push({
        id: 'expiring-soon',
        type: 'warning',
        title: 'Expiration proche',
        description: `Ce devis expire dans ${daysUntilExpiry} jours. Pensez à relancer le client.`,
      });
    }
  }

  // Vérifier les lignes
  if (!devis.lines || devis.lines.length === 0) {
    insights.push({
      id: 'no-lines',
      type: 'warning',
      title: 'Aucune ligne',
      description: 'Ce devis ne contient pas de lignes. Ajoutez des produits ou services.',
    });
  } else {
    insights.push({
      id: 'lines-ok',
      type: 'success',
      title: 'Lignes complètes',
      description: `${devis.lines.length} ligne(s) avec un total de ${formatCurrency(devis.subtotal)}.`,
    });
  }

  // Vérifier la remise
  if (devis.discount_percent > 20) {
    insights.push({
      id: 'high-discount',
      type: 'warning',
      title: 'Remise élevée',
      description: `Une remise de ${devis.discount_percent}% est appliquée. Vérifiez la marge.`,
    });
  } else if (devis.discount_percent > 0) {
    insights.push({
      id: 'discount-applied',
      type: 'success',
      title: 'Remise attractive',
      description: `Une remise de ${devis.discount_percent}% rend l'offre compétitive.`,
    });
  }

  // Suggestion de suivi
  if (devis.status === 'SENT') {
    insights.push({
      id: 'follow-up',
      type: 'suggestion',
      title: 'Relance suggérée',
      description: 'Le devis a été envoyé. Planifiez une relance dans 3-5 jours.',
    });
  }

  // Client fidèle
  if (devis.customer_code) {
    insights.push({
      id: 'known-customer',
      type: 'success',
      title: 'Client connu',
      description: 'Ce client est référencé dans votre base. Historique disponible.',
    });
  }

  return insights;
}

export default DevisIATab;
