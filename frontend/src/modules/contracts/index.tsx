/**
 * AZALSCORE - Module Contracts
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const ContractsModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Contracts"
      subtitle="Module contracts"
    >
      <div className="azals-module-content">
        <p>Module Contracts - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('contracts')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const ContractsRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<ContractsModule />} />
    </Routes>
  );
};

export default ContractsRoutes;
