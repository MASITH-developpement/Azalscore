/**
 * AZALSCORE - Systeme de Traductions (i18n)
 * ==========================================
 * Support multi-langue pour le module de formation
 */

export type SupportedLanguage = 'fr' | 'en' | 'es' | 'de' | 'ar';

export interface TranslationStrings {
  // General
  general: {
    loading: string;
    error: string;
    success: string;
    cancel: string;
    confirm: string;
    close: string;
    save: string;
    next: string;
    previous: string;
    finish: string;
    retry: string;
    start: string;
    continue: string;
    quit: string;
    back: string;
    seeAll: string;
    seeMore: string;
    seeLess: string;
    search: string;
    filter: string;
    all: string;
    none: string;
    yes: string;
    no: string;
    or: string;
    and: string;
    points: string;
    minutes: string;
    seconds: string;
    hours: string;
    days: string;
    level: string;
    xp: string;
  };

  // Gamification
  gamification: {
    // Niveaux
    levels: {
      title: string;
      currentLevel: string;
      nextLevel: string;
      xpToNext: string;
      maxLevel: string;
      levelNames: string[];
    };

    // Points
    points: {
      title: string;
      total: string;
      earned: string;
      categories: {
        learning: string;
        practice: string;
        social: string;
        exam: string;
      };
      actions: {
        completeTour: string;
        completeLesson: string;
        watchVideo: string;
        readArticle: string;
        completeQuiz: string;
        perfectQuiz: string;
        completeExercise: string;
        useFeature: string;
        dailyLogin: string;
        streak3Days: string;
        streak7Days: string;
        streak30Days: string;
        helpColleague: string;
        shareKnowledge: string;
        writeComment: string;
        passExam: string;
        passExamFirst: string;
        perfectExam: string;
        levelUp: string;
      };
    };

    // Badges
    badges: {
      title: string;
      unlocked: string;
      locked: string;
      progress: string;
      rarity: {
        common: string;
        rare: string;
        epic: string;
        legendary: string;
      };
      names: {
        firstSteps: string;
        explorer: string;
        learner: string;
        expert: string;
        master: string;
        perfectionist: string;
        speedRunner: string;
        dedicated: string;
        helpful: string;
        champion: string;
      };
      descriptions: {
        firstSteps: string;
        explorer: string;
        learner: string;
        expert: string;
        master: string;
        perfectionist: string;
        speedRunner: string;
        dedicated: string;
        helpful: string;
        champion: string;
      };
    };

    // Defis
    challenges: {
      title: string;
      daily: string;
      weekly: string;
      special: string;
      completed: string;
      inProgress: string;
      timeRemaining: string;
      reward: string;
      difficulty: {
        easy: string;
        medium: string;
        hard: string;
      };
    };

    // Classement
    leaderboard: {
      title: string;
      rank: string;
      player: string;
      score: string;
      yourRank: string;
      top10: string;
      thisWeek: string;
      thisMonth: string;
      allTime: string;
    };

    // Streak
    streak: {
      title: string;
      currentStreak: string;
      bestStreak: string;
      keepItUp: string;
      streakLost: string;
      daysInRow: string;
    };
  };

  // Examens
  exams: {
    title: string;
    levelExam: string;
    practiceQuiz: string;
    startExam: string;
    continueExam: string;
    timeRemaining: string;
    question: string;
    questionOf: string;
    selectAnswer: string;
    confirmAnswer: string;
    nextQuestion: string;
    previousQuestion: string;
    submitExam: string;

    // Resultats
    results: {
      title: string;
      passed: string;
      failed: string;
      score: string;
      percentage: string;
      correctAnswers: string;
      incorrectAnswers: string;
      unanswered: string;
      xpEarned: string;
      timeSpent: string;
      grade: string;
      stars: string;

      // Notes
      grades: {
        excellent: string;
        veryGood: string;
        good: string;
        satisfactory: string;
        passable: string;
        insufficient: string;
      };

      // Messages
      messages: {
        congratulations: string;
        levelUp: string;
        tryAgain: string;
        almostThere: string;
        keepLearning: string;
        perfectScore: string;
      };
    };

    // Erreurs
    errors: {
      title: string;
      yourAnswer: string;
      correctAnswer: string;
      explanation: string;
      noErrors: string;
      reviewErrors: string;
    };

    // Tabs
    tabs: {
      errors: string;
      allAnswers: string;
      summary: string;
    };

    // Difficulte
    difficulty: {
      easy: string;
      medium: string;
      hard: string;
    };

    // Historique
    history: {
      title: string;
      noExams: string;
      date: string;
      score: string;
      passed: string;
      failed: string;
      retake: string;
    };
  };

  // Quiz d'entrainement
  practiceQuizzes: {
    title: string;
    subtitle: string;
    categories: {
      all: string;
      navigation: string;
      crm: string;
      invoicing: string;
      accounting: string;
      inventory: string;
      ai: string;
      admin: string;
    };
    startQuiz: string;
    questionsCount: string;
    duration: string;
    difficulty: string;
    xpReward: string;
    completed: string;
    bestScore: string;

    // Feedback immediat
    feedback: {
      correct: string;
      incorrect: string;
      correctAnswerWas: string;
    };
  };

  // Notifications
  notifications: {
    levelUp: {
      title: string;
      message: string;
      newLevel: string;
      unlocked: string;
    };
    badgeUnlocked: {
      title: string;
      message: string;
    };
    challengeCompleted: {
      title: string;
      message: string;
    };
    streakMilestone: {
      title: string;
      message: string;
    };
    examPassed: {
      title: string;
      message: string;
    };
  };

  // Training Hub
  trainingHub: {
    title: string;
    subtitle: string;
    tabs: {
      dashboard: string;
      lessons: string;
      quizzes: string;
      games: string;
      progress: string;
    };
    welcome: string;
    continueTraining: string;
    recommendedForYou: string;
    yourProgress: string;
  };
}

// ============================================================================
// TRADUCTIONS FRANCAISES
// ============================================================================

