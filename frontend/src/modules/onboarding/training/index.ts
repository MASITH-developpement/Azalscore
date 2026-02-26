/**
 * AZALSCORE - Module de Formation Centralise
 * ===========================================
 * Systeme de formation modulaire et personnalise
 *
 * Architecture:
 * - Chaque module AZALSCORE contient un dossier `training/` avec son contenu
 * - Ce module central agregre les formations des modules accessibles
 * - La progression est globale par utilisateur
 */

// Types
export * from './types';

// Registre
export {
  registerTrainingModule,
  getRegisteredModules,
  isModuleRegistered,
  loadModuleTraining,
  loadMultipleModuleTrainings,
  loadUserTrainings,
  getAccessibleModules,
  clearTrainingCache,
  clearModuleCache,
  generateGlobalSynthesis,
  calculateTrainingStats,
  generateGlobalExam,
} from './registry';

// Hooks
export {
  useTraining,
  useModuleTraining,
  useLessonPlayer,
  useQuizPlayer,
} from './hooks';

// Initialisation
export {
  initializeTrainingModules,
  AVAILABLE_TRAINING_MODULES,
} from './init';
export type { TrainingModuleId } from './init';
