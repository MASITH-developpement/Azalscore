/**
 * AZALSCORE - Module Finance
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const FinanceModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Finance"
      subtitle="Module finance"
    >
      <div className="azals-module-content">
        <p>Module Finance - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('finance')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const FinanceRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<FinanceModule />} />
    </Routes>
  );
};

export default FinanceRoutes;
