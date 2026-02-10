/**
 * AZALSCORE Module - Projects Types
 * Types et helpers pour la gestion de projets
 */

// ============================================================================
// TYPES DE BASE
// ============================================================================

export type ProjectStatus = 'DRAFT' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'CANCELLED';
export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'REVIEW' | 'DONE';
export type Priority = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

// ============================================================================
// INTERFACES PRINCIPALES
// ============================================================================

export interface Project {
  id: string;
  code: string;
  name: string;
  description?: string;
  client_id?: string;
  client_name?: string;
  manager_id?: string;
  manager_name?: string;
  team_members?: TeamMember[];
  status: ProjectStatus;
  priority: Priority;
  start_date?: string;
  end_date?: string;
  actual_end_date?: string;
  budget?: number;
  spent?: number;
  progress: number;
  currency: string;
  tags?: string[];
  tasks?: Task[];
  milestones?: Milestone[];
  documents?: ProjectDocument[];
  time_entries?: TimeEntry[];
  history?: ProjectHistoryEntry[];
  notes?: string;
  created_at: string;
  created_by?: string;
  updated_at?: string;
  updated_by?: string;
}

export interface Task {
  id: string;
  project_id: string;
  project_name?: string;
  parent_id?: string;
  title: string;
  description?: string;
  assignee_id?: string;
  assignee_name?: string;
  status: TaskStatus;
  priority: Priority;
  start_date?: string;
  due_date?: string;
  completed_at?: string;
  estimated_hours?: number;
  logged_hours?: number;
  subtasks?: Task[];
  dependencies?: string[];
  tags?: string[];
  created_at: string;
  created_by?: string;
  updated_at?: string;
}

export interface TimeEntry {
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
  hourly_rate?: number;
  created_at: string;
}

export interface TeamMember {
  id: string;
  user_id: string;
  user_name: string;
  user_email?: string;
  role: 'MANAGER' | 'MEMBER' | 'VIEWER';
  assigned_at: string;
  hours_logged?: number;
}

export interface Milestone {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  due_date: string;
  completed_at?: string;
  status: 'PENDING' | 'COMPLETED' | 'OVERDUE';
}

export interface ProjectDocument {
  id: string;
  project_id: string;
  name: string;
  type: 'specification' | 'contract' | 'report' | 'invoice' | 'other';
  file_url?: string;
  file_size?: number;
  mime_type?: string;
  category?: string;
  uploaded_by?: string;
  uploaded_by_name?: string;
  created_at: string;
}

export interface ProjectHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_id?: string;
  user_name?: string;
  field?: string;
  old_value?: string;
  new_value?: string;
  details?: string;
}

export interface ProjectStats {
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
// CONFIGURATION
// ============================================================================

export const PROJECT_STATUS_CONFIG: Record<ProjectStatus, { label: string; color: string; description: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray', description: 'Projet en preparation' },
  ACTIVE: { label: 'En cours', color: 'blue', description: 'Projet actif' },
  PAUSED: { label: 'En pause', color: 'orange', description: 'Projet suspendu' },
  COMPLETED: { label: 'Termine', color: 'green', description: 'Projet termine' },
  CANCELLED: { label: 'Annule', color: 'red', description: 'Projet annule' }
};

export const TASK_STATUS_CONFIG: Record<TaskStatus, { label: string; color: string; description: string }> = {
  TODO: { label: 'A faire', color: 'gray', description: 'Tache non demarree' },
  IN_PROGRESS: { label: 'En cours', color: 'blue', description: 'Tache en cours' },
  REVIEW: { label: 'En revue', color: 'purple', description: 'En attente de validation' },
  DONE: { label: 'Termine', color: 'green', description: 'Tache terminee' }
};

export const PRIORITY_CONFIG: Record<Priority, { label: string; color: string; icon?: string }> = {
  LOW: { label: 'Basse', color: 'gray' },
  NORMAL: { label: 'Normale', color: 'blue' },
  HIGH: { label: 'Haute', color: 'orange' },
  URGENT: { label: 'Urgente', color: 'red' }
};

export const TEAM_ROLE_CONFIG: Record<string, { label: string; color: string }> = {
  MANAGER: { label: 'Responsable', color: 'purple' },
  MEMBER: { label: 'Membre', color: 'blue' },
  VIEWER: { label: 'Observateur', color: 'gray' }
};

export const DOCUMENT_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  specification: { label: 'Specification', color: 'blue' },
  contract: { label: 'Contrat', color: 'purple' },
  report: { label: 'Rapport', color: 'green' },
  invoice: { label: 'Facture', color: 'orange' },
  other: { label: 'Autre', color: 'gray' }
};

export const MILESTONE_STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  PENDING: { label: 'En attente', color: 'gray' },
  COMPLETED: { label: 'Atteint', color: 'green' },
  OVERDUE: { label: 'En retard', color: 'red' }
};

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Calcule la duree du projet en jours
 */
