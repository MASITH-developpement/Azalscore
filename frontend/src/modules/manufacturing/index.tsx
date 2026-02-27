/**
 * AZALSCORE Module - Manufacturing
 * Interface principale du module GPAO/Production
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
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Skeleton,
  EmptyState,
} from '@/ui-engine';
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

  const columns = [
    {
      header: 'N° OF',
      accessorKey: 'work_order_number' as const,
      cell: (row: WorkOrder) => (
        <span className="font-mono font-medium">{row.work_order_number}</span>
      ),
    },
    {
      header: 'Produit',
      accessorKey: 'product_name' as const,
    },
    {
      header: 'Quantite',
      accessorKey: 'quantity_planned' as const,
      cell: (row: WorkOrder) => (
        <span>
          {toNum(row.quantity_produced)}/{toNum(row.quantity_planned)} {row.unit}
        </span>
      ),
    },
    {
      header: 'Statut',
      accessorKey: 'status' as const,
      cell: (row: WorkOrder) => <StatusBadge status={row.status} type="workOrder" />,
    },
    {
      header: 'Date prevue',
      accessorKey: 'planned_start' as const,
      cell: (row: WorkOrder) => formatDate(row.planned_start),
    },
    {
      header: 'Assigne a',
      accessorKey: 'assigned_to_name' as const,
      cell: (row: WorkOrder) => row.assigned_to_name || '-',
    },
    {
      header: 'Actions',
      accessorKey: 'id' as const,
      cell: (row: WorkOrder) => (
        <div className="flex gap-2">
          {row.status === 'confirmed' && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => startWorkOrder.mutate(row.id)}
            >
              <Play className="h-4 w-4" />
            </Button>
          )}
          {row.status === 'in_progress' && (
            <>
              <Button
                size="sm"
                variant="outline"
                onClick={() => pauseWorkOrder.mutate({ id: row.id })}
              >
                <Pause className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => completeWorkOrder.mutate({ id: row.id, data: { quantity_produced: toNum(row.quantity_planned) } })}
              >
                <CheckCircle className="h-4 w-4" />
              </Button>
            </>
          )}
          {row.status === 'paused' && (
            <Button
              size="sm"
              variant="outline"
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
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select
          value={statusFilter}
          onValueChange={(value) => setStatusFilter(value as WorkOrderStatus | '')}
        >
          <option value="">Tous les statuts</option>
          {Object.entries(WORK_ORDER_STATUS_CONFIG).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </Select>
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

  const columns = [
    {
      header: 'Code',
      accessorKey: 'code' as const,
      cell: (row: BOM) => <span className="font-mono">{row.code}</span>,
    },
    {
      header: 'Nom',
      accessorKey: 'name' as const,
    },
    {
      header: 'Produit',
      accessorKey: 'product_name' as const,
    },
    {
      header: 'Version',
      accessorKey: 'bom_version' as const,
      cell: (row: BOM) => (
        <span className="flex items-center gap-2">
          v{row.bom_version}
          {row.is_current && <Badge variant="outline">Actuelle</Badge>}
        </span>
      ),
    },
    {
      header: 'Statut',
      accessorKey: 'status' as const,
      cell: (row: BOM) => <StatusBadge status={row.status} type="bom" />,
    },
    {
      header: 'Cout total',
      accessorKey: 'total_cost' as const,
      cell: (row: BOM) => `${toNum(row.total_cost).toFixed(2)} EUR`,
    },
    {
      header: 'Lignes',
      accessorKey: 'lines' as const,
      cell: (row: BOM) => row.lines?.length || 0,
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
            onChange={(e) => setSearch(e.target.value)}
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

  const columns = [
    {
      header: 'Code',
      accessorKey: 'code' as const,
      cell: (row: Workcenter) => <span className="font-mono">{row.code}</span>,
    },
    {
      header: 'Nom',
      accessorKey: 'name' as const,
    },
    {
      header: 'Type',
      accessorKey: 'workcenter_type' as const,
    },
    {
      header: 'Etat',
      accessorKey: 'state' as const,
      cell: (row: Workcenter) => <StatusBadge status={row.state} type="workcenter" />,
    },
    {
      header: 'Capacite',
      accessorKey: 'capacity' as const,
    },
    {
      header: 'Efficacite',
      accessorKey: 'efficiency' as const,
      cell: (row: Workcenter) => `${(toNum(row.efficiency) * 100).toFixed(0)}%`,
    },
    {
      header: 'Cout horaire',
      accessorKey: 'hourly_cost' as const,
      cell: (row: Workcenter) => `${toNum(row.hourly_cost).toFixed(2)} EUR/h`,
    },
    {
      header: 'Operateur',
      accessorKey: 'current_operator_name' as const,
      cell: (row: Workcenter) => row.current_operator_name || '-',
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
          <Button variant="outline">
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
export { manufacturingMeta } from './meta';
