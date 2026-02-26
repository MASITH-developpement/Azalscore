/**
 * AZALSCORE - Types du système de Gamification
 * =============================================
 */

// ============================================================================
// PROFIL UTILISATEUR
// ============================================================================

export interface UserGameProfile {
  id: string;
  displayName: string;
  avatar: string;
  level: number;
  xp: number;
  xpToNextLevel: number;
  totalPoints: number;
  streak: number;
  badges: Badge[];
  achievements: Achievement[];
  completedChallenges: string[];
  rank: number;
  title: string;
}

// ============================================================================
// BADGES & ACHIEVEMENTS
// ============================================================================

export type BadgeRarity = 'common' | 'rare' | 'epic' | 'legendary';

export interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  rarity: BadgeRarity;
  unlockedAt?: string;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  progress: number;
  target: number;
  reward: number;
  completed: boolean;
}

// ============================================================================
// DÉFIS
// ============================================================================

export type ChallengeType = 'daily' | 'weekly' | 'special';
export type ChallengeDifficulty = 'easy' | 'medium' | 'hard';

export interface ChallengeTask {
  id: string;
  description: string;
  completed: boolean;
}

export interface Challenge {
  id: string;
  title: string;
  description: string;
  type: ChallengeType;
  difficulty: ChallengeDifficulty;
  xpReward: number;
  timeLimit?: number;
  tasks: ChallengeTask[];
  completed: boolean;
}

// ============================================================================
// CLASSEMENT
// ============================================================================

export interface LeaderboardEntry {
  rank: number;
  userId: string;
  displayName: string;
  avatar: string;
  level: number;
  points: number;
  isCurrentUser?: boolean;
}

// ============================================================================
// SYSTÈME D'EXAMEN
// ============================================================================

export type QuestionDifficulty = 'facile' | 'moyen' | 'difficile';
export type ExamGrade = 'A+' | 'A' | 'B' | 'C' | 'D' | 'F';

export interface ExamQuestion {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
  points: number;
  difficulty: QuestionDifficulty;
}

export interface LevelExam {
  level: number;
  title: string;
  description: string;
  duration: number; // en secondes
  passingScore: number; // pourcentage minimum pour réussir
  questions: ExamQuestion[];
  xpReward: number;
  badgeReward?: string;
}

export interface ExamResult {
  examLevel: number;
  score: number;
  totalPoints: number;
  maxPoints: number;
  percentage: number;
  passed: boolean;
  grade: ExamGrade;
  timeSpent: number;
  correctAnswers: number;
  totalQuestions: number;
  xpEarned: number;
  completedAt: string;
}

// ============================================================================
// QUIZ D'ENTRAÎNEMENT
// ============================================================================

export interface PracticeQuiz {
  id: string;
  title: string;
  description: string;
  category: string;
  icon: string;
  color: string;
  duration: number; // en minutes
  difficulty: QuestionDifficulty;
  xpReward: number;
  questions: ExamQuestion[];
}

export interface PracticeQuizResult {
  score: number;
  percentage: number;
  xpEarned: number;
}

// ============================================================================
// SYSTÈME DE POINTS
// ============================================================================

export type PointsCategory = 'apprentissage' | 'pratique' | 'social' | 'examen';

export interface PointsAction {
  id: string;
  action: string;
  points: number;
  category: PointsCategory;
  icon: string;
}

export interface PointsHistoryEntry {
  action: string;
  points: number;
  timestamp: string;
}

// ============================================================================
// NIVEAUX
// ============================================================================

export interface LevelDefinition {
  level: number;
  title: string;
  xp: number;
  color: string;
}

// ============================================================================
// GRADES
// ============================================================================

export interface GradeThreshold {
  grade: ExamGrade;
  min: number;
  label: string;
  color: string;
  stars: number;
}

// ============================================================================
// CÉLÉBRATION
// ============================================================================

export type CelebrationType = 'levelup' | 'badge' | 'achievement' | 'streak';

export interface CelebrationData {
  type: CelebrationType;
  message: string;
  reward?: number;
}
