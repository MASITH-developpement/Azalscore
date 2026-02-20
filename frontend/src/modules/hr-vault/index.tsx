/**
 * AZALSCORE - Module Hr Vault
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const Hr_vaultModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Hr Vault"
      subtitle="Module hr-vault"
    >
      <div className="azals-module-content">
        <p>Module Hr Vault - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('hr_vault')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const Hr_vaultRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<Hr_vaultModule />} />
    </Routes>
  );
};

export default Hr_vaultRoutes;
