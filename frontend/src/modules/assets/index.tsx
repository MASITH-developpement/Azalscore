/**
 * AZALSCORE - Module Assets
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const AssetsModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Assets"
      subtitle="Module assets"
    >
      <div className="azals-module-content">
        <p>Module Assets - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('assets')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const AssetsRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<AssetsModule />} />
    </Routes>
  );
};

export default AssetsRoutes;
