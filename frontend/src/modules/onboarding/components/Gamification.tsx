/**
 * AZALSCORE - Systeme de Gamification
 * ====================================
 * Formation ludique avec points, badges, niveaux et defis.
 * Support multi-langue (i18n)
 */

import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import {
  Trophy,
  Star,
  Zap,
  Target,
  Award,
  Flame,
  Gift,
  Crown,
  Rocket,
  Heart,
  TrendingUp,
  CheckCircle,
  Lock,
  Play,
  Sparkles,
  PartyPopper,
  Medal,
  Timer,
  Brain,
  Gamepad2,
  Dices,
  ChevronRight,
  GraduationCap,
  X,
  AlertTriangle,
  Lightbulb,
  BookOpen,
  BarChart3,
  HelpCircle,
  RefreshCw,
  FileQuestion,
  Globe,
} from 'lucide-react';

// Import i18n
import { useI18n, I18nProvider, LanguageSelector } from '../i18n';
import { getLevelExams, getPracticeQuizzes, getExamByLevel, getQuizById } from '../i18n/examQuestions';
import type { SupportedLanguage } from '../i18n';

// ============================================================================
// TYPES
// ============================================================================

interface UserGameProfile {
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

interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  unlockedAt?: string;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  progress: number;
  target: number;
  reward: number;
  completed: boolean;
}

interface Challenge {
  id: string;
  title: string;
  description: string;
  type: 'daily' | 'weekly' | 'special';
  difficulty: 'easy' | 'medium' | 'hard';
  xpReward: number;
  timeLimit?: number;
  tasks: ChallengeTask[];
  completed: boolean;
}

interface ChallengeTask {
  id: string;
  description: string;
  completed: boolean;
}

interface LeaderboardEntry {
  rank: number;
  userId: string;
  displayName: string;
  avatar: string;
  level: number;
  points: number;
  isCurrentUser?: boolean;
}

// ============================================================================
// TYPES - SYSTEME D'EXAMEN
// ============================================================================

interface ExamQuestion {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
  points: number;
  difficulty: 'facile' | 'moyen' | 'difficile';
}

interface LevelExam {
  level: number;
  title: string;
  description: string;
  duration: number; // en secondes
  passingScore: number; // pourcentage minimum pour reussir (ex: 70)
  questions: ExamQuestion[];
  xpReward: number;
  badgeReward?: string;
}

interface ExamResult {
  examLevel: number;
  score: number;
  totalPoints: number;
  maxPoints: number;
  percentage: number;
  passed: boolean;
  grade: 'A+' | 'A' | 'B' | 'C' | 'D' | 'F';
  timeSpent: number;
  correctAnswers: number;
  totalQuestions: number;
  xpEarned: number;
  completedAt: string;
}

interface PointsAction {
  id: string;
  action: string;
  points: number;
  category: 'apprentissage' | 'pratique' | 'social' | 'examen';
  icon: string;
}

// ============================================================================
// CONSTANTES
// ============================================================================

const LEVELS = [
  { level: 1, title: 'Debutant', xp: 0, color: 'gray' },
  { level: 2, title: 'Apprenti', xp: 100, color: 'green' },
  { level: 3, title: 'Initie', xp: 350, color: 'blue' },
  { level: 4, title: 'Competent', xp: 700, color: 'purple' },
  { level: 5, title: 'Expert', xp: 1200, color: 'orange' },
  { level: 6, title: 'Maitre', xp: 1800, color: 'red' },
  { level: 7, title: 'Champion', xp: 2800, color: 'yellow' },
  { level: 8, title: 'Legende', xp: 4500, color: 'pink' },
];

const BADGES: Badge[] = [
  { id: 'first-login', name: 'Premier Pas', description: 'Premiere connexion', icon: '🚀', rarity: 'common' },
  { id: 'explorer', name: 'Explorateur', description: 'Visite 5 modules', icon: '🗺️', rarity: 'common' },
  { id: 'fast-learner', name: 'Rapide', description: 'Complete une lecon en moins de 2 min', icon: '⚡', rarity: 'rare' },
  { id: 'perfect-quiz', name: 'Sans Faute', description: '100% a un quiz', icon: '💯', rarity: 'rare' },
  { id: 'streak-7', name: 'Assidu', description: '7 jours consecutifs', icon: '🔥', rarity: 'epic' },
  { id: 'all-modules', name: 'Completiste', description: 'Tous les modules termines', icon: '🏆', rarity: 'legendary' },
  { id: 'helper', name: 'Entraideur', description: 'Aide 3 collegues', icon: '🤝', rarity: 'rare' },
  { id: 'night-owl', name: 'Noctambule', description: 'Apprend apres 22h', icon: '🦉', rarity: 'common' },
  { id: 'early-bird', name: 'Matinal', description: 'Apprend avant 8h', icon: '🐦', rarity: 'common' },
  { id: 'speedster', name: 'Speedster', description: 'Complete 3 lecons en 1 jour', icon: '🏃', rarity: 'epic' },
];

const DAILY_CHALLENGES: Challenge[] = [
  {
    id: 'daily-1',
    title: 'Defi du Jour',
    description: 'Completez ces 3 taches pour gagner 50 XP',
    type: 'daily',
    difficulty: 'easy',
    xpReward: 50,
    completed: false,
    tasks: [
      { id: 't1', description: 'Se connecter', completed: true },
      { id: 't2', description: 'Completer 1 lecon', completed: false },
      { id: 't3', description: 'Repondre a 1 quiz', completed: false },
    ],
  },
  {
    id: 'daily-2',
    title: 'Speed Challenge',
    description: 'Terminez une lecon en moins de 3 minutes',
    type: 'daily',
    difficulty: 'medium',
    xpReward: 75,
    timeLimit: 180,
    completed: false,
    tasks: [
      { id: 't1', description: 'Completer la lecon rapidement', completed: false },
    ],
  },
];

// ============================================================================
// SYSTEME DE POINTS
// ============================================================================

const POINTS_ACTIONS: PointsAction[] = [
  // Apprentissage
  { id: 'complete-lesson', action: 'Completer une micro-lecon', points: 10, category: 'apprentissage', icon: '📚' },
  { id: 'watch-video', action: 'Regarder une video', points: 15, category: 'apprentissage', icon: '🎬' },
  { id: 'read-doc', action: 'Lire un document', points: 5, category: 'apprentissage', icon: '📖' },
  { id: 'complete-tour', action: 'Terminer un tour guide', points: 25, category: 'apprentissage', icon: '🗺️' },

  // Pratique
  { id: 'quiz-correct', action: 'Bonne reponse quiz', points: 5, category: 'pratique', icon: '✅' },
  { id: 'quiz-perfect', action: 'Quiz sans faute', points: 50, category: 'pratique', icon: '💯' },
  { id: 'game-win', action: 'Gagner un mini-jeu', points: 20, category: 'pratique', icon: '🎮' },
  { id: 'simulation-complete', action: 'Terminer une simulation', points: 30, category: 'pratique', icon: '🎯' },
  { id: 'daily-challenge', action: 'Defi quotidien', points: 50, category: 'pratique', icon: '⭐' },

  // Social
  { id: 'help-colleague', action: 'Aider un collegue', points: 25, category: 'social', icon: '🤝' },
  { id: 'share-tip', action: 'Partager une astuce', points: 10, category: 'social', icon: '💡' },
  { id: 'first-place', action: '1ere place classement', points: 100, category: 'social', icon: '🥇' },

  // Examens
  { id: 'exam-pass', action: 'Reussir un examen', points: 100, category: 'examen', icon: '🎓' },
  { id: 'exam-perfect', action: 'Examen note A+', points: 200, category: 'examen', icon: '🏆' },
  { id: 'level-up', action: 'Passage de niveau', points: 150, category: 'examen', icon: '⬆️' },
];

// ============================================================================
// EXAMENS DE PASSAGE DE NIVEAU
// ============================================================================

