import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input, TextArea } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import type { TableColumn } from '@/types';
import { Folder, ClipboardList, CheckCircle, RefreshCw, Clock, BarChart3, DollarSign } from 'lucide-react';

// ============================================================================
// LOCAL COMPONENTS
// ============================================================================

const Badge: React.FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <span className={`azals-badge azals-badge--${color}`}>{children}</span>
);

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

// ============================================================================
// TYPES
// ============================================================================

interface Project {
  id: string;
  code: string;
  name: string;
  description?: string;
  client_id?: string;
  client_name?: string;
  manager_id?: string;
  manager_name?: string;
  status: 'DRAFT' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'CANCELLED';
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  start_date?: string;
  end_date?: string;
  budget?: number;
  spent?: number;
  progress: number;
  currency: string;
  created_at: string;
}

interface Task {
  id: string;
  project_id: string;
  project_name?: string;
  title: string;
  description?: string;
  assignee_id?: string;
  assignee_name?: string;
  status: 'TODO' | 'IN_PROGRESS' | 'REVIEW' | 'DONE';
  priority: 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';
  due_date?: string;
  estimated_hours?: number;
  logged_hours?: number;
  created_at: string;
}

interface TimeEntry {
  id: string;
  project_id: string;
  project_name?: string;
  task_id?: string;
  task_title?: string;
  user_id: string;
  user_name: string;
  date: string;
  hours: number;
  description?: string;
  is_billable: boolean;
  created_at: string;
}

interface ProjectStats {
  active_projects: number;
  total_projects: number;
  total_tasks: number;
  tasks_completed: number;
  tasks_in_progress: number;
  hours_this_week: number;
  hours_this_month: number;
  budget_used_percent: number;
}

// ============================================================================
// CONSTANTES
// ============================================================================

const PROJECT_STATUS = [
  { value: 'DRAFT', label: 'Brouillon' },
  { value: 'ACTIVE', label: 'En cours' },
  { value: 'PAUSED', label: 'En pause' },
  { value: 'COMPLETED', label: 'Terminé' },
  { value: 'CANCELLED', label: 'Annulé' }
];

const TASK_STATUS = [
  { value: 'TODO', label: 'À faire' },
  { value: 'IN_PROGRESS', label: 'En cours' },
  { value: 'REVIEW', label: 'En revue' },
  { value: 'DONE', label: 'Terminé' }
];

const PRIORITIES = [
  { value: 'LOW', label: 'Basse' },
  { value: 'NORMAL', label: 'Normale' },
  { value: 'HIGH', label: 'Haute' },
  { value: 'URGENT', label: 'Urgente' }
];

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'gray',
  ACTIVE: 'blue',
  PAUSED: 'orange',
  COMPLETED: 'green',
  CANCELLED: 'red',
  TODO: 'gray',
  IN_PROGRESS: 'blue',
  REVIEW: 'purple',
  DONE: 'green'
};

const PRIORITY_COLORS: Record<string, string> = {
  LOW: 'gray',
  NORMAL: 'blue',
  HIGH: 'orange',
  URGENT: 'red'
};

// ============================================================================
// HELPERS
// ============================================================================

const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);
};

const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

const formatHours = (hours: number): string => {
  return `${hours.toFixed(1)}h`;
};

// Navigation inter-modules
const navigateTo = (view: string, params?: Record<string, any>) => {
  window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view, params } }));
};

// ============================================================================
// API HOOKS
// ============================================================================

const useProjectStats = () => {
  return useQuery({
    queryKey: ['projects', 'stats'],
    queryFn: async () => {
      const response = await api.get<ProjectStats>('/v1/projects/summary').then(r => r.data);
      return response;
    }
  });
};

const useProjects = (filters?: { status?: string; client_id?: string }) => {
  return useQuery({
    queryKey: ['projects', 'list', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.client_id) params.append('client_id', filters.client_id);
      const queryString = params.toString();
      const url = queryString ? `/v1/projects?${queryString}` : '/v1/projects';
      const response = await api.get<{ items: Project[] } | Project[]>(url).then(r => r.data);
      return (response as any)?.items || response as Project[];
    }
  });
};