export const FR: TranslationStrings = {
  general: {
    loading: 'Chargement...',
    error: 'Erreur',
    success: 'Succes',
    cancel: 'Annuler',
    confirm: 'Confirmer',
    close: 'Fermer',
    save: 'Enregistrer',
    next: 'Suivant',
    previous: 'Precedent',
    finish: 'Terminer',
    retry: 'Reessayer',
    start: 'Commencer',
    continue: 'Continuer',
    quit: 'Quitter',
    back: 'Retour',
    seeAll: 'Voir tout',
    seeMore: 'Voir plus',
    seeLess: 'Voir moins',
    search: 'Rechercher',
    filter: 'Filtrer',
    all: 'Tout',
    none: 'Aucun',
    yes: 'Oui',
    no: 'Non',
    or: 'ou',
    and: 'et',
    points: 'points',
    minutes: 'minutes',
    seconds: 'secondes',
    hours: 'heures',
    days: 'jours',
    level: 'Niveau',
    xp: 'XP',
  },

  gamification: {
    levels: {
      title: 'Niveaux',
      currentLevel: 'Niveau actuel',
      nextLevel: 'Prochain niveau',
      xpToNext: 'XP pour le prochain niveau',
      maxLevel: 'Niveau maximum atteint !',
      levelNames: [
        'Debutant',
        'Apprenti',
        'Initie',
        'Competent',
        'Confirme',
        'Expert',
        'Maitre',
        'Grand Maitre',
      ],
    },

    points: {
      title: 'Points',
      total: 'Total des points',
      earned: 'Points gagnes',
      categories: {
        learning: 'Apprentissage',
        practice: 'Pratique',
        social: 'Social',
        exam: 'Examens',
      },
      actions: {
        completeTour: 'Terminer un tour guide',
        completeLesson: 'Terminer une lecon',
        watchVideo: 'Regarder une video',
        readArticle: 'Lire un article',
        completeQuiz: 'Terminer un quiz',
        perfectQuiz: 'Quiz parfait (100%)',
        completeExercise: 'Terminer un exercice pratique',
        useFeature: 'Utiliser une nouvelle fonctionnalite',
        dailyLogin: 'Connexion quotidienne',
        streak3Days: 'Serie de 3 jours',
        streak7Days: 'Serie de 7 jours',
        streak30Days: 'Serie de 30 jours',
        helpColleague: 'Aider un collegue',
        shareKnowledge: 'Partager une connaissance',
        writeComment: 'Ecrire un commentaire utile',
        passExam: 'Reussir un examen',
        passExamFirst: 'Reussir du premier coup',
        perfectExam: 'Examen parfait (100%)',
        levelUp: 'Passer au niveau superieur',
      },
    },

    badges: {
      title: 'Badges',
      unlocked: 'Debloques',
      locked: 'Verrouilles',
      progress: 'Progression',
      rarity: {
        common: 'Commun',
        rare: 'Rare',
        epic: 'Epique',
        legendary: 'Legendaire',
      },
      names: {
        firstSteps: 'Premiers Pas',
        explorer: 'Explorateur',
        learner: 'Apprenant',
        expert: 'Expert',
        master: 'Maitre',
        perfectionist: 'Perfectionniste',
        speedRunner: 'Rapide',
        dedicated: 'Dedie',
        helpful: 'Entraide',
        champion: 'Champion',
      },
      descriptions: {
        firstSteps: 'Completer votre premier tour guide',
        explorer: 'Visiter tous les modules de l\'application',
        learner: 'Terminer 10 lecons',
        expert: 'Atteindre le niveau Expert',
        master: 'Atteindre le niveau Maitre',
        perfectionist: 'Obtenir 100% a 5 examens',
        speedRunner: 'Terminer un examen en moins de 5 minutes',
        dedicated: 'Maintenir une serie de 30 jours',
        helpful: 'Aider 10 collegues',
        champion: 'Atteindre le top 3 du classement',
      },
    },

    challenges: {
      title: 'Defis',
      daily: 'Defi du jour',
      weekly: 'Defi de la semaine',
      special: 'Defi special',
      completed: 'Termine',
      inProgress: 'En cours',
      timeRemaining: 'Temps restant',
      reward: 'Recompense',
      difficulty: {
        easy: 'Facile',
        medium: 'Moyen',
        hard: 'Difficile',
      },
    },

    leaderboard: {
      title: 'Classement',
      rank: 'Rang',
      player: 'Joueur',
      score: 'Score',
      yourRank: 'Votre classement',
      top10: 'Top 10',
      thisWeek: 'Cette semaine',
      thisMonth: 'Ce mois',
      allTime: 'Tous les temps',
    },

    streak: {
      title: 'Serie',
      currentStreak: 'Serie actuelle',
      bestStreak: 'Meilleure serie',
      keepItUp: 'Continuez comme ca !',
      streakLost: 'Serie perdue',
      daysInRow: 'jours consecutifs',
    },
  },

  exams: {
    title: 'Examens',
    levelExam: 'Examen de niveau',
    practiceQuiz: 'Quiz d\'entrainement',
    startExam: 'Commencer l\'examen',
    continueExam: 'Continuer l\'examen',
    timeRemaining: 'Temps restant',
    question: 'Question',
    questionOf: 'sur',
    selectAnswer: 'Selectionnez une reponse',
    confirmAnswer: 'Confirmer',
    nextQuestion: 'Question suivante',
    previousQuestion: 'Question precedente',
    submitExam: 'Terminer l\'examen',

    results: {
      title: 'Resultats',
      passed: 'Reussi !',
      failed: 'Echec',
      score: 'Score',
      percentage: 'de reussite',
      correctAnswers: 'Bonnes reponses',
      incorrectAnswers: 'Mauvaises reponses',
      unanswered: 'Non repondues',
      xpEarned: 'XP gagnes',
      timeSpent: 'Temps passe',
      grade: 'Note',
      stars: 'Etoiles',

      grades: {
        excellent: 'Excellent',
        veryGood: 'Tres Bien',
        good: 'Bien',
        satisfactory: 'Assez Bien',
        passable: 'Passable',
        insufficient: 'Insuffisant',
      },

      messages: {
        congratulations: 'Felicitations !',
        levelUp: 'Vous passez au niveau',
        tryAgain: 'Reessayez pour progresser',
        almostThere: 'Vous y etes presque !',
        keepLearning: 'Continuez votre apprentissage',
        perfectScore: 'Score parfait !',
      },
    },

    errors: {
      title: 'Erreurs a corriger',
      yourAnswer: 'Votre reponse',
      correctAnswer: 'Bonne reponse',
      explanation: 'Explication',
      noErrors: 'Aucune erreur ! Parfait !',
      reviewErrors: 'Revoir les erreurs',
    },

    tabs: {
      errors: 'Erreurs a corriger',
      allAnswers: 'Toutes les reponses',
      summary: 'Resume',
    },

    difficulty: {
      easy: 'Facile',
      medium: 'Moyen',
      hard: 'Difficile',
    },

    history: {
      title: 'Historique des examens',
      noExams: 'Aucun examen passe',
      date: 'Date',
      score: 'Score',
      passed: 'Reussi',
      failed: 'Echec',
      retake: 'Repasser',
    },
  },

  practiceQuizzes: {
    title: 'Quiz d\'entrainement',
    subtitle: 'Testez vos connaissances avec des quiz thematiques',
    categories: {
      all: 'Tous',
      navigation: 'Navigation',
      crm: 'CRM & Clients',
      invoicing: 'Facturation',
      accounting: 'Comptabilite',
      inventory: 'Stocks',
      ai: 'Intelligence Artificielle',
      admin: 'Administration',
    },
    startQuiz: 'Commencer le quiz',
    questionsCount: 'questions',
    duration: 'Duree estimee',
    difficulty: 'Difficulte',
    xpReward: 'Recompense XP',
    completed: 'Termine',
    bestScore: 'Meilleur score',

    feedback: {
      correct: 'Bonne reponse !',
      incorrect: 'Mauvaise reponse',
      correctAnswerWas: 'La bonne reponse etait',
    },
  },

  notifications: {
    levelUp: {
      title: 'Niveau Superieur !',
      message: 'Vous avez atteint le niveau',
      newLevel: 'Nouveau niveau',
      unlocked: 'Debloques',
    },
    badgeUnlocked: {
      title: 'Badge Debloqueee !',
      message: 'Vous avez obtenu le badge',
    },
    challengeCompleted: {
      title: 'Defi Termine !',
      message: 'Vous avez complete le defi',
    },
    streakMilestone: {
      title: 'Serie !',
      message: 'Vous avez atteint une serie de',
    },
    examPassed: {
      title: 'Examen Reussi !',
      message: 'Felicitations pour votre reussite',
    },
  },

  trainingHub: {
    title: 'Centre de Formation',
    subtitle: 'Apprenez a maitriser AZALSCORE',
    tabs: {
      dashboard: 'Tableau de bord',
      lessons: 'Lecons',
      quizzes: 'Quiz',
      games: 'Jeux',
      progress: 'Progression',
    },
    welcome: 'Bienvenue',
    continueTraining: 'Continuer la formation',
    recommendedForYou: 'Recommande pour vous',
    yourProgress: 'Votre progression',
  },
};

