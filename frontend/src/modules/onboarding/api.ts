/**
 * AZALSCORE - Onboarding API
 * ===========================
 * Complete typed API client for User Onboarding & Help module.
 * Covers: Tours, Progress, Achievements, Help Articles, Feedback
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/core/api-client';

// ============================================================================
// QUERY KEYS
// ============================================================================

export const onboardingKeys = {
  all: ['onboarding'] as const,
  progress: () => [...onboardingKeys.all, 'progress'] as const,
  tours: () => [...onboardingKeys.all, 'tours'] as const,
  tour: (id: string) => [...onboardingKeys.tours(), id] as const,
  achievements: () => [...onboardingKeys.all, 'achievements'] as const,
  help: () => [...onboardingKeys.all, 'help'] as const,
  helpCategories: () => [...onboardingKeys.help(), 'categories'] as const,
  helpArticles: (category?: string) => [...onboardingKeys.help(), 'articles', category] as const,
  helpArticle: (id: string) => [...onboardingKeys.help(), 'article', id] as const,
  features: () => [...onboardingKeys.all, 'features'] as const,
  tips: () => [...onboardingKeys.all, 'tips'] as const,
};

// ============================================================================
// TYPES - ENTITIES
// ============================================================================

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  target?: string | null;
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  action?: string | null;
  video?: string | null;
  image?: string | null;
  highlight?: boolean;
  skippable?: boolean;
}

export interface OnboardingTour {
  id: string;
  name: string;
  description: string;
  steps: OnboardingStep[];
  module?: string | null;
  duration?: string | null;
  level?: 'debutant' | 'intermediaire' | 'avance';
  required_tours?: string[] | null;
  badge?: string | null;
  is_active: boolean;
  sort_order: number;
}

export interface UserProgress {
  user_id?: string | null;
  completed_tours: string[];
  completed_steps: Record<string, number[]>;
  current_tour?: string | null;
  current_step?: number | null;
  achievements: string[];
  total_progress: number;
  last_activity?: string | null;
  preferences: UserOnboardingPreferences;
}

export interface UserOnboardingPreferences {
  show_tips: boolean;
  show_highlights: boolean;
  auto_start_tours: boolean;
  dismissed_features: string[];
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  condition_type: string;
  condition_value: string | number;
  reward?: string | null;
  is_unlocked: boolean;
  unlocked_at?: string | null;
}

export interface HelpCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
  article_count: number;
  order: number;
}

export interface HelpArticle {
  id: string;
  title: string;
  summary: string;
  content: string;
  category: string;
  tags: string[];
  module?: string | null;
  difficulty: 'facile' | 'moyen' | 'avance';
  read_time: string;
  helpful?: number | null;
  not_helpful?: number | null;
  related_articles?: string[] | null;
  video?: string | null;
  last_updated: string;
}

export interface HelpArticleListItem {
  id: string;
  title: string;
  summary: string;
  category: string;
  tags: string[];
  difficulty: 'facile' | 'moyen' | 'avance';
  read_time: string;
  last_updated: string;
}

export interface FeatureHighlight {
  id: string;
  title: string;
  description: string;
  target: string;
  is_new: boolean;
  valid_until?: string | null;
  user_roles?: string[] | null;
  is_dismissed: boolean;
}

export interface Tooltip {
  id: string;
  content: string;
  type: 'info' | 'tip' | 'warning' | 'success';
  position: 'top' | 'bottom' | 'left' | 'right';
  target: string;
  show_once?: boolean;
  delay?: number;
}

// ============================================================================
// TYPES - CREATE/UPDATE
// ============================================================================

export interface SaveProgressRequest {
  completed_tours?: string[];
  completed_steps?: Record<string, number[]>;
  current_tour?: string;
  current_step?: number;
  achievements?: string[];
}

export interface UpdatePreferencesRequest {
  show_tips?: boolean;
  show_highlights?: boolean;
  auto_start_tours?: boolean;
  dismissed_features?: string[];
}

export interface SubmitFeedbackRequest {
  article_id: string;
  helpful: boolean;
  comment?: string;
}

// ============================================================================
// HOOKS - PROGRESS
// ============================================================================

export function useOnboardingProgress() {
  return useQuery({
    queryKey: onboardingKeys.progress(),
    queryFn: async () => {
      const response = await api.get<UserProgress>('/onboarding/progress');
      return response;
    },
  });
}

export function useSaveProgress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SaveProgressRequest) => {
      return api.put<UserProgress>('/onboarding/progress', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.progress() });
      queryClient.invalidateQueries({ queryKey: onboardingKeys.achievements() });
    },
  });
}

export function useResetProgress() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      return api.post<UserProgress>('/onboarding/progress/reset');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.progress() });
      queryClient.invalidateQueries({ queryKey: onboardingKeys.achievements() });
    },
  });
}

// ============================================================================
// HOOKS - TOURS
// ============================================================================

export function useOnboardingTours(filters?: {
  module?: string;
  level?: 'debutant' | 'intermediaire' | 'avance';
}) {
  return useQuery({
    queryKey: [...onboardingKeys.tours(), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.module) params.append('module', filters.module);
      if (filters?.level) params.append('level', filters.level);
      const queryString = params.toString();
      const response = await api.get<{ items: OnboardingTour[] }>(
        `/onboarding/tours${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useOnboardingTour(id: string) {
  return useQuery({
    queryKey: onboardingKeys.tour(id),
    queryFn: async () => {
      const response = await api.get<OnboardingTour>(`/onboarding/tours/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useStartTour() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tourId: string) => {
      return api.post<{ progress: UserProgress }>(`/onboarding/tours/${tourId}/start`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.progress() });
    },
  });
}

export function useCompleteTourStep() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ tourId, stepIndex }: { tourId: string; stepIndex: number }) => {
      return api.post<{ progress: UserProgress }>(
        `/onboarding/tours/${tourId}/steps/${stepIndex}/complete`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.progress() });
    },
  });
}

export function useCompleteTour() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tourId: string) => {
      return api.post<{ progress: UserProgress; achievement?: Achievement }>(
        `/onboarding/tours/${tourId}/complete`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.progress() });
      queryClient.invalidateQueries({ queryKey: onboardingKeys.achievements() });
    },
  });
}

export function useSkipTour() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ tourId, stepIndex }: { tourId: string; stepIndex: number }) => {
      return api.post<{ progress: UserProgress }>(
        `/onboarding/tours/${tourId}/skip`,
        { step_index: stepIndex }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.progress() });
    },
  });
}

// ============================================================================
// HOOKS - ACHIEVEMENTS
// ============================================================================

export function useAchievements() {
  return useQuery({
    queryKey: onboardingKeys.achievements(),
    queryFn: async () => {
      const response = await api.get<{ items: Achievement[]; unlocked: number; total: number }>(
        '/onboarding/achievements'
      );
      return response;
    },
  });
}

export function useClaimAchievementReward() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (achievementId: string) => {
      return api.post<{ success: boolean; reward: string }>(
        `/onboarding/achievements/${achievementId}/claim`
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.achievements() });
    },
  });
}

// ============================================================================
// HOOKS - PREFERENCES
// ============================================================================

export function useOnboardingPreferences() {
  return useQuery({
    queryKey: [...onboardingKeys.progress(), 'preferences'],
    queryFn: async () => {
      const response = await api.get<UserOnboardingPreferences>('/onboarding/preferences');
      return response;
    },
  });
}

export function useUpdateOnboardingPreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: UpdatePreferencesRequest) => {
      return api.put<UserOnboardingPreferences>('/onboarding/preferences', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.progress() });
    },
  });
}

// ============================================================================
// HOOKS - HELP
// ============================================================================

export function useHelpCategories() {
  return useQuery({
    queryKey: onboardingKeys.helpCategories(),
    queryFn: async () => {
      const response = await api.get<{ items: HelpCategory[] }>('/onboarding/help/categories');
      return response;
    },
  });
}

export function useHelpArticles(filters?: {
  category?: string;
  difficulty?: 'facile' | 'moyen' | 'avance';
  module?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: [...onboardingKeys.helpArticles(filters?.category), filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.category) params.append('category', filters.category);
      if (filters?.difficulty) params.append('difficulty', filters.difficulty);
      if (filters?.module) params.append('module', filters.module);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.page) params.append('page', String(filters.page));
      if (filters?.per_page) params.append('per_page', String(filters.per_page));
      const queryString = params.toString();
      const response = await api.get<{ items: HelpArticleListItem[]; total: number }>(
        `/onboarding/help/articles${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
  });
}

export function useHelpArticle(id: string) {
  return useQuery({
    queryKey: onboardingKeys.helpArticle(id),
    queryFn: async () => {
      const response = await api.get<HelpArticle>(`/onboarding/help/articles/${id}`);
      return response;
    },
    enabled: !!id,
  });
}

export function useSearchHelp(query: string) {
  return useQuery({
    queryKey: [...onboardingKeys.help(), 'search', query],
    queryFn: async () => {
      const response = await api.get<{ items: HelpArticleListItem[] }>(
        `/onboarding/help/search?q=${encodeURIComponent(query)}`
      );
      return response;
    },
    enabled: query.length >= 2,
  });
}

export function useSubmitHelpFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: SubmitFeedbackRequest) => {
      return api.post<{ success: boolean }>('/onboarding/help/feedback', data);
    },
    onSuccess: (_, { article_id }) => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.helpArticle(article_id) });
    },
  });
}

// ============================================================================
// HOOKS - FEATURE HIGHLIGHTS
// ============================================================================

export function useFeatureHighlights() {
  return useQuery({
    queryKey: onboardingKeys.features(),
    queryFn: async () => {
      const response = await api.get<{ items: FeatureHighlight[] }>('/onboarding/features');
      return response;
    },
  });
}

export function useDismissFeature() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (featureId: string) => {
      return api.post(`/onboarding/features/${featureId}/dismiss`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.features() });
      queryClient.invalidateQueries({ queryKey: onboardingKeys.progress() });
    },
  });
}

// ============================================================================
// HOOKS - TOOLTIPS
// ============================================================================

export function useTooltips(target?: string) {
  return useQuery({
    queryKey: [...onboardingKeys.tips(), target],
    queryFn: async () => {
      const url = target
        ? `/onboarding/tooltips?target=${encodeURIComponent(target)}`
        : '/onboarding/tooltips';
      const response = await api.get<{ items: Tooltip[] }>(url);
      return response;
    },
  });
}

export function useDismissTooltip() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (tooltipId: string) => {
      return api.post(`/onboarding/tooltips/${tooltipId}/dismiss`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: onboardingKeys.tips() });
    },
  });
}

// ============================================================================
// HOOKS - CONTEXTUAL HELP
// ============================================================================

export function useContextualHelp(context: { module?: string; page?: string; element?: string }) {
  return useQuery({
    queryKey: [...onboardingKeys.help(), 'contextual', context],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (context.module) params.append('module', context.module);
      if (context.page) params.append('page', context.page);
      if (context.element) params.append('element', context.element);
      const queryString = params.toString();
      const response = await api.get<{
        articles: HelpArticleListItem[];
        tooltips: Tooltip[];
        tours: OnboardingTour[];
      }>(`/onboarding/help/contextual${queryString ? `?${queryString}` : ''}`);
      return response;
    },
    enabled: !!(context.module || context.page || context.element),
  });
}

// ============================================================================
// HOOKS - EVENTS TRACKING
// ============================================================================

export function useTrackOnboardingEvent() {
  return useMutation({
    mutationFn: async (event: {
      type: string;
      tour_id?: string;
      step_id?: string;
      article_id?: string;
      achievement_id?: string;
      metadata?: Record<string, unknown>;
    }) => {
      return api.post('/onboarding/events', event);
    },
  });
}
