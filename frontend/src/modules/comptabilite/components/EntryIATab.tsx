/**
 * AZALSCORE Module - Comptabilite - IA Tab
 * Onglet Assistant IA pour l'ecriture comptable
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ThumbsDown, ChevronRight,
  CheckCircle2, XCircle, BookOpen
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Entry } from '../types';
import {
  formatCurrency, isEntryBalanced, canValidateEntry, canPostEntry,
  ENTRY_STATUS_CONFIG
} from '../types';

/**
 * EntryIATab - Assistant IA
 */
export const EntryIATab: React.FC<TabContentProps<Entry>> = ({ data: entry }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(entry);

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
            J'ai analyse cette ecriture comptable et identifie{' '}
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

      {/* Score de conformite */}
      <Card title="Score de conformite" icon={<TrendingUp size={18} />} className="mb-4">
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
            {entry.status === 'DRAFT' && canValidateEntry(entry) && (
              <SuggestedAction
                title="Valider l'ecriture"
                description="L'ecriture est equilibree et peut etre validee."
                confidence={95}
                icon={<CheckCircle2 size={16} />}
              />
            )}
            {entry.status === 'DRAFT' && !isEntryBalanced(entry) && (
              <SuggestedAction
                title="Equilibrer l'ecriture"
                description="Corrigez le desequilibre avant validation."
                confidence={100}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {canPostEntry(entry) && (
              <SuggestedAction
                title="Comptabiliser l'ecriture"
                description="L'ecriture validee peut etre comptabilisee."
                confidence={90}
                icon={<BookOpen size={16} />}
              />
            )}
            {entry.status === 'DRAFT' && entry.lines.length === 0 && (
              <SuggestedAction
                title="Ajouter des lignes"
                description="L'ecriture ne contient aucune ligne."
                confidence={100}
                icon={<AlertTriangle size={16} />}
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
            <p className="text-lg font-medium text-primary">{entry.lines.length}</p>
            <p className="text-sm text-muted">Lignes d'ecriture</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Comptes</h4>
            <p className="text-lg font-medium">
              {new Set(entry.lines.map(l => l.account_id)).size}
            </p>
            <p className="text-sm text-muted">Comptes touches</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Total mouvement</h4>
            <p className="text-lg font-medium text-blue-600">
              {formatCurrency(entry.total_debit)}
            </p>
            <p className="text-sm text-muted">Debit = Credit</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Equilibre</h4>
            <p className={`text-lg font-medium ${isEntryBalanced(entry) ? 'text-success' : 'text-danger'}`}>
              {isEntryBalanced(entry) ? 'Oui' : 'Non'}
            </p>
            <p className="text-sm text-muted">
              {isEntryBalanced(entry) ? 'Ecriture equilibree' : 'A corriger'}
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
 * Generer les insights bases sur l'ecriture
 */
function generateInsights(entry: Entry): Insight[] {
  const insights: Insight[] = [];
  const statusConfig = ENTRY_STATUS_CONFIG[entry.status];

  // Statut
  if (entry.status === 'DRAFT') {
    insights.push({
      id: 'draft',
      type: 'suggestion',
      title: 'Ecriture en brouillon',
      description: 'Validez l\'ecriture une fois terminee.',
    });
  } else if (entry.status === 'VALIDATED') {
    insights.push({
      id: 'validated',
      type: 'success',
      title: 'Ecriture validee',
      description: 'Prete a etre comptabilisee.',
    });
  } else if (entry.status === 'POSTED') {
    insights.push({
      id: 'posted',
      type: 'success',
      title: 'Ecriture comptabilisee',
      description: 'Definitivement enregistree dans les comptes.',
    });
  } else if (entry.status === 'CANCELLED') {
    insights.push({
      id: 'cancelled',
      type: 'warning',
      title: 'Ecriture annulee',
      description: 'Cette ecriture a ete annulee.',
    });
  }

  // Equilibre
  if (isEntryBalanced(entry)) {
    insights.push({
      id: 'balanced',
      type: 'success',
      title: 'Ecriture equilibree',
      description: 'Debit = Credit, conforme aux principes comptables.',
    });
  } else {
    insights.push({
      id: 'unbalanced',
      type: 'warning',
      title: 'Ecriture desequilibree',
      description: `Ecart de ${formatCurrency(Math.abs(entry.total_debit - entry.total_credit))} a corriger.`,
    });
  }

  // Lignes
  if (entry.lines.length > 0) {
    insights.push({
      id: 'has-lines',
      type: 'success',
      title: 'Lignes presentes',
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
      title: 'Journal affecte',
      description: `Journal: ${entry.journal_code}`,
    });
  }

  // Description
  if (entry.description && entry.description.length > 10) {
    insights.push({
      id: 'has-description',
      type: 'success',
      title: 'Libelle renseigne',
      description: 'Le libelle permet d\'identifier l\'operation.',
    });
  } else {
    insights.push({
      id: 'short-description',
      type: 'suggestion',
      title: 'Libelle court',
      description: 'Ajoutez plus de details pour faciliter la recherche.',
    });
  }

  // Nombre de comptes
  const uniqueAccounts = new Set(entry.lines.map(l => l.account_id)).size;
  if (uniqueAccounts >= 2) {
    insights.push({
      id: 'multi-accounts',
      type: 'success',
      title: 'Mouvements multiples',
      description: `${uniqueAccounts} comptes differents impactes.`,
    });
  }

  return insights;
}

export default EntryIATab;
