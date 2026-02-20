/**
 * AZALSCORE - Module Stripe Integration
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const Stripe_integrationModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Stripe Integration"
      subtitle="Module stripe-integration"
    >
      <div className="azals-module-content">
        <p>Module Stripe Integration - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('stripe_integration')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const Stripe_integrationRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<Stripe_integrationModule />} />
    </Routes>
  );
};

export default Stripe_integrationRoutes;
