/**
 * AZALSCORE - Module Commercial
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const CommercialModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Commercial"
      subtitle="Module commercial"
    >
      <div className="azals-module-content">
        <p>Module Commercial - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('commercial')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const CommercialRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<CommercialModule />} />
    </Routes>
  );
};

export default CommercialRoutes;
