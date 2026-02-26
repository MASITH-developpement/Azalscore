/**
 * AZALSCORE - Système de Gamification
 * ====================================
 * Formation ludique avec points, badges, niveaux et défis.
 *
 * Structure refactorisée depuis le fichier monolithique Gamification.tsx (4,414 lignes)
 * vers une architecture modulaire avec séparation des responsabilités.
 *
 * @module gamification
 */

// ============================================================================
// TYPES
// ============================================================================

export type {
  UserGameProfile,
  Badge,
  BadgeRarity,
  Achievement,
  Challenge,
  ChallengeType,
  ChallengeDifficulty,
  ChallengeTask,
  LeaderboardEntry,
  ExamQuestion,
  LevelExam,
  ExamResult,
  ExamGrade,
  QuestionDifficulty,
  PracticeQuiz,
  PracticeQuizResult,
  PointsAction,
  PointsCategory,
  PointsHistoryEntry,
  LevelDefinition,
  GradeThreshold,
  CelebrationType,
  CelebrationData,
} from './types';

// ============================================================================
// CONSTANTES
// ============================================================================

export {
  LEVELS,
  BADGES,
  DAILY_CHALLENGES,
  GRADE_THRESHOLDS,
  getLevelInfo,
  getBadgeById,
  getGradeFromPercentage,
  getXPToNextLevel,
} from './constants';

// ============================================================================
// DONNÉES
// ============================================================================

export {
  // Examens de niveau
  LEVEL_EXAMS,
  getExamByLevel,
  getAvailableExams,
  canTakeExam,
  // Quiz d'entraînement
  PRACTICE_QUIZZES,
  getQuizById,
  getQuizzesByCategory,
  getQuizCategories,
  getTotalQuestionsCount,
  // Actions de points
  POINTS_ACTIONS,
  getPointsAction,
  getActionsByCategory,
  calculatePoints,
} from './data';

// ============================================================================
// CONTEXT & HOOKS
// ============================================================================

export {
  GamificationProvider,
  useGamification,
  useGamificationOptional,
  useGamificationState,
  type GamificationState,
} from './context';

// ============================================================================
// COMPOSANTS UI
// ============================================================================

export {
  // Composants de base
  XPProgressBar,
  PlayerStatsCard,
  BadgeCollection,
  Leaderboard,
  DailyChallengeCard,
  CelebrationOverlay,
  PointsTable,
} from './components';

export {
  // Composants d'examen
  LevelUpNotification,
  ExamHistory,
  ExamResultsDisplay,
} from './exam';

// ============================================================================
// EXPORT PAR DÉFAUT (compatibilité)
// ============================================================================

import { GamificationProvider, useGamification } from './context';
import { XPProgressBar, PlayerStatsCard, BadgeCollection, Leaderboard, DailyChallengeCard, CelebrationOverlay, PointsTable } from './components';
import { LevelUpNotification, ExamHistory, ExamResultsDisplay } from './exam';
import { BADGES, LEVELS, GRADE_THRESHOLDS } from './constants';
import { LEVEL_EXAMS, PRACTICE_QUIZZES, POINTS_ACTIONS } from './data';

export default {
  // Context & Hooks
  GamificationProvider,
  useGamification,

  // Composants principaux
  XPProgressBar,
  PlayerStatsCard,
  BadgeCollection,
  Leaderboard,
  DailyChallengeCard,
  CelebrationOverlay,
  PointsTable,

  // Système d'examen
  LevelUpNotification,
  ExamHistory,
  ExamResultsDisplay,

  // Constantes
  BADGES,
  LEVELS,
  GRADE_THRESHOLDS,
  LEVEL_EXAMS,
  PRACTICE_QUIZZES,
  POINTS_ACTIONS,
};
