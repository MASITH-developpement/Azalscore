/**
 * AZALSCORE Module - Training Types
 * Types TypeScript pour le module de formation
 */

// ============================================================================
// ENUMS
// ============================================================================

export type TrainingType =
  | 'classroom'
  | 'online'
  | 'elearning'
  | 'blended'
  | 'on_the_job'
  | 'workshop'
  | 'seminar'
  | 'certification';

export type TrainingLevel =
  | 'beginner'
  | 'intermediate'
  | 'advanced'
  | 'expert';

export type SessionStatus =
  | 'draft'
  | 'scheduled'
  | 'open'
  | 'in_progress'
  | 'completed'
  | 'cancelled';

export type EnrollmentStatus =
  | 'pending'
  | 'confirmed'
  | 'waitlisted'
  | 'attended'
  | 'completed'
  | 'no_show'
  | 'cancelled';

export type EvaluationType =
  | 'pre_assessment'
  | 'post_assessment'
  | 'quiz'
  | 'practical'
  | 'project'
  | 'certification';

export type ContentType =
  | 'video'
  | 'document'
  | 'presentation'
  | 'quiz'
  | 'interactive'
  | 'scorm';

export type CertificateStatus =
  | 'pending'
  | 'issued'
  | 'expired'
  | 'revoked';

// ============================================================================
// TRAINING CATEGORY
// ============================================================================

export interface TrainingCategory {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  parent_id?: string;
  color?: string;
  is_active: boolean;
}

// ============================================================================
// TRAINING COURSE
// ============================================================================

export interface TrainingCourse {
  id: string;
  tenant_id: string;
  code: string;
  name: string;
  description: string;
  category_id?: string;
  category_name?: string;
  training_type: TrainingType;
  level: TrainingLevel;
  duration_hours: number;
  min_participants: number;
  max_participants: number;
  objectives: string[];
  prerequisites: string[];
  target_audience: string[];
  skills_acquired: string[];
  materials_required: string[];
  cost_per_participant: number | string;
  cost_per_session: number | string;
  currency: string;
  certification_available: boolean;
  certification_validity_months?: number;
  has_elearning: boolean;
  elearning_modules: string[];
  rating_avg: number | string;
  rating_count: number;
  total_sessions: number;
  total_participants: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  // Alias for display
  price?: number | string;
}

export interface TrainingCourseCreate {
  code: string;
  name: string;
  description: string;
  category_id?: string;
  training_type?: TrainingType;
  level?: TrainingLevel;
  duration_hours?: number;
  min_participants?: number;
  max_participants?: number;
  objectives?: string[];
  prerequisites?: string[];
  skills_acquired?: string[];
  cost_per_participant?: number;
  cost_per_session?: number;
  certification_available?: boolean;
  certification_validity_months?: number;
}

export interface TrainingCourseUpdate {
  name?: string;
  description?: string;
  category_id?: string;
  training_type?: TrainingType;
  level?: TrainingLevel;
  duration_hours?: number;
  min_participants?: number;
  max_participants?: number;
  objectives?: string[];
  prerequisites?: string[];
  skills_acquired?: string[];
  cost_per_participant?: number;
  cost_per_session?: number;
  certification_available?: boolean;
  certification_validity_months?: number;
  is_active?: boolean;
}

// ============================================================================
// TRAINER
// ============================================================================

export interface Trainer {
  id: string;
  tenant_id: string;
  user_id?: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  bio?: string;
  specializations: string[];
  certifications: string[];
  languages: string[];
  hourly_rate: number | string;
  daily_rate: number | string;
  currency: string;
  is_internal: boolean;
  company_name?: string;
  rating_avg: number | string;
  rating_count: number;
  total_sessions: number;
  total_hours: number;
  is_active: boolean;
  created_at: string;
}

export interface TrainerCreate {
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  bio?: string;
  specializations?: string[];
  certifications?: string[];
  languages?: string[];
  hourly_rate?: number;
  daily_rate?: number;
  is_internal?: boolean;
  company_name?: string;
}

export interface TrainerUpdate {
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  bio?: string;
  specializations?: string[];
  certifications?: string[];
  languages?: string[];
  hourly_rate?: number;
  daily_rate?: number;
  is_internal?: boolean;
  company_name?: string;
  is_active?: boolean;
}

// ============================================================================
// TRAINING SESSION
// ============================================================================

