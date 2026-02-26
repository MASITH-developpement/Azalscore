/**
 * AZALSCORE - Module Broadcast
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const BroadcastModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Broadcast"
      subtitle="Module broadcast"
    >
      <div className="azals-module-content">
        <p>Module Broadcast - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('broadcast')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const BroadcastRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<BroadcastModule />} />
    </Routes>
  );
};

export default BroadcastRoutes;
