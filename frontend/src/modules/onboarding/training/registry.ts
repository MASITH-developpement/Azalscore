/**
 * AZALSCORE - Registre des Modules de Formation
 * ==============================================
 * Centralise et charge dynamiquement les formations de chaque module
 */

import { SupportedLanguage } from '../i18n';
import {
  ModuleTrainingContent,
  ModuleTrainingLoader,
  TrainingModuleRegistry,
  ModuleProgress,
  UserTrainingProgress,
  GlobalSynthesis,
  SynthesisItem,
} from './types';

// ============================================================================
// REGISTRE CENTRAL
// ============================================================================

/**
 * Registre des modules de formation
 * Chaque module s'enregistre ici avec son loader
 */
const moduleRegistry: TrainingModuleRegistry = {
  modules: {},
};

/**
 * Enregistrer un module de formation
 */
export function registerTrainingModule(
  moduleId: string,
  loader: ModuleTrainingLoader,
  requiredPermissions?: string[]
): void {
  moduleRegistry.modules[moduleId] = {
    loader,
    requiredPermissions,
  };
}

/**
 * Obtenir la liste des modules enregistres
 */
export function getRegisteredModules(): string[] {
  return Object.keys(moduleRegistry.modules);
}

/**
 * Verifier si un module est enregistre
 */
export function isModuleRegistered(moduleId: string): boolean {
  return moduleId in moduleRegistry.modules;
}

// ============================================================================
// CHARGEMENT DES FORMATIONS
// ============================================================================

/**
 * Cache des formations chargees
 */
const trainingCache: Map<string, ModuleTrainingContent> = new Map();

/**
 * Charger la formation d'un module
 */
export async function loadModuleTraining(
  moduleId: string,
  language: SupportedLanguage
): Promise<ModuleTrainingContent | null> {
  const cacheKey = `${moduleId}_${language}`;

  // Verifier le cache
  if (trainingCache.has(cacheKey)) {
    return trainingCache.get(cacheKey)!;
  }

  // Verifier si le module est enregistre
  const moduleEntry = moduleRegistry.modules[moduleId];
  if (!moduleEntry) {
    console.warn(`Module de formation non enregistre: ${moduleId}`);
    return null;
  }

  try {
    const content = await moduleEntry.loader(language);
    trainingCache.set(cacheKey, content);
    return content;
  } catch (error) {
    console.error(`Erreur chargement formation ${moduleId}:`, error);
    return null;
  }
}

/**
 * Charger les formations de plusieurs modules
 */
export async function loadMultipleModuleTrainings(
  moduleIds: string[],
  language: SupportedLanguage
): Promise<Map<string, ModuleTrainingContent>> {
  const results = new Map<string, ModuleTrainingContent>();

  await Promise.all(
    moduleIds.map(async (moduleId) => {
      const content = await loadModuleTraining(moduleId, language);
      if (content) {
        results.set(moduleId, content);
      }
    })
  );

  return results;
}

/**
 * Charger toutes les formations accessibles par l'utilisateur
 */
export async function loadUserTrainings(
  userPermissions: string[],
  language: SupportedLanguage
): Promise<Map<string, ModuleTrainingContent>> {
  const accessibleModules = getAccessibleModules(userPermissions);
  return loadMultipleModuleTrainings(accessibleModules, language);
}

/**
 * Obtenir les modules accessibles selon les permissions
 */
export function getAccessibleModules(userPermissions: string[]): string[] {
  return Object.entries(moduleRegistry.modules)
    .filter(([_, entry]) => {
      if (!entry.requiredPermissions || entry.requiredPermissions.length === 0) {
        return true; // Pas de permission requise
      }
      return entry.requiredPermissions.some(perm => userPermissions.includes(perm));
    })
    .map(([moduleId]) => moduleId);
}

// ============================================================================
// VIDER LE CACHE
// ============================================================================

/**
 * Vider le cache des formations
 */
export function clearTrainingCache(): void {
  trainingCache.clear();
}

/**
 * Vider le cache d'un module specifique
 */
export function clearModuleCache(moduleId: string): void {
  for (const key of trainingCache.keys()) {
    if (key.startsWith(`${moduleId}_`)) {
      trainingCache.delete(key);
    }
  }
}

// ============================================================================
// SYNTHESE
// ============================================================================

/**
 * Generer la synthese globale a partir des modules charges
 */
