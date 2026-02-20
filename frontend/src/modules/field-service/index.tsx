/**
 * AZALSCORE - Module Field Service
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const Field_serviceModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Field Service"
      subtitle="Module field-service"
    >
      <div className="azals-module-content">
        <p>Module Field Service - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('field_service')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const Field_serviceRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<Field_serviceModule />} />
    </Routes>
  );
};

export default Field_serviceRoutes;
