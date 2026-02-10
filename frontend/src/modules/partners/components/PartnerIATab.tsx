/**
 * AZALSCORE Module - Partners - IA Tab
 * Onglet Assistant IA pour le partenaire
 *
 * Conforme AZA-NF-REUSE: Utilise les composants partagés shared-ia
 */

import React, { useState } from 'react';
import { TrendingUp, UserCheck, Star, ShoppingCart, Mail, Phone } from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Partner, Client } from '../types';
import { formatCurrency } from '@/utils/formatters';
import {
  getPartnerAgeDays, hasContacts, hasDocuments,
  getContactsCount, CLIENT_TYPE_CONFIG
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
 * PartnerIATab - Assistant IA
 */
export const PartnerIATab: React.FC<TabContentProps<Partner>> = ({ data: partner }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Générer les insights
  const insights = generateInsights(partner);
  const sharedInsights: SharedInsight[] = insights.map(i => ({
    id: i.id,
    type: i.type,
    title: i.title,
    description: i.description,
  }));

  // Générer les actions suggérées
  const suggestedActions = generateSuggestedActions(partner);

  // Calcul du score
  const positiveCount = insights.filter(i => i.type === 'success').length;
  const warningCount = insights.filter(i => i.type === 'warning').length;
  const suggestionCount = insights.filter(i => i.type === 'suggestion').length;
  const completenessScore = Math.round((positiveCount / Math.max(insights.length, 1)) * 100);

  const handleRefreshAnalysis = () => {
    setIsAnalyzing(true);
    setTimeout(() => setIsAnalyzing(false), 2000);
  };

  const panelSubtitle = `J'ai analysé cette fiche partenaire et identifié ${insights.length} points d'attention.${warningCount > 0 ? ` (${warningCount} alertes)` : ''}`;

  return (
    <div className="azals-std-tab-content">
      {/* En-tête IA - Composant partagé */}
      <IAPanelHeader
        title="Assistant AZALSCORE IA"
        subtitle={panelSubtitle}
        onRefresh={handleRefreshAnalysis}
        isLoading={isAnalyzing}
      />

      {/* Score de complétude - Composant partagé */}
      <Card title="Score de complétude" icon={<TrendingUp size={18} />} className="mb-4">
        <IAScoreCircle
          score={completenessScore}
          label="Complétude"
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
            <h4>Type</h4>
            <p className="text-lg font-medium text-primary">
              {partner.type === 'client' ? 'Client' : partner.type === 'supplier' ? 'Fournisseur' : 'Contact'}
            </p>
            {partner.type === 'client' && (partner as Client).client_type && (
              <p className={`text-sm text-${CLIENT_TYPE_CONFIG[(partner as Client).client_type]?.color || 'muted'}`}>
                {CLIENT_TYPE_CONFIG[(partner as Client).client_type]?.label}
              </p>
            )}
          </div>
          <div className="azals-analysis-item">
            <h4>Contacts</h4>
            <p className="text-lg font-medium">
              {getContactsCount(partner)}
            </p>
            <p className="text-sm text-muted">
              Personnes associées
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Ancienneté</h4>
            <p className="text-lg font-medium text-primary">
              {getPartnerAgeDays(partner)}j
            </p>
            <p className="text-sm text-muted">
              Depuis la création
            </p>
          </div>
          {partner.type === 'client' && (
            <div className="azals-analysis-item">
              <h4>CA Total</h4>
              <p className="text-lg font-medium text-success">
                {formatCurrency((partner as Client).total_revenue || 0)}
              </p>
              <p className="text-sm text-muted">
                {(partner as Client).total_orders || 0} commande(s)
              </p>
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
 * Générer les actions suggérées basées sur le partenaire
 */
function generateSuggestedActions(partner: Partner): SuggestedActionData[] {
  const actions: SuggestedActionData[] = [];

  if (!partner.email) {
    actions.push({
      id: 'add-email',
      title: 'Ajouter un email',
      description: "L'email est essentiel pour les communications.",
      confidence: 95,
      icon: <Mail size={16} />,
      actionLabel: 'Modifier',
    });
  }

  if (!partner.phone) {
    actions.push({
      id: 'add-phone',
      title: 'Ajouter un téléphone',
      description: 'Facilite le contact direct.',
      confidence: 90,
      icon: <Phone size={16} />,
      actionLabel: 'Modifier',
    });
  }

  if (!hasContacts(partner) && partner.type !== 'contact') {
    actions.push({
      id: 'add-contacts',
      title: 'Ajouter des contacts',
      description: 'Identifiez les interlocuteurs clés.',
      confidence: 85,
      icon: <UserCheck size={16} />,
      actionLabel: 'Ajouter',
    });
  }

  if (partner.type === 'client' && !(partner as Client).total_orders) {
    actions.push({
      id: 'first-order',
      title: 'Première commande',
      description: "Ce client n'a pas encore commandé.",
      confidence: 80,
      icon: <ShoppingCart size={16} />,
      actionLabel: 'Créer',
    });
  }

  if (getPartnerAgeDays(partner) > 365 && partner.type === 'client') {
    actions.push({
      id: 'loyalty',
      title: 'Client fidèle',
      description: 'Envisagez un programme de fidélité.',
      confidence: 75,
      icon: <Star size={16} />,
      actionLabel: 'Voir',
    });
  }

  return actions;
}

/**
 * Générer les insights basés sur le partenaire
 */
function generateInsights(partner: Partner): Insight[] {
  const insights: Insight[] = [];

  // Statut actif
  if (partner.is_active) {
    insights.push({
      id: 'active',
      type: 'success',
      title: 'Partenaire actif',
      description: 'La fiche est active et utilisable.',
    });
  } else {
    insights.push({
      id: 'inactive',
      type: 'warning',
      title: 'Partenaire inactif',
      description: 'Cette fiche est désactivée.',
    });
  }

  // Coordonnées
  if (partner.email) {
    insights.push({
      id: 'has-email',
      type: 'success',
      title: 'Email renseigné',
      description: 'Contact possible par email.',
    });
  } else {
    insights.push({
      id: 'no-email',
      type: 'warning',
      title: 'Email manquant',
      description: 'Aucun email de contact.',
    });
  }

  if (partner.phone || partner.mobile) {
    insights.push({
      id: 'has-phone',
      type: 'success',
      title: 'Téléphone renseigné',
      description: 'Contact téléphonique possible.',
    });
  }

  // Adresse
  if (partner.city || partner.address_line1 || partner.address) {
    insights.push({
      id: 'has-address',
      type: 'success',
      title: 'Adresse renseignée',
      description: 'Localisation connue.',
    });
  } else {
    insights.push({
      id: 'no-address',
      type: 'suggestion',
      title: 'Adresse manquante',
      description: "Complétez l'adresse pour les livraisons.",
    });
  }

  // Contacts
  if (hasContacts(partner)) {
    insights.push({
      id: 'has-contacts',
      type: 'success',
      title: 'Contacts associés',
      description: `${getContactsCount(partner)} contact(s) enregistré(s).`,
    });
  } else if (partner.type !== 'contact') {
    insights.push({
      id: 'no-contacts',
      type: 'suggestion',
      title: 'Pas de contacts',
      description: 'Ajoutez des interlocuteurs.',
    });
  }

  // Client spécifique
  if (partner.type === 'client') {
    const client = partner as Client;
    if (client.total_orders && client.total_orders > 0) {
      insights.push({
        id: 'has-orders',
        type: 'success',
        title: 'Client actif',
        description: `${client.total_orders} commande(s) passée(s).`,
      });
    }
    if (client.client_type === 'VIP') {
      insights.push({
        id: 'vip',
        type: 'success',
        title: 'Client VIP',
        description: 'Traitement prioritaire recommandé.',
      });
    }
    if (client.client_type === 'CHURNED') {
      insights.push({
        id: 'churned',
        type: 'warning',
        title: 'Client perdu',
        description: 'Envisagez une action de réactivation.',
      });
    }
  }

  // Ancienneté
  const ageDays = getPartnerAgeDays(partner);
  if (ageDays > 365) {
    insights.push({
      id: 'loyal',
      type: 'success',
      title: 'Partenaire fidèle',
      description: "Dans la base depuis plus d'un an.",
    });
  } else if (ageDays < 30) {
    insights.push({
      id: 'new',
      type: 'suggestion',
      title: 'Nouveau partenaire',
      description: 'Assurez un bon suivi initial.',
    });
  }

  return insights;
}

export default PartnerIATab;
