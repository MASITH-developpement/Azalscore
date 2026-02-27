/**
 * AZALSCORE Module - Training API
 * Client API pour le module de formation
 */

import { api } from '@/core/api-client';
import type {
  TrainingCourse, TrainingCourseCreate, TrainingCourseUpdate, CourseListResponse, CourseFilters,
  TrainingSession, TrainingSessionCreate, TrainingSessionUpdate, SessionListResponse, SessionFilters,
  Trainer, TrainerCreate, TrainerUpdate, TrainerListResponse,
  Enrollment, EnrollmentCreate, EnrollmentListResponse, EnrollmentFilters,
  Certificate, CertificateListResponse,
  ELearningModule, ModuleProgress,
  SessionFeedback, FeedbackCreate,
  TrainingCategory,
  TrainingStats, TrainingDashboard,
} from './types';

const BASE_URL = '/training';

// ============================================================================
// COURSE API
// ============================================================================

export const courseApi = {
  list: async (filters?: CourseFilters): Promise<CourseListResponse> => {
    const params = new URLSearchParams();
    if (filters?.category_id) params.set('category_id', filters.category_id);
    if (filters?.training_type) params.set('training_type', filters.training_type);
    if (filters?.level) params.set('level', filters.level);
    if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active));
    if (filters?.search) params.set('search', filters.search);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    return api.get(`${BASE_URL}/courses?${params}`);
  },

  get: async (id: string): Promise<TrainingCourse> => {
    return api.get(`${BASE_URL}/courses/${id}`);
  },

  create: async (data: TrainingCourseCreate): Promise<TrainingCourse> => {
    return api.post(`${BASE_URL}/courses`, data);
  },

  update: async (id: string, data: TrainingCourseUpdate): Promise<TrainingCourse> => {
    return api.put(`${BASE_URL}/courses/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/courses/${id}`);
  },

  getSessions: async (courseId: string): Promise<TrainingSession[]> => {
    return api.get(`${BASE_URL}/courses/${courseId}/sessions`);
  },
};

// ============================================================================
// SESSION API
// ============================================================================

export const sessionApi = {
  list: async (filters?: SessionFilters): Promise<SessionListResponse> => {
    const params = new URLSearchParams();
    if (filters?.course_id) params.set('course_id', filters.course_id);
    if (filters?.trainer_id) params.set('trainer_id', filters.trainer_id);
    if (filters?.status) params.set('status', filters.status);
    if (filters?.from_date) params.set('from_date', filters.from_date);
    if (filters?.to_date) params.set('to_date', filters.to_date);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    return api.get(`${BASE_URL}/sessions?${params}`);
  },

  get: async (id: string): Promise<TrainingSession> => {
    return api.get(`${BASE_URL}/sessions/${id}`);
  },

  create: async (data: TrainingSessionCreate): Promise<TrainingSession> => {
    return api.post(`${BASE_URL}/sessions`, data);
  },

  update: async (id: string, data: TrainingSessionUpdate): Promise<TrainingSession> => {
    return api.put(`${BASE_URL}/sessions/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/sessions/${id}`);
  },

  // Status transitions
  open: async (id: string): Promise<TrainingSession> => {
    return api.post(`${BASE_URL}/sessions/${id}/open`);
  },

  start: async (id: string): Promise<TrainingSession> => {
    return api.post(`${BASE_URL}/sessions/${id}/start`);
  },

  complete: async (id: string): Promise<TrainingSession> => {
    return api.post(`${BASE_URL}/sessions/${id}/complete`);
  },

  cancel: async (id: string, reason?: string): Promise<TrainingSession> => {
    return api.post(`${BASE_URL}/sessions/${id}/cancel`, { reason });
  },

  // Enrollments
  getEnrollments: async (sessionId: string): Promise<Enrollment[]> => {
    return api.get(`${BASE_URL}/sessions/${sessionId}/enrollments`);
  },
};

// ============================================================================
// TRAINER API
// ============================================================================

export const trainerApi = {
  list: async (filters?: { specialization?: string; is_internal?: boolean; is_active?: boolean }): Promise<TrainerListResponse> => {
    const params = new URLSearchParams();
    if (filters?.specialization) params.set('specialization', filters.specialization);
    if (filters?.is_internal !== undefined) params.set('is_internal', String(filters.is_internal));
    if (filters?.is_active !== undefined) params.set('is_active', String(filters.is_active));
    return api.get(`${BASE_URL}/trainers?${params}`);
  },

  get: async (id: string): Promise<Trainer> => {
    return api.get(`${BASE_URL}/trainers/${id}`);
  },

  create: async (data: TrainerCreate): Promise<Trainer> => {
    return api.post(`${BASE_URL}/trainers`, data);
  },

  update: async (id: string, data: TrainerUpdate): Promise<Trainer> => {
    return api.put(`${BASE_URL}/trainers/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/trainers/${id}`);
  },

  getSessions: async (trainerId: string): Promise<TrainingSession[]> => {
    return api.get(`${BASE_URL}/trainers/${trainerId}/sessions`);
  },
};

// ============================================================================
// ENROLLMENT API
// ============================================================================

