/**
 * AZALSCORE - Module Timesheet
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const TimesheetModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Timesheet"
      subtitle="Module timesheet"
    >
      <div className="azals-module-content">
        <p>Module Timesheet - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('timesheet')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const TimesheetRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<TimesheetModule />} />
    </Routes>
  );
};

export default TimesheetRoutes;
