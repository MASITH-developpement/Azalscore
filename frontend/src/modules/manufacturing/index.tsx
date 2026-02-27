/**
 * AZALSCORE Module - Manufacturing
 * Interface principale du module GPAO/Production
 */

import React, { useState } from 'react';
import { Button } from '@ui/actions';
import { Card, PageWrapper, Grid } from '@ui/layout';
import { Input, Select } from '@ui/forms';
import { DataTable } from '@ui/tables';
import { StatCard } from '@ui/dashboards';

// Local components
const Badge: React.FC<{ variant?: string; className?: string; children: React.ReactNode }> = ({ variant = 'default', className = '', children }) => (
  <span className={`azals-badge azals-badge--${variant} ${className}`}>{children}</span>
);

const Skeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
);

const EmptyState: React.FC<{ icon?: React.ReactNode; title: string; description?: string; action?: React.ReactNode }> = ({ icon, title, description, action }) => (
  <div className="text-center py-12">
    {icon && <div className="flex justify-center mb-4 text-gray-400">{icon}</div>}
    <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
    {description && <p className="text-gray-500 mb-4">{description}</p>}
    {action && <div className="flex justify-center">{action}</div>}
  </div>
);

const CardContent: React.FC<{ className?: string; children: React.ReactNode }> = ({ className = '', children }) => (
  <div className={`azals-card__body ${className}`}>{children}</div>
);

