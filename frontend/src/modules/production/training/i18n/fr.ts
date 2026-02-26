/**
 * Module Production - Contenu de formation (Français)
 */
import type { ModuleTrainingContent, ModuleLesson, ModuleQuiz, ModuleExercise } from '@/modules/onboarding/training/types';

const lessons: ModuleLesson[] = [
  {
    id: 'prod-lesson-1',
    moduleId: 'production',
    title: 'Introduction à la Production',
    description: 'Comprendre les concepts de gestion de production',
    duration: 25,
    difficulty: 'facile',
    order: 1,
    content: {
      type: 'slides',
      slides: [
        { id: 'prod-1-1', title: 'Bienvenue', content: 'Le module Production planifie et suit vos processus de fabrication.' },
        { id: 'prod-1-2', title: 'Concepts clés', content: '- **Nomenclature (BOM)** : Liste des composants\n- **Gamme** : Séquence des opérations\n- **OF** : Ordre de fabrication\n- **Poste de charge** : Ressource de production' },
        { id: 'prod-1-3', title: 'Flux de production', content: 'Planification → Création OF → Lancement → Exécution → Clôture' },
      ],
    },
  },
  {
    id: 'prod-lesson-2',
    moduleId: 'production',
    title: 'Ordres de Fabrication',
    description: 'Créer et suivre les OF',
    duration: 30,
    difficulty: 'moyen',
    order: 2,
    prerequisites: ['prod-lesson-1'],
    content: {
      type: 'slides',
      slides: [
        { id: 'prod-2-1', title: 'Cycle de vie d\'un OF', content: '📝 Brouillon → ⏳ Planifié → 🚀 Lancé → ⚙️ En cours → ✅ Terminé → 📦 Clôturé' },
        { id: 'prod-2-2', title: 'Lancement', content: 'Le lancement déclenche :\n- Réservation des composants\n- Impression des documents\n- Notification aux opérateurs' },
      ],
    },
  },
];

const quizzes: ModuleQuiz[] = [
  {
    id: 'prod-quiz-1',
    moduleId: 'production',
    title: 'Quiz - Production',
    description: 'Testez vos connaissances',
    duration: 10,
    passingScore: 70,
    difficulty: 'moyen',
    xpReward: 60,
    order: 1,
    questions: [
      {
        id: 'prodq1-1',
        moduleId: 'production',
        question: 'La nomenclature définit :',
        type: 'single',
        options: [{ id: 0, text: 'Les opérations' }, { id: 1, text: 'Les composants' }, { id: 2, text: 'Les clients' }],
        correctAnswers: [1],
        explanation: 'La nomenclature (BOM) liste les composants nécessaires.',
        points: 10,
        difficulty: 'moyen',
      },
    ],
  },
];

const exercises: ModuleExercise[] = [
  {
    id: 'prod-exercise-1',
    moduleId: 'production',
    title: 'Créer un OF',
    description: 'Créez et lancez un ordre de fabrication',
    objective: 'Maîtriser le cycle de production',
    duration: 20,
    difficulty: 'moyen',
    xpReward: 100,
    order: 1,
    steps: [
      { id: 'step-1', instruction: 'Créez un nouvel OF' },
      { id: 'step-2', instruction: 'Sélectionnez l\'article à fabriquer' },
      { id: 'step-3', instruction: 'Vérifiez la nomenclature et la gamme' },
      { id: 'step-4', instruction: 'Lancez l\'OF' },
    ],
    validation: { type: 'checklist', criteria: ['OF créé', 'OF lancé', 'Composants réservés'] },
  },
];

const finalExam: ModuleQuiz = {
  id: 'prod-final-exam',
  moduleId: 'production',
  title: 'Examen Final - Module Production',
  description: 'Évaluation complète',
  duration: 15,
  passingScore: 75,
  difficulty: 'moyen',
  xpReward: 200,
  order: 99,
  questions: [
    {
      id: 'prodfe-1',
      moduleId: 'production',
      question: 'Le lancement d\'un OF réserve les composants.',
      type: 'truefalse',
      options: [{ id: 0, text: 'Vrai' }, { id: 1, text: 'Faux' }],
      correctAnswers: [0],
      explanation: 'Le lancement bloque les composants pour la fabrication.',
      points: 10,
      difficulty: 'facile',
    },
  ],
};

export const fr: ModuleTrainingContent = {
  moduleId: 'production',
  moduleName: 'Production',
  moduleIcon: 'Factory',
  moduleColor: '#F59E0B',
  version: '1.0.0',
  lastUpdated: '2025-01-15',
  estimatedDuration: 55,
  availableLanguages: ['fr', 'en', 'es', 'de', 'ar'],
  lessons,
  quizzes,
  exercises,
  finalExam,
  resources: [{ title: 'Guide Production', type: 'pdf', url: '/docs/production/guide.pdf' }],
};
