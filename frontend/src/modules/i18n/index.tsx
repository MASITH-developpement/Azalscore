/**
 * AZALSCORE - Module I18n
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { PageWrapper } from '@ui/layout';
import { useCapabilities } from '@core/capabilities';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const I18nModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="I18n"
      subtitle="Module i18n"
    >
      <div className="azals-module-content">
        <p>Module I18n - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('i18n')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const I18nRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<I18nModule />} />
    </Routes>
  );
};

export default I18nRoutes;
