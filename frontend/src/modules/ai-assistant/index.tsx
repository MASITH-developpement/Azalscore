/**
 * AZALSCORE - Module Ai Assistant
 * Structure conforme AZA-FE-ENF
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useCapabilities } from '@core/capabilities';
import { PageWrapper } from '@ui/layout';

// ============================================================
// MAIN MODULE COMPONENT
// ============================================================

const Ai_assistantModule: React.FC = () => {
  const { capabilities } = useCapabilities();

  return (
    <PageWrapper
      title="Ai Assistant"
      subtitle="Module ai-assistant"
    >
      <div className="azals-module-content">
        <p>Module Ai Assistant - Interface en cours de développement</p>
        <p>Capacités disponibles: {capabilities.filter(c => c.startsWith('ai_assistant')).length}</p>
      </div>
    </PageWrapper>
  );
};

// ============================================================
// ROUTES
// ============================================================

const Ai_assistantRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<Ai_assistantModule />} />
    </Routes>
  );
};

export default Ai_assistantRoutes;
