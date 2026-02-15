/**
 * AZALSCORE Module - Projects - Project Timesheet Tab
 * Onglet feuilles de temps du projet
 */

import React from 'react';
import {
  Clock, User, Calendar, Euro, TrendingUp,
  CheckCircle, XCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Project, TimeEntry } from '../types';
import { formatDate, formatHours, formatCurrency } from '@/utils/formatters';
import {
  getTotalLoggedHours, getBillableHours, getBillableAmount,
  getTotalEstimatedHours
} from '../types';

/**
 * ProjectTimesheetTab - Feuilles de temps du projet
 */
export const ProjectTimesheetTab: React.FC<TabContentProps<Project>> = ({ data: project }) => {
  const timeEntries = project.time_entries || [];
  const totalLogged = getTotalLoggedHours(project);
  const billableHours = getBillableHours(project);
  const billableAmount = getBillableAmount(project);
  const estimatedHours = getTotalEstimatedHours(project);
  const nonBillableHours = totalLogged - billableHours;

  // Grouper par date
  const entriesByDate = timeEntries.reduce((acc, entry) => {
    const date = entry.date;
    if (!acc[date]) acc[date] = [];
    acc[date].push(entry);
    return acc;
  }, {} as Record<string, TimeEntry[]>);

  const sortedDates = Object.keys(entriesByDate).sort((a, b) =>
    new Date(b).getTime() - new Date(a).getTime()
  );

  return (
    <div className="azals-std-tab-content">
      {/* Resume temps */}
      <Grid cols={4} gap="md" className="mb-4">
        <TimeStatCard
          label="Heures totales"
          value={formatHours(totalLogged)}
          subValue={estimatedHours > 0 ? `/ ${formatHours(estimatedHours)} estimees` : undefined}
          icon={<Clock size={20} />}
          color="blue"
        />
        <TimeStatCard
          label="Heures facturables"
          value={formatHours(billableHours)}
          subValue={`${totalLogged > 0 ? Math.round((billableHours / totalLogged) * 100) : 0}% du total`}
          icon={<Euro size={20} />}
          color="green"
        />
        <TimeStatCard
          label="Non facturables"
          value={formatHours(nonBillableHours)}
          icon={<XCircle size={20} />}
          color="gray"
        />
        <TimeStatCard
          label="Montant facturable"
          value={formatCurrency(billableAmount, project.currency)}
          icon={<TrendingUp size={20} />}
          color="purple"
        />
      </Grid>

      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Clock size={16} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'logTime', projectId: project.id } })); }}>
          Saisir du temps
        </Button>
      </div>

      {/* Liste des entrees par date */}
      <Card title="Saisies de temps" icon={<Clock size={18} />}>
        {sortedDates.length > 0 ? (
          <div className="azals-timesheet">
            {sortedDates.map((date) => (
              <div key={date} className="azals-timesheet__day">
                <div className="azals-timesheet__date">
                  <Calendar size={14} />
                  <span>{formatDate(date)}</span>
                  <span className="text-muted">
                    ({formatHours(entriesByDate[date].reduce((sum, e) => sum + e.hours, 0))})
                  </span>
                </div>
                <div className="azals-timesheet__entries">
                  {entriesByDate[date].map((entry) => (
                    <TimeEntryItem key={entry.id} entry={entry} currency={project.currency} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Clock size={32} className="text-muted" />
            <p className="text-muted">Aucune saisie de temps</p>
            <Button size="sm" variant="ghost" leftIcon={<Clock size={14} />} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'logTime', projectId: project.id } })); }}>
              Saisir du temps
            </Button>
          </div>
        )}
      </Card>

      {/* Repartition par utilisateur (ERP only) */}
      <Card
        title="Repartition par utilisateur"
        icon={<User size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <UserTimeBreakdown entries={timeEntries} />
      </Card>

      {/* Repartition par tache (ERP only) */}
      <Card
        title="Repartition par tache"
        icon={<CheckCircle size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <TaskTimeBreakdown entries={timeEntries} />
      </Card>
    </div>
  );
};

/**
 * Carte statistique temps
 */
interface TimeStatCardProps {
  label: string;
  value: string;
  subValue?: string;
  icon: React.ReactNode;
  color: string;
}

