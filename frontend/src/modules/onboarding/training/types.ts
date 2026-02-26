/**
 * AZALSCORE - Types pour le Systeme de Formation Modulaire
 * =========================================================
 * Types standards que chaque module doit implementer pour sa formation
 */

import { SupportedLanguage } from '../i18n';

// ============================================================================
// TYPES DE BASE
// ============================================================================

/**
 * Niveau de difficulte
 */
export type Difficulty = 'facile' | 'moyen' | 'difficile';

/**
 * Type de contenu de formation
 */
export type ContentType = 'lesson' | 'quiz' | 'exercise' | 'video' | 'slide';

// ============================================================================
// LECONS
// ============================================================================

/**
 * Une lecon de formation
 */
export interface ModuleLesson {
  id: string;
  moduleId: string;
  title: string;
  description: string;
  duration: number; // en minutes
  difficulty: Difficulty;
  order: number;
  content: LessonContent;
  prerequisites?: string[]; // IDs des lecons prerequises
  tags?: string[];
}

/**
 * Contenu d'une lecon
 */
export interface LessonContent {
  type: 'slides' | 'interactive' | 'video' | 'text';
  slides?: LessonSlide[];
  videoUrl?: string;
  textContent?: string;
  interactiveSteps?: InteractiveStep[];
}

/**
 * Slide de presentation
 */
export interface LessonSlide {
  id: string;
  title: string;
  content: string; // Markdown
  image?: string;
  notes?: string;
  animation?: 'fade' | 'slide' | 'zoom';
}

/**
 * Etape interactive
 */
export interface InteractiveStep {
  id: string;
  instruction: string;
  targetSelector?: string; // Element a cibler dans l'UI
  action?: 'click' | 'input' | 'select' | 'drag';
  validation?: string; // Expression de validation
  hint?: string;
}

// ============================================================================
// QUIZ ET QUESTIONS
// ============================================================================

/**
 * Question de quiz/examen
 */
export interface ModuleQuestion {
  id: string;
  moduleId: string;
  question: string;
  type: 'single' | 'multiple' | 'truefalse' | 'ordering' | 'matching';
  options: QuestionOption[];
  correctAnswers: number[]; // Index des bonnes reponses
  explanation: string;
  points: number;
  difficulty: Difficulty;
  tags?: string[];
  relatedLessonId?: string;
}

/**
 * Option de reponse
 */
export interface QuestionOption {
  id: number;
  text: string;
  image?: string;
}

/**
 * Quiz de module
 */
export interface ModuleQuiz {
  id: string;
  moduleId: string;
  title: string;
  description: string;
  duration: number; // en minutes
  passingScore: number; // pourcentage
  questions: ModuleQuestion[];
  difficulty: Difficulty;
  xpReward: number;
  badgeReward?: string;
  order: number;
}

// ============================================================================
// EXERCICES PRATIQUES
// ============================================================================

/**
 * Exercice pratique
 */
export interface ModuleExercise {
  id: string;
  moduleId: string;
  title: string;
  description: string;
  objective: string;
  duration: number;
  difficulty: Difficulty;
  steps: ExerciseStep[];
  validation: ExerciseValidation;
  xpReward: number;
  order: number;
}

/**
 * Etape d'exercice
 */
export interface ExerciseStep {
  id: string;
  instruction: string;
  hint?: string;
  screenshot?: string;
}

/**
 * Validation d'exercice
 */
export interface ExerciseValidation {
  type: 'manual' | 'automatic' | 'checklist';
  criteria?: string[];
  checkFunction?: string; // Nom de la fonction de validation
}

// ============================================================================
// CONTENU DE FORMATION D'UN MODULE
// ============================================================================

/**
 * Structure complete de formation d'un module
 * Chaque module AZALSCORE doit exporter un objet de ce type
 */
export interface ModuleTrainingContent {
  moduleId: string;
  moduleName: string;
  moduleIcon: string;
  moduleColor: string;

  // Metadonnees
  version: string;
  lastUpdated: string;
  estimatedDuration: number; // Total en minutes

  // Contenu
  lessons: ModuleLesson[];
  quizzes: ModuleQuiz[];
  exercises: ModuleExercise[];

  // Examen final du module
  finalExam?: ModuleQuiz;

  // Ressources additionnelles
  resources?: {
    title: string;
    type: 'pdf' | 'video' | 'link';
    url: string;
  }[];

  // Traductions disponibles
  availableLanguages: SupportedLanguage[];
}

/**
 * Fonction de chargement des traductions d'un module
 */
export type ModuleTrainingLoader = (language: SupportedLanguage) => Promise<ModuleTrainingContent>;

// ============================================================================
// PROGRESSION UTILISATEUR
// ============================================================================

/**
 * Progression d'un utilisateur sur un module
 */
export interface ModuleProgress {
  moduleId: string;

  // Lecons
  completedLessons: string[];
  currentLessonId?: string;
  currentSlideIndex?: number;

  // Quiz
  completedQuizzes: string[];
  quizScores: Record<string, number>;

  // Exercices
  completedExercises: string[];

  // Examen final
  finalExamPassed: boolean;
  finalExamScore?: number;
  finalExamAttempts: number;

  // Stats
  totalTimeSpent: number; // en minutes
  lastAccessedAt: string;
  startedAt: string;
  completedAt?: string;
}

/**
 * Progression globale de l'utilisateur
 */
export interface UserTrainingProgress {
  userId: string;

  // Progression par module
  moduleProgress: Record<string, ModuleProgress>;

  // Stats globales
  totalXP: number;
  level: number;
  badges: string[];
  streak: number;
  lastTrainingDate: string;

  // Examen global
  globalExamPassed: boolean;
  globalExamScore?: number;
  certificationDate?: string;
}

// ============================================================================
// SYNTHESE
// ============================================================================

/**
 * Element de synthese
 */
export interface SynthesisItem {
  moduleId: string;
  moduleName: string;
  keyPoints: string[];
  shortcuts: { key: string; action: string }[];
  tips: string[];
  warnings: string[];
}

/**
 * Synthese globale
 */
export interface GlobalSynthesis {
  generatedAt: string;
  modules: SynthesisItem[];
  totalKeyPoints: number;
  totalShortcuts: number;
}

// ============================================================================
// REGISTRE DES MODULES
// ============================================================================

/**
 * Registre central des modules de formation
 */
export interface TrainingModuleRegistry {
  modules: Record<string, {
    loader: ModuleTrainingLoader;
    requiredPermissions?: string[];
  }>;
}

// ============================================================================
// EXAMEN FINAL GLOBAL
// ============================================================================

/**
 * Configuration de l'examen final global
 */
export interface GlobalExamConfig {
  title: string;
  description: string;
  duration: number;
  passingScore: number;
  questionsPerModule: number; // Nombre de questions a piocher par module
  totalQuestions: number;
  xpReward: number;
  certificateBadge: string;
}

/**
 * Resultat d'examen
 */
export interface ExamResult {
  examId: string;
  examType: 'module' | 'global';
  userId: string;
  moduleId?: string;

  // Resultats
  score: number;
  percentage: number;
  passed: boolean;
  grade: string;

  // Details
  answers: {
    questionId: string;
    selectedAnswers: number[];
    correct: boolean;
    points: number;
  }[];

  // Temps
  startedAt: string;
  completedAt: string;
  duration: number;

  // Recompenses
  xpEarned: number;
  badgeEarned?: string;
}
