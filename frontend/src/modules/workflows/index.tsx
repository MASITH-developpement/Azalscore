// @ts-nocheck

/**
 * AZALSCORE Module - Workflows
 * Interface principale du module BPM/Workflows
 */

import React, { useState } from 'react';
import { Button } from '@ui/actions';
import { Card, PageWrapper, Grid } from '@ui/layout';
import { Input, Select } from '@ui/forms';
import { DataTable } from '@ui/tables';
import { LoadingState, EmptyState } from '@ui/components/StateViews';
import type { TableColumn } from '@/types';
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
    <Grid cols={4} gap="md">
      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-orange-100 rounded-lg">
            <Clock className="h-5 w-5 text-orange-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Taches en attente</p>
            <p className="text-2xl font-bold">{stats.pending_tasks}</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Play className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">En cours</p>
            <p className="text-2xl font-bold">{stats.running_instances}</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <CheckCircle className="h-5 w-5 text-green-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Termines</p>
            <p className="text-2xl font-bold">{stats.completed_today}</p>
          </div>
        </div>
      </Card>

      <Card>
        <div className="p-4 flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <GitBranch className="h-5 w-5 text-purple-600" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Workflows actifs</p>
            <p className="text-2xl font-bold">{stats.active_workflows}</p>
          </div>
        </div>
      </Card>
    </Grid>
  );
}

// ============================================================================
// MY TASKS TAB
// ============================================================================

function MyTasksTab() {
  const { data: tasks, isLoading } = useMyTasks();
  const completeTask = useCompleteTask();
  const startTask = useStartTask();

  const columns: TableColumn<TaskInstance>[] = [
    {
      id: 'step_id',
      header: 'Tache',
      accessor: 'step_id',
      render: (_, row) => (
        <div>
          <p className="font-medium">{row.step_id}</p>
          <p className="text-sm text-muted-foreground">Instance: {row.instance_id}</p>
        </div>
      ),
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (_, row) => <StatusBadge status={row.status} type="task" />,
    },
    {
      id: 'assigned_to',
      header: 'Assigne a',
      accessor: 'assigned_to',
      render: (_, row) => (
        <div className="flex items-center gap-2">
          <User className="h-4 w-4" />
          {row.assigned_to || '-'}
        </div>
      ),
    },
    {
      id: 'due_at',
      header: 'Echeance',
      accessor: 'due_at',
      render: (_, row) => {
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
      id: 'actions',
      header: 'Actions',
      accessor: 'task_id',
      render: (_, row) => (
        <div className="flex gap-2">
          {row.status === 'assigned' && (
            <Button
              size="sm"
              variant="secondary"
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
        message="Vous n'avez pas de taches assignees pour le moment."
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

  const columns: TableColumn<WorkflowDefinition>[] = [
    {
      id: 'name',
      header: 'Nom',
      accessor: 'name',
      render: (_, row) => (
        <div>
          <p className="font-medium">{row.name}</p>
          <p className="text-sm text-muted-foreground">{row.category}</p>
        </div>
      ),
    },
    {
      id: 'version',
      header: 'Version',
      accessor: 'version',
      render: (_, row) => `v${row.version}`,
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (_, row) => <StatusBadge status={row.status} type="workflow" />,
    },
    {
      id: 'steps',
      header: 'Etapes',
      accessor: 'steps',
      render: (_, row) => row.steps?.length || 0,
    },
    {
      id: 'sla_hours',
      header: 'SLA',
      accessor: 'sla_hours',
      render: (_, row) => row.sla_hours ? `${row.sla_hours}h` : '-',
    },
    {
      id: 'updated_at',
      header: 'Mise a jour',
      accessor: 'updated_at',
      render: (_, row) => formatDate(row.updated_at || row.created_at),
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
            onChange={(value) => setSearch(value)}
          />
        </div>
        <Button leftIcon={<Plus className="h-4 w-4" />}>
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
          message="Creez votre premier workflow pour automatiser vos processus metier."
          action={{
            label: 'Creer un workflow',
            onClick: () => {},
            icon: <Plus className="h-4 w-4" />,
          }}
        />
      )}
    </div>
  );
}

// ============================================================================
// INSTANCES TAB
// ============================================================================

function InstancesTab() {
  const [statusFilter, setStatusFilter] = useState('');
  const { data, isLoading } = useInstanceList({
    status: (statusFilter || undefined) as InstanceStatus | undefined,
  });

  const columns: TableColumn<WorkflowInstance>[] = [
    {
      id: 'instance_id',
      header: 'Instance',
      accessor: 'instance_id',
      render: (_, row) => (
        <div>
          <p className="font-mono text-sm">{row.instance_id}</p>
          <p className="text-sm text-muted-foreground">{row.workflow_name}</p>
        </div>
      ),
    },
    {
      id: 'reference_name',
      header: 'Reference',
      accessor: 'reference_name',
      render: (_, row) => row.reference_name || row.reference_id || '-',
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (_, row) => <StatusBadge status={row.status} type="instance" />,
    },
    {
      id: 'initiated_by',
      header: 'Initie par',
      accessor: 'initiated_by',
    },
    {
      id: 'initiated_at',
      header: 'Demarre',
      accessor: 'initiated_at',
      render: (_, row) => formatDateTime(row.initiated_at),
    },
    {
      id: 'current_step_ids',
      header: 'Etape',
      accessor: 'current_step_ids',
      render: (_, row) => row.current_step_ids?.join(', ') || '-',
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
          onChange={(value) => setStatusFilter(value)}
          options={[
            { value: '', label: 'Tous les statuts' },
            ...Object.entries(INSTANCE_STATUS_CONFIG).map(([key, { label }]) => ({ value: key, label }))
          ]}
        />
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
          message="Aucune instance de workflow en cours."
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
        <Grid cols={4} gap="md">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </Grid>
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
    <PageWrapper
      title="Workflows (BPM)"
      subtitle="Gestion des processus metier et automatisation"
      actions={
        <Button leftIcon={<Plus className="h-4 w-4" />}>
          Nouveau workflow
        </Button>
      }
    >
      <div className="space-y-6">
        <StatsCards stats={stats} />

        {stats.sla_breach_rate > 0.1 && (
          <Card className="border-orange-200 bg-orange-50">
            <div className="p-4 flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <span className="font-medium text-orange-800">
                {(stats.sla_breach_rate * 100).toFixed(1)}% des instances ont depasse leur SLA
              </span>
            </div>
          </Card>
        )}

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
    </PageWrapper>
  );
}

// Named exports
export { WorkflowsModule };
export * from './types';
export * from './hooks';
export * from './api';
export { workflowsMeta } from './meta';
