/**
 * AZALSCORE Module - Invoicing - IA Tab
 * Onglet Assistant IA pour le document
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  TrendingUp, AlertTriangle, ThumbsUp, ChevronRight,
  Clock, Send, AlertCircle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Document } from '../types';
import {
  getDaysUntilDue, isDocumentOverdue,
  canValidateDocument, canTransformDocument, DOCUMENT_TYPE_CONFIG, TRANSFORM_WORKFLOW
} from '../types';
import { formatCurrency, formatPercent } from '@/utils/formatters';

// Composants partagés IA (AZA-NF-REUSE)
import {
  IAPanelHeader,
  IAScoreCircle,
  InsightList,
  SuggestedActionList,
  type Insight as SharedInsight,
  type SuggestedActionData,
} from '@ui/components/shared-ia';

/**
 * InvoicingIATab - Assistant IA
 */
export const InvoicingIATab: React.FC<TabContentProps<Document>> = ({ data: doc }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(doc);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(doc);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const healthScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce ${DOCUMENT_TYPE_CONFIG[doc.type].label.toLowerCase()} et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de santé - Composant partagé */}
      <Card title="Score de santé" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={healthScore}
          label="Santé"
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur le document
 */
function generateSuggestedActions(doc: Document): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (doc.status === 'DRAFT' && canValidateDocument(doc)) {
    actions.push({
      id: 'validate',
      title: 'Valider le document',
      description: 'Le document est complet et prêt à être validé.',
      confidence: 95,
      icon: <ThumbsUp size={16} />,
      actionLabel: 'Valider',
    });
  }

  if (doc.status === 'VALIDATED' && doc.type !== 'INVOICE' && canTransformDocument(doc)) {
    const target = TRANSFORM_WORKFLOW[doc.type]?.target || 'INVOICE';
    actions.push({
      id: 'transform',
      title: TRANSFORM_WORKFLOW[doc.type]?.label || 'Transformer',
      description: `Créer ${DOCUMENT_TYPE_CONFIG[target].label.toLowerCase()}.`,
      confidence: 90,
      icon: <ChevronRight size={16} />,
      actionLabel: 'Créer',
    });
  }

  if (doc.status === 'VALIDATED' && !doc.sent_at) {
    actions.push({
      id: 'send',
      title: 'Envoyer au client',
      description: "Le document n'a pas encore été envoyé.",
      confidence: 85,
      icon: <Send size={16} />,
      actionLabel: 'Envoyer',
    });
  }

  if (doc.type === 'INVOICE' && isDocumentOverdue(doc)) {
    actions.push({
      id: 'remind',
      title: 'Relancer le client',
      description: 'La facture est en retard de paiement.',
      confidence: 95,
      icon: <AlertCircle size={16} />,
      actionLabel: 'Relancer',
    });
  }

  if (doc.type === 'QUOTE' && getDaysUntilDue(doc) !== null && (getDaysUntilDue(doc) || 0) < 7) {
    actions.push({
      id: 'remind-quote',
      title: 'Relancer le prospect',
      description: 'Le devis arrive bientôt à échéance.',
      confidence: 80,
      icon: <Clock size={16} />,
      actionLabel: 'Relancer',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le document
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
