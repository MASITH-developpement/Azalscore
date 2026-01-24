/**
 * AZALSCORE Module - Partners - IA Tab
 * Onglet Assistant IA pour le partenaire
 */

import React, { useState } from 'react';
import {
  Sparkles, TrendingUp, AlertTriangle, Lightbulb,
  RefreshCw, ThumbsUp, ThumbsDown, ChevronRight,
  UserCheck, Star, ShoppingCart, Mail, Phone
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Partner, Client } from '../types';
import {
  formatCurrency, getPartnerAgeDays, hasContacts, hasDocuments,
  getContactsCount, CLIENT_TYPE_CONFIG
} from '../types';

/**
 * PartnerIATab - Assistant IA
 */
export const PartnerIATab: React.FC<TabContentProps<Partner>> = ({ data: partner }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const insights = generateInsights(partner);

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
            J'ai analyse cette fiche partenaire et identifie{' '}
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

      {/* Score de completude */}
      <Card title="Score de completude" icon={<TrendingUp size={18} />} className="mb-4">
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
            {!partner.email && (
              <SuggestedAction
                title="Ajouter un email"
                description="L'email est essentiel pour les communications."
                confidence={95}
                icon={<Mail size={16} />}
              />
            )}
            {!partner.phone && (
              <SuggestedAction
                title="Ajouter un telephone"
                description="Facilite le contact direct."
                confidence={90}
                icon={<Phone size={16} />}
              />
            )}
            {!hasContacts(partner) && partner.type !== 'contact' && (
              <SuggestedAction
                title="Ajouter des contacts"
                description="Identifiez les interlocuteurs cles."
                confidence={85}
                icon={<UserCheck size={16} />}
              />
            )}
            {partner.type === 'client' && !(partner as Client).total_orders && (
              <SuggestedAction
                title="Premiere commande"
                description="Ce client n'a pas encore commande."
                confidence={80}
                icon={<ShoppingCart size={16} />}
              />
            )}
            {getPartnerAgeDays(partner) > 365 && partner.type === 'client' && (
              <SuggestedAction
                title="Client fidele"
                description="Envisagez un programme de fidelite."
                confidence={75}
                icon={<Star size={16} />}
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
              Personnes associees
            </p>
          </div>
          <div className="azals-analysis-item">
            <h4>Anciennete</h4>
            <p className="text-lg font-medium text-primary">
              {getPartnerAgeDays(partner)}j
            </p>
            <p className="text-sm text-muted">
              Depuis la creation
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
 * Generer les insights bases sur le partenaire
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
      description: 'Cette fiche est desactivee.',
    });
  }

  // Coordonnees
  if (partner.email) {
    insights.push({
      id: 'has-email',
      type: 'success',
      title: 'Email renseigne',
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
      title: 'Telephone renseigne',
      description: 'Contact telephonique possible.',
    });
  }

  // Adresse
  if (partner.city || partner.address_line1 || partner.address) {
    insights.push({
      id: 'has-address',
      type: 'success',
      title: 'Adresse renseignee',
      description: 'Localisation connue.',
    });
  } else {
    insights.push({
      id: 'no-address',
      type: 'suggestion',
      title: 'Adresse manquante',
      description: 'Completez l\'adresse pour les livraisons.',
    });
  }

  // Contacts
  if (hasContacts(partner)) {
    insights.push({
      id: 'has-contacts',
      type: 'success',
      title: 'Contacts associes',
      description: `${getContactsCount(partner)} contact(s) enregistre(s).`,
    });
  } else if (partner.type !== 'contact') {
    insights.push({
      id: 'no-contacts',
      type: 'suggestion',
      title: 'Pas de contacts',
      description: 'Ajoutez des interlocuteurs.',
    });
  }

  // Client specifique
  if (partner.type === 'client') {
    const client = partner as Client;
    if (client.total_orders && client.total_orders > 0) {
      insights.push({
        id: 'has-orders',
        type: 'success',
        title: 'Client actif',
        description: `${client.total_orders} commande(s) passee(s).`,
      });
    }
    if (client.client_type === 'VIP') {
      insights.push({
        id: 'vip',
        type: 'success',
        title: 'Client VIP',
        description: 'Traitement prioritaire recommande.',
      });
    }
    if (client.client_type === 'CHURNED') {
      insights.push({
        id: 'churned',
        type: 'warning',
        title: 'Client perdu',
        description: 'Envisagez une action de reactivation.',
      });
    }
  }

  // Anciennete
  const ageDays = getPartnerAgeDays(partner);
  if (ageDays > 365) {
    insights.push({
      id: 'loyal',
      type: 'success',
      title: 'Partenaire fidele',
      description: `Dans la base depuis plus d'un an.`,
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