const useTasks = (filters?: { status?: string; project_id?: string; assignee_id?: string }) => {
  return useQuery({
    queryKey: ['projects', 'tasks', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.project_id) params.append('project_id', filters.project_id);
      if (filters?.assignee_id) params.append('assignee_id', filters.assignee_id);
      const queryString = params.toString();
      const url = queryString ? `/v1/projects/tasks?${queryString}` : '/v1/projects/tasks';
      const response = await api.get<{ items: Task[] } | Task[]>(url).then(r => r.data);
      return (response as any)?.items || response as Task[];
    }
  });
};

const useTimeEntries = (filters?: { project_id?: string; date_from?: string; date_to?: string }) => {
  return useQuery({
    queryKey: ['projects', 'time-entries', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.project_id) params.append('project_id', filters.project_id);
      if (filters?.date_from) params.append('date_from', filters.date_from);
      if (filters?.date_to) params.append('date_to', filters.date_to);
      const queryString = params.toString();
      const url = queryString ? `/v1/projects/time-entries?${queryString}` : '/v1/projects/time-entries';
      const response = await api.get<TimeEntry[]>(url).then(r => r.data);
      return response;
    }
  });
};

const useCreateProject = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Project>) => {
      return api.post<Project>('/v1/projects', data).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    }
  });
};

const useUpdateTaskStatus = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      return api.patch<Task>(`/v1/projects/tasks/${id}/status`, { status }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', 'tasks'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'stats'] });
    }
  });
};

const useLogTime = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { project_id: string; task_id?: string; date: string; hours: number; description?: string; is_billable?: boolean }) => {
      return api.post<TimeEntry>('/v1/projects/time-entries', data).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', 'time-entries'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'stats'] });
    }
  });
};

// ============================================================================
// COMPOSANTS
// ============================================================================

