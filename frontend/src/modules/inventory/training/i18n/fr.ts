/**
 * Module Inventaire - Contenu de formation (Français)
 */
import type { ModuleTrainingContent, ModuleLesson, ModuleQuiz, ModuleExercise } from '@/modules/onboarding/training/types';

const lessons: ModuleLesson[] = [
  {
    id: 'inv-lesson-1',
    moduleId: 'inventory',
    title: 'Introduction à l\'Inventaire',
    description: 'Comprendre la gestion des stocks',
    duration: 20,
    difficulty: 'facile',
    order: 1,
    content: {
      type: 'slides',
      slides: [
        { id: 'inv-1-1', title: 'Bienvenue', content: 'Le module Inventaire gère vos articles, stocks, mouvements et emplacements.' },
        { id: 'inv-1-2', title: 'Concepts clés', content: '- **Article** : Produit stocké\n- **Emplacement** : Lieu de stockage\n- **Mouvement** : Entrée/Sortie de stock\n- **Inventaire** : Comptage physique' },
        { id: 'inv-1-3', title: 'Types d\'articles', content: '📦 **Stockable** : Suivi des quantités\n🔧 **Service** : Non stocké\n🏭 **Consommable** : Stock simplifié' },
      ],
    },
  },
  {
    id: 'inv-lesson-2',
    moduleId: 'inventory',
    title: 'Mouvements de stock',
    description: 'Gérer les entrées et sorties',
    duration: 25,
    difficulty: 'facile',
    order: 2,
    prerequisites: ['inv-lesson-1'],
    content: {
      type: 'slides',
      slides: [
        { id: 'inv-2-1', title: 'Types de mouvements', content: '📥 **Réception** : Entrée fournisseur\n📤 **Livraison** : Sortie client\n🔄 **Transfert** : Entre emplacements\n📉 **Ajustement** : Correction d\'écart' },
        { id: 'inv-2-2', title: 'Traçabilité', content: 'Chaque mouvement enregistre :\n- Date et heure\n- Utilisateur\n- Quantité\n- Référence (BL, OF...)' },
      ],
    },
  },
];

const quizzes: ModuleQuiz[] = [
  {
    id: 'inv-quiz-1',
    moduleId: 'inventory',
    title: 'Quiz - Gestion des stocks',
    description: 'Testez vos connaissances',
    duration: 8,
    passingScore: 70,
    difficulty: 'facile',
    xpReward: 50,
    order: 1,
    questions: [
      {
        id: 'invq1-1',
        moduleId: 'inventory',
        question: 'Un article "Service" est stockable.',
        type: 'truefalse',
        options: [{ id: 0, text: 'Vrai' }, { id: 1, text: 'Faux' }],
        correctAnswers: [1],
        explanation: 'Les services ne sont pas stockés physiquement.',
        points: 10,
        difficulty: 'facile',
      },
    ],
  },
];

const exercises: ModuleExercise[] = [
  {
    id: 'inv-exercise-1',
    moduleId: 'inventory',
    title: 'Réceptionner une commande',
    description: 'Enregistrez une réception fournisseur',
    objective: 'Maîtriser les entrées de stock',
    duration: 15,
    difficulty: 'facile',
    xpReward: 80,
    order: 1,
    steps: [
      { id: 'step-1', instruction: 'Ouvrez le bon de commande fournisseur' },
      { id: 'step-2', instruction: 'Créez une réception' },
      { id: 'step-3', instruction: 'Saisissez les quantités reçues' },
      { id: 'step-4', instruction: 'Validez la réception' },
    ],
    validation: { type: 'checklist', criteria: ['Réception créée', 'Stock mis à jour'] },
  },
];

const finalExam: ModuleQuiz = {
  id: 'inv-final-exam',
  moduleId: 'inventory',
  title: 'Examen Final - Module Inventaire',
  description: 'Évaluation complète',
  duration: 15,
  passingScore: 75,
  difficulty: 'moyen',
  xpReward: 200,
  order: 99,
  questions: [
    {
      id: 'invfe-1',
      moduleId: 'inventory',
      question: 'Un transfert modifie le stock total.',
      type: 'truefalse',
      options: [{ id: 0, text: 'Vrai' }, { id: 1, text: 'Faux' }],
      correctAnswers: [1],
      explanation: 'Un transfert déplace le stock mais ne change pas la quantité totale.',
      points: 10,
      difficulty: 'moyen',
    },
  ],
};

export const fr: ModuleTrainingContent = {
  moduleId: 'inventory',
  moduleName: 'Inventaire et Stocks',
  moduleIcon: 'Package',
  moduleColor: '#F59E0B',
  version: '1.0.0',
  lastUpdated: '2025-01-15',
  estimatedDuration: 45,
  availableLanguages: ['fr', 'en', 'es', 'de', 'ar'],
  lessons,
  quizzes,
  exercises,
  finalExam,
  resources: [{ title: 'Guide Inventaire', type: 'pdf', url: '/docs/inventory/guide.pdf' }],
};
