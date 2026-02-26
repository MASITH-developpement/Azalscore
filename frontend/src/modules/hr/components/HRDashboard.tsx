/**
 * AZALSCORE Module - HR - HRDashboard
 * Vue tableau de bord RH
 */

import React from 'react';
import { Users, Calendar, Clock, AlertTriangle, Plus, Minus, Building, BarChart3 } from 'lucide-react';
import { StatCard } from '@ui/dashboards';
import { Grid } from '@ui/layout';
import type { HRDashboard as HRDashboardData, Department } from '../types';

type View = 'dashboard' | 'employees' | 'departments' | 'positions' | 'leave' | 'timesheets' | 'employee-detail';

interface HRDashboardProps {
  dashboard: HRDashboardData | null;
  departments: Department[];
  onNavigate: (view: View) => void;
}

const HRDashboard: React.FC<HRDashboardProps> = ({ dashboard, departments, onNavigate }) => {
  return (
    <div className="space-y-4">
      <Grid cols={4}>
        <StatCard
          title="Employes actifs"
          value={String(dashboard?.active_employees || 0)}
          icon={<Users />}
          variant="default"
          onClick={() => onNavigate('employees')}
        />
        <StatCard
          title="En conge"
          value={String(dashboard?.on_leave_employees || dashboard?.employees_on_leave_today || 0)}
          icon={<Calendar />}
          variant="success"
          onClick={() => onNavigate('leave')}
        />
        <StatCard
          title="Demandes en attente"
          value={String(dashboard?.pending_leave_requests || 0)}
          icon={<Clock />}
          variant="warning"
          onClick={() => onNavigate('leave')}
        />
        <StatCard
          title="Contrats expirant"
          value={String(dashboard?.contracts_ending_soon || 0)}
          icon={<AlertTriangle />}
          variant="danger"
          onClick={() => onNavigate('employees')}
        />
      </Grid>
      <Grid cols={4}>
        <StatCard
          title="Embauches (mois)"
          value={String(dashboard?.new_hires_this_month || 0)}
          icon={<Plus />}
          variant="success"
        />
        <StatCard
          title="Departs (mois)"
          value={String(dashboard?.departures_this_month || 0)}
          icon={<Minus />}
          variant="danger"
        />
        <StatCard
          title="Departements"
          value={String(departments.length)}
          icon={<Building />}
          variant="default"
          onClick={() => onNavigate('departments')}
        />
        <StatCard
          title="Total employes"
          value={String(dashboard?.total_employees || 0)}
          icon={<BarChart3 />}
          variant="default"
        />
      </Grid>
    </div>
  );
};

export default HRDashboard;
