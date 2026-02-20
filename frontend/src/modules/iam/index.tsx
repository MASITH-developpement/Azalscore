/**
 * AZALSCORE - Module Iam
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const IamModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Iam"
      subtitle="Module iam"
    >
      <div className="azals-module-content">
        <p>Module Iam - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('iam')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const IamRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<IamModule />} />
    </Routes>
  );
};

export default IamRoutes;
