/**
 * AZALSCORE Module - INTERVENTIONS - Dashboard
 * Vue d'ensemble avec statistiques
 */

import React from 'react';
import {
  ClipboardList, Calendar, Wrench, CheckCircle, BarChart3, Clock, MapPin,
  FileEdit, Lock
} from 'lucide-react';
import { LoadingState, ErrorState } from '@ui/components/StateViews';
import { StatCard } from '@ui/dashboards';
import { Grid } from '@ui/layout';
import { formatDuration } from '@/utils/formatters';
import { useInterventionStats } from '../api';

export interface InterventionsDashboardProps {
  onNavigateToList: () => void;
  onNavigateToPlanning: () => void;
}

export const InterventionsDashboard: React.FC<InterventionsDashboardProps> = ({
  onNavigateToList,
  onNavigateToPlanning
}) => {
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useInterventionStats();

  if (statsLoading) {
    return <LoadingState onRetry={() => refetchStats()} message="Chargement des statistiques..." />;
  }

  if (statsError) {
    return (
      <ErrorState
        message="Impossible de charger les statistiques"
        onRetry={() => refetchStats()}
      />
    );
  }

  return (
    <div className="space-y-4">
      <Grid cols={3}>
        <StatCard
          title="Brouillons"
          value={String(stats?.brouillons || 0)}
          icon={<FileEdit size={20} />}
          variant="default"
          onClick={onNavigateToList}
        />
        <StatCard
          title="À planifier"
          value={String(stats?.a_planifier || 0)}
          icon={<ClipboardList size={20} />}
          variant="default"
          onClick={onNavigateToList}
        />
        <StatCard
          title="Planifiées"
          value={String(stats?.planifiees || 0)}
          icon={<Calendar size={20} />}
          variant="default"
          onClick={onNavigateToPlanning}
        />
      </Grid>

      <Grid cols={3}>
        <StatCard
          title="En cours"
          value={String(stats?.en_cours || 0)}
          icon={<Wrench size={20} />}
          variant="warning"
        />
        <StatCard
          title="Bloquées"
          value={String(stats?.bloquees || 0)}
          icon={<Lock size={20} />}
          variant="danger"
        />
        <StatCard
          title="Terminées (semaine)"
          value={String(stats?.terminees_semaine || 0)}
          icon={<CheckCircle size={20} />}
          variant="success"
        />
      </Grid>

      <Grid cols={3}>
        <StatCard
          title="Terminées (mois)"
          value={String(stats?.terminees_mois || 0)}
          icon={<BarChart3 size={20} />}
          variant="default"
        />
        <StatCard
          title="Durée moyenne"
          value={stats?.duree_moyenne_minutes ? formatDuration(stats.duree_moyenne_minutes) : '-'}
          icon={<Clock size={20} />}
          variant="default"
        />
        <StatCard
          title="Aujourd'hui"
          value={String(stats?.interventions_jour || 0)}
          icon={<MapPin size={20} />}
          variant="success"
        />
      </Grid>
    </div>
  );
};

export default InterventionsDashboard;
