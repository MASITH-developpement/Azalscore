/**
 * AZALSCORE - HR (Ressources Humaines) API
 * ========================================
 * Client API typé pour la gestion RH
 */

import { api } from '@core/api-client';

// ============================================================================
// HELPERS
// ============================================================================

function buildQueryString(params: Record<string, string | number | boolean | undefined | null>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

// ============================================================================
// ENUMS
// ============================================================================

export type EmployeeStatus = 'ACTIVE' | 'ON_LEAVE' | 'SUSPENDED' | 'TERMINATED';
export type ContractType = 'CDI' | 'CDD' | 'INTERIM' | 'APPRENTICESHIP' | 'INTERNSHIP' | 'FREELANCE';
export type LeaveType = 'ANNUAL' | 'SICK' | 'MATERNITY' | 'PATERNITY' | 'UNPAID' | 'RTT' | 'COMPENSATORY' | 'SPECIAL' | 'OTHER';
export type LeaveStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
export type PayrollStatus = 'DRAFT' | 'VALIDATED' | 'PAID' | 'CANCELLED';
export type PayElementType = 'SALARY' | 'BONUS' | 'OVERTIME' | 'DEDUCTION' | 'CHARGE' | 'TAX' | 'OTHER';
export type TrainingStatus = 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type TrainingType = 'INTERNAL' | 'EXTERNAL' | 'ONLINE' | 'CERTIFICATION';
export type EvaluationStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
export type EvaluationType = 'ANNUAL' | 'PROBATION' | 'PROJECT' | 'PROMOTION' | 'OTHER';
export type DocumentType = 'CONTRACT' | 'ID' | 'CERTIFICATE' | 'PAYSLIP' | 'EVALUATION' | 'TRAINING' | 'MEDICAL' | 'OTHER';

// ============================================================================
// TYPES - DÉPARTEMENTS
// ============================================================================

export interface DepartmentCreate {
  code: string;
  name: string;
  description?: string | null;
  parent_id?: string | null;
  manager_id?: string | null;
  cost_center?: string | null;
}

export interface DepartmentUpdate {
  name?: string;
  description?: string | null;
  parent_id?: string | null;
  manager_id?: string | null;
  cost_center?: string | null;
  is_active?: boolean;
}

export interface Department {
  id: string;
  code: string;
  name: string;
  description: string | null;
  parent_id: string | null;
  manager_id: string | null;
  cost_center: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - POSTES
// ============================================================================

export interface PositionCreate {
  code: string;
  title: string;
  description?: string | null;
  department_id?: string | null;
  category?: string | null;
  level?: number;
  min_salary?: number | null;
  max_salary?: number | null;
  requirements?: string[];
}

export interface PositionUpdate {
  title?: string;
  description?: string | null;
  department_id?: string | null;
  category?: string | null;
  level?: number;
  min_salary?: number | null;
  max_salary?: number | null;
  requirements?: string[];
  is_active?: boolean;
}

export interface Position {
  id: string;
  code: string;
  title: string;
  description: string | null;
  department_id: string | null;
  category: string | null;
  level: number;
  min_salary: number | null;
  max_salary: number | null;
  requirements: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - EMPLOYÉS
// ============================================================================

export interface EmployeeCreate {
  employee_number: string;
  first_name: string;
  last_name: string;
  maiden_name?: string | null;
  gender?: string | null;
  birth_date?: string | null;
  birth_place?: string | null;
  nationality?: string | null;
  social_security_number?: string | null;
  email?: string | null;
  personal_email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  postal_code?: string | null;
  city?: string | null;
  country?: string;
  user_id?: number | null;
  department_id?: string | null;
  position_id?: string | null;
  manager_id?: string | null;
  work_location?: string | null;
  contract_type?: ContractType | null;
  hire_date?: string | null;
  start_date?: string | null;
  gross_salary?: number | null;
  currency?: string;
  weekly_hours?: number;
  bank_name?: string | null;
  iban?: string | null;
  bic?: string | null;
}

export interface EmployeeUpdate {
  first_name?: string;
  last_name?: string;
  maiden_name?: string | null;
  gender?: string | null;
  birth_date?: string | null;
  birth_place?: string | null;
  nationality?: string | null;
  email?: string | null;
  personal_email?: string | null;
  phone?: string | null;
  mobile?: string | null;
  address_line1?: string | null;
  address_line2?: string | null;
  postal_code?: string | null;
  city?: string | null;
  country?: string | null;
  department_id?: string | null;
  position_id?: string | null;
  manager_id?: string | null;
  work_location?: string | null;
  status?: EmployeeStatus;
  gross_salary?: number | null;
  weekly_hours?: number | null;
  bank_name?: string | null;
  iban?: string | null;
  bic?: string | null;
  photo_url?: string | null;
  notes?: string | null;
  tags?: string[];
  is_active?: boolean;
}

export interface Employee {
  id: string;
  employee_number: string;
  first_name: string;
  last_name: string;
  maiden_name: string | null;
  gender: string | null;
  birth_date: string | null;
  birth_place: string | null;
  nationality: string | null;
  social_security_number: string | null;
  email: string | null;
  personal_email: string | null;
  phone: string | null;
  mobile: string | null;
  address_line1: string | null;
  address_line2: string | null;
  postal_code: string | null;
  city: string | null;
  country: string;
  user_id: number | null;
  department_id: string | null;
  position_id: string | null;
  manager_id: string | null;
  work_location: string | null;
  status: EmployeeStatus;
  contract_type: ContractType | null;
  hire_date: string | null;
  start_date: string | null;
  end_date: string | null;
  gross_salary: number | null;
  currency: string;
  weekly_hours: number;
  annual_leave_balance: number;
  rtt_balance: number;
  photo_url: string | null;
  tags: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmployeeList {
  items: Employee[];
  total: number;
}

// ============================================================================
// TYPES - CONTRATS
// ============================================================================

export interface ContractCreate {
  employee_id: string;
  contract_number: string;
  type: ContractType;
  title?: string | null;
  department_id?: string | null;
  position_id?: string | null;
  start_date: string;
  end_date?: string | null;
  probation_duration?: number | null;
  gross_salary: number;
  currency?: string;
  pay_frequency?: string;
  weekly_hours?: number;
  work_schedule?: string;
  bonus_clause?: string | null;
  notice_period?: number | null;
  non_compete_clause?: boolean;
  confidentiality_clause?: boolean;
}

export interface Contract {
  id: string;
  employee_id: string;
  contract_number: string;
  type: ContractType;
  title: string | null;
  department_id: string | null;
  position_id: string | null;
  start_date: string;
  end_date: string | null;
  probation_duration: number | null;
  probation_end_date: string | null;
  gross_salary: number;
  currency: string;
  pay_frequency: string;
  weekly_hours: number;
  work_schedule: string;
  signed_date: string | null;
  is_current: boolean;
  terminated_date: string | null;
  termination_reason: string | null;
  document_url: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - CONGÉS
// ============================================================================

export interface LeaveRequestCreate {
  type: LeaveType;
  start_date: string;
  end_date: string;
  half_day_start?: boolean;
  half_day_end?: boolean;
  reason?: string | null;
  replacement_id?: string | null;
}

export interface LeaveRequest {
  id: string;
  employee_id: string;
  employee_name: string | null;
  type: LeaveType;
  start_date: string;
  end_date: string;
  half_day_start: boolean;
  half_day_end: boolean;
  reason: string | null;
  replacement_id: string | null;
  status: LeaveStatus;
  days: number;
  attachment_url: string | null;
  approved_by: string | null;
  approved_at: string | null;
  rejection_reason: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface LeaveBalance {
  id: string;
  employee_id: string;
  year: number;
  leave_type: LeaveType;
  entitled_days: number;
  taken_days: number;
  pending_days: number;
  remaining_days: number;
  carried_over: number;
}

export interface LeaveRequestList {
  items: LeaveRequest[];
  total: number;
}

// ============================================================================
// TYPES - PAIE
// ============================================================================

export interface PayrollPeriodCreate {
  name: string;
  year: number;
  month: number;
  start_date: string;
  end_date: string;
  payment_date?: string | null;
}

export interface PayrollPeriod {
  id: string;
  name: string;
  year: number;
  month: number;
  start_date: string;
  end_date: string;
  payment_date: string | null;
  status: PayrollStatus;
  is_closed: boolean;
  closed_at: string | null;
  total_gross: number;
  total_net: number;
  total_employer_charges: number;
  employee_count: number;
  created_at: string;
  updated_at: string;
}

export interface PayslipLineCreate {
  type: PayElementType;
  code: string;
  label: string;
  base?: number | null;
  rate?: number | null;
  quantity?: number | null;
  amount: number;
  is_deduction?: boolean;
  is_employer_charge?: boolean;
}

export interface PayslipLine {
  id: string;
  payslip_id: string;
  type: PayElementType;
  code: string;
  label: string;
  base: number | null;
  rate: number | null;
  quantity: number | null;
  amount: number;
  is_deduction: boolean;
  is_employer_charge: boolean;
  line_number: number;
  created_at: string;
}

export interface PayslipCreate {
  employee_id: string;
  period_id: string;
  start_date: string;
  end_date: string;
  payment_date?: string | null;
  worked_hours?: number;
  overtime_hours?: number;
  absence_hours?: number;
  gross_salary: number;
  lines?: PayslipLineCreate[];
}

export interface Payslip {
  id: string;
  employee_id: string;
  period_id: string;
  payslip_number: string;
  status: PayrollStatus;
  start_date: string;
  end_date: string;
  payment_date: string | null;
  worked_hours: number;
  overtime_hours: number;
  absence_hours: number;
  gross_salary: number;
  total_gross: number;
  total_deductions: number;
  employee_charges: number;
  employer_charges: number;
  taxable_income: number;
  tax_withheld: number;
  net_before_tax: number;
  net_salary: number;
  ytd_gross: number;
  ytd_net: number;
  ytd_tax: number;
  document_url: string | null;
  sent_at: string | null;
  validated_by: string | null;
  validated_at: string | null;
  paid_at: string | null;
  lines: PayslipLine[];
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - TEMPS DE TRAVAIL
// ============================================================================

export interface TimeEntryCreate {
  date: string;
  start_time?: string | null;
  end_time?: string | null;
  break_duration?: number;
  worked_hours: number;
  overtime_hours?: number;
  project_id?: string | null;
  task_description?: string | null;
}

export interface TimeEntry {
  id: string;
  employee_id: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
  break_duration: number;
  worked_hours: number;
  overtime_hours: number;
  project_id: string | null;
  task_description: string | null;
  is_approved: boolean;
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - COMPÉTENCES
// ============================================================================

export interface SkillCreate {
  code: string;
  name: string;
  category?: string | null;
  description?: string | null;
}

export interface Skill {
  id: string;
  code: string;
  name: string;
  category: string | null;
  description: string | null;
  is_active: boolean;
  created_at: string;
}

export interface EmployeeSkillCreate {
  skill_id: string;
  level?: number;
  acquired_date?: string | null;
  expiry_date?: string | null;
  certification_url?: string | null;
  notes?: string | null;
}

export interface EmployeeSkill {
  id: string;
  employee_id: string;
  skill_id: string;
  level: number;
  acquired_date: string | null;
  expiry_date: string | null;
  certification_url: string | null;
  notes: string | null;
  validated_by: string | null;
  validated_at: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - FORMATIONS
// ============================================================================

export interface TrainingCreate {
  code: string;
  name: string;
  description?: string | null;
  type: TrainingType;
  provider?: string | null;
  trainer?: string | null;
  location?: string | null;
  start_date: string;
  end_date: string;
  duration_hours?: number | null;
  max_participants?: number | null;
  cost_per_person?: number | null;
  skills_acquired?: string[];
}

export interface Training {
  id: string;
  code: string;
  name: string;
  description: string | null;
  type: TrainingType;
  provider: string | null;
  trainer: string | null;
  location: string | null;
  start_date: string;
  end_date: string;
  duration_hours: number | null;
  max_participants: number | null;
  cost_per_person: number | null;
  status: TrainingStatus;
  total_cost: number | null;
  skills_acquired: string[];
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface TrainingParticipantCreate {
  employee_id: string;
}

export interface TrainingParticipant {
  id: string;
  training_id: string;
  employee_id: string;
  status: string;
  attendance_rate: number | null;
  score: number | null;
  passed: boolean | null;
  certificate_url: string | null;
  feedback: string | null;
  enrolled_at: string;
  completed_at: string | null;
}

// ============================================================================
// TYPES - ÉVALUATIONS
// ============================================================================

export interface EvaluationCreate {
  employee_id: string;
  type: EvaluationType;
  period_start: string;
  period_end: string;
  scheduled_date?: string | null;
  evaluator_id?: string | null;
}

export interface EvaluationUpdate {
  status?: EvaluationStatus;
  completed_date?: string | null;
  overall_score?: number | null;
  objectives_score?: number | null;
  skills_score?: number | null;
  behavior_score?: number | null;
  objectives_achieved?: string[];
  objectives_next?: string[];
  strengths?: string | null;
  improvements?: string | null;
  employee_comments?: string | null;
  evaluator_comments?: string | null;
  promotion_recommended?: boolean;
  salary_increase_recommended?: boolean;
  training_needs?: string[];
}

export interface Evaluation {
  id: string;
  employee_id: string;
  type: EvaluationType;
  period_start: string;
  period_end: string;
  scheduled_date: string | null;
  evaluator_id: string | null;
  status: EvaluationStatus;
  completed_date: string | null;
  overall_score: number | null;
  objectives_score: number | null;
  skills_score: number | null;
  behavior_score: number | null;
  objectives_achieved: string[];
  objectives_next: string[];
  strengths: string | null;
  improvements: string | null;
  employee_comments: string | null;
  evaluator_comments: string | null;
  promotion_recommended: boolean;
  salary_increase_recommended: boolean;
  training_needs: string[];
  employee_signed_at: string | null;
  evaluator_signed_at: string | null;
  document_url: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TYPES - DOCUMENTS
// ============================================================================

export interface HRDocumentCreate {
  employee_id: string;
  type: DocumentType;
  name: string;
  description?: string | null;
  file_url: string;
  file_size?: number | null;
  mime_type?: string | null;
  issue_date?: string | null;
  expiry_date?: string | null;
  is_confidential?: boolean;
}

export interface HRDocument {
  id: string;
  employee_id: string;
  type: DocumentType;
  name: string;
  description: string | null;
  file_url: string;
  file_size: number | null;
  mime_type: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  is_confidential: boolean;
  uploaded_by: string | null;
  created_at: string;
}

// ============================================================================
// TYPES - DASHBOARD
// ============================================================================

export interface HRDashboard {
  total_employees: number;
  active_employees: number;
  on_leave_employees: number;
  new_hires_this_month: number;
  departures_this_month: number;
  cdi_count: number;
  cdd_count: number;
  probation_ending_soon: number;
  contracts_ending_soon: number;
  pending_leave_requests: number;
  employees_on_leave_today: number;
  average_leave_balance: number;
  current_payroll_status: string;
  last_payroll_total: number;
  average_salary: number;
  trainings_in_progress: number;
  employees_trained_this_year: number;
  pending_evaluations: number;
  overdue_evaluations: number;
  by_department: Record<string, number>;
  by_contract_type: Record<string, number>;
  by_gender: Record<string, number>;
}

// ============================================================================
// API CLIENT
// ============================================================================

const BASE_PATH = '/v1/hr';

export const hrApi = {
  // --------------------------------------------------------------------------
  // Dashboard
  // --------------------------------------------------------------------------
  getDashboard: () =>
    api.get<HRDashboard>(`${BASE_PATH}/dashboard`),

  // --------------------------------------------------------------------------
  // Départements
  // --------------------------------------------------------------------------
  createDepartment: (data: DepartmentCreate) =>
    api.post<Department>(`${BASE_PATH}/departments`, data),

  listDepartments: (isActive = true) =>
    api.get<Department[]>(`${BASE_PATH}/departments${buildQueryString({ is_active: isActive })}`),

  getDepartment: (departmentId: string) =>
    api.get<Department>(`${BASE_PATH}/departments/${departmentId}`),

  updateDepartment: (departmentId: string, data: DepartmentUpdate) =>
    api.put<Department>(`${BASE_PATH}/departments/${departmentId}`, data),

  // --------------------------------------------------------------------------
  // Postes
  // --------------------------------------------------------------------------
  createPosition: (data: PositionCreate) =>
    api.post<Position>(`${BASE_PATH}/positions`, data),

  listPositions: (params?: { department_id?: string; is_active?: boolean }) =>
    api.get<Position[]>(`${BASE_PATH}/positions${buildQueryString(params || {})}`),

  getPosition: (positionId: string) =>
    api.get<Position>(`${BASE_PATH}/positions/${positionId}`),

  updatePosition: (positionId: string, data: PositionUpdate) =>
    api.put<Position>(`${BASE_PATH}/positions/${positionId}`, data),

  // --------------------------------------------------------------------------
  // Employés
  // --------------------------------------------------------------------------
  createEmployee: (data: EmployeeCreate) =>
    api.post<Employee>(`${BASE_PATH}/employees`, data),

  listEmployees: (params?: {
    department_id?: string;
    status?: EmployeeStatus;
    manager_id?: string;
    search?: string;
    is_active?: boolean;
    skip?: number;
    limit?: number;
  }) =>
    api.get<EmployeeList>(`${BASE_PATH}/employees${buildQueryString(params || {})}`),

  getEmployee: (employeeId: string) =>
    api.get<Employee>(`${BASE_PATH}/employees/${employeeId}`),

  updateEmployee: (employeeId: string, data: EmployeeUpdate) =>
    api.put<Employee>(`${BASE_PATH}/employees/${employeeId}`, data),

  terminateEmployee: (employeeId: string, endDate: string, reason?: string) =>
    api.post<Employee>(`${BASE_PATH}/employees/${employeeId}/terminate${buildQueryString({
      end_date: endDate,
      reason,
    })}`),

  // --------------------------------------------------------------------------
  // Contrats
  // --------------------------------------------------------------------------
  createContract: (data: ContractCreate) =>
    api.post<Contract>(`${BASE_PATH}/contracts`, data),

  getContract: (contractId: string) =>
    api.get<Contract>(`${BASE_PATH}/contracts/${contractId}`),

  listEmployeeContracts: (employeeId: string) =>
    api.get<Contract[]>(`${BASE_PATH}/employees/${employeeId}/contracts`),

  // --------------------------------------------------------------------------
  // Congés
  // --------------------------------------------------------------------------
  createLeaveRequest: (employeeId: string, data: LeaveRequestCreate) =>
    api.post<LeaveRequest>(`${BASE_PATH}/employees/${employeeId}/leave-requests`, data),

  listLeaveRequests: (params?: {
    employee_id?: string;
    leave_status?: LeaveStatus;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }) =>
    api.get<LeaveRequestList>(`${BASE_PATH}/leave-requests${buildQueryString(params || {})}`),

  approveLeaveRequest: (leaveId: string) =>
    api.post<LeaveRequest>(`${BASE_PATH}/leave-requests/${leaveId}/approve`),

  rejectLeaveRequest: (leaveId: string, reason: string) =>
    api.post<LeaveRequest>(`${BASE_PATH}/leave-requests/${leaveId}/reject${buildQueryString({ reason })}`),

  getEmployeeLeaveBalance: (employeeId: string, year?: number) =>
    api.get<LeaveBalance[]>(`${BASE_PATH}/employees/${employeeId}/leave-balance${buildQueryString({ year })}`),

  // --------------------------------------------------------------------------
  // Paie
  // --------------------------------------------------------------------------
  createPayrollPeriod: (data: PayrollPeriodCreate) =>
    api.post<PayrollPeriod>(`${BASE_PATH}/payroll-periods`, data),

  listPayrollPeriods: (year?: number) =>
    api.get<PayrollPeriod[]>(`${BASE_PATH}/payroll-periods${buildQueryString({ year })}`),

  getPayrollPeriod: (periodId: string) =>
    api.get<PayrollPeriod>(`${BASE_PATH}/payroll-periods/${periodId}`),

  listPayslips: (params?: {
    period_id?: string;
    employee_id?: string;
    year?: number;
    skip?: number;
    limit?: number;
  }) =>
    api.get<Payslip[]>(`${BASE_PATH}/payslips${buildQueryString(params || {})}`),

  createPayslip: (data: PayslipCreate) =>
    api.post<Payslip>(`${BASE_PATH}/payslips`, data),

  validatePayslip: (payslipId: string) =>
    api.post<Payslip>(`${BASE_PATH}/payslips/${payslipId}/validate`),

  getEmployeePayslips: (employeeId: string, year?: number) =>
    api.get<Payslip[]>(`${BASE_PATH}/employees/${employeeId}/payslips${buildQueryString({ year })}`),

  // --------------------------------------------------------------------------
  // Temps de travail
  // --------------------------------------------------------------------------
  createTimeEntry: (employeeId: string, data: TimeEntryCreate) =>
    api.post<TimeEntry>(`${BASE_PATH}/employees/${employeeId}/time-entries`, data),

  listTimeEntries: (params?: {
    employee_id?: string;
    start_date?: string;
    end_date?: string;
  }) =>
    api.get<TimeEntry[]>(`${BASE_PATH}/time-entries${buildQueryString(params || {})}`),

  // --------------------------------------------------------------------------
  // Compétences
  // --------------------------------------------------------------------------
  createSkill: (data: SkillCreate) =>
    api.post<Skill>(`${BASE_PATH}/skills`, data),

  listSkills: (category?: string) =>
    api.get<Skill[]>(`${BASE_PATH}/skills${buildQueryString({ category })}`),

  addEmployeeSkill: (employeeId: string, data: EmployeeSkillCreate) =>
    api.post<EmployeeSkill>(`${BASE_PATH}/employees/${employeeId}/skills`, data),

  getEmployeeSkills: (employeeId: string) =>
    api.get<EmployeeSkill[]>(`${BASE_PATH}/employees/${employeeId}/skills`),

  // --------------------------------------------------------------------------
  // Formations
  // --------------------------------------------------------------------------
  createTraining: (data: TrainingCreate) =>
    api.post<Training>(`${BASE_PATH}/trainings`, data),

  listTrainings: (params?: {
    training_status?: TrainingStatus;
    training_type?: TrainingType;
  }) =>
    api.get<Training[]>(`${BASE_PATH}/trainings${buildQueryString(params || {})}`),

  getTraining: (trainingId: string) =>
    api.get<Training>(`${BASE_PATH}/trainings/${trainingId}`),

  enrollInTraining: (trainingId: string, data: TrainingParticipantCreate) =>
    api.post<TrainingParticipant>(`${BASE_PATH}/trainings/${trainingId}/enroll`, data),

  // --------------------------------------------------------------------------
  // Évaluations
  // --------------------------------------------------------------------------
  createEvaluation: (data: EvaluationCreate) =>
    api.post<Evaluation>(`${BASE_PATH}/evaluations`, data),

  listEvaluations: (params?: {
    employee_id?: string;
    evaluation_status?: EvaluationStatus;
    evaluator_id?: string;
  }) =>
    api.get<Evaluation[]>(`${BASE_PATH}/evaluations${buildQueryString(params || {})}`),

  getEvaluation: (evaluationId: string) =>
    api.get<Evaluation>(`${BASE_PATH}/evaluations/${evaluationId}`),

  updateEvaluation: (evaluationId: string, data: EvaluationUpdate) =>
    api.put<Evaluation>(`${BASE_PATH}/evaluations/${evaluationId}`, data),

  // --------------------------------------------------------------------------
  // Documents
  // --------------------------------------------------------------------------
  createDocument: (data: HRDocumentCreate) =>
    api.post<HRDocument>(`${BASE_PATH}/documents`, data),

  getEmployeeDocuments: (employeeId: string, docType?: DocumentType) =>
    api.get<HRDocument[]>(`${BASE_PATH}/employees/${employeeId}/documents${buildQueryString({
      doc_type: docType,
    })}`),
};

export default hrApi;
