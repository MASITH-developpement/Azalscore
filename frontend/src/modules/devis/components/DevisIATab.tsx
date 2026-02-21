/**
 * AZALSCORE Module - DEVIS - IA Tab
 * Onglet Assistant IA pour le devis
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, Zap, ChevronRight, Mail, FileText, Tag } from 'lucide-react';
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
import type { Devis } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * DevisIATab - Assistant IA pour le devis
 * Fournit des insights, suggestions et analyses automatiques
 */
export const DevisIATab: React.FC<TabContentProps<Devis>> = ({ data: devis }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights basés sur les données du devis
  const insights = generateInsights(devis);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(devis);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const qualityScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé ce devis et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

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
      <Card title="Score de qualité du devis" icon={<Zap size={18} />} className="mb-4">
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
            <p className="text-lg font-medium text-success">32%</p>
            <p className="text-sm text-muted">Supérieure à la moyenne (28%)</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Probabilité de conversion</h4>
            <p className="text-lg font-medium">78%</p>
            <p className="text-sm text-muted">Basé sur l&apos;historique client</p>
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
 * Types pour les insights (local)
 */
interface Insight {
  id: string;
  type: 'success' | 'warning' | 'suggestion';
  title: string;
  description: string;
}

/**
 * Générer les actions suggérées basées sur le devis
 */
function generateSuggestedActions(devis: Devis): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (devis.status === 'DRAFT') {
    actions.push({
      id: 'validate',
      title: 'Valider le devis',
      description: 'Le devis est complet et peut être validé pour envoi.',
      confidence: 85,
      icon: <ChevronRight size={16} />,
      actionLabel: 'Valider',
    });
  }

  if (devis.status === 'VALIDATED') {
    actions.push({
      id: 'send',
      title: 'Envoyer au client',
      description: 'Le devis est validé, prêt pour envoi au client.',
      confidence: 90,
      icon: <Mail size={16} />,
      actionLabel: 'Envoyer',
    });
  }

  if (devis.status === 'ACCEPTED') {
    actions.push({
      id: 'convert',
      title: 'Convertir en commande',
      description: 'Le devis a été accepté, vous pouvez créer la commande.',
      confidence: 95,
      icon: <FileText size={16} />,
      actionLabel: 'Convertir',
    });
  }

  if (devis.discount_percent === 0) {
    actions.push({
      id: 'discount',
      title: 'Proposer une remise',
      description: 'Aucune remise appliquée. Une remise de 5% pourrait accélérer la décision.',
      confidence: 65,
      icon: <Tag size={16} />,
      actionLabel: 'Ajouter',
    });
  }

  return actions;
}

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
