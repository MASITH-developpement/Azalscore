/**
 * AZALSCORE - Module Consolidation
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const ConsolidationModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Consolidation"
      subtitle="Module consolidation"
    >
      <div className="azals-module-content">
        <p>Module Consolidation - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('consolidation')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const ConsolidationRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<ConsolidationModule />} />
    </Routes>
  );
};

export default ConsolidationRoutes;
