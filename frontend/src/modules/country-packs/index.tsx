/**
 * AZALSCORE - Module Country Packs
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const Country_packsModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Country Packs"
      subtitle="Module country-packs"
    >
      <div className="azals-module-content">
        <p>Module Country Packs - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('country_packs')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const Country_packsRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<Country_packsModule />} />
    </Routes>
  );
};

export default Country_packsRoutes;
