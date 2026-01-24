/**
 * AZALSCORE Module - Invoicing - IA Tab
 * Onglet Assistant IA pour le document
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ThumbsDown, ChevronRight,
  Clock, CreditCard, Send, AlertCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Document } from '../types';
import {
  formatCurrency, formatPercent, getDaysUntilDue, isDocumentOverdue,
  canValidateDocument, canTransformDocument, DOCUMENT_TYPE_CONFIG, TRANSFORM_WORKFLOW
} from '../types';

/**
 * InvoicingIATab - Assistant IA
 */
export const InvoicingIATab: React.FC<TabContentProps<Document>> = ({ data: doc }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(doc);

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
            J'ai analyse ce {DOCUMENT_TYPE_CONFIG[doc.type].label.toLowerCase()} et identifie{' '}
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

      {/* Score de sante du document */}
      <Card title="Score de sante" icon={<TrendingUp size={18} />} className="mb-4">
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
            {doc.status === 'DRAFT' && canValidateDocument(doc) && (
              <SuggestedAction
                title="Valider le document"
                description="Le document est complet et pret a etre valide."
                confidence={95}
                icon={<ThumbsUp size={16} />}
              />
            )}
            {doc.status === 'VALIDATED' && doc.type !== 'INVOICE' && canTransformDocument(doc) && (
              <SuggestedAction
                title={TRANSFORM_WORKFLOW[doc.type]?.label || 'Transformer'}
                description={`Creer ${DOCUMENT_TYPE_CONFIG[TRANSFORM_WORKFLOW[doc.type]?.target || 'INVOICE'].label.toLowerCase()}.`}
                confidence={90}
                icon={<ChevronRight size={16} />}
              />
            )}
            {doc.status === 'VALIDATED' && !doc.sent_at && (
              <SuggestedAction
                title="Envoyer au client"
                description="Le document n'a pas encore ete envoye."
                confidence={85}
                icon={<Send size={16} />}
              />
            )}
            {doc.type === 'INVOICE' && isDocumentOverdue(doc) && (
              <SuggestedAction
                title="Relancer le client"
                description="La facture est en retard de paiement."
                confidence={95}
                icon={<AlertCircle size={16} />}
              />
            )}
            {doc.type === 'QUOTE' && getDaysUntilDue(doc) !== null && (getDaysUntilDue(doc) || 0) < 7 && (
              <SuggestedAction
                title="Relancer le prospect"
                description="Le devis arrive bientot a echeance."
                confidence={80}
                icon={<Clock size={16} />}
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
            <p className="text-lg font-medium text-primary">{doc.lines.length}</p>
            <p className="text-sm text-muted">Lignes de document</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Panier moyen</h4>
            <p className="text-lg font-medium">
              {doc.lines.length > 0
                ? formatCurrency(doc.subtotal / doc.lines.length, doc.currency)
                : '-'}
            </p>
            <p className="text-sm text-muted">Par ligne</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Remise</h4>
            <p className={`text-lg font-medium ${doc.discount_percent > 0 ? 'text-orange' : ''}`}>
              {formatPercent(doc.discount_percent)}
            </p>
            <p className="text-sm text-muted">
              {doc.discount_amount > 0 ? formatCurrency(doc.discount_amount, doc.currency) : 'Aucune'}
            </p>
          </div>
          {doc.stats?.margin_percent !== undefined && (
            <div className="azals-analysis-item">
              <h4>Marge</h4>
              <p className={`text-lg font-medium ${(doc.stats.margin_percent || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                {formatPercent(doc.stats.margin_percent)}
              </p>
              <p className="text-sm text-muted">Taux de marge</p>
            </div>
          )}
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
 * Generer les insights bases sur le document
 */
function generateInsights(doc: Document): Insight[] {
  const insights: Insight[] = [];
  const typeConfig = DOCUMENT_TYPE_CONFIG[doc.type];

  // Statut
  if (doc.status === 'DRAFT') {
    insights.push({
      id: 'draft',
      type: 'suggestion',
      title: 'Document en brouillon',
      description: 'Pensez a valider le document une fois termine.',
    });
  } else if (doc.status === 'VALIDATED') {
    insights.push({
      id: 'validated',
      type: 'success',
      title: 'Document valide',
      description: 'Le document est verrouille et pret a etre envoye.',
    });
  } else if (doc.status === 'PAID') {
    insights.push({
      id: 'paid',
      type: 'success',
      title: 'Paiement recu',
      description: 'La facture a ete reglee.',
    });
  }

  // Lignes
  if (doc.lines.length > 0) {
    insights.push({
      id: 'has-lines',
      type: 'success',
      title: 'Lignes presentes',
      description: `${doc.lines.length} ligne(s) dans le document.`,
    });
  } else {
    insights.push({
      id: 'no-lines',
      type: 'warning',
      title: 'Aucune ligne',
      description: 'Ajoutez au moins une ligne au document.',
    });
  }

  // Montant
  if (doc.total > 0) {
    insights.push({
      id: 'has-amount',
      type: 'success',
      title: 'Montant valide',
      description: `Total: ${formatCurrency(doc.total, doc.currency)}`,
    });
  }

  // Remise importante
  if (doc.discount_percent > 20) {
    insights.push({
      id: 'high-discount',
      type: 'warning',
      title: 'Remise importante',
      description: `Remise de ${formatPercent(doc.discount_percent)} appliquee.`,
    });
  }

  // Retard de paiement (factures)
  if (doc.type === 'INVOICE' && isDocumentOverdue(doc)) {
    const days = Math.abs(getDaysUntilDue(doc) || 0);
    insights.push({
      id: 'overdue',
      type: 'warning',
      title: 'Facture en retard',
      description: `Echeance depassee de ${days} jour(s).`,
    });
  }

  // Echeance proche (devis)
  if (doc.type === 'QUOTE' && doc.validity_date) {
    const days = getDaysUntilDue({ ...doc, due_date: doc.validity_date });
    if (days !== null && days <= 7 && days >= 0) {
      insights.push({
        id: 'expiring-soon',
        type: 'warning',
        title: 'Validite proche',
        description: days === 0 ? "Le devis expire aujourd'hui." : `Le devis expire dans ${days} jour(s).`,
      });
    }
  }

  // Transformation possible
  if (canTransformDocument(doc)) {
    const targetType = TRANSFORM_WORKFLOW[doc.type]?.target;
    if (targetType) {
      insights.push({
        id: 'can-transform',
        type: 'suggestion',
        title: 'Transformation possible',
        description: `Vous pouvez creer ${DOCUMENT_TYPE_CONFIG[targetType].label.toLowerCase()}.`,
      });
    }
  }

  // Marge faible
  if (doc.stats?.margin_percent !== undefined && doc.stats.margin_percent < 10) {
    insights.push({
      id: 'low-margin',
      type: 'warning',
      title: 'Marge faible',
      description: `Taux de marge de seulement ${formatPercent(doc.stats.margin_percent)}.`,
    });
  }

  // Client
  if (doc.customer_name) {
    insights.push({
      id: 'has-customer',
      type: 'success',
      title: 'Client identifie',
      description: doc.customer_name,
    });
  }

  return insights;
}

export default InvoicingIATab;