// ============================================================================
// TRADUCTIONS ANGLAISES
// ============================================================================

export const EN: TranslationStrings = {
  general: {
    loading: 'Loading...',
    error: 'Error',
    success: 'Success',
    cancel: 'Cancel',
    confirm: 'Confirm',
    close: 'Close',
    save: 'Save',
    next: 'Next',
    previous: 'Previous',
    finish: 'Finish',
    retry: 'Retry',
    start: 'Start',
    continue: 'Continue',
    quit: 'Quit',
    back: 'Back',
    seeAll: 'See all',
    seeMore: 'See more',
    seeLess: 'See less',
    search: 'Search',
    filter: 'Filter',
    all: 'All',
    none: 'None',
    yes: 'Yes',
    no: 'No',
    or: 'or',
    and: 'and',
    points: 'points',
    minutes: 'minutes',
    seconds: 'seconds',
    hours: 'hours',
    days: 'days',
    level: 'Level',
    xp: 'XP',
  },

  gamification: {
    levels: {
      title: 'Levels',
      currentLevel: 'Current level',
      nextLevel: 'Next level',
      xpToNext: 'XP to next level',
      maxLevel: 'Maximum level reached!',
      levelNames: [
        'Beginner',
        'Apprentice',
        'Initiate',
        'Competent',
        'Proficient',
        'Expert',
        'Master',
        'Grand Master',
      ],
    },

    points: {
      title: 'Points',
      total: 'Total points',
      earned: 'Points earned',
      categories: {
        learning: 'Learning',
        practice: 'Practice',
        social: 'Social',
        exam: 'Exams',
      },
      actions: {
        completeTour: 'Complete a guided tour',
        completeLesson: 'Complete a lesson',
        watchVideo: 'Watch a video',
        readArticle: 'Read an article',
        completeQuiz: 'Complete a quiz',
        perfectQuiz: 'Perfect quiz (100%)',
        completeExercise: 'Complete a practical exercise',
        useFeature: 'Use a new feature',
        dailyLogin: 'Daily login',
        streak3Days: '3-day streak',
        streak7Days: '7-day streak',
        streak30Days: '30-day streak',
        helpColleague: 'Help a colleague',
        shareKnowledge: 'Share knowledge',
        writeComment: 'Write a helpful comment',
        passExam: 'Pass an exam',
        passExamFirst: 'Pass on first try',
        perfectExam: 'Perfect exam (100%)',
        levelUp: 'Level up',
      },
    },

    badges: {
      title: 'Badges',
      unlocked: 'Unlocked',
      locked: 'Locked',
      progress: 'Progress',
      rarity: {
        common: 'Common',
        rare: 'Rare',
        epic: 'Epic',
        legendary: 'Legendary',
      },
      names: {
        firstSteps: 'First Steps',
        explorer: 'Explorer',
        learner: 'Learner',
        expert: 'Expert',
        master: 'Master',
        perfectionist: 'Perfectionist',
        speedRunner: 'Speed Runner',
        dedicated: 'Dedicated',
        helpful: 'Helpful',
        champion: 'Champion',
      },
      descriptions: {
        firstSteps: 'Complete your first guided tour',
        explorer: 'Visit all application modules',
        learner: 'Complete 10 lessons',
        expert: 'Reach Expert level',
        master: 'Reach Master level',
        perfectionist: 'Get 100% on 5 exams',
        speedRunner: 'Complete an exam in under 5 minutes',
        dedicated: 'Maintain a 30-day streak',
        helpful: 'Help 10 colleagues',
        champion: 'Reach top 3 on the leaderboard',
      },
    },

    challenges: {
      title: 'Challenges',
      daily: 'Daily challenge',
      weekly: 'Weekly challenge',
      special: 'Special challenge',
      completed: 'Completed',
      inProgress: 'In progress',
      timeRemaining: 'Time remaining',
      reward: 'Reward',
      difficulty: {
        easy: 'Easy',
        medium: 'Medium',
        hard: 'Hard',
      },
    },

    leaderboard: {
      title: 'Leaderboard',
      rank: 'Rank',
      player: 'Player',
      score: 'Score',
      yourRank: 'Your rank',
      top10: 'Top 10',
      thisWeek: 'This week',
      thisMonth: 'This month',
      allTime: 'All time',
    },

    streak: {
      title: 'Streak',
      currentStreak: 'Current streak',
      bestStreak: 'Best streak',
      keepItUp: 'Keep it up!',
      streakLost: 'Streak lost',
      daysInRow: 'days in a row',
    },
  },

  exams: {
    title: 'Exams',
    levelExam: 'Level exam',
    practiceQuiz: 'Practice quiz',
    startExam: 'Start exam',
    continueExam: 'Continue exam',
    timeRemaining: 'Time remaining',
    question: 'Question',
    questionOf: 'of',
    selectAnswer: 'Select an answer',
    confirmAnswer: 'Confirm',
    nextQuestion: 'Next question',
    previousQuestion: 'Previous question',
    submitExam: 'Submit exam',

    results: {
      title: 'Results',
      passed: 'Passed!',
      failed: 'Failed',
      score: 'Score',
      percentage: 'success rate',
      correctAnswers: 'Correct answers',
      incorrectAnswers: 'Incorrect answers',
      unanswered: 'Unanswered',
      xpEarned: 'XP earned',
      timeSpent: 'Time spent',
      grade: 'Grade',
      stars: 'Stars',

      grades: {
        excellent: 'Excellent',
        veryGood: 'Very Good',
        good: 'Good',
        satisfactory: 'Satisfactory',
        passable: 'Passable',
        insufficient: 'Insufficient',
      },

      messages: {
        congratulations: 'Congratulations!',
        levelUp: 'You reached level',
        tryAgain: 'Try again to improve',
        almostThere: 'Almost there!',
        keepLearning: 'Keep learning',
        perfectScore: 'Perfect score!',
      },
    },

    errors: {
      title: 'Errors to review',
      yourAnswer: 'Your answer',
      correctAnswer: 'Correct answer',
      explanation: 'Explanation',
      noErrors: 'No errors! Perfect!',
      reviewErrors: 'Review errors',
    },

    tabs: {
      errors: 'Errors to review',
      allAnswers: 'All answers',
      summary: 'Summary',
    },

    difficulty: {
      easy: 'Easy',
      medium: 'Medium',
      hard: 'Hard',
    },

    history: {
      title: 'Exam history',
      noExams: 'No exams taken',
      date: 'Date',
      score: 'Score',
      passed: 'Passed',
      failed: 'Failed',
      retake: 'Retake',
    },
  },

  practiceQuizzes: {
    title: 'Practice Quizzes',
    subtitle: 'Test your knowledge with themed quizzes',
    categories: {
      all: 'All',
      navigation: 'Navigation',
      crm: 'CRM & Clients',
      invoicing: 'Invoicing',
      accounting: 'Accounting',
      inventory: 'Inventory',
      ai: 'Artificial Intelligence',
      admin: 'Administration',
    },
    startQuiz: 'Start quiz',
    questionsCount: 'questions',
    duration: 'Estimated duration',
    difficulty: 'Difficulty',
    xpReward: 'XP reward',
    completed: 'Completed',
    bestScore: 'Best score',

    feedback: {
      correct: 'Correct!',
      incorrect: 'Incorrect',
      correctAnswerWas: 'The correct answer was',
    },
  },

  notifications: {
    levelUp: {
      title: 'Level Up!',
      message: 'You reached level',
      newLevel: 'New level',
      unlocked: 'Unlocked',
    },
    badgeUnlocked: {
      title: 'Badge Unlocked!',
      message: 'You earned the badge',
    },
    challengeCompleted: {
      title: 'Challenge Completed!',
      message: 'You completed the challenge',
    },
    streakMilestone: {
      title: 'Streak!',
      message: 'You reached a streak of',
    },
    examPassed: {
      title: 'Exam Passed!',
      message: 'Congratulations on your success',
    },
  },

  trainingHub: {
    title: 'Training Center',
    subtitle: 'Learn to master AZALSCORE',
    tabs: {
      dashboard: 'Dashboard',
      lessons: 'Lessons',
      quizzes: 'Quizzes',
      games: 'Games',
      progress: 'Progress',
    },
    welcome: 'Welcome',
    continueTraining: 'Continue training',
    recommendedForYou: 'Recommended for you',
    yourProgress: 'Your progress',
  },
};

