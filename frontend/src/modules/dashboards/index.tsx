// @ts-nocheck
/**
 * AZALSCORE Module - Dashboards
 * Interface principale du module de tableaux de bord
 * TODO: Fix type issues with API responses and component props
 */

import React, { useState } from 'react';
import { Button } from '@ui/actions';
import { Card, PageWrapper, Grid } from '@ui/layout';
import { Input, Select } from '@ui/forms';
import { DataTable } from '@ui/tables';
import { EmptyState } from '@ui/components/StateViews';
import type { TableColumn } from '@/types';
import {
  LayoutDashboard,
  Star,
  Bell,
  LayoutTemplate,
  Plus,
  Search,
  Eye,
  Edit,
  Trash2,
  Share2,
  Copy,
  Clock,
  BarChart,
} from 'lucide-react';
import {
  useDashboardList,
  useFavorites,
  useAlertRules,
  useTemplates,
  useDeleteDashboard,
  useDuplicateDashboard,
  useAddFavorite,
  useRemoveFavorite,
} from './hooks';
import type {
  Dashboard,
  DashboardTemplate,
  AlertRule,
  Favorite,
  DashboardType,
  AlertSeverity,
} from './types';
import {
  DASHBOARD_TYPE_CONFIG,
  ALERT_SEVERITY_CONFIG,
} from './types';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ variant?: string; className?: string; children: React.ReactNode }> = ({ variant = 'default', className = '', children }) => (
  <span className={`azals-badge azals-badge--${variant} ${className}`}>{children}</span>
);

const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
);

// Simple Tabs components
const Tabs: React.FC<{ defaultValue: string; children: React.ReactNode }> = ({ defaultValue, children }) => {
  const [activeTab, setActiveTab] = useState(defaultValue);
  return (
    <div className="azals-tabs">
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child as React.ReactElement<{ activeTab?: string; setActiveTab?: (v: string) => void }>, { activeTab, setActiveTab });
        }
        return child;
      })}
    </div>
  );
};

const TabsList: React.FC<{ children: React.ReactNode; activeTab?: string; setActiveTab?: (v: string) => void }> = ({ children, activeTab, setActiveTab }) => (
  <div className="azals-tabs__list flex gap-2 border-b mb-4" role="tablist">
    {React.Children.map(children, (child) => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child as React.ReactElement<{ activeTab?: string; setActiveTab?: (v: string) => void }>, { activeTab, setActiveTab });
      }
      return child;
    })}
  </div>
);

