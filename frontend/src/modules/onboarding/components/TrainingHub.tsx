/**
 * AZALSCORE - Training Hub
 * ========================
 * Hub central de formation unifiant tous les systemes :
 * - Gamification (XP, badges, leaderboard)
 * - Mini-jeux interactifs
 * - Micro-learning
 * - Tours guides
 * - Base de connaissances
 */

import React, { useState, useEffect } from 'react';
import {
  GraduationCap,
  Trophy,
  Gamepad2,
  BookOpen,
  Target,
  Sparkles,
  Flame,
  Star,
  ChevronRight,
  Play,
  Clock,
  Award,
  TrendingUp,
  Zap,
  Gift,
  Crown,
  Users,
  BarChart3,
} from 'lucide-react';

// Import des composants
import { useGamification, GamificationProvider, PlayerStatsCard, DailyChallengeCard, BadgeCollection, Leaderboard } from './Gamification';
import { AnimatedQuiz, DragDropCategory, MatchingGame, MemoryGame } from './InteractiveGames';
import { MicroLearningLibrary } from './MicroLearning';

// ============================================================================
// TYPES
// ============================================================================

interface TabConfig {
  id: string;
  label: string;
  icon: React.ElementType;
  color: string;
  description: string;
}

interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  progress?: number;
  total?: number;
}

interface LearningPath {
  id: string;
  title: string;
  description: string;
  modules: string[];
  duration: string;
  difficulty: 'debutant' | 'intermediaire' | 'avance';
  progress: number;
  xpReward: number;
}

// ============================================================================
// CONFIGURATION
// ============================================================================

const TABS: TabConfig[] = [
  {
    id: 'overview',
    label: 'Accueil',
    icon: GraduationCap,
    color: 'blue',
    description: 'Vue d\'ensemble de votre progression',
  },
  {
    id: 'learning',
    label: 'Apprendre',
    icon: BookOpen,
    color: 'green',
    description: 'Micro-lecons et tutoriels',
  },
  {
    id: 'games',
    label: 'Jouer',
    icon: Gamepad2,
    color: 'purple',
    description: 'Mini-jeux educatifs',
  },
  {
    id: 'achievements',
    label: 'Succes',
    icon: Trophy,
    color: 'amber',
    description: 'Badges et recompenses',
  },
  {
    id: 'leaderboard',
    label: 'Classement',
    icon: Crown,
    color: 'pink',
    description: 'Comparez-vous aux autres',
  },
];

const LEARNING_PATHS: LearningPath[] = [
  {
    id: 'basics',
    title: 'Les Fondamentaux',
    description: 'Maitrisez les bases d\'AZALSCORE',
    modules: ['navigation', 'search', 'profile'],
    duration: '30 min',
    difficulty: 'debutant',
    progress: 0,
    xpReward: 200,
  },
  {
    id: 'commercial',
    title: 'Gestion Commerciale',
    description: 'Clients, devis et factures',
    modules: ['crm', 'quotes', 'invoices', 'payments'],
    duration: '1h30',
    difficulty: 'intermediaire',
    progress: 0,
    xpReward: 500,
  },
  {
    id: 'finance',
    title: 'Finance & Comptabilite',
    description: 'Tresorerie et ecritures comptables',
    modules: ['treasury', 'accounting', 'bank-reconciliation'],
    duration: '2h',
    difficulty: 'avance',
    progress: 0,
    xpReward: 750,
  },
  {
    id: 'operations',
    title: 'Operations',
    description: 'Stocks, production et interventions',
    modules: ['inventory', 'production', 'maintenance', 'interventions'],
    duration: '2h',
    difficulty: 'avance',
    progress: 0,
    xpReward: 750,
  },
];