// ============================================================================
// TRADUCTIONS ESPAGNOLES
// ============================================================================

export const ES: TranslationStrings = {
  general: {
    loading: 'Cargando...',
    error: 'Error',
    success: 'Exito',
    cancel: 'Cancelar',
    confirm: 'Confirmar',
    close: 'Cerrar',
    save: 'Guardar',
    next: 'Siguiente',
    previous: 'Anterior',
    finish: 'Finalizar',
    retry: 'Reintentar',
    start: 'Comenzar',
    continue: 'Continuar',
    quit: 'Salir',
    back: 'Volver',
    seeAll: 'Ver todo',
    seeMore: 'Ver mas',
    seeLess: 'Ver menos',
    search: 'Buscar',
    filter: 'Filtrar',
    all: 'Todo',
    none: 'Ninguno',
    yes: 'Si',
    no: 'No',
    or: 'o',
    and: 'y',
    points: 'puntos',
    minutes: 'minutos',
    seconds: 'segundos',
    hours: 'horas',
    days: 'dias',
    level: 'Nivel',
    xp: 'XP',
  },

  gamification: {
    levels: {
      title: 'Niveles',
      currentLevel: 'Nivel actual',
      nextLevel: 'Proximo nivel',
      xpToNext: 'XP para el proximo nivel',
      maxLevel: 'Nivel maximo alcanzado!',
      levelNames: [
        'Principiante',
        'Aprendiz',
        'Iniciado',
        'Competente',
        'Avanzado',
        'Experto',
        'Maestro',
        'Gran Maestro',
      ],
    },

    points: {
      title: 'Puntos',
      total: 'Total de puntos',
      earned: 'Puntos ganados',
      categories: {
        learning: 'Aprendizaje',
        practice: 'Practica',
        social: 'Social',
        exam: 'Examenes',
      },
      actions: {
        completeTour: 'Completar un tour guiado',
        completeLesson: 'Completar una leccion',
        watchVideo: 'Ver un video',
        readArticle: 'Leer un articulo',
        completeQuiz: 'Completar un quiz',
        perfectQuiz: 'Quiz perfecto (100%)',
        completeExercise: 'Completar un ejercicio practico',
        useFeature: 'Usar una nueva funcion',
        dailyLogin: 'Inicio de sesion diario',
        streak3Days: 'Racha de 3 dias',
        streak7Days: 'Racha de 7 dias',
        streak30Days: 'Racha de 30 dias',
        helpColleague: 'Ayudar a un colega',
        shareKnowledge: 'Compartir conocimiento',
        writeComment: 'Escribir un comentario util',
        passExam: 'Aprobar un examen',
        passExamFirst: 'Aprobar al primer intento',
        perfectExam: 'Examen perfecto (100%)',
        levelUp: 'Subir de nivel',
      },
    },

    badges: {
      title: 'Insignias',
      unlocked: 'Desbloqueadas',
      locked: 'Bloqueadas',
      progress: 'Progreso',
      rarity: {
        common: 'Comun',
        rare: 'Rara',
        epic: 'Epica',
        legendary: 'Legendaria',
      },
      names: {
        firstSteps: 'Primeros Pasos',
        explorer: 'Explorador',
        learner: 'Aprendiz',
        expert: 'Experto',
        master: 'Maestro',
        perfectionist: 'Perfeccionista',
        speedRunner: 'Velocista',
        dedicated: 'Dedicado',
        helpful: 'Servicial',
        champion: 'Campeon',
      },
      descriptions: {
        firstSteps: 'Completar tu primer tour guiado',
        explorer: 'Visitar todos los modulos de la aplicacion',
        learner: 'Completar 10 lecciones',
        expert: 'Alcanzar el nivel Experto',
        master: 'Alcanzar el nivel Maestro',
        perfectionist: 'Obtener 100% en 5 examenes',
        speedRunner: 'Completar un examen en menos de 5 minutos',
        dedicated: 'Mantener una racha de 30 dias',
        helpful: 'Ayudar a 10 colegas',
        champion: 'Alcanzar el top 3 del ranking',
      },
    },

    challenges: {
      title: 'Desafios',
      daily: 'Desafio diario',
      weekly: 'Desafio semanal',
      special: 'Desafio especial',
      completed: 'Completado',
      inProgress: 'En progreso',
      timeRemaining: 'Tiempo restante',
      reward: 'Recompensa',
      difficulty: {
        easy: 'Facil',
        medium: 'Medio',
        hard: 'Dificil',
      },
    },

    leaderboard: {
      title: 'Clasificacion',
      rank: 'Posicion',
      player: 'Jugador',
      score: 'Puntuacion',
      yourRank: 'Tu posicion',
      top10: 'Top 10',
      thisWeek: 'Esta semana',
      thisMonth: 'Este mes',
      allTime: 'Historico',
    },

    streak: {
      title: 'Racha',
      currentStreak: 'Racha actual',
      bestStreak: 'Mejor racha',
      keepItUp: 'Sigue asi!',
      streakLost: 'Racha perdida',
      daysInRow: 'dias consecutivos',
    },
  },

  exams: {
    title: 'Examenes',
    levelExam: 'Examen de nivel',
    practiceQuiz: 'Quiz de practica',
    startExam: 'Comenzar examen',
    continueExam: 'Continuar examen',
    timeRemaining: 'Tiempo restante',
    question: 'Pregunta',
    questionOf: 'de',
    selectAnswer: 'Selecciona una respuesta',
    confirmAnswer: 'Confirmar',
    nextQuestion: 'Siguiente pregunta',
    previousQuestion: 'Pregunta anterior',
    submitExam: 'Enviar examen',

    results: {
      title: 'Resultados',
      passed: 'Aprobado!',
      failed: 'Suspenso',
      score: 'Puntuacion',
      percentage: 'de aciertos',
      correctAnswers: 'Respuestas correctas',
      incorrectAnswers: 'Respuestas incorrectas',
      unanswered: 'Sin responder',
      xpEarned: 'XP ganados',
      timeSpent: 'Tiempo empleado',
      grade: 'Nota',
      stars: 'Estrellas',

      grades: {
        excellent: 'Excelente',
        veryGood: 'Muy Bien',
        good: 'Bien',
        satisfactory: 'Suficiente',
        passable: 'Aprobado',
        insufficient: 'Insuficiente',
      },

      messages: {
        congratulations: 'Felicidades!',
        levelUp: 'Has alcanzado el nivel',
        tryAgain: 'Intenta de nuevo para mejorar',
        almostThere: 'Casi lo logras!',
        keepLearning: 'Sigue aprendiendo',
        perfectScore: 'Puntuacion perfecta!',
      },
    },

    errors: {
      title: 'Errores a revisar',
      yourAnswer: 'Tu respuesta',
      correctAnswer: 'Respuesta correcta',
      explanation: 'Explicacion',
      noErrors: 'Sin errores! Perfecto!',
      reviewErrors: 'Revisar errores',
    },

    tabs: {
      errors: 'Errores a revisar',
      allAnswers: 'Todas las respuestas',
      summary: 'Resumen',
    },

    difficulty: {
      easy: 'Facil',
      medium: 'Medio',
      hard: 'Dificil',
    },

    history: {
      title: 'Historial de examenes',
      noExams: 'Ningun examen realizado',
      date: 'Fecha',
      score: 'Puntuacion',
      passed: 'Aprobado',
      failed: 'Suspenso',
      retake: 'Repetir',
    },
  },

  practiceQuizzes: {
    title: 'Quiz de Practica',
    subtitle: 'Pon a prueba tus conocimientos con quiz tematicos',
    categories: {
      all: 'Todos',
      navigation: 'Navegacion',
      crm: 'CRM y Clientes',
      invoicing: 'Facturacion',
      accounting: 'Contabilidad',
      inventory: 'Inventario',
      ai: 'Inteligencia Artificial',
      admin: 'Administracion',
    },
    startQuiz: 'Comenzar quiz',
    questionsCount: 'preguntas',
    duration: 'Duracion estimada',
    difficulty: 'Dificultad',
    xpReward: 'Recompensa XP',
    completed: 'Completado',
    bestScore: 'Mejor puntuacion',

    feedback: {
      correct: 'Correcto!',
      incorrect: 'Incorrecto',
      correctAnswerWas: 'La respuesta correcta era',
    },
  },

  notifications: {
    levelUp: {
      title: 'Subida de Nivel!',
      message: 'Has alcanzado el nivel',
      newLevel: 'Nuevo nivel',
      unlocked: 'Desbloqueados',
    },
    badgeUnlocked: {
      title: 'Insignia Desbloqueada!',
      message: 'Has obtenido la insignia',
    },
    challengeCompleted: {
      title: 'Desafio Completado!',
      message: 'Has completado el desafio',
    },
    streakMilestone: {
      title: 'Racha!',
      message: 'Has alcanzado una racha de',
    },
    examPassed: {
      title: 'Examen Aprobado!',
      message: 'Felicidades por tu exito',
    },
  },

  trainingHub: {
    title: 'Centro de Formacion',
    subtitle: 'Aprende a dominar AZALSCORE',
    tabs: {
      dashboard: 'Panel',
      lessons: 'Lecciones',
      quizzes: 'Quiz',
      games: 'Juegos',
      progress: 'Progreso',
    },
    welcome: 'Bienvenido',
    continueTraining: 'Continuar formacion',
    recommendedForYou: 'Recomendado para ti',
    yourProgress: 'Tu progreso',
  },
};

