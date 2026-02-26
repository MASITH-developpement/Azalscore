/**
 * AZALSCORE - Module Odoo Import
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const Odoo_importModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Odoo Import"
      subtitle="Module odoo-import"
    >
      <div className="azals-module-content">
        <p>Module Odoo Import - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('odoo_import')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const Odoo_importRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<Odoo_importModule />} />
    </Routes>
  );
};

export default Odoo_importRoutes;
