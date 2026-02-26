/**
 * AZALS MODULE GAP-086 - Integration Hub
 * =======================================
 *
 * Module de gestion des integrations tierces:
 * - Dashboard avec KPIs et statistiques
 * - Liste des connecteurs disponibles
 * - Gestion des connexions actives
 * - Monitoring des synchronisations
 * - Resolution des conflits
 * - Configuration des webhooks
 */

import React, { useState, useCallback } from 'react';

import {
  IntegrationDashboard,
  ConnectorsList,
  ConnectionsList,
  ConnectionDetail,
  ConnectionForm,
  ExecutionsList,
  ConflictsList,
} from './components';

// Re-export types
export * from './types';

// Re-export hooks
export * from './hooks';

// Re-export components
export * from './components';

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type IntegrationView =
  | 'dashboard'
  | 'connectors'
  | 'connections'
  | 'connection-detail'
  | 'connection-form'
  | 'executions'
  | 'conflicts';

interface IntegrationNavState {
  view: IntegrationView;
  connectionId?: string;
  connectorType?: string;
  isNew?: boolean;
}

export const IntegrationModule: React.FC = () => {
  const [navState, setNavState] = useState<IntegrationNavState>({ view: 'dashboard' });

  const navigateToDashboard = useCallback(() => setNavState({ view: 'dashboard' }), []);
  const navigateToConnectors = useCallback(() => setNavState({ view: 'connectors' }), []);
  const navigateToConnections = useCallback(() => setNavState({ view: 'connections' }), []);
  const navigateToExecutions = useCallback(() => setNavState({ view: 'executions' }), []);
  const navigateToConflicts = useCallback(() => setNavState({ view: 'conflicts' }), []);

  const navigateToConnectionDetail = useCallback((id: string) => {
    setNavState({ view: 'connection-detail', connectionId: id });
  }, []);

  const navigateToConnectionForm = useCallback((id?: string, connectorType?: string) => {
    setNavState({
      view: 'connection-form',
      connectionId: id,
      connectorType,
      isNew: !id,
    });
  }, []);

  const handleSelectConnector = useCallback((connectorType: string) => {
    setNavState({
      view: 'connection-form',
      connectorType,
      isNew: true,
    });
  }, []);

  switch (navState.view) {
    case 'connectors':
      return (
        <ConnectorsList
          onSelectConnector={handleSelectConnector}
          onBack={navigateToDashboard}
        />
      );

    case 'connections':
      return (
        <ConnectionsList
          onSelectConnection={navigateToConnectionDetail}
          onCreateConnection={() => navigateToConnectionForm()}
          onBack={navigateToDashboard}
        />
      );

    case 'connection-detail':
      return (
        <ConnectionDetail
          connectionId={navState.connectionId!}
          onBack={navigateToConnections}
          onEdit={() => navigateToConnectionForm(navState.connectionId)}
        />
      );

    case 'connection-form':
      return (
        <ConnectionForm
          connectionId={navState.connectionId}
          connectorType={navState.connectorType}
          onBack={
            navState.isNew
              ? navState.connectorType
                ? navigateToConnectors
                : navigateToDashboard
              : () => navigateToConnectionDetail(navState.connectionId!)
          }
          onSaved={navigateToConnectionDetail}
        />
      );

    case 'executions':
      return <ExecutionsList onBack={navigateToDashboard} />;

    case 'conflicts':
      return <ConflictsList onBack={navigateToDashboard} />;

    default:
      return (
        <IntegrationDashboard
          onNavigateToConnectors={navigateToConnectors}
          onNavigateToConnections={navigateToConnections}
          onNavigateToExecutions={navigateToExecutions}
          onNavigateToConflicts={navigateToConflicts}
          onSelectConnection={navigateToConnectionDetail}
          onCreateConnection={() => navigateToConnectionForm()}
        />
      );
  }
};

export default IntegrationModule;