// ============================================================================
// TRADUCTIONS ALLEMANDES
// ============================================================================

export const DE: TranslationStrings = {
  general: {
    loading: 'Laden...',
    error: 'Fehler',
    success: 'Erfolg',
    cancel: 'Abbrechen',
    confirm: 'Bestatigen',
    close: 'Schliessen',
    save: 'Speichern',
    next: 'Weiter',
    previous: 'Zuruck',
    finish: 'Beenden',
    retry: 'Wiederholen',
    start: 'Starten',
    continue: 'Fortsetzen',
    quit: 'Beenden',
    back: 'Zuruck',
    seeAll: 'Alle anzeigen',
    seeMore: 'Mehr anzeigen',
    seeLess: 'Weniger anzeigen',
    search: 'Suchen',
    filter: 'Filtern',
    all: 'Alle',
    none: 'Keine',
    yes: 'Ja',
    no: 'Nein',
    or: 'oder',
    and: 'und',
    points: 'Punkte',
    minutes: 'Minuten',
    seconds: 'Sekunden',
    hours: 'Stunden',
    days: 'Tage',
    level: 'Stufe',
    xp: 'XP',
  },

  gamification: {
    levels: {
      title: 'Stufen',
      currentLevel: 'Aktuelle Stufe',
      nextLevel: 'Nachste Stufe',
      xpToNext: 'XP bis zur nachsten Stufe',
      maxLevel: 'Hochststufe erreicht!',
      levelNames: [
        'Anfanger',
        'Lehrling',
        'Eingeweihter',
        'Kompetent',
        'Fortgeschritten',
        'Experte',
        'Meister',
        'Grossmeister',
      ],
    },

    points: {
      title: 'Punkte',
      total: 'Gesamtpunkte',
      earned: 'Verdiente Punkte',
      categories: {
        learning: 'Lernen',
        practice: 'Ubung',
        social: 'Sozial',
        exam: 'Prufungen',
      },
      actions: {
        completeTour: 'Eine Fuhrung abschliessen',
        completeLesson: 'Eine Lektion abschliessen',
        watchVideo: 'Ein Video ansehen',
        readArticle: 'Einen Artikel lesen',
        completeQuiz: 'Ein Quiz abschliessen',
        perfectQuiz: 'Perfektes Quiz (100%)',
        completeExercise: 'Eine praktische Ubung abschliessen',
        useFeature: 'Eine neue Funktion nutzen',
        dailyLogin: 'Tagliche Anmeldung',
        streak3Days: '3-Tage-Serie',
        streak7Days: '7-Tage-Serie',
        streak30Days: '30-Tage-Serie',
        helpColleague: 'Einem Kollegen helfen',
        shareKnowledge: 'Wissen teilen',
        writeComment: 'Einen hilfreichen Kommentar schreiben',
        passExam: 'Eine Prufung bestehen',
        passExamFirst: 'Beim ersten Versuch bestehen',
        perfectExam: 'Perfekte Prufung (100%)',
        levelUp: 'Aufsteigen',
      },
    },

    badges: {
      title: 'Abzeichen',
      unlocked: 'Freigeschaltet',
      locked: 'Gesperrt',
      progress: 'Fortschritt',
      rarity: {
        common: 'Gewohnlich',
        rare: 'Selten',
        epic: 'Episch',
        legendary: 'Legendar',
      },
      names: {
        firstSteps: 'Erste Schritte',
        explorer: 'Entdecker',
        learner: 'Lernender',
        expert: 'Experte',
        master: 'Meister',
        perfectionist: 'Perfektionist',
        speedRunner: 'Schnelllaufer',
        dedicated: 'Engagiert',
        helpful: 'Hilfsbereit',
        champion: 'Champion',
      },
      descriptions: {
        firstSteps: 'Ihre erste Fuhrung abschliessen',
        explorer: 'Alle Anwendungsmodule besuchen',
        learner: '10 Lektionen abschliessen',
        expert: 'Expertenstufe erreichen',
        master: 'Meisterstufe erreichen',
        perfectionist: '100% bei 5 Prufungen erreichen',
        speedRunner: 'Eine Prufung in unter 5 Minuten abschliessen',
        dedicated: 'Eine 30-Tage-Serie aufrechterhalten',
        helpful: '10 Kollegen helfen',
        champion: 'Top 3 der Rangliste erreichen',
      },
    },

    challenges: {
      title: 'Herausforderungen',
      daily: 'Tagliche Herausforderung',
      weekly: 'Wochentliche Herausforderung',
      special: 'Spezielle Herausforderung',
      completed: 'Abgeschlossen',
      inProgress: 'In Bearbeitung',
      timeRemaining: 'Verbleibende Zeit',
      reward: 'Belohnung',
      difficulty: {
        easy: 'Einfach',
        medium: 'Mittel',
        hard: 'Schwer',
      },
    },

    leaderboard: {
      title: 'Rangliste',
      rank: 'Rang',
      player: 'Spieler',
      score: 'Punktzahl',
      yourRank: 'Ihr Rang',
      top10: 'Top 10',
      thisWeek: 'Diese Woche',
      thisMonth: 'Diesen Monat',
      allTime: 'Aller Zeiten',
    },

    streak: {
      title: 'Serie',
      currentStreak: 'Aktuelle Serie',
      bestStreak: 'Beste Serie',
      keepItUp: 'Weiter so!',
      streakLost: 'Serie verloren',
      daysInRow: 'Tage in Folge',
    },
  },

  exams: {
    title: 'Prufungen',
    levelExam: 'Stufenprufung',
    practiceQuiz: 'Ubungsquiz',
    startExam: 'Prufung starten',
    continueExam: 'Prufung fortsetzen',
    timeRemaining: 'Verbleibende Zeit',
    question: 'Frage',
    questionOf: 'von',
    selectAnswer: 'Wahlen Sie eine Antwort',
    confirmAnswer: 'Bestatigen',
    nextQuestion: 'Nachste Frage',
    previousQuestion: 'Vorherige Frage',
    submitExam: 'Prufung abgeben',

    results: {
      title: 'Ergebnisse',
      passed: 'Bestanden!',
      failed: 'Nicht bestanden',
      score: 'Punktzahl',
      percentage: 'Erfolgsquote',
      correctAnswers: 'Richtige Antworten',
      incorrectAnswers: 'Falsche Antworten',
      unanswered: 'Unbeantwortet',
      xpEarned: 'Verdiente XP',
      timeSpent: 'Verbrachte Zeit',
      grade: 'Note',
      stars: 'Sterne',

      grades: {
        excellent: 'Ausgezeichnet',
        veryGood: 'Sehr Gut',
        good: 'Gut',
        satisfactory: 'Befriedigend',
        passable: 'Ausreichend',
        insufficient: 'Mangelhaft',
      },

      messages: {
        congratulations: 'Herzlichen Gluckwunsch!',
        levelUp: 'Sie haben Stufe erreicht',
        tryAgain: 'Versuchen Sie es erneut, um sich zu verbessern',
        almostThere: 'Fast geschafft!',
        keepLearning: 'Lernen Sie weiter',
        perfectScore: 'Perfekte Punktzahl!',
      },
    },

    errors: {
      title: 'Zu uberprufende Fehler',
      yourAnswer: 'Ihre Antwort',
      correctAnswer: 'Richtige Antwort',
      explanation: 'Erklarung',
      noErrors: 'Keine Fehler! Perfekt!',
      reviewErrors: 'Fehler uberprufen',
    },

    tabs: {
      errors: 'Zu uberprufende Fehler',
      allAnswers: 'Alle Antworten',
      summary: 'Zusammenfassung',
    },

    difficulty: {
      easy: 'Einfach',
      medium: 'Mittel',
      hard: 'Schwer',
    },

    history: {
      title: 'Prufungsverlauf',
      noExams: 'Keine Prufungen abgelegt',
      date: 'Datum',
      score: 'Punktzahl',
      passed: 'Bestanden',
      failed: 'Nicht bestanden',
      retake: 'Wiederholen',
    },
  },

  practiceQuizzes: {
    title: 'Ubungsquiz',
    subtitle: 'Testen Sie Ihr Wissen mit thematischen Quiz',
    categories: {
      all: 'Alle',
      navigation: 'Navigation',
      crm: 'CRM & Kunden',
      invoicing: 'Rechnungsstellung',
      accounting: 'Buchhaltung',
      inventory: 'Lager',
      ai: 'Kunstliche Intelligenz',
      admin: 'Verwaltung',
    },
    startQuiz: 'Quiz starten',
    questionsCount: 'Fragen',
    duration: 'Geschatzte Dauer',
    difficulty: 'Schwierigkeit',
    xpReward: 'XP-Belohnung',
    completed: 'Abgeschlossen',
    bestScore: 'Beste Punktzahl',

    feedback: {
      correct: 'Richtig!',
      incorrect: 'Falsch',
      correctAnswerWas: 'Die richtige Antwort war',
    },
  },

  notifications: {
    levelUp: {
      title: 'Aufgestiegen!',
      message: 'Sie haben Stufe erreicht',
      newLevel: 'Neue Stufe',
      unlocked: 'Freigeschaltet',
    },
    badgeUnlocked: {
      title: 'Abzeichen Freigeschaltet!',
      message: 'Sie haben das Abzeichen erhalten',
    },
    challengeCompleted: {
      title: 'Herausforderung Abgeschlossen!',
      message: 'Sie haben die Herausforderung abgeschlossen',
    },
    streakMilestone: {
      title: 'Serie!',
      message: 'Sie haben eine Serie von erreicht',
    },
    examPassed: {
      title: 'Prufung Bestanden!',
      message: 'Herzlichen Gluckwunsch zu Ihrem Erfolg',
    },
  },

  trainingHub: {
    title: 'Schulungszentrum',
    subtitle: 'Lernen Sie AZALSCORE zu beherrschen',
    tabs: {
      dashboard: 'Dashboard',
      lessons: 'Lektionen',
      quizzes: 'Quiz',
      games: 'Spiele',
      progress: 'Fortschritt',
    },
    welcome: 'Willkommen',
    continueTraining: 'Schulung fortsetzen',
    recommendedForYou: 'Fur Sie empfohlen',
    yourProgress: 'Ihr Fortschritt',
  },
};

