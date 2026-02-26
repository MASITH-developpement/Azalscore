/**
 * AZALSCORE - Hooks pour le Systeme de Formation
 * ===============================================
 * Hooks React pour gerer la formation utilisateur
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useI18n } from '../i18n';
import {
  ModuleTrainingContent,
  ModuleProgress,
  UserTrainingProgress,
  ModuleLesson,
  ModuleQuiz,
  ModuleQuestion,
  GlobalSynthesis,
  ExamResult,
  LessonSlide,
} from './types';
import {
  loadUserTrainings,
  loadModuleTraining,
  generateGlobalSynthesis,
  calculateTrainingStats,
  generateGlobalExam,
  getAccessibleModules,
} from './registry';

// ============================================================================
// HOOK PRINCIPAL - useTraining
// ============================================================================

interface UseTrainingOptions {
  userPermissions: string[];
  userId: string;
  autoLoad?: boolean;
}

interface UseTrainingReturn {
  // Etat
  isLoading: boolean;
  error: string | null;
  trainings: Map<string, ModuleTrainingContent>;

  // Progression
  progress: UserTrainingProgress;
  updateProgress: (moduleId: string, updates: Partial<ModuleProgress>) => void;
  saveProgress: () => Promise<void>;

  // Stats
  stats: ReturnType<typeof calculateTrainingStats>;

  // Synthese
  synthesis: GlobalSynthesis | null;
  generateSynthesis: () => void;

  // Navigation
  currentModule: string | null;
  setCurrentModule: (moduleId: string | null) => void;
  currentLesson: ModuleLesson | null;
  setCurrentLesson: (lessonId: string | null) => void;

  // Actions
  completeLesson: (moduleId: string, lessonId: string) => void;
  completeQuiz: (moduleId: string, quizId: string, score: number) => void;
  completeExercise: (moduleId: string, exerciseId: string) => void;

  // Examen
  startGlobalExam: () => { questions: any[]; duration: number } | null;
  submitExamResult: (result: ExamResult) => void;

  // Utilitaires
  reload: () => Promise<void>;
  getModuleProgress: (moduleId: string) => number;
  isModuleCompleted: (moduleId: string) => boolean;
}

export function useTraining(options: UseTrainingOptions): UseTrainingReturn {
  const { userPermissions, userId, autoLoad = true } = options;
  const { language } = useI18n();

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trainings, setTrainings] = useState<Map<string, ModuleTrainingContent>>(new Map());
  const [synthesis, setSynthesis] = useState<GlobalSynthesis | null>(null);
  const [currentModule, setCurrentModule] = useState<string | null>(null);
  const [currentLessonId, setCurrentLessonId] = useState<string | null>(null);

  // Progression utilisateur
  const [progress, setProgress] = useState<UserTrainingProgress>(() => {
    // Charger depuis localStorage
    const saved = localStorage.getItem(`azalscore_training_progress_${userId}`);
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        // Ignore
      }
    }
    return {
      userId,
      moduleProgress: {},
      totalXP: 0,
      level: 1,
      badges: [],
      streak: 0,
      lastTrainingDate: '',
      globalExamPassed: false,
    };
  });

  // Charger les formations
  const loadTrainings = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const loaded = await loadUserTrainings(userPermissions, language);
      setTrainings(loaded);
    } catch (err) {
      setError('Erreur lors du chargement des formations');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [userPermissions, language]);

  // Charger au montage
  useEffect(() => {
    if (autoLoad) {
      loadTrainings();
    }
  }, [autoLoad, loadTrainings]);

  // Sauvegarder la progression
  const saveProgress = useCallback(async () => {
    localStorage.setItem(
      `azalscore_training_progress_${userId}`,
      JSON.stringify(progress)
    );
    // TODO: Envoyer au serveur aussi
  }, [userId, progress]);

  // Sauvegarder automatiquement quand la progression change
  useEffect(() => {
    saveProgress();
  }, [progress, saveProgress]);

  // Mettre a jour la progression d'un module
  const updateProgress = useCallback((moduleId: string, updates: Partial<ModuleProgress>) => {
    setProgress(prev => ({
      ...prev,
      moduleProgress: {
        ...prev.moduleProgress,
        [moduleId]: {
          ...prev.moduleProgress[moduleId],
          ...updates,
          moduleId,
        },
      },
      lastTrainingDate: new Date().toISOString().split('T')[0],
    }));
  }, []);

  // Completer une lecon
  const completeLesson = useCallback((moduleId: string, lessonId: string) => {
    const currentProgress = progress.moduleProgress[moduleId] || {
      moduleId,
      completedLessons: [],
      completedQuizzes: [],
      quizScores: {},
      completedExercises: [],
      finalExamPassed: false,
      finalExamAttempts: 0,
      totalTimeSpent: 0,
      lastAccessedAt: new Date().toISOString(),
      startedAt: new Date().toISOString(),
    };

    if (!currentProgress.completedLessons.includes(lessonId)) {
      updateProgress(moduleId, {
        completedLessons: [...currentProgress.completedLessons, lessonId],
        lastAccessedAt: new Date().toISOString(),
      });

      // Ajouter XP
      setProgress(prev => ({
        ...prev,
        totalXP: prev.totalXP + 25, // 25 XP par lecon
      }));
    }
  }, [progress.moduleProgress, updateProgress]);

  // Completer un quiz
  const completeQuiz = useCallback((moduleId: string, quizId: string, score: number) => {
    const currentProgress = progress.moduleProgress[moduleId] || {
      moduleId,
      completedLessons: [],
      completedQuizzes: [],
      quizScores: {},
      completedExercises: [],
      finalExamPassed: false,
      finalExamAttempts: 0,
      totalTimeSpent: 0,
      lastAccessedAt: new Date().toISOString(),
      startedAt: new Date().toISOString(),
    };

    const newQuizScores = { ...currentProgress.quizScores, [quizId]: score };
    const newCompleted = currentProgress.completedQuizzes.includes(quizId)
      ? currentProgress.completedQuizzes
      : [...currentProgress.completedQuizzes, quizId];

    updateProgress(moduleId, {
      completedQuizzes: newCompleted,
      quizScores: newQuizScores,
      lastAccessedAt: new Date().toISOString(),
    });

    // Ajouter XP selon le score
    const xpEarned = Math.round(50 * (score / 100));
    setProgress(prev => ({
      ...prev,
      totalXP: prev.totalXP + xpEarned,
    }));
  }, [progress.moduleProgress, updateProgress]);

  // Completer un exercice
  const completeExercise = useCallback((moduleId: string, exerciseId: string) => {
    const currentProgress = progress.moduleProgress[moduleId] || {
      moduleId,
      completedLessons: [],
      completedQuizzes: [],
      quizScores: {},
      completedExercises: [],
      finalExamPassed: false,
      finalExamAttempts: 0,
      totalTimeSpent: 0,
      lastAccessedAt: new Date().toISOString(),
      startedAt: new Date().toISOString(),
    };

    if (!currentProgress.completedExercises.includes(exerciseId)) {
      updateProgress(moduleId, {
        completedExercises: [...currentProgress.completedExercises, exerciseId],
        lastAccessedAt: new Date().toISOString(),
      });

      setProgress(prev => ({
        ...prev,
        totalXP: prev.totalXP + 40, // 40 XP par exercice
      }));
    }
  }, [progress.moduleProgress, updateProgress]);

  // Calculer les stats
  const stats = useMemo(() => {
    return calculateTrainingStats(trainings, progress);
  }, [trainings, progress]);

  // Generer la synthese
  const generateSynthesisHandler = useCallback(() => {
    const synth = generateGlobalSynthesis(trainings);
    setSynthesis(synth);
  }, [trainings]);

  // Lecon courante
  const currentLesson = useMemo(() => {
    if (!currentModule || !currentLessonId) return null;
    const moduleTraining = trainings.get(currentModule);
    if (!moduleTraining) return null;
    return moduleTraining.lessons.find(l => l.id === currentLessonId) || null;
  }, [currentModule, currentLessonId, trainings]);

  const setCurrentLesson = useCallback((lessonId: string | null) => {
    setCurrentLessonId(lessonId);
  }, []);

  // Demarrer l'examen global
  const startGlobalExam = useCallback(() => {
    if (trainings.size === 0) return null;
    return generateGlobalExam(trainings, 5, 30);
  }, [trainings]);

  // Soumettre un resultat d'examen
  const submitExamResult = useCallback((result: ExamResult) => {
    if (result.examType === 'global') {
      setProgress(prev => ({
        ...prev,
        globalExamPassed: result.passed,
        globalExamScore: result.percentage,
        certificationDate: result.passed ? new Date().toISOString() : undefined,
        totalXP: prev.totalXP + result.xpEarned,
        badges: result.badgeEarned
          ? [...prev.badges, result.badgeEarned]
          : prev.badges,
      }));
    } else if (result.examType === 'module' && result.moduleId) {
      const currentProgress = progress.moduleProgress[result.moduleId];
      updateProgress(result.moduleId, {
        finalExamPassed: result.passed,
        finalExamScore: result.percentage,
        finalExamAttempts: (currentProgress?.finalExamAttempts || 0) + 1,
        completedAt: result.passed ? new Date().toISOString() : undefined,
      });
    }
  }, [progress.moduleProgress, updateProgress]);

  // Calculer la progression d'un module
  const getModuleProgress = useCallback((moduleId: string): number => {
    const moduleTraining = trainings.get(moduleId);
    const moduleProgress = progress.moduleProgress[moduleId];

    if (!moduleTraining || !moduleProgress) return 0;

    const totalItems =
      moduleTraining.lessons.length +
      moduleTraining.quizzes.length +
      moduleTraining.exercises.length;

    const completedItems =
      moduleProgress.completedLessons.length +
      moduleProgress.completedQuizzes.length +
      moduleProgress.completedExercises.length;

    return totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;
  }, [trainings, progress.moduleProgress]);

  // Verifier si un module est complete
  const isModuleCompleted = useCallback((moduleId: string): boolean => {
    const moduleProgress = progress.moduleProgress[moduleId];
    return moduleProgress?.completedAt !== undefined;
  }, [progress.moduleProgress]);

  return {
    isLoading,
    error,
    trainings,
    progress,
    updateProgress,
    saveProgress,
    stats,
    synthesis,
    generateSynthesis: generateSynthesisHandler,
    currentModule,
    setCurrentModule,
    currentLesson,
    setCurrentLesson,
    completeLesson,
    completeQuiz,
    completeExercise,
    startGlobalExam,
    submitExamResult,
    reload: loadTrainings,
    getModuleProgress,
    isModuleCompleted,
  };
}

// ============================================================================
// HOOK - useModuleTraining
// ============================================================================

interface UseModuleTrainingOptions {
  moduleId: string;
  autoLoad?: boolean;
}

interface UseModuleTrainingReturn {
  isLoading: boolean;
  error: string | null;
  training: ModuleTrainingContent | null;
  reload: () => Promise<void>;
}

export function useModuleTraining(options: UseModuleTrainingOptions): UseModuleTrainingReturn {
  const { moduleId, autoLoad = true } = options;
  const { language } = useI18n();

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [training, setTraining] = useState<ModuleTrainingContent | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const content = await loadModuleTraining(moduleId, language);
      setTraining(content);
    } catch (err) {
      setError(`Erreur lors du chargement de la formation ${moduleId}`);
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [moduleId, language]);

  useEffect(() => {
    if (autoLoad) {
      load();
    }
  }, [autoLoad, load]);

  return {
    isLoading,
    error,
    training,
    reload: load,
  };
}

// ============================================================================
// HOOK - useLessonPlayer
// ============================================================================

interface UseLessonPlayerOptions {
  lesson: ModuleLesson;
  onComplete: () => void;
}

interface UseLessonPlayerReturn {
  currentSlideIndex: number;
  totalSlides: number;
  currentSlide: LessonSlide | null;
  progress: number;
  isFirstSlide: boolean;
  isLastSlide: boolean;
  goToSlide: (index: number) => void;
  nextSlide: () => void;
  prevSlide: () => void;
  complete: () => void;
}

export function useLessonPlayer(options: UseLessonPlayerOptions): UseLessonPlayerReturn {
  const { lesson, onComplete } = options;
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);

  const slides = lesson.content.slides || [];
  const totalSlides = slides.length;
  const currentSlide = slides[currentSlideIndex] || null;
  const progress = totalSlides > 0 ? ((currentSlideIndex + 1) / totalSlides) * 100 : 0;
  const isFirstSlide = currentSlideIndex === 0;
  const isLastSlide = currentSlideIndex === totalSlides - 1;

  const goToSlide = useCallback((index: number) => {
    if (index >= 0 && index < totalSlides) {
      setCurrentSlideIndex(index);
    }
  }, [totalSlides]);

  const nextSlide = useCallback(() => {
    if (!isLastSlide) {
      setCurrentSlideIndex(prev => prev + 1);
    }
  }, [isLastSlide]);

  const prevSlide = useCallback(() => {
    if (!isFirstSlide) {
      setCurrentSlideIndex(prev => prev - 1);
    }
  }, [isFirstSlide]);

  const complete = useCallback(() => {
    onComplete();
  }, [onComplete]);

  return {
    currentSlideIndex,
    totalSlides,
    currentSlide,
    progress,
    isFirstSlide,
    isLastSlide,
    goToSlide,
    nextSlide,
    prevSlide,
    complete,
  };
}

// ============================================================================
// HOOK - useQuizPlayer
// ============================================================================

interface UseQuizPlayerOptions {
  quiz: ModuleQuiz;
  onComplete: (score: number, percentage: number, answers: number[][]) => void;
}

interface UseQuizPlayerReturn {
  currentQuestionIndex: number;
  totalQuestions: number;
  currentQuestion: ModuleQuestion | null;
  selectedAnswers: number[];
  allAnswers: number[][];
  progress: number;
  isFirstQuestion: boolean;
  isLastQuestion: boolean;
  timeRemaining: number;
  selectAnswer: (answerIndex: number) => void;
  toggleAnswer: (answerIndex: number) => void;
  nextQuestion: () => void;
  prevQuestion: () => void;
  submitQuiz: () => void;
}

export function useQuizPlayer(options: UseQuizPlayerOptions): UseQuizPlayerReturn {
  const { quiz, onComplete } = options;
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [allAnswers, setAllAnswers] = useState<number[][]>(
    quiz.questions.map(() => [])
  );
  const [timeRemaining, setTimeRemaining] = useState(quiz.duration * 60); // en secondes

  const questions = quiz.questions;
  const totalQuestions = questions.length;
  const currentQuestion = questions[currentQuestionIndex] || null;
  const selectedAnswers = allAnswers[currentQuestionIndex] || [];
  const progress = totalQuestions > 0 ? ((currentQuestionIndex + 1) / totalQuestions) * 100 : 0;
  const isFirstQuestion = currentQuestionIndex === 0;
  const isLastQuestion = currentQuestionIndex === totalQuestions - 1;

  // Timer
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 0) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Auto-submit quand le temps est ecoule
  useEffect(() => {
    if (timeRemaining === 0) {
      submitQuiz();
    }
  }, [timeRemaining]);

  const selectAnswer = useCallback((answerIndex: number) => {
    setAllAnswers(prev => {
      const newAnswers = [...prev];
      newAnswers[currentQuestionIndex] = [answerIndex];
      return newAnswers;
    });
  }, [currentQuestionIndex]);

  const toggleAnswer = useCallback((answerIndex: number) => {
    setAllAnswers(prev => {
      const newAnswers = [...prev];
      const current = newAnswers[currentQuestionIndex] || [];
      if (current.includes(answerIndex)) {
        newAnswers[currentQuestionIndex] = current.filter(a => a !== answerIndex);
      } else {
        newAnswers[currentQuestionIndex] = [...current, answerIndex];
      }
      return newAnswers;
    });
  }, [currentQuestionIndex]);

  const nextQuestion = useCallback(() => {
    if (!isLastQuestion) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  }, [isLastQuestion]);

  const prevQuestion = useCallback(() => {
    if (!isFirstQuestion) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  }, [isFirstQuestion]);

  const submitQuiz = useCallback(() => {
    let totalPoints = 0;
    let earnedPoints = 0;

    questions.forEach((q, index) => {
      totalPoints += q.points;
      const userAnswers = allAnswers[index] || [];
      const isCorrect =
        userAnswers.length === q.correctAnswers.length &&
        userAnswers.every(a => q.correctAnswers.includes(a));
      if (isCorrect) {
        earnedPoints += q.points;
      }
    });

    const percentage = totalPoints > 0 ? Math.round((earnedPoints / totalPoints) * 100) : 0;
    onComplete(earnedPoints, percentage, allAnswers);
  }, [questions, allAnswers, onComplete]);

  return {
    currentQuestionIndex,
    totalQuestions,
    currentQuestion,
    selectedAnswers,
    allAnswers,
    progress,
    isFirstQuestion,
    isLastQuestion,
    timeRemaining,
    selectAnswer,
    toggleAnswer,
    nextQuestion,
    prevQuestion,
    submitQuiz,
  };
}
