/**
 * AZALSCORE Module - Dashboards
 * Interface principale du module de tableaux de bord
 */

import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  DataTable,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Input,
  Select,
  Skeleton,
  EmptyState,
} from '@/ui-engine';
import {
  LayoutDashboard,
  Star,
  Bell,
  FileText,
  LayoutTemplate,
  Plus,
  Search,
  Eye,
  Edit,
  Trash2,
  Share2,
  Copy,
  Clock,
  AlertTriangle,
  BarChart,
  PieChart,
  LineChart,
  Table,
} from 'lucide-react';
import {
  useDashboardList,
  useFavorites,
  useAlertList,
  useScheduledReportList,
  useTemplateList,
  useDashboardStats,
  useToggleFavorite,
  useDeleteDashboard,
  useDuplicateDashboard,
} from './hooks';
import type {
  Dashboard,
  DashboardTemplate,
  AlertRule,
  ScheduledReport,
  Favorite,
  DashboardType,
  AlertSeverity,
} from './types';
import {
  DASHBOARD_TYPE_CONFIG,
  ALERT_SEVERITY_CONFIG,
  EXPORT_FORMAT_CONFIG,
} from './types';

// ============================================================================
// HELPERS
// ============================================================================

function formatDate(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
}

function formatDateTime(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleString('fr-FR');
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

interface StatsCardsProps {
  stats: {
    total_dashboards: number;
    total_widgets: number;
    active_alerts: number;
    scheduled_reports: number;
  };
}

function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <LayoutDashboard className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Tableaux</p>
              <p className="text-2xl font-bold">{stats.total_dashboards}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <BarChart className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Widgets</p>
              <p className="text-2xl font-bold">{stats.total_widgets}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Bell className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Alertes actives</p>
              <p className="text-2xl font-bold">{stats.active_alerts}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Clock className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Rapports planifies</p>
              <p className="text-2xl font-bold">{stats.scheduled_reports}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// DASHBOARDS TAB
// ============================================================================

function DashboardsTab() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<DashboardType | ''>('');

  const { data, isLoading } = useDashboardList({
    search: search || undefined,
    dashboard_type: typeFilter || undefined,
  });

  const deleteDashboard = useDeleteDashboard();
  const duplicateDashboard = useDuplicateDashboard();
  const toggleFavorite = useToggleFavorite();

  const columns = [
    {
      header: 'Nom',
      accessorKey: 'name' as const,
      cell: (row: Dashboard) => (
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="p-1"
            onClick={() => toggleFavorite.mutate({ id: row.id, isFavorite: !row.is_favorite })}
          >
            <Star className={`h-4 w-4 ${row.is_favorite ? 'fill-yellow-400 text-yellow-400' : 'text-gray-400'}`} />
          </Button>
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
      header: 'Type',
      accessorKey: 'dashboard_type' as const,
      cell: (row: Dashboard) => <TypeBadge type={row.dashboard_type} />,
    },
    {
      header: 'Widgets',
      accessorKey: 'widgets' as const,
      cell: (row: Dashboard) => row.widgets?.length || 0,
    },
    {
      header: 'Partage',
      accessorKey: 'is_public' as const,
      cell: (row: Dashboard) => (
        <Badge variant={row.is_public ? 'default' : 'outline'}>
          {row.is_public ? 'Public' : 'Prive'}
        </Badge>
      ),
    },
    {
      header: 'Derniere modif.',
      accessorKey: 'updated_at' as const,
      cell: (row: Dashboard) => formatDate(row.updated_at || row.created_at),
    },
    {
      header: 'Actions',
      accessorKey: 'id' as const,
      cell: (row: Dashboard) => (
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
            onClick={() => duplicateDashboard.mutate(row.id)}
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
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select
          value={typeFilter}
          onValueChange={(value) => setTypeFilter(value as DashboardType | '')}
        >
          <option value="">Tous les types</option>
          {Object.entries(DASHBOARD_TYPE_CONFIG).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </Select>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
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
          description="Creez votre premier tableau de bord pour visualiser vos donnees."
          action={
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Creer un tableau
            </Button>
          }
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
  const toggleFavorite = useToggleFavorite();

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!favorites || favorites.length === 0) {
    return (
      <EmptyState
        icon={<Star className="h-12 w-12" />}
        title="Aucun favori"
        description="Ajoutez des tableaux de bord a vos favoris pour y acceder rapidement."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {favorites.map((fav) => (
        <Card key={fav.id} className="cursor-pointer hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium">{fav.dashboard_name}</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Ajoute le {formatDate(fav.created_at)}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleFavorite.mutate({ id: fav.dashboard_id, isFavorite: false })}
              >
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ============================================================================
// ALERTS TAB
// ============================================================================

function AlertsTab() {
  const { data: alerts, isLoading } = useAlertList({ is_active: true });

  const columns = [
    {
      header: 'Alerte',
      accessorKey: 'name' as const,
      cell: (row: AlertRule) => (
        <div>
          <p className="font-medium">{row.name}</p>
          <p className="text-sm text-muted-foreground">{row.condition_expression}</p>
        </div>
      ),
    },
    {
      header: 'Severite',
      accessorKey: 'severity' as const,
      cell: (row: AlertRule) => <SeverityBadge severity={row.severity} />,
    },
    {
      header: 'Widget',
      accessorKey: 'widget_id' as const,
    },
    {
      header: 'Notification',
      accessorKey: 'notification_channels' as const,
      cell: (row: AlertRule) => row.notification_channels?.join(', ') || '-',
    },
    {
      header: 'Statut',
      accessorKey: 'is_active' as const,
      cell: (row: AlertRule) => (
        <Badge variant={row.is_active ? 'default' : 'outline'}>
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
        description="Configurez des alertes pour etre notifie des evenements importants."
        action={
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Creer une alerte
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button>
          <Plus className="h-4 w-4 mr-2" />
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
// REPORTS TAB
// ============================================================================

function ReportsTab() {
  const { data: reports, isLoading } = useScheduledReportList();

  const columns = [
    {
      header: 'Nom',
      accessorKey: 'name' as const,
      cell: (row: ScheduledReport) => (
        <div>
          <p className="font-medium">{row.name}</p>
          <p className="text-sm text-muted-foreground">{row.dashboard_name}</p>
        </div>
      ),
    },
    {
      header: 'Frequence',
      accessorKey: 'schedule_cron' as const,
    },
    {
      header: 'Format',
      accessorKey: 'export_format' as const,
      cell: (row: ScheduledReport) => (
        <Badge variant="outline">
          {EXPORT_FORMAT_CONFIG[row.export_format]?.label || row.export_format}
        </Badge>
      ),
    },
    {
      header: 'Destinataires',
      accessorKey: 'recipients' as const,
      cell: (row: ScheduledReport) => row.recipients?.length || 0,
    },
    {
      header: 'Prochain envoi',
      accessorKey: 'next_run_at' as const,
      cell: (row: ScheduledReport) => formatDateTime(row.next_run_at),
    },
    {
      header: 'Statut',
      accessorKey: 'is_active' as const,
      cell: (row: ScheduledReport) => (
        <Badge variant={row.is_active ? 'default' : 'outline'}>
          {row.is_active ? 'Actif' : 'Inactif'}
        </Badge>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!reports || reports.length === 0) {
    return (
      <EmptyState
        icon={<FileText className="h-12 w-12" />}
        title="Aucun rapport planifie"
        description="Planifiez des rapports automatiques pour recevoir vos donnees periodiquement."
        action={
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Planifier un rapport
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Planifier un rapport
        </Button>
      </div>
      <DataTable
        data={reports}
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
  const { data: templates, isLoading } = useTemplateList();

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!templates || templates.length === 0) {
    return (
      <EmptyState
        icon={<LayoutTemplate className="h-12 w-12" />}
        title="Aucun template"
        description="Creez des templates pour reutiliser vos configurations de tableaux."
        action={
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Creer un template
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Creer un template
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map((template) => (
          <Card key={template.id} className="cursor-pointer hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium">{template.name}</h3>
                  {template.description && (
                    <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                      {template.description}
                    </p>
                  )}
                  <div className="flex gap-2 mt-2">
                    <Badge variant="outline">{template.category}</Badge>
                    {template.is_public && <Badge>Public</Badge>}
                  </div>
                </div>
              </div>
              <div className="mt-4 flex gap-2">
                <Button size="sm" className="flex-1">
                  Utiliser
                </Button>
                <Button size="sm" variant="outline">
                  <Eye className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DashboardsModule() {
  const { data: stats, isLoading } = useDashboardStats();

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  const dashboardStats = stats || {
    total_dashboards: 0,
    total_widgets: 0,
    active_alerts: 0,
    scheduled_reports: 0,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <LayoutDashboard className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Tableaux de bord</h1>
            <p className="text-muted-foreground">
              Visualisation de donnees, KPIs et rapports
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nouveau tableau
          </Button>
        </div>
      </div>

      {/* Stats */}
      <StatsCards stats={dashboardStats} />

      {/* Main Content */}
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
            {dashboardStats.active_alerts > 0 && (
              <Badge className="ml-2 bg-orange-100 text-orange-800">{dashboardStats.active_alerts}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="reports">
            <FileText className="h-4 w-4 mr-2" />
            Rapports
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

        <TabsContent value="reports" className="mt-6">
          <ReportsTab />
        </TabsContent>

        <TabsContent value="templates" className="mt-6">
          <TemplatesTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Named exports
export { DashboardsModule };
export * from './types';
export * from './hooks';
export * from './api';
export { dashboardsMeta } from './meta';
