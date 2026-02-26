/**
 * AZALSCORE - Module Publications Réseaux Sociaux
 * ================================================
 *
 * Module de création et gestion des publications sur les réseaux sociaux
 * pour générer des leads vers azalscore.com.
 *
 * Conformité: AZA-FE-002, AZA-FE-003, AZA-FE-004
 */

import React, { useState } from 'react';
import { BaseViewStandard } from '@/ui-engine/standards/BaseViewStandard';

// Composants
import { Dashboard } from './components/Dashboard';
import { PostsList } from './components/PostsList';
import { LeadsList } from './components/LeadsList';

/**
 * Module Principal - Publications & Leads Réseaux Sociaux
 *
 * Fonctionnalités:
 * - Tableau de bord avec KPIs
 * - Création et programmation de publications
 * - Gestion des leads générés
 * - Tracking UTM automatique
 */
export default function SocialPublicationsModule() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const handleNavigate = (tab: string) => {
    setActiveTab(tab);
  };

  return (
    <BaseViewStandard
      title="Publications & Leads"
      data={{}}
      view="list"
      defaultTab={activeTab}
      onTabChange={setActiveTab}
      tabs={[
        {
          id: 'dashboard',
          label: 'Tableau de bord',
          content: <Dashboard onNavigate={handleNavigate} />,
        },
        {
          id: 'posts',
          label: 'Publications',
          content: <PostsList />,
        },
        {
          id: 'leads',
          label: 'Leads',
          content: <LeadsList />,
        },
      ]}
    />
  );
}

// Export nommé pour compatibilité
export { SocialPublicationsModule };
