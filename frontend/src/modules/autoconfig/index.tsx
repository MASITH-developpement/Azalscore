/**
 * AZALSCORE - Module Autoconfig
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const AutoconfigModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Autoconfig"
      subtitle="Module autoconfig"
    >
      <div className="azals-module-content">
        <p>Module Autoconfig - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('autoconfig')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const AutoconfigRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<AutoconfigModule />} />
    </Routes>
  );
};

export default AutoconfigRoutes;