const TimeStatCard: React.FC<TimeStatCardProps> = ({ label, value, subValue, icon, color }) => {
  return (
    <div className={`azals-stat-card azals-stat-card--${color}`}>
      <div className="azals-stat-card__icon">{icon}</div>
      <div className="azals-stat-card__content">
        <div className="azals-stat-card__value">{value}</div>
        <div className="azals-stat-card__label">{label}</div>
        {subValue && <div className="azals-stat-card__sub text-xs text-muted">{subValue}</div>}
      </div>
    </div>
  );
};

/**
 * Composant item d'entree de temps
 */
interface TimeEntryItemProps {
  entry: TimeEntry;
  currency: string;
}

const TimeEntryItem: React.FC<TimeEntryItemProps> = ({ entry, currency }) => {
  return (
    <div className="azals-time-entry">
      <div className="azals-time-entry__user">
        <User size={14} />
        <span>{entry.user_name}</span>
      </div>
      <div className="azals-time-entry__task">
        {entry.task_title || 'Sans tache'}
      </div>
      <div className="azals-time-entry__description text-sm text-muted">
        {entry.description || '-'}
      </div>
      <div className="azals-time-entry__hours font-medium">
        {formatHours(entry.hours)}
      </div>
      <div className="azals-time-entry__billable">
        {entry.is_billable ? (
          <span className="azals-badge azals-badge--green azals-badge--sm">
            <CheckCircle size={10} className="mr-1" />
            Facturable
          </span>
        ) : (
          <span className="azals-badge azals-badge--gray azals-badge--sm">
            Non fact.
          </span>
        )}
      </div>
      {entry.hourly_rate && entry.is_billable && (
        <div className="azals-time-entry__amount text-sm">
          {formatCurrency(entry.hours * entry.hourly_rate, currency)}
        </div>
      )}
    </div>
  );
};

/**
 * Repartition par utilisateur
 */
const UserTimeBreakdown: React.FC<{ entries: TimeEntry[] }> = ({ entries }) => {
  const byUser = entries.reduce((acc, entry) => {
    const key = entry.user_name;
    if (!acc[key]) acc[key] = { total: 0, billable: 0 };
    acc[key].total += entry.hours;
    if (entry.is_billable) acc[key].billable += entry.hours;
    return acc;
  }, {} as Record<string, { total: number; billable: number }>);

  const users = Object.entries(byUser).sort((a, b) => b[1].total - a[1].total);
  const maxHours = Math.max(...users.map(([_, data]) => data.total));

  if (users.length === 0) {
    return <p className="text-muted">Aucune donnee</p>;
  }

  return (
    <div className="azals-breakdown">
      {users.map(([name, data]) => (
        <div key={name} className="azals-breakdown__item">
          <div className="azals-breakdown__label">
            <User size={14} />
            <span>{name}</span>
          </div>
          <div className="azals-breakdown__bar">
            <div
              className="azals-breakdown__bar-fill azals-breakdown__bar-fill--blue"
              style={{ width: `${(data.total / maxHours) * 100}%` }}
            />
          </div>
          <div className="azals-breakdown__value">
            {formatHours(data.total)}
            <span className="text-muted text-xs ml-1">
              ({formatHours(data.billable)} fact.)
            </span>
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Repartition par tache
 */
const TaskTimeBreakdown: React.FC<{ entries: TimeEntry[] }> = ({ entries }) => {
  const byTask = entries.reduce((acc, entry) => {
    const key = entry.task_title || 'Sans tache';
    if (!acc[key]) acc[key] = 0;
    acc[key] += entry.hours;
    return acc;
  }, {} as Record<string, number>);

  const tasks = Object.entries(byTask).sort((a, b) => b[1] - a[1]);
  const maxHours = Math.max(...tasks.map(([_, hours]) => hours));

  if (tasks.length === 0) {
    return <p className="text-muted">Aucune donnee</p>;
  }

  return (
    <div className="azals-breakdown">
      {tasks.map(([name, hours]) => (
        <div key={name} className="azals-breakdown__item">
          <div className="azals-breakdown__label">
            <CheckCircle size={14} />
            <span>{name}</span>
          </div>
          <div className="azals-breakdown__bar">
            <div
              className="azals-breakdown__bar-fill azals-breakdown__bar-fill--purple"
              style={{ width: `${(hours / maxHours) * 100}%` }}
            />
          </div>
          <div className="azals-breakdown__value">
            {formatHours(hours)}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ProjectTimesheetTab;
