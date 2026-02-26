/**
 * AZALSCORE - Module Esignature
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const EsignatureModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Esignature"
      subtitle="Module esignature"
    >
      <div className="azals-module-content">
        <p>Module Esignature - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('esignature')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const EsignatureRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<EsignatureModule />} />
    </Routes>
  );
};

export default EsignatureRoutes;