export function generateGlobalSynthesis(
  trainings: Map<string, ModuleTrainingContent>
): GlobalSynthesis {
  const modules: SynthesisItem[] = [];
  let totalKeyPoints = 0;
  let totalShortcuts = 0;

  for (const [moduleId, content] of trainings) {
    // Extraire les points cles de chaque lecon
    const keyPoints: string[] = [];
    const shortcuts: { key: string; action: string }[] = [];
    const tips: string[] = [];
    const warnings: string[] = [];

    content.lessons.forEach(lesson => {
      if (lesson.content.slides) {
        lesson.content.slides.forEach(slide => {
          // Extraire les points cles (lignes commencant par - ou *)
          const lines = slide.content.split('\n');
          lines.forEach(line => {
            const trimmed = line.trim();
            if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
              keyPoints.push(trimmed.substring(2));
            }
            // Extraire les raccourcis (format: `Ctrl+X` : action)
            const shortcutMatch = trimmed.match(/`([^`]+)`\s*:\s*(.+)/);
            if (shortcutMatch) {
              shortcuts.push({ key: shortcutMatch[1], action: shortcutMatch[2] });
            }
            // Extraire les conseils
            if (trimmed.toLowerCase().includes('conseil') || trimmed.toLowerCase().includes('astuce')) {
              tips.push(trimmed);
            }
            // Extraire les avertissements
            if (trimmed.toLowerCase().includes('attention') || trimmed.toLowerCase().includes('important')) {
              warnings.push(trimmed);
            }
          });
        });
      }
    });

    modules.push({
      moduleId,
      moduleName: content.moduleName,
      keyPoints: [...new Set(keyPoints)].slice(0, 10), // Max 10 points cles uniques
      shortcuts: shortcuts.slice(0, 10),
      tips: [...new Set(tips)].slice(0, 5),
      warnings: [...new Set(warnings)].slice(0, 5),
    });

    totalKeyPoints += keyPoints.length;
    totalShortcuts += shortcuts.length;
  }

  return {
    generatedAt: new Date().toISOString(),
    modules,
    totalKeyPoints,
    totalShortcuts,
  };
}

// ============================================================================
// STATISTIQUES
// ============================================================================

/**
 * Calculer les statistiques globales de formation
 */
export function calculateTrainingStats(
  trainings: Map<string, ModuleTrainingContent>,
  progress: UserTrainingProgress
): {
  totalModules: number;
  completedModules: number;
  totalLessons: number;
  completedLessons: number;
  totalQuizzes: number;
  completedQuizzes: number;
  totalExercises: number;
  completedExercises: number;
  totalDuration: number;
  timeSpent: number;
  overallProgress: number;
} {
  let totalLessons = 0;
  let completedLessons = 0;
  let totalQuizzes = 0;
  let completedQuizzes = 0;
  let totalExercises = 0;
  let completedExercises = 0;
  let totalDuration = 0;
  let timeSpent = 0;
  let completedModules = 0;

  for (const [moduleId, content] of trainings) {
    totalLessons += content.lessons.length;
    totalQuizzes += content.quizzes.length;
    totalExercises += content.exercises.length;
    totalDuration += content.estimatedDuration;

    const moduleProgress = progress.moduleProgress[moduleId];
    if (moduleProgress) {
      completedLessons += moduleProgress.completedLessons.length;
      completedQuizzes += moduleProgress.completedQuizzes.length;
      completedExercises += moduleProgress.completedExercises.length;
      timeSpent += moduleProgress.totalTimeSpent;

      if (moduleProgress.completedAt) {
        completedModules++;
      }
    }
  }

  const totalItems = totalLessons + totalQuizzes + totalExercises;
  const completedItems = completedLessons + completedQuizzes + completedExercises;
  const overallProgress = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;

  return {
    totalModules: trainings.size,
    completedModules,
    totalLessons,
    completedLessons,
    totalQuizzes,
    completedQuizzes,
    totalExercises,
    completedExercises,
    totalDuration,
    timeSpent,
    overallProgress,
  };
}

// ============================================================================
// EXAMEN GLOBAL
// ============================================================================

/**
 * Generer un examen global a partir des questions de tous les modules
 */
export function generateGlobalExam(
  trainings: Map<string, ModuleTrainingContent>,
  questionsPerModule: number = 5,
  totalQuestions: number = 30
): {
  questions: Array<{
    moduleId: string;
    question: ModuleTrainingContent['quizzes'][0]['questions'][0];
  }>;
  duration: number;
} {
  const allQuestions: Array<{
    moduleId: string;
    question: ModuleTrainingContent['quizzes'][0]['questions'][0];
  }> = [];

  // Collecter les questions de chaque module
  for (const [moduleId, content] of trainings) {
    const moduleQuestions = content.quizzes.flatMap(quiz =>
      quiz.questions.map(q => ({ moduleId, question: q }))
    );

    // Ajouter aussi les questions de l'examen final du module
    if (content.finalExam) {
      content.finalExam.questions.forEach(q => {
        moduleQuestions.push({ moduleId, question: q });
      });
    }

    // Melanger et prendre N questions par module
    const shuffled = moduleQuestions.sort(() => Math.random() - 0.5);
    allQuestions.push(...shuffled.slice(0, questionsPerModule));
  }

  // Melanger toutes les questions et limiter au total
  const finalQuestions = allQuestions
    .sort(() => Math.random() - 0.5)
    .slice(0, totalQuestions);

  // Calculer la duree (environ 2 min par question)
  const duration = Math.max(30, finalQuestions.length * 2);

  return {
    questions: finalQuestions,
    duration,
  };
}

// ============================================================================
// EXPORTS
// ============================================================================

export {
  moduleRegistry,
  trainingCache,
};