const ProjectsListView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: projects = [], isLoading } = useProjects({
    status: filterStatus || undefined
  });

  const columns: TableColumn<Project>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Projet', accessor: 'name' },
    { id: 'client_name', header: 'Client', accessor: 'client_name', render: (v) => (v as string) || '-' },
    { id: 'manager_name', header: 'Responsable', accessor: 'manager_name', render: (v) => (v as string) || '-' },
    { id: 'priority', header: 'Priorité', accessor: 'priority', render: (v) => {
      const val = v as string;
      const info = PRIORITIES.find(p => p.value === val);
      return <Badge color={PRIORITY_COLORS[val] || 'gray'}>{info?.label || val}</Badge>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const val = v as string;
      const info = PROJECT_STATUS.find(s => s.value === val);
      return <Badge color={STATUS_COLORS[val] || 'gray'}>{info?.label || val}</Badge>;
    }},
    { id: 'progress', header: 'Avancement', accessor: 'progress', render: (v) => {
      const val = v as number;
      return (
        <div className="w-24">
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${val}%` }}
              />
            </div>
            <span className="text-sm">{val}%</span>
          </div>
        </div>
      );
    }},
    { id: 'end_date', header: 'Échéance', accessor: 'end_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'budget', header: 'Budget', accessor: 'budget', render: (v, row: Project) => (v as number) ? formatCurrency(v as number, row.currency) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: () => <Button size="sm" variant="secondary">Détail</Button> }
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Projets</h3>
        <div className="flex gap-2">
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...PROJECT_STATUS]}
            className="w-36"
          />
          <Button>Nouveau projet</Button>
        </div>
      </div>
      <DataTable columns={columns} data={projects} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const TasksView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterProject, setFilterProject] = useState<string>('');
  const { data: tasks = [], isLoading } = useTasks({
    status: filterStatus || undefined,
    project_id: filterProject || undefined
  });
  const { data: projects = [] } = useProjects();
  const updateStatus = useUpdateTaskStatus();

  const columns: TableColumn<Task>[] = [
    { id: 'title', header: 'Tâche', accessor: 'title' },
    { id: 'project_name', header: 'Projet', accessor: 'project_name', render: (v) => (v as string) || '-' },
    { id: 'assignee_name', header: 'Assigné à', accessor: 'assignee_name', render: (v) => (v as string) || 'Non assigné' },
    { id: 'priority', header: 'Priorité', accessor: 'priority', render: (v) => {
      const val = v as string;
      const info = PRIORITIES.find(p => p.value === val);
      return <Badge color={PRIORITY_COLORS[val] || 'gray'}>{info?.label || val}</Badge>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const val = v as string;
      const info = TASK_STATUS.find(s => s.value === val);
      return <Badge color={STATUS_COLORS[val] || 'gray'}>{info?.label || val}</Badge>;
    }},
    { id: 'due_date', header: 'Échéance', accessor: 'due_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'estimated_hours', header: 'Est.', accessor: 'estimated_hours', render: (v) => (v as number) ? formatHours(v as number) : '-' },
    { id: 'logged_hours', header: 'Réel', accessor: 'logged_hours', render: (v) => (v as number) ? formatHours(v as number) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row: Task) => (
      <div className="flex gap-1">
        {row.status === 'TODO' && (
          <Button size="sm" variant="primary" onClick={() => updateStatus.mutate({ id: row.id, status: 'IN_PROGRESS' })}>Démarrer</Button>
        )}
        {row.status === 'IN_PROGRESS' && (
          <Button size="sm" variant="warning" onClick={() => updateStatus.mutate({ id: row.id, status: 'REVIEW' })}>Soumettre</Button>
        )}
        {row.status === 'REVIEW' && (
          <Button size="sm" variant="success" onClick={() => updateStatus.mutate({ id: row.id, status: 'DONE' })}>Valider</Button>
        )}
      </div>
    )}
  ];

  return (
    <Card>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Tâches</h3>
        <div className="flex gap-2">
          <Select
            value={filterProject}
            onChange={(v) => setFilterProject(v)}
            options={[
              { value: '', label: 'Tous projets' },
              ...projects.map((p: Project) => ({ value: p.id, label: p.name }))
            ]}
            className="w-40"
          />
          <Select
            value={filterStatus}
            onChange={(v) => setFilterStatus(v)}
            options={[{ value: '', label: 'Tous statuts' }, ...TASK_STATUS]}
            className="w-32"
          />
          <Button>Nouvelle tâche</Button>
        </div>
      </div>
      <DataTable columns={columns} data={tasks} isLoading={isLoading} keyField="id" />
    </Card>
  );
};

const TimesheetView: React.FC = () => {
  const [filterProject, setFilterProject] = useState<string>('');
  const [showLogModal, setShowLogModal] = useState(false);
  const [formProjectId, setFormProjectId] = useState<string>('');
  const [formDate, setFormDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [formHours, setFormHours] = useState<string>('');
  const [formDescription, setFormDescription] = useState<string>('');
  const { data: timeEntries = [], isLoading } = useTimeEntries({
    project_id: filterProject || undefined
  });
  const { data: projects = [] } = useProjects();
  const logTime = useLogTime();

  const columns: TableColumn<TimeEntry>[] = [
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'project_name', header: 'Projet', accessor: 'project_name' },
    { id: 'task_title', header: 'Tâche', accessor: 'task_title', render: (v) => (v as string) || '-' },
    { id: 'user_name', header: 'Utilisateur', accessor: 'user_name' },
    { id: 'hours', header: 'Heures', accessor: 'hours', render: (v) => formatHours(v as number) },
    { id: 'description', header: 'Description', accessor: 'description', render: (v) => {
      const val = v as string;
      return (
        <span className="text-sm">{val?.length > 50 ? val.substring(0, 50) + '...' : val || '-'}</span>
      );
    }},
    { id: 'is_billable', header: 'Facturable', accessor: 'is_billable', render: (v) => (
      <Badge color={(v as boolean) ? 'green' : 'gray'}>{(v as boolean) ? 'Oui' : 'Non'}</Badge>
    )}
  ];

  const handleLogTime = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    logTime.mutate({
      project_id: formProjectId,
      task_id: formData.get('task_id') as string || undefined,
      date: formDate,
      hours: parseFloat(formHours),
      description: formDescription || undefined,
      is_billable: formData.get('is_billable') === 'true'
    }, {
      onSuccess: () => setShowLogModal(false)
    });
  };

  return (
    <>
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Feuilles de temps</h3>
          <div className="flex gap-2">
            <Select
              value={filterProject}
              onChange={(v) => setFilterProject(v)}
              options={[
                { value: '', label: 'Tous projets' },
                ...projects.map((p: Project) => ({ value: p.id, label: p.name }))
              ]}
              className="w-40"
            />
            <Button onClick={() => setShowLogModal(true)}>Saisir du temps</Button>
          </div>
        </div>
        <DataTable columns={columns} data={timeEntries} isLoading={isLoading} keyField="id" />
      </Card>

      {showLogModal && (
        <Modal isOpen={true} onClose={() => setShowLogModal(false)} title="Saisir du temps">
          <form onSubmit={handleLogTime}>
            <div className="space-y-4">
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Projet *</label>
                <Select
                  value={formProjectId}
                  onChange={(v) => setFormProjectId(v)}
                  options={[
                    { value: '', label: 'Sélectionner...' },
                    ...projects.map((p: Project) => ({ value: p.id, label: p.name }))
                  ]}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="azals-field">
                  <label className="block text-sm font-medium mb-1">Date *</label>
                  <input
                    type="date"
                    name="date"
                    required
                    value={formDate}
                    onChange={(e) => setFormDate(e.target.value)}
                    className="azals-input"
                  />
                </div>
                <div className="azals-field">
                  <label className="block text-sm font-medium mb-1">Heures *</label>
                  <Input
                    type="number"
                    value={formHours}
                    onChange={(v) => setFormHours(v)}
                    placeholder="0.00"
                    min={0.25}
                    max={24}
                  />
                </div>
              </div>
              <div className="azals-field">
                <label className="block text-sm font-medium mb-1">Description</label>
                <TextArea
                  rows={2}
                  placeholder="Travail effectué..."
                  value={formDescription}
                  onChange={(v) => setFormDescription(v)}
                />
              </div>
              <div>
                <label className="flex items-center gap-2">
                  <input type="checkbox" name="is_billable" value="true" defaultChecked />
                  <span className="text-sm">Temps facturable</span>
                </label>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="secondary" onClick={() => setShowLogModal(false)}>Annuler</Button>
                <Button type="submit" disabled={logTime.isPending}>Enregistrer</Button>
              </div>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
};

// ============================================================================
// MODULE PRINCIPAL
// ============================================================================

type View = 'dashboard' | 'projects' | 'tasks' | 'timesheet';

const ProjectsModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const { data: stats } = useProjectStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'projects', label: 'Projets' },
    { id: 'tasks', label: 'Tâches' },
    { id: 'timesheet', label: 'Temps' }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'projects':
        return <ProjectsListView />;
      case 'tasks':
        return <TasksView />;
      case 'timesheet':
        return <TimesheetView />;
      default:
        return (
          <div className="space-y-4">
            <Grid cols={4}>
              <StatCard
                title="Projets actifs"
                value={String(stats?.active_projects || 0)}
                icon={<Folder className="h-5 w-5" />}
                variant="default"
                onClick={() => setCurrentView('projects')}
              />
              <StatCard
                title="Tâches totales"
                value={String(stats?.total_tasks || 0)}
                icon={<ClipboardList className="h-5 w-5" />}
                variant="default"
                onClick={() => setCurrentView('tasks')}
              />
              <StatCard
                title="Tâches terminées"
                value={String(stats?.tasks_completed || 0)}
                icon={<CheckCircle className="h-5 w-5" />}
                variant="success"
              />
              <StatCard
                title="En cours"
                value={String(stats?.tasks_in_progress || 0)}
                icon={<RefreshCw className="h-5 w-5" />}
                variant="warning"
              />
            </Grid>

            <Grid cols={3}>
              <StatCard
                title="Heures (semaine)"
                value={formatHours(stats?.hours_this_week || 0)}
                icon={<Clock className="h-5 w-5" />}
                variant="default"
                onClick={() => setCurrentView('timesheet')}
              />
              <StatCard
                title="Heures (mois)"
                value={formatHours(stats?.hours_this_month || 0)}
                icon={<BarChart3 className="h-5 w-5" />}
                variant="default"
              />
              <StatCard
                title="Budget utilisé"
                value={`${stats?.budget_used_percent || 0}%`}
                icon={<DollarSign className="h-5 w-5" />}
                variant={stats?.budget_used_percent && stats.budget_used_percent > 90 ? 'danger' : 'success'}
              />
            </Grid>
          </div>
        );
    }
  };

  return (
    <PageWrapper title="Projets" subtitle="Gestion de projets et suivi du temps">
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

export default ProjectsModule;
