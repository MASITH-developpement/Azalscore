/**
 * AZALSCORE Module - Purchases - Invoice IA Tab
 * Onglet Assistant IA pour la facture fournisseur
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ThumbsDown, ChevronRight,
  CheckCircle2, CreditCard, XCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { PurchaseInvoice } from '../types';
import {
  INVOICE_STATUS_CONFIG, formatCurrency,
  canValidateInvoice, canPayInvoice, isOverdue
} from '../types';

/**
 * InvoiceIATab - Assistant IA
 */
export const InvoiceIATab: React.FC<TabContentProps<PurchaseInvoice>> = ({ data: invoice }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(invoice);

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
            J'ai analyse cette facture et identifie{' '}
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
            {invoice.status === 'DRAFT' && canValidateInvoice(invoice) && (
              <SuggestedAction
                title="Valider la facture"
                description="La facture est complete et peut etre validee."
                confidence={95}
                icon={<CheckCircle2 size={16} />}
              />
            )}
            {invoice.status === 'DRAFT' && invoice.lines.length === 0 && (
              <SuggestedAction
                title="Ajouter des lignes"
                description="La facture ne contient aucune ligne."
                confidence={100}
                icon={<AlertTriangle size={16} />}
              />
            )}
            {canPayInvoice(invoice) && (
              <SuggestedAction
                title="Enregistrer un paiement"
                description={isOverdue(invoice.due_date)
                  ? "Attention: cette facture est en retard!"
                  : "La facture est en attente de paiement."}
                confidence={isOverdue(invoice.due_date) ? 100 : 85}
                icon={<CreditCard size={16} />}
              />
            )}
            {invoice.status === 'PAID' && (
              <SuggestedAction
                title="Facture soldee"
                description="Cette facture est integralement payee."
                confidence={100}
                icon={<CheckCircle2 size={16} />}
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
            <p className="text-lg font-medium text-primary">{invoice.lines.length}</p>
            <p className="text-sm text-muted">Lignes de facture</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Total HT</h4>
            <p className="text-lg font-medium text-blue-600">
              {formatCurrency(invoice.total_ht, invoice.currency)}
            </p>
            <p className="text-sm text-muted">Montant hors taxes</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Reste a payer</h4>
            <p className={`text-lg font-medium ${isOverdue(invoice.due_date) ? 'text-red-600' : 'text-orange-600'}`}>
              {formatCurrency(invoice.amount_remaining || invoice.total_ttc, invoice.currency)}
            </p>
            <p className="text-sm text-muted">A regler</p>
          </div>
          <div className="azals-analysis-item">
            <h4>Total TTC</h4>
            <p className="text-lg font-medium text-green-600">
              {formatCurrency(invoice.total_ttc, invoice.currency)}
            </p>
            <p className="text-sm text-muted">Montant total</p>
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
 * Generer les insights bases sur la facture
 */
function generateInsights(invoice: PurchaseInvoice): Insight[] {
  const insights: Insight[] = [];
  const overdue = isOverdue(invoice.due_date);

  // Statut
  if (invoice.status === 'DRAFT') {
    insights.push({
      id: 'draft',
      type: 'suggestion',
      title: 'Facture en brouillon',
      description: 'Validez la facture pour la comptabiliser.',
    });
  } else if (invoice.status === 'VALIDATED') {
    insights.push({
      id: 'validated',
      type: 'success',
      title: 'Facture validee',
      description: 'En attente de paiement.',
    });
  } else if (invoice.status === 'PAID') {
    insights.push({
      id: 'paid',
      type: 'success',
      title: 'Facture payee',
      description: 'Facture integralement reglee.',
    });
  } else if (invoice.status === 'PARTIAL') {
    insights.push({
      id: 'partial',
      type: 'suggestion',
      title: 'Paiement partiel',
      description: 'Un solde reste a payer.',
    });
  } else if (invoice.status === 'CANCELLED') {
    insights.push({
      id: 'cancelled',
      type: 'warning',
      title: 'Facture annulee',
      description: 'Cette facture a ete annulee.',
    });
  }

  // Echeance
  if (overdue && invoice.status !== 'PAID' && invoice.status !== 'CANCELLED') {
    insights.push({
      id: 'overdue',
      type: 'warning',
      title: 'Facture en retard',
      description: 'L\'echeance de paiement est depassee!',
    });
  } else if (invoice.due_date) {
    insights.push({
      id: 'has-due-date',
      type: 'success',
      title: 'Echeance definie',
      description: 'Date de paiement planifiee.',
    });
  }

  // Lignes
  if (invoice.lines.length > 0) {
    insights.push({
      id: 'has-lines',
      type: 'success',
      title: 'Lignes presentes',
      description: `${invoice.lines.length} ligne(s) de facture.`,
    });
  } else {
    insights.push({
      id: 'no-lines',
      type: 'warning',
      title: 'Aucune ligne',
      description: 'Ajoutez au moins une ligne de facture.',
    });
  }

  // Fournisseur
  insights.push({
    id: 'has-supplier',
    type: 'success',
    title: 'Fournisseur identifie',
    description: `${invoice.supplier_code} - ${invoice.supplier_name}`,
  });

  // Reference
  if (invoice.supplier_reference) {
    insights.push({
      id: 'has-reference',
      type: 'success',
      title: 'Reference fournisseur',
      description: 'Numero de facture fournisseur renseigne.',
    });
  } else {
    insights.push({
      id: 'no-reference',
      type: 'suggestion',
      title: 'Reference manquante',
      description: 'Ajoutez la reference de la facture fournisseur.',
    });
  }

  // Commande liee
  if (invoice.order_id) {
    insights.push({
      id: 'linked-order',
      type: 'success',
      title: 'Commande liee',
      description: 'Facture liee a une commande.',
    });
  }

  return insights;
}

export default InvoiceIATab;
