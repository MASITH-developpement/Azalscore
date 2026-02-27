/**
 * AZALSCORE Module - Training API
 * Client API pour le module de formation
 */

import { api } from '@core/api-client';
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
    const queryString = params.toString();
    const url = `${BASE_URL}/courses${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<CourseListResponse>(url);
    return response as unknown as CourseListResponse;
  },

  get: async (id: string): Promise<TrainingCourse> => {
    const response = await api.get<TrainingCourse>(`${BASE_URL}/courses/${id}`);
    return response as unknown as TrainingCourse;
  },

  create: async (data: TrainingCourseCreate): Promise<TrainingCourse> => {
    const response = await api.post<TrainingCourse>(`${BASE_URL}/courses`, data);
    return response as unknown as TrainingCourse;
  },

  update: async (id: string, data: TrainingCourseUpdate): Promise<TrainingCourse> => {
    const response = await api.put<TrainingCourse>(`${BASE_URL}/courses/${id}`, data);
    return response as unknown as TrainingCourse;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/courses/${id}`);
  },

  getSessions: async (courseId: string): Promise<TrainingSession[]> => {
    const response = await api.get<TrainingSession[]>(`${BASE_URL}/courses/${courseId}/sessions`);
    return response as unknown as TrainingSession[];
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
    const queryString = params.toString();
    const url = `${BASE_URL}/sessions${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<SessionListResponse>(url);
    return response as unknown as SessionListResponse;
  },

  get: async (id: string): Promise<TrainingSession> => {
    const response = await api.get<TrainingSession>(`${BASE_URL}/sessions/${id}`);
    return response as unknown as TrainingSession;
  },

  create: async (data: TrainingSessionCreate): Promise<TrainingSession> => {
    const response = await api.post<TrainingSession>(`${BASE_URL}/sessions`, data);
    return response as unknown as TrainingSession;
  },

  update: async (id: string, data: TrainingSessionUpdate): Promise<TrainingSession> => {
    const response = await api.put<TrainingSession>(`${BASE_URL}/sessions/${id}`, data);
    return response as unknown as TrainingSession;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/sessions/${id}`);
  },

  // Status transitions
  open: async (id: string): Promise<TrainingSession> => {
    const response = await api.post<TrainingSession>(`${BASE_URL}/sessions/${id}/open`);
    return response as unknown as TrainingSession;
  },

  start: async (id: string): Promise<TrainingSession> => {
    const response = await api.post<TrainingSession>(`${BASE_URL}/sessions/${id}/start`);
    return response as unknown as TrainingSession;
  },

  complete: async (id: string): Promise<TrainingSession> => {
    const response = await api.post<TrainingSession>(`${BASE_URL}/sessions/${id}/complete`);
    return response as unknown as TrainingSession;
  },

  cancel: async (id: string, reason?: string): Promise<TrainingSession> => {
    const response = await api.post<TrainingSession>(`${BASE_URL}/sessions/${id}/cancel`, { reason });
    return response as unknown as TrainingSession;
  },

  // Enrollments
  getEnrollments: async (sessionId: string): Promise<Enrollment[]> => {
    const response = await api.get<Enrollment[]>(`${BASE_URL}/sessions/${sessionId}/enrollments`);
    return response as unknown as Enrollment[];
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
    const queryString = params.toString();
    const url = `${BASE_URL}/trainers${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<TrainerListResponse>(url);
    return response as unknown as TrainerListResponse;
  },

  get: async (id: string): Promise<Trainer> => {
    const response = await api.get<Trainer>(`${BASE_URL}/trainers/${id}`);
    return response as unknown as Trainer;
  },

  create: async (data: TrainerCreate): Promise<Trainer> => {
    const response = await api.post<Trainer>(`${BASE_URL}/trainers`, data);
    return response as unknown as Trainer;
  },

  update: async (id: string, data: TrainerUpdate): Promise<Trainer> => {
    const response = await api.put<Trainer>(`${BASE_URL}/trainers/${id}`, data);
    return response as unknown as Trainer;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/trainers/${id}`);
  },

  getSessions: async (trainerId: string): Promise<TrainingSession[]> => {
    const response = await api.get<TrainingSession[]>(`${BASE_URL}/trainers/${trainerId}/sessions`);
    return response as unknown as TrainingSession[];
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
    const queryString = params.toString();
    const url = `${BASE_URL}/enrollments${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<EnrollmentListResponse>(url);
    return response as unknown as EnrollmentListResponse;
  },

  get: async (id: string): Promise<Enrollment> => {
    const response = await api.get<Enrollment>(`${BASE_URL}/enrollments/${id}`);
    return response as unknown as Enrollment;
  },

  enroll: async (data: EnrollmentCreate): Promise<Enrollment> => {
    const response = await api.post<Enrollment>(`${BASE_URL}/enrollments`, data);
    return response as unknown as Enrollment;
  },

  confirm: async (id: string): Promise<Enrollment> => {
    const response = await api.post<Enrollment>(`${BASE_URL}/enrollments/${id}/confirm`);
    return response as unknown as Enrollment;
  },

  cancel: async (id: string): Promise<Enrollment> => {
    const response = await api.post<Enrollment>(`${BASE_URL}/enrollments/${id}/cancel`);
    return response as unknown as Enrollment;
  },

  recordAttendance: async (id: string, date: string, isPresent: boolean): Promise<void> => {
    await api.post(`${BASE_URL}/enrollments/${id}/attendance`, { date, is_present: isPresent });
  },

  complete: async (id: string, score?: number): Promise<Enrollment> => {
    const response = await api.post<Enrollment>(`${BASE_URL}/enrollments/${id}/complete`, { score });
    return response as unknown as Enrollment;
  },

  getMyEnrollments: async (): Promise<Enrollment[]> => {
    const response = await api.get<Enrollment[]>(`${BASE_URL}/enrollments/my`);
    return response as unknown as Enrollment[];
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
    const queryString = params.toString();
    const url = `${BASE_URL}/certificates${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<CertificateListResponse>(url);
    return response as unknown as CertificateListResponse;
  },

  get: async (id: string): Promise<Certificate> => {
    const response = await api.get<Certificate>(`${BASE_URL}/certificates/${id}`);
    return response as unknown as Certificate;
  },

  issue: async (enrollmentId: string): Promise<Certificate> => {
    const response = await api.post<Certificate>(`${BASE_URL}/certificates`, { enrollment_id: enrollmentId });
    return response as unknown as Certificate;
  },

  verify: async (certificateNumber: string): Promise<Certificate> => {
    const response = await api.get<Certificate>(`${BASE_URL}/certificates/verify/${certificateNumber}`);
    return response as unknown as Certificate;
  },

  download: async (id: string): Promise<Blob> => {
    const response = await api.get<Blob>(`${BASE_URL}/certificates/${id}/download`, { responseType: 'blob' });
    return response as unknown as Blob;
  },

  getMyCertificates: async (): Promise<Certificate[]> => {
    const response = await api.get<Certificate[]>(`${BASE_URL}/certificates/my`);
    return response as unknown as Certificate[];
  },
};

