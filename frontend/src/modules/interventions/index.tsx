/**
 * AZALSCORE Module - Interventions
 * Tickets, Planning, Rapports d'intervention
 */

import React, { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Plus, Ticket, Calendar, FileText } from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { DataTable } from '@ui/tables';
import { Button } from '@ui/actions';
import { KPICard, SeverityBadge } from '@ui/dashboards';
import type { PaginatedResponse, TableColumn, DashboardKPI } from '@/types';

interface Ticket {
  id: string;
  number: string;
  title: string;
  client_id?: string;
  client_name?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'new' | 'assigned' | 'in_progress' | 'resolved' | 'closed';
  assigned_to?: string;
  created_at: string;
  due_date?: string;
}

interface InterventionSummary {
  open_tickets: number;
  critical_tickets: number;
  scheduled_today: number;
  completed_this_week: number;
}

const useSummary = () => {
  return useQuery({
    queryKey: ['interventions', 'summary'],
    queryFn: async () => {
      const response = await api.get<InterventionSummary>('/v1/interventions/summary');
      return response.data;
    },
  });
};

const useTickets = (page = 1, pageSize = 25) => {
  return useQuery({
    queryKey: ['interventions', 'tickets', page, pageSize],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<Ticket>>(
        `/v1/interventions/tickets?page=${page}&page_size=${pageSize}`
      );
      return response.data;
    },
  });
};

const PRIORITY_MAP = { low: 'GREEN', medium: 'ORANGE', high: 'ORANGE', critical: 'RED' } as const;
const STATUS_LABELS: Record<string, string> = {
  new: 'Nouveau', assigned: 'Assigné', in_progress: 'En cours', resolved: 'Résolu', closed: 'Fermé',
};

export const InterventionsDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = useSummary();

  const kpis: DashboardKPI[] = summary
    ? [
        { id: 'open', label: 'Tickets ouverts', value: summary.open_tickets },
        { id: 'critical', label: 'Critiques', value: summary.critical_tickets, severity: summary.critical_tickets > 0 ? 'RED' : 'GREEN' },
        { id: 'today', label: 'Planifiées aujourd\'hui', value: summary.scheduled_today },
        { id: 'completed', label: 'Terminées (semaine)', value: summary.completed_this_week },
      ]
    : [];

  return (
    <PageWrapper title="Interventions" subtitle="Support et maintenance">
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
              <Card title="Tickets" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/interventions/tickets')}>Voir tout</Button>}>
                <Ticket size={32} className="azals-text--primary" />
                <p>Gestion des tickets</p>
              </Card>
              <Card title="Planning" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/interventions/planning')}>Voir</Button>}>
                <Calendar size={32} className="azals-text--primary" />
                <p>Planning des interventions</p>
              </Card>
              <Card title="Rapports" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/interventions/reports')}>Voir</Button>}>
                <FileText size={32} className="azals-text--primary" />
                <p>Rapports d'intervention</p>
              </Card>
            </Grid>
          </section>
        </>
      )}
    </PageWrapper>
  );
};

export const TicketsPage: React.FC = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const { data, isLoading, refetch } = useTickets(page, pageSize);

  const columns: TableColumn<Ticket>[] = [
    { id: 'number', header: 'N°', accessor: 'number' },
    { id: 'title', header: 'Titre', accessor: 'title' },
    { id: 'client_name', header: 'Client', accessor: 'client_name' },
    {
      id: 'priority',
      header: 'Priorité',
      accessor: 'priority',
      render: (value) => <SeverityBadge severity={PRIORITY_MAP[value as keyof typeof PRIORITY_MAP]} size="sm" />,
    },
    {
      id: 'status',
      header: 'Statut',
      accessor: 'status',
      render: (value) => STATUS_LABELS[value as string],
    },
    {
      id: 'created_at',
      header: 'Créé le',
      accessor: 'created_at',
      render: (value) => new Date(value as string).toLocaleDateString('fr-FR'),
    },
  ];

  return (
    <PageWrapper
      title="Tickets"
      actions={
        <CapabilityGuard capability="interventions.tickets.create">
          <Button leftIcon={<Plus size={16} />} onClick={() => navigate('/interventions/tickets/new')}>
            Nouveau ticket
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

export const InterventionsRoutes: React.FC = () => (
  <Routes>
    <Route index element={<InterventionsDashboard />} />
    <Route path="tickets" element={<TicketsPage />} />
  </Routes>
);

export default InterventionsRoutes;
