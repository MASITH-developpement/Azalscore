/**
 * AZALSCORE - Module Enrichment
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const EnrichmentModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Enrichment"
      subtitle="Module enrichment"
    >
      <div className="azals-module-content">
        <p>Module Enrichment - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('enrichment')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const EnrichmentRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<EnrichmentModule />} />
    </Routes>
  );
};

export default EnrichmentRoutes;
