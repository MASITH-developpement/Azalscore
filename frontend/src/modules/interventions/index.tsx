/**
 * AZALSCORE Module - INTERVENTIONS
 * Gestion des interventions terrain
 *
 * Structure:
 * - api.ts: React Query hooks
 * - types.ts: Types et configurations
 * - constants.ts: Constantes UI
 * - hooks/: Workflow actions hooks
 * - components/: Composants UI
 */

import React, { useState } from 'react';
import { PageWrapper } from '@ui/layout';
import {
  InterventionsDashboard,
  InterventionsListView,
  InterventionFormView,
  PlanningView,
  DonneursOrdreView,
} from './components';

// Re-exports
export * from './types';
export * from './api';
export * from './constants';
export * from './components';

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'interventions' | 'planning' | 'donneurs-ordre' | 'form';

export const InterventionsModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [editInterventionId, setEditInterventionId] = useState<string | undefined>(undefined);

  const navigateToForm = (interventionId?: string) => {
    setEditInterventionId(interventionId);
    setCurrentView('form');
  };

  const navigateToList = () => {
    setEditInterventionId(undefined);
    setCurrentView('interventions');
  };

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'interventions', label: 'Interventions' },
    { id: 'planning', label: 'Planning' },
    { id: 'donneurs-ordre', label: 'Donneurs d\'ordre' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'form':
        return (
          <InterventionFormView
            interventionId={editInterventionId}
            onBack={navigateToList}
            onSaved={() => navigateToList()}
          />
        );
      case 'interventions':
        return (
          <InterventionsListView
            onNewIntervention={() => navigateToForm()}
            onEditIntervention={(id) => navigateToForm(id)}
          />
        );
      case 'planning':
        return <PlanningView />;
      case 'donneurs-ordre':
        return <DonneursOrdreView />;
      default:
        return (
          <InterventionsDashboard
            onNavigateToList={() => setCurrentView('interventions')}
            onNavigateToPlanning={() => setCurrentView('planning')}
          />
        );
    }
  };

  // Form view renders its own PageWrapper
  if (currentView === 'form') {
    return renderContent();
  }

  return (
    <PageWrapper title="Interventions" subtitle="Gestion des interventions terrain">
      <div className="azals-tab-nav">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`azals-tab-nav__item ${currentView === tab.id ? 'azals-tab-nav__item--active' : ''}`}
            onClick={() => setCurrentView(tab.id as View)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default InterventionsModule;
