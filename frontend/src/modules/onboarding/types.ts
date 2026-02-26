/**
 * AZALSCORE - Types du Module Onboarding
 * =======================================
 */

// ============================================================================
// TOUR TYPES
// ============================================================================

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  target?: string;
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  action?: () => void;
  video?: string;
  image?: string;
  highlight?: boolean;
  skippable?: boolean;
}

export interface OnboardingTour {
  id: string;
  name: string;
  description: string;
  steps: OnboardingStep[];
  module?: string;
  duration?: string;
  level?: 'debutant' | 'intermediaire' | 'avance';
  requiredTours?: string[];
  badge?: string;
}

// ============================================================================
// PROGRESS TYPES
// ============================================================================

export interface UserProgress {
  userId?: string;
  completedTours: string[];
  completedSteps: Record<string, number[]>;
  currentTour?: string;
  currentStep?: number;
  achievements: string[];
  totalProgress: number;
  lastActivity?: string;
  preferences: UserOnboardingPreferences;
}

export interface UserOnboardingPreferences {
  showTips: boolean;
  showHighlights: boolean;
  autoStartTours: boolean;
  dismissedFeatures: string[];
}

// ============================================================================
// ACHIEVEMENT TYPES
// ============================================================================

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  condition: AchievementCondition;
  reward?: string;
}

export type AchievementCondition =
  | { type: 'complete_tour'; tourId: string }
  | { type: 'complete_tours'; count: number }
  | { type: 'use_feature'; featureId: string; count?: number }
  | { type: 'streak'; days: number };

// ============================================================================
// HELP TYPES
// ============================================================================

export interface HelpArticle {
  id: string;
  title: string;
  summary: string;
  content: string;
  category: string;
  tags: string[];
  module?: string;
  difficulty: 'facile' | 'moyen' | 'avance';
  readTime: string;
  helpful?: number;
  notHelpful?: number;
  relatedArticles?: string[];
  video?: string;
  lastUpdated: string;
}

export interface HelpCategory {
  id: string;
  name: string;
  icon: string;
  description: string;
  articleCount: number;
  order: number;
}

export interface HelpFeedback {
  articleId: string;
  userId: string;
  helpful: boolean;
  comment?: string;
  timestamp: string;
}

// ============================================================================
// TOOLTIP TYPES
// ============================================================================

export type TooltipType = 'info' | 'tip' | 'warning' | 'success';
export type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';

export interface TooltipConfig {
  id: string;
  content: string;
  type: TooltipType;
  position: TooltipPosition;
  target: string;
  showOnce?: boolean;
  delay?: number;
}

// ============================================================================
// FEATURE HIGHLIGHT TYPES
// ============================================================================

export interface FeatureHighlight {
  id: string;
  title: string;
  description: string;
  target: string;
  isNew: boolean;
  validUntil?: string;
  userRoles?: string[];
}

// ============================================================================
// API TYPES
// ============================================================================

export interface SaveProgressRequest {
  progress: Partial<UserProgress>;
}

export interface SaveProgressResponse {
  success: boolean;
  progress: UserProgress;
}

export interface GetProgressResponse {
  progress: UserProgress;
}

export interface SubmitFeedbackRequest {
  articleId: string;
  helpful: boolean;
  comment?: string;
}

export interface SubmitFeedbackResponse {
  success: boolean;
}

// ============================================================================
// EVENTS
// ============================================================================

export type OnboardingEvent =
  | { type: 'TOUR_STARTED'; tourId: string }
  | { type: 'TOUR_COMPLETED'; tourId: string }
  | { type: 'TOUR_SKIPPED'; tourId: string; stepIndex: number }
  | { type: 'STEP_COMPLETED'; tourId: string; stepId: string }
  | { type: 'ACHIEVEMENT_UNLOCKED'; achievementId: string }
  | { type: 'HELP_VIEWED'; articleId: string }
  | { type: 'FEEDBACK_SUBMITTED'; articleId: string; helpful: boolean };

export type OnboardingEventHandler = (event: OnboardingEvent) => void;
