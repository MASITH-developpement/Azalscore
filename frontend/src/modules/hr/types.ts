/**
 * AZALSCORE Module - HR - Types
 * Types et helpers pour le module Ressources Humaines
 */

// ============================================================================
// TYPES DE BASE
// ============================================================================

export type ContractType = 'CDI' | 'CDD' | 'INTERIM' | 'APPRENTICE' | 'INTERN';
export type EmployeeStatus = 'ACTIVE' | 'ON_LEAVE' | 'SUSPENDED' | 'TERMINATED';
export type LeaveType = 'PAID' | 'UNPAID' | 'SICK' | 'MATERNITY' | 'PATERNITY' | 'OTHER';
export type LeaveStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
export type TimesheetStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED';

// ============================================================================
// INTERFACES
// ============================================================================

/**
 * Departement
 */
export interface Department {
  id: string;
  code: string;
  name: string;
  description?: string;
  manager_id?: string;
  manager_name?: string;
  parent_id?: string;
  parent_name?: string;
  employee_count?: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

/**
 * Poste / Position
 */
export interface Position {
  id: string;
  code: string;
  title: string;
  description?: string;
  department_id?: string;
  department_name?: string;
  level: number;
  min_salary?: number;
  max_salary?: number;
  is_active: boolean;
  created_at: string;
}

/**
 * Contact d'urgence
 */
export interface EmergencyContact {
  id: string;
  name: string;
  relationship: string;
  phone: string;
  email?: string;
}

/**
 * Document employe
 */
export interface EmployeeDocument {
  id: string;
  name: string;
  type: 'contract' | 'id' | 'diploma' | 'certificate' | 'other';
  category?: string;
  size?: number;
  url?: string;
  expiry_date?: string;
  created_at: string;
  created_by?: string;
}

/**
 * Historique employe
 */
export interface EmployeeHistoryEntry {
  id: string;
  timestamp: string;
  action: string;
  user_id?: string;
  user_name?: string;
  details?: string;
  old_value?: string;
  new_value?: string;
}

/**
 * Solde de conges
 */
export interface LeaveBalance {
  type: LeaveType;
  type_label: string;
  entitled: number;
  taken: number;
  pending: number;
  remaining: number;
}

/**
 * Demande de conge
 */
export interface LeaveRequest {
  id: string;
  employee_id: string;
  employee_name?: string;
  type: LeaveType;
  start_date: string;
  end_date: string;
  days: number;
  half_day_start?: boolean;
  half_day_end?: boolean;
  status: LeaveStatus;
  reason?: string;
  approved_by_id?: string;
  approved_by_name?: string;
  approved_at?: string;
  rejection_reason?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Entree de feuille de temps
 */
export interface TimesheetEntry {
  id: string;
  date: string;
  hours_worked: number;
  overtime: number;
  project_id?: string;
  project_name?: string;
  task_id?: string;
  task_name?: string;
  notes?: string;
}

/**
 * Feuille de temps
 */
export interface Timesheet {
  id: string;
  employee_id: string;
  employee_name?: string;
  period_start: string;
  period_end: string;
  total_hours: number;
  overtime_hours: number;
  status: TimesheetStatus;
  entries: TimesheetEntry[];
  submitted_at?: string;
  approved_at?: string;
  approved_by_id?: string;
  approved_by_name?: string;
  created_at: string;
}

/**
 * Employe
 */
export interface Employee {
  id: string;
  employee_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  mobile?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  birth_date?: string;
  birth_place?: string;
  nationality?: string;
  social_security_number?: string;
  department_id?: string;
  department_name?: string;
  position_id?: string;
  position_title?: string;
  manager_id?: string;
  manager_name?: string;
  hire_date: string;
  seniority_date?: string;
  contract_type: ContractType;
  contract_start_date?: string;
  contract_end_date?: string;
  probation_end_date?: string;
  status: EmployeeStatus;
  salary?: number;
  salary_currency?: string;
  bank_name?: string;
  bank_iban?: string;
  bank_bic?: string;
  emergency_contacts?: EmergencyContact[];
  leave_balances?: LeaveBalance[];
  leave_requests?: LeaveRequest[];
  timesheets?: Timesheet[];
  documents?: EmployeeDocument[];
  history?: EmployeeHistoryEntry[];
  skills?: string[];
  certifications?: string[];
  notes?: string;
  photo_url?: string;
  created_at: string;
  updated_at?: string;
  created_by?: string;
}

/**
 * Dashboard RH
 */
export interface HRDashboard {
  total_employees: number;
  active_employees: number;
  on_leave: number;
  pending_leave_requests: number;
  contracts_expiring_soon: number;
  new_hires_month: number;
  terminations_month: number;
  departments_count: number;
  positions_count?: number;
  average_seniority?: number;
}

// ============================================================================
// CONFIGURATIONS
// ============================================================================

export const CONTRACT_TYPE_CONFIG: Record<ContractType, { label: string; color: string; description: string }> = {
  CDI: { label: 'CDI', color: 'green', description: 'Contrat a duree indeterminee' },
  CDD: { label: 'CDD', color: 'blue', description: 'Contrat a duree determinee' },
  INTERIM: { label: 'Interim', color: 'orange', description: 'Travail temporaire' },
  APPRENTICE: { label: 'Apprenti', color: 'purple', description: 'Contrat d\'apprentissage' },
  INTERN: { label: 'Stagiaire', color: 'cyan', description: 'Convention de stage' }
};

export const EMPLOYEE_STATUS_CONFIG: Record<EmployeeStatus, { label: string; color: string; description: string }> = {
  ACTIVE: { label: 'Actif', color: 'green', description: 'En poste' },
  ON_LEAVE: { label: 'En conge', color: 'blue', description: 'Absence autorisee' },
  SUSPENDED: { label: 'Suspendu', color: 'orange', description: 'Contrat suspendu' },
  TERMINATED: { label: 'Sorti', color: 'red', description: 'Contrat termine' }
};

export const LEAVE_TYPE_CONFIG: Record<LeaveType, { label: string; color: string; description: string }> = {
  PAID: { label: 'Conges payes', color: 'green', description: 'Conges payes annuels' },
  UNPAID: { label: 'Sans solde', color: 'gray', description: 'Conge non remunere' },
  SICK: { label: 'Maladie', color: 'orange', description: 'Arret maladie' },
  MATERNITY: { label: 'Maternite', color: 'purple', description: 'Conge maternite' },
  PATERNITY: { label: 'Paternite', color: 'blue', description: 'Conge paternite' },
  OTHER: { label: 'Autre', color: 'gray', description: 'Autre type de conge' }
};

export const LEAVE_STATUS_CONFIG: Record<LeaveStatus, { label: string; color: string; description: string }> = {
  PENDING: { label: 'En attente', color: 'orange', description: 'Demande en cours de traitement' },
  APPROVED: { label: 'Approuve', color: 'green', description: 'Demande acceptee' },
  REJECTED: { label: 'Refuse', color: 'red', description: 'Demande refusee' },
  CANCELLED: { label: 'Annule', color: 'gray', description: 'Demande annulee' }
};

export const TIMESHEET_STATUS_CONFIG: Record<TimesheetStatus, { label: string; color: string; description: string }> = {
  DRAFT: { label: 'Brouillon', color: 'gray', description: 'En cours de saisie' },
  SUBMITTED: { label: 'Soumis', color: 'blue', description: 'En attente de validation' },
  APPROVED: { label: 'Approuve', color: 'green', description: 'Valide' },
  REJECTED: { label: 'Rejete', color: 'red', description: 'A corriger' }
};

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Formater une date
 */
export const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('fr-FR');
};

/**
 * Formater une date avec heure
 */
export const formatDateTime = (date: string): string => {
  return new Date(date).toLocaleString('fr-FR');
};

/**
 * Formater un montant en euros
 */
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR' }).format(amount);
};

