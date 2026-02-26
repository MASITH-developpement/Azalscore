/**
 * AZALSCORE Module - Purchases - Invoice IA Tab
 * Onglet Assistant IA pour la facture fournisseur
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, AlertTriangle, CheckCircle2, CreditCard } from 'lucide-react';
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
import {
  canValidateInvoice, canPayInvoice, isOverdue
} from '../types';
import type { PurchaseInvoice } from '../types';
import type { TabContentProps } from '@ui/standards';

// Composants partagés IA (AZA-NF-REUSE)

/**
 * InvoiceIATab - Assistant IA
 */
export const InvoiceIATab: React.FC<TabContentProps<PurchaseInvoice>> = ({ data: invoice }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(invoice);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(invoice);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const conformityScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cette facture et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

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
function generateSuggestedActions(invoice: PurchaseInvoice): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (invoice.status === 'DRAFT' && canValidateInvoice(invoice)) {
    actions.push({
      id: 'validate',
      title: 'Valider la facture',
      description: 'La facture est complète et peut être validée.',
      confidence: 95,
      icon: <CheckCircle2 size={16} />,
      actionLabel: 'Valider',
    });
  }

  if (invoice.status === 'DRAFT' && invoice.lines.length === 0) {
    actions.push({
      id: 'add-lines',
      title: 'Ajouter des lignes',
      description: 'La facture ne contient aucune ligne.',
      confidence: 100,
      icon: <AlertTriangle size={16} />,
      actionLabel: 'Ajouter',
    });
  }

  if (canPayInvoice(invoice)) {
    actions.push({
      id: 'pay',
      title: 'Enregistrer un paiement',
      description: isOverdue(invoice.due_date)
        ? 'Attention: cette facture est en retard!'
        : 'La facture est en attente de paiement.',
      confidence: isOverdue(invoice.due_date) ? 100 : 85,
      icon: <CreditCard size={16} />,
      actionLabel: 'Payer',
    });
  }

  if (invoice.status === 'PAID') {
    actions.push({
      id: 'paid',
      title: 'Facture soldée',
      description: 'Cette facture est intégralement payée.',
      confidence: 100,
      icon: <CheckCircle2 size={16} />,
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur la facture
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
