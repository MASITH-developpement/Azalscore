/**
 * AZALSCORE - Module Guardian
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const GuardianModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Guardian"
      subtitle="Module guardian"
    >
      <div className="azals-module-content">
        <p>Module Guardian - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('guardian')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const GuardianRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<GuardianModule />} />
    </Routes>
  );
};

export default GuardianRoutes;