export interface TrainingSession {
  id: string;
  tenant_id: string;
  course_id: string;
  course_name: string;
  trainer_id?: string;
  trainer_name?: string;
  status: SessionStatus;
  start_date: string;
  end_date?: string;
  start_time?: string;
  end_time?: string;
  location?: string;
  room?: string;
  is_virtual: boolean;
  virtual_link?: string;
  max_participants: number;
  enrolled_count: number;
  waitlist_count: number;
  attendance_count: number;
  cost_total: number | string;
  materials_provided: string[];
  schedule: Record<string, unknown>[];
  notes?: string;
  internal_notes?: string;
  created_by?: string;
  created_at: string;
  updated_at?: string;
}

export interface TrainingSessionCreate {
  course_id: string;
  trainer_id?: string;
  start_date: string;
  end_date?: string;
  start_time?: string;
  end_time?: string;
  location?: string;
  room?: string;
  is_virtual?: boolean;
  virtual_link?: string;
  max_participants?: number;
  notes?: string;
}

export interface TrainingSessionUpdate {
  trainer_id?: string;
  status?: SessionStatus;
  start_date?: string;
  end_date?: string;
  start_time?: string;
  end_time?: string;
  location?: string;
  room?: string;
  is_virtual?: boolean;
  virtual_link?: string;
  max_participants?: number;
  notes?: string;
  internal_notes?: string;
}

// ============================================================================
// ENROLLMENT
// ============================================================================

export interface Enrollment {
  id: string;
  tenant_id: string;
  session_id: string;
  participant_id: string;
  participant_name: string;
  participant_email?: string;
  department?: string;
  status: EnrollmentStatus;
  enrolled_at: string;
  confirmed_at?: string;
  attendance_dates: string[];
  completion_date?: string;
  completion_rate: number | string;
  pre_assessment_score?: number | string;
  post_assessment_score?: number | string;
  score_improvement?: number | string;
  certificate_id?: string;
  feedback_submitted: boolean;
  manager_approval_required: boolean;
  manager_approved: boolean;
  manager_approved_by?: string;
  cost_charged: number | string;
  notes?: string;
}

export interface EnrollmentCreate {
  session_id: string;
  participant_id: string;
  participant_name: string;
  participant_email?: string;
  department?: string;
  manager_approval_required?: boolean;
}

// ============================================================================
// EVALUATION
// ============================================================================

export interface Evaluation {
  id: string;
  tenant_id: string;
  session_id: string;
  participant_id: string;
  evaluation_type: EvaluationType;
  title: string;
  max_score: number;
  passing_score: number;
  score?: number;
  passed: boolean;
  time_taken_minutes?: number;
  attempts: number;
  max_attempts: number;
  questions: Record<string, unknown>[];
  answers: Record<string, unknown>[];
  feedback?: string;
  evaluated_by?: string;
  evaluated_at?: string;
  created_at: string;
}

// ============================================================================
// CERTIFICATE
// ============================================================================

export interface Certificate {
  id: string;
  tenant_id: string;
  participant_id: string;
  participant_name: string;
  course_id: string;
  course_name: string;
  session_id: string;
  certificate_number: string;
  status: CertificateStatus;
  issue_date?: string;
  expiry_date?: string;
  score?: number;
  grade?: string;
  skills_certified: string[];
  issued_by?: string;
  file_id?: string;
  verification_url?: string;
  created_at: string;
}

// ============================================================================
// E-LEARNING MODULE
// ============================================================================

export interface ELearningModule {
  id: string;
  tenant_id: string;
  course_id: string;
  title: string;
  description?: string;
  order: number;
  content_type: ContentType;
  content_url?: string;
  file_id?: string;
  duration_minutes: number;
  is_mandatory: boolean;
  passing_score?: number;
  created_at: string;
}

export interface ModuleProgress {
  id: string;
  participant_id: string;
  module_id: string;
  started_at?: string;
  completed_at?: string;
  progress_percent: number | string;
  time_spent_minutes: number;
  score?: number;
  attempts: number;
}

// ============================================================================
// FEEDBACK
// ============================================================================

export interface SessionFeedback {
  id: string;
  session_id: string;
  participant_id: string;
  overall_rating: number;
  content_rating: number;
  trainer_rating: number;
  materials_rating: number;
  venue_rating?: number;
  would_recommend: boolean;
  strengths?: string;
  improvements?: string;
  additional_comments?: string;
  submitted_at: string;
}

