/**
 * AZALSCORE Module - Workflows
 * Interface principale du module BPM/Workflows
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
  Workflow,
  CheckSquare,
  GitBranch,
  Play,
  Plus,
  Search,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  User,
  ArrowRight,
} from 'lucide-react';
import {
  useWorkflowDashboard,
  useWorkflowList,
  useInstanceList,
  useMyTasks,
  useCompleteTask,
  useStartTask,
} from './hooks';
import type {
  WorkflowDefinition,
  WorkflowInstance,
  TaskInstance,
  WorkflowStatus,
  InstanceStatus,
  TaskStatus,
} from './types';
import {
  WORKFLOW_STATUS_CONFIG,
  INSTANCE_STATUS_CONFIG,
  TASK_STATUS_CONFIG,
} from './types';

// ============================================================================
// HELPERS
// ============================================================================

function formatDateTime(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleString('fr-FR');
}

function formatDate(date: string | undefined): string {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
}

// ============================================================================
// STATUS BADGE
// ============================================================================

interface StatusBadgeProps {
  status: WorkflowStatus | InstanceStatus | TaskStatus;
  type: 'workflow' | 'instance' | 'task';
}

function StatusBadge({ status, type }: StatusBadgeProps) {
  let config: { label: string; color: string };

  switch (type) {
    case 'workflow':
      config = WORKFLOW_STATUS_CONFIG[status as WorkflowStatus];
      break;
    case 'instance':
      config = INSTANCE_STATUS_CONFIG[status as InstanceStatus];
      break;
    case 'task':
      config = TASK_STATUS_CONFIG[status as TaskStatus];
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
    pending_tasks: number;
    running_instances: number;
    completed_today: number;
    sla_breach_rate: number;
    total_workflows: number;
    active_workflows: number;
  };
}

function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Clock className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Taches en attente</p>
              <p className="text-2xl font-bold">{stats.pending_tasks}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Play className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">En cours</p>
              <p className="text-2xl font-bold">{stats.running_instances}</p>
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
              <GitBranch className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Workflows actifs</p>
              <p className="text-2xl font-bold">{stats.active_workflows}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// MY TASKS TAB
// ============================================================================

function MyTasksTab() {
  const { data: tasks, isLoading } = useMyTasks();
  const completeTask = useCompleteTask();
  const startTask = useStartTask();

  const columns = [
    {
      header: 'Tache',
      accessorKey: 'step_id' as const,
      cell: (row: TaskInstance) => (
        <div>
          <p className="font-medium">{row.step_id}</p>
          <p className="text-sm text-muted-foreground">Instance: {row.instance_id}</p>
        </div>
      ),
    },
    {
      header: 'Statut',
      accessorKey: 'status' as const,
      cell: (row: TaskInstance) => <StatusBadge status={row.status} type="task" />,
    },
    {
      header: 'Assigne a',
      accessorKey: 'assigned_to' as const,
      cell: (row: TaskInstance) => (
        <div className="flex items-center gap-2">
          <User className="h-4 w-4" />
          {row.assigned_to || '-'}
        </div>
      ),
    },
    {
      header: 'Echeance',
      accessorKey: 'due_at' as const,
      cell: (row: TaskInstance) => {
        if (!row.due_at) return '-';
        const isOverdue = new Date(row.due_at) < new Date();
        return (
          <span className={isOverdue ? 'text-red-600 font-medium' : ''}>
            {formatDateTime(row.due_at)}
          </span>
        );
      },
    },
    {
      header: 'Actions',
      accessorKey: 'task_id' as const,
      cell: (row: TaskInstance) => (
        <div className="flex gap-2">
          {row.status === 'assigned' && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => startTask.mutate(row.task_id)}
            >
              Demarrer
            </Button>
          )}
          {row.status === 'in_progress' && (
            <Button
              size="sm"
              onClick={() => completeTask.mutate({ id: row.task_id, data: { outcome: 'approved' } })}
            >
              Approuver
            </Button>
          )}
        </div>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (!tasks || tasks.length === 0) {
    return (
      <EmptyState
        icon={<CheckSquare className="h-12 w-12" />}
        title="Aucune tache en attente"
        description="Vous n'avez pas de taches assignees pour le moment."
      />
    );
  }

  return (
    <DataTable
      data={tasks}
      columns={columns}
      keyField="task_id"
    />
  );
}

// ============================================================================
// WORKFLOWS TAB
// ============================================================================

function WorkflowsTab() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useWorkflowList({ search: search || undefined });

  const columns = [
    {
      header: 'Nom',
      accessorKey: 'name' as const,
      cell: (row: WorkflowDefinition) => (
        <div>
          <p className="font-medium">{row.name}</p>
          <p className="text-sm text-muted-foreground">{row.category}</p>
        </div>
      ),
    },
    {
      header: 'Version',
      accessorKey: 'version' as const,
      cell: (row: WorkflowDefinition) => `v${row.version}`,
    },
    {
      header: 'Statut',
      accessorKey: 'status' as const,
      cell: (row: WorkflowDefinition) => <StatusBadge status={row.status} type="workflow" />,
    },
    {
      header: 'Etapes',
      accessorKey: 'steps' as const,
      cell: (row: WorkflowDefinition) => row.steps?.length || 0,
    },
    {
      header: 'SLA',
      accessorKey: 'sla_hours' as const,
      cell: (row: WorkflowDefinition) => row.sla_hours ? `${row.sla_hours}h` : '-',
    },
    {
      header: 'Mise a jour',
      accessorKey: 'updated_at' as const,
      cell: (row: WorkflowDefinition) => formatDate(row.updated_at || row.created_at),
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
            placeholder="Rechercher un workflow..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Nouveau workflow
        </Button>
      </div>

      {data?.items && data.items.length > 0 ? (
        <DataTable
          data={data.items}
          columns={columns}
          keyField="workflow_id"
        />
      ) : (
        <EmptyState
          icon={<GitBranch className="h-12 w-12" />}
          title="Aucun workflow"
          description="Creez votre premier workflow pour automatiser vos processus metier."
          action={
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Creer un workflow
            </Button>
          }
        />
      )}
    </div>
  );
}

// ============================================================================
// INSTANCES TAB
// ============================================================================

function InstancesTab() {
  const [statusFilter, setStatusFilter] = useState<InstanceStatus | ''>('');
  const { data, isLoading } = useInstanceList({
    status: statusFilter || undefined,
  });

  const columns = [
    {
      header: 'Instance',
      accessorKey: 'instance_id' as const,
      cell: (row: WorkflowInstance) => (
        <div>
          <p className="font-mono text-sm">{row.instance_id}</p>
          <p className="text-sm text-muted-foreground">{row.workflow_name}</p>
        </div>
      ),
    },
    {
      header: 'Reference',
      accessorKey: 'reference_name' as const,
      cell: (row: WorkflowInstance) => row.reference_name || row.reference_id || '-',
    },
    {
      header: 'Statut',
      accessorKey: 'status' as const,
      cell: (row: WorkflowInstance) => <StatusBadge status={row.status} type="instance" />,
    },
    {
      header: 'Initie par',
      accessorKey: 'initiated_by' as const,
    },
    {
      header: 'Demarre',
      accessorKey: 'initiated_at' as const,
      cell: (row: WorkflowInstance) => formatDateTime(row.initiated_at),
    },
    {
      header: 'Etape',
      accessorKey: 'current_step_ids' as const,
      cell: (row: WorkflowInstance) => row.current_step_ids?.join(', ') || '-',
    },
  ];

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Select
          value={statusFilter}
          onValueChange={(value) => setStatusFilter(value as InstanceStatus | '')}
          className="w-48"
        >
          <option value="">Tous les statuts</option>
          {Object.entries(INSTANCE_STATUS_CONFIG).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </Select>
      </div>

      {data?.items && data.items.length > 0 ? (
        <DataTable
          data={data.items}
          columns={columns}
          keyField="instance_id"
        />
      ) : (
        <EmptyState
          icon={<Play className="h-12 w-12" />}
          title="Aucune instance"
          description="Aucune instance de workflow en cours."
        />
      )}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function WorkflowsModule() {
  const { data: dashboard, isLoading } = useWorkflowDashboard();

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
    pending_tasks: 0,
    running_instances: 0,
    completed_today: 0,
    sla_breach_rate: 0,
    total_workflows: 0,
    active_workflows: 0,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Workflow className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Workflows (BPM)</h1>
            <p className="text-muted-foreground">
              Gestion des processus metier et automatisation
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nouveau workflow
          </Button>
        </div>
      </div>

      {/* Stats */}
      <StatsCards stats={stats} />

      {/* SLA Alert */}
      {stats.sla_breach_rate > 0.1 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <span className="font-medium text-orange-800">
                {(stats.sla_breach_rate * 100).toFixed(1)}% des instances ont depasse leur SLA
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <Tabs defaultValue="tasks">
        <TabsList>
          <TabsTrigger value="tasks">
            <CheckSquare className="h-4 w-4 mr-2" />
            Mes taches
            {stats.pending_tasks > 0 && (
              <Badge className="ml-2 bg-orange-100 text-orange-800">{stats.pending_tasks}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="workflows">
            <GitBranch className="h-4 w-4 mr-2" />
            Workflows
          </TabsTrigger>
          <TabsTrigger value="instances">
            <Play className="h-4 w-4 mr-2" />
            Instances
          </TabsTrigger>
        </TabsList>

        <TabsContent value="tasks" className="mt-6">
          <MyTasksTab />
        </TabsContent>

        <TabsContent value="workflows" className="mt-6">
          <WorkflowsTab />
        </TabsContent>

        <TabsContent value="instances" className="mt-6">
          <InstancesTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Named exports
export { WorkflowsModule };
export * from './types';
export * from './hooks';
export * from './api';
export { workflowsMeta } from './meta';
