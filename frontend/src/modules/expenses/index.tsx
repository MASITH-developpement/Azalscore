/**
 * AZALSCORE - Module Expenses
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const ExpensesModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Expenses"
      subtitle="Module expenses"
    >
      <div className="azals-module-content">
        <p>Module Expenses - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('expenses')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const ExpensesRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<ExpensesModule />} />
    </Routes>
  );
};

export default ExpensesRoutes;
