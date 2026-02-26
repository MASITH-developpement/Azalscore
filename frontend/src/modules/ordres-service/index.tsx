/**
 * AZALSCORE Module - ORDRES DE SERVICE (ODS)
 * Gestion des interventions et travaux
 * Flux : CRM → DEV → [ODS] → AFF → FAC/AVO → CPT
 * Numerotation : ODS-YY-MM-XXXX
 */

import React, { useState, useCallback, useEffect } from 'react';

import {
  ODSListView,
  InterventionDetailView,
  ODSFormView,
  DonneursOrdreView,
} from './components';

// Re-export types
export * from './types';

// Re-export hooks
export * from './hooks';

// Re-export components
export * from './components';

// ============================================================
// NAVIGATION
// ============================================================

type ODSView = 'list' | 'detail' | 'form' | 'donneurs-ordre';

interface ODSNavState {
  view: ODSView;
  interventionId?: string;
  isNew?: boolean;
}

// ============================================================
// MODULE PRINCIPAL
// ============================================================

export const OrdresServiceModule: React.FC = () => {
  const [navState, setNavState] = useState<ODSNavState>({ view: 'list' });

  useEffect(() => {
    const handleNavigate = (event: CustomEvent) => {
      const { params } = event.detail || {};
      if (params?.id) {
        setNavState({ view: 'detail', interventionId: params.id });
      }
    };
    const handleNavigateDonneurs = () => {
      setNavState({ view: 'donneurs-ordre' });
    };
    window.addEventListener('azals:navigate:ods', handleNavigate as EventListener);
    window.addEventListener('azals:navigate:ods:donneurs', handleNavigateDonneurs as EventListener);
    return () => {
      window.removeEventListener('azals:navigate:ods', handleNavigate as EventListener);
      window.removeEventListener('azals:navigate:ods:donneurs', handleNavigateDonneurs as EventListener);
    };
  }, []);

  const navigateToList = useCallback(() => setNavState({ view: 'list' }), []);
  const navigateToDetail = useCallback((id: string) => setNavState({ view: 'detail', interventionId: id }), []);
  const navigateToForm = useCallback((id?: string) => setNavState({ view: 'form', interventionId: id, isNew: !id }), []);

  switch (navState.view) {
    case 'detail':
      return (
        <InterventionDetailView
          interventionId={navState.interventionId!}
          onBack={navigateToList}
          onEdit={navigateToForm}
        />
      );
    case 'form':
      return (
        <ODSFormView
          interventionId={navState.interventionId}
          onBack={navState.isNew ? navigateToList : () => navigateToDetail(navState.interventionId!)}
          onSaved={navigateToDetail}
        />
      );
    case 'donneurs-ordre':
      return (
        <DonneursOrdreView
          onBack={navigateToList}
        />
      );
    default:
      return (
        <ODSListView
          onSelectODS={navigateToDetail}
          onCreateODS={() => navigateToForm()}
          onEditODS={navigateToForm}
        />
      );
  }
};

export default OrdresServiceModule;
