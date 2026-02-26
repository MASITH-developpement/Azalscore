/**
 * AZALSCORE Module - Comptabilité Automatisée
 *
 * Module de comptabilité automatisée piloté par IA.
 * Une facture reçue = la comptabilité se fait toute seule.
 *
 * TROIS VUES DISTINCTES:
 * - Dirigeant: Piloter & décider (ZÉRO jargon comptable)
 * - Assistante: Centraliser & organiser (JAMAIS comptabiliser)
 * - Expert-comptable: Contrôler, valider (exceptions uniquement)
 *
 * PRINCIPES:
 * - ZÉRO saisie comptable manuelle
 * - ZÉRO export par défaut
 * - Automatisation maximale par IA
 * - L'humain valide par exception uniquement
 * - Banque en mode PULL (jamais PUSH)
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@core/auth';
import { CapabilityGuard } from '@core/capabilities';

// Views
import { AssistanteDashboard } from './components/AssistanteDashboard';
import { BankConnections } from './components/BankConnections';
import { DirigeantDashboard } from './components/DirigeantDashboard';
import { DocumentDetail } from './components/DocumentDetail';
import { ExpertDashboard } from './components/ExpertDashboard';
import { ReconciliationView } from './components/ReconciliationView';

// ============================================================
// VIEW ROUTER - REDIRECTS BASED ON USER ROLE
// ============================================================

const ViewRouter: React.FC = () => {
  const { user } = useAuthStore();

  // Determine default view based on role
  const getDefaultView = () => {
    if (!user) return 'dirigeant';

    switch (user.role) {
      case 'DIRIGEANT':
      case 'ADMIN':
        return 'dirigeant';
      case 'ASSISTANTE':
      case 'SECRETAIRE':
        return 'assistante';
      case 'EXPERT_COMPTABLE':
      case 'COMPTABLE':
        return 'expert';
      default:
        return 'dirigeant';
    }
  };

  return <Navigate to={getDefaultView()} replace />;
};

// ============================================================
// MODULE ROUTES
// ============================================================

export const AutomatedAccountingRoutes: React.FC = () => (
  <Routes>
    {/* Default redirect based on role */}
    <Route index element={<ViewRouter />} />

    {/* Vue Dirigeant */}
    <Route
      path="dirigeant"
      element={
        <CapabilityGuard capability="accounting.dirigeant.view">
          <DirigeantDashboard />
        </CapabilityGuard>
      }
    />

    {/* Vue Assistante */}
    <Route
      path="assistante"
      element={
        <CapabilityGuard capability="accounting.assistante.view">
          <AssistanteDashboard />
        </CapabilityGuard>
      }
    />

    {/* Vue Expert-comptable */}
    <Route
      path="expert"
      element={
        <CapabilityGuard capability="accounting.expert.view">
          <ExpertDashboard />
        </CapabilityGuard>
      }
    />

    {/* Document detail (shared) */}
    <Route
      path="documents/:documentId"
      element={<DocumentDetail />}
    />

    {/* Bank connections (dirigeant only) */}
    <Route
      path="bank"
      element={
        <CapabilityGuard capability="accounting.bank.manage">
          <BankConnections />
        </CapabilityGuard>
      }
    />

    {/* Reconciliation (expert only) */}
    <Route
      path="reconciliation"
      element={
        <CapabilityGuard capability="accounting.reconciliation.manage">
          <ReconciliationView />
        </CapabilityGuard>
      }
    />
  </Routes>
);

export default AutomatedAccountingRoutes;
