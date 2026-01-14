/**
 * AZALSCORE GUARDIAN - Connecteur Panel
 * ======================================
 * Connecte le GuardianPanel au store d'incidents
 */

import React, { useCallback } from 'react';
import { GuardianPanel } from './GuardianPanel';
import {
  useIncidentStore,
  GuardianActions,
} from '@/core/guardian/incident-store';

export const GuardianPanelContainer: React.FC = () => {
  const {
    incidents,
    is_panel_visible,
    is_panel_collapsed,
    togglePanel,
    removeIncident,
    acknowledgeIncident,
    toggleIncidentExpanded,
    clearIncidents,
  } = useIncidentStore();

  const handleGuardianAction = useCallback(async (incidentId: string, action: string) => {
    switch (action) {
      case 'force_logout':
        await GuardianActions.forceLogout(incidentId);
        break;
      case 'refresh_token':
        await GuardianActions.attemptTokenRefresh(incidentId);
        break;
      case 'reload':
        GuardianActions.reloadPage(incidentId);
        break;
      case 'go_back':
        GuardianActions.goBack(incidentId);
        break;
      case 'go_cockpit':
        GuardianActions.goToCockpit(incidentId);
        break;
      default:
        console.warn('[GUARDIAN] Unknown action:', action);
    }
  }, []);

  if (!is_panel_visible || incidents.length === 0) {
    return null;
  }

  return (
    <GuardianPanel
      incidents={incidents}
      isCollapsed={is_panel_collapsed}
      onToggleCollapse={togglePanel}
      onRemoveIncident={removeIncident}
      onAcknowledgeIncident={acknowledgeIncident}
      onToggleExpanded={toggleIncidentExpanded}
      onClearAll={clearIncidents}
      onGuardianAction={handleGuardianAction}
    />
  );
};

export default GuardianPanelContainer;