const TabsTrigger: React.FC<{ value: string; children: React.ReactNode; activeTab?: string; setActiveTab?: (v: string) => void }> = ({ value, children, activeTab, setActiveTab }) => (
  <button
    type="button"
    role="tab"
    className={`px-4 py-2 border-b-2 transition-colors ${activeTab === value ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
    aria-selected={activeTab === value}
    onClick={() => setActiveTab?.(value)}
  >
    <span className="flex items-center gap-2">{children}</span>
  </button>
);

const TabsContent: React.FC<{ value: string; children: React.ReactNode; className?: string; activeTab?: string }> = ({ value, children, className = '', activeTab }) => {
  if (activeTab !== value) return null;
  return <div className={className} role="tabpanel">{children}</div>;
};

// ============================================================================
// HELPERS
// ============================================================================

function formatDate(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
}

// ============================================================================
// TYPE BADGE
// ============================================================================

interface TypeBadgeProps {
  type: DashboardType;
}

function TypeBadge({ type }: TypeBadgeProps) {
  const config = DASHBOARD_TYPE_CONFIG[type];
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    purple: 'bg-purple-100 text-purple-800',
    orange: 'bg-orange-100 text-orange-800',
    gray: 'bg-gray-100 text-gray-800',
  };

  return (
    <Badge className={colorMap[config.color] || colorMap.gray}>
      {config.label}
    </Badge>
  );
}

// ============================================================================
// SEVERITY BADGE
// ============================================================================

interface SeverityBadgeProps {
  severity: AlertSeverity;
}

function SeverityBadge({ severity }: SeverityBadgeProps) {
  const config = ALERT_SEVERITY_CONFIG[severity];
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    orange: 'bg-orange-100 text-orange-800',
    red: 'bg-red-100 text-red-800',
  };

  return (
    <Badge className={colorMap[config.color] || 'bg-gray-100 text-gray-800'}>
      {config.label}
    </Badge>
  );
}

// ============================================================================
// STATS CARDS
// ============================================================================

function StatsCards() {
  return (
    <Grid cols={4} gap="md">
      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <LayoutDashboard className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Tableaux</p>
            <p className="text-2xl font-bold">0</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <BarChart className="h-5 w-5 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Widgets</p>
            <p className="text-2xl font-bold">0</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-orange-100 rounded-lg">
            <Bell className="h-5 w-5 text-orange-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Alertes actives</p>
            <p className="text-2xl font-bold">0</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Clock className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Rapports planifies</p>
            <p className="text-2xl font-bold">0</p>
          </div>
        </div>
      </Card>
    </Grid>
  );
}

// ============================================================================
// DASHBOARDS TAB
// ============================================================================

function DashboardsTab() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const { data, isLoading } = useDashboardList({
    search: search || undefined,
  });

  const deleteDashboard = useDeleteDashboard();
  const duplicateDashboard = useDuplicateDashboard();
  const addFavorite = useAddFavorite();

  const columns: TableColumn<Dashboard>[] = [
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      render: (_, row) => (
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="p-1 hover:bg-gray-100 rounded"
            onClick={() => addFavorite.mutate({ dashboard_id: row.id })}
          >
            <Star className="h-4 w-4 text-gray-400" />
          </button>
          <div>
            <p className="font-medium">{row.name}</p>
            {row.description && (
              <p className="text-sm text-muted-foreground truncate max-w-xs">{row.description}</p>
            )}
          </div>
        </div>
      ),
    },
    {
      id: 'type',
      header: 'Type',
      accessor: 'type',
      render: (_, row) => <TypeBadge type={row.type} />,
    },
    {
      id: 'widgets',
      header: 'Widgets',
      accessor: 'widgets',
      render: (_, row) => row.widgets?.length || 0,
    },
    {
      id: 'updated_at',
      header: 'Derniere modif.',
      accessor: 'updated_at',
      render: (_, row) => formatDate(row.updated_at || row.created_at),
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_, row) => (
        <div className="flex gap-1">
          <Button variant="ghost" size="sm">
            <Eye className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <Edit className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => duplicateDashboard.mutate({ id: row.id })}
          >
            <Copy className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <Share2 className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => deleteDashboard.mutate(row.id)}
          >
            <Trash2 className="h-4 w-4 text-red-500" />
          </Button>
        </div>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher un tableau de bord..."
            value={search}
            onChange={(value) => setSearch(value)}
          />
        </div>
        <Select
          value={typeFilter}
          onChange={(value) => setTypeFilter(value)}
          options={[
            { value: '', label: 'Tous les types' },
            ...Object.entries(DASHBOARD_TYPE_CONFIG).map(([key, { label }]) => ({ value: key, label }))
          ]}
        />
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Nouveau tableau
        </Button>
      </div>

      {data?.items && data.items.length > 0 ? (
        <DataTable
          data={data.items}
          columns={columns}
          keyField="id"
        />
      ) : (
        <EmptyState
          icon={<LayoutDashboard className="h-12 w-12" />}
          title="Aucun tableau de bord"
          message="Creez votre premier tableau de bord pour visualiser vos donnees."
          action={{
            label: 'Creer un tableau',
            onClick: () => {},
            icon: <Plus className="h-4 w-4" />,
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// FAVORITES TAB
// ============================================================================

function FavoritesTab() {
  const { data: favorites, isLoading } = useFavorites();
  const removeFavorite = useRemoveFavorite();

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!favorites || favorites.length === 0) {
    return (
      <EmptyState
        icon={<Star className="h-12 w-12" />}
        title="Aucun favori"
        message="Ajoutez des tableaux de bord a vos favoris pour y acceder rapidement."
      />
    );
  }

  return (
    <Grid cols={3} gap="md">
      {favorites.map((fav: Favorite) => (
        <Card key={fav.id} className="cursor-pointer hover:shadow-md transition-shadow">
          <div className="p-4 flex items-start justify-between">
            <div>
              <h3 className="font-medium">{fav.dashboard_name}</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Ajoute le {formatDate(fav.created_at)}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => removeFavorite.mutate(fav.dashboard_id)}
            >
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
            </Button>
          </div>
        </Card>
      ))}
    </Grid>
  );
}

// ============================================================================
// ALERTS TAB
// ============================================================================

function AlertsTab() {
  const { data: alerts, isLoading } = useAlertRules();

  const columns: TableColumn<AlertRule>[] = [
    {
      id: 'name',
      header: 'Alerte',
      accessor: 'name',
      render: (_, row) => (
        <div>
          <p className="font-medium">{row.name}</p>
        </div>
      ),
    },
    {
      id: 'severity',
      header: 'Severite',
      accessor: 'severity',
      render: (_, row) => <SeverityBadge severity={row.severity} />,
    },
    {
      id: 'widget_id',
      header: 'Widget',
      accessor: 'widget_id',
    },
    {
      id: 'is_active',
      header: 'Statut',
      accessor: 'is_active',
      render: (_, row) => (
        <Badge variant={row.is_active ? 'default' : 'secondary'}>
          {row.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!alerts || alerts.length === 0) {
    return (
      <EmptyState
        icon={<Bell className="h-12 w-12" />}
        title="Aucune alerte"
        message="Configurez des alertes pour etre notifie des evenements importants."
        action={{
          label: 'Creer une alerte',
          onClick: () => {},
          icon: <Plus className="h-4 w-4" />,
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Nouvelle alerte
        </Button>
      </div>
      <DataTable
        data={alerts}
        columns={columns}
        keyField="id"
      />
    </div>
  );
}

// ============================================================================
// TEMPLATES TAB
// ============================================================================

function TemplatesTab() {
  const { data: templates, isLoading } = useTemplates();

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!templates?.items || templates.items.length === 0) {
    return (
      <EmptyState
        icon={<LayoutTemplate className="h-12 w-12" />}
        title="Aucun template"
        message="Creez des templates pour reutiliser vos configurations de tableaux."
        action={{
          label: 'Creer un template',
          onClick: () => {},
          icon: <Plus className="h-4 w-4" />,
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Creer un template
        </Button>
      </div>

      <Grid cols={3} gap="md">
        {templates.items.map((template: DashboardTemplate) => (
          <Card key={template.id} className="cursor-pointer hover:shadow-md transition-shadow">
            <div className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium">{template.name}</h3>
                  {template.description && (
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                      {template.description}
                    </p>
                  )}
                  <div className="flex gap-2 mt-2">
                    <Badge variant="secondary">{template.category}</Badge>
                    {template.is_public && <Badge>Public</Badge>}
                  </div>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <Button size="sm" className="flex-1">
                  Utiliser
                </Button>
                <Button size="sm" variant="secondary">
                  <Eye className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </Grid>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DashboardsModule() {
  return (
    <PageWrapper
      title="Tableaux de bord"
      subtitle="Visualisation de donnees, KPIs et rapports"
      actions={
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Nouveau tableau
        </Button>
      }
    >
      <div className="space-y-6">
        <StatsCards />

        <Tabs defaultValue="dashboards">
          <TabsList>
            <TabsTrigger value="dashboards">
              <LayoutDashboard className="h-4 w-4 mr-2" />
              Mes tableaux
            </TabsTrigger>
            <TabsTrigger value="favorites">
              <Star className="h-4 w-4 mr-2" />
              Favoris
            </TabsTrigger>
            <TabsTrigger value="alerts">
              <Bell className="h-4 w-4 mr-2" />
              Alertes
            </TabsTrigger>
            <TabsTrigger value="templates">
              <LayoutTemplate className="h-4 w-4 mr-2" />
              Templates
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboards" className="mt-6">
            <DashboardsTab />
          </TabsContent>

          <TabsContent value="favorites" className="mt-6">
            <FavoritesTab />
          </TabsContent>

          <TabsContent value="alerts" className="mt-6">
            <AlertsTab />
          </TabsContent>

          <TabsContent value="templates" className="mt-6">
            <TemplatesTab />
          </TabsContent>
        </Tabs>
      </div>
    </PageWrapper>
  );
}

// Named exports
export { DashboardsModule };
export * from './types';
export * from './hooks';
export * from './api';
export { dashboardsMeta } from './meta';
