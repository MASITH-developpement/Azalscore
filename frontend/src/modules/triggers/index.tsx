/**
 * AZALSCORE - Module Triggers
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const TriggersModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Triggers"
      subtitle="Module triggers"
    >
      <div className="azals-module-content">
        <p>Module Triggers - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('triggers')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const TriggersRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<TriggersModule />} />
    </Routes>
  );
};

export default TriggersRoutes;