export const getProjectDuration = (project: Project): number | null => {
  if (!project.start_date) return null;
  const endDate = project.actual_end_date || project.end_date;
  if (!endDate) return null;
  const start = new Date(project.start_date);
  const end = new Date(endDate);
  return Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
};

/**
 * Calcule les jours restants
 */
export const getDaysRemaining = (project: Project): number | null => {
  if (!project.end_date || project.status === 'COMPLETED' || project.status === 'CANCELLED') return null;
  const end = new Date(project.end_date);
  const now = new Date();
  return Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
};

/**
 * Verifie si le projet est en retard
 */
export const isProjectOverdue = (project: Project): boolean => {
  const daysRemaining = getDaysRemaining(project);
  return daysRemaining !== null && daysRemaining < 0 && project.status === 'ACTIVE';
};

/**
 * Verifie si le projet est proche de l'echeance
 */
export const isProjectNearDeadline = (project: Project, days = 7): boolean => {
  const daysRemaining = getDaysRemaining(project);
  return daysRemaining !== null && daysRemaining >= 0 && daysRemaining <= days && project.status === 'ACTIVE';
};

/**
 * Calcule le budget restant
 */
export const getRemainingBudget = (project: Project): number | null => {
  if (project.budget === undefined) return null;
  return project.budget - (project.spent || 0);
};

/**
 * Calcule le pourcentage de budget utilise
 */
export const getBudgetUsedPercent = (project: Project): number => {
  if (!project.budget || project.budget === 0) return 0;
  return Math.round(((project.spent || 0) / project.budget) * 100);
};

/**
 * Verifie si le budget est depasse
 */
export const isBudgetOverrun = (project: Project): boolean => {
  if (!project.budget) return false;
  return (project.spent || 0) > project.budget;
};

/**
 * Compte les taches par statut
 */
export const getTaskCountByStatus = (project: Project): Record<TaskStatus, number> => {
  const counts: Record<TaskStatus, number> = {
    TODO: 0,
    IN_PROGRESS: 0,
    REVIEW: 0,
    DONE: 0
  };
  project.tasks?.forEach(task => {
    counts[task.status]++;
  });
  return counts;
};

/**
 * Calcule le total des heures logguees
 */
export const getTotalLoggedHours = (project: Project): number => {
  return project.time_entries?.reduce((sum, entry) => sum + entry.hours, 0) || 0;
};

/**
 * Calcule les heures facturables
 */
export const getBillableHours = (project: Project): number => {
  return project.time_entries?.filter(e => e.is_billable).reduce((sum, entry) => sum + entry.hours, 0) || 0;
};

/**
 * Calcule le montant facturable
 */
export const getBillableAmount = (project: Project): number => {
  return project.time_entries?.filter(e => e.is_billable).reduce((sum, entry) => {
    return sum + (entry.hours * (entry.hourly_rate || 0));
  }, 0) || 0;
};

/**
 * Calcule les heures estimees totales
 */
export const getTotalEstimatedHours = (project: Project): number => {
  return project.tasks?.reduce((sum, task) => sum + (task.estimated_hours || 0), 0) || 0;
};

/**
 * Compte les jalons par statut
 */
export const getMilestoneStats = (project: Project): { total: number; completed: number; overdue: number } => {
  const milestones = project.milestones || [];
  return {
    total: milestones.length,
    completed: milestones.filter(m => m.status === 'COMPLETED').length,
    overdue: milestones.filter(m => m.status === 'OVERDUE').length
  };
};

/**
 * Verifie si le projet est actif
 */
export const isProjectActive = (project: Project): boolean => {
  return project.status === 'ACTIVE';
};

/**
 * Verifie si le projet est termine
 */
export const isProjectCompleted = (project: Project): boolean => {
  return project.status === 'COMPLETED';
};

/**
 * Verifie si le projet est en pause
 */
export const isProjectPaused = (project: Project): boolean => {
  return project.status === 'PAUSED';
};

/**
 * Obtient le prochain jalon
 */
export const getNextMilestone = (project: Project): Milestone | null => {
  const pending = project.milestones?.filter(m => m.status === 'PENDING').sort((a, b) =>
    new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
  );
  return pending?.[0] || null;
};

/**
 * Obtient les taches en retard
 */
export const getOverdueTasks = (project: Project): Task[] => {
  const now = new Date();
  return project.tasks?.filter(task =>
    task.due_date &&
    new Date(task.due_date) < now &&
    task.status !== 'DONE'
  ) || [];
};

/**
 * Formate la duree du projet
 */
export const formatProjectDuration = (project: Project): string => {
  const duration = getProjectDuration(project);
  if (duration === null) return '-';
  if (duration < 30) return `${duration} jours`;
  if (duration < 365) return `${Math.round(duration / 30)} mois`;
  return `${(duration / 365).toFixed(1)} ans`;
};

export default {
  PROJECT_STATUS_CONFIG,
  TASK_STATUS_CONFIG,
  PRIORITY_CONFIG,
};
