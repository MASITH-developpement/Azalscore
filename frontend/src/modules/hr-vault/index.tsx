/**
 * AZALSCORE Module - HR Vault (Coffre-fort RH)
 * ==============================================
 * Module de gestion securisee des documents employes
 *
 * Structure:
 * - api.ts: Client API
 * - types.ts: Types et configurations
 * - hooks.ts: React Query hooks
 * - components/: Composants UI
 */

import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import {
  FileText, Shield, Eye, FolderOpen, Archive
} from 'lucide-react';
import { PageWrapper } from '@ui/layout';
import { useDashboardStats } from './hooks';
import {
  TabNav,
  DashboardView,
  DocumentsListView,
  GDPRView,
  AccessLogsView,
  CategoriesView,
  DocumentDetailView,
} from './components';

// Re-exports
export * from './types';
export * from './hooks';
export * from './components';

// ============================================================================
// MAIN MODULE
// ============================================================================

type View = 'dashboard' | 'documents' | 'gdpr' | 'access-logs' | 'categories';

const HRVaultModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats } = useDashboardStats();

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: <FileText size={16} /> },
    { id: 'documents', label: 'Documents', icon: <FolderOpen size={16} /> },
    { id: 'gdpr', label: 'RGPD', icon: <Shield size={16} />, badge: stats?.gdpr_requests_pending },
    { id: 'access-logs', label: 'Historique', icon: <Eye size={16} /> },
    { id: 'categories', label: 'Categories', icon: <Archive size={16} /> },
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'documents':
        return <DocumentsListView />;
      case 'gdpr':
        return <GDPRView />;
      case 'access-logs':
        return <AccessLogsView />;
      case 'categories':
        return <CategoriesView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <PageWrapper
      title="Coffre-fort RH"
      subtitle="Gestion securisee des documents employes"
    >
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">{renderContent()}</div>
    </PageWrapper>
  );
};

// ============================================================================
// ROUTES
// ============================================================================

const HRVaultRoutes: React.FC = () => {
  return (
    <Routes>
      <Route index element={<HRVaultModule />} />
      <Route path="documents/:id" element={<DocumentDetailView />} />
    </Routes>
  );
};

export default HRVaultRoutes;