// ============================================================================
// E-LEARNING API
// ============================================================================

export const elearningApi = {
  getModules: async (courseId: string): Promise<ELearningModule[]> => {
    const response = await api.get<ELearningModule[]>(`${BASE_URL}/courses/${courseId}/modules`);
    return response as unknown as ELearningModule[];
  },

  getModule: async (moduleId: string): Promise<ELearningModule> => {
    const response = await api.get<ELearningModule>(`${BASE_URL}/modules/${moduleId}`);
    return response as unknown as ELearningModule;
  },

  createModule: async (courseId: string, data: Partial<ELearningModule>): Promise<ELearningModule> => {
    const response = await api.post<ELearningModule>(`${BASE_URL}/courses/${courseId}/modules`, data);
    return response as unknown as ELearningModule;
  },

  updateModule: async (moduleId: string, data: Partial<ELearningModule>): Promise<ELearningModule> => {
    const response = await api.put<ELearningModule>(`${BASE_URL}/modules/${moduleId}`, data);
    return response as unknown as ELearningModule;
  },

  deleteModule: async (moduleId: string): Promise<void> => {
    await api.delete(`${BASE_URL}/modules/${moduleId}`);
  },

  getProgress: async (moduleId: string): Promise<ModuleProgress> => {
    const response = await api.get<ModuleProgress>(`${BASE_URL}/modules/${moduleId}/progress`);
    return response as unknown as ModuleProgress;
  },

  updateProgress: async (moduleId: string, progressPercent: number, timeSpentMinutes: number): Promise<ModuleProgress> => {
    const response = await api.post<ModuleProgress>(`${BASE_URL}/modules/${moduleId}/progress`, {
      progress_percent: progressPercent,
      time_spent_minutes: timeSpentMinutes,
    });
    return response as unknown as ModuleProgress;
  },
};

// ============================================================================
// FEEDBACK API
// ============================================================================

export const feedbackApi = {
  list: async (sessionId: string): Promise<SessionFeedback[]> => {
    const response = await api.get<SessionFeedback[]>(`${BASE_URL}/sessions/${sessionId}/feedback`);
    return response as unknown as SessionFeedback[];
  },

  submit: async (data: FeedbackCreate): Promise<SessionFeedback> => {
    const response = await api.post<SessionFeedback>(`${BASE_URL}/feedback`, data);
    return response as unknown as SessionFeedback;
  },
};

// ============================================================================
// CATEGORY API
// ============================================================================

export const categoryApi = {
  list: async (): Promise<TrainingCategory[]> => {
    const response = await api.get<TrainingCategory[]>(`${BASE_URL}/categories`);
    return response as unknown as TrainingCategory[];
  },

  get: async (id: string): Promise<TrainingCategory> => {
    const response = await api.get<TrainingCategory>(`${BASE_URL}/categories/${id}`);
    return response as unknown as TrainingCategory;
  },

  create: async (data: Partial<TrainingCategory>): Promise<TrainingCategory> => {
    const response = await api.post<TrainingCategory>(`${BASE_URL}/categories`, data);
    return response as unknown as TrainingCategory;
  },

  update: async (id: string, data: Partial<TrainingCategory>): Promise<TrainingCategory> => {
    const response = await api.put<TrainingCategory>(`${BASE_URL}/categories/${id}`, data);
    return response as unknown as TrainingCategory;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${BASE_URL}/categories/${id}`);
  },
};

// ============================================================================
// STATS API
// ============================================================================

export const statsApi = {
  getStats: async (periodStart: string, periodEnd: string): Promise<TrainingStats> => {
    const response = await api.get<TrainingStats>(`${BASE_URL}/stats?period_start=${periodStart}&period_end=${periodEnd}`);
    return response as unknown as TrainingStats;
  },

  getDashboard: async (): Promise<TrainingDashboard> => {
    const response = await api.get<TrainingDashboard>(`${BASE_URL}/dashboard`);
    return response as unknown as TrainingDashboard;
  },
};
