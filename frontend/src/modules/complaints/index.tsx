/**
 * AZALSCORE - Module Complaints
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const ComplaintsModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Complaints"
      subtitle="Module complaints"
    >
      <div className="azals-module-content">
        <p>Module Complaints - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('complaints')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const ComplaintsRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<ComplaintsModule />} />
    </Routes>
  );
};

export default ComplaintsRoutes;
