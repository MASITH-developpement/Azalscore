/**
 * AZALSCORE - Module Quality
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const QualityModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Quality"
      subtitle="Module quality"
    >
      <div className="azals-module-content">
        <p>Module Quality - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('quality')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const QualityRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<QualityModule />} />
    </Routes>
  );
};

export default QualityRoutes;
