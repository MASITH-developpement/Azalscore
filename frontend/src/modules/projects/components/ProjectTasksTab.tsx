/**
 * AZALSCORE Module - Projects - Project Tasks Tab
 * Onglet taches du projet
 */

import React, { useState } from 'react';
import {
  CheckSquare, User, Calendar, Clock, AlertTriangle,
  Play, CheckCircle, XCircle, Flag
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Project, Task, TaskStatus } from '../types';
import {
  formatDate, formatHours,
  TASK_STATUS_CONFIG, PRIORITY_CONFIG,
  getTaskCountByStatus, getOverdueTasks
} from '../types';

/**
 * ProjectTasksTab - Taches du projet
 */
export const ProjectTasksTab: React.FC<TabContentProps<Project>> = ({ data: project }) => {
  const [filterStatus, setFilterStatus] = useState<TaskStatus | 'ALL'>('ALL');
  const tasks = project.tasks || [];
  const taskCounts = getTaskCountByStatus(project);
  const overdueTasks = getOverdueTasks(project);

  const filteredTasks = filterStatus === 'ALL'
    ? tasks
    : tasks.filter(t => t.status === filterStatus);

  return (
    <div className="azals-std-tab-content">
      {/* Alertes taches en retard */}
      {overdueTasks.length > 0 && (
        <div className="azals-alert azals-alert--warning mb-4">
          <AlertTriangle size={18} />
          <span>
            {overdueTasks.length} tache(s) en retard necessitent votre attention.
          </span>
        </div>
      )}

      {/* Resume des taches */}
      <Grid cols={4} gap="md" className="mb-4">
        <TaskStatCard
          label="A faire"
          count={taskCounts.TODO}
          color="gray"
          active={filterStatus === 'TODO'}
          onClick={() => setFilterStatus(filterStatus === 'TODO' ? 'ALL' : 'TODO')}
        />
        <TaskStatCard
          label="En cours"
          count={taskCounts.IN_PROGRESS}
          color="blue"
          active={filterStatus === 'IN_PROGRESS'}
          onClick={() => setFilterStatus(filterStatus === 'IN_PROGRESS' ? 'ALL' : 'IN_PROGRESS')}
        />
        <TaskStatCard
          label="En revue"
          count={taskCounts.REVIEW}
          color="purple"
          active={filterStatus === 'REVIEW'}
          onClick={() => setFilterStatus(filterStatus === 'REVIEW' ? 'ALL' : 'REVIEW')}
        />
        <TaskStatCard
          label="Terminees"
          count={taskCounts.DONE}
          color="green"
          active={filterStatus === 'DONE'}
          onClick={() => setFilterStatus(filterStatus === 'DONE' ? 'ALL' : 'DONE')}
        />
      </Grid>

      {/* Liste des taches */}
      <Card title={`Taches${filterStatus !== 'ALL' ? ` - ${TASK_STATUS_CONFIG[filterStatus].label}` : ''}`} icon={<CheckSquare size={18} />}>
        {filteredTasks.length > 0 ? (
          <div className="azals-task-list">
            {filteredTasks.map((task) => (
              <TaskItem key={task.id} task={task} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <CheckSquare size={32} className="text-muted" />
            <p className="text-muted">Aucune tache{filterStatus !== 'ALL' ? ' dans ce statut' : ''}</p>
            <Button size="sm" variant="ghost">
              Ajouter une tache
            </Button>
          </div>
        )}
      </Card>

      {/* Vue Kanban (ERP only) */}
      <Card
        title="Vue Kanban"
        icon={<CheckSquare size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-kanban">
          {(['TODO', 'IN_PROGRESS', 'REVIEW', 'DONE'] as TaskStatus[]).map((status) => (
            <div key={status} className="azals-kanban__column">
              <div className={`azals-kanban__header azals-kanban__header--${TASK_STATUS_CONFIG[status].color}`}>
                <span>{TASK_STATUS_CONFIG[status].label}</span>
                <span className="azals-badge azals-badge--gray">{taskCounts[status]}</span>
              </div>
              <div className="azals-kanban__cards">
                {tasks.filter(t => t.status === status).map((task) => (
                  <div key={task.id} className="azals-kanban__card">
                    <div className="font-medium text-sm">{task.title}</div>
                    {task.assignee_name && (
                      <div className="text-xs text-muted mt-1">
                        <User size={10} className="inline mr-1" />
                        {task.assignee_name}
                      </div>
                    )}
                    {task.due_date && (
                      <div className="text-xs text-muted mt-1">
                        <Calendar size={10} className="inline mr-1" />
                        {formatDate(task.due_date)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

/**
 * Carte statistique tache
 */
interface TaskStatCardProps {
  label: string;
  count: number;
  color: string;
  active?: boolean;
  onClick?: () => void;
}

const TaskStatCard: React.FC<TaskStatCardProps> = ({ label, count, color, active, onClick }) => {
  return (
    <div
      className={`azals-stat-card azals-stat-card--${color} ${active ? 'azals-stat-card--active' : ''} cursor-pointer`}
      onClick={onClick}
    >
      <div className="azals-stat-card__value">{count}</div>
      <div className="azals-stat-card__label">{label}</div>
    </div>
  );
};

/**
 * Composant item de tache
 */
const TaskItem: React.FC<{ task: Task }> = ({ task }) => {
  const statusConfig = TASK_STATUS_CONFIG[task.status];
  const priorityConfig = PRIORITY_CONFIG[task.priority];
  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && task.status !== 'DONE';

  const getStatusIcon = () => {
    switch (task.status) {
      case 'TODO':
        return <CheckSquare size={16} className="text-gray-400" />;
      case 'IN_PROGRESS':
        return <Play size={16} className="text-blue-500" />;
      case 'REVIEW':
        return <Clock size={16} className="text-purple-500" />;
      case 'DONE':
        return <CheckCircle size={16} className="text-green-500" />;
    }
  };

  return (
    <div className={`azals-task-item ${isOverdue ? 'azals-task-item--overdue' : ''}`}>
      <div className="azals-task-item__status">{getStatusIcon()}</div>
      <div className="azals-task-item__content">
        <div className="azals-task-item__header">
          <span className="azals-task-item__title">{task.title}</span>
          <div className="azals-task-item__badges">
            <span className={`azals-badge azals-badge--${priorityConfig.color} azals-badge--sm`}>
              <Flag size={10} className="mr-1" />
              {priorityConfig.label}
            </span>
            <span className={`azals-badge azals-badge--${statusConfig.color} azals-badge--sm`}>
              {statusConfig.label}
            </span>
          </div>
        </div>
        {task.description && (
          <p className="azals-task-item__description text-sm text-muted">
            {task.description.length > 100 ? task.description.substring(0, 100) + '...' : task.description}
          </p>
        )}
        <div className="azals-task-item__meta">
          {task.assignee_name && (
            <span className="text-sm">
              <User size={12} className="inline mr-1" />
              {task.assignee_name}
            </span>
          )}
          {task.due_date && (
            <span className={`text-sm ${isOverdue ? 'text-danger' : ''}`}>
              <Calendar size={12} className="inline mr-1" />
              {formatDate(task.due_date)}
              {isOverdue && ' (En retard)'}
            </span>
          )}
          {(task.estimated_hours || task.logged_hours) && (
            <span className="text-sm">
              <Clock size={12} className="inline mr-1" />
              {formatHours(task.logged_hours || 0)} / {formatHours(task.estimated_hours || 0)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectTasksTab;
