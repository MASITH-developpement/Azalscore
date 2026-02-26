/**
 * Module Comptabilité - Contenu de formation (Français)
 */
import type { ModuleTrainingContent, ModuleLesson, ModuleQuiz, ModuleExercise } from '@/modules/onboarding/training/types';

const lessons: ModuleLesson[] = [
  {
    id: 'acc-lesson-1',
    moduleId: 'accounting',
    title: 'Introduction à la Comptabilité',
    description: 'Comprendre les bases du module comptable',
    duration: 25,
    difficulty: 'facile',
    order: 1,
    content: {
      type: 'slides',
      slides: [
        { id: 'acc-1-1', title: 'Bienvenue', content: 'Le module Comptabilité gère l\'ensemble de votre comptabilité : plan comptable, écritures, journaux, états financiers.' },
        { id: 'acc-1-2', title: 'Concepts clés', content: '- **Journal** : Registre des opérations\n- **Écriture** : Mouvement comptable\n- **Compte** : Catégorie du plan comptable\n- **Exercice** : Période comptable (année)' },
        { id: 'acc-1-3', title: 'Plan comptable', content: 'Structure hiérarchique :\n- Classe 1-5 : Bilan\n- Classe 6 : Charges\n- Classe 7 : Produits' },
      ],
    },
  },
  {
    id: 'acc-lesson-2',
    moduleId: 'accounting',
    title: 'Écritures comptables',
    description: 'Saisir et valider les écritures',
    duration: 30,
    difficulty: 'moyen',
    order: 2,
    prerequisites: ['acc-lesson-1'],
    content: {
      type: 'slides',
      slides: [
        { id: 'acc-2-1', title: 'Principe de la partie double', content: 'Toute écriture doit être équilibrée :\n\n**Total Débit = Total Crédit**\n\nLe système vérifie automatiquement l\'équilibre.' },
        { id: 'acc-2-2', title: 'Saisie d\'une écriture', content: '1. Sélectionnez le journal\n2. Choisissez la date\n3. Ajoutez les lignes (compte, montant, D/C)\n4. Vérifiez l\'équilibre\n5. Enregistrez' },
        { id: 'acc-2-3', title: 'Validation', content: 'Les écritures passent par :\n- Brouillon (modifiable)\n- Validée (définitive)\n\nUne écriture validée ne peut plus être modifiée.' },
      ],
    },
  },
];

const quizzes: ModuleQuiz[] = [
  {
    id: 'acc-quiz-1',
    moduleId: 'accounting',
    title: 'Quiz - Fondamentaux Comptables',
    description: 'Testez vos connaissances',
    duration: 10,
    passingScore: 70,
    difficulty: 'moyen',
    xpReward: 60,
    order: 1,
    questions: [
      {
        id: 'accq1-1',
        moduleId: 'accounting',
        question: 'Une écriture comptable doit toujours être :',
        type: 'single',
        options: [{ id: 0, text: 'Négative' }, { id: 1, text: 'Équilibrée (Débit = Crédit)' }, { id: 2, text: 'En attente' }],
        correctAnswers: [1],
        explanation: 'Le principe de la partie double impose l\'équilibre Débit = Crédit.',
        points: 10,
        difficulty: 'moyen',
      },
    ],
  },
];

const exercises: ModuleExercise[] = [
  {
    id: 'acc-exercise-1',
    moduleId: 'accounting',
    title: 'Saisir une écriture',
    description: 'Comptabilisez une facture d\'achat',
    objective: 'Maîtriser la saisie d\'écritures',
    duration: 20,
    difficulty: 'moyen',
    xpReward: 100,
    order: 1,
    steps: [
      { id: 'step-1', instruction: 'Ouvrez le journal des achats' },
      { id: 'step-2', instruction: 'Créez une nouvelle écriture' },
      { id: 'step-3', instruction: 'Saisissez : compte 401 crédit 1200€, compte 607 débit 1000€, compte 44566 débit 200€' },
      { id: 'step-4', instruction: 'Vérifiez l\'équilibre et validez' },
    ],
    validation: { type: 'automatic', criteria: ['Écriture équilibrée', 'Comptes corrects'] },
  },
];

const finalExam: ModuleQuiz = {
  id: 'acc-final-exam',
  moduleId: 'accounting',
  title: 'Examen Final - Module Comptabilité',
  description: 'Évaluation complète',
  duration: 20,
  passingScore: 75,
  difficulty: 'moyen',
  xpReward: 250,
  order: 99,
  questions: [
    {
      id: 'accfe-1',
      moduleId: 'accounting',
      question: 'Une écriture validée peut être modifiée.',
      type: 'truefalse',
      options: [{ id: 0, text: 'Vrai' }, { id: 1, text: 'Faux' }],
      correctAnswers: [1],
      explanation: 'Une écriture validée est définitive et ne peut être modifiée.',
      points: 10,
      difficulty: 'facile',
    },
    {
      id: 'accfe-2',
      moduleId: 'accounting',
      question: 'Les comptes de classe 6 représentent :',
      type: 'single',
      options: [{ id: 0, text: 'L\'actif' }, { id: 1, text: 'Les charges' }, { id: 2, text: 'Les produits' }],
      correctAnswers: [1],
      explanation: 'La classe 6 regroupe les comptes de charges.',
      points: 10,
      difficulty: 'moyen',
    },
  ],
};

export const fr: ModuleTrainingContent = {
  moduleId: 'accounting',
  moduleName: 'Comptabilité',
  moduleIcon: 'Calculator',
  moduleColor: '#6366F1',
  version: '1.0.0',
  lastUpdated: '2025-01-15',
  estimatedDuration: 55,
  availableLanguages: ['fr', 'en', 'es', 'de', 'ar'],
  lessons,
  quizzes,
  exercises,
  finalExam,
  resources: [{ title: 'Guide Comptable', type: 'pdf', url: '/docs/accounting/guide.pdf' }],
};
