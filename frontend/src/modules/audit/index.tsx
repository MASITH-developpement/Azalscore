/**
 * AZALSCORE - Module Audit
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const AuditModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Audit"
      subtitle="Module audit"
    >
      <div className="azals-module-content">
        <p>Module Audit - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('audit')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const AuditRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<AuditModule />} />
    </Routes>
  );
};

export default AuditRoutes;
