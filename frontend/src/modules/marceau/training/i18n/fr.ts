/**
 * Module Marceau - Contenu de formation (Français)
 */
import type { ModuleTrainingContent, ModuleLesson, ModuleQuiz, ModuleExercise } from '@/modules/onboarding/training/types';

const lessons: ModuleLesson[] = [
  {
    id: 'marc-lesson-1',
    moduleId: 'marceau',
    title: 'Introduction à Marceau',
    description: 'Découvrir l\'agent IA intelligent',
    duration: 20,
    difficulty: 'facile',
    order: 1,
    content: {
      type: 'slides',
      slides: [
        { id: 'marc-1-1', title: 'Bienvenue', content: 'Marceau est l\'assistant IA d\'AZALSCORE. Il automatise vos tâches et améliore votre productivité.' },
        { id: 'marc-1-2', title: 'Capacités', content: '🤖 Marceau peut :\n- Répondre aux questions\n- Créer des documents\n- Automatiser des tâches\n- Analyser des données\n- Gérer la téléphonie' },
        { id: 'marc-1-3', title: 'Modules', content: '📞 Téléphonie\n📝 SEO\n💼 Commercial\n🎧 Support\n📢 Marketing\n📊 Comptabilité' },
      ],
    },
  },
  {
    id: 'marc-lesson-2',
    moduleId: 'marceau',
    title: 'Formuler des Demandes',
    description: 'Communiquer efficacement avec l\'IA',
    duration: 20,
    difficulty: 'facile',
    order: 2,
    prerequisites: ['marc-lesson-1'],
    content: {
      type: 'slides',
      slides: [
        { id: 'marc-2-1', title: 'Bonnes pratiques', content: '✅ Soyez précis\n✅ Donnez du contexte\n✅ Spécifiez le format\n✅ Indiquez les contraintes' },
        { id: 'marc-2-2', title: 'À éviter', content: '❌ Trop vague\n❌ Trop complexe\n❌ Ambigu\n❌ Sans contexte' },
        { id: 'marc-2-3', title: 'Exemple', content: '❌ "Fais un devis"\n\n✅ "Crée un devis pour Dupont SA : installation 3j×600€, formation 1j×500€"' },
      ],
    },
  },
];

const quizzes: ModuleQuiz[] = [
  {
    id: 'marc-quiz-1',
    moduleId: 'marceau',
    title: 'Quiz - Marceau',
    description: 'Testez vos connaissances',
    duration: 8,
    passingScore: 70,
    difficulty: 'facile',
    xpReward: 50,
    order: 1,
    questions: [
      {
        id: 'marcq1-1',
        moduleId: 'marceau',
        question: 'Marceau exécute les actions :',
        type: 'single',
        options: [{ id: 0, text: 'Sans validation' }, { id: 1, text: 'Après validation utilisateur' }, { id: 2, text: 'Jamais' }],
        correctAnswers: [1],
        explanation: 'Toute action est soumise à validation pour garantir le contrôle.',
        points: 10,
        difficulty: 'facile',
      },
    ],
  },
];

const exercises: ModuleExercise[] = [
  {
    id: 'marc-exercise-1',
    moduleId: 'marceau',
    title: 'Première conversation',
    description: 'Interagissez avec Marceau',
    objective: 'Maîtriser l\'interface de chat',
    duration: 10,
    difficulty: 'facile',
    xpReward: 60,
    order: 1,
    steps: [
      { id: 'step-1', instruction: 'Ouvrez le chat Marceau' },
      { id: 'step-2', instruction: 'Demandez la création d\'un devis' },
      { id: 'step-3', instruction: 'Vérifiez la proposition' },
      { id: 'step-4', instruction: 'Validez l\'action' },
    ],
    validation: { type: 'checklist', criteria: ['Conversation initiée', 'Action validée'] },
  },
];

const finalExam: ModuleQuiz = {
  id: 'marc-final-exam',
  moduleId: 'marceau',
  title: 'Examen Final - Module Marceau',
  description: 'Évaluation complète',
  duration: 12,
  passingScore: 75,
  difficulty: 'moyen',
  xpReward: 180,
  order: 99,
  questions: [
    {
      id: 'marcfe-1',
      moduleId: 'marceau',
      question: 'Une demande précise donne de meilleurs résultats.',
      type: 'truefalse',
      options: [{ id: 0, text: 'Vrai' }, { id: 1, text: 'Faux' }],
      correctAnswers: [0],
      explanation: 'Plus la demande est claire, meilleur est le résultat.',
      points: 10,
      difficulty: 'facile',
    },
    {
      id: 'marcfe-2',
      moduleId: 'marceau',
      question: 'Le feedback sur les refus aide Marceau à s\'améliorer.',
      type: 'truefalse',
      options: [{ id: 0, text: 'Vrai' }, { id: 1, text: 'Faux' }],
      correctAnswers: [0],
      explanation: 'L\'IA apprend des retours utilisateurs.',
      points: 10,
      difficulty: 'facile',
    },
  ],
};

export const fr: ModuleTrainingContent = {
  moduleId: 'marceau',
  moduleName: 'Marceau - Agent IA',
  moduleIcon: 'Bot',
  moduleColor: '#7C3AED',
  version: '1.0.0',
  lastUpdated: '2025-01-15',
  estimatedDuration: 40,
  availableLanguages: ['fr', 'en', 'es', 'de', 'ar'],
  lessons,
  quizzes,
  exercises,
  finalExam,
  resources: [{ title: 'Guide Marceau', type: 'pdf', url: '/docs/marceau/guide.pdf' }],
};