export const enrollmentApi = {
  list: async (filters?: EnrollmentFilters): Promise<EnrollmentListResponse> => {
    const params = new URLSearchParams();
    if (filters?.session_id) params.set('session_id', filters.session_id);
    if (filters?.participant_id) params.set('participant_id', filters.participant_id);
    if (filters?.status) params.set('status', filters.status);
    if (filters?.page) params.set('page', String(filters.page));
    if (filters?.page_size) params.set('page_size', String(filters.page_size));
    return api.get(`${BASE_URL}/enrollments?${params}`);
  },

  get: async (id: string): Promise<Enrollment> => {
    return api.get(`${BASE_URL}/enrollments/${id}`);
  },

  enroll: async (data: EnrollmentCreate): Promise<Enrollment> => {
    return api.post(`${BASE_URL}/enrollments`, data);
  },

  confirm: async (id: string): Promise<Enrollment> => {
    return api.post(`${BASE_URL}/enrollments/${id}/confirm`);
  },

  cancel: async (id: string): Promise<Enrollment> => {
    return api.post(`${BASE_URL}/enrollments/${id}/cancel`);
  },

  recordAttendance: async (id: string, date: string, isPresent: boolean): Promise<void> => {
    return api.post(`${BASE_URL}/enrollments/${id}/attendance`, { date, is_present: isPresent });
  },

  complete: async (id: string, score?: number): Promise<Enrollment> => {
    return api.post(`${BASE_URL}/enrollments/${id}/complete`, { score });
  },

  getMyEnrollments: async (): Promise<Enrollment[]> => {
    return api.get(`${BASE_URL}/enrollments/my`);
  },
};

// ============================================================================
// CERTIFICATE API
// ============================================================================

export const certificateApi = {
  list: async (filters?: { participant_id?: string; course_id?: string; status?: string }): Promise<CertificateListResponse> => {
    const params = new URLSearchParams();
    if (filters?.participant_id) params.set('participant_id', filters.participant_id);
    if (filters?.course_id) params.set('course_id', filters.course_id);
    if (filters?.status) params.set('status', filters.status);
    return api.get(`${BASE_URL}/certificates?${params}`);
  },

  get: async (id: string): Promise<Certificate> => {
    return api.get(`${BASE_URL}/certificates/${id}`);
  },

  issue: async (enrollmentId: string): Promise<Certificate> => {
    return api.post(`${BASE_URL}/certificates`, { enrollment_id: enrollmentId });
  },

  verify: async (certificateNumber: string): Promise<Certificate> => {
    return api.get(`${BASE_URL}/certificates/verify/${certificateNumber}`);
  },

  download: async (id: string): Promise<Blob> => {
    return api.get(`${BASE_URL}/certificates/${id}/download`, { responseType: 'blob' });
  },

  getMyCertificates: async (): Promise<Certificate[]> => {
    return api.get(`${BASE_URL}/certificates/my`);
  },
};

// ============================================================================
// E-LEARNING API
// ============================================================================

export const elearningApi = {
  getModules: async (courseId: string): Promise<ELearningModule[]> => {
    return api.get(`${BASE_URL}/courses/${courseId}/modules`);
  },

  getModule: async (moduleId: string): Promise<ELearningModule> => {
    return api.get(`${BASE_URL}/modules/${moduleId}`);
  },

  createModule: async (courseId: string, data: Partial<ELearningModule>): Promise<ELearningModule> => {
    return api.post(`${BASE_URL}/courses/${courseId}/modules`, data);
  },

  updateModule: async (moduleId: string, data: Partial<ELearningModule>): Promise<ELearningModule> => {
    return api.put(`${BASE_URL}/modules/${moduleId}`, data);
  },

  deleteModule: async (moduleId: string): Promise<void> => {
    return api.delete(`${BASE_URL}/modules/${moduleId}`);
  },

  getProgress: async (moduleId: string): Promise<ModuleProgress> => {
    return api.get(`${BASE_URL}/modules/${moduleId}/progress`);
  },

  updateProgress: async (moduleId: string, progressPercent: number, timeSpentMinutes: number): Promise<ModuleProgress> => {
    return api.post(`${BASE_URL}/modules/${moduleId}/progress`, {
      progress_percent: progressPercent,
      time_spent_minutes: timeSpentMinutes,
    });
  },
};

// ============================================================================
// FEEDBACK API
// ============================================================================

export const feedbackApi = {
  list: async (sessionId: string): Promise<SessionFeedback[]> => {
    return api.get(`${BASE_URL}/sessions/${sessionId}/feedback`);
  },

  submit: async (data: FeedbackCreate): Promise<SessionFeedback> => {
    return api.post(`${BASE_URL}/feedback`, data);
  },
};

// ============================================================================
// CATEGORY API
// ============================================================================

export const categoryApi = {
  list: async (): Promise<TrainingCategory[]> => {
    return api.get(`${BASE_URL}/categories`);
  },

  get: async (id: string): Promise<TrainingCategory> => {
    return api.get(`${BASE_URL}/categories/${id}`);
  },

  create: async (data: Partial<TrainingCategory>): Promise<TrainingCategory> => {
    return api.post(`${BASE_URL}/categories`, data);
  },

  update: async (id: string, data: Partial<TrainingCategory>): Promise<TrainingCategory> => {
    return api.put(`${BASE_URL}/categories/${id}`, data);
  },

  delete: async (id: string): Promise<void> => {
    return api.delete(`${BASE_URL}/categories/${id}`);
  },
};

// ============================================================================
// STATS API
// ============================================================================

export const statsApi = {
  getStats: async (periodStart: string, periodEnd: string): Promise<TrainingStats> => {
    return api.get(`${BASE_URL}/stats?period_start=${periodStart}&period_end=${periodEnd}`);
  },

  getDashboard: async (): Promise<TrainingDashboard> => {
    return api.get(`${BASE_URL}/dashboard`);
  },
};
