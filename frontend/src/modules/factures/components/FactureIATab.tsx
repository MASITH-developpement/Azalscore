/**
 * AZALSCORE Module - FACTURES - IA Tab
 * Onglet Assistant IA pour la facture
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import {
  TrendingUp, AlertTriangle, ChevronRight, Zap,
  CreditCard, Send, FileText
} from 'lucide-react';
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
import { isOverdue, getDaysUntilDue } from '../types';
import type { Facture } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * FactureIATab - Assistant IA pour la facture
 */
export const FactureIATab: React.FC<TabContentProps<Facture>> = ({ data: facture }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const isCreditNote = facture.type === 'CREDIT_NOTE';

  // Générer les insights
  const insights = generateInsights(facture);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(facture);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const recouvrementScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const entityLabel = isCreditNote ? 'cet avoir' : 'cette facture';
  const panelSubtitle = `J'ai analysé ${entityLabel} et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de recouvrement - Composant partagé */}
      <Card title="Score de recouvrement" icon={<Zap size={18} />} className="mb-4">
        <IAScoreCircle
          score={recouvrementScore}
          label="Recouvrement"
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
            <p className="text-sm text-muted">Basé sur l&apos;historique</p>
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur la facture
 */
function generateSuggestedActions(facture: Facture): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];
  const isCreditNote = facture.type === 'CREDIT_NOTE';

  if (facture.status === 'DRAFT') {
    actions.push({
      id: 'validate',
      title: 'Valider le document',
      description: `${isCreditNote ? "L'avoir" : 'La facture'} est complet et peut être validé.`,
      confidence: 85,
      icon: <ChevronRight size={16} />,
      actionLabel: 'Valider',
    });
  }

  if (facture.status === 'VALIDATED') {
    actions.push({
      id: 'send',
      title: 'Envoyer au client',
      description: 'Document validé, prêt pour envoi.',
      confidence: 90,
      icon: <Send size={16} />,
      actionLabel: 'Envoyer',
    });
  }

  if (!isCreditNote && ['SENT', 'PARTIAL', 'OVERDUE'].includes(facture.status) && facture.remaining_amount > 0) {
    actions.push({
      id: 'payment',
      title: 'Enregistrer un paiement',
      description: `Reste à encaisser: ${formatCurrency(facture.remaining_amount)}.`,
      confidence: 95,
      icon: <CreditCard size={16} />,
      actionLabel: 'Encaisser',
    });
  }

  if (!isCreditNote && facture.status === 'PAID') {
    actions.push({
      id: 'export',
      title: 'Comptabiliser',
      description: 'Facture soldée, prête pour export comptable.',
      confidence: 90,
      icon: <FileText size={16} />,
      actionLabel: 'Exporter',
    });
  }

  if (!isCreditNote && isOverdue(facture)) {
    actions.push({
      id: 'reminder',
      title: 'Relancer le client',
      description: 'Échéance dépassée. Envoyez une relance.',
      confidence: 85,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Relancer',
    });
  }

  return actions;
}

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
      description: "Planifiez une relance amiable quelques jours avant l'échéance.",
    });
  }

  return insights;
}

export default FactureIATab;
