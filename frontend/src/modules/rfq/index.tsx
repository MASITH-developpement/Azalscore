/**
 * AZALSCORE - Module Rfq
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const RfqModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Rfq"
      subtitle="Module rfq"
    >
      <div className="azals-module-content">
        <p>Module Rfq - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('rfq')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const RfqRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<RfqModule />} />
    </Routes>
  );
};

export default RfqRoutes;
