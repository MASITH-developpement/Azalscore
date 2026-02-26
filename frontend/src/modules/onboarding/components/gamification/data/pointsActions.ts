/**
 * AZALSCORE - Table des Points
 * ============================
 * Définit les points gagnés pour chaque action
 */

import type { PointsAction } from '../types';

export const POINTS_ACTIONS: PointsAction[] = [
  // Apprentissage
  { id: 'complete-lesson', action: 'Compléter une micro-leçon', points: 10, category: 'apprentissage', icon: '📚' },
  { id: 'watch-video', action: 'Regarder une vidéo', points: 15, category: 'apprentissage', icon: '🎬' },
  { id: 'read-doc', action: 'Lire un document', points: 5, category: 'apprentissage', icon: '📖' },
  { id: 'complete-tour', action: 'Terminer un tour guidé', points: 25, category: 'apprentissage', icon: '🗺️' },

  // Pratique
  { id: 'quiz-correct', action: 'Bonne réponse quiz', points: 5, category: 'pratique', icon: '✅' },
  { id: 'quiz-perfect', action: 'Quiz sans faute', points: 50, category: 'pratique', icon: '💯' },
  { id: 'game-win', action: 'Gagner un mini-jeu', points: 20, category: 'pratique', icon: '🎮' },
  { id: 'simulation-complete', action: 'Terminer une simulation', points: 30, category: 'pratique', icon: '🎯' },
  { id: 'daily-challenge', action: 'Défi quotidien', points: 50, category: 'pratique', icon: '⭐' },

  // Social
  { id: 'help-colleague', action: 'Aider un collègue', points: 25, category: 'social', icon: '🤝' },
  { id: 'share-tip', action: 'Partager une astuce', points: 10, category: 'social', icon: '💡' },
  { id: 'first-place', action: '1ère place classement', points: 100, category: 'social', icon: '🥇' },

  // Examens
  { id: 'exam-pass', action: 'Réussir un examen', points: 100, category: 'examen', icon: '🎓' },
  { id: 'exam-perfect', action: 'Examen note A+', points: 200, category: 'examen', icon: '🏆' },
  { id: 'level-up', action: 'Passage de niveau', points: 150, category: 'examen', icon: '⬆️' },
];

/**
 * Obtient une action de points par son ID
 */
export function getPointsAction(actionId: string): PointsAction | undefined {
  return POINTS_ACTIONS.find(a => a.id === actionId);
}

/**
 * Obtient les actions par catégorie
 */
export function getActionsByCategory(category: string): PointsAction[] {
  return POINTS_ACTIONS.filter(a => a.category === category);
}

/**
 * Calcule les points avec multiplicateur
 */
export function calculatePoints(actionId: string, multiplier: number = 1): number {
  const action = getPointsAction(actionId);
  if (!action) return 0;
  return Math.round(action.points * multiplier);
}
