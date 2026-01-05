/**
 * AZALSCORE Module - Cockpit Dirigeant
 * Tableau de bord exécutif avec KPIs RED/ORANGE/GREEN
 * Données fournies par API - AUCUNE logique métier
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  Users,
  Euro,
  Activity,
} from 'lucide-react';
import { api } from '@core/api-client';
import { CapabilityGuard } from '@core/capabilities';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { KPIGrid, AlertList, SeverityBadge, MetricComparison, ProgressBar } from '@ui/dashboards';
import { Button, ButtonGroup } from '@ui/actions';
import { DataTable } from '@ui/tables';
import type { DashboardKPI, Alert, PaginatedResponse } from '@/types';

// ============================================================
// TYPES
// ============================================================

interface CockpitData {
  kpis: DashboardKPI[];
  alerts: Alert[];
  treasury_summary: {
    balance: number;
    forecast_30d: number;
    pending_payments: number;
  };
  sales_summary: {
    month_revenue: number;
    prev_month_revenue: number;
    pending_invoices: number;
    overdue_invoices: number;
  };
  activity_summary: {
    open_quotes: number;
    pending_orders: number;
    scheduled_interventions: number;
  };
}

interface PendingDecision {
  id: string;
  type: string;
  title: string;
  severity: 'RED' | 'ORANGE' | 'GREEN';
  module: string;
  created_at: string;
  action_url: string;
}

// ============================================================
// API HOOKS
// ============================================================

const useCockpitData = () => {
  return useQuery({
    queryKey: ['cockpit', 'data'],
    queryFn: async () => {
      const response = await api.get<CockpitData>('/v1/cockpit/dashboard');
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });
};

const usePendingDecisions = () => {
  return useQuery({
    queryKey: ['cockpit', 'decisions'],
    queryFn: async () => {
      const response = await api.get<PaginatedResponse<PendingDecision>>('/v1/cockpit/decisions');
      return response.data;
    },
  });
};

const useAcknowledgeAlert = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (alertId: string) => {
      await api.post(`/v1/alerts/${alertId}/acknowledge`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cockpit'] });
    },
  });
};

// ============================================================
// COCKPIT WIDGETS
// ============================================================

const TreasurySummaryWidget: React.FC<{ data: CockpitData['treasury_summary'] }> = ({ data }) => {
  const navigate = useNavigate();

  return (
    <Card title="Trésorerie" actions={
      <Button variant="ghost" size="sm" onClick={() => navigate('/treasury')}>
        Détails
      </Button>
    }>
      <div className="azals-cockpit__treasury">
        <MetricComparison
          label="Solde actuel"
          current={data.balance}
          previous={data.balance - data.forecast_30d}
          format="currency"
        />
        <div className="azals-cockpit__treasury-row">
          <div className="azals-cockpit__metric">
            <span className="azals-cockpit__metric-label">Prévision 30j</span>
            <span className="azals-cockpit__metric-value">
              {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(data.forecast_30d)}
            </span>
          </div>
          <div className="azals-cockpit__metric">
            <span className="azals-cockpit__metric-label">En attente</span>
            <span className="azals-cockpit__metric-value azals-cockpit__metric-value--warning">
              {new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(data.pending_payments)}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};

const SalesSummaryWidget: React.FC<{ data: CockpitData['sales_summary'] }> = ({ data }) => {
  const navigate = useNavigate();

  return (
    <Card title="Ventes" actions={
      <Button variant="ghost" size="sm" onClick={() => navigate('/invoicing')}>
        Détails
      </Button>
    }>
      <div className="azals-cockpit__sales">
        <MetricComparison
          label="CA du mois"
          current={data.month_revenue}
          previous={data.prev_month_revenue}
          format="currency"
        />
        <div className="azals-cockpit__sales-row">
          <div className="azals-cockpit__metric">
            <span className="azals-cockpit__metric-label">Factures en attente</span>
            <span className="azals-cockpit__metric-value">{data.pending_invoices}</span>
          </div>
          <div className="azals-cockpit__metric">
            <span className="azals-cockpit__metric-label">Factures en retard</span>
            <span className={`azals-cockpit__metric-value ${data.overdue_invoices > 0 ? 'azals-cockpit__metric-value--danger' : ''}`}>
              {data.overdue_invoices}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};

const ActivitySummaryWidget: React.FC<{ data: CockpitData['activity_summary'] }> = ({ data }) => {
  return (
    <Card title="Activité">
      <div className="azals-cockpit__activity">
        <div className="azals-cockpit__activity-item">
          <FileText size={20} />
          <span className="azals-cockpit__activity-label">Devis ouverts</span>
          <span className="azals-cockpit__activity-value">{data.open_quotes}</span>
        </div>
        <div className="azals-cockpit__activity-item">
          <Clock size={20} />
          <span className="azals-cockpit__activity-label">Commandes en cours</span>
          <span className="azals-cockpit__activity-value">{data.pending_orders}</span>
        </div>
        <div className="azals-cockpit__activity-item">
          <Activity size={20} />
          <span className="azals-cockpit__activity-label">Interventions planifiées</span>
          <span className="azals-cockpit__activity-value">{data.scheduled_interventions}</span>
        </div>
      </div>
    </Card>
  );
};

const PendingDecisionsWidget: React.FC = () => {
  const navigate = useNavigate();
  const { data, isLoading } = usePendingDecisions();

  const columns = [
    {
      id: 'severity',
      header: '',
      accessor: 'severity' as const,
      width: '60px',
      render: (value: unknown) => <SeverityBadge severity={value as 'RED' | 'ORANGE' | 'GREEN'} size="sm" />,
    },
    {
      id: 'title',
      header: 'Décision',
      accessor: 'title' as const,
    },
    {
      id: 'module',
      header: 'Module',
      accessor: 'module' as const,
    },
    {
      id: 'created_at',
      header: 'Date',
      accessor: 'created_at' as const,
      render: (value: unknown) => new Date(value as string).toLocaleDateString('fr-FR'),
    },
  ];

  const actions = [
    {
      id: 'view',
      label: 'Traiter',
      onClick: (row: PendingDecision) => navigate(row.action_url),
    },
  ];

  return (
    <Card title="Décisions en attente" noPadding>
      <DataTable
        columns={columns}
        data={data?.items || []}
        keyField="id"
        actions={actions}
        isLoading={isLoading}
        emptyMessage="Aucune décision en attente"
      />
    </Card>
  );
};

// ============================================================
// MAIN COCKPIT PAGE
// ============================================================

export const CockpitPage: React.FC = () => {
  const { data, isLoading, error, refetch } = useCockpitData();
  const acknowledgeAlert = useAcknowledgeAlert();
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <PageWrapper title="Cockpit Dirigeant">
        <div className="azals-loading">
          <div className="azals-spinner" />
          <p>Chargement du tableau de bord...</p>
        </div>
      </PageWrapper>
    );
  }

  if (error || !data) {
    return (
      <PageWrapper title="Cockpit Dirigeant">
        <Card>
          <div className="azals-error">
            <AlertTriangle size={48} />
            <p>Impossible de charger le tableau de bord</p>
            <Button onClick={() => refetch()}>Réessayer</Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title="Cockpit Dirigeant"
      subtitle="Vue d'ensemble de votre activité"
      actions={
        <Button variant="ghost" onClick={() => refetch()}>
          Actualiser
        </Button>
      }
    >
      {/* KPIs */}
      <section className="azals-cockpit__section">
        <KPIGrid kpis={data.kpis} columns={4} />
      </section>

      {/* Alertes critiques */}
      {data.alerts.filter((a) => a.severity === 'RED').length > 0 && (
        <section className="azals-cockpit__section azals-cockpit__section--alerts">
          <Card title="Alertes Critiques" className="azals-card--danger">
            <AlertList
              alerts={data.alerts.filter((a) => a.severity === 'RED')}
              onAcknowledge={(alert) => acknowledgeAlert.mutate(alert.id)}
              onAction={(alert) => alert.action_url && navigate(alert.action_url)}
            />
          </Card>
        </section>
      )}

      {/* Widgets principaux */}
      <section className="azals-cockpit__section">
        <Grid cols={3} gap="md">
          <TreasurySummaryWidget data={data.treasury_summary} />
          <SalesSummaryWidget data={data.sales_summary} />
          <ActivitySummaryWidget data={data.activity_summary} />
        </Grid>
      </section>

      {/* Décisions en attente */}
      <CapabilityGuard capability="cockpit.decisions.view">
        <section className="azals-cockpit__section">
          <PendingDecisionsWidget />
        </section>
      </CapabilityGuard>

      {/* Autres alertes */}
      {data.alerts.filter((a) => a.severity !== 'RED').length > 0 && (
        <section className="azals-cockpit__section">
          <Card title="Alertes et Notifications">
            <AlertList
              alerts={data.alerts.filter((a) => a.severity !== 'RED')}
              maxItems={5}
              onAcknowledge={(alert) => acknowledgeAlert.mutate(alert.id)}
              onViewAll={() => navigate('/alerts')}
            />
          </Card>
        </section>
      )}
    </PageWrapper>
  );
};

export default CockpitPage;