const ACHIEVEMENTS: Achievement[] = [
  { id: 'first-lesson', title: 'Premiere Lecon', description: 'Completez votre premiere micro-lecon', icon: '📚', unlocked: false },
  { id: 'game-master', title: 'Maitre du Jeu', description: 'Gagnez 5 mini-jeux', icon: '🎮', unlocked: false, progress: 0, total: 5 },
  { id: 'streak-7', title: 'Semaine Parfaite', description: 'Connectez-vous 7 jours consecutifs', icon: '🔥', unlocked: false, progress: 0, total: 7 },
  { id: 'quiz-ace', title: 'Sans Faute', description: 'Obtenez 100% a un quiz', icon: '💯', unlocked: false },
  { id: 'speed-learner', title: 'Apprentissage Eclair', description: 'Terminez 3 lecons en une journee', icon: '⚡', unlocked: false, progress: 0, total: 3 },
  { id: 'explorer', title: 'Explorateur', description: 'Visitez tous les modules', icon: '🧭', unlocked: false, progress: 0, total: 15 },
  { id: 'helper', title: 'Bon Samaritain', description: 'Aidez un collegue via le chat', icon: '🤝', unlocked: false },
  { id: 'all-paths', title: 'Chemin Complet', description: 'Terminez tous les parcours', icon: '🏆', unlocked: false, progress: 0, total: 4 },
];

// Mock data pour les composants de gamification
const MOCK_DAILY_CHALLENGE = {
  id: 'daily-1',
  title: 'Defi du jour',
  description: 'Completez ces taches pour gagner des XP bonus',
  type: 'daily' as const,
  difficulty: 'medium' as const,
  xpReward: 100,
  tasks: [
    { id: 't1', description: 'Creer un nouveau client', completed: false },
    { id: 't2', description: 'Generer un devis', completed: false },
    { id: 't3', description: 'Consulter le tableau de bord', completed: true },
  ],
  completed: false,
};

const MOCK_BADGES = [
  { id: 'b1', name: 'Debutant', description: 'Premier pas', icon: '🌟', rarity: 'common' as const, unlockedAt: '2024-01-15' },
  { id: 'b2', name: 'Assidu', description: '7 jours consecutifs', icon: '🔥', rarity: 'rare' as const, unlockedAt: '2024-01-22' },
];

const ALL_BADGES = [
  ...MOCK_BADGES,
  { id: 'b3', name: 'Expert CRM', description: 'Maitriser le CRM', icon: '🎯', rarity: 'epic' as const },
  { id: 'b4', name: 'Legende', description: 'Completez tout', icon: '👑', rarity: 'legendary' as const },
];

const MOCK_LEADERBOARD = [
  { rank: 1, userId: 'u1', displayName: 'Marie D.', avatar: '/avatars/1.png', level: 12, points: 2500 },
  { rank: 2, userId: 'u2', displayName: 'Jean M.', avatar: '/avatars/2.png', level: 10, points: 2100 },
  { rank: 3, userId: 'u3', displayName: 'Vous', avatar: '/avatars/3.png', level: 5, points: 1250, isCurrentUser: true },
  { rank: 4, userId: 'u4', displayName: 'Sophie L.', avatar: '/avatars/4.png', level: 4, points: 980 },
  { rank: 5, userId: 'u5', displayName: 'Pierre R.', avatar: '/avatars/5.png', level: 3, points: 750 },
];

// ============================================================================
// COMPOSANTS
// ============================================================================

/**
 * Carte de statistiques rapides
 */
function QuickStats({ stats }: { stats: { label: string; value: string | number; icon: React.ElementType; color: string; trend?: string }[] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <div
          key={index}
          className="bg-white rounded-xl p-4 border border-gray-100 shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className={`w-10 h-10 rounded-lg bg-${stat.color}-100 flex items-center justify-center`}>
              <stat.icon className={`w-5 h-5 text-${stat.color}-600`} />
            </div>
            {stat.trend && (
              <span className="text-xs text-green-600 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                {stat.trend}
              </span>
            )}
          </div>
          <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
          <p className="text-sm text-gray-500">{stat.label}</p>
        </div>
      ))}
    </div>
  );
}

/**
 * Carte de parcours d'apprentissage
 */