const LEVEL_EXAMS: LevelExam[] = [
  {
    level: 2,
    title: 'Examen Niveau 2 - Apprenti',
    description: 'Validez vos connaissances de base sur AZALSCORE',
    duration: 600, // 10 minutes
    passingScore: 60,
    xpReward: 150,
    badgeReward: 'exam-level-2',
    questions: [
      {
        id: 'l2-q1',
        question: 'Comment acceder rapidement a la recherche globale ?',
        options: ['Ctrl+F', 'Touche /', 'Ctrl+K', 'F3'],
        correctAnswer: 1,
        explanation: 'La touche "/" ouvre instantanement la barre de recherche globale.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q2',
        question: 'Quel prefixe utiliser pour rechercher un client ?',
        options: ['#', '@', '!', '$'],
        correctAnswer: 1,
        explanation: 'Le prefixe @ permet de rechercher specifiquement parmi les clients.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q3',
        question: 'Ou se trouve le menu principal de navigation ?',
        options: ['En haut', 'A gauche', 'A droite', 'En bas'],
        correctAnswer: 1,
        explanation: 'Le menu principal est situe dans la barre laterale gauche.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q4',
        question: 'Comment s\'appelle l\'assistant IA conversationnel d\'AZALSCORE ?',
        options: ['Alex', 'Theo', 'Max', 'Leo'],
        correctAnswer: 1,
        explanation: 'Theo est l\'assistant IA conversationnel d\'AZALSCORE.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q5',
        question: 'Que signifie le symbole * sur un champ de formulaire ?',
        options: ['Champ important', 'Champ obligatoire', 'Champ modifie', 'Nouveau champ'],
        correctAnswer: 1,
        explanation: 'L\'asterisque (*) indique un champ obligatoire a remplir.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q6',
        question: 'Quel prefixe utiliser pour rechercher un document ?',
        options: ['@', '#', '!', '&'],
        correctAnswer: 1,
        explanation: 'Le prefixe # permet de rechercher parmi les documents (devis, factures, etc.).',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q7',
        question: 'Comment acceder a votre profil utilisateur ?',
        options: ['Menu Parametres', 'Clic sur votre avatar en haut a droite', 'Touche P', 'Menu Aide'],
        correctAnswer: 1,
        explanation: 'Cliquez sur votre avatar en haut a droite pour acceder a votre profil.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q8',
        question: 'Ou trouver les notifications ?',
        options: ['Menu principal', 'Icone cloche en haut', 'Bas de l\'ecran', 'Onglet special'],
        correctAnswer: 1,
        explanation: 'Les notifications sont accessibles via l\'icone cloche dans la barre superieure.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q9',
        question: 'Comment reduire le menu lateral ?',
        options: ['Double-clic dessus', 'Bouton fleche sur le menu', 'Impossible', 'Touche Echap'],
        correctAnswer: 1,
        explanation: 'Le bouton fleche permet de reduire/etendre le menu lateral.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q10',
        question: 'Quel raccourci permet d\'ouvrir l\'aide ?',
        options: ['F1', '?', 'H', 'Ctrl+H'],
        correctAnswer: 1,
        explanation: 'La touche "?" ouvre le panneau d\'aide contextuelle.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q11',
        question: 'Comment changer la langue de l\'interface ?',
        options: ['Parametres > Langue', 'Profil > Preferences', 'Menu Aide', 'Impossible'],
        correctAnswer: 1,
        explanation: 'La langue se change dans Profil > Preferences.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l2-q12',
        question: 'Que represente l\'icone en forme de maison ?',
        options: ['Parametres', 'Accueil / Tableau de bord', 'Deconnexion', 'Aide'],
        correctAnswer: 1,
        explanation: 'L\'icone maison ramene toujours au tableau de bord principal.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q13',
        question: 'Comment rafraichir les donnees d\'une page ?',
        options: ['F5 uniquement', 'Bouton actualiser ou F5', 'Fermer et rouvrir', 'Attendre'],
        correctAnswer: 1,
        explanation: 'Utilisez le bouton actualiser dans l\'interface ou F5 pour rafraichir.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q14',
        question: 'Ou voir les actions recentes effectuees ?',
        options: ['Menu Historique', 'Journal d\'activite dans le profil', 'Notifications', 'Impossible'],
        correctAnswer: 1,
        explanation: 'Le journal d\'activite dans votre profil montre toutes vos actions recentes.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l2-q15',
        question: 'Comment contacter le support depuis AZALSCORE ?',
        options: ['Email externe', 'Bouton chat en bas a droite', 'Telephone uniquement', 'Impossible'],
        correctAnswer: 1,
        explanation: 'Le bouton chat en bas a droite permet de contacter le support directement.',
        points: 10,
        difficulty: 'facile',
      },
    ],
  },
  {
    level: 3,
    title: 'Examen Niveau 3 - Initie',
    description: 'Demontrez votre maitrise de la gestion commerciale',
    duration: 900, // 15 minutes
    passingScore: 65,
    xpReward: 250,
    badgeReward: 'exam-level-3',
    questions: [
      {
        id: 'l3-q1',
        question: 'Dans quel module cree-t-on un nouveau client ?',
        options: ['Facturation', 'CRM', 'Comptabilite', 'Stocks'],
        correctAnswer: 1,
        explanation: 'Le module CRM gere toutes les fiches clients et prospects.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q2',
        question: 'Quel est l\'ordre correct du cycle commercial ?',
        options: ['Facture > Devis > Commande', 'Devis > Commande > Facture', 'Commande > Devis > Facture', 'Devis > Facture > Commande'],
        correctAnswer: 1,
        explanation: 'Le cycle commercial suit : Devis > Commande > Facture.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q3',
        question: 'Combien de jours de validite par defaut pour un devis ?',
        options: ['15 jours', '30 jours', '45 jours', '60 jours'],
        correctAnswer: 1,
        explanation: 'Par defaut, un devis est valide 30 jours.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q4',
        question: 'Comment convertir un devis accepte en commande ?',
        options: ['Supprimer et recreer', 'Bouton "Convertir"', 'Export puis import', 'Copier-coller les lignes'],
        correctAnswer: 1,
        explanation: 'Le bouton "Convertir" permet de transformer un devis en commande.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q5',
        question: 'Ou consulter l\'historique des interactions avec un client ?',
        options: ['Menu Parametres', 'Onglet Historique de la fiche client', 'Module Rapports', 'Export Excel'],
        correctAnswer: 1,
        explanation: 'L\'onglet Historique de la fiche client montre toutes les interactions.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q6',
        question: 'Quelle information est obligatoire pour un client professionnel francais ?',
        options: ['Email', 'Telephone', 'SIRET', 'Site web'],
        correctAnswer: 2,
        explanation: 'Le SIRET est obligatoire pour les clients professionnels en France.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q7',
        question: 'Quelle est la difference entre un prospect et un client ?',
        options: ['Aucune difference', 'Le prospect n\'a pas encore achete', 'Le prospect est inactif', 'Le client est archive'],
        correctAnswer: 1,
        explanation: 'Un prospect devient client apres sa premiere commande/achat.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q8',
        question: 'Comment dupliquer un devis existant ?',
        options: ['Impossible', 'Menu Actions > Dupliquer', 'Copier-coller', 'Exporter/Importer'],
        correctAnswer: 1,
        explanation: 'Le menu Actions permet de dupliquer rapidement un devis.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q9',
        question: 'Quel statut indique qu\'un devis a ete envoye au client ?',
        options: ['Brouillon', 'Envoye', 'En attente', 'Valide'],
        correctAnswer: 1,
        explanation: 'Le statut "Envoye" indique que le devis a ete transmis au client.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q10',
        question: 'Comment ajouter une remise sur une ligne de devis ?',
        options: ['Modifier le prix unitaire', 'Colonne remise sur la ligne', 'Champ remise globale uniquement', 'Impossible'],
        correctAnswer: 1,
        explanation: 'Chaque ligne peut avoir sa propre remise dans la colonne dediee.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q11',
        question: 'Que se passe-t-il quand un devis expire ?',
        options: ['Il est supprime', 'Son statut passe a "Expire"', 'Il reste valide', 'Il est archive automatiquement'],
        correctAnswer: 1,
        explanation: 'Un devis expire change automatiquement de statut mais reste consultable.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q12',
        question: 'Comment envoyer un devis par email depuis AZALSCORE ?',
        options: ['Export PDF puis email externe', 'Bouton "Envoyer par email"', 'Impossible directement', 'Uniquement via Outlook'],
        correctAnswer: 1,
        explanation: 'Le bouton "Envoyer par email" permet l\'envoi direct depuis l\'application.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q13',
        question: 'Ou definir les conditions de paiement par defaut ?',
        options: ['Sur chaque devis', 'Parametres > Commercial', 'Fiche client', 'Impossible'],
        correctAnswer: 1,
        explanation: 'Les conditions par defaut se definissent dans Parametres > Commercial.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q14',
        question: 'Combien de contacts peut-on associer a un client ?',
        options: ['Un seul', 'Maximum 5', 'Maximum 10', 'Illimite'],
        correctAnswer: 3,
        explanation: 'Il n\'y a pas de limite au nombre de contacts par client.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q15',
        question: 'Comment archiver un client inactif ?',
        options: ['Le supprimer', 'Menu Actions > Archiver', 'Changer son statut', 'Impossible'],
        correctAnswer: 1,
        explanation: 'L\'archivage permet de conserver l\'historique tout en masquant le client.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q16',
        question: 'Que signifie le statut "Commande confirmee" ?',
        options: ['Le client a signe', 'Le devis est accepte et converti', 'La livraison est faite', 'Le paiement est recu'],
        correctAnswer: 1,
        explanation: 'Une commande confirmee signifie que le client a valide et qu\'elle peut etre traitee.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q17',
        question: 'Comment ajouter une note interne sur un devis ?',
        options: ['Dans le champ description', 'Onglet Notes', 'Commentaire en bas', 'Impossible'],
        correctAnswer: 1,
        explanation: 'L\'onglet Notes permet d\'ajouter des informations internes non visibles du client.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q18',
        question: 'Quel module permet de gerer les relances clients ?',
        options: ['CRM', 'Comptabilite', 'Les deux', 'Module Relances dedie'],
        correctAnswer: 2,
        explanation: 'Les relances commerciales sont dans le CRM, les relances paiement en Comptabilite.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l3-q19',
        question: 'Comment voir tous les devis en attente de reponse ?',
        options: ['Recherche manuelle', 'Filtre "Statut = Envoye"', 'Tableau de bord uniquement', 'Impossible'],
        correctAnswer: 1,
        explanation: 'Le filtre par statut permet de lister tous les devis en attente.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l3-q20',
        question: 'Quelle action declenche la generation d\'un numero de facture ?',
        options: ['Creation de la facture', 'Validation de la facture', 'Envoi de la facture', 'Paiement recu'],
        correctAnswer: 1,
        explanation: 'Le numero de facture est genere lors de la validation (pas en brouillon).',
        points: 15,
        difficulty: 'moyen',
      },
    ],
  },
  {
    level: 4,
    title: 'Examen Niveau 4 - Competent',
    description: 'Prouvez votre expertise en gestion financiere et stocks',
    duration: 1200, // 20 minutes
    passingScore: 70,
    xpReward: 400,
    badgeReward: 'exam-level-4',
    questions: [
      {
        id: 'l4-q1',
        question: 'Dans quel journal comptabilise-t-on une facture de vente ?',
        options: ['Journal des achats (AC)', 'Journal des ventes (VE)', 'Journal de banque (BQ)', 'Journal OD'],
        correctAnswer: 1,
        explanation: 'Les factures de vente sont comptabilisees dans le journal des ventes (VE).',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l4-q2',
        question: 'Qu\'est-ce que le rapprochement bancaire ?',
        options: ['Comparer deux banques', 'Verifier la concordance comptabilite/releve bancaire', 'Transferer de l\'argent', 'Cloturer un compte'],
        correctAnswer: 1,
        explanation: 'Le rapprochement bancaire verifie que le solde comptable correspond au releve bancaire.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q3',
        question: 'Quel compte utilise-t-on pour les ventes de marchandises ?',
        options: ['401 Fournisseurs', '411 Clients', '707 Ventes de marchandises', '512 Banque'],
        correctAnswer: 2,
        explanation: 'Le compte 707 "Ventes de marchandises" enregistre le chiffre d\'affaires.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l4-q4',
        question: 'Que represente une ecriture comptable equilibree ?',
        options: ['Debit superieur au Credit', 'Debit inferieur au Credit', 'Debit egal au Credit', 'Pas de relation'],
        correctAnswer: 2,
        explanation: 'En comptabilite en partie double, chaque ecriture doit avoir Debit = Credit.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q5',
        question: 'Comment creer un avoir client ?',
        options: ['Facture avec montant negatif', 'Supprimer la facture', 'Depuis la facture > Creer avoir', 'Modifier la facture'],
        correctAnswer: 2,
        explanation: 'Un avoir se cree depuis la facture originale pour garder la tracabilite.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q6',
        question: 'Quel est le taux de TVA standard en France ?',
        options: ['10%', '15%', '20%', '25%'],
        correctAnswer: 2,
        explanation: 'Le taux normal de TVA en France est de 20%.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l4-q7',
        question: 'Ou visualiser la tresorerie previsionnelle ?',
        options: ['Module Comptabilite uniquement', 'Cockpit Dirigeant', 'CRM', 'Parametres'],
        correctAnswer: 1,
        explanation: 'Le Cockpit Dirigeant affiche les previsions de tresorerie avec graphiques.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q8',
        question: 'Quel compte represente la banque ?',
        options: ['401', '411', '607', '512'],
        correctAnswer: 3,
        explanation: 'Le compte 512 represente les comptes bancaires de l\'entreprise.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q9',
        question: 'Comment lettrer une facture avec son paiement ?',
        options: ['Automatique a la saisie', 'Selection des ecritures > Lettrer', 'Impossible manuellement', 'Module separe'],
        correctAnswer: 1,
        explanation: 'Le lettrage manuel se fait en selectionnant les ecritures correspondantes.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q10',
        question: 'Que signifie TVA deductible ?',
        options: ['TVA a payer', 'TVA recuperable sur les achats', 'TVA exoneree', 'TVA a credit'],
        correctAnswer: 1,
        explanation: 'La TVA deductible est celle payee sur les achats et recuperable aupres de l\'Etat.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l4-q11',
        question: 'Comment gerer les echeances de paiement fournisseur ?',
        options: ['Manuellement dans un tableau', 'Module Tresorerie > Echeancier', 'Export vers Excel', 'Notifications email uniquement'],
        correctAnswer: 1,
        explanation: 'L\'echeancier du module Tresorerie centralise toutes les echeances.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q12',
        question: 'Quel document permet d\'enregistrer une entree en stock ?',
        options: ['Facture d\'achat', 'Bon de reception', 'Commande fournisseur', 'Devis'],
        correctAnswer: 1,
        explanation: 'Le bon de reception valide l\'entree physique des marchandises en stock.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l4-q13',
        question: 'Comment calculer le stock disponible ?',
        options: ['Stock physique uniquement', 'Stock physique - Reserves', 'Stock physique + Commandes', 'Automatique'],
        correctAnswer: 1,
        explanation: 'Le stock disponible = stock physique moins les quantites reservees.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q14',
        question: 'Qu\'est-ce qu\'une immobilisation ?',
        options: ['Stock bloque', 'Bien durable utilise sur plusieurs annees', 'Tresorerie immobilisee', 'Facture impayee'],
        correctAnswer: 1,
        explanation: 'Une immobilisation est un actif durable (materiel, vehicule, etc.) amorti sur plusieurs annees.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l4-q15',
        question: 'Comment enregistrer une note de frais ?',
        options: ['Module Comptabilite direct', 'Module RH > Notes de frais', 'Demander au comptable', 'Impossible dans AZALSCORE'],
        correctAnswer: 1,
        explanation: 'Les notes de frais se saisissent dans le module RH puis sont validees et comptabilisees.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q16',
        question: 'Que represente le compte 401 ?',
        options: ['Clients', 'Fournisseurs', 'Banque', 'Capital'],
        correctAnswer: 1,
        explanation: 'Le compte 401 enregistre les dettes envers les fournisseurs.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q17',
        question: 'Comment generer la declaration de TVA ?',
        options: ['Manuellement', 'Module Comptabilite > Declarations > TVA', 'Export vers logiciel fiscal', 'Automatique mensuel'],
        correctAnswer: 1,
        explanation: 'La declaration TVA se genere depuis le module Comptabilite > Declarations.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l4-q18',
        question: 'Qu\'est-ce qu\'un inventaire tournant ?',
        options: ['Inventaire annuel', 'Comptage partiel regulier du stock', 'Rotation des produits', 'Inventaire automatique'],
        correctAnswer: 1,
        explanation: 'L\'inventaire tournant consiste a compter regulierement une partie du stock.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q19',
        question: 'Comment traiter un ecart d\'inventaire ?',
        options: ['Ignorer', 'Ajustement de stock avec justificatif', 'Modifier l\'historique', 'Supprimer les mouvements'],
        correctAnswer: 1,
        explanation: 'Les ecarts doivent etre regularises par un ajustement de stock documente.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q20',
        question: 'Quel rapport montre la rentabilite par produit ?',
        options: ['Balance', 'Grand Livre', 'Analyse des marges', 'Journal'],
        correctAnswer: 2,
        explanation: 'L\'analyse des marges montre la rentabilite de chaque produit ou famille.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q21',
        question: 'Comment gerer plusieurs entrepots ?',
        options: ['Impossible', 'Parametres > Entrepots', 'Un seul par defaut', 'Module separe payant'],
        correctAnswer: 1,
        explanation: 'AZALSCORE supporte plusieurs entrepots configurables dans les parametres.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q22',
        question: 'Qu\'est-ce que le seuil de reapprovisionnement ?',
        options: ['Stock maximum', 'Quantite declenchant une commande', 'Prix minimum', 'Delai de livraison'],
        correctAnswer: 1,
        explanation: 'Le seuil de reapprovisionnement declenche une alerte ou commande automatique.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q23',
        question: 'Comment suivre les lots et numeros de serie ?',
        options: ['Notes manuelles', 'Tracabilite activee sur le produit', 'Impossible', 'Module externe'],
        correctAnswer: 1,
        explanation: 'La tracabilite par lot/serie s\'active dans la fiche produit.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l4-q24',
        question: 'Quel taux de TVA s\'applique aux produits alimentaires de base ?',
        options: ['5.5%', '10%', '20%', '0%'],
        correctAnswer: 0,
        explanation: 'Les produits alimentaires de premiere necessite sont a 5.5% de TVA.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q25',
        question: 'Comment cloturer un exercice comptable ?',
        options: ['Automatique au 31/12', 'Comptabilite > Cloture exercice', 'Demander au support', 'Export puis nouveau fichier'],
        correctAnswer: 1,
        explanation: 'La cloture se fait manuellement apres verification de toutes les ecritures.',
        points: 25,
        difficulty: 'difficile',
      },
    ],
  },
  {
    level: 5,
    title: 'Examen Niveau 5 - Expert',
    description: 'Demontrez une maitrise avancee d\'AZALSCORE',
    duration: 1500, // 25 minutes
    passingScore: 75,
    xpReward: 600,
    badgeReward: 'exam-level-5',
    questions: [
      {
        id: 'l5-q1',
        question: 'Comment creer un workflow automatise ?',
        options: ['Module Parametres > Workflows', 'Demander au support', 'Ce n\'est pas possible', 'Module CRM > Automatisations'],
        correctAnswer: 0,
        explanation: 'Les workflows se configurent dans Parametres > Workflows avec un editeur visuel.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q2',
        question: 'Quelle est la difference entre Theo et Marceau ?',
        options: ['Theo est plus rapide', 'Theo est conversationnel, Marceau execute des actions', 'Marceau est plus ancien', 'Aucune difference'],
        correctAnswer: 1,
        explanation: 'Theo repond aux questions, Marceau est l\'agent autonome qui execute des taches complexes.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q3',
        question: 'Comment programmer une tache recurrente ?',
        options: ['Module Taches > Planifier', 'Calendrier > Recurrence', 'Ce n\'est pas supporte', 'Demander a Theo'],
        correctAnswer: 0,
        explanation: 'Le module Taches permet de planifier des taches recurrentes avec expressions cron.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q4',
        question: 'Quel format d\'export est le plus adapte pour Excel ?',
        options: ['PDF', 'CSV', 'JSON', 'XML'],
        correctAnswer: 1,
        explanation: 'Le format CSV s\'ouvre directement dans Excel avec formatage automatique.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l5-q5',
        question: 'Comment definir des droits d\'acces personnalises ?',
        options: ['Impossible sans admin systeme', 'Parametres > Roles et Permissions', 'Contacter le support', 'Fichier de configuration'],
        correctAnswer: 1,
        explanation: 'Les roles et permissions se gerent dans Parametres > Roles et Permissions.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q6',
        question: 'Quelles API de paiement AZALSCORE supporte-t-il ?',
        options: ['PayPal uniquement', 'Stripe uniquement', 'PayPal, Stripe et GoCardless', 'Aucune'],
        correctAnswer: 2,
        explanation: 'AZALSCORE supporte PayPal, Stripe et GoCardless pour les paiements en ligne.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q7',
        question: 'Comment generer un rapport personnalise ?',
        options: ['Module BI > Nouveau rapport', 'Export Excel puis modification', 'Contacter le support', 'Impossible'],
        correctAnswer: 0,
        explanation: 'Le module Business Intelligence permet de creer des rapports personnalises avec drag-and-drop.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q8',
        question: 'Quel est l\'avantage du mode hors-ligne ?',
        options: ['Interface plus rapide', 'Travail sans connexion internet', 'Economie de batterie', 'Securite renforcee'],
        correctAnswer: 1,
        explanation: 'Le mode hors-ligne permet de continuer a travailler sans internet puis de synchroniser.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q9',
        question: 'Comment configurer une integration avec un logiciel tiers ?',
        options: ['Impossible', 'API REST documentee', 'Uniquement via support', 'Webhooks seulement'],
        correctAnswer: 1,
        explanation: 'AZALSCORE offre une API REST complete et documentee pour les integrations.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q10',
        question: 'Qu\'est-ce qu\'un webhook dans AZALSCORE ?',
        options: ['Type de rapport', 'Notification HTTP vers une URL externe', 'Widget du dashboard', 'Outil de debug'],
        correctAnswer: 1,
        explanation: 'Les webhooks envoient des notifications HTTP a des systemes externes lors d\'evenements.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q11',
        question: 'Comment activer l\'authentification a deux facteurs ?',
        options: ['Par defaut active', 'Profil > Securite > 2FA', 'Demander a l\'admin', 'Non disponible'],
        correctAnswer: 1,
        explanation: 'Le 2FA s\'active dans les parametres de securite du profil utilisateur.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q12',
        question: 'Quel est le role du module GMAO ?',
        options: ['Gestion des achats', 'Maintenance des equipements', 'Marketing automatise', 'Gestion documentaire'],
        correctAnswer: 1,
        explanation: 'La GMAO (Gestion de Maintenance Assistee par Ordinateur) gere la maintenance des equipements.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q13',
        question: 'Comment creer un template d\'email personnalise ?',
        options: ['Parametres > Templates > Emails', 'HTML dans chaque email', 'Impossible', 'Module Marketing uniquement'],
        correctAnswer: 0,
        explanation: 'Les templates email se gerent centralement dans Parametres > Templates.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q14',
        question: 'Qu\'est-ce que le scoring client dans le CRM ?',
        options: ['Note de satisfaction', 'Score de priorite base sur le comportement', 'Evaluation du risque', 'Classement alphabetique'],
        correctAnswer: 1,
        explanation: 'Le scoring attribue automatiquement une note basee sur les interactions et le potentiel.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q15',
        question: 'Comment configurer des alertes automatiques ?',
        options: ['Notifications systeme uniquement', 'Parametres > Alertes avec conditions', 'Demander au support', 'Via l\'API seulement'],
        correctAnswer: 1,
        explanation: 'Les alertes se configurent avec des conditions dans Parametres > Alertes.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q16',
        question: 'Quel module gere les interventions terrain ?',
        options: ['CRM', 'Helpdesk', 'Interventions/FSM', 'GMAO'],
        correctAnswer: 2,
        explanation: 'Le module Interventions (Field Service Management) gere les interventions terrain.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q17',
        question: 'Comment importer des donnees en masse ?',
        options: ['Saisie manuelle uniquement', 'Import CSV/Excel dans chaque module', 'API uniquement', 'Support technique requis'],
        correctAnswer: 1,
        explanation: 'Chaque module propose une fonction d\'import CSV/Excel avec mapping des colonnes.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q18',
        question: 'Qu\'est-ce que le multi-tenant dans AZALSCORE ?',
        options: ['Multi-utilisateur', 'Plusieurs bases de donnees separees par client', 'Multi-ecran', 'Multi-langue'],
        correctAnswer: 1,
        explanation: 'Le multi-tenant permet d\'heberger plusieurs entreprises avec des donnees isolees.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q19',
        question: 'Comment configurer le SSO (Single Sign-On) ?',
        options: ['Parametres > Securite > SSO', 'Impossible', 'Via l\'API uniquement', 'Forfait Premium requis'],
        correctAnswer: 0,
        explanation: 'Le SSO (SAML/OAuth) se configure dans Parametres > Securite > SSO.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q20',
        question: 'Quel est l\'avantage des champs personnalises ?',
        options: ['Esthetique', 'Adapter AZALSCORE aux besoins specifiques', 'Performance', 'Securite'],
        correctAnswer: 1,
        explanation: 'Les champs personnalises permettent d\'adapter les formulaires aux besoins metier.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q21',
        question: 'Comment auditer les actions des utilisateurs ?',
        options: ['Impossible', 'Parametres > Audit > Journal', 'Demander au support', 'Via l\'API'],
        correctAnswer: 1,
        explanation: 'Le journal d\'audit enregistre toutes les actions avec horodatage et utilisateur.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q22',
        question: 'Qu\'est-ce que le Rate Limiting dans l\'API ?',
        options: ['Tarification', 'Limitation du nombre de requetes', 'Classement', 'Compression'],
        correctAnswer: 1,
        explanation: 'Le rate limiting protege l\'API en limitant le nombre de requetes par periode.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q23',
        question: 'Comment sauvegarder les donnees AZALSCORE ?',
        options: ['Automatique quotidien', 'Parametres > Sauvegarde', 'Export manuel uniquement', 'Via l\'hebergeur'],
        correctAnswer: 0,
        explanation: 'Les sauvegardes sont automatiques et quotidiennes, avec retention configurable.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q24',
        question: 'Quel protocole securise les communications API ?',
        options: ['HTTP', 'HTTPS avec TLS 1.3', 'FTP', 'SSH'],
        correctAnswer: 1,
        explanation: 'Toutes les communications API utilisent HTTPS avec TLS 1.3 minimum.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q25',
        question: 'Comment gerer les conges des employes ?',
        options: ['Module RH > Conges', 'Calendrier partage', 'Email au manager', 'Application externe'],
        correctAnswer: 0,
        explanation: 'Le module RH > Conges gere les demandes, validations et soldes de conges.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l5-q26',
        question: 'Qu\'est-ce qu\'une nomenclature de production ?',
        options: ['Liste de prix', 'Liste des composants d\'un produit fini', 'Catalogue produits', 'Bon de commande'],
        correctAnswer: 1,
        explanation: 'La nomenclature (BOM) liste tous les composants necessaires pour fabriquer un produit.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q27',
        question: 'Comment definir des SLA dans le helpdesk ?',
        options: ['Non supporte', 'Helpdesk > Parametres > SLA', 'Par ticket manuellement', 'Via l\'API'],
        correctAnswer: 1,
        explanation: 'Les SLA (Service Level Agreements) se definissent dans les parametres du helpdesk.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q28',
        question: 'Quel module permet la signature electronique ?',
        options: ['Documents', 'CRM', 'Tous les documents commerciaux', 'Non disponible'],
        correctAnswer: 2,
        explanation: 'La signature electronique est disponible sur tous les documents commerciaux.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q29',
        question: 'Comment creer un portail client ?',
        options: ['Parametres > Portail Client', 'Module separe', 'Developpement sur mesure', 'Non disponible'],
        correctAnswer: 0,
        explanation: 'Le portail client se configure dans Parametres > Portail Client avec les droits d\'acces.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q30',
        question: 'Quelle certification de securite AZALSCORE possede-t-il ?',
        options: ['Aucune', 'ISO 27001', 'PCI-DSS uniquement', 'SOC 2 uniquement'],
        correctAnswer: 1,
        explanation: 'AZALSCORE est certifie ISO 27001 pour la securite de l\'information.',
        points: 15,
        difficulty: 'moyen',
      },
    ],
  },
  {
    level: 6,
    title: 'Examen Niveau 6 - Maitre',
    description: 'Prouvez votre expertise complete sur AZALSCORE',
    duration: 1800, // 30 minutes
    passingScore: 80,
    xpReward: 800,
    badgeReward: 'exam-level-6',
    questions: [
      {
        id: 'l6-q1',
        question: 'Comment optimiser les performances d\'une requete BI complexe ?',
        options: ['Augmenter le timeout', 'Utiliser des vues materialisees et index', 'Reduire les donnees manuellement', 'Impossible'],
        correctAnswer: 1,
        explanation: 'Les vues materialisees et index optimisent les requetes BI complexes.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q2',
        question: 'Quelle est la strategie de backup recommandee ?',
        options: ['Quotidien suffit', '3-2-1 : 3 copies, 2 supports, 1 hors site', 'Mensuel', 'A la demande'],
        correctAnswer: 1,
        explanation: 'La strategie 3-2-1 assure une protection optimale des donnees.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q3',
        question: 'Comment implementer un processus d\'approbation multi-niveaux ?',
        options: ['Manuellement par email', 'Workflows > Approbations avec conditions', 'Non supporte', 'Plugin externe'],
        correctAnswer: 1,
        explanation: 'Les workflows permettent de definir des chaines d\'approbation conditionnelles.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q4',
        question: 'Qu\'est-ce que l\'architecture microservices d\'AZALSCORE ?',
        options: ['Monolithique', 'Services independants communiquant via API', 'Base de donnees unique', 'Architecture legacy'],
        correctAnswer: 1,
        explanation: 'AZALSCORE utilise des microservices independants pour scalabilite et resilience.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q5',
        question: 'Comment configurer le load balancing ?',
        options: ['Automatique cloud', 'Infrastructure > Load Balancer', 'Non necessaire', 'Support devops'],
        correctAnswer: 0,
        explanation: 'Le load balancing est automatique dans l\'environnement cloud AZALSCORE.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q6',
        question: 'Quel mecanisme assure la coherence des donnees en multi-tenant ?',
        options: ['Locks database', 'Row Level Security (RLS)', 'Application seule', 'Pas de mecanisme'],
        correctAnswer: 1,
        explanation: 'Le Row Level Security garantit l\'isolation des donnees entre tenants au niveau base.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q7',
        question: 'Comment debugger un workflow qui echoue ?',
        options: ['Logs systeme uniquement', 'Workflows > Historique > Details execution', 'Recrer le workflow', 'Contacter le dev'],
        correctAnswer: 1,
        explanation: 'L\'historique d\'execution montre chaque etape avec les erreurs detaillees.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q8',
        question: 'Quelle methode d\'authentification API est la plus securisee ?',
        options: ['API Key simple', 'OAuth 2.0 avec JWT', 'Basic Auth', 'Session cookie'],
        correctAnswer: 1,
        explanation: 'OAuth 2.0 avec JWT offre la meilleure securite avec tokens a duree limitee.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q9',
        question: 'Comment gerer la conformite RGPD dans AZALSCORE ?',
        options: ['Manuel', 'Parametres > Conformite > RGPD avec outils dedies', 'Non concerne', 'Consultant externe'],
        correctAnswer: 1,
        explanation: 'AZALSCORE inclut des outils RGPD : consentement, export, anonymisation, retention.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q10',
        question: 'Qu\'est-ce que le CDC (Change Data Capture) ?',
        options: ['Sauvegarde', 'Capture des modifications pour synchronisation temps reel', 'Compression', 'Chiffrement'],
        correctAnswer: 1,
        explanation: 'Le CDC capture les modifications pour les repliquer vers d\'autres systemes en temps reel.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q11',
        question: 'Comment monitorer les performances en production ?',
        options: ['Logs manuels', 'Dashboard monitoring avec alertes', 'Tests periodiques', 'Feedback utilisateurs'],
        correctAnswer: 1,
        explanation: 'Le dashboard monitoring affiche les metriques temps reel avec alertes automatiques.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q12',
        question: 'Quelle strategie de migration de donnees recommandez-vous ?',
        options: ['Big bang', 'Migration incrementale avec validation', 'Copier-coller', 'Saisie manuelle'],
        correctAnswer: 1,
        explanation: 'La migration incrementale permet de valider chaque lot avant de continuer.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q13',
        question: 'Comment etendre AZALSCORE avec du code personnalise ?',
        options: ['Impossible', 'Plugins/Extensions avec API et hooks', 'Fork du code', 'Demande speciale'],
        correctAnswer: 1,
        explanation: 'Le systeme de plugins permet d\'etendre AZALSCORE sans modifier le code source.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q14',
        question: 'Qu\'est-ce que le circuit breaker pattern ?',
        options: ['Protection electrique', 'Pattern qui isole les services defaillants', 'Authentification', 'Compression'],
        correctAnswer: 1,
        explanation: 'Le circuit breaker empeche les appels vers un service defaillant pour eviter la cascade.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q15',
        question: 'Comment configurer la haute disponibilite ?',
        options: ['Un seul serveur suffit', 'Cluster avec replication et failover', 'Sauvegarde frequente', 'Non supporte'],
        correctAnswer: 1,
        explanation: 'La haute disponibilite requiert un cluster avec replication et basculement automatique.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q16',
        question: 'Quel outil utiliser pour les tests de charge ?',
        options: ['Tests manuels', 'Outils integres ou JMeter/k6', 'Non necessaire', 'Uniquement en dev'],
        correctAnswer: 1,
        explanation: 'Les tests de charge avec JMeter ou k6 valident les performances sous stress.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q17',
        question: 'Comment gerer les versions d\'API ?',
        options: ['Pas de versioning', 'URL versionnee (/v1/, /v2/)', 'Header uniquement', 'Automatique'],
        correctAnswer: 1,
        explanation: 'Le versioning par URL permet une transition progressive entre versions.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q18',
        question: 'Qu\'est-ce que l\'eventual consistency ?',
        options: ['Coherence immediate', 'Coherence atteinte apres un delai', 'Incoherence permanente', 'Terme marketing'],
        correctAnswer: 1,
        explanation: 'L\'eventual consistency garantit la coherence apres propagation, pas instantanement.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q19',
        question: 'Comment securiser les secrets et cles API ?',
        options: ['Fichier config', 'Vault/Secret Manager avec rotation', 'Variables environnement', 'Base de donnees'],
        correctAnswer: 1,
        explanation: 'Un vault avec rotation automatique est la methode la plus securisee.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q20',
        question: 'Quelle est la retention par defaut des logs d\'audit ?',
        options: ['30 jours', '90 jours', '1 an', '7 ans'],
        correctAnswer: 3,
        explanation: 'Les logs d\'audit sont conserves 7 ans pour conformite legale.',
        points: 20,
        difficulty: 'difficile',
      },
    ],
  },
  {
    level: 7,
    title: 'Examen Niveau 7 - Champion',
    description: 'Certification finale - Devenez un expert certifie AZALSCORE',
    duration: 2400, // 40 minutes
    passingScore: 85,
    xpReward: 1000,
    badgeReward: 'exam-level-7-champion',
    questions: [
      {
        id: 'l7-q1',
        question: 'Quel pattern architectural AZALSCORE utilise-t-il pour la communication inter-services ?',
        options: ['RPC synchrone', 'Event-driven avec message broker', 'Fichiers partages', 'Base de donnees commune'],
        correctAnswer: 1,
        explanation: 'AZALSCORE utilise un pattern event-driven avec RabbitMQ/Redis pour la communication asynchrone.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q2',
        question: 'Comment implementer une strategie de retry avec backoff exponentiel ?',
        options: ['Boucle while', 'Configuration dans les workflows avec parametres retry', 'Plugin externe', 'Manuellement'],
        correctAnswer: 1,
        explanation: 'Les workflows supportent nativement le retry avec backoff exponentiel configurable.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q3',
        question: 'Qu\'est-ce que le CQRS et comment l\'utiliser dans AZALSCORE ?',
        options: ['Protocole reseau', 'Separation lecture/ecriture via Module BI pour queries', 'Cache Redis', 'Compression'],
        correctAnswer: 1,
        explanation: 'CQRS separe les commandes des queries - le module BI utilise des modeles de lecture optimises.',
        points: 35,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q4',
        question: 'Comment gerer les transactions distribuees entre microservices ?',
        options: ['Transaction SQL classique', 'Pattern Saga avec compensation', 'Ignorer la coherence', 'Locks globaux'],
        correctAnswer: 1,
        explanation: 'Le pattern Saga orchestre des transactions distribuees avec actions de compensation.',
        points: 35,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q5',
        question: 'Quelle strategie de deploiement minimise les temps d\'arret ?',
        options: ['Recreate', 'Blue-Green ou Canary deployment', 'Manuel apres heures', 'Hot reload'],
        correctAnswer: 1,
        explanation: 'Blue-Green et Canary permettent des deploiements sans interruption de service.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q6',
        question: 'Comment optimiser les requetes N+1 dans les rapports ?',
        options: ['Augmenter la memoire', 'Utiliser les jointures et eager loading', 'Pagination', 'Cache uniquement'],
        correctAnswer: 1,
        explanation: 'Les jointures SQL et eager loading evitent les requetes N+1 en chargeant les relations en une fois.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q7',
        question: 'Quel mecanisme assure l\'idempotence des operations API ?',
        options: ['Cache', 'Idempotency-Key header avec stockage', 'Retry automatique', 'Timestamps'],
        correctAnswer: 1,
        explanation: 'Le header Idempotency-Key permet de rejouer une requete sans effet de bord.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q8',
        question: 'Comment implementer le rate limiting distribue ?',
        options: ['Variable en memoire', 'Redis avec algorithme token bucket', 'Base de donnees', 'Load balancer seul'],
        correctAnswer: 1,
        explanation: 'Redis avec token bucket ou sliding window assure un rate limiting coherent entre instances.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q9',
        question: 'Quelle approche pour la gestion des secrets en production ?',
        options: ['Variables env', 'HashiCorp Vault avec rotation automatique', 'Fichier .env', 'Config serveur'],
        correctAnswer: 1,
        explanation: 'Vault avec rotation automatique est la solution la plus securisee en production.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q10',
        question: 'Comment assurer la tracabilite complete d\'une transaction metier ?',
        options: ['Logs standards', 'Distributed tracing avec correlation ID', 'Timestamps', 'Notifications'],
        correctAnswer: 1,
        explanation: 'Le distributed tracing avec correlation ID permet de suivre une requete a travers tous les services.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q11',
        question: 'Quel est le role du service mesh dans l\'architecture ?',
        options: ['Base de donnees', 'Gestion du trafic, securite et observabilite inter-services', 'Frontend', 'Cache'],
        correctAnswer: 1,
        explanation: 'Le service mesh (Istio/Linkerd) gere le trafic, mTLS et metriques entre services.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q12',
        question: 'Comment gerer les migrations de schema sans downtime ?',
        options: ['Arreter le service', 'Migrations compatibles backward avec expand-contract', 'Script manuel', 'Ignorer'],
        correctAnswer: 1,
        explanation: 'Le pattern expand-contract permet des migrations incrementales sans casser la compatibilite.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q13',
        question: 'Quelle strategie de partitionnement pour les grandes tables ?',
        options: ['Aucune', 'Partitionnement par date ou tenant_id', 'Archivage manuel', 'Plusieurs bases'],
        correctAnswer: 1,
        explanation: 'Le partitionnement par date ou tenant optimise les performances sur grandes tables.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q14',
        question: 'Comment implementer le feature flagging ?',
        options: ['Commentaires code', 'Systeme de flags avec evaluation temps reel', 'Branches Git', 'Configuration'],
        correctAnswer: 1,
        explanation: 'Les feature flags permettent d\'activer/desactiver des fonctionnalites sans deploiement.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q15',
        question: 'Quel pattern pour gerer la charge lors des pics ?',
        options: ['Ignorer', 'Auto-scaling avec queue de messages', 'Serveur plus gros', 'Bloquer les requetes'],
        correctAnswer: 1,
        explanation: 'L\'auto-scaling horizontal avec bufferisation par queue absorbe les pics de charge.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q16',
        question: 'Comment garantir la delivrabilite des emails transactionnels ?',
        options: ['SMTP direct', 'Service dedie avec SPF/DKIM/DMARC et suivi', 'Gmail', 'Pas de garantie'],
        correctAnswer: 1,
        explanation: 'Un service email dedie avec authentification DNS assure la delivrabilite.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q17',
        question: 'Quelle approche pour les tests en environnement de production ?',
        options: ['Jamais', 'Feature flags + synthetic monitoring + canary', 'Tests manuels', 'Copie de prod'],
        correctAnswer: 1,
        explanation: 'Feature flags et synthetic monitoring permettent des tests securises en production.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q18',
        question: 'Comment gerer les dependances circulaires entre services ?',
        options: ['Acceptable', 'Refactoring avec event sourcing ou service intermediaire', 'Ignorer', 'Timeout'],
        correctAnswer: 1,
        explanation: 'Les dependances circulaires se resolvent par events ou introduction d\'un service mediateur.',
        points: 35,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q19',
        question: 'Quel mecanisme pour la gestion des sessions distribuees ?',
        options: ['Sticky sessions', 'Store session externe (Redis) avec JWT stateless', 'Fichiers', 'Base SQL'],
        correctAnswer: 1,
        explanation: 'Redis pour sessions + JWT stateless permet une scalabilite horizontale complete.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q20',
        question: 'Comment implementer un systeme de recommandation dans le CRM ?',
        options: ['Regles manuelles', 'ML avec embeddings et analyse comportementale', 'Random', 'Tri alphabetique'],
        correctAnswer: 1,
        explanation: 'Le ML avec embeddings analyse les comportements pour des recommandations pertinentes.',
        points: 35,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q21',
        question: 'Quelle strategie pour la gestion des erreurs dans les pipelines async ?',
        options: ['Ignorer', 'Dead letter queue avec retry et alerting', 'Log uniquement', 'Arret pipeline'],
        correctAnswer: 1,
        explanation: 'Les dead letter queues isolent les erreurs pour retry ulterieur avec alertes.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q22',
        question: 'Comment assurer la coherence des caches distribues ?',
        options: ['Pas de cache', 'Invalidation par events avec TTL', 'Synchrone', 'Cache local seul'],
        correctAnswer: 1,
        explanation: 'L\'invalidation event-driven avec TTL assure coherence et performances.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q23',
        question: 'Quel est le role du chaos engineering ?',
        options: ['Detruire en prod', 'Tester la resilience en injectant des pannes controlees', 'Tests de charge', 'Debug'],
        correctAnswer: 1,
        explanation: 'Le chaos engineering valide la resilience en simulant des pannes en conditions reelles.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q24',
        question: 'Comment optimiser le temps de demarrage des conteneurs ?',
        options: ['Plus de RAM', 'Multi-stage builds, lazy loading, warmup', 'Ignorer', 'Moins de code'],
        correctAnswer: 1,
        explanation: 'Images optimisees, lazy loading et warmup pools reduisent le cold start.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q25',
        question: 'Quelle approche pour documenter une API evolutive ?',
        options: ['Wiki manuel', 'OpenAPI/Swagger genere automatiquement avec versioning', 'README', 'Pas de doc'],
        correctAnswer: 1,
        explanation: 'OpenAPI genere automatiquement assure une documentation toujours a jour.',
        points: 20,
        difficulty: 'difficile',
      },
    ],
  },
];

