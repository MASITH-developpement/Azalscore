/**
 * AZALSCORE - Module Backup
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const BackupModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Backup"
      subtitle="Module backup"
    >
      <div className="azals-module-content">
        <p>Module Backup - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('backup')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const BackupRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<BackupModule />} />
    </Routes>
  );
};

export default BackupRoutes;