/**
 * Formater un nombre d'heures
 */
export const formatHours = (hours: number): string => {
  return `${hours}h`;
};

/**
 * Obtenir le nom complet de l'employe
 */
export const getFullName = (employee: Employee): string => {
  return `${employee.first_name} ${employee.last_name}`;
};

/**
 * Obtenir les initiales de l'employe
 */
export const getInitials = (employee: Employee): string => {
  return `${employee.first_name.charAt(0)}${employee.last_name.charAt(0)}`.toUpperCase();
};

/**
 * Calculer l'anciennete en annees
 */
export const getSeniority = (employee: Employee): number => {
  const startDate = new Date(employee.seniority_date || employee.hire_date);
  const now = new Date();
  const years = (now.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24 * 365.25);
  return Math.floor(years);
};

/**
 * Calculer l'anciennete formatee
 */
export const getSeniorityFormatted = (employee: Employee): string => {
  const years = getSeniority(employee);
  if (years < 1) {
    const months = Math.floor(
      (new Date().getTime() - new Date(employee.seniority_date || employee.hire_date).getTime()) /
      (1000 * 60 * 60 * 24 * 30)
    );
    return `${months} mois`;
  }
  return `${years} an${years > 1 ? 's' : ''}`;
};

/**
 * Verifier si l'employe est actif
 */
