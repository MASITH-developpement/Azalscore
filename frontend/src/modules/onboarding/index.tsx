/**
 * AZALSCORE - Module Onboarding
 * ==============================
 * Systeme de formation integre au logiciel.
 * Comprend: Wizard d'accueil, Tours guides, Aide contextuelle.
 */

// ============================================================================
// TYPES
// ============================================================================

export * from './types';

// ============================================================================
// CONSTANTS
// ============================================================================

export { ONBOARDING_TOURS } from './constants';

// ============================================================================
// CONTEXT
// ============================================================================

export { OnboardingProvider, useOnboarding } from './context';

// ============================================================================
// CORE COMPONENTS
// ============================================================================

export {
  TourOverlay,
  TrainingCenter,
  ContextualHelp,
  HelpWidget,
} from './components';

// ============================================================================
// GAMIFICATION
// ============================================================================

export {
  useGamification,
  GamificationProvider,
  XPProgressBar,
  PlayerStatsCard,
  DailyChallengeCard,
  BadgeCollection,
  Leaderboard,
  CelebrationOverlay,
  GamificationDashboard,
  LevelExamComponent,
  ExamResultsDisplay,
  ExamHistory,
  LevelUpNotification,
  PointsTable,
  PracticeQuizCard,
  PracticeQuizPlayer,
  PracticeQuizLibrary,
} from './components/Gamification';

// ============================================================================
// JEUX INTERACTIFS
// ============================================================================

export {
  AnimatedQuiz,
  DragDropCategory,
  MatchingGame,
  InteractiveSimulation,
  MemoryGame,
} from './components/InteractiveGames';

// ============================================================================
// MICRO-LEARNING
// ============================================================================

export {
  MicroLessonCard,
  MicroLessonPlayer,
  MicroLearningLibrary,
} from './components/MicroLearning';

// ============================================================================
// TOOLTIPS & AIDE
// ============================================================================

export {
  Tooltip,
  FeatureHighlight,
  FieldHint,
  InlineHelp,
  StepIndicator,
  AchievementBadge,
} from './components/Tooltips';

// ============================================================================
// BASE DE CONNAISSANCES
// ============================================================================

export { KnowledgeBase } from './components/KnowledgeBase';

// ============================================================================
// TRAINING HUB
// ============================================================================

export { TrainingHub } from './components/TrainingHub';

// ============================================================================
// INTERNATIONALISATION (I18N)
// ============================================================================

export {
  I18nProvider,
  useI18n,
  LanguageSelector,
  translations,
  languageNames,
  languageFlags,
  isRTL,
  FR,
} from './i18n';
export type { SupportedLanguage, TranslationStrings, I18nContextType } from './i18n';

// Questions d'examens multilingues
export {
  getLevelExams,
  getPracticeQuizzes,
  getExamByLevel,
  getQuizById,
} from './i18n/examQuestions';

// ============================================================================
// SYSTEME DE FORMATION MODULAIRE
// ============================================================================

export {
  // Types
  type ModuleTrainingContent,
  type ModuleLesson,
  type ModuleQuiz,
  type ModuleQuestion,
  type ModuleExercise,
  type ModuleProgress,
  type UserTrainingProgress,
  type GlobalSynthesis,
  type ExamResult,
  // Registre
  registerTrainingModule,
  getRegisteredModules,
  isModuleRegistered,
  loadModuleTraining,
  loadUserTrainings,
  getAccessibleModules,
  generateGlobalSynthesis,
  calculateTrainingStats,
  generateGlobalExam,
  // Hooks
  useTraining,
  useModuleTraining,
  useLessonPlayer,
  useQuizPlayer,
} from './training';

// ============================================================================
// DEFAULT EXPORT
// ============================================================================

export default {
  // Provider est exporte comme default pour faciliter l'import
  OnboardingProvider: () => import('./context').then(m => m.OnboardingProvider),
};
