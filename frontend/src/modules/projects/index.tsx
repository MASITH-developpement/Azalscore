/**
 * AZALSCORE Module - Projects
 * Gestion de projets et suivi du temps
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button, Modal } from '@ui/actions';
import { Select, Input, TextArea } from '@ui/forms';
import { StatCard } from '@ui/dashboards';
import {
  BaseViewStandard,
  type TabDefinition,
  type InfoBarItem,
  type SidebarSection,
  type ActionDefinition,
  type SemanticColor
} from '@ui/standards';
import type { TableColumn } from '@/types';
import {
  Folder, ClipboardList, CheckCircle, RefreshCw, Clock, BarChart3,
  DollarSign, ArrowLeft, Edit, Send, Printer, Trash2, Target,
  User, Sparkles, FileText, CheckSquare
} from 'lucide-react';
import { LoadingState, ErrorState } from '@ui/components/StateViews';

// Types et helpers
import type { Project, Task, TimeEntry, ProjectStats } from './types';
import {
  PROJECT_STATUS_CONFIG, TASK_STATUS_CONFIG, PRIORITY_CONFIG,
  getDaysRemaining, getBudgetUsedPercent, getTaskCountByStatus,
  getTotalLoggedHours, isProjectOverdue, isProjectNearDeadline,
  isBudgetOverrun
} from './types';
import { formatDate, formatCurrency, formatHours, formatPercent } from '@/utils/formatters';

// Composants tabs
import {
  ProjectInfoTab,
  ProjectTasksTab,
  ProjectTimesheetTab,
  ProjectDocsTab,
  ProjectHistoryTab,
  ProjectIATab
} from './components';

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
// API HOOKS
// ============================================================================

const useProjectStats = () => {
  return useQuery({
    queryKey: ['projects', 'stats'],
    queryFn: async () => {
      const response = await api.get<ProjectStats>('/v3/projects/summary').then(r => r.data);
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
      const url = queryString ? `/v3/projects?${queryString}` : '/v3/projects';
      const response = await api.get<{ items: Project[] }>(url).then(r => r.data);
      return response?.items || [];
    }
  });
};

const useProject = (id: string) => {
  return useQuery({
    queryKey: ['projects', 'detail', id],
    queryFn: async () => {
      const response = await api.get<Project>(`/v3/projects/${id}`).then(r => r.data);
      return response;
    },
    enabled: !!id
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
      const url = queryString ? `/v3/projects/tasks?${queryString}` : '/v3/projects/tasks';
      const response = await api.get<{ items: Task[] }>(url).then(r => r.data);
      return response?.items || [];
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
      const url = queryString ? `/v3/projects/time-entries?${queryString}` : '/v3/projects/time-entries';
      const response = await api.get<TimeEntry[]>(url).then(r => r.data);
      return response;
    }
  });
};

const useCreateProject = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<Project>) => {
      return api.post<Project>('/v3/projects', data).then(r => r.data);
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
      return api.patch<Task>(`/v3/projects/tasks/${id}/status`, { status }).then(r => r.data);
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
      return api.post<TimeEntry>('/v3/projects/time-entries', data).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', 'time-entries'] });
      queryClient.invalidateQueries({ queryKey: ['projects', 'stats'] });
    }
  });
};

// ============================================================================
// PROJECT DETAIL VIEW (BaseViewStandard)
// ============================================================================

interface ProjectDetailViewProps {
  projectId: string;
  onBack: () => void;
  onEdit?: () => void;
}

const ProjectDetailView: React.FC<ProjectDetailViewProps> = ({ projectId, onBack, onEdit }) => {
  const { data: project, isLoading, error, refetch } = useProject(projectId);

  if (isLoading) {
    return <LoadingState onRetry={() => refetch()} message="Chargement du projet..." />;
  }

  if (error || !project) {
    return (
      <ErrorState
        message="Erreur lors du chargement du projet"
        onRetry={() => refetch()}
        onBack={onBack}
      />
    );
  }

  // Configuration statut
  const statusConfig = PROJECT_STATUS_CONFIG[project.status];
  const statusColorMap: Record<string, SemanticColor> = {
    gray: 'gray',
    blue: 'blue',
    green: 'green',
    orange: 'orange',
    red: 'red',
    purple: 'purple'
  };

  // Calculs
  const taskCounts = getTaskCountByStatus(project);
  const totalTasks = (project.tasks || []).length;
  const daysRemaining = getDaysRemaining(project);
  const budgetPercent = getBudgetUsedPercent(project);
  const isOverdue = isProjectOverdue(project);
  const isNearDeadline = isProjectNearDeadline(project);
  const budgetOverrun = isBudgetOverrun(project);

  // Tabs
  const tabs: TabDefinition<Project>[] = [
    {
      id: 'info',
      label: 'Informations',
      icon: <Folder size={16} />,
      component: ProjectInfoTab
    },
    {
      id: 'tasks',
      label: 'Taches',
      icon: <CheckSquare size={16} />,
      badge: taskCounts.TODO + taskCounts.IN_PROGRESS,
      component: ProjectTasksTab
    },
    {
      id: 'timesheet',
      label: 'Temps',
      icon: <Clock size={16} />,
      component: ProjectTimesheetTab
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <FileText size={16} />,
      badge: project.documents?.length,
      component: ProjectDocsTab
    },
    {
      id: 'history',
      label: 'Historique',
      icon: <Clock size={16} />,
      component: ProjectHistoryTab
    },
    {
      id: 'ia',
      label: 'Assistant IA',
      icon: <Sparkles size={16} />,
      component: ProjectIATab
    }
  ];

  // Info bar items
  const infoBarItems: InfoBarItem[] = [
    {
      id: 'progress',
      label: 'Avancement',
      value: formatPercent(project.progress),
      valueColor: project.progress >= 100 ? 'green' : project.progress >= 50 ? 'blue' : 'orange'
    },
    {
      id: 'tasks',
      label: 'Taches',
      value: `${taskCounts.DONE}/${totalTasks}`,
      valueColor: taskCounts.DONE === totalTasks ? 'green' : 'blue'
    },
    {
      id: 'budget',
      label: 'Budget',
      value: formatPercent(budgetPercent),
      valueColor: budgetOverrun ? 'red' : budgetPercent > 80 ? 'orange' : 'green'
    },
    {
      id: 'deadline',
      label: 'Echeance',
      value: daysRemaining !== null ? `${daysRemaining}j` : '-',
      valueColor: isOverdue ? 'red' : isNearDeadline ? 'orange' : 'green'
    }
  ];

  // Sidebar sections
  const sidebarSections: SidebarSection[] = [
    {
      id: 'summary',
      title: 'Resume projet',
      items: [
        { id: 'code', label: 'Code', value: project.code },
        { id: 'client', label: 'Client', value: project.client_name || '-' },
        { id: 'manager', label: 'Responsable', value: project.manager_name || '-' },
        { id: 'priority', label: 'Priorite', value: PRIORITY_CONFIG[project.priority].label }
      ]
    },
    {
      id: 'planning',
      title: 'Planning',
      items: [
        { id: 'start', label: 'Debut', value: formatDate(project.start_date) },
        { id: 'end', label: 'Fin prevue', value: formatDate(project.end_date) },
        { id: 'remaining', label: 'Jours restants', value: daysRemaining !== null ? `${daysRemaining}` : '-', highlight: isOverdue || isNearDeadline }
      ]
    },
    {
      id: 'budget',
      title: 'Budget',
      items: [
        { id: 'budget-total', label: 'Budget total', value: formatCurrency(project.budget, project.currency), format: 'currency' as const },
        { id: 'budget-spent', label: 'Depense', value: formatCurrency(project.spent, project.currency), format: 'currency' as const },
        { id: 'budget-remaining', label: 'Reste', value: formatCurrency((project.budget || 0) - (project.spent || 0), project.currency), format: 'currency' as const, highlight: budgetOverrun }
      ]
    },
    {
      id: 'time',
      title: 'Temps',
      items: [
        { id: 'hours', label: 'Heures logguees', value: formatHours(getTotalLoggedHours(project)) },
        { id: 'team', label: 'Equipe', value: `${project.team_members?.length || 0} membre(s)` }
      ]
    }
  ];

  // Header actions
  const headerActions: ActionDefinition[] = [
    {
      id: 'back',
      label: 'Retour',
      icon: <ArrowLeft size={16} />,
      variant: 'ghost',
      onClick: onBack
    },
    {
      id: 'edit',
      label: 'Modifier',
      icon: <Edit size={16} />,
      variant: 'secondary',
      onClick: onEdit
    }
  ];

  // Primary actions
  const primaryActions: ActionDefinition[] = [
    {
      id: 'log-time',
      label: 'Saisir du temps',
      icon: <Clock size={16} />,
      variant: 'primary'
    },
    {
      id: 'add-task',
      label: 'Ajouter tache',
      icon: <CheckSquare size={16} />,
      variant: 'secondary'
    },
    {
      id: 'print',
      label: 'Imprimer',
      icon: <Printer size={16} />,
      variant: 'ghost'
    }
  ];

  return (
    <BaseViewStandard<Project>
      title={project.name}
      subtitle={`${project.code} - ${project.client_name || 'Sans client'}`}
      status={{
        label: statusConfig.label,
        color: statusColorMap[statusConfig.color] || 'gray'
      }}
      data={project}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      primaryActions={primaryActions}
      error={error && typeof error === 'object' && 'message' in error ? error as Error : null}
      onRetry={() => refetch()}
    />
  );
};

// ============================================================================
// LIST VIEWS
// ============================================================================

const ProjectsListView: React.FC<{ onSelectProject: (id: string) => void }> = ({ onSelectProject }) => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const { data: projects = [], isLoading, error, refetch } = useProjects({
    status: filterStatus || undefined
  });

  const PROJECT_STATUS = [
    { value: 'DRAFT', label: 'Brouillon' },
    { value: 'ACTIVE', label: 'En cours' },
    { value: 'PAUSED', label: 'En pause' },
    { value: 'COMPLETED', label: 'Termine' },
    { value: 'CANCELLED', label: 'Annule' }
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
    CANCELLED: 'red'
  };

  const PRIORITY_COLORS: Record<string, string> = {
    LOW: 'gray',
    NORMAL: 'blue',
    HIGH: 'orange',
    URGENT: 'red'
  };

  const columns: TableColumn<Project>[] = [
    { id: 'code', header: 'Code', accessor: 'code', render: (v) => <code className="font-mono">{v as string}</code> },
    { id: 'name', header: 'Projet', accessor: 'name' },
    { id: 'client_name', header: 'Client', accessor: 'client_name', render: (v) => (v as string) || '-' },
    { id: 'manager_name', header: 'Responsable', accessor: 'manager_name', render: (v) => (v as string) || '-' },
    { id: 'priority', header: 'Priorite', accessor: 'priority', render: (v) => {
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
    { id: 'end_date', header: 'Echeance', accessor: 'end_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'budget', header: 'Budget', accessor: 'budget', render: (v, row: Project) => (v as number) ? formatCurrency(v as number, row.currency) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row: Project) => (
      <Button size="sm" variant="secondary" onClick={() => onSelectProject(row.id)}>Detail</Button>
    )}
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
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:modal', { detail: { type: 'project-create' } })); }}>Nouveau projet</Button>
        </div>
      </div>
      <DataTable columns={columns} data={projects} isLoading={isLoading} keyField="id" filterable error={error && typeof error === 'object' && 'message' in error ? error as Error : null} onRetry={() => refetch()} />
    </Card>
  );
};

const TasksView: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterProject, setFilterProject] = useState<string>('');
  const { data: tasks = [], isLoading, error, refetch } = useTasks({
    status: filterStatus || undefined,
    project_id: filterProject || undefined
  });
  const { data: projects = [] } = useProjects();
  const updateStatus = useUpdateTaskStatus();

  const TASK_STATUS = [
    { value: 'TODO', label: 'A faire' },
    { value: 'IN_PROGRESS', label: 'En cours' },
    { value: 'REVIEW', label: 'En revue' },
    { value: 'DONE', label: 'Termine' }
  ];

  const PRIORITIES = [
    { value: 'LOW', label: 'Basse' },
    { value: 'NORMAL', label: 'Normale' },
    { value: 'HIGH', label: 'Haute' },
    { value: 'URGENT', label: 'Urgente' }
  ];

  const STATUS_COLORS: Record<string, string> = {
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

  const columns: TableColumn<Task>[] = [
    { id: 'title', header: 'Tache', accessor: 'title' },
    { id: 'project_name', header: 'Projet', accessor: 'project_name', render: (v) => (v as string) || '-' },
    { id: 'assignee_name', header: 'Assigne a', accessor: 'assignee_name', render: (v) => (v as string) || 'Non assigne' },
    { id: 'priority', header: 'Priorite', accessor: 'priority', render: (v) => {
      const val = v as string;
      const info = PRIORITIES.find(p => p.value === val);
      return <Badge color={PRIORITY_COLORS[val] || 'gray'}>{info?.label || val}</Badge>;
    }},
    { id: 'status', header: 'Statut', accessor: 'status', render: (v) => {
      const val = v as string;
      const info = TASK_STATUS.find(s => s.value === val);
      return <Badge color={STATUS_COLORS[val] || 'gray'}>{info?.label || val}</Badge>;
    }},
    { id: 'due_date', header: 'Echeance', accessor: 'due_date', render: (v) => (v as string) ? formatDate(v as string) : '-' },
    { id: 'estimated_hours', header: 'Est.', accessor: 'estimated_hours', render: (v) => (v as number) ? formatHours(v as number) : '-' },
    { id: 'logged_hours', header: 'Reel', accessor: 'logged_hours', render: (v) => (v as number) ? formatHours(v as number) : '-' },
    { id: 'actions', header: 'Actions', accessor: 'id', render: (_, row: Task) => (
      <div className="flex gap-1">
        {row.status === 'TODO' && (
          <Button size="sm" variant="primary" onClick={() => updateStatus.mutate({ id: row.id, status: 'IN_PROGRESS' })}>Demarrer</Button>
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
        <h3 className="text-lg font-semibold">Taches</h3>
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
          <Button onClick={() => { window.dispatchEvent(new CustomEvent('azals:modal', { detail: { type: 'task-create' } })); }}>Nouvelle tache</Button>
        </div>
      </div>
      <DataTable columns={columns} data={tasks} isLoading={isLoading} keyField="id" filterable error={error && typeof error === 'object' && 'message' in error ? error as Error : null} onRetry={() => refetch()} />
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
  const { data: timeEntries = [], isLoading, error: timeError, refetch: timeRefetch } = useTimeEntries({
    project_id: filterProject || undefined
  });
  const { data: projects = [] } = useProjects();
  const logTime = useLogTime();

  const columns: TableColumn<TimeEntry>[] = [
    { id: 'date', header: 'Date', accessor: 'date', render: (v) => formatDate(v as string) },
    { id: 'project_name', header: 'Projet', accessor: 'project_name' },
    { id: 'task_title', header: 'Tache', accessor: 'task_title', render: (v) => (v as string) || '-' },
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
        <DataTable columns={columns} data={timeEntries} isLoading={isLoading} keyField="id" filterable error={timeError instanceof Error ? timeError : null} onRetry={() => timeRefetch()} />
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
                    { value: '', label: 'Selectionner...' },
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
                  placeholder="Travail effectue..."
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

type View = 'dashboard' | 'projects' | 'tasks' | 'timesheet' | 'detail';

const ProjectsModule: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('dashboard');
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const { data: stats } = useProjectStats();

  const tabs = [
    { id: 'dashboard', label: 'Vue d\'ensemble' },
    { id: 'projects', label: 'Projets' },
    { id: 'tasks', label: 'Taches' },
    { id: 'timesheet', label: 'Temps' }
  ];

  const handleSelectProject = (id: string) => {
    setSelectedProjectId(id);
    setCurrentView('detail');
  };

  const handleBackFromDetail = () => {
    setSelectedProjectId(null);
    setCurrentView('projects');
  };

  // Render detail view
  if (currentView === 'detail' && selectedProjectId) {
    return (
      <ProjectDetailView
        projectId={selectedProjectId}
        onBack={handleBackFromDetail}
      />
    );
  }

  const renderContent = () => {
    switch (currentView) {
      case 'projects':
        return <ProjectsListView onSelectProject={handleSelectProject} />;
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
                title="Taches totales"
                value={String(stats?.total_tasks || 0)}
                icon={<ClipboardList className="h-5 w-5" />}
                variant="default"
                onClick={() => setCurrentView('tasks')}
              />
              <StatCard
                title="Taches terminees"
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
                title="Budget utilise"
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