export const isActive = (employee: Employee): boolean => {
  return employee.status === 'ACTIVE';
};

/**
 * Verifier si l'employe est en conge
 */
export const isOnLeave = (employee: Employee): boolean => {
  return employee.status === 'ON_LEAVE';
};

/**
 * Verifier si le contrat est a duree determinee
 */
export const isFixedTerm = (employee: Employee): boolean => {
  return employee.contract_type === 'CDD' || employee.contract_type === 'INTERIM';
};

/**
 * Verifier si le contrat expire bientot (dans les 30 jours)
 */
export const isContractExpiringSoon = (employee: Employee): boolean => {
  if (!employee.contract_end_date) return false;
  const endDate = new Date(employee.contract_end_date);
  const now = new Date();
  const daysUntilEnd = (endDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  return daysUntilEnd > 0 && daysUntilEnd <= 30;
};

/**
 * Verifier si la periode d'essai est en cours
 */
export const isOnProbation = (employee: Employee): boolean => {
  if (!employee.probation_end_date) return false;
  return new Date(employee.probation_end_date) > new Date();
};

/**
 * Calculer le solde de conges restant
 */
export const getRemainingLeave = (employee: Employee, type: LeaveType = 'PAID'): number => {
  const balance = employee.leave_balances?.find(b => b.type === type);
  return balance?.remaining || 0;
};

/**
 * Calculer le total des conges restants
 */
export const getTotalRemainingLeave = (employee: Employee): number => {
  return employee.leave_balances?.reduce((sum, b) => sum + b.remaining, 0) || 0;
};

/**
 * Obtenir les demandes de conges en attente
 */
export const getPendingLeaveRequests = (employee: Employee): LeaveRequest[] => {
  return employee.leave_requests?.filter(r => r.status === 'PENDING') || [];
};

/**
 * Calculer l'age de l'employe
 */
export const getAge = (employee: Employee): number | null => {
  if (!employee.birth_date) return null;
  const birth = new Date(employee.birth_date);
  const now = new Date();
  const age = (now.getTime() - birth.getTime()) / (1000 * 60 * 60 * 24 * 365.25);
  return Math.floor(age);
};

/**
 * Obtenir la couleur du statut
 */
export const getStatusColor = (status: EmployeeStatus): string => {
  return EMPLOYEE_STATUS_CONFIG[status]?.color || 'gray';
};

/**
 * Obtenir la couleur du type de contrat
 */
export const getContractColor = (type: ContractType): string => {
  return CONTRACT_TYPE_CONFIG[type]?.color || 'gray';
};
