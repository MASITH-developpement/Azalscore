/**
 * AZALSCORE Module - Partners - PartnerDetailView
 * Vue détail standardisée BaseViewStandard pour tous les types de partenaires
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { User, Users, ShoppingCart, FileText, Clock, Sparkles, Shield } from 'lucide-react';
import { PageWrapper } from '@ui/layout';
import {
  BaseViewStandard,
  type TabDefinition,
  type InfoBarItem,
  type SidebarSection,
  type ActionDefinition,
  type SemanticColor
} from '@ui/standards';
import { formatCurrency } from '@/utils/formatters';
import { usePartner } from '../hooks';
import {
  PartnerInfoTab,
  PartnerContactsTab,
  PartnerTransactionsTab,
  PartnerDocumentsTab,
  PartnerHistoryTab,
  PartnerIATab,
  PartnerRiskTab
} from './index';
import {
  PARTNER_TYPE_CONFIG,
  CLIENT_TYPE_CONFIG,
  getPartnerAgeDays,
  getContactsCount
} from '../types';
import type { Partner, Client } from '../types';

export interface PartnerDetailViewProps {
  partnerType: 'client' | 'supplier' | 'contact';
}

export const PartnerDetailView: React.FC<PartnerDetailViewProps> = ({ partnerType }) => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: partner, isLoading, error, refetch } = usePartner(partnerType, id);

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">Chargement du partenaire...</div>
      </PageWrapper>
    );
  }

  if (error || !partner) {
    return (
      <PageWrapper title="Erreur">
        <div className="azals-alert azals-alert--danger">
          Partenaire introuvable
        </div>
      </PageWrapper>
    );
  }

  // Configuration des onglets
  const tabs: TabDefinition<Partner>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <User size={16} />,
      component: PartnerInfoTab
    },
    {
      id: 'contacts',
      label: 'Contacts',
      icon: <Users size={16} />,
      badge: getContactsCount(partner),
      component: PartnerContactsTab
    },
    {
      id: 'transactions',
      label: 'Transactions',
      icon: <ShoppingCart size={16} />,
      component: PartnerTransactionsTab
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={16} />,
      badge: partner.documents?.length,
      component: PartnerDocumentsTab
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <Clock size={16} />,
      component: PartnerHistoryTab
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: PartnerIATab
    },
    {
      id: 'risk',
      label: 'Risque',
      icon: <Shield size={16} />,
      component: PartnerRiskTab
    }
  ];

  // Barre d'info KPIs
  const typeConfig = PARTNER_TYPE_CONFIG[partner.type];
  const clientTypeConfig = partner.type === 'client' && (partner as Client).client_type
    ? CLIENT_TYPE_CONFIG[(partner as Client).client_type]
    : null;

  const infoBarItems: InfoBarItem[] = [
    {
      id: 'type',
      label: 'Type',
      value: typeConfig?.label || partner.type,
      valueColor: (typeConfig?.color || 'gray') as SemanticColor
    },
    {
      id: 'status',
      label: 'Statut',
      value: partner.is_active ? 'Actif' : 'Inactif',
      valueColor: partner.is_active ? 'green' : 'gray'
    }
  ];

  // Ajouter des KPIs spécifiques selon le type
  if (partner.type === 'client') {
    const client = partner as Client;
    if (clientTypeConfig) {
      infoBarItems.push({
        id: 'client_type',
        label: 'Categorie',
        value: clientTypeConfig.label,
        valueColor: (clientTypeConfig.color || 'gray') as SemanticColor
      });
    }
    if (client.total_orders !== undefined) {
      infoBarItems.push({
        id: 'orders',
        label: 'Commandes',
        value: String(client.total_orders),
        valueColor: 'blue'
      });
    }
    if (client.total_revenue !== undefined) {
      infoBarItems.push({
        id: 'revenue',
        label: 'CA Total',
        value: formatCurrency(client.total_revenue),
        valueColor: 'green'
      });
    }
  }

  // Ajouter ancienneté
  const ageDays = getPartnerAgeDays(partner);
  infoBarItems.push({
    id: 'age',
    label: 'Anciennete',
    value: ageDays > 365 ? `${Math.floor(ageDays / 365)} an(s)` : `${ageDays}j`,
    valueColor: ageDays > 365 ? 'green' : 'gray'
  });

  // Sidebar
  const sidebarSections: SidebarSection[] = [
    {
      id: 'summary',
      title: 'Resume',
      items: [
        { id: 'code', label: 'Code', value: partner.code || '-' },
        { id: 'email', label: 'Email', value: partner.email || '-' },
        { id: 'phone', label: 'Telephone', value: partner.phone || partner.mobile || '-' },
        { id: 'city', label: 'Ville', value: partner.city || '-' }
      ]
    }
  ];

  // Section financière pour clients
  if (partner.type === 'client') {
    const client = partner as Client;
    sidebarSections.push({
      id: 'financial',
      title: 'Donnees financieres',
      items: [
        { id: 'revenue', label: 'CA Total', value: formatCurrency(client.total_revenue || 0), highlight: true },
        { id: 'orders', label: 'Commandes', value: String(client.total_orders || 0) },
        { id: 'outstanding', label: 'Encours', value: formatCurrency(client.stats?.total_outstanding || 0) }
      ]
    });
  }

  // Actions header
  const headerActions: ActionDefinition[] = [
    {
      id: 'edit',
      label: 'Modifier',
      variant: 'secondary',
      capability: `partners.${partnerType}s.edit`,
      onClick: () => navigate(`/partners/${partnerType}s/${id}/edit`)
    }
  ];

  // Statut du partenaire
  const status = {
    label: partner.is_active ? 'Actif' : 'Inactif',
    color: partner.is_active ? 'green' as const : 'gray' as const
  };

  return (
    <BaseViewStandard<Partner>
      title={partner.name}
      subtitle={partner.code ? `Code: ${partner.code}` : undefined}
      status={status}
      data={partner}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
    />
  );
};

// Wrappers typés pour chaque type de partenaire
export const ClientDetailView: React.FC = () => <PartnerDetailView partnerType="client" />;
export const SupplierDetailView: React.FC = () => <PartnerDetailView partnerType="supplier" />;
export const ContactDetailView: React.FC = () => <PartnerDetailView partnerType="contact" />;

export default PartnerDetailView;
