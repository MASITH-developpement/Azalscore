/**
 * Module Helpdesk - Contenu de formation (Français)
 */
import type { ModuleTrainingContent, ModuleLesson, ModuleQuiz, ModuleExercise } from '@/modules/onboarding/training/types';

const lessons: ModuleLesson[] = [
  {
    id: 'hd-lesson-1',
    moduleId: 'helpdesk',
    title: 'Introduction au Support',
    description: 'Comprendre le module Helpdesk',
    duration: 20,
    difficulty: 'facile',
    order: 1,
    content: {
      type: 'slides',
      slides: [
        { id: 'hd-1-1', title: 'Bienvenue', content: 'Le module Support centralise les demandes clients et garantit les SLA.' },
        { id: 'hd-1-2', title: 'Concepts clés', content: '- **Ticket** : Demande client\n- **File d\'attente** : Organisation par thème\n- **SLA** : Engagement de temps\n- **Agent** : Membre support' },
        { id: 'hd-1-3', title: 'Canaux d\'entrée', content: '📧 Email\n🌐 Portail web\n📞 Téléphone\n💬 Chat\n🔗 API' },
      ],
    },
  },
  {
    id: 'hd-lesson-2',
    moduleId: 'helpdesk',
    title: 'Gestion des Tickets',
    description: 'Traiter et résoudre les tickets',
    duration: 25,
    difficulty: 'facile',
    order: 2,
    prerequisites: ['hd-lesson-1'],
    content: {
      type: 'slides',
      slides: [
        { id: 'hd-2-1', title: 'Cycle de vie', content: '🆕 Nouveau → 📋 Ouvert → ⏳ En attente → ✅ Résolu → 🔒 Fermé' },
        { id: 'hd-2-2', title: 'Priorités', content: '🔴 Critique : Blocage total\n🟠 Haute : Impact important\n🟡 Moyenne : Impact modéré\n🟢 Basse : Question simple' },
        { id: 'hd-2-3', title: 'Traitement', content: '1. Assignez-vous le ticket\n2. Analysez le problème\n3. Recherchez dans la KB\n4. Répondez au client\n5. Résolvez si traité' },
      ],
    },
  },
];

const quizzes: ModuleQuiz[] = [
  {
    id: 'hd-quiz-1',
    moduleId: 'helpdesk',
    title: 'Quiz - Support Client',
    description: 'Testez vos connaissances',
    duration: 8,
    passingScore: 70,
    difficulty: 'facile',
    xpReward: 50,
    order: 1,
    questions: [
      {
        id: 'hdq1-1',
        moduleId: 'helpdesk',
        question: 'Un SLA définit :',
        type: 'single',
        options: [{ id: 0, text: 'Le prix du support' }, { id: 1, text: 'Les temps de réponse garantis' }, { id: 2, text: 'Le nombre d\'agents' }],
        correctAnswers: [1],
        explanation: 'Le SLA fixe les engagements de temps de traitement.',
        points: 10,
        difficulty: 'facile',
      },
    ],
  },
];

const exercises: ModuleExercise[] = [
  {
    id: 'hd-exercise-1',
    moduleId: 'helpdesk',
    title: 'Traiter un ticket',
    description: 'Résolvez un ticket de A à Z',
    objective: 'Maîtriser le workflow de tickets',
    duration: 15,
    difficulty: 'facile',
    xpReward: 80,
    order: 1,
    steps: [
      { id: 'step-1', instruction: 'Ouvrez le ticket de démonstration' },
      { id: 'step-2', instruction: 'Assignez-vous le ticket' },
      { id: 'step-3', instruction: 'Recherchez une solution dans la KB' },
      { id: 'step-4', instruction: 'Répondez et résolvez' },
    ],
    validation: { type: 'checklist', criteria: ['Ticket assigné', 'Réponse envoyée', 'Ticket résolu'] },
  },
];

const finalExam: ModuleQuiz = {
  id: 'hd-final-exam',
  moduleId: 'helpdesk',
  title: 'Examen Final - Module Helpdesk',
  description: 'Évaluation complète',
  duration: 15,
  passingScore: 75,
  difficulty: 'moyen',
  xpReward: 200,
  order: 99,
  questions: [
    {
      id: 'hdfe-1',
      moduleId: 'helpdesk',
      question: 'Le statut "En attente" signifie qu\'on attend le client.',
      type: 'truefalse',
      options: [{ id: 0, text: 'Vrai' }, { id: 1, text: 'Faux' }],
      correctAnswers: [0],
      explanation: 'Ce statut indique que l\'agent attend une réponse du client.',
      points: 10,
      difficulty: 'facile',
    },
  ],
};

export const fr: ModuleTrainingContent = {
  moduleId: 'helpdesk',
  moduleName: 'Support Client',
  moduleIcon: 'Headphones',
  moduleColor: '#06B6D4',
  version: '1.0.0',
  lastUpdated: '2025-01-15',
  estimatedDuration: 45,
  availableLanguages: ['fr', 'en', 'es', 'de', 'ar'],
  lessons,
  quizzes,
  exercises,
  finalExam,
  resources: [{ title: 'Guide Support', type: 'pdf', url: '/docs/helpdesk/guide.pdf' }],
};
