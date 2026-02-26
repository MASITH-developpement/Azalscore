/**
 * AZALSCORE - Module Website
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const WebsiteModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Website"
      subtitle="Module website"
    >
      <div className="azals-module-content">
        <p>Module Website - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('website')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const WebsiteRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<WebsiteModule />} />
    </Routes>
  );
};

export default WebsiteRoutes;