export interface FeedbackCreate {
  session_id: string;
  overall_rating: number;
  content_rating: number;
  trainer_rating: number;
  materials_rating: number;
  venue_rating?: number;
  would_recommend?: boolean;
  strengths?: string;
  improvements?: string;
  additional_comments?: string;
}

// ============================================================================
// BUDGET
// ============================================================================

export interface TrainingBudget {
  id: string;
  tenant_id: string;
  year: number;
  department?: string;
  allocated_amount: number | string;
  spent_amount: number | string;
  committed_amount: number | string;
  remaining_amount: number | string;
  currency: string;
  target_hours_per_employee: number;
  actual_hours_per_employee: number | string;
}

// ============================================================================
// STATS
// ============================================================================

export interface TrainingStats {
  tenant_id: string;
  period_start: string;
  period_end: string;
  total_courses: number;
  total_sessions: number;
  sessions_completed: number;
  total_participants: number;
  unique_participants: number;
  total_hours: number;
  completion_rate: number | string;
  avg_satisfaction: number | string;
  avg_score_improvement: number | string;
  certificates_issued: number;
  total_cost: number | string;
  cost_per_hour: number | string;
}

export interface TrainingDashboard {
  stats: TrainingStats;
  upcoming_sessions: TrainingSession[];
  recent_completions: Enrollment[];
  top_courses: TrainingCourse[];
}

// ============================================================================
// LIST RESPONSES
// ============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export type CourseListResponse = PaginatedResponse<TrainingCourse>;
export type SessionListResponse = PaginatedResponse<TrainingSession>;
export type TrainerListResponse = PaginatedResponse<Trainer>;
export type EnrollmentListResponse = PaginatedResponse<Enrollment>;
export type CertificateListResponse = PaginatedResponse<Certificate>;

// ============================================================================
// FILTERS
// ============================================================================

export interface CourseFilters {
  category_id?: string;
  training_type?: TrainingType;
  level?: TrainingLevel;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface SessionFilters {
  course_id?: string;
  trainer_id?: string;
  status?: SessionStatus;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
}

export interface EnrollmentFilters {
  session_id?: string;
  participant_id?: string;
  status?: EnrollmentStatus;
  page?: number;
  page_size?: number;
}

// ============================================================================
// CONFIG CONSTANTS
// ============================================================================

export const TRAINING_TYPE_CONFIG: Record<TrainingType, { label: string; color: string }> = {
  classroom: { label: 'Presentiel', color: 'blue' },
  online: { label: 'En ligne', color: 'green' },
  elearning: { label: 'E-learning', color: 'cyan' },
  blended: { label: 'Mixte', color: 'purple' },
  on_the_job: { label: 'Sur le terrain', color: 'orange' },
  workshop: { label: 'Atelier', color: 'yellow' },
  seminar: { label: 'Seminaire', color: 'pink' },
  certification: { label: 'Certification', color: 'red' },
};

export const TRAINING_LEVEL_CONFIG: Record<TrainingLevel, { label: string; color: string }> = {
  beginner: { label: 'Debutant', color: 'green' },
  intermediate: { label: 'Intermediaire', color: 'yellow' },
  advanced: { label: 'Avance', color: 'orange' },
  expert: { label: 'Expert', color: 'red' },
};

export const SESSION_STATUS_CONFIG: Record<SessionStatus, { label: string; color: string }> = {
  draft: { label: 'Brouillon', color: 'gray' },
  scheduled: { label: 'Planifiee', color: 'blue' },
  open: { label: 'Inscriptions ouvertes', color: 'green' },
  in_progress: { label: 'En cours', color: 'orange' },
  completed: { label: 'Terminee', color: 'gray' },
  cancelled: { label: 'Annulee', color: 'red' },
};

export const ENROLLMENT_STATUS_CONFIG: Record<EnrollmentStatus, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'gray' },
  confirmed: { label: 'Confirmee', color: 'green' },
  waitlisted: { label: 'Liste d\'attente', color: 'yellow' },
  attended: { label: 'Present', color: 'blue' },
  completed: { label: 'Terminee', color: 'green' },
  no_show: { label: 'Absent', color: 'red' },
  cancelled: { label: 'Annulee', color: 'gray' },
};

export const CERTIFICATE_STATUS_CONFIG: Record<CertificateStatus, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'gray' },
  issued: { label: 'Delivre', color: 'green' },
  expired: { label: 'Expire', color: 'orange' },
  revoked: { label: 'Revoque', color: 'red' },
};
