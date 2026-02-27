/**
 * AZALSCORE Module - Admin - AdminDashboardView
 * Vue principale du module administration avec tabs
 */

import React, { useState } from 'react';
import { Users, Building, Shield, Database, Activity, AlertTriangle } from 'lucide-react';
import SocialNetworksModule from '@modules/social-networks';
import { StatCard } from '@ui/dashboards';
import { PageWrapper, Grid } from '@ui/layout';
import { useAdminDashboard } from '../hooks';
import AuditView from './AuditView';
import BackupsView from './BackupsView';
import RolesView from './RolesView';
import TenantsView from './TenantsView';
import UsersPermissionsView from './UsersPermissionsView';
import UsersView from './UsersView';
import { SequencesView, EnrichmentProvidersView, CSSCustomizationView } from './index';

interface TabNavProps {
  tabs: { id: string; label: string }[];
  activeTab: string;
  onChange: (id: string) => void;
}

const TabNav: React.FC<TabNavProps> = ({ tabs, activeTab, onChange }) => (
  <nav className="azals-tab-nav">
    {tabs.map((tab) => (
      <button
        key={tab.id}
        className={`azals-tab-nav__item ${activeTab === tab.id ? 'azals-tab-nav__item--active' : ''}`}
        onClick={() => onChange(tab.id)}
      >
        {tab.label}
      </button>
    ))}
  </nav>
);

type View = 'dashboard' | 'users' | 'permissions' | 'roles' | 'tenants' | 'sequences' | 'enrichment' | 'social-networks' | 'audit' | 'backups' | 'css';

const AdminDashboardView: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: dashboard } = useAdminDashboard();

  const tabs = [
    { id: 'dashboard', label: 'Tableau de bord' },
    { id: 'users', label: 'Utilisateurs' },
    { id: 'permissions', label: 'Acces Modules' },
    { id: 'roles', label: 'Roles' },
    { id: 'tenants', label: 'Tenants' },
    { id: 'sequences', label: 'Numerotation' },
    { id: 'enrichment', label: 'Enrichissement' },
    { id: 'social-networks', label: 'Reseaux Sociaux' },
    { id: 'css', label: 'Apparence' },
    { id: 'audit', label: 'Audit' },
    { id: 'backups', label: 'Sauvegardes' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'users':
        return <UsersView />;
      case 'permissions':
        return <UsersPermissionsView />;
      case 'roles':
        return <RolesView />;
      case 'tenants':
        return <TenantsView />;
      case 'sequences':
        return <SequencesView />;
      case 'enrichment':
        return <EnrichmentProvidersView />;
      case 'social-networks':
        return <SocialNetworksModule />;
      case 'css':
        return <CSSCustomizationView />;
      case 'audit':
        return <AuditView />;
      case 'backups':
        return <BackupsView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Utilisateurs actifs"
                value={`${dashboard?.active_users || 0} / ${dashboard?.total_users || 0}`}
                icon={<Users size={20} />}
                variant="default"
                onClick={() => setCurrentView('users')}
              />
              <StatCard
                title="Tenants actifs"
                value={`${dashboard?.active_tenants || 0} / ${dashboard?.total_tenants || 0}`}
                icon={<Building size={20} />}
                variant="default"
                onClick={() => setCurrentView('tenants')}
              />
              <StatCard
                title="Roles"
                value={String(dashboard?.total_roles || 0)}
                icon={<Shield size={20} />}
                variant="success"
                onClick={() => setCurrentView('roles')}
              />
              <StatCard
                title="Stockage utilise"
                value={`${dashboard?.storage_used_gb || 0} GB`}
                icon={<Database size={20} />}
                variant="warning"
              />
            </Grid>
            <Grid cols={2}>
              <StatCard
                title="Appels API (aujourd'hui)"
                value={String(dashboard?.api_calls_today || 0)}
                icon={<Activity size={20} />}
                variant="default"
              />
              <StatCard
                title="Erreurs (aujourd'hui)"
                value={String(dashboard?.errors_today || 0)}
                icon={<AlertTriangle size={20} />}
                variant={dashboard?.errors_today ? 'danger' : 'success'}
                onClick={() => setCurrentView('audit')}
              />
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Administration" subtitle="Gestion des utilisateurs, roles et systeme">
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

export default AdminDashboardView;
