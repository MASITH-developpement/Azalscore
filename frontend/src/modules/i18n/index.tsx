/**
 * AZALSCORE - Module I18N (Internationalisation)
 * ================================================
 *
 * Module complet d'internationalisation avec:
 * - Dashboard de couverture traduction
 * - Gestion des langues
 * - Gestion des traductions
 * - Import/Export
 * - Traduction automatique
 */

import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';

// Components
import {
  DashboardView,
  LanguagesView,
  TranslationsView,
  AutoTranslateView,
  ImportExportView,
} from './components';

// Re-exports
export * from './types';
export { i18nApi } from './api';
export {
  StatCard,
  LanguageCoverageBar,
  StatusBadge,
  LoadingSpinner,
  AddLanguageModal,
  TranslationEditModal,
} from './components';
export type {
  StatCardProps,
  LanguageCoverageBarProps,
  StatusBadgeProps,
  AddLanguageModalProps,
  TranslationEditModalProps,
} from './components';

// ============================================================================
// MAIN MODULE COMPONENT
// ============================================================================

const I18NModule: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  const tabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'languages', label: 'Langues' },
    { id: 'translations', label: 'Traductions' },
    { id: 'auto', label: 'Traduction auto' },
    { id: 'import-export', label: 'Import/Export' },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardView />;
      case 'languages':
        return <LanguagesView />;
      case 'translations':
        return <TranslationsView />;
      case 'auto':
        return <AutoTranslateView />;
      case 'import-export':
        return <ImportExportView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900">Internationalisation</h1>
        <p className="text-sm text-gray-500 mt-1">
          Gestion des langues et traductions
        </p>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 px-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6 bg-gray-50">{renderContent()}</div>
    </div>
  );
};

// ============================================================================
// ROUTES
// ============================================================================

const I18NRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<I18NModule />} />
    </Routes>
  );
};

export default I18NRoutes;
