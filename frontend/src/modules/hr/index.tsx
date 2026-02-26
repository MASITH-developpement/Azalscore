/**
 * AZALSCORE Module - HR
 * Gestion des Ressources Humaines
 * Point d'entree du module
 */

import React, { useState } from 'react';
import { PageWrapper } from '@ui/layout';
import { useHRDashboard, useDepartments } from './hooks';
import {
  EmployeeDetailView, EmployeesView, LeaveRequestsView,
  DepartmentsView, PositionsView, TimesheetsView, HRDashboard
} from './components';

// Navigation par onglets
interface TabNavItem {
  id: string;
  label: string;
}

interface TabNavProps {
  tabs: TabNavItem[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <div className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </div>
);

// Types de vues
type View = 'dashboard' | 'employees' | 'departments' | 'positions' | 'leave' | 'timesheets' | 'employee-detail';

/**
 * Module principal HR
 */
const HRModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string | null>(null);
  const { data: dashboard } = useHRDashboard();
  const { data: departments = [] } = useDepartments();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'employees', label: 'Employes' },
    { id: 'departments', label: 'Departements' },
    { id: 'positions', label: 'Postes' },
    { id: 'leave', label: 'Conges' },
    { id: 'timesheets', label: 'Temps' }
  ];

  const handleSelectEmployee = (id: string) => {
    setSelectedEmployeeId(id);
    setCurrentView('employee-detail');
  };

  const handleBackFromDetail = () => {
    setSelectedEmployeeId(null);
    setCurrentView('employees');
  };

  // Vue detail d'un employe
  if (currentView === 'employee-detail' && selectedEmployeeId) {
    return (
      <EmployeeDetailView
        employeeId={selectedEmployeeId}
        onBack={handleBackFromDetail}
      />
    );
  }

  const renderContent = () => {
    switch (currentView) {
      case 'employees':
        return <EmployeesView onSelectEmployee={handleSelectEmployee} />;
      case 'departments':
        return <DepartmentsView />;
      case 'positions':
        return <PositionsView />;
      case 'leave':
        return <LeaveRequestsView />;
      case 'timesheets':
        return <TimesheetsView />;
      default:
        return (
          <HRDashboard
            dashboard={dashboard ?? null}
            departments={departments}
            onNavigate={setCurrentView}
          />
        );
    }
  };

  return (
    <PageWrapper
      title="Ressources Humaines"
      subtitle="Gestion du personnel et des conges"
    >
      <TabNav
        tabs={tabs}
        activeTab={currentView}
        onChange={(id) => setCurrentView(id as View)}
      />
      <div className="mt-4">
        {renderContent()}
      </div>
    </PageWrapper>
  );
};

export default HRModule;
