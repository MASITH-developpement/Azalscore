/**
 * AZALSCORE - Module Qc
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const QcModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Qc"
      subtitle="Module qc"
    >
      <div className="azals-module-content">
        <p>Module Qc - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('qc')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const QcRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<QcModule />} />
    </Routes>
  );
};

export default QcRoutes;