function LearningPathCard({ path, onStart }: { path: LearningPath; onStart: () => void }) {
  const difficultyColors = {
    debutant: 'green',
    intermediaire: 'amber',
    avance: 'purple',
  };

  const difficultyLabels = {
    debutant: 'Debutant',
    intermediaire: 'Intermediaire',
    avance: 'Avance',
  };

  const color = difficultyColors[path.difficulty];

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-lg transition-all group">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-semibold text-gray-900 text-lg group-hover:text-blue-600 transition-colors">
            {path.title}
          </h3>
          <p className="text-gray-600 text-sm mt-1">{path.description}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium bg-${color}-100 text-${color}-700`}>
          {difficultyLabels[path.difficulty]}
        </span>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-gray-500">{path.modules.length} modules</span>
          <span className="font-medium text-gray-900">{path.progress}%</span>
        </div>
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all"
            style={{ width: `${path.progress}%` }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {path.duration}
          </span>
          <span className="flex items-center gap-1">
            <Zap className="w-4 h-4 text-amber-500" />
            +{path.xpReward} XP
          </span>
        </div>
        <button
          onClick={onStart}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          {path.progress > 0 ? 'Continuer' : 'Commencer'}
          <Play className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

/**
 * Grille de succes/achievements
 */
function AchievementsGrid({ achievements }: { achievements: Achievement[] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {achievements.map((achievement) => (
        <div
          key={achievement.id}
          className={`relative rounded-xl p-4 border-2 transition-all ${
            achievement.unlocked
              ? 'bg-gradient-to-br from-amber-50 to-amber-100 border-amber-300 shadow-md'
              : 'bg-gray-50 border-gray-200 grayscale'
          }`}
        >
          <div className="text-4xl mb-3 text-center">
            {achievement.icon}
          </div>
          <h4 className={`font-semibold text-center mb-1 ${
            achievement.unlocked ? 'text-gray-900' : 'text-gray-500'
          }`}>
            {achievement.title}
          </h4>
          <p className={`text-xs text-center ${
            achievement.unlocked ? 'text-gray-600' : 'text-gray-400'
          }`}>
            {achievement.description}
          </p>

          {/* Progress indicator */}
          {achievement.progress !== undefined && achievement.total && (
            <div className="mt-3">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>{achievement.progress}/{achievement.total}</span>
              </div>
              <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-500 rounded-full transition-all"
                  style={{ width: `${(achievement.progress / achievement.total) * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Unlocked badge */}
          {achievement.unlocked && (
            <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/**
 * Section de recommandations personnalisees
 */
function Recommendations() {
  const recommendations = [
    {
      type: 'lesson',
      title: 'Creez votre premier devis',
      description: 'Apprenez a creer un devis en 5 minutes',
      duration: '5 min',
      xp: 50,
      icon: BookOpen,
      color: 'green',
    },
    {
      type: 'game',
      title: 'Quiz: Le CRM',
      description: 'Testez vos connaissances',
      duration: '3 min',
      xp: 30,
      icon: Gamepad2,
      color: 'purple',
    },
    {
      type: 'challenge',
      title: 'Defi du jour',
      description: 'Completez 3 taches dans le CRM',
      duration: '15 min',
      xp: 100,
      icon: Flame,
      color: 'orange',
    },
  ];

  return (
    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
      <div className="flex items-center gap-3 mb-4">
        <Sparkles className="w-6 h-6" />
        <h3 className="text-lg font-semibold">Recommande pour vous</h3>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {recommendations.map((rec, index) => (
          <div
            key={index}
            className="bg-white/10 backdrop-blur-sm rounded-lg p-4 hover:bg-white/20 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3 mb-2">
              <div className={`w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center`}>
                <rec.icon className="w-4 h-4" />
              </div>
              <span className="text-xs text-blue-200">{rec.duration}</span>
            </div>
            <h4 className="font-medium mb-1">{rec.title}</h4>
            <p className="text-sm text-blue-200 mb-3">{rec.description}</p>
            <div className="flex items-center gap-1 text-sm">
              <Zap className="w-4 h-4 text-amber-300" />
              <span className="text-amber-200">+{rec.xp} XP</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Recompense quotidienne
 */
function DailyReward({ claimed, onClaim }: { claimed: boolean; onClaim: () => void }) {
  return (
    <div className={`rounded-xl p-5 border-2 transition-all ${
      claimed
        ? 'bg-gray-50 border-gray-200'
        : 'bg-gradient-to-br from-amber-50 to-orange-50 border-amber-300 shadow-lg animate-pulse-slow'
    }`}>
      <div className="flex items-center gap-4">
        <div className={`w-16 h-16 rounded-xl flex items-center justify-center ${
          claimed ? 'bg-gray-200' : 'bg-gradient-to-br from-amber-400 to-orange-500'
        }`}>
          <Gift className={`w-8 h-8 ${claimed ? 'text-gray-400' : 'text-white'}`} />
        </div>
        <div className="flex-1">
          <h3 className={`font-semibold ${claimed ? 'text-gray-500' : 'text-gray-900'}`}>
            Recompense Quotidienne
          </h3>
          <p className={`text-sm ${claimed ? 'text-gray-400' : 'text-gray-600'}`}>
            {claimed ? 'Deja reclamee - revenez demain !' : 'Reclamez votre bonus du jour !'}
          </p>
          {!claimed && (
            <div className="flex items-center gap-2 mt-2">
              <span className="flex items-center gap-1 text-amber-600 font-medium">
                <Zap className="w-4 h-4" />
                +50 XP
              </span>
              <span className="flex items-center gap-1 text-amber-600 font-medium">
                <Flame className="w-4 h-4" />
                +1 Streak
              </span>
            </div>
          )}
        </div>
        {!claimed && (
          <button
            onClick={onClaim}
            className="px-6 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-medium hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg hover:shadow-xl"
          >
            Reclamer
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Selecteur de jeux (remplace GameCenter qui n'existe pas)
 */
function GameSelector() {
  const [selectedGame, setSelectedGame] = useState<string | null>(null);

  const games = [
    {
      id: 'quiz',
      title: 'Quiz Rapide',
      description: 'Testez vos connaissances sur AZALSCORE',
      icon: Target,
      color: 'blue',
    },
    {
      id: 'memory',
      title: 'Jeu de Memoire',
      description: 'Associez les fonctionnalites a leurs icones',
      icon: Sparkles,
      color: 'purple',
    },
    {
      id: 'matching',
      title: 'Association',
      description: 'Reliez les termes a leurs definitions',
      icon: Zap,
      color: 'amber',
    },
  ];

  const handleGameComplete = (result: string) => {
    console.log('Game completed:', result);
    setSelectedGame(null);
  };

  if (selectedGame === 'quiz') {
    return (
      <AnimatedQuiz
        questions={[
          {
            id: 'q1',
            question: 'Quel module permet de gerer les clients ?',
            options: ['Comptabilite', 'CRM', 'Stock', 'RH'],
            correctIndex: 1,
            explanation: 'Le CRM (Customer Relationship Management) est le module dedie a la gestion de la relation client.',
            points: 10,
            timeLimit: 30,
          },
          {
            id: 'q2',
            question: 'Comment creer une facture a partir d\'un devis ?',
            options: ['Menu Fichier', 'Bouton Transformer', 'Double-clic', 'Impossible'],
            correctIndex: 1,
            explanation: 'Le bouton "Transformer en facture" permet de convertir un devis valide en facture.',
            points: 10,
            timeLimit: 30,
          },
        ]}
        onComplete={(score, total) => handleGameComplete(`Score: ${score}/${total}`)}
      />
    );
  }

  if (selectedGame === 'memory') {
    return (
      <MemoryGame
        cards={[
          { id: 1, content: '📊' },
          { id: 2, content: '👥' },
          { id: 3, content: '📝' },
          { id: 4, content: '💰' },
        ]}
        onComplete={(moves, time) => handleGameComplete(`${moves} coups en ${time}s`)}
      />
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Gamepad2 className="w-5 h-5 text-purple-600" />
        Mini-Jeux Educatifs
      </h3>
      <div className="grid md:grid-cols-3 gap-4">
        {games.map((game) => (
          <button
            key={game.id}
            onClick={() => setSelectedGame(game.id)}
            className={`p-6 bg-white rounded-xl border-2 border-gray-200 hover:border-${game.color}-300 hover:shadow-lg transition-all text-left group`}
          >
            <div className={`w-12 h-12 rounded-xl bg-${game.color}-100 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
              <game.icon className={`w-6 h-6 text-${game.color}-600`} />
            </div>
            <h4 className="font-semibold text-gray-900 mb-1">{game.title}</h4>
            <p className="text-sm text-gray-600">{game.description}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// COMPOSANT PRINCIPAL
// ============================================================================

export function TrainingHub() {
  const [activeTab, setActiveTab] = useState('overview');
  const [dailyRewardClaimed, setDailyRewardClaimed] = useState(false);
  const [achievements, setAchievements] = useState(ACHIEVEMENTS);
  const [learningPaths, setLearningPaths] = useState(LEARNING_PATHS);

  // Simuler le chargement des donnees utilisateur
  useEffect(() => {
    const savedReward = localStorage.getItem('azalscore_daily_reward_claimed');
    if (savedReward) {
      const claimDate = new Date(savedReward);
      const today = new Date();
      if (claimDate.toDateString() === today.toDateString()) {
        setDailyRewardClaimed(true);
      }
    }
  }, []);

  const handleClaimReward = () => {
    setDailyRewardClaimed(true);
    localStorage.setItem('azalscore_daily_reward_claimed', new Date().toISOString());
  };

  const stats = [
    { label: 'Points XP', value: 1250, icon: Zap, color: 'amber', trend: '+120' },
    { label: 'Niveau', value: 5, icon: Star, color: 'purple' },
    { label: 'Streak', value: '7 jours', icon: Flame, color: 'orange' },
    { label: 'Badges', value: 12, icon: Award, color: 'blue' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* Daily Reward */}
            <DailyReward claimed={dailyRewardClaimed} onClaim={handleClaimReward} />

            {/* Quick Stats */}
            <QuickStats stats={stats} />

            {/* Recommendations */}
            <Recommendations />

            {/* Learning Paths */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-600" />
                Parcours d'Apprentissage
              </h3>
              <div className="grid md:grid-cols-2 gap-4">
                {learningPaths.slice(0, 2).map((path) => (
                  <LearningPathCard
                    key={path.id}
                    path={path}
                    onStart={() => console.log('Start path:', path.id)}
                  />
                ))}
              </div>
            </div>

            {/* Daily Challenges Preview */}
            <DailyChallengeCard
              challenge={MOCK_DAILY_CHALLENGE}
              onComplete={() => console.log('Challenge completed')}
            />
          </div>
        );

      case 'learning':
        return <MicroLearningLibrary />;

      case 'games':
        return <GameSelector />;

      case 'achievements':
        return (
          <div className="space-y-6">
            {/* Badges unlocked */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Trophy className="w-5 h-5 text-amber-500" />
                Vos Succes
              </h3>
              <AchievementsGrid achievements={achievements} />
            </div>

            {/* Badge collection */}
            <BadgeCollection badges={MOCK_BADGES} allBadges={ALL_BADGES} />
          </div>
        );

      case 'leaderboard':
        return <Leaderboard entries={MOCK_LEADERBOARD} />;

      default:
        return null;
    }
  };

  return (
    <GamificationProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
                  <GraduationCap className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">Centre de Formation</h1>
                  <p className="text-sm text-gray-500">Apprenez AZALSCORE en vous amusant</p>
                </div>
              </div>

              {/* Quick XP display */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 bg-amber-100 px-4 py-2 rounded-full">
                  <Zap className="w-5 h-5 text-amber-600" />
                  <span className="font-bold text-amber-700">1,250 XP</span>
                </div>
                <div className="flex items-center gap-2 bg-orange-100 px-4 py-2 rounded-full">
                  <Flame className="w-5 h-5 text-orange-600" />
                  <span className="font-bold text-orange-700">7</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav className="flex gap-1 overflow-x-auto py-2">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                    activeTab === tab.id
                      ? `bg-${tab.color}-100 text-${tab.color}-700`
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {renderTabContent()}
        </div>

        {/* Floating Action Button - Start Learning */}
        <button className="fixed bottom-6 right-6 flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-105 group">
          <Play className="w-5 h-5 group-hover:animate-pulse" />
          <span className="font-medium">Commencer</span>
        </button>
      </div>
    </GamificationProvider>
  );
}

export default TrainingHub;
