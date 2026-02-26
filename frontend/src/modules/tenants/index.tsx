/**
 * AZALSCORE - Module Tenants
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const TenantsModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Tenants"
      subtitle="Module tenants"
    >
      <div className="azals-module-content">
        <p>Module Tenants - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('tenants')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const TenantsRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<TenantsModule />} />
    </Routes>
  );
};

export default TenantsRoutes;