// ============================================================================
// TRADUCTIONS ARABES
// ============================================================================

export const AR: TranslationStrings = {
  general: {
    loading: '...جاري التحميل',
    error: 'خطأ',
    success: 'نجاح',
    cancel: 'إلغاء',
    confirm: 'تأكيد',
    close: 'إغلاق',
    save: 'حفظ',
    next: 'التالي',
    previous: 'السابق',
    finish: 'إنهاء',
    retry: 'إعادة المحاولة',
    start: 'ابدأ',
    continue: 'متابعة',
    quit: 'خروج',
    back: 'رجوع',
    seeAll: 'عرض الكل',
    seeMore: 'عرض المزيد',
    seeLess: 'عرض أقل',
    search: 'بحث',
    filter: 'تصفية',
    all: 'الكل',
    none: 'لا شيء',
    yes: 'نعم',
    no: 'لا',
    or: 'أو',
    and: 'و',
    points: 'نقاط',
    minutes: 'دقائق',
    seconds: 'ثواني',
    hours: 'ساعات',
    days: 'أيام',
    level: 'المستوى',
    xp: 'نقاط الخبرة',
  },

  gamification: {
    levels: {
      title: 'المستويات',
      currentLevel: 'المستوى الحالي',
      nextLevel: 'المستوى التالي',
      xpToNext: 'نقاط الخبرة للمستوى التالي',
      maxLevel: '!تم الوصول للمستوى الأقصى',
      levelNames: [
        'مبتدئ',
        'متدرب',
        'مُلم',
        'كفء',
        'متقدم',
        'خبير',
        'ماهر',
        'أسطوري',
      ],
    },

    points: {
      title: 'النقاط',
      total: 'إجمالي النقاط',
      earned: 'النقاط المكتسبة',
      categories: {
        learning: 'التعلم',
        practice: 'التمرين',
        social: 'اجتماعي',
        exam: 'الامتحانات',
      },
      actions: {
        completeTour: 'إكمال جولة إرشادية',
        completeLesson: 'إكمال درس',
        watchVideo: 'مشاهدة فيديو',
        readArticle: 'قراءة مقال',
        completeQuiz: 'إكمال اختبار',
        perfectQuiz: '(٪100) اختبار مثالي',
        completeExercise: 'إكمال تمرين عملي',
        useFeature: 'استخدام ميزة جديدة',
        dailyLogin: 'تسجيل دخول يومي',
        streak3Days: 'سلسلة 3 أيام',
        streak7Days: 'سلسلة 7 أيام',
        streak30Days: 'سلسلة 30 يوم',
        helpColleague: 'مساعدة زميل',
        shareKnowledge: 'مشاركة المعرفة',
        writeComment: 'كتابة تعليق مفيد',
        passExam: 'اجتياز امتحان',
        passExamFirst: 'النجاح من أول محاولة',
        perfectExam: '(٪100) امتحان مثالي',
        levelUp: 'الترقية للمستوى التالي',
      },
    },

    badges: {
      title: 'الشارات',
      unlocked: 'مفتوحة',
      locked: 'مقفلة',
      progress: 'التقدم',
      rarity: {
        common: 'عادي',
        rare: 'نادر',
        epic: 'ملحمي',
        legendary: 'أسطوري',
      },
      names: {
        firstSteps: 'الخطوات الأولى',
        explorer: 'مستكشف',
        learner: 'متعلم',
        expert: 'خبير',
        master: 'ماهر',
        perfectionist: 'مثالي',
        speedRunner: 'سريع',
        dedicated: 'مُتفاني',
        helpful: 'مُعاون',
        champion: 'بطل',
      },
      descriptions: {
        firstSteps: 'إكمال أول جولة إرشادية',
        explorer: 'زيارة جميع وحدات التطبيق',
        learner: 'إكمال 10 دروس',
        expert: 'الوصول لمستوى خبير',
        master: 'الوصول لمستوى ماهر',
        perfectionist: 'الحصول على ٪100 في 5 امتحانات',
        speedRunner: 'إكمال امتحان في أقل من 5 دقائق',
        dedicated: 'الحفاظ على سلسلة 30 يوم',
        helpful: 'مساعدة 10 زملاء',
        champion: 'الوصول لأفضل 3 في الترتيب',
      },
    },

    challenges: {
      title: 'التحديات',
      daily: 'تحدي اليوم',
      weekly: 'تحدي الأسبوع',
      special: 'تحدي خاص',
      completed: 'مكتمل',
      inProgress: 'قيد التنفيذ',
      timeRemaining: 'الوقت المتبقي',
      reward: 'المكافأة',
      difficulty: {
        easy: 'سهل',
        medium: 'متوسط',
        hard: 'صعب',
      },
    },

    leaderboard: {
      title: 'لوحة المتصدرين',
      rank: 'الترتيب',
      player: 'اللاعب',
      score: 'النتيجة',
      yourRank: 'ترتيبك',
      top10: 'أفضل 10',
      thisWeek: 'هذا الأسبوع',
      thisMonth: 'هذا الشهر',
      allTime: 'كل الأوقات',
    },

    streak: {
      title: 'السلسلة',
      currentStreak: 'السلسلة الحالية',
      bestStreak: 'أفضل سلسلة',
      keepItUp: '!استمر',
      streakLost: 'انتهت السلسلة',
      daysInRow: 'أيام متتالية',
    },
  },

  exams: {
    title: 'الامتحانات',
    levelExam: 'امتحان المستوى',
    practiceQuiz: 'اختبار تدريبي',
    startExam: 'بدء الامتحان',
    continueExam: 'متابعة الامتحان',
    timeRemaining: 'الوقت المتبقي',
    question: 'السؤال',
    questionOf: 'من',
    selectAnswer: 'اختر إجابة',
    confirmAnswer: 'تأكيد',
    nextQuestion: 'السؤال التالي',
    previousQuestion: 'السؤال السابق',
    submitExam: 'إرسال الامتحان',

    results: {
      title: 'النتائج',
      passed: '!ناجح',
      failed: 'راسب',
      score: 'النتيجة',
      percentage: 'نسبة النجاح',
      correctAnswers: 'إجابات صحيحة',
      incorrectAnswers: 'إجابات خاطئة',
      unanswered: 'بدون إجابة',
      xpEarned: 'نقاط الخبرة المكتسبة',
      timeSpent: 'الوقت المستغرق',
      grade: 'الدرجة',
      stars: 'النجوم',

      grades: {
        excellent: 'ممتاز',
        veryGood: 'جيد جداً',
        good: 'جيد',
        satisfactory: 'مقبول',
        passable: 'ناجح',
        insufficient: 'غير كافٍ',
      },

      messages: {
        congratulations: '!تهانينا',
        levelUp: 'لقد وصلت للمستوى',
        tryAgain: 'حاول مجدداً للتحسن',
        almostThere: '!أنت قريب',
        keepLearning: 'استمر في التعلم',
        perfectScore: '!نتيجة مثالية',
      },
    },

    errors: {
      title: 'أخطاء للمراجعة',
      yourAnswer: 'إجابتك',
      correctAnswer: 'الإجابة الصحيحة',
      explanation: 'التوضيح',
      noErrors: '!لا أخطاء! مثالي',
      reviewErrors: 'مراجعة الأخطاء',
    },

    tabs: {
      errors: 'أخطاء للمراجعة',
      allAnswers: 'جميع الإجابات',
      summary: 'ملخص',
    },

    difficulty: {
      easy: 'سهل',
      medium: 'متوسط',
      hard: 'صعب',
    },

    history: {
      title: 'سجل الامتحانات',
      noExams: 'لا امتحانات',
      date: 'التاريخ',
      score: 'النتيجة',
      passed: 'ناجح',
      failed: 'راسب',
      retake: 'إعادة',
    },
  },

  practiceQuizzes: {
    title: 'اختبارات التدريب',
    subtitle: 'اختبر معرفتك باختبارات موضوعية',
    categories: {
      all: 'الكل',
      navigation: 'التنقل',
      crm: 'إدارة العملاء',
      invoicing: 'الفواتير',
      accounting: 'المحاسبة',
      inventory: 'المخزون',
      ai: 'الذكاء الاصطناعي',
      admin: 'الإدارة',
    },
    startQuiz: 'بدء الاختبار',
    questionsCount: 'أسئلة',
    duration: 'المدة المقدرة',
    difficulty: 'الصعوبة',
    xpReward: 'مكافأة نقاط الخبرة',
    completed: 'مكتمل',
    bestScore: 'أفضل نتيجة',

    feedback: {
      correct: '!صحيح',
      incorrect: 'خطأ',
      correctAnswerWas: 'الإجابة الصحيحة كانت',
    },
  },

  notifications: {
    levelUp: {
      title: '!ترقية',
      message: 'لقد وصلت للمستوى',
      newLevel: 'مستوى جديد',
      unlocked: 'مفتوح',
    },
    badgeUnlocked: {
      title: '!شارة جديدة',
      message: 'لقد حصلت على شارة',
    },
    challengeCompleted: {
      title: '!تحدي مكتمل',
      message: 'لقد أكملت التحدي',
    },
    streakMilestone: {
      title: '!سلسلة',
      message: 'لقد حققت سلسلة من',
    },
    examPassed: {
      title: '!نجاح في الامتحان',
      message: 'تهانينا على نجاحك',
    },
  },

  trainingHub: {
    title: 'مركز التدريب',
    subtitle: 'تعلم إتقان أزال سكور',
    tabs: {
      dashboard: 'لوحة التحكم',
      lessons: 'الدروس',
      quizzes: 'الاختبارات',
      games: 'الألعاب',
      progress: 'التقدم',
    },
    welcome: 'مرحباً',
    continueTraining: 'متابعة التدريب',
    recommendedForYou: 'موصى به لك',
    yourProgress: 'تقدمك',
  },
};

// ============================================================================
// EXPORTS
// ============================================================================

export const translations: Record<SupportedLanguage, TranslationStrings> = {
  fr: FR,
  en: EN,
  es: ES,
  de: DE,
  ar: AR,
};

export const languageNames: Record<SupportedLanguage, string> = {
  fr: 'Francais',
  en: 'English',
  es: 'Espanol',
  de: 'Deutsch',
  ar: 'العربية',
};

export const languageFlags: Record<SupportedLanguage, string> = {
  fr: '🇫🇷',
  en: '🇬🇧',
  es: '🇪🇸',
  de: '🇩🇪',
  ar: '🇸🇦',
};

export const isRTL: Record<SupportedLanguage, boolean> = {
  fr: false,
  en: false,
  es: false,
  de: false,
  ar: true,
};