// Simple Tabs components
const Tabs: React.FC<{ defaultValue: string; children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = React.useState('');
  return (
    <div className="azals-tabs" data-active={activeTab}>
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
import {
  Factory,
  FileStack,
  ClipboardList,
  Wrench,
  Plus,
  Search,
  Play,
  Pause,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Gauge,
  TrendingUp,
  Calendar,
} from 'lucide-react';
import {
  useManufacturingDashboard,
  useWorkOrderList,
  useBOMList,
  useWorkcenterList,
  useCreateWorkOrder,
  useStartWorkOrder,
  usePauseWorkOrder,
  useCompleteWorkOrder,
} from './hooks';
import type {
  WorkOrder,
  BOM,
  Workcenter,
  WorkOrderStatus,
  BOMStatus,
  WorkcenterState,
} from './types';
import {
  WORK_ORDER_STATUS_CONFIG,
  BOM_STATUS_CONFIG,
  WORKCENTER_STATE_CONFIG,
} from './types';

// ============================================================================
// HELPERS
// ============================================================================

function toNum(value: number | string | undefined): number {
  if (value === undefined || value === null) return 0;
  if (typeof value === 'number') return value;
  return parseFloat(value) || 0;
}

function formatDate(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
}

function formatDateTime(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleString('fr-FR');
}

// ============================================================================
// STATUS BADGE
// ============================================================================

interface StatusBadgeProps {
  status: WorkOrderStatus | BOMStatus | WorkcenterState;
  type: 'workOrder' | 'bom' | 'workcenter';
}

function StatusBadge({ status, type }: StatusBadgeProps) {
  let config: { label: string; color: string };

  switch (type) {
    case 'workOrder':
      config = WORK_ORDER_STATUS_CONFIG[status as WorkOrderStatus];
      break;
    case 'bom':
      config = BOM_STATUS_CONFIG[status as BOMStatus];
      break;
    case 'workcenter':
      config = WORKCENTER_STATE_CONFIG[status as WorkcenterState];
      break;
  }

  const colorMap: Record<string, string> = {
    gray: 'bg-gray-100 text-gray-800',
    blue: 'bg-blue-100 text-blue-800',
    green: 'bg-green-100 text-green-800',
    orange: 'bg-orange-100 text-orange-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    red: 'bg-red-100 text-red-800',
    purple: 'bg-purple-100 text-purple-800',
  };

  return (
    <Badge className={colorMap[config.color] || colorMap.gray}>
      {config.label}
    </Badge>
  );
}

// ============================================================================
// STATS CARDS
// ============================================================================

interface StatsCardsProps {
  stats: {
    active_work_orders: number;
    completed_today: number;
    in_progress: number;
    delayed: number;
    oee_today: number;
    quality_pass_rate: number;
    workcenters_available: number;
    workcenters_busy: number;
  };
}

function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <ClipboardList className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">OF actifs</p>
              <p className="text-2xl font-bold">{stats.active_work_orders}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Play className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">En cours</p>
              <p className="text-2xl font-bold">{stats.in_progress}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Termines</p>
              <p className="text-2xl font-bold">{stats.completed_today}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Gauge className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">OEE</p>
              <p className="text-2xl font-bold">{(stats.oee_today * 100).toFixed(1)}%</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// WORK ORDERS TAB
// ============================================================================

function WorkOrdersTab() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<WorkOrderStatus | ''>('');

  const { data, isLoading } = useWorkOrderList({
    search: search || undefined,
    status: statusFilter || undefined,
  });

  const startWorkOrder = useStartWorkOrder();
  const pauseWorkOrder = usePauseWorkOrder();
  const completeWorkOrder = useCompleteWorkOrder();

  const columns: import('@/types').TableColumn<WorkOrder>[] = [
    {
      id: 'work_order_number',
      header: 'N° OF',
      accessor: 'work_order_number',
      render: (_value, row) => (
        <span className="font-mono font-medium">{row.work_order_number}</span>
      ),
    },
    {
      id: 'product_name',
      header: 'Produit',
      accessor: 'product_name',
    },
    {
      id: 'quantity_planned',
      header: 'Quantite',
      accessor: 'quantity_planned',
      render: (_value, row) => (
        <span>
          {toNum(row.quantity_produced)}/{toNum(row.quantity_planned)} {row.unit}
        </span>
      ),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (_value, row) => <StatusBadge status={row.status} type="workOrder" />,
    },
    {
      id: 'planned_start',
      header: 'Date prevue',
      accessor: 'planned_start',
      render: (_value, row) => formatDate(row.planned_start),
    },
    {
      id: 'assigned_to_name',
      header: 'Assigne a',
      accessor: 'assigned_to_name',
      render: (_value, row) => row.assigned_to_name || '-',
    },
    {
      id: 'actions',
      header: 'Actions',
      accessor: 'id',
      render: (_value, row) => (
        <div className="flex gap-2">
          {row.status === 'confirmed' && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => startWorkOrder.mutate(row.id)}
            >
              <Play className="h-4 w-4" />
            </Button>
          )}
          {row.status === 'in_progress' && (
            <>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => pauseWorkOrder.mutate({ id: row.id })}
              >
                <Pause className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => completeWorkOrder.mutate({ id: row.id, data: { quantity_produced: toNum(row.quantity_planned) } })}
              >
                <CheckCircle className="h-4 w-4" />
              </Button>
            </>
          )}
          {row.status === 'paused' && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => startWorkOrder.mutate(row.id)}
            >
              <Play className="h-4 w-4" />
            </Button>
          )}
        </div>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher un ordre de fabrication..."
            value={search}
            onChange={(value: string) => setSearch(value)}
            className="pl-10"
          />
        </div>
        <Select
          value={statusFilter}
          onChange={(value: string) => setStatusFilter(value as WorkOrderStatus | '')}
          options={[
            { value: '', label: 'Tous les statuts' },
            ...Object.entries(WORK_ORDER_STATUS_CONFIG).map(([key, { label }]) => ({ value: key, label }))
          ]}
        />
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Nouvel OF
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
          icon={<ClipboardList className="h-12 w-12" />}
          title="Aucun ordre de fabrication"
          description="Creez votre premier ordre de fabrication pour demarrer la production."
          action={
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Creer un OF
            </Button>
          }
        />
      )}
    </div>
  );
}

// ============================================================================
// BOMS TAB
// ============================================================================