// Grades selon le pourcentage
const GRADE_THRESHOLDS = [
  { min: 95, grade: 'A+' as const, label: 'Excellent', color: 'from-yellow-400 to-orange-500', stars: 5 },
  { min: 85, grade: 'A' as const, label: 'Tres Bien', color: 'from-green-400 to-emerald-500', stars: 5 },
  { min: 75, grade: 'B' as const, label: 'Bien', color: 'from-blue-400 to-cyan-500', stars: 4 },
  { min: 65, grade: 'C' as const, label: 'Assez Bien', color: 'from-purple-400 to-violet-500', stars: 3 },
  { min: 50, grade: 'D' as const, label: 'Passable', color: 'from-amber-400 to-yellow-500', stars: 2 },
  { min: 0, grade: 'F' as const, label: 'Insuffisant', color: 'from-red-400 to-rose-500', stars: 0 },
];

// ============================================================================
// QUIZ D'ENTRAINEMENT PAR THEME
// ============================================================================

interface PracticeQuiz {
  id: string;
  title: string;
  description: string;
  category: string;
  icon: string;
  color: string;
  duration: number; // minutes
  questions: ExamQuestion[];
  xpReward: number;
  difficulty: 'facile' | 'moyen' | 'difficile';
}

const PRACTICE_QUIZZES: PracticeQuiz[] = [
  // ==================== NAVIGATION & INTERFACE ====================
  {
    id: 'quiz-navigation',
    title: 'Navigation & Interface',
    description: 'Maitrisez l\'interface d\'AZALSCORE',
    category: 'Bases',
    icon: '🧭',
    color: 'blue',
    duration: 5,
    difficulty: 'facile',
    xpReward: 30,
    questions: [
      {
        id: 'nav-1', question: 'Quel raccourci ouvre la recherche globale ?',
        options: ['Ctrl+F', 'Touche /', 'Ctrl+K', 'F3'],
        correctAnswer: 1, explanation: 'La touche "/" ouvre la recherche globale depuis n\'importe quel ecran.',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'nav-2', question: 'Comment acceder aux notifications ?',
        options: ['Menu principal', 'Icone cloche en haut a droite', 'Profil utilisateur', 'Parametres'],
        correctAnswer: 1, explanation: 'L\'icone cloche dans la barre superieure affiche les notifications.',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'nav-3', question: 'Ou se trouve votre profil utilisateur ?',
        options: ['Menu principal', 'Clic sur votre avatar', 'Parametres systeme', 'Page d\'accueil'],
        correctAnswer: 1, explanation: 'Cliquez sur votre avatar en haut a droite pour acceder a votre profil.',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'nav-4', question: 'Comment reduire la barre de menu laterale ?',
        options: ['Double-clic', 'Bouton fleche sur le menu', 'Parametres', 'Impossible'],
        correctAnswer: 1, explanation: 'Le bouton fleche permet de reduire/etendre le menu lateral.',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'nav-5', question: 'Quel prefixe pour chercher un client ?',
        options: ['#client', '@NomClient', '!client', '/client'],
        correctAnswer: 1, explanation: 'Le prefixe @ permet de rechercher parmi les clients.',
        points: 10, difficulty: 'facile',
      },
    ],
  },

  // ==================== CRM & CLIENTS ====================
  {
    id: 'quiz-crm',
    title: 'CRM & Gestion Clients',
    description: 'Gerez efficacement vos clients et prospects',
    category: 'Commercial',
    icon: '👥',
    color: 'green',
    duration: 8,
    difficulty: 'moyen',
    xpReward: 50,
    questions: [
      {
        id: 'crm-1', question: 'Quelle est la difference entre prospect et client ?',
        options: ['Aucune', 'Le prospect n\'a pas encore achete', 'Le client est inactif', 'Question de budget'],
        correctAnswer: 1, explanation: 'Un prospect devient client apres sa premiere commande.',
        points: 15, difficulty: 'facile',
      },
      {
        id: 'crm-2', question: 'Quelle info est obligatoire pour un client B2B francais ?',
        options: ['Email', 'Telephone', 'SIRET', 'Site web'],
        correctAnswer: 2, explanation: 'Le SIRET (14 chiffres) est obligatoire pour les entreprises francaises.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'crm-3', question: 'Combien de contacts peut-on associer a un client ?',
        options: ['1 seul', 'Maximum 5', 'Maximum 10', 'Illimite'],
        correctAnswer: 3, explanation: 'Il n\'y a pas de limite au nombre de contacts par fiche client.',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'crm-4', question: 'Comment archiver un client inactif ?',
        options: ['Le supprimer', 'Menu Actions > Archiver', 'Modifier son statut', 'Contacter le support'],
        correctAnswer: 1, explanation: 'L\'archivage conserve l\'historique tout en masquant le client des listes.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'crm-5', question: 'Ou voir l\'historique des echanges avec un client ?',
        options: ['Menu Rapports', 'Onglet Historique de la fiche', 'Export Excel', 'Module Audit'],
        correctAnswer: 1, explanation: 'L\'onglet Historique centralise tous les echanges: emails, appels, notes.',
        points: 15, difficulty: 'facile',
      },
      {
        id: 'crm-6', question: 'Qu\'est-ce que le scoring client ?',
        options: ['Note de satisfaction', 'Score calcule selon le comportement', 'Evaluation de risque', 'Classement par CA'],
        correctAnswer: 1, explanation: 'Le scoring attribue automatiquement un score base sur les interactions et le potentiel.',
        points: 20, difficulty: 'moyen',
      },
      {
        id: 'crm-7', question: 'Comment fusionner deux fiches client en doublon ?',
        options: ['Supprimer une', 'Menu Actions > Fusionner', 'Copier-coller', 'Impossible'],
        correctAnswer: 1, explanation: 'La fusion conserve toutes les donnees des deux fiches en une seule.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'crm-8', question: 'Comment importer une liste de clients depuis Excel ?',
        options: ['Copier-coller', 'CRM > Importer > CSV/Excel', 'Demander au support', 'API uniquement'],
        correctAnswer: 1, explanation: 'L\'import CSV/Excel permet de mapper les colonnes aux champs AZALSCORE.',
        points: 15, difficulty: 'moyen',
      },
    ],
  },

  // ==================== DEVIS & FACTURATION ====================
  {
    id: 'quiz-facturation',
    title: 'Devis & Facturation',
    description: 'Maitrisez le cycle commercial complet',
    category: 'Commercial',
    icon: '📄',
    color: 'indigo',
    duration: 10,
    difficulty: 'moyen',
    xpReward: 60,
    questions: [
      {
        id: 'fact-1', question: 'Quel est l\'ordre du cycle commercial ?',
        options: ['Facture > Devis > Commande', 'Devis > Commande > Facture', 'Commande > Facture > Devis', 'Devis > Facture'],
        correctAnswer: 1, explanation: 'Le cycle standard: Devis > Commande > Bon de livraison > Facture.',
        points: 15, difficulty: 'facile',
      },
      {
        id: 'fact-2', question: 'Duree de validite par defaut d\'un devis ?',
        options: ['15 jours', '30 jours', '60 jours', '90 jours'],
        correctAnswer: 1, explanation: 'Par defaut, un devis est valide 30 jours (modifiable dans les parametres).',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'fact-3', question: 'Comment appliquer une remise de 10% sur une ligne ?',
        options: ['Modifier le prix', 'Colonne Remise de la ligne', 'Note en bas', 'Impossible par ligne'],
        correctAnswer: 1, explanation: 'Chaque ligne a sa colonne Remise pour les remises individuelles.',
        points: 15, difficulty: 'facile',
      },
      {
        id: 'fact-4', question: 'Quand le numero de facture est-il genere ?',
        options: ['A la creation', 'A la validation', 'A l\'envoi', 'Au paiement'],
        correctAnswer: 1, explanation: 'Le numero est attribue a la validation, pas en mode brouillon.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'fact-5', question: 'Comment creer un avoir suite a un retour ?',
        options: ['Facture negative', 'Depuis la facture > Creer avoir', 'Supprimer la facture', 'Nouveau document'],
        correctAnswer: 1, explanation: 'Creer l\'avoir depuis la facture originale assure la tracabilite.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'fact-6', question: 'Comment dupliquer un devis existant ?',
        options: ['Copier-coller', 'Menu Actions > Dupliquer', 'Export/Import', 'Nouveau + copie manuelle'],
        correctAnswer: 1, explanation: 'La duplication cree une copie complete du devis.',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'fact-7', question: 'Quel statut indique un devis en attente de reponse ?',
        options: ['Brouillon', 'Envoye', 'Accepte', 'En cours'],
        correctAnswer: 1, explanation: 'Le statut "Envoye" indique que le client a recu le devis.',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'fact-8', question: 'Comment envoyer une facture par email ?',
        options: ['Export PDF + email externe', 'Bouton Envoyer par email', 'Partager le lien', 'Impression uniquement'],
        correctAnswer: 1, explanation: 'Le bouton "Envoyer par email" genere le PDF et l\'envoie directement.',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'fact-9', question: 'Peut-on modifier une facture validee ?',
        options: ['Oui librement', 'Non, il faut creer un avoir', 'Seulement les notes', 'Avec mot de passe admin'],
        correctAnswer: 1, explanation: 'Une facture validee est figee. Pour corriger, creez un avoir puis une nouvelle facture.',
        points: 20, difficulty: 'moyen',
      },
      {
        id: 'fact-10', question: 'Ou configurer les conditions de paiement par defaut ?',
        options: ['Chaque document', 'Parametres > Commercial', 'Fiche client', 'Non configurable'],
        correctAnswer: 1, explanation: 'Les valeurs par defaut se definissent dans Parametres > Commercial.',
        points: 15, difficulty: 'moyen',
      },
    ],
  },

  // ==================== COMPTABILITE ====================
  {
    id: 'quiz-comptabilite',
    title: 'Comptabilite & Finance',
    description: 'Les fondamentaux de la gestion financiere',
    category: 'Finance',
    icon: '💰',
    color: 'emerald',
    duration: 12,
    difficulty: 'difficile',
    xpReward: 80,
    questions: [
      {
        id: 'compta-1', question: 'Quel journal pour les factures de vente ?',
        options: ['AC (Achats)', 'VE (Ventes)', 'BQ (Banque)', 'OD (Operations Diverses)'],
        correctAnswer: 1, explanation: 'Les ventes sont enregistrees dans le journal VE (Ventes).',
        points: 15, difficulty: 'facile',
      },
      {
        id: 'compta-2', question: 'Que signifie une ecriture equilibree ?',
        options: ['Debit > Credit', 'Debit < Credit', 'Debit = Credit', 'Pas de relation'],
        correctAnswer: 2, explanation: 'En partie double, chaque ecriture doit avoir Total Debit = Total Credit.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'compta-3', question: 'Quel compte represente les clients ?',
        options: ['401', '411', '512', '707'],
        correctAnswer: 1, explanation: 'Le compte 411 enregistre les creances clients.',
        points: 20, difficulty: 'moyen',
      },
      {
        id: 'compta-4', question: 'Quel compte represente la banque ?',
        options: ['401', '411', '512', '707'],
        correctAnswer: 2, explanation: 'Le compte 512 represente les comptes bancaires.',
        points: 20, difficulty: 'moyen',
      },
      {
        id: 'compta-5', question: 'Qu\'est-ce que le lettrage ?',
        options: ['Classement alphabetique', 'Rapprochement facture/paiement', 'Numerotation', 'Archivage'],
        correctAnswer: 1, explanation: 'Le lettrage associe une facture a son paiement pour suivre les soldes.',
        points: 20, difficulty: 'moyen',
      },
      {
        id: 'compta-6', question: 'Quel est le taux de TVA standard en France ?',
        options: ['5.5%', '10%', '20%', '25%'],
        correctAnswer: 2, explanation: 'Le taux normal de TVA en France est 20%.',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'compta-7', question: 'Qu\'est-ce que la TVA deductible ?',
        options: ['TVA a payer', 'TVA recuperable sur achats', 'TVA exoneree', 'Remboursement TVA'],
        correctAnswer: 1, explanation: 'La TVA deductible est payee sur les achats et recuperable aupres de l\'Etat.',
        points: 20, difficulty: 'moyen',
      },
      {
        id: 'compta-8', question: 'Comment effectuer un rapprochement bancaire ?',
        options: ['Manuellement dans Excel', 'Comptabilite > Banque > Rapprochement', 'Export uniquement', 'Support technique'],
        correctAnswer: 1, explanation: 'Le module de rapprochement compare les ecritures au releve bancaire.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'compta-9', question: 'Quel compte pour les ventes de services ?',
        options: ['706', '707', '708', '709'],
        correctAnswer: 0, explanation: 'Le compte 706 "Prestations de services" enregistre les ventes de services.',
        points: 25, difficulty: 'difficile',
      },
      {
        id: 'compta-10', question: 'Qu\'est-ce qu\'une immobilisation ?',
        options: ['Stock bloque', 'Bien durable amorti sur plusieurs annees', 'Tresorerie bloquee', 'Facture impayee'],
        correctAnswer: 1, explanation: 'Une immobilisation est un actif durable (materiel, vehicule) amorti sur sa duree d\'utilisation.',
        points: 20, difficulty: 'difficile',
      },
    ],
  },

  // ==================== STOCKS ====================
  {
    id: 'quiz-stocks',
    title: 'Gestion des Stocks',
    description: 'Optimisez votre gestion des stocks',
    category: 'Operations',
    icon: '📦',
    color: 'orange',
    duration: 8,
    difficulty: 'moyen',
    xpReward: 50,
    questions: [
      {
        id: 'stock-1', question: 'Quel document valide une entree en stock ?',
        options: ['Bon de commande', 'Bon de reception', 'Facture', 'Devis'],
        correctAnswer: 1, explanation: 'Le bon de reception confirme l\'entree physique des marchandises.',
        points: 15, difficulty: 'facile',
      },
      {
        id: 'stock-2', question: 'Comment calculer le stock disponible ?',
        options: ['Stock physique', 'Stock physique - Reserves', 'Stock physique + Commandes', 'Stock moyen'],
        correctAnswer: 1, explanation: 'Stock disponible = Stock physique moins les quantites reservees.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'stock-3', question: 'Qu\'est-ce qu\'un inventaire tournant ?',
        options: ['Inventaire annuel', 'Comptage regulier partiel', 'Rotation des produits', 'Inventaire automatique'],
        correctAnswer: 1, explanation: 'L\'inventaire tournant compte regulierement une partie du stock.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'stock-4', question: 'Comment traiter un ecart d\'inventaire ?',
        options: ['Ignorer', 'Ajustement de stock documente', 'Modifier l\'historique', 'Supprimer les mouvements'],
        correctAnswer: 1, explanation: 'Les ecarts se regularisent par ajustement avec justificatif.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'stock-5', question: 'Qu\'est-ce que le seuil de reapprovisionnement ?',
        options: ['Stock maximum', 'Niveau declenchant commande', 'Prix minimum', 'Delai livraison'],
        correctAnswer: 1, explanation: 'Sous ce seuil, une alerte ou commande auto est declenchee.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'stock-6', question: 'Comment activer le suivi par lot ?',
        options: ['Parametres globaux', 'Fiche produit > Tracabilite', 'Impossible', 'Module externe'],
        correctAnswer: 1, explanation: 'La tracabilite lot/serie s\'active sur chaque fiche produit.',
        points: 20, difficulty: 'moyen',
      },
      {
        id: 'stock-7', question: 'Peut-on gerer plusieurs entrepots ?',
        options: ['Non', 'Oui, dans Parametres > Entrepots', 'Forfait Premium', 'Module separe'],
        correctAnswer: 1, explanation: 'AZALSCORE supporte plusieurs entrepots avec transferts inter-sites.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'stock-8', question: 'Comment visualiser les mouvements d\'un article ?',
        options: ['Export manuel', 'Fiche article > Mouvements', 'Module Rapports', 'Audit uniquement'],
        correctAnswer: 1, explanation: 'L\'onglet Mouvements de la fiche montre tout l\'historique.',
        points: 10, difficulty: 'facile',
      },
    ],
  },

  // ==================== ASSISTANT IA ====================
  {
    id: 'quiz-ia',
    title: 'Theo & Marceau - Assistants IA',
    description: 'Exploitez la puissance de l\'IA',
    category: 'Intelligence',
    icon: '🤖',
    color: 'purple',
    duration: 6,
    difficulty: 'moyen',
    xpReward: 40,
    questions: [
      {
        id: 'ia-1', question: 'Qui est Theo ?',
        options: ['Agent autonome', 'Assistant conversationnel', 'Module de reporting', 'Administrateur'],
        correctAnswer: 1, explanation: 'Theo est l\'assistant IA conversationnel qui repond a vos questions.',
        points: 15, difficulty: 'facile',
      },
      {
        id: 'ia-2', question: 'Qui est Marceau ?',
        options: ['Assistant vocal', 'Agent IA executant des taches', 'Module comptable', 'Support technique'],
        correctAnswer: 1, explanation: 'Marceau est l\'agent IA autonome qui execute des taches complexes.',
        points: 15, difficulty: 'facile',
      },
      {
        id: 'ia-3', question: 'Que peut faire Theo ?',
        options: ['Modifier la base', 'Repondre a des questions sur AZALSCORE', 'Valider des factures', 'Gerer les utilisateurs'],
        correctAnswer: 1, explanation: 'Theo aide et repond aux questions, mais ne modifie pas les donnees.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'ia-4', question: 'Comment demander a Marceau de creer un devis ?',
        options: ['Email', 'Chat avec description du besoin', 'Formulaire dedie', 'Impossible'],
        correctAnswer: 1, explanation: 'Decrivez votre besoin dans le chat Marceau, il creera le devis.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'ia-5', question: 'Les actions de Marceau sont-elles automatiques ?',
        options: ['Toujours', 'Jamais', 'Validation humaine requise', 'Selon configuration'],
        correctAnswer: 3, explanation: 'Selon la configuration, certaines actions requierent une validation.',
        points: 20, difficulty: 'moyen',
      },
      {
        id: 'ia-6', question: 'Ou consulter l\'historique des actions Marceau ?',
        options: ['Non disponible', 'Dashboard Marceau', 'Logs systeme', 'Email uniquement'],
        correctAnswer: 1, explanation: 'Le dashboard Marceau affiche toutes les actions avec leur statut.',
        points: 15, difficulty: 'moyen',
      },
    ],
  },

  // ==================== ADMINISTRATION ====================
  {
    id: 'quiz-admin',
    title: 'Administration & Securite',
    description: 'Gerez les utilisateurs et la securite',
    category: 'Administration',
    icon: '⚙️',
    color: 'red',
    duration: 10,
    difficulty: 'difficile',
    xpReward: 70,
    questions: [
      {
        id: 'admin-1', question: 'Ou gerer les utilisateurs ?',
        options: ['CRM', 'Parametres > Utilisateurs', 'Module RH', 'Support technique'],
        correctAnswer: 1, explanation: 'La gestion des utilisateurs se fait dans Parametres > Utilisateurs.',
        points: 10, difficulty: 'facile',
      },
      {
        id: 'admin-2', question: 'Comment creer un role personnalise ?',
        options: ['Copier un existant', 'Parametres > Roles > Nouveau', 'Impossible', 'Support uniquement'],
        correctAnswer: 1, explanation: 'Les roles personnalises permettent des permissions sur mesure.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'admin-3', question: 'Qu\'est-ce que le 2FA ?',
        options: ['Format fichier', 'Double authentification', 'Sauvegarde', 'Type de rapport'],
        correctAnswer: 1, explanation: 'Le 2FA (authentification a deux facteurs) renforce la securite.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'admin-4', question: 'Comment activer le 2FA ?',
        options: ['Automatique', 'Profil > Securite > 2FA', 'Admin uniquement', 'Forfait Premium'],
        correctAnswer: 1, explanation: 'Chaque utilisateur peut activer le 2FA dans son profil.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'admin-5', question: 'Ou consulter le journal d\'audit ?',
        options: ['Rapports', 'Parametres > Audit > Journal', 'Non disponible', 'Base de donnees'],
        correctAnswer: 1, explanation: 'Le journal d\'audit trace toutes les actions des utilisateurs.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'admin-6', question: 'Combien de temps sont conserves les logs d\'audit ?',
        options: ['30 jours', '1 an', '5 ans', '7 ans'],
        correctAnswer: 3, explanation: 'Les logs sont conserves 7 ans pour conformite legale.',
        points: 20, difficulty: 'difficile',
      },
      {
        id: 'admin-7', question: 'Comment configurer le SSO ?',
        options: ['Plugin externe', 'Parametres > Securite > SSO', 'Non supporte', 'Developpement custom'],
        correctAnswer: 1, explanation: 'Le SSO (SAML/OAuth) se configure dans les parametres de securite.',
        points: 25, difficulty: 'difficile',
      },
      {
        id: 'admin-8', question: 'Comment sauvegarder les donnees ?',
        options: ['Manuel uniquement', 'Automatique quotidien + export', 'Non disponible', 'Cloud uniquement'],
        correctAnswer: 1, explanation: 'Sauvegardes automatiques quotidiennes + possibilite d\'export manuel.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'admin-9', question: 'Comment desactiver un utilisateur sans supprimer ?',
        options: ['Impossible', 'Utilisateur > Desactiver', 'Changer mot de passe', 'Retirer tous les roles'],
        correctAnswer: 1, explanation: 'La desactivation bloque l\'acces tout en conservant l\'historique.',
        points: 15, difficulty: 'moyen',
      },
      {
        id: 'admin-10', question: 'Quelle certification securite possede AZALSCORE ?',
        options: ['Aucune', 'ISO 27001', 'SOC 2 uniquement', 'PCI-DSS'],
        correctAnswer: 1, explanation: 'AZALSCORE est certifie ISO 27001 pour la securite de l\'information.',
        points: 20, difficulty: 'difficile',
      },
    ],
  },
];

