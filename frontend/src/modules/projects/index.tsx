/**
 * AZALSCORE Module - Projets
 * Gestion de projets, Tâches, Feuilles de temps
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Plus, FolderKanban, CheckSquare, Clock } from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button } from '@ui/actions';
import { KPICard, ProgressBar } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

interface Project {
  id: string;
  name: string;
  client_id?: string;
  client_name?: string;
  status: 'draft' | 'active' | 'paused' | 'completed' | 'cancelled';
  start_date?: string;
  end_date?: string;
  budget?: number;
  progress: number;
  currency: string;
}

interface ProjectSummary {
  active_projects: number;
  total_tasks: number;
  tasks_completed: number;
  hours_this_week: number;
}

const useProjectSummary = () => {
  return useQuery({
    queryKey: ['projects', 'summary'],
    queryFn: async () => {
      const response = await api.get<ProjectSummary>('/v1/projects/summary');
      return response.data;
    },
  });
};

const useProjects = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['projects', 'list', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Project>>(
        `/v1/projects?page=${page}&page_size=${pageSize}`
      );
      return response.data;
    },
  });
};

const STATUS_LABELS: Record<string, string> = {
  draft: 'Brouillon',
  active: 'En cours',
  paused: 'En pause',
  completed: 'Terminé',
  cancelled: 'Annulé',
};

const STATUS_COLORS: Record<string, string> = {
  draft: 'gray',
  active: 'blue',
  paused: 'orange',
  completed: 'green',
  cancelled: 'red',
};

export const ProjectsDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = useProjectSummary();

  const kpis: DashboardKPI[] = summary
    ? [
        { id: 'active', label: 'Projets actifs', value: summary.active_projects },
        { id: 'tasks', label: 'Tâches totales', value: summary.total_tasks },
        { id: 'completed', label: 'Tâches terminées', value: summary.tasks_completed },
        { id: 'hours', label: 'Heures cette semaine', value: `${summary.hours_this_week}h` },
      ]
    : [];

  return (
    <PageWrapper title="Projets" subtitle="Gestion de projets et suivi">
      {isLoading ? (
        <div className="azals-loading"><div className="azals-spinner" /></div>
      ) : (
        <>
          <section className="azals-section">
            <Grid cols={4} gap="md">
              {kpis.map((kpi) => <KPICard key={kpi.id} kpi={kpi} />)}
            </Grid>
          </section>

          <section className="azals-section">
            <Grid cols={3} gap="md">
              <Card
                title="Projets"
                actions={<Button variant="ghost" size="sm" onClick={() => navigate('/projects/list')}>Voir tout</Button>}
              >
                <FolderKanban size={32} className="azals-text--primary" />
                <p>Liste des projets</p>
              </Card>

              <Card
                title="Tâches"
                actions={<Button variant="ghost" size="sm" onClick={() => navigate('/projects/tasks')}>Voir tout</Button>}
              >
                <CheckSquare size={32} className="azals-text--primary" />
                <p>Gestion des tâches</p>
              </Card>

              <Card
                title="Feuilles de temps"
                actions={<Button variant="ghost" size="sm" onClick={() => navigate('/projects/timesheet')}>Saisir</Button>}
              >
                <Clock size={32} className="azals-text--primary" />
                <p>Saisie du temps passé</p>
              </Card>
            </Grid>
          </section>
        </>
      )}
    </PageWrapper>
  );
};

export const ProjectsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const { data, isLoading, refetch } = useProjects(page, pageSize);

  const columns: TableColumn<Project>[] = [
    { id: 'name', header: 'Nom', accessor: 'name', sortable: true },
    { id: 'client_name', header: 'Client', accessor: 'client_name' },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => (
        <span className={`azals-badge azals-badge--${STATUS_COLORS[value as string]}`}>
          {STATUS_LABELS[value as string]}
        </span>
      ),
    },
    {
      id: 'progress',
      header: 'Avancement',
      accessor: 'progress',
      render: (value) => <ProgressBar value={value as number} max={100} showValue={false} />,
    },
    {
      id: 'end_date',
      header: 'Échéance',
      accessor: 'end_date',
      render: (value) => value ? new Date(value as string).toLocaleDateString('fr-FR') : '-',
    },
  ];

  return (
    <PageWrapper
      title="Liste des Projets"
      actions={
        <CapabilityGuard capability="projects.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/projects/new')}>
            Nouveau projet
          </Button>
        </CapabilityGuard>
      }
    >
      <Card noPadding>
        <DataTable
          columns={columns}
          data={data?.items || []}
          keyField="id"
          isLoading={isLoading}
          pagination={{ page, pageSize, total: data?.total || 0, onPageChange: setPage, onPageSizeChange: setPageSize }}
          onRefresh={refetch}
        />
      </Card>
    </PageWrapper>
  );
};

export const ProjectsRoutes: React.FC = () => (
  <Routes>
    <Route index element={<ProjectsDashboard />} />
    <Route path="list" element={<ProjectsListPage />} />
  </Routes>
);

export default ProjectsRoutes;
