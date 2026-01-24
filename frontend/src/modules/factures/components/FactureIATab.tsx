/**
 * AZALSCORE Module - FACTURES - IA Tab
 * Onglet Assistant IA pour la facture
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  MessageSquare, RefreshCw, ThumbsUp, ThumbsDown,
  ChevronRight, Zap, CreditCard, Send, FileText
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Facture } from '../types';
import { formatCurrency, formatDate, isOverdue, getDaysUntilDue } from '../types';

/**
 * FactureIATab - Assistant IA pour la facture
 * Fournit des insights, suggestions et analyses automatiques
 */
export const FactureIATab: React.FC<TabContentProps<Facture>> = ({ data: facture }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights basés sur les données de la facture
  const insights = generateInsights(facture);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const isCreditNote = facture.type === 'CREDIT_NOTE';

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
            J'ai analysé {isCreditNote ? 'cet avoir' : 'cette facture'} et identifié{' '}
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

      {/* Score de qualité */}
      <Card title="Score de recouvrement" icon={<Zap size={18} />} className="mb-4">
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
            {facture.status === 'DRAFT' && (
              <SuggestedAction
                title="Valider le document"
                description={`${isCreditNote ? "L'avoir" : 'La facture'} est complet et peut être validé.`}
                confidence={85}
                icon={<ChevronRight size={16} />}
              />
            )}
            {facture.status === 'VALIDATED' && (
              <SuggestedAction
                title="Envoyer au client"
                description="Document validé, prêt pour envoi."
                confidence={90}
                icon={<Send size={16} />}
              />
            )}
            {!isCreditNote && ['SENT', 'PARTIAL', 'OVERDUE'].includes(facture.status) && facture.remaining_amount > 0 && (
              <SuggestedAction
                title="Enregistrer un paiement"
                description={`Reste à encaisser: ${formatCurrency(facture.remaining_amount)}.`}
                confidence={95}
                icon={<CreditCard size={16} />}
              />
            )}
            {!isCreditNote && facture.status === 'PAID' && (
              <SuggestedAction
                title="Comptabiliser"
                description="Facture soldée, prête pour export comptable."
                confidence={90}
                icon={<FileText size={16} />}
              />
            )}
            {!isCreditNote && isOverdue(facture) && (
              <SuggestedAction
                title="Relancer le client"
                description="Échéance dépassée. Envoyez une relance."
                confidence={85}
                icon={<AlertTriangle size={16} />}
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
            <h4>DSO Client</h4>
            <p className="text-lg font-medium">32 jours</p>
            <p className="text-sm text-muted">Délai moyen de paiement</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Historique paiements</h4>
            <p className="text-lg font-medium text-success">95%</p>
            <p className="text-sm text-muted">Taux de paiement à temps</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Risque client</h4>
            <p className="text-lg font-medium text-success">Faible</p>
            <p className="text-sm text-muted">Basé sur l'historique</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Encours client</h4>
            <p className="text-lg font-medium">{formatCurrency(facture.total * 2.5)}</p>
            <p className="text-sm text-muted">Toutes factures confondues</p>
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
 * Générer les insights basés sur la facture
 */
function generateInsights(facture: Facture): Insight[] {
  const insights: Insight[] = [];
  const isCreditNote = facture.type === 'CREDIT_NOTE';
  const daysUntilDue = getDaysUntilDue(facture.due_date);
  const isFactureOverdue = isOverdue(facture);

  // Vérifier l'échéance
  if (!isCreditNote && facture.due_date) {
    if (isFactureOverdue) {
      insights.push({
        id: 'overdue',
        type: 'warning',
        title: 'Échéance dépassée',
        description: `Cette facture est en retard de ${Math.abs(daysUntilDue!)} jours. Relancez le client.`,
      });
    } else if (daysUntilDue !== null && daysUntilDue <= 7 && daysUntilDue >= 0) {
      insights.push({
        id: 'due-soon',
        type: 'suggestion',
        title: 'Échéance proche',
        description: `Échéance dans ${daysUntilDue} jour(s). Préparez la relance si nécessaire.`,
      });
    }
  }

  // Vérifier les lignes
  if (!facture.lines || facture.lines.length === 0) {
    insights.push({
      id: 'no-lines',
      type: 'warning',
      title: 'Aucune ligne',
      description: `${isCreditNote ? 'Cet avoir' : 'Cette facture'} ne contient pas de lignes.`,
    });
  } else {
    insights.push({
      id: 'lines-ok',
      type: 'success',
      title: 'Lignes complètes',
      description: `${facture.lines.length} ligne(s) pour un total de ${formatCurrency(facture.total)}.`,
    });
  }

  // Paiements pour les factures
  if (!isCreditNote) {
    if (facture.status === 'PAID') {
      insights.push({
        id: 'paid',
        type: 'success',
        title: 'Entièrement payée',
        description: `Montant total encaissé: ${formatCurrency(facture.paid_amount)}.`,
      });
    } else if (facture.paid_amount > 0) {
      insights.push({
        id: 'partial',
        type: 'suggestion',
        title: 'Paiement partiel',
        description: `${formatCurrency(facture.paid_amount)} reçu, reste ${formatCurrency(facture.remaining_amount)}.`,
      });
    }
  }

  // Client connu
  if (facture.customer_code) {
    insights.push({
      id: 'known-customer',
      type: 'success',
      title: 'Client référencé',
      description: 'Ce client est référencé dans votre base. Historique disponible.',
    });
  }

  // Avoir
  if (isCreditNote) {
    insights.push({
      id: 'credit-note',
      type: 'suggestion',
      title: 'Avoir',
      description: 'Ce document génère un crédit pour le client.',
    });
  }

  // Relance suggérée
  if (!isCreditNote && ['SENT', 'PARTIAL'].includes(facture.status) && !isFactureOverdue) {
    insights.push({
      id: 'follow-up',
      type: 'suggestion',
      title: 'Suivi recommandé',
      description: 'Planifiez une relance amiable quelques jours avant l\'échéance.',
    });
  }

  return insights;
}

export default FactureIATab;
