/**
 * AZALSCORE - Constantes du système de Gamification
 * ==================================================
 */

import type { LevelDefinition, Badge, Challenge, GradeThreshold } from './types';

// ============================================================================
// NIVEAUX
// ============================================================================

export const LEVELS: LevelDefinition[] = [
  { level: 1, title: 'Débutant', xp: 0, color: 'gray' },
  { level: 2, title: 'Apprenti', xp: 100, color: 'green' },
  { level: 3, title: 'Initié', xp: 350, color: 'blue' },
  { level: 4, title: 'Compétent', xp: 700, color: 'purple' },
  { level: 5, title: 'Expert', xp: 1200, color: 'orange' },
  { level: 6, title: 'Maître', xp: 1800, color: 'red' },
  { level: 7, title: 'Champion', xp: 2800, color: 'yellow' },
  { level: 8, title: 'Légende', xp: 4500, color: 'pink' },
];

// ============================================================================
// BADGES
// ============================================================================

export const BADGES: Badge[] = [
  { id: 'first-login', name: 'Premier Pas', description: 'Première connexion', icon: '🚀', rarity: 'common' },
  { id: 'explorer', name: 'Explorateur', description: 'Visite 5 modules', icon: '🗺️', rarity: 'common' },
  { id: 'fast-learner', name: 'Rapide', description: 'Complète une leçon en moins de 2 min', icon: '⚡', rarity: 'rare' },
  { id: 'perfect-quiz', name: 'Sans Faute', description: '100% à un quiz', icon: '💯', rarity: 'rare' },
  { id: 'streak-7', name: 'Assidu', description: '7 jours consécutifs', icon: '🔥', rarity: 'epic' },
  { id: 'all-modules', name: 'Complétiste', description: 'Tous les modules terminés', icon: '🏆', rarity: 'legendary' },
  { id: 'helper', name: 'Entraideur', description: 'Aide 3 collègues', icon: '🤝', rarity: 'rare' },
  { id: 'night-owl', name: 'Noctambule', description: 'Apprend après 22h', icon: '🦉', rarity: 'common' },
  { id: 'early-bird', name: 'Matinal', description: 'Apprend avant 8h', icon: '🐦', rarity: 'common' },
  { id: 'speedster', name: 'Speedster', description: 'Complète 3 leçons en 1 jour', icon: '🏃', rarity: 'epic' },
];

// ============================================================================
// DÉFIS QUOTIDIENS
// ============================================================================

export const DAILY_CHALLENGES: Challenge[] = [
  {
    id: 'daily-1',
    title: 'Défi du Jour',
    description: 'Complétez ces 3 tâches pour gagner 50 XP',
    type: 'daily',
    difficulty: 'easy',
    xpReward: 50,
    completed: false,
    tasks: [
      { id: 't1', description: 'Se connecter', completed: true },
      { id: 't2', description: 'Compléter 1 leçon', completed: false },
      { id: 't3', description: 'Répondre à 1 quiz', completed: false },
    ],
  },
  {
    id: 'daily-2',
    title: 'Speed Challenge',
    description: 'Terminez une leçon en moins de 3 minutes',
    type: 'daily',
    difficulty: 'medium',
    xpReward: 75,
    timeLimit: 180,
    completed: false,
    tasks: [
      { id: 't1', description: 'Compléter la leçon rapidement', completed: false },
    ],
  },
];

// ============================================================================
// SEUILS DE NOTES
// ============================================================================

export const GRADE_THRESHOLDS: GradeThreshold[] = [
  { grade: 'A+', min: 95, label: 'Excellent', color: 'from-yellow-400 to-amber-500', stars: 5 },
  { grade: 'A', min: 85, label: 'Très bien', color: 'from-green-400 to-emerald-500', stars: 4 },
  { grade: 'B', min: 75, label: 'Bien', color: 'from-blue-400 to-cyan-500', stars: 3 },
  { grade: 'C', min: 65, label: 'Assez bien', color: 'from-purple-400 to-violet-500', stars: 2 },
  { grade: 'D', min: 50, label: 'Passable', color: 'from-orange-400 to-amber-500', stars: 1 },
  { grade: 'F', min: 0, label: 'Insuffisant', color: 'from-red-400 to-rose-500', stars: 0 },
];

// ============================================================================
// UTILITAIRES
// ============================================================================

/**
 * Obtient les informations d'un niveau
 */
export function getLevelInfo(level: number): LevelDefinition | undefined {
  return LEVELS.find(l => l.level === level);
}

/**
 * Obtient le badge par son ID
 */
export function getBadgeById(badgeId: string): Badge | undefined {
  return BADGES.find(b => b.id === badgeId);
}

/**
 * Calcule la note à partir du pourcentage
 */
export function getGradeFromPercentage(percentage: number): GradeThreshold {
  return GRADE_THRESHOLDS.find(g => percentage >= g.min) || GRADE_THRESHOLDS[GRADE_THRESHOLDS.length - 1];
}

/**
 * Calcule l'XP nécessaire pour le niveau suivant
 */
export function getXPToNextLevel(currentLevel: number): number {
  const nextLevel = LEVELS.find(l => l.level === currentLevel + 1);
  const currentLevelData = LEVELS.find(l => l.level === currentLevel);

  if (!nextLevel || !currentLevelData) return 9999;
  return nextLevel.xp - currentLevelData.xp;
}
