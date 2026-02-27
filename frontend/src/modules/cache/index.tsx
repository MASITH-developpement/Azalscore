/**
 * AZALSCORE - Module Cache Admin Panel
 * =====================================
 * Interface d'administration pour la gestion du cache applicatif.
 */

import React, { useState } from 'react';
import {
  BarChart3,
  Layers,
  Trash2,
  RefreshCw,
  AlertTriangle,
  Clock,
  Settings,
} from 'lucide-react';
import { PageWrapper } from '@ui/layout';

// Components
import {
  TabNav,
  DashboardView,
  RegionsView,
  AlertsView,
  PreloadView,
  InvalidationView,
  AuditView,
  ConfigView,
} from './components';
import type { TabNavItem } from './components';

// Re-exports
export * from './types';
export { cacheApi } from './api';
export * from './hooks';
export {
  Badge,
  TabNav,
  ProgressBar,
  formatDateTime,
  formatDate,
} from './components';

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'regions' | 'invalidation' | 'preload' | 'alerts' | 'audit' | 'config';

const CacheModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');

  const tabs: TabNavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <BarChart3 className="w-4 h-4" /> },
    { id: 'regions', label: 'Regions', icon: <Layers className="w-4 h-4" /> },
    { id: 'invalidation', label: 'Invalidation', icon: <Trash2 className="w-4 h-4" /> },
    { id: 'preload', label: 'Prechargement', icon: <RefreshCw className="w-4 h-4" /> },
    { id: 'alerts', label: 'Alertes', icon: <AlertTriangle className="w-4 h-4" /> },
    { id: 'audit', label: 'Audit', icon: <Clock className="w-4 h-4" /> },
    { id: 'config', label: 'Configuration', icon: <Settings className="w-4 h-4" /> },
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'regions':
        return <RegionsView />;
      case 'invalidation':
        return <InvalidationView />;
      case 'preload':
        return <PreloadView />;
      case 'alerts':
        return <AlertsView />;
      case 'audit':
        return <AuditView />;
      case 'config':
        return <ConfigView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <PageWrapper
      title="Gestion du Cache"
      subtitle="Administration du cache applicatif multi-niveau"
    >
      <TabNav tabs={tabs} activeTab={currentView} onChange={(id) => setCurrentView(id as View)} />
      <div className="mt-4">{renderContent()}</div>
    </PageWrapper>
  );
};

export default CacheModule;
