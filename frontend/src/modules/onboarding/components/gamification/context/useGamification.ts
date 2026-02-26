/**
 * AZALSCORE - Hook de gestion de l'état de gamification
 * ======================================================
 */

import { useState, useCallback } from 'react';
import type { UserGameProfile, ExamResult, PointsHistoryEntry } from '../types';
import { LEVELS, BADGES } from '../constants';
import { POINTS_ACTIONS, getPointsAction } from '../data/pointsActions';

/**
 * État initial du profil utilisateur
 */
const INITIAL_PROFILE: UserGameProfile = {
  id: 'user-1',
  displayName: 'Utilisateur',
  avatar: '👤',
  level: 1,
  xp: 45,
  xpToNextLevel: 100,
  totalPoints: 145,
  streak: 3,
  badges: BADGES.slice(0, 3).map(b => ({ ...b, unlockedAt: new Date().toISOString() })),
  achievements: [],
  completedChallenges: [],
  rank: 42,
  title: 'Débutant',
};

/**
 * Hook principal de gestion de l'état de gamification
 */
export function useGamificationState() {
  const [profile, setProfile] = useState<UserGameProfile>(INITIAL_PROFILE);
  const [examResults, setExamResults] = useState<ExamResult[]>([]);
  const [pendingLevelUp, setPendingLevelUp] = useState<number | null>(null);
  const [pointsHistory, setPointsHistory] = useState<PointsHistoryEntry[]>([]);

  /**
   * Ajoute des points avec historique
   */
  const addPoints = useCallback((actionId: string, multiplier: number = 1): number => {
    const action = getPointsAction(actionId);
    if (!action) return 0;

    const points = Math.round(action.points * multiplier);

    setPointsHistory(prev => [
      { action: action.action, points, timestamp: new Date().toISOString() },
      ...prev.slice(0, 49), // Garder les 50 derniers
    ]);

    setProfile(prev => ({
      ...prev,
      totalPoints: prev.totalPoints + points,
    }));

    return points;
  }, []);

  /**
   * Ajoute de l'XP avec vérification de niveau
   */
  const addXP = useCallback((amount: number): void => {
    setProfile(prev => {
      let newXP = prev.xp + amount;
      const newLevel = prev.level;
      const newXPToNext = prev.xpToNextLevel;
      let levelUpPending = false;

      // Vérifier si on atteint le seuil du niveau suivant
      if (newXP >= newXPToNext && newLevel < LEVELS.length) {
        // Ne pas monter de niveau automatiquement - il faut passer l'examen
        levelUpPending = true;
        newXP = newXPToNext; // Plafonner à l'XP max du niveau
      }

      if (levelUpPending) {
        setPendingLevelUp(newLevel + 1);
      }

      return {
        ...prev,
        xp: newXP,
        xpToNextLevel: newXPToNext,
        totalPoints: prev.totalPoints + amount,
      };
    });
  }, []);

  /**
   * Passe au niveau supérieur après réussite de l'examen
   */
  const levelUp = useCallback((newLevel: number): void => {
    setProfile(prev => {
      const nextLevelData = LEVELS.find(l => l.level === newLevel + 1);
      const currentLevelData = LEVELS.find(l => l.level === newLevel);
      const xpToNext = nextLevelData && currentLevelData
        ? nextLevelData.xp - currentLevelData.xp
        : 9999;

      return {
        ...prev,
        level: newLevel,
        xp: 0,
        xpToNextLevel: xpToNext,
        title: LEVELS[newLevel - 1]?.title || prev.title,
      };
    });
    setPendingLevelUp(null);
  }, []);

  /**
   * Enregistre un résultat d'examen
   */
  const recordExamResult = useCallback((result: ExamResult): void => {
    setExamResults(prev => [result, ...prev]);
    if (result.passed) {
      addPoints('exam-pass');
      if (result.grade === 'A+') {
        addPoints('exam-perfect');
      }
    }
  }, [addPoints]);

  /**
   * Débloque un badge
   */
  const unlockBadge = useCallback((badgeId: string): void => {
    setProfile(prev => {
      if (prev.badges.some(b => b.id === badgeId)) return prev;
      const badge = BADGES.find(b => b.id === badgeId);
      if (!badge) return prev;
      return {
        ...prev,
        badges: [...prev.badges, { ...badge, unlockedAt: new Date().toISOString() }],
      };
    });
  }, []);

  /**
   * Incrémente la série de jours consécutifs
   */
  const incrementStreak = useCallback((): void => {
    setProfile(prev => ({ ...prev, streak: prev.streak + 1 }));
  }, []);

  /**
   * Réinitialise le profil (pour tests)
   */
  const resetProfile = useCallback((): void => {
    setProfile(INITIAL_PROFILE);
    setExamResults([]);
    setPendingLevelUp(null);
    setPointsHistory([]);
  }, []);

  return {
    // État
    profile,
    examResults,
    pendingLevelUp,
    pointsHistory,

    // Actions
    addXP,
    addPoints,
    levelUp,
    recordExamResult,
    unlockBadge,
    incrementStreak,
    resetProfile,

    // Données statiques (pour compatibilité)
    POINTS_ACTIONS,
  };
}

export type GamificationState = ReturnType<typeof useGamificationState>;
