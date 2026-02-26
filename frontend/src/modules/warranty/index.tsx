/**
 * AZALSCORE - Module Warranty
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const WarrantyModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Warranty"
      subtitle="Module warranty"
    >
      <div className="azals-module-content">
        <p>Module Warranty - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('warranty')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const WarrantyRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<WarrantyModule />} />
    </Routes>
  );
};

export default WarrantyRoutes;
