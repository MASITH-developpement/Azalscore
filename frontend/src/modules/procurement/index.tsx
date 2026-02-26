/**
 * AZALSCORE - Module Procurement
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const ProcurementModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Procurement"
      subtitle="Module procurement"
    >
      <div className="azals-module-content">
        <p>Module Procurement - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('procurement')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const ProcurementRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<ProcurementModule />} />
    </Routes>
  );
};

export default ProcurementRoutes;
