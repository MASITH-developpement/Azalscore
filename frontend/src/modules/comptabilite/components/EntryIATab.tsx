/**
 * AZALSCORE Module - Comptabilité - IA Tab
 * Onglet Assistant IA pour l'écriture comptable
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, CheckCircle2, AlertTriangle, BookOpen } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Entry } from '../types';
import { formatCurrency } from '@/utils/formatters';
import {
  isEntryBalanced, canValidateEntry, canPostEntry,
  ENTRY_STATUS_CONFIG
} from '../types';

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
 * EntryIATab - Assistant IA
 */
export const EntryIATab: React.FC<TabContentProps<Entry>> = ({ data: entry }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(entry);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(entry);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const conformityScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cette écriture comptable et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de conformité - Composant partagé */}
      <Card title="Score de conformité" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={conformityScore}
          label="Conformité"
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
            <h4>Lignes</h4>
            <p className="text-lg font-medium text-primary">{entry.lines.length}</p>
            <p className="text-sm text-muted">Lignes d'écriture</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Comptes</h4>
            <p className="text-lg font-medium">
              {new Set(entry.lines.map(l => l.account_id)).size}
            </p>
            <p className="text-sm text-muted">Comptes touchés</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Total mouvement</h4>
            <p className="text-lg font-medium text-blue-600">
              {formatCurrency(entry.total_debit)}
            </p>
            <p className="text-sm text-muted">Débit = Crédit</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Équilibre</h4>
            <p className={`text-lg font-medium ${isEntryBalanced(entry) ? 'text-success' : 'text-danger'}`}>
              {isEntryBalanced(entry) ? 'Oui' : 'Non'}
            </p>
            <p className="text-sm text-muted">
              {isEntryBalanced(entry) ? 'Écriture équilibrée' : 'À corriger'}
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
 * Générer les actions suggérées basées sur l'écriture
 */
function generateSuggestedActions(entry: Entry): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (entry.status === 'DRAFT' && canValidateEntry(entry)) {
    actions.push({
      id: 'validate',
      title: "Valider l'écriture",
      description: "L'écriture est équilibrée et peut être validée.",
      confidence: 95,
      icon: <CheckCircle2 size={16} />,
      actionLabel: 'Valider',
    });
  }

  if (entry.status === 'DRAFT' && !isEntryBalanced(entry)) {
    actions.push({
      id: 'balance',
      title: "Équilibrer l'écriture",
      description: 'Corrigez le déséquilibre avant validation.',
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Corriger',
    });
  }

  if (canPostEntry(entry)) {
    actions.push({
      id: 'post',
      title: "Comptabiliser l'écriture",
      description: "L'écriture validée peut être comptabilisée.",
      confidence: 90,
      icon: <BookOpen size={16} />,
      actionLabel: 'Comptabiliser',
    });
  }

  if (entry.status === 'DRAFT' && entry.lines.length === 0) {
    actions.push({
      id: 'add-lines',
      title: 'Ajouter des lignes',
      description: "L'écriture ne contient aucune ligne.",
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Ajouter',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur l'écriture
 */
function generateInsights(entry: Entry): Insight[] {
  const insights: Insight[] = [];
  const statusConfig = ENTRY_STATUS_CONFIG[entry.status];

  // Statut
  if (entry.status === 'DRAFT') {
    insights.push({
      id: 'draft',
      type: 'suggestion',
      title: 'Écriture en brouillon',
      description: "Validez l'écriture une fois terminée.",
    });
  } else if (entry.status === 'VALIDATED') {
    insights.push({
      id: 'validated',
      type: 'success',
      title: 'Écriture validée',
      description: 'Prête à être comptabilisée.',
    });
  } else if (entry.status === 'POSTED') {
    insights.push({
      id: 'posted',
      type: 'success',
      title: 'Écriture comptabilisée',
      description: 'Définitivement enregistrée dans les comptes.',
    });
  } else if (entry.status === 'CANCELLED') {
    insights.push({
      id: 'cancelled',
      type: 'warning',
      title: 'Écriture annulée',
      description: 'Cette écriture a été annulée.',
    });
  }

  // Équilibre
  if (isEntryBalanced(entry)) {
    insights.push({
      id: 'balanced',
      type: 'success',
      title: 'Écriture équilibrée',
      description: 'Débit = Crédit, conforme aux principes comptables.',
    });
  } else {
    insights.push({
      id: 'unbalanced',
      type: 'warning',
      title: 'Écriture déséquilibrée',
      description: `Écart de ${formatCurrency(Math.abs(entry.total_debit - entry.total_credit))} à corriger.`,
    });
  }

  // Lignes
  if (entry.lines.length > 0) {
    insights.push({
      id: 'has-lines',
      type: 'success',
      title: 'Lignes présentes',
      description: `${entry.lines.length} ligne(s) saisie(s).`,
    });
  } else {
    insights.push({
      id: 'no-lines',
      type: 'warning',
      title: 'Aucune ligne',
      description: 'Ajoutez au moins une ligne.',
    });
  }

  // Journal
  if (entry.journal_code) {
    insights.push({
      id: 'has-journal',
      type: 'success',
      title: 'Journal affecté',
      description: `Journal: ${entry.journal_code}`,
    });
  }

  // Description
  if (entry.description && entry.description.length > 10) {
    insights.push({
      id: 'has-description',
      type: 'success',
      title: 'Libellé renseigné',
      description: "Le libellé permet d'identifier l'opération.",
    });
  } else {
    insights.push({
      id: 'short-description',
      type: 'suggestion',
      title: 'Libellé court',
      description: 'Ajoutez plus de détails pour faciliter la recherche.',
    });
  }

  // Nombre de comptes
  const uniqueAccounts = new Set(entry.lines.map(l => l.account_id)).size;
  if (uniqueAccounts >= 2) {
    insights.push({
      id: 'multi-accounts',
      type: 'success',
      title: 'Mouvements multiples',
      description: `${uniqueAccounts} comptes différents impactés.`,
    });
  }

  return insights;
}

export default EntryIATab;
