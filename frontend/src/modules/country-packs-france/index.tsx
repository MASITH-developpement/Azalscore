/**
 * AZALSCORE Module - Country Packs France
 * Pack France: PCG, TVA, FEC, DSN, RGPD
 *
 * Structure:
 * - types.ts: Re-export types depuis api.ts
 * - api.ts: Types et client API typé
 * - hooks.ts: React Query hooks
 * - constants.ts: Constantes et configurations
 * - components/: Composants UI et vues
 */

import React, { useState } from 'react';
import { PageWrapper } from '@ui/layout';
import {
  TabNav,
  PCGView,
  TVAView,
  FECView,
  DSNView,
  RGPDView,
  DashboardView
} from './components';

// Re-exports
export * from './types';
export * from './hooks';
export * from './constants';
export * from './components';

// ============================================================================
// MAIN MODULE
// ============================================================================

type View = 'dashboard' | 'pcg' | 'tva' | 'fec' | 'dsn' | 'rgpd';

export const CountryPacksFranceModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'pcg', label: 'PCG' },
    { id: 'tva', label: 'TVA' },
    { id: 'fec', label: 'FEC' },
    { id: 'dsn', label: 'DSN' },
    { id: 'rgpd', label: 'RGPD' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'pcg':
        return <PCGView />;
      case 'tva':
        return <TVAView />;
      case 'fec':
        return <FECView />;
      case 'dsn':
        return <DSNView />;
      case 'rgpd':
        return <RGPDView />;
      default:
        return <DashboardView onNavigate={(view) => setCurrentView(view as View)} />;
    }
  };

  return (
    <PageWrapper
      title="Pack France"
      subtitle="Conformite comptable et reglementaire France"
    >
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default CountryPacksFranceModule;
