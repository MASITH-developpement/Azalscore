/**
 * AZALSCORE - Module Email
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const EmailModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Email"
      subtitle="Module email"
    >
      <div className="azals-module-content">
        <p>Module Email - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('email')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const EmailRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<EmailModule />} />
    </Routes>
  );
};

export default EmailRoutes;