function BOMsTab() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useBOMList({ search: search || undefined });

  const columns: import('@/types').TableColumn<BOM>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      render: (_value, row) => <span className="font-mono">{row.code}</span>,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
    },
    {
      id: 'product_name',
      header: 'Produit',
      accessor: 'product_name',
    },
    {
      id: 'bom_version',
      header: 'Version',
      accessor: 'bom_version',
      render: (_value, row) => (
        <span className="flex items-center gap-2">
          v{row.bom_version}
          {row.is_current && <Badge variant="secondary">Actuelle</Badge>}
        </span>
      ),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (_value, row) => <StatusBadge status={row.status} type="bom" />,
    },
    {
      id: 'total_cost',
      header: 'Cout total',
      accessor: 'total_cost',
      render: (_value, row) => `${toNum(row.total_cost).toFixed(2)} EUR`,
    },
    {
      id: 'lines',
      header: 'Lignes',
      accessor: 'lines',
      render: (_value, row) => row.lines?.length || 0,
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
            placeholder="Rechercher une nomenclature..."
            value={search}
            onChange={(value: string) => setSearch(value)}
            className="pl-10"
          />
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Nouvelle nomenclature
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
          icon={<FileStack className="h-12 w-12" />}
          title="Aucune nomenclature"
          description="Creez votre premiere nomenclature (BOM) pour definir la composition de vos produits."
          action={
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Creer une nomenclature
            </Button>
          }
        />
      )}
    </div>
  );
}

// ============================================================================
// WORKCENTERS TAB
// ============================================================================

function WorkcentersTab() {
  const { data, isLoading } = useWorkcenterList();

  const columns: import('@/types').TableColumn<Workcenter>[] = [
    {
      id: 'code',
      header: 'Code',
      accessor: 'code',
      render: (_value, row) => <span className="font-mono">{row.code}</span>,
    },
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
    },
    {
      id: 'workcenter_type',
      header: 'Type',
      accessor: 'workcenter_type',
    },
    {
      id: 'state',
      header: 'Etat',
      accessor: 'state',
      render: (_value, row) => <StatusBadge status={row.state} type="workcenter" />,
    },
    {
      id: 'capacity',
      header: 'Capacite',
      accessor: 'capacity',
    },
    {
      id: 'efficiency',
      header: 'Efficacite',
      accessor: 'efficiency',
      render: (_value, row) => `${(toNum(row.efficiency) * 100).toFixed(0)}%`,
    },
    {
      id: 'hourly_cost',
      header: 'Cout horaire',
      accessor: 'hourly_cost',
      render: (_value, row) => `${toNum(row.hourly_cost).toFixed(2)} EUR/h`,
    },
    {
      id: 'current_operator_name',
      header: 'Operateur',
      accessor: 'current_operator_name',
      render: (_value, row) => row.current_operator_name || '-',
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Nouveau poste de travail
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
          icon={<Wrench className="h-12 w-12" />}
          title="Aucun poste de travail"
          description="Configurez vos postes de travail pour organiser votre production."
          action={
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Creer un poste
            </Button>
          }
        />
      )}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function ManufacturingModule() {
  const { data: dashboard, isLoading } = useManufacturingDashboard();

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

  const stats = dashboard?.stats || {
    active_work_orders: 0,
    completed_today: 0,
    in_progress: 0,
    delayed: 0,
    oee_today: 0,
    quality_pass_rate: 0,
    workcenters_available: 0,
    workcenters_busy: 0,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Factory className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Production (GPAO)</h1>
            <p className="text-muted-foreground">
              Gestion de Production Assistee par Ordinateur
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary">
            <Calendar className="h-4 w-4 mr-2" />
            Planning
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nouvel OF
          </Button>
        </div>
      </div>

      {/* Stats */}
      <StatsCards stats={stats} />

      {/* Alerts */}
      {stats.delayed > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <span className="font-medium text-orange-800">
                {stats.delayed} ordre(s) de fabrication en retard
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <Tabs defaultValue="work-orders">
        <TabsList>
          <TabsTrigger value="work-orders">
            <ClipboardList className="h-4 w-4 mr-2" />
            Ordres de fabrication
          </TabsTrigger>
          <TabsTrigger value="boms">
            <FileStack className="h-4 w-4 mr-2" />
            Nomenclatures
          </TabsTrigger>
          <TabsTrigger value="workcenters">
            <Wrench className="h-4 w-4 mr-2" />
            Postes de travail
          </TabsTrigger>
        </TabsList>

        <TabsContent value="work-orders" className="mt-6">
          <WorkOrdersTab />
        </TabsContent>

        <TabsContent value="boms" className="mt-6">
          <BOMsTab />
        </TabsContent>

        <TabsContent value="workcenters" className="mt-6">
          <WorkcentersTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Named exports
export { ManufacturingModule };
export * from './types';
export * from './hooks';
export * from './api';
export { moduleMeta as manufacturingMeta } from './meta';
