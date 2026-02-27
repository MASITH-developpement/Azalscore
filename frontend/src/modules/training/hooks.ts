/**
 * AZALSCORE Module - Training Hooks
 * React Query hooks pour le module de formation
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  courseApi, sessionApi, trainerApi, enrollmentApi,
  certificateApi, elearningApi, feedbackApi, categoryApi, statsApi,
} from './api';
import type {
  TrainingCourseCreate, TrainingCourseUpdate, CourseFilters,
  TrainingSessionCreate, TrainingSessionUpdate, SessionFilters,
  TrainerCreate, TrainerUpdate,
  EnrollmentCreate, EnrollmentFilters,
  FeedbackCreate,
} from './types';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const trainingKeys = {
  all: ['training'] as const,

  // Courses
  courses: () => [...trainingKeys.all, 'courses'] as const,
  courseList: (filters?: CourseFilters) => [...trainingKeys.courses(), 'list', filters] as const,
  courseDetail: (id: string) => [...trainingKeys.courses(), 'detail', id] as const,

  // Sessions
  sessions: () => [...trainingKeys.all, 'sessions'] as const,
  sessionList: (filters?: SessionFilters) => [...trainingKeys.sessions(), 'list', filters] as const,
  sessionDetail: (id: string) => [...trainingKeys.sessions(), 'detail', id] as const,
  sessionEnrollments: (id: string) => [...trainingKeys.sessions(), 'enrollments', id] as const,

  // Trainers
  trainers: () => [...trainingKeys.all, 'trainers'] as const,
  trainerDetail: (id: string) => [...trainingKeys.trainers(), 'detail', id] as const,

  // Enrollments
  enrollments: () => [...trainingKeys.all, 'enrollments'] as const,
  enrollmentList: (filters?: EnrollmentFilters) => [...trainingKeys.enrollments(), 'list', filters] as const,
  myEnrollments: () => [...trainingKeys.enrollments(), 'my'] as const,

  // Certificates
  certificates: () => [...trainingKeys.all, 'certificates'] as const,
  myCertificates: () => [...trainingKeys.certificates(), 'my'] as const,

  // E-Learning
  modules: (courseId: string) => [...trainingKeys.all, 'modules', courseId] as const,
  moduleProgress: (moduleId: string) => [...trainingKeys.all, 'progress', moduleId] as const,

  // Categories
  categories: () => [...trainingKeys.all, 'categories'] as const,

  // Stats
  stats: () => [...trainingKeys.all, 'stats'] as const,
  dashboard: () => [...trainingKeys.all, 'dashboard'] as const,
};

// ============================================================================
// COURSE HOOKS
// ============================================================================

export function useCourseList(filters?: CourseFilters) {
  return useQuery({
    queryKey: trainingKeys.courseList(filters),
    queryFn: () => courseApi.list(filters),
  });
}

export function useCourse(id: string) {
  return useQuery({
    queryKey: trainingKeys.courseDetail(id),
    queryFn: () => courseApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TrainingCourseCreate) => courseApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.courses() });
    },
  });
}

export function useUpdateCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TrainingCourseUpdate }) => courseApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.courseDetail(id) });
      queryClient.invalidateQueries({ queryKey: trainingKeys.courses() });
    },
  });
}

export function useDeleteCourse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => courseApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.courses() });
    },
  });
}

// ============================================================================
// SESSION HOOKS
// ============================================================================

export function useSessionList(filters?: SessionFilters) {
  return useQuery({
    queryKey: trainingKeys.sessionList(filters),
    queryFn: () => sessionApi.list(filters),
  });
}

export function useSession(id: string) {
  return useQuery({
    queryKey: trainingKeys.sessionDetail(id),
    queryFn: () => sessionApi.get(id),
    enabled: !!id,
  });
}

export function useSessionEnrollments(sessionId: string) {
  return useQuery({
    queryKey: trainingKeys.sessionEnrollments(sessionId),
    queryFn: () => sessionApi.getEnrollments(sessionId),
    enabled: !!sessionId,
  });
}

export function useCreateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TrainingSessionCreate) => sessionApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessions() });
    },
  });
}

export function useUpdateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TrainingSessionUpdate }) => sessionApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessionDetail(id) });
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessions() });
    },
  });
}

export function useOpenSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => sessionApi.open(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessionDetail(id) });
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessions() });
    },
  });
}

export function useStartSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => sessionApi.start(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessionDetail(id) });
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessions() });
    },
  });
}

export function useCompleteSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => sessionApi.complete(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessionDetail(id) });
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessions() });
    },
  });
}

export function useCancelSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => sessionApi.cancel(id, reason),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessionDetail(id) });
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessions() });
    },
  });
}

// ============================================================================
// TRAINER HOOKS
// ============================================================================

export function useTrainerList(filters?: { specialization?: string; is_internal?: boolean; is_active?: boolean }) {
  return useQuery({
    queryKey: trainingKeys.trainers(),
    queryFn: () => trainerApi.list(filters),
  });
}

export function useTrainer(id: string) {
  return useQuery({
    queryKey: trainingKeys.trainerDetail(id),
    queryFn: () => trainerApi.get(id),
    enabled: !!id,
  });
}

export function useCreateTrainer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TrainerCreate) => trainerApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.trainers() });
    },
  });
}

export function useUpdateTrainer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TrainerUpdate }) => trainerApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.trainerDetail(id) });
      queryClient.invalidateQueries({ queryKey: trainingKeys.trainers() });
    },
  });
}

// ============================================================================
// ENROLLMENT HOOKS
// ============================================================================

export function useEnrollmentList(filters?: EnrollmentFilters) {
  return useQuery({
    queryKey: trainingKeys.enrollmentList(filters),
    queryFn: () => enrollmentApi.list(filters),
  });
}

export function useMyEnrollments() {
  return useQuery({
    queryKey: trainingKeys.myEnrollments(),
    queryFn: () => enrollmentApi.getMyEnrollments(),
  });
}

export function useEnroll() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EnrollmentCreate) => enrollmentApi.enroll(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.enrollments() });
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessions() });
    },
  });
}

export function useConfirmEnrollment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => enrollmentApi.confirm(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.enrollments() });
    },
  });
}

export function useCancelEnrollment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => enrollmentApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.enrollments() });
      queryClient.invalidateQueries({ queryKey: trainingKeys.sessions() });
    },
  });
}

export function useRecordAttendance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, date, isPresent }: { id: string; date: string; isPresent: boolean }) =>
      enrollmentApi.recordAttendance(id, date, isPresent),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.enrollments() });
    },
  });
}

export function useCompleteEnrollment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, score }: { id: string; score?: number }) => enrollmentApi.complete(id, score),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.enrollments() });
      queryClient.invalidateQueries({ queryKey: trainingKeys.stats() });
    },
  });
}

// ============================================================================
// CERTIFICATE HOOKS
// ============================================================================

export function useCertificateList(filters?: { participant_id?: string; course_id?: string; status?: string }) {
  return useQuery({
    queryKey: trainingKeys.certificates(),
    queryFn: () => certificateApi.list(filters),
  });
}

export function useMyCertificates() {
  return useQuery({
    queryKey: trainingKeys.myCertificates(),
    queryFn: () => certificateApi.getMyCertificates(),
  });
}

export function useIssueCertificate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (enrollmentId: string) => certificateApi.issue(enrollmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.certificates() });
    },
  });
}

export function useVerifyCertificate() {
  return useMutation({
    mutationFn: (certificateNumber: string) => certificateApi.verify(certificateNumber),
  });
}

// ============================================================================
// E-LEARNING HOOKS
// ============================================================================

export function useELearningModules(courseId: string) {
  return useQuery({
    queryKey: trainingKeys.modules(courseId),
    queryFn: () => elearningApi.getModules(courseId),
    enabled: !!courseId,
  });
}

export function useModuleProgress(moduleId: string) {
  return useQuery({
    queryKey: trainingKeys.moduleProgress(moduleId),
    queryFn: () => elearningApi.getProgress(moduleId),
    enabled: !!moduleId,
  });
}

export function useUpdateModuleProgress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ moduleId, progressPercent, timeSpentMinutes }: { moduleId: string; progressPercent: number; timeSpentMinutes: number }) =>
      elearningApi.updateProgress(moduleId, progressPercent, timeSpentMinutes),
    onSuccess: (_, { moduleId }) => {
      queryClient.invalidateQueries({ queryKey: trainingKeys.moduleProgress(moduleId) });
    },
  });
}

// ============================================================================
// FEEDBACK HOOKS
// ============================================================================

export function useSessionFeedback(sessionId: string) {
  return useQuery({
    queryKey: ['feedback', sessionId],
    queryFn: () => feedbackApi.list(sessionId),
    enabled: !!sessionId,
  });
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: FeedbackCreate) => feedbackApi.submit(data),
    onSuccess: (_, data) => {
      queryClient.invalidateQueries({ queryKey: ['feedback', data.session_id] });
    },
  });
}

// ============================================================================
// CATEGORY HOOKS
// ============================================================================

export function useCategories() {
  return useQuery({
    queryKey: trainingKeys.categories(),
    queryFn: () => categoryApi.list(),
  });
}

// ============================================================================
// STATS HOOKS
// ============================================================================

export function useTrainingStats(periodStart: string, periodEnd: string) {
  return useQuery({
    queryKey: trainingKeys.stats(),
    queryFn: () => statsApi.getStats(periodStart, periodEnd),
    enabled: !!periodStart && !!periodEnd,
  });
}

export function useTrainingDashboard() {
  return useQuery({
    queryKey: trainingKeys.dashboard(),
    queryFn: () => statsApi.getDashboard(),
  });
}