// ============================================================================
// HOOKS
// ============================================================================

// Context pour la gamification
const GamificationContext = React.createContext<ReturnType<typeof useGamificationState> | null>(null);

function useGamificationState() {
  const [profile, setProfile] = useState<UserGameProfile>({
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
    title: 'Debutant',
  });

  const [examResults, setExamResults] = useState<ExamResult[]>([]);
  const [pendingLevelUp, setPendingLevelUp] = useState<number | null>(null);
  const [pointsHistory, setPointsHistory] = useState<Array<{ action: string; points: number; timestamp: string }>>([]);

  // Ajouter des points avec historique
  const addPoints = useCallback((actionId: string, multiplier: number = 1) => {
    const action = POINTS_ACTIONS.find(a => a.id === actionId);
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

  // Ajouter XP avec verification de niveau
  const addXP = useCallback((amount: number) => {
    setProfile(prev => {
      let newXP = prev.xp + amount;
      let newLevel = prev.level;
      let newXPToNext = prev.xpToNextLevel;
      let levelUpPending = false;

      // Verifier si on atteint le seuil du niveau suivant
      if (newXP >= newXPToNext && newLevel < LEVELS.length) {
        // Ne pas monter de niveau automatiquement - il faut passer l'examen
        levelUpPending = true;
        newXP = newXPToNext; // Plafonner a l'XP max du niveau
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

  // Passer au niveau superieur apres reussite de l'examen
  const levelUp = useCallback((newLevel: number) => {
    setProfile(prev => {
      const nextLevelData = LEVELS.find(l => l.level === newLevel + 1);
      const currentLevelXP = LEVELS.find(l => l.level === newLevel)?.xp || 0;
      const prevLevelXP = LEVELS.find(l => l.level === newLevel - 1)?.xp || 0;
      const xpToNext = nextLevelData ? nextLevelData.xp - currentLevelXP : 9999;

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

  // Enregistrer un resultat d'examen
  const recordExamResult = useCallback((result: ExamResult) => {
    setExamResults(prev => [result, ...prev]);
    if (result.passed) {
      addPoints('exam-pass');
      if (result.grade === 'A+') {
        addPoints('exam-perfect');
      }
    }
  }, [addPoints]);

  const unlockBadge = useCallback((badgeId: string) => {
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

  const incrementStreak = useCallback(() => {
    setProfile(prev => ({ ...prev, streak: prev.streak + 1 }));
  }, []);

  return {
    profile,
    examResults,
    pendingLevelUp,
    pointsHistory,
    addXP,
    addPoints,
    levelUp,
    recordExamResult,
    unlockBadge,
    incrementStreak,
    POINTS_ACTIONS,
    LEVEL_EXAMS,
  };
}

export function GamificationProvider({ children }: { children: React.ReactNode }) {
  const gamification = useGamificationState();

  return (
    <GamificationContext.Provider value={gamification}>
      {children}
    </GamificationContext.Provider>
  );
}

export function useGamification() {
  const context = React.useContext(GamificationContext);
  if (!context) {
    // Fallback pour utilisation sans Provider
    return useGamificationState();
  }
  return context;
}

// ============================================================================
// COMPOSANTS
// ============================================================================

/**
 * Barre de progression XP animee
 */
export function XPProgressBar({ xp, xpToNext, level }: { xp: number; xpToNext: number; level: number }) {
  const percentage = Math.min((xp / xpToNext) * 100, 100);
  const levelData = LEVELS[level - 1];

  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-full bg-gradient-to-br from-${levelData?.color || 'blue'}-400 to-${levelData?.color || 'blue'}-600 flex items-center justify-center text-white font-bold text-sm shadow-lg`}>
            {level}
          </div>
          <span className="text-sm font-medium text-gray-700">{levelData?.title}</span>
        </div>
        <span className="text-xs text-gray-500">{xp} / {xpToNext} XP</span>
      </div>
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full transition-all duration-500 ease-out relative"
          style={{ width: `${percentage}%` }}
        >
          <div className="absolute inset-0 bg-white/20 animate-pulse" />
          <Sparkles className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-4 text-white animate-bounce" />
        </div>
      </div>
    </div>
  );
}

/**
 * Carte de statistiques du joueur
 */
export function PlayerStatsCard({ profile }: { profile: UserGameProfile }) {
  return (
    <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-6 text-white shadow-xl">
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center text-3xl backdrop-blur-sm">
            {profile.avatar}
          </div>
          <div>
            <h3 className="text-xl font-bold">{profile.displayName}</h3>
            <p className="text-white/70 flex items-center gap-1">
              <Crown className="w-4 h-4" />
              {profile.title}
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold">#{profile.rank}</div>
          <div className="text-white/70 text-sm">Classement</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white/10 rounded-xl p-3 text-center backdrop-blur-sm">
          <Zap className="w-6 h-6 mx-auto mb-1 text-yellow-300" />
          <div className="text-2xl font-bold">{profile.totalPoints}</div>
          <div className="text-xs text-white/70">Points</div>
        </div>
        <div className="bg-white/10 rounded-xl p-3 text-center backdrop-blur-sm">
          <Flame className="w-6 h-6 mx-auto mb-1 text-orange-400" />
          <div className="text-2xl font-bold">{profile.streak}</div>
          <div className="text-xs text-white/70">Jours serie</div>
        </div>
        <div className="bg-white/10 rounded-xl p-3 text-center backdrop-blur-sm">
          <Award className="w-6 h-6 mx-auto mb-1 text-blue-300" />
          <div className="text-2xl font-bold">{profile.badges.length}</div>
          <div className="text-xs text-white/70">Badges</div>
        </div>
      </div>

      <XPProgressBar xp={profile.xp} xpToNext={profile.xpToNextLevel} level={profile.level} />
    </div>
  );
}

/**
 * Carte de defi quotidien
 */
export function DailyChallengeCard({ challenge, onComplete }: { challenge: Challenge; onComplete: () => void }) {
  const completedTasks = challenge.tasks.filter(t => t.completed).length;
  const progress = (completedTasks / challenge.tasks.length) * 100;

  const difficultyColors = {
    easy: 'bg-green-100 text-green-700',
    medium: 'bg-amber-100 text-amber-700',
    hard: 'bg-red-100 text-red-700',
  };

  return (
    <div className={`border-2 rounded-2xl p-5 transition-all ${
      challenge.completed
        ? 'border-green-300 bg-green-50'
        : 'border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50 hover:shadow-lg'
    }`}>
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
            challenge.completed ? 'bg-green-100' : 'bg-purple-100'
          }`}>
            {challenge.completed ? (
              <CheckCircle className="w-6 h-6 text-green-600" />
            ) : (
              <Target className="w-6 h-6 text-purple-600" />
            )}
          </div>
          <div>
            <h4 className="font-bold text-gray-900">{challenge.title}</h4>
            <div className="flex items-center gap-2 mt-1">
              <span className={`text-xs px-2 py-0.5 rounded-full ${difficultyColors[challenge.difficulty]}`}>
                {challenge.difficulty === 'easy' ? 'Facile' : challenge.difficulty === 'medium' ? 'Moyen' : 'Difficile'}
              </span>
              {challenge.timeLimit && (
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Timer className="w-3 h-3" />
                  {Math.floor(challenge.timeLimit / 60)} min
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 bg-yellow-100 px-3 py-1 rounded-full">
          <Zap className="w-4 h-4 text-yellow-600" />
          <span className="font-bold text-yellow-700">+{challenge.xpReward}</span>
        </div>
      </div>

      <p className="text-gray-600 text-sm mb-4">{challenge.description}</p>

      {/* Tasks */}
      <div className="space-y-2 mb-4">
        {challenge.tasks.map(task => (
          <div
            key={task.id}
            className={`flex items-center gap-3 p-2 rounded-lg ${
              task.completed ? 'bg-green-100' : 'bg-white'
            }`}
          >
            <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
              task.completed
                ? 'bg-green-500 text-white'
                : 'border-2 border-gray-300'
            }`}>
              {task.completed && <CheckCircle className="w-3 h-3" />}
            </div>
            <span className={`text-sm ${task.completed ? 'text-green-700 line-through' : 'text-gray-700'}`}>
              {task.description}
            </span>
          </div>
        ))}
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-3">
        <div
          className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all"
          style={{ width: `${progress}%` }}
        />
      </div>

      <button
        onClick={onComplete}
        disabled={challenge.completed}
        className={`w-full py-2 rounded-xl font-medium transition-all ${
          challenge.completed
            ? 'bg-green-100 text-green-700 cursor-not-allowed'
            : 'bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:shadow-lg hover:scale-[1.02]'
        }`}
      >
        {challenge.completed ? '✓ Complete !' : 'Commencer le defi'}
      </button>
    </div>
  );
}

/**
 * Collection de badges
 */
export function BadgeCollection({ badges, allBadges }: { badges: Badge[]; allBadges: Badge[] }) {
  const rarityColors = {
    common: 'from-gray-400 to-gray-500',
    rare: 'from-blue-400 to-blue-600',
    epic: 'from-purple-500 to-pink-500',
    legendary: 'from-yellow-400 via-orange-500 to-red-500',
  };

  const rarityGlow = {
    common: '',
    rare: 'shadow-blue-300/50',
    epic: 'shadow-purple-400/50',
    legendary: 'shadow-yellow-400/50 animate-pulse',
  };

  return (
    <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-4">
      {allBadges.map(badge => {
        const isUnlocked = badges.some(b => b.id === badge.id);

        return (
          <div
            key={badge.id}
            className={`relative group cursor-pointer transition-all duration-300 ${
              isUnlocked ? 'hover:scale-110' : 'opacity-40 grayscale'
            }`}
          >
            <div
              className={`w-16 h-16 rounded-2xl flex items-center justify-center text-3xl bg-gradient-to-br ${
                isUnlocked ? rarityColors[badge.rarity] : 'from-gray-300 to-gray-400'
              } shadow-lg ${isUnlocked ? rarityGlow[badge.rarity] : ''}`}
            >
              {isUnlocked ? badge.icon : <Lock className="w-6 h-6 text-gray-500" />}
            </div>

            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
              <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 whitespace-nowrap">
                <div className="font-bold">{badge.name}</div>
                <div className="text-gray-300">{badge.description}</div>
                <div className={`text-xs mt-1 ${
                  badge.rarity === 'legendary' ? 'text-yellow-400' :
                  badge.rarity === 'epic' ? 'text-purple-400' :
                  badge.rarity === 'rare' ? 'text-blue-400' : 'text-gray-400'
                }`}>
                  {badge.rarity.charAt(0).toUpperCase() + badge.rarity.slice(1)}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/**
 * Classement / Leaderboard
 */
export function Leaderboard({ entries }: { entries: LeaderboardEntry[] }) {
  const getMedalIcon = (rank: number) => {
    if (rank === 1) return <Crown className="w-5 h-5 text-yellow-500" />;
    if (rank === 2) return <Medal className="w-5 h-5 text-gray-400" />;
    if (rank === 3) return <Medal className="w-5 h-5 text-amber-600" />;
    return <span className="text-gray-500 text-sm font-medium">#{rank}</span>;
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-4 text-white">
        <h3 className="font-bold flex items-center gap-2">
          <Trophy className="w-5 h-5" />
          Classement
        </h3>
      </div>
      <div className="divide-y divide-gray-100">
        {entries.map((entry, index) => (
          <div
            key={entry.userId}
            className={`flex items-center gap-4 p-4 transition-colors ${
              entry.isCurrentUser
                ? 'bg-blue-50 border-l-4 border-blue-500'
                : 'hover:bg-gray-50'
            }`}
          >
            <div className="w-8 flex justify-center">
              {getMedalIcon(entry.rank)}
            </div>
            <div className="w-10 h-10 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full flex items-center justify-center text-xl">
              {entry.avatar}
            </div>
            <div className="flex-1">
              <div className="font-medium text-gray-900">
                {entry.displayName}
                {entry.isCurrentUser && <span className="text-blue-600 text-sm ml-2">(Vous)</span>}
              </div>
              <div className="text-sm text-gray-500">Niveau {entry.level}</div>
            </div>
            <div className="text-right">
              <div className="font-bold text-gray-900">{entry.points.toLocaleString()}</div>
              <div className="text-xs text-gray-500">points</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Tableau des points
 */
export function PointsTable({ actions }: { actions: PointsAction[] }) {
  const categories = ['apprentissage', 'pratique', 'social', 'examen'] as const;
  const categoryLabels = {
    apprentissage: 'Apprentissage',
    pratique: 'Pratique',
    social: 'Social',
    examen: 'Examens',
  };
  const categoryColors = {
    apprentissage: 'blue',
    pratique: 'green',
    social: 'purple',
    examen: 'amber',
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4 text-white">
        <h3 className="font-bold flex items-center gap-2">
          <Zap className="w-5 h-5" />
          Systeme de Points
        </h3>
      </div>
      <div className="p-4">
        {categories.map(category => (
          <div key={category} className="mb-4 last:mb-0">
            <h4 className={`text-sm font-semibold text-${categoryColors[category]}-600 mb-2`}>
              {categoryLabels[category]}
            </h4>
            <div className="space-y-2">
              {actions.filter(a => a.category === category).map(action => (
                <div
                  key={action.id}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{action.icon}</span>
                    <span className="text-sm text-gray-700">{action.action}</span>
                  </div>
                  <span className={`font-bold text-${categoryColors[category]}-600`}>
                    +{action.points}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Composant d'examen de niveau
 */
export function LevelExamComponent({
  exam,
  onComplete,
  onCancel,
}: {
  exam: LevelExam;
  onComplete: (result: ExamResult) => void;
  onCancel: () => void;
}) {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>(new Array(exam.questions.length).fill(null));
  const [timeLeft, setTimeLeft] = useState(exam.duration);
  const [showResults, setShowResults] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [startTime] = useState(Date.now());

  // Timer
  useEffect(() => {
    if (showResults) return;

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [showResults]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSelectAnswer = (answerIndex: number) => {
    setSelectedAnswer(answerIndex);
  };

  const handleConfirmAnswer = () => {
    if (selectedAnswer === null) return;

    const newAnswers = [...answers];
    newAnswers[currentQuestion] = selectedAnswer;
    setAnswers(newAnswers);

    if (currentQuestion < exam.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
      setSelectedAnswer(null);
    }
  };

  const handleSubmit = () => {
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);

    let correctAnswers = 0;
    let totalPoints = 0;
    let maxPoints = 0;

    exam.questions.forEach((q, index) => {
      maxPoints += q.points;
      if (answers[index] === q.correctAnswer) {
        correctAnswers++;
        totalPoints += q.points;
      }
    });

    const percentage = Math.round((totalPoints / maxPoints) * 100);
    const passed = percentage >= exam.passingScore;

    // Determiner la note
    const gradeInfo = GRADE_THRESHOLDS.find(g => percentage >= g.min)!;

    // Calculer XP gagne
    let xpEarned = 0;
    if (passed) {
      xpEarned = exam.xpReward;
      // Bonus pour bonne note
      if (gradeInfo.grade === 'A+') xpEarned = Math.round(xpEarned * 1.5);
      else if (gradeInfo.grade === 'A') xpEarned = Math.round(xpEarned * 1.25);
    } else {
      // XP de consolation
      xpEarned = Math.round(exam.xpReward * 0.1 * (percentage / 100));
    }

    const result: ExamResult = {
      examLevel: exam.level,
      score: totalPoints,
      totalPoints,
      maxPoints,
      percentage,
      passed,
      grade: gradeInfo.grade,
      timeSpent,
      correctAnswers,
      totalQuestions: exam.questions.length,
      xpEarned,
      completedAt: new Date().toISOString(),
    };

    setShowResults(true);
    onComplete(result);
  };

  const question = exam.questions[currentQuestion];
  const progress = ((currentQuestion + 1) / exam.questions.length) * 100;

  if (showResults) {
    const result = {
      correctAnswers: exam.questions.filter((q, i) => answers[i] === q.correctAnswer).length,
      totalQuestions: exam.questions.length,
      percentage: Math.round(
        (exam.questions.filter((q, i) => answers[i] === q.correctAnswer).reduce((sum, q) => sum + q.points, 0) /
          exam.questions.reduce((sum, q) => sum + q.points, 0)) * 100
      ),
    };
    const gradeInfo = GRADE_THRESHOLDS.find(g => result.percentage >= g.min)!;
    const passed = result.percentage >= exam.passingScore;

    return (
      <ExamResultsDisplay
        result={{
          ...result,
          passed,
          grade: gradeInfo.grade,
          xpEarned: passed ? exam.xpReward : Math.round(exam.xpReward * 0.1),
          examLevel: exam.level,
        }}
        questions={exam.questions}
        answers={answers}
        onClose={onCancel}
      />
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-4 text-white">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-bold text-lg flex items-center gap-2">
              <GraduationCap className="w-5 h-5" />
              {exam.title}
            </h2>
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${
              timeLeft < 60 ? 'bg-red-500 animate-pulse' : 'bg-white/20'
            }`}>
              <Timer className="w-4 h-4" />
              <span className="font-mono font-bold">{formatTime(timeLeft)}</span>
            </div>
          </div>
          <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-white rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between text-sm mt-1 text-white/80">
            <span>Question {currentQuestion + 1} / {exam.questions.length}</span>
            <span>{Math.round(progress)}% complete</span>
          </div>
        </div>

        {/* Question */}
        <div className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              question.difficulty === 'facile' ? 'bg-green-100 text-green-700' :
              question.difficulty === 'moyen' ? 'bg-amber-100 text-amber-700' :
              'bg-red-100 text-red-700'
            }`}>
              {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
            </span>
            <span className="text-sm text-gray-500 flex items-center gap-1">
              <Zap className="w-3 h-3" />
              {question.points} pts
            </span>
          </div>

          <h3 className="text-xl font-semibold text-gray-900 mb-6">
            {question.question}
          </h3>

          <div className="space-y-3">
            {question.options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleSelectAnswer(index)}
                className={`w-full p-4 rounded-xl text-left transition-all ${
                  selectedAnswer === index
                    ? 'bg-indigo-100 border-2 border-indigo-500 shadow-md'
                    : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                    selectedAnswer === index
                      ? 'bg-indigo-500 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}>
                    {String.fromCharCode(65 + index)}
                  </span>
                  <span className={selectedAnswer === index ? 'text-indigo-900 font-medium' : 'text-gray-700'}>
                    {option}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-50 p-4 flex justify-between">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
          >
            Abandonner
          </button>
          <div className="flex gap-3">
            {currentQuestion === exam.questions.length - 1 ? (
              <button
                onClick={handleSubmit}
                disabled={selectedAnswer === null}
                className={`px-6 py-2 rounded-xl font-medium transition-all ${
                  selectedAnswer !== null
                    ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white hover:shadow-lg'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                Terminer l'examen
              </button>
            ) : (
              <button
                onClick={handleConfirmAnswer}
                disabled={selectedAnswer === null}
                className={`px-6 py-2 rounded-xl font-medium transition-all flex items-center gap-2 ${
                  selectedAnswer !== null
                    ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:shadow-lg'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }`}
              >
                Suivant
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Affichage des resultats d'examen avec notation
 */
export function ExamResultsDisplay({
  result,
  questions,
  answers,
  onClose,
  showErrorsOnly = false,
}: {
  result: {
    passed: boolean;
    grade: 'A+' | 'A' | 'B' | 'C' | 'D' | 'F';
    percentage: number;
    correctAnswers: number;
    totalQuestions: number;
    xpEarned: number;
    examLevel?: number;
  };
  questions: ExamQuestion[];
  answers: (number | null)[];
  onClose: () => void;
  showErrorsOnly?: boolean;
}) {
  const { t, isRTL } = useI18n();
  const [activeTab, setActiveTab] = useState<'summary' | 'errors' | 'all'>('errors');
  const gradeInfo = GRADE_THRESHOLDS.find(g => g.grade === result.grade)!;

  // Get translated grade label
  const gradeLabels: Record<string, keyof typeof t.exams.results.grades> = {
    'A+': 'excellent',
    'A': 'veryGood',
    'B': 'good',
    'C': 'satisfactory',
    'D': 'passable',
    'F': 'insufficient',
  };
  const gradeLabel = t.exams.results.grades[gradeLabels[result.grade] || 'insufficient'];

  // Separer les reponses correctes et incorrectes
  const incorrectAnswers = questions.map((q, i) => ({ question: q, index: i, userAnswer: answers[i] }))
    .filter(item => item.userAnswer !== item.question.correctAnswer);
  const correctAnswersList = questions.map((q, i) => ({ question: q, index: i, userAnswer: answers[i] }))
    .filter(item => item.userAnswer === item.question.correctAnswer);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" dir={isRTL ? 'rtl' : 'ltr'}>
      <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header avec note */}
        <div className={`relative p-6 text-center text-white bg-gradient-to-br ${gradeInfo.color} flex-shrink-0`}>
          {result.passed && (
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              {[...Array(30)].map((_, i) => (
                <div
                  key={i}
                  className="absolute w-2 h-2 animate-confetti rounded-full"
                  style={{
                    left: `${Math.random() * 100}%`,
                    animationDelay: `${Math.random() * 2}s`,
                    backgroundColor: ['#FFD700', '#FFF', '#87CEEB', '#98FB98'][Math.floor(Math.random() * 4)],
                  }}
                />
              ))}
            </div>
          )}

          <div className="relative flex items-center justify-center gap-8">
            <div>
              {result.passed ? (
                <Trophy className="w-12 h-12 mx-auto mb-2" />
              ) : (
                <Target className="w-12 h-12 mx-auto mb-2" />
              )}
              <div className="text-6xl font-black drop-shadow-lg">{result.grade}</div>
              <div className="text-xl font-bold">{gradeInfo.label}</div>
            </div>

            <div className="text-left">
              <div className="text-white/90 mb-2">
                <span className="text-3xl font-bold">{result.percentage}%</span>
                <span className="text-lg ml-2">de reussite</span>
              </div>
              <div className="flex gap-1">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    className={`w-6 h-6 ${i < gradeInfo.stars ? 'text-yellow-300 fill-yellow-300' : 'text-white/30'}`}
                  />
                ))}
              </div>
              <div className="mt-2 text-white/80 text-sm">
                {result.correctAnswers} / {result.totalQuestions} {t.exams.results.correctAnswers.toLowerCase()}
              </div>
            </div>
          </div>
        </div>

        {/* Statistiques rapides */}
        <div className="grid grid-cols-4 gap-2 p-4 bg-gray-50 border-b flex-shrink-0">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{result.correctAnswers}</div>
            <div className="text-xs text-gray-500">{t.exams.results.correctAnswers}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{incorrectAnswers.length}</div>
            <div className="text-xs text-gray-500">{t.exams.results.incorrectAnswers}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{answers.filter(a => a === null).length}</div>
            <div className="text-xs text-gray-500">{t.exams.results.unanswered}</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-amber-600">+{result.xpEarned}</div>
            <div className="text-xs text-gray-500">{t.exams.results.xpEarned}</div>
          </div>
        </div>

        {/* Tabs pour navigation */}
        <div className="flex border-b flex-shrink-0">
          <button
            onClick={() => setActiveTab('errors')}
            className={`flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 ${
              activeTab === 'errors' ? 'text-red-600 border-b-2 border-red-600 bg-red-50' : 'text-gray-500'
            }`}
          >
            <X className="w-4 h-4" />
            {t.exams.tabs.errors} ({incorrectAnswers.length})
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 ${
              activeTab === 'all' ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50' : 'text-gray-500'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            {t.exams.tabs.allAnswers} ({questions.length})
          </button>
          <button
            onClick={() => setActiveTab('summary')}
            className={`flex-1 py-3 text-sm font-medium flex items-center justify-center gap-2 ${
              activeTab === 'summary' ? 'text-green-600 border-b-2 border-green-600 bg-green-50' : 'text-gray-500'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            {t.exams.tabs.summary}
          </button>
        </div>

        {/* Contenu scrollable */}
        <div className="flex-1 overflow-y-auto p-4">
          {activeTab === 'summary' && (
            <div className="space-y-4">
              {/* Message principal */}
              <div className={`p-4 rounded-xl ${
                result.passed ? 'bg-green-50 border border-green-200' : 'bg-amber-50 border border-amber-200'
              }`}>
                {result.passed ? (
                  <div className="flex items-center gap-3">
                    <Rocket className="w-10 h-10 text-green-600" />
                    <div>
                      <h4 className="font-bold text-green-800">Felicitations !</h4>
                      <p className="text-green-700">
                        {result.examLevel
                          ? `Vous avez reussi l'examen et passez au niveau ${result.examLevel} !`
                          : 'Excellent travail ! Vous maitrisez bien ce sujet.'
                        }
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <Brain className="w-10 h-10 text-amber-600" />
                    <div>
                      <h4 className="font-bold text-amber-800">Continuez vos efforts !</h4>
                      <p className="text-amber-700">
                        Consultez les erreurs ci-dessous pour comprendre vos points faibles.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Repartition par difficulte */}
              <div className="bg-white rounded-xl border p-4">
                <h4 className="font-semibold text-gray-900 mb-3">Repartition par difficulte</h4>
                {['facile', 'moyen', 'difficile'].map(diff => {
                  const diffQuestions = questions.filter(q => q.difficulty === diff);
                  const diffCorrect = diffQuestions.filter((q, i) => {
                    const idx = questions.indexOf(q);
                    return answers[idx] === q.correctAnswer;
                  }).length;
                  const percentage = diffQuestions.length > 0 ? Math.round((diffCorrect / diffQuestions.length) * 100) : 0;

                  return (
                    <div key={diff} className="mb-3 last:mb-0">
                      <div className="flex justify-between text-sm mb-1">
                        <span className={`font-medium ${
                          diff === 'facile' ? 'text-green-700' : diff === 'moyen' ? 'text-amber-700' : 'text-red-700'
                        }`}>
                          {diff.charAt(0).toUpperCase() + diff.slice(1)}
                        </span>
                        <span className="text-gray-600">{diffCorrect}/{diffQuestions.length} ({percentage}%)</span>
                      </div>
                      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            diff === 'facile' ? 'bg-green-500' : diff === 'moyen' ? 'bg-amber-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Points a reviser */}
              {incorrectAnswers.length > 0 && (
                <div className="bg-red-50 rounded-xl border border-red-200 p-4">
                  <h4 className="font-semibold text-red-800 mb-3 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    Points a reviser
                  </h4>
                  <ul className="space-y-2">
                    {incorrectAnswers.slice(0, 5).map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-red-700">
                        <span className="text-red-400">•</span>
                        {item.question.question.substring(0, 60)}...
                      </li>
                    ))}
                    {incorrectAnswers.length > 5 && (
                      <li className="text-sm text-red-600 font-medium">
                        + {incorrectAnswers.length - 5} autres erreurs
                      </li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}

          {activeTab === 'errors' && (
            <div className="space-y-4">
              {incorrectAnswers.length === 0 ? (
                <div className="text-center py-12">
                  <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
                  <h3 className="text-xl font-bold text-gray-900">Parfait !</h3>
                  <p className="text-gray-600">Aucune erreur - Vous avez tout juste !</p>
                </div>
              ) : (
                <>
                  <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4">
                    <h3 className="font-bold text-red-800 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      {incorrectAnswers.length} erreur{incorrectAnswers.length > 1 ? 's' : ''} a comprendre
                    </h3>
                    <p className="text-red-700 text-sm mt-1">
                      Lisez attentivement les explications pour chaque erreur afin de progresser.
                    </p>
                  </div>

                  {incorrectAnswers.map((item, idx) => (
                    <div key={item.question.id} className="bg-white rounded-xl border-2 border-red-200 overflow-hidden">
                      {/* Question header */}
                      <div className="bg-red-50 p-4 border-b border-red-200">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <span className="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center font-bold text-sm">
                              {idx + 1}
                            </span>
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              item.question.difficulty === 'facile' ? 'bg-green-100 text-green-700' :
                              item.question.difficulty === 'moyen' ? 'bg-amber-100 text-amber-700' :
                              'bg-red-100 text-red-700'
                            }`}>
                              {item.question.difficulty}
                            </span>
                          </div>
                          <span className="text-sm text-red-600 font-medium">{item.question.points} pts perdus</span>
                        </div>
                        <h4 className="font-semibold text-gray-900 mt-2">{item.question.question}</h4>
                      </div>

                      {/* Reponses */}
                      <div className="p-4 space-y-2">
                        {item.question.options.map((option, optIdx) => {
                          const isUserAnswer = item.userAnswer === optIdx;
                          const isCorrect = item.question.correctAnswer === optIdx;

                          return (
                            <div
                              key={optIdx}
                              className={`p-3 rounded-lg flex items-center gap-3 ${
                                isCorrect
                                  ? 'bg-green-100 border-2 border-green-500'
                                  : isUserAnswer
                                  ? 'bg-red-100 border-2 border-red-500'
                                  : 'bg-gray-50 border border-gray-200'
                              }`}
                            >
                              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold ${
                                isCorrect
                                  ? 'bg-green-500 text-white'
                                  : isUserAnswer
                                  ? 'bg-red-500 text-white'
                                  : 'bg-gray-300 text-gray-600'
                              }`}>
                                {String.fromCharCode(65 + optIdx)}
                              </span>
                              <span className={`flex-1 ${isCorrect ? 'text-green-800 font-medium' : isUserAnswer ? 'text-red-800' : 'text-gray-700'}`}>
                                {option}
                              </span>
                              {isCorrect && <CheckCircle className="w-5 h-5 text-green-600" />}
                              {isUserAnswer && !isCorrect && <X className="w-5 h-5 text-red-600" />}
                            </div>
                          );
                        })}
                      </div>

                      {/* Explication */}
                      <div className="bg-blue-50 p-4 border-t border-blue-200">
                        <div className="flex items-start gap-3">
                          <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <h5 className="font-semibold text-blue-800 mb-1">Explication</h5>
                            <p className="text-blue-700 text-sm">{item.question.explanation}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}

          {activeTab === 'all' && (
            <div className="space-y-3">
              {questions.map((q, index) => {
                const isCorrect = answers[index] === q.correctAnswer;
                const userAnswer = answers[index];

                return (
                  <div
                    key={q.id}
                    className={`rounded-xl border-2 overflow-hidden ${
                      isCorrect ? 'border-green-300 bg-green-50' : 'border-red-300 bg-red-50'
                    }`}
                  >
                    <div className="p-3 flex items-start gap-3">
                      <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                        isCorrect ? 'bg-green-500' : 'bg-red-500'
                      }`}>
                        {isCorrect ? (
                          <CheckCircle className="w-5 h-5 text-white" />
                        ) : (
                          <X className="w-5 h-5 text-white" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 text-sm">{q.question}</p>
                        <div className="mt-2 text-sm">
                          <p className={isCorrect ? 'text-green-700' : 'text-red-700'}>
                            <span className="text-gray-500">Votre reponse: </span>
                            {userAnswer !== null ? q.options[userAnswer] : 'Non repondu'}
                          </p>
                          {!isCorrect && (
                            <p className="text-green-700 mt-1">
                              <span className="text-gray-500">Bonne reponse: </span>
                              {q.options[q.correctAnswer]}
                            </p>
                          )}
                        </div>
                        {!isCorrect && (
                          <p className="mt-2 text-xs text-blue-600 bg-blue-100 p-2 rounded">
                            <Lightbulb className="w-3 h-3 inline mr-1" />
                            {q.explanation}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">{q.points} pts</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 p-4 border-t flex-shrink-0">
          <button
            onClick={onClose}
            className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
          >
            {result.passed ? 'Continuer' : 'Fermer et reviser'}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Ancien ExamResultsDisplay - conserve pour compatibilite
 */
function OldExamResultsDisplay({
  result,
  questions,
  answers,
  onClose,
}: {
  result: {
    passed: boolean;
    grade: 'A+' | 'A' | 'B' | 'C' | 'D' | 'F';
    percentage: number;
    correctAnswers: number;
    totalQuestions: number;
    xpEarned: number;
    examLevel: number;
  };
  questions: ExamQuestion[];
  answers: (number | null)[];
  onClose: () => void;
}) {
  const [showDetails, setShowDetails] = useState(false);
  const gradeInfo = GRADE_THRESHOLDS.find(g => g.grade === result.grade)!;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-auto">
        {/* Header avec confetti si reussi */}
        <div className={`relative p-8 text-center text-white bg-gradient-to-br ${gradeInfo.color}`}>
          {result.passed && (
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              {[...Array(30)].map((_, i) => (
                <div
                  key={i}
                  className="absolute w-2 h-2 animate-confetti rounded-full"
                  style={{
                    left: `${Math.random() * 100}%`,
                    animationDelay: `${Math.random() * 2}s`,
                    backgroundColor: ['#FFD700', '#FFF', '#87CEEB', '#98FB98'][Math.floor(Math.random() * 4)],
                  }}
                />
              ))}
            </div>
          )}

          {/* Note principale */}
          <div className="relative">
            {result.passed ? (
              <Trophy className="w-16 h-16 mx-auto mb-4 animate-bounce" />
            ) : (
              <Target className="w-16 h-16 mx-auto mb-4" />
            )}

            <div className="text-8xl font-black mb-2 drop-shadow-lg">
              {result.grade}
            </div>
            <div className="text-2xl font-bold mb-1">{gradeInfo.label}</div>
            <div className="text-white/80">{result.percentage}% de bonnes reponses</div>

            {/* Etoiles */}
            <div className="flex justify-center gap-1 mt-4">
              {[...Array(5)].map((_, i) => (
                <Star
                  key={i}
                  className={`w-8 h-8 ${
                    i < gradeInfo.stars
                      ? 'text-yellow-300 fill-yellow-300'
                      : 'text-white/30'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Statistiques */}
        <div className="p-6">
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-gray-50 rounded-xl p-4 text-center">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-500" />
              <div className="text-2xl font-bold text-gray-900">{result.correctAnswers}</div>
              <div className="text-sm text-gray-500">Bonnes reponses</div>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 text-center">
              <Target className="w-8 h-8 mx-auto mb-2 text-blue-500" />
              <div className="text-2xl font-bold text-gray-900">{result.totalQuestions}</div>
              <div className="text-sm text-gray-500">Questions</div>
            </div>
            <div className="bg-gray-50 rounded-xl p-4 text-center">
              <Zap className="w-8 h-8 mx-auto mb-2 text-amber-500" />
              <div className="text-2xl font-bold text-gray-900">+{result.xpEarned}</div>
              <div className="text-sm text-gray-500">XP gagnes</div>
            </div>
          </div>

          {/* Message */}
          <div className={`p-4 rounded-xl mb-6 ${
            result.passed
              ? 'bg-green-50 border border-green-200'
              : 'bg-amber-50 border border-amber-200'
          }`}>
            {result.passed ? (
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Rocket className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h4 className="font-bold text-green-800">Felicitations !</h4>
                  <p className="text-green-700">
                    Vous avez reussi l'examen et passez au niveau {result.examLevel} !
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
                  <Brain className="w-6 h-6 text-amber-600" />
                </div>
                <div>
                  <h4 className="font-bold text-amber-800">Continuez vos efforts !</h4>
                  <p className="text-amber-700">
                    Revisez les lecons et repassez l'examen quand vous vous sentirez pret.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Bouton voir details */}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="w-full flex items-center justify-center gap-2 py-3 text-gray-600 hover:bg-gray-100 rounded-xl transition-colors"
          >
            {showDetails ? 'Masquer les details' : 'Voir les details'}
            <ChevronRight className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-90' : ''}`} />
          </button>

          {/* Details des reponses */}
          {showDetails && (
            <div className="mt-4 space-y-3 max-h-64 overflow-y-auto">
              {questions.map((q, index) => {
                const isCorrect = answers[index] === q.correctAnswer;
                return (
                  <div
                    key={q.id}
                    className={`p-4 rounded-xl border ${
                      isCorrect
                        ? 'bg-green-50 border-green-200'
                        : 'bg-red-50 border-red-200'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center ${
                        isCorrect ? 'bg-green-500' : 'bg-red-500'
                      }`}>
                        {isCorrect ? (
                          <CheckCircle className="w-4 h-4 text-white" />
                        ) : (
                          <X className="w-4 h-4 text-white" />
                        )}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 mb-1">{q.question}</p>
                        <p className="text-sm text-gray-600 mb-2">
                          <span className="text-gray-400">Votre reponse : </span>
                          <span className={isCorrect ? 'text-green-700' : 'text-red-700'}>
                            {answers[index] !== null ? q.options[answers[index]] : 'Non repondu'}
                          </span>
                        </p>
                        {!isCorrect && (
                          <p className="text-sm">
                            <span className="text-gray-400">Bonne reponse : </span>
                            <span className="text-green-700 font-medium">{q.options[q.correctAnswer]}</span>
                          </p>
                        )}
                        <p className="text-xs text-gray-500 mt-2 italic">{q.explanation}</p>
                      </div>
                      <span className="text-sm font-bold text-gray-400">{q.points} pts</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 p-4">
          <button
            onClick={onClose}
            className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
          >
            {result.passed ? 'Continuer' : 'Fermer'}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Carte de notification de passage de niveau
 */
export function LevelUpNotification({
  pendingLevel,
  onStartExam,
  onDismiss,
}: {
  pendingLevel: number;
  onStartExam: () => void;
  onDismiss: () => void;
}) {
  const exam = LEVEL_EXAMS.find(e => e.level === pendingLevel);
  const levelInfo = LEVELS.find(l => l.level === pendingLevel);

  if (!exam || !levelInfo) return null;

  return (
    <div className="fixed bottom-6 right-6 z-40 max-w-sm animate-slideUp">
      <div className="bg-white rounded-2xl shadow-2xl border-2 border-purple-200 overflow-hidden">
        <div className="bg-gradient-to-r from-purple-600 to-pink-600 p-4 text-white">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center animate-pulse">
              <Rocket className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold">Pret pour le niveau {pendingLevel} ?</h3>
              <p className="text-white/80 text-sm">Passez l'examen pour progresser</p>
            </div>
          </div>
        </div>

        <div className="p-4">
          <div className="flex items-center gap-4 mb-4">
            <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br from-${levelInfo.color}-400 to-${levelInfo.color}-600 flex items-center justify-center`}>
              <span className="text-3xl font-black text-white">{pendingLevel}</span>
            </div>
            <div>
              <h4 className="font-bold text-gray-900">{levelInfo.title}</h4>
              <p className="text-sm text-gray-500">{exam.questions.length} questions - {Math.floor(exam.duration / 60)} min</p>
              <p className="text-sm text-amber-600 flex items-center gap-1">
                <Zap className="w-3 h-3" />
                +{exam.xpReward} XP
              </p>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={onDismiss}
              className="flex-1 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Plus tard
            </button>
            <button
              onClick={onStartExam}
              className="flex-1 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:shadow-lg transition-all flex items-center justify-center gap-2"
            >
              <Play className="w-4 h-4" />
              Passer l'examen
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Historique des examens passes
 */
export function ExamHistory({ results }: { results: ExamResult[] }) {
  if (results.length === 0) {
    return (
      <div className="bg-gray-50 rounded-2xl p-8 text-center">
        <GraduationCap className="w-12 h-12 mx-auto text-gray-300 mb-3" />
        <p className="text-gray-500">Aucun examen passe pour le moment</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-4 text-white">
        <h3 className="font-bold flex items-center gap-2">
          <GraduationCap className="w-5 h-5" />
          Historique des Examens
        </h3>
      </div>
      <div className="divide-y divide-gray-100">
        {results.map((result, index) => {
          const gradeInfo = GRADE_THRESHOLDS.find(g => g.grade === result.grade)!;

          return (
            <div key={index} className="p-4 flex items-center gap-4">
              <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${gradeInfo.color} flex items-center justify-center`}>
                <span className="text-2xl font-black text-white">{result.grade}</span>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-gray-900">Niveau {result.examLevel}</h4>
                  {result.passed ? (
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">Reussi</span>
                  ) : (
                    <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">Echec</span>
                  )}
                </div>
                <p className="text-sm text-gray-500">
                  {result.correctAnswers}/{result.totalQuestions} bonnes reponses - {result.percentage}%
                </p>
                <p className="text-xs text-gray-400">
                  {new Date(result.completedAt).toLocaleDateString('fr-FR', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1 text-amber-600">
                  <Zap className="w-4 h-4" />
                  <span className="font-bold">+{result.xpEarned}</span>
                </div>
                <div className="flex gap-0.5 mt-1">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`w-3 h-3 ${
                        i < gradeInfo.stars
                          ? 'text-yellow-400 fill-yellow-400'
                          : 'text-gray-200'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Animation de celebration
 */
export function CelebrationOverlay({
  type,
  message,
  reward,
  onClose
}: {
  type: 'levelup' | 'badge' | 'achievement' | 'streak';
  message: string;
  reward?: string | number;
  onClose: () => void;
}) {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const icons = {
    levelup: <Rocket className="w-16 h-16 text-purple-500" />,
    badge: <Award className="w-16 h-16 text-yellow-500" />,
    achievement: <Trophy className="w-16 h-16 text-orange-500" />,
    streak: <Flame className="w-16 h-16 text-red-500" />,
  };

  const colors = {
    levelup: 'from-purple-500 to-pink-500',
    badge: 'from-yellow-400 to-orange-500',
    achievement: 'from-orange-500 to-red-500',
    streak: 'from-red-500 to-orange-500',
  };

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fadeIn">
      {/* Confetti effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(50)].map((_, i) => (
          <div
            key={i}
            className="absolute w-3 h-3 animate-confetti"
            style={{
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 2}s`,
              backgroundColor: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'][
                Math.floor(Math.random() * 6)
              ],
            }}
          />
        ))}
      </div>

      <div className="bg-white rounded-3xl p-8 text-center shadow-2xl animate-bounceIn max-w-sm mx-4">
        <div className={`w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-to-br ${colors[type]} flex items-center justify-center animate-pulse`}>
          {icons[type]}
        </div>

        <PartyPopper className="w-8 h-8 mx-auto text-yellow-500 mb-2 animate-bounce" />

        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          {type === 'levelup' && 'Niveau superieur !'}
          {type === 'badge' && 'Nouveau badge !'}
          {type === 'achievement' && 'Succes debloque !'}
          {type === 'streak' && 'Serie en cours !'}
        </h2>

        <p className="text-gray-600 mb-4">{message}</p>

        {reward && (
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-yellow-100 to-orange-100 px-4 py-2 rounded-full">
            <Zap className="w-5 h-5 text-yellow-600" />
            <span className="font-bold text-yellow-700">+{reward} XP</span>
          </div>
        )}

        <button
          onClick={onClose}
          className="mt-6 w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
        >
          Genial ! 🎉
        </button>
      </div>
    </div>
  );
}

/**
 * Tableau de bord gamification complet
 */
export function GamificationDashboard() {
  const { t, language, isRTL } = useI18n();
  const gamification = useGamification();
  const { profile, addXP, unlockBadge, pendingLevelUp, examResults, levelUp, recordExamResult } = gamification;

  const [showCelebration, setShowCelebration] = useState<{
    type: 'levelup' | 'badge' | 'achievement' | 'streak';
    message: string;
    reward?: number;
  } | null>(null);

  const [activeExam, setActiveExam] = useState<LevelExam | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'points' | 'exams'>('overview');

  const mockLeaderboard: LeaderboardEntry[] = [
    { rank: 1, userId: '1', displayName: 'Marie D.', avatar: '👩', level: 7, points: 3250 },
    { rank: 2, userId: '2', displayName: 'Jean P.', avatar: '👨', level: 6, points: 2890 },
    { rank: 3, userId: '3', displayName: 'Sophie M.', avatar: '👩‍💼', level: 5, points: 2340 },
    { rank: profile.rank, userId: profile.id, displayName: profile.displayName, avatar: profile.avatar, level: profile.level, points: profile.totalPoints, isCurrentUser: true },
  ];

  // Get level name from translations
  const getLevelName = (levelNum: number) => {
    return t.gamification.levels.levelNames[levelNum - 1] || t.gamification.levels.levelNames[0];
  };

  const handleCompleteChallenge = () => {
    addXP(50);
    setShowCelebration({
      type: 'achievement',
      message: t.notifications.challengeCompleted.message,
      reward: 50,
    });
  };

  const handleStartExam = (level: number) => {
    const exam = LEVEL_EXAMS.find(e => e.level === level);
    if (exam) {
      setActiveExam(exam);
    }
  };

  const handleExamComplete = (result: ExamResult) => {
    recordExamResult(result);
    if (result.passed) {
      levelUp(result.examLevel);
      setTimeout(() => {
        setShowCelebration({
          type: 'levelup',
          message: `${t.notifications.levelUp.message} ${result.examLevel} - ${getLevelName(result.examLevel)} !`,
          reward: result.xpEarned,
        });
      }, 500);
    }
    setActiveExam(null);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6" dir={isRTL ? 'rtl' : 'ltr'}>
      {/* Header avec stats + selecteur de langue */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <PlayerStatsCard profile={profile} />
        </div>
        <div className="flex-shrink-0">
          <LanguageSelector variant="dropdown" showFlag showName />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 pb-2">
        {[
          { id: 'overview', label: t.trainingHub.tabs.dashboard, icon: Target },
          { id: 'points', label: t.gamification.points.title, icon: Zap },
          { id: 'exams', label: t.exams.title, icon: GraduationCap },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-indigo-100 text-indigo-700'
                : 'text-gray-500 hover:bg-gray-100'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <>
          {/* Defis du jour */}
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-600" />
              {t.gamification.challenges.daily}
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              {DAILY_CHALLENGES.map(challenge => (
                <DailyChallengeCard
                  key={challenge.id}
                  challenge={challenge}
                  onComplete={handleCompleteChallenge}
                />
              ))}
            </div>
          </div>

          {/* Badges */}
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Award className="w-5 h-5 text-yellow-600" />
              {t.gamification.badges.title} ({profile.badges.length}/{BADGES.length})
            </h3>
            <BadgeCollection badges={profile.badges} allBadges={BADGES} />
          </div>

          {/* Classement */}
          <Leaderboard entries={mockLeaderboard} />
        </>
      )}

      {activeTab === 'points' && (
        <PointsTable actions={POINTS_ACTIONS} />
      )}

      {activeTab === 'exams' && (
        <div className="space-y-6">
          {/* Examens disponibles */}
          <div>
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-indigo-600" />
              Examens de Niveau
            </h3>
            <div className="grid gap-4">
              {LEVEL_EXAMS.map(exam => {
                const levelInfo = LEVELS.find(l => l.level === exam.level);
                const canTake = profile.level === exam.level - 1 && pendingLevelUp === exam.level;
                const passed = examResults.some(r => r.examLevel === exam.level && r.passed);
                const alreadyAtLevel = profile.level >= exam.level;

                return (
                  <div
                    key={exam.level}
                    className={`border-2 rounded-xl p-5 transition-all ${
                      passed
                        ? 'border-green-300 bg-green-50'
                        : canTake
                        ? 'border-purple-300 bg-purple-50 shadow-lg'
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                          passed
                            ? 'bg-green-500'
                            : alreadyAtLevel
                            ? `bg-${levelInfo?.color || 'gray'}-500`
                            : 'bg-gray-300'
                        }`}>
                          {passed ? (
                            <CheckCircle className="w-7 h-7 text-white" />
                          ) : alreadyAtLevel ? (
                            <span className="text-2xl font-black text-white">{exam.level}</span>
                          ) : (
                            <Lock className="w-6 h-6 text-gray-500" />
                          )}
                        </div>
                        <div>
                          <h4 className="font-bold text-gray-900">{exam.title}</h4>
                          <p className="text-sm text-gray-600">{exam.description}</p>
                          <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                            <span className="flex items-center gap-1">
                              <Target className="w-3 h-3" />
                              {exam.questions.length} questions
                            </span>
                            <span className="flex items-center gap-1">
                              <Timer className="w-3 h-3" />
                              {Math.floor(exam.duration / 60)} min
                            </span>
                            <span className="flex items-center gap-1">
                              <Zap className="w-3 h-3 text-amber-500" />
                              +{exam.xpReward} XP
                            </span>
                          </div>
                        </div>
                      </div>
                      <div>
                        {passed ? (
                          <span className="px-4 py-2 bg-green-100 text-green-700 rounded-lg font-medium flex items-center gap-2">
                            <Trophy className="w-4 h-4" />
                            Reussi
                          </span>
                        ) : canTake ? (
                          <button
                            onClick={() => handleStartExam(exam.level)}
                            className="px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:shadow-lg transition-all flex items-center gap-2"
                          >
                            <Play className="w-4 h-4" />
                            Passer l'examen
                          </button>
                        ) : alreadyAtLevel ? (
                          <span className="px-4 py-2 bg-gray-100 text-gray-500 rounded-lg font-medium">
                            Deja acquis
                          </span>
                        ) : (
                          <span className="px-4 py-2 bg-gray-100 text-gray-400 rounded-lg font-medium flex items-center gap-2">
                            <Lock className="w-4 h-4" />
                            Verrouille
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Historique */}
          <ExamHistory results={examResults} />
        </div>
      )}

      {/* Notification de niveau disponible */}
      {pendingLevelUp && !activeExam && (
        <LevelUpNotification
          pendingLevel={pendingLevelUp}
          onStartExam={() => handleStartExam(pendingLevelUp)}
          onDismiss={() => {}}
        />
      )}

      {/* Modal d'examen */}
      {activeExam && (
        <LevelExamComponent
          exam={activeExam}
          onComplete={handleExamComplete}
          onCancel={() => setActiveExam(null)}
        />
      )}

      {/* Celebration overlay */}
      {showCelebration && (
        <CelebrationOverlay
          type={showCelebration.type}
          message={showCelebration.message}
          reward={showCelebration.reward}
          onClose={() => setShowCelebration(null)}
        />
      )}
    </div>
  );
}

// ============================================================================
// STYLES CSS (a ajouter dans globals.css)
// ============================================================================

const styles = `
@keyframes confetti {
  0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
  100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
}

@keyframes bounceIn {
  0% { transform: scale(0.3); opacity: 0; }
  50% { transform: scale(1.05); }
  70% { transform: scale(0.9); }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.animate-confetti {
  animation: confetti 3s ease-out infinite;
}

.animate-bounceIn {
  animation: bounceIn 0.6s ease-out;
}

.animate-fadeIn {
  animation: fadeIn 0.3s ease-out;
}
`;

// ============================================================================
// QUIZ D'ENTRAINEMENT - COMPOSANTS
// ============================================================================

/**
 * Carte de quiz d'entrainement
 */
export function PracticeQuizCard({
  quiz,
  onStart,
  completed,
  bestScore,
}: {
  quiz: PracticeQuiz;
  onStart: () => void;
  completed?: boolean;
  bestScore?: number;
}) {
  const difficultyConfig = {
    facile: { color: 'green', label: 'Facile' },
    moyen: { color: 'amber', label: 'Moyen' },
    difficile: { color: 'red', label: 'Difficile' },
  };

  const diff = difficultyConfig[quiz.difficulty];

  return (
    <div className={`bg-white rounded-xl border-2 p-5 transition-all hover:shadow-lg ${
      completed ? 'border-green-300' : 'border-gray-200 hover:border-blue-300'
    }`}>
      <div className="flex items-start gap-4">
        <div className={`w-14 h-14 rounded-xl bg-${quiz.color}-100 flex items-center justify-center text-2xl`}>
          {quiz.icon}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900">{quiz.title}</h3>
            {completed && <CheckCircle className="w-5 h-5 text-green-500" />}
          </div>
          <p className="text-sm text-gray-600 mb-2">{quiz.description}</p>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className={`px-2 py-1 rounded-full bg-${diff.color}-100 text-${diff.color}-700`}>
              {diff.label}
            </span>
            <span className="px-2 py-1 rounded-full bg-gray-100 text-gray-600">
              {quiz.questions.length} questions
            </span>
            <span className="px-2 py-1 rounded-full bg-gray-100 text-gray-600">
              ~{quiz.duration} min
            </span>
            <span className="px-2 py-1 rounded-full bg-amber-100 text-amber-700">
              +{quiz.xpReward} XP
            </span>
          </div>
          {bestScore !== undefined && (
            <div className="mt-2 text-sm">
              <span className="text-gray-500">Meilleur score: </span>
              <span className={`font-bold ${bestScore >= 80 ? 'text-green-600' : bestScore >= 60 ? 'text-amber-600' : 'text-red-600'}`}>
                {bestScore}%
              </span>
            </div>
          )}
        </div>
        <button
          onClick={onStart}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            completed
              ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {completed ? 'Refaire' : 'Commencer'}
        </button>
      </div>
    </div>
  );
}

/**
 * Interface de quiz d'entrainement avec feedback immediat apres chaque question
 */
export function PracticeQuizPlayer({
  quiz,
  onComplete,
  onCancel,
}: {
  quiz: PracticeQuiz;
  onComplete: (result: { score: number; percentage: number; xpEarned: number }) => void;
  onCancel: () => void;
}) {
  const { t, isRTL } = useI18n();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>(new Array(quiz.questions.length).fill(null));
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isFinished, setIsFinished] = useState(false);

  const question = quiz.questions[currentQuestion];
  const isCorrect = selectedAnswer === question.correctAnswer;
  const progress = ((currentQuestion + 1) / quiz.questions.length) * 100;

  const handleSelectAnswer = (index: number) => {
    if (showFeedback) return;
    setSelectedAnswer(index);
  };

  const handleConfirm = () => {
    if (selectedAnswer === null) return;

    // Enregistrer la reponse
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = selectedAnswer;
    setAnswers(newAnswers);

    // Afficher le feedback immediat
    setShowFeedback(true);
  };

  const handleNext = () => {
    if (currentQuestion < quiz.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
      setSelectedAnswer(null);
      setShowFeedback(false);
    } else {
      setIsFinished(true);
    }
  };

  // Calcul des resultats
  const calculateResults = () => {
    let correctCount = 0;
    let totalPoints = 0;
    let maxPoints = 0;

    quiz.questions.forEach((q, i) => {
      maxPoints += q.points;
      if (answers[i] === q.correctAnswer) {
        correctCount++;
        totalPoints += q.points;
      }
    });

    const percentage = Math.round((totalPoints / maxPoints) * 100);
    const xpEarned = Math.round(quiz.xpReward * (percentage / 100));

    return { correctCount, totalPoints, maxPoints, percentage, xpEarned };
  };

  // Afficher les resultats finaux avec details des erreurs
  if (isFinished) {
    const results = calculateResults();
    const gradeInfo = GRADE_THRESHOLDS.find(g => results.percentage >= g.min)!;

    return (
      <ExamResultsDisplay
        result={{
          passed: results.percentage >= 60,
          grade: gradeInfo.grade,
          percentage: results.percentage,
          correctAnswers: results.correctCount,
          totalQuestions: quiz.questions.length,
          xpEarned: results.xpEarned,
        }}
        questions={quiz.questions}
        answers={answers}
        onClose={() => onComplete({
          score: results.totalPoints,
          percentage: results.percentage,
          xpEarned: results.xpEarned,
        })}
      />
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-4 text-white">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{quiz.icon}</span>
              <div>
                <h2 className="font-bold">{quiz.title}</h2>
                <p className="text-sm text-white/80">Question {currentQuestion + 1} / {quiz.questions.length}</p>
              </div>
            </div>
            <button onClick={onCancel} className="p-2 hover:bg-white/20 rounded-lg">
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="w-full h-2 bg-white/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-white rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Question */}
        <div className="flex-1 p-6 overflow-y-auto">
          <div className="flex items-center gap-2 mb-4">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              question.difficulty === 'facile' ? 'bg-green-100 text-green-700' :
              question.difficulty === 'moyen' ? 'bg-amber-100 text-amber-700' :
              'bg-red-100 text-red-700'
            }`}>
              {question.difficulty}
            </span>
            <span className="text-sm text-gray-500">{question.points} points</span>
          </div>

          <h3 className="text-xl font-semibold text-gray-900 mb-6">{question.question}</h3>

          <div className="space-y-3">
            {question.options.map((option, index) => {
              const isSelected = selectedAnswer === index;
              const isCorrectAnswer = index === question.correctAnswer;
              const showAsCorrect = showFeedback && isCorrectAnswer;
              const showAsWrong = showFeedback && isSelected && !isCorrectAnswer;

              return (
                <button
                  key={index}
                  onClick={() => handleSelectAnswer(index)}
                  disabled={showFeedback}
                  className={`w-full p-4 rounded-xl text-left transition-all flex items-center gap-3 ${
                    showAsCorrect
                      ? 'bg-green-100 border-2 border-green-500 ring-2 ring-green-200'
                      : showAsWrong
                      ? 'bg-red-100 border-2 border-red-500 ring-2 ring-red-200'
                      : isSelected
                      ? 'bg-blue-100 border-2 border-blue-500'
                      : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100 hover:border-gray-300'
                  }`}
                >
                  <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                    showAsCorrect
                      ? 'bg-green-500 text-white'
                      : showAsWrong
                      ? 'bg-red-500 text-white'
                      : isSelected
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}>
                    {showAsCorrect ? <CheckCircle className="w-5 h-5" /> :
                     showAsWrong ? <X className="w-5 h-5" /> :
                     String.fromCharCode(65 + index)}
                  </span>
                  <span className={`flex-1 ${
                    showAsCorrect ? 'text-green-800 font-medium' :
                    showAsWrong ? 'text-red-800' :
                    isSelected ? 'text-blue-800 font-medium' :
                    'text-gray-700'
                  }`}>
                    {option}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Feedback immediat apres chaque reponse */}
          {showFeedback && (
            <div className={`mt-6 p-4 rounded-xl ${
              isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-start gap-3">
                {isCorrect ? (
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0" />
                ) : (
                  <X className="w-6 h-6 text-red-600 flex-shrink-0" />
                )}
                <div>
                  <h4 className={`font-bold ${isCorrect ? 'text-green-800' : 'text-red-800'}`}>
                    {isCorrect ? t.practiceQuizzes.feedback.correct : t.practiceQuizzes.feedback.incorrect}
                  </h4>
                  <p className={`mt-1 ${isCorrect ? 'text-green-700' : 'text-red-700'}`}>
                    {question.explanation}
                  </p>
                  {!isCorrect && (
                    <p className="mt-2 text-sm">
                      <span className="text-gray-500">{t.practiceQuizzes.feedback.correctAnswerWas}: </span>
                      <span className="font-medium text-green-700">
                        {question.options[question.correctAnswer]}
                      </span>
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 p-4 border-t flex justify-between">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg"
          >
            {t.general.quit}
          </button>
          {!showFeedback ? (
            <button
              onClick={handleConfirm}
              disabled={selectedAnswer === null}
              className={`px-6 py-2 rounded-xl font-medium ${
                selectedAnswer !== null
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              Valider ma reponse
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="px-6 py-2 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 flex items-center gap-2"
            >
              {currentQuestion < quiz.questions.length - 1 ? (
                <>Question suivante <ChevronRight className="w-4 h-4" /></>
              ) : (
                <>Voir mes resultats</>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Bibliotheque des quiz d'entrainement par categorie
 */
export function PracticeQuizLibrary() {
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [activeQuiz, setActiveQuiz] = useState<PracticeQuiz | null>(null);
  const [completedQuizzes, setCompletedQuizzes] = useState<Record<string, number>>({});

  // Charger les scores sauvegardes
  useEffect(() => {
    const saved = localStorage.getItem('azalscore_practice_quiz_scores');
    if (saved) {
      setCompletedQuizzes(JSON.parse(saved));
    }
  }, []);

  const categories = ['all', ...new Set(PRACTICE_QUIZZES.map(q => q.category))];

  const filteredQuizzes = activeCategory === 'all'
    ? PRACTICE_QUIZZES
    : PRACTICE_QUIZZES.filter(q => q.category === activeCategory);

  const handleQuizComplete = (quizId: string, result: { percentage: number; xpEarned: number }) => {
    const newScores = {
      ...completedQuizzes,
      [quizId]: Math.max(completedQuizzes[quizId] || 0, result.percentage),
    };
    setCompletedQuizzes(newScores);
    localStorage.setItem('azalscore_practice_quiz_scores', JSON.stringify(newScores));
    setActiveQuiz(null);
  };

  // Statistiques globales
  const totalQuizzes = PRACTICE_QUIZZES.length;
  const completedCount = Object.keys(completedQuizzes).length;
  const avgScore = completedCount > 0
    ? Math.round(Object.values(completedQuizzes).reduce((a, b) => a + b, 0) / completedCount)
    : 0;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header avec statistiques */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-6 text-white mb-6">
        <div className="flex items-center gap-3 mb-4">
          <FileQuestion className="w-8 h-8" />
          <div>
            <h2 className="text-2xl font-bold">Quiz d'Entrainement</h2>
            <p className="text-white/80">Testez vos connaissances avec feedback immediat</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white/20 rounded-xl p-3 text-center">
            <div className="text-2xl font-bold">{completedCount}/{totalQuizzes}</div>
            <div className="text-sm text-white/80">Quiz completes</div>
          </div>
          <div className="bg-white/20 rounded-xl p-3 text-center">
            <div className="text-2xl font-bold">{avgScore}%</div>
            <div className="text-sm text-white/80">Score moyen</div>
          </div>
          <div className="bg-white/20 rounded-xl p-3 text-center">
            <div className="text-2xl font-bold">
              {PRACTICE_QUIZZES.reduce((sum, q) => sum + q.questions.length, 0)}
            </div>
            <div className="text-sm text-white/80">Questions totales</div>
          </div>
        </div>
      </div>

      {/* Filtres par categorie */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setActiveCategory(cat)}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
              activeCategory === cat
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {cat === 'all' ? 'Tous les quiz' : cat}
          </button>
        ))}
      </div>

      {/* Liste des quiz */}
      <div className="space-y-4">
        {filteredQuizzes.map(quiz => (
          <PracticeQuizCard
            key={quiz.id}
            quiz={quiz}
            onStart={() => setActiveQuiz(quiz)}
            completed={completedQuizzes[quiz.id] !== undefined}
            bestScore={completedQuizzes[quiz.id]}
          />
        ))}
      </div>

      {/* Modal du quiz actif */}
      {activeQuiz && (
        <PracticeQuizPlayer
          quiz={activeQuiz}
          onComplete={(result) => handleQuizComplete(activeQuiz.id, result)}
          onCancel={() => setActiveQuiz(null)}
        />
      )}
    </div>
  );
}

// ============================================================================
// STYLES CSS (a ajouter dans globals.css)
// ============================================================================

const additionalStyles = `
@keyframes slideUp {
  from { transform: translateY(100px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.animate-slideUp {
  animation: slideUp 0.4s ease-out;
}
`;

// Re-export i18n for convenience
export { useI18n, I18nProvider, LanguageSelector } from '../i18n';
export { getLevelExams, getPracticeQuizzes, getExamByLevel, getQuizById } from '../i18n/examQuestions';

export default {
  // Hooks & Context
  useGamification,
  GamificationProvider,

  // Composants principaux
  XPProgressBar,
  PlayerStatsCard,
  DailyChallengeCard,
  BadgeCollection,
  Leaderboard,
  CelebrationOverlay,
  GamificationDashboard,

  // Systeme d'examen
  LevelExamComponent,
  ExamResultsDisplay,
  ExamHistory,
  LevelUpNotification,
  PointsTable,

  // Quiz d'entrainement
  PracticeQuizCard,
  PracticeQuizPlayer,
  PracticeQuizLibrary,

  // Constantes
  BADGES,
  LEVELS,
  POINTS_ACTIONS,
  LEVEL_EXAMS,
  GRADE_THRESHOLDS,
  PRACTICE_QUIZZES,

  // i18n
  useI18n,
  I18nProvider,
  LanguageSelector,
};
