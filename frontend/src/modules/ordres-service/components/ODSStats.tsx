/**
 * AZALSCORE Module - Ordres de Service - Stats
 * KPIs du tableau de bord
 */

import React from 'react';
import { Calendar, Clock, Play, CheckCircle2 } from 'lucide-react';
import { KPICard } from '@ui/dashboards';
import { Grid } from '@ui/layout';
import type { DashboardKPI } from '@/types';
import { useInterventionStats } from '../hooks';

export const ODSStats: React.FC = () => {
  const { data: stats } = useInterventionStats();

  const kpis: DashboardKPI[] = stats ? [
    { id: 'planifier', label: 'A planifier', value: stats.a_planifier, icon: <Calendar size={20} />, variant: stats.a_planifier > 0 ? 'warning' : undefined },
    { id: 'planifiees', label: 'Planifiees', value: stats.planifiees, icon: <Clock size={20} /> },
    { id: 'encours', label: 'En cours', value: stats.en_cours, icon: <Play size={20} /> },
    { id: 'terminees', label: 'Terminees', value: stats.terminees, icon: <CheckCircle2 size={20} /> },
  ] : [];

  return (
    <Grid cols={4} gap="md">
      {kpis.map(kpi => <KPICard key={kpi.id} kpi={kpi} />)}
    </Grid>
  );
};

export default ODSStats;
