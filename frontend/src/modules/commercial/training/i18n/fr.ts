/**
 * Module Commercial - Contenu de formation (Français)
 */
import type { ModuleTrainingContent, ModuleLesson, ModuleQuiz, ModuleExercise } from '@/modules/onboarding/training/types';

const lessons: ModuleLesson[] = [
  {
    id: 'com-lesson-1',
    moduleId: 'commercial',
    title: 'Introduction au module Commercial',
    description: 'Découvrir la gestion des devis et factures',
    duration: 20,
    difficulty: 'facile',
    order: 1,
    content: {
      type: 'slides',
      slides: [
        { id: 'com-1-1', title: 'Bienvenue', content: 'Le module Commercial gère tout le cycle de vente : devis, commandes, factures, avoirs.' },
        { id: 'com-1-2', title: 'Documents commerciaux', content: '- **Devis** : Proposition commerciale\n- **Commande** : Validation client\n- **Facture** : Document comptable\n- **Avoir** : Correction/remboursement' },
        { id: 'com-1-3', title: 'Cycle de vie', content: 'Devis → Commande → Bon de livraison → Facture\n\nChaque étape génère automatiquement le document suivant.' },
      ],
    },
  },
  {
    id: 'com-lesson-2',
    moduleId: 'commercial',
    title: 'Création de devis',
    description: 'Maîtriser la création et l\'envoi des devis',
    duration: 25,
    difficulty: 'facile',
    order: 2,
    prerequisites: ['com-lesson-1'],
    content: {
      type: 'slides',
      slides: [
        { id: 'com-2-1', title: 'Créer un devis', content: '1. Sélectionnez le client\n2. Ajoutez les articles\n3. Appliquez les remises\n4. Définissez la validité\n5. Enregistrez et envoyez' },
        { id: 'com-2-2', title: 'Articles et prix', content: 'Le catalogue permet :\n- Recherche rapide\n- Prix par quantité\n- Variantes de produits\n- Descriptions personnalisables' },
        { id: 'com-2-3', title: 'TVA et totaux', content: 'Calcul automatique :\n- HT par ligne\n- TVA par taux\n- Total TTC\n- Acomptes éventuels' },
      ],
    },
  },
  {
    id: 'com-lesson-3',
    moduleId: 'commercial',
    title: 'Facturation',
    description: 'Gérer les factures et paiements',
    duration: 30,
    difficulty: 'moyen',
    order: 3,
    prerequisites: ['com-lesson-2'],
    content: {
      type: 'slides',
      slides: [
        { id: 'com-3-1', title: 'Création de facture', content: 'Depuis une commande validée :\n1. Cliquez sur "Facturer"\n2. Vérifiez les quantités\n3. Générez la facture\n4. Numérotation automatique' },
        { id: 'com-3-2', title: 'Suivi des paiements', content: 'Statuts possibles :\n- En attente\n- Partiellement payée\n- Payée\n- En retard' },
        { id: 'com-3-3', title: 'Relances', content: 'Automatisation des relances :\n- Email automatique à J+7\n- Deuxième relance J+15\n- Mise en recouvrement J+30' },
      ],
    },
  },
];

const quizzes: ModuleQuiz[] = [
  {
    id: 'com-quiz-1',
    moduleId: 'commercial',
    title: 'Quiz - Documents commerciaux',
    description: 'Testez vos connaissances',
    duration: 8,
    passingScore: 70,
    difficulty: 'facile',
    xpReward: 50,
    order: 1,
    questions: [
      {
        id: 'comq1-1',
        moduleId: 'commercial',
        question: 'L\'ordre correct du cycle de vente est :',
        type: 'single',
        options: [
          { id: 0, text: 'Facture → Devis → Commande' },
          { id: 1, text: 'Devis → Commande → Facture' },
          { id: 2, text: 'Commande → Devis → Facture' },
        ],
        correctAnswers: [1],
        explanation: 'Le cycle standard est Devis → Commande → Facture.',
        points: 10,
        difficulty: 'facile',
      },
    ],
  },
];

const exercises: ModuleExercise[] = [
  {
    id: 'com-exercise-1',
    moduleId: 'commercial',
    title: 'Créer un devis complet',
    description: 'Créez un devis avec plusieurs articles et remise',
    objective: 'Maîtriser le processus de devis',
    duration: 15,
    difficulty: 'facile',
    xpReward: 80,
    order: 1,
    steps: [
      { id: 'step-1', instruction: 'Créez un nouveau devis' },
      { id: 'step-2', instruction: 'Ajoutez 3 articles différents' },
      { id: 'step-3', instruction: 'Appliquez une remise de 10%' },
      { id: 'step-4', instruction: 'Envoyez le devis par email' },
    ],
    validation: { type: 'checklist', criteria: ['Devis créé', 'Articles ajoutés', 'Remise appliquée', 'Email envoyé'] },
  },
];

const finalExam: ModuleQuiz = {
  id: 'com-final-exam',
  moduleId: 'commercial',
  title: 'Examen Final - Module Commercial',
  description: 'Évaluation complète',
  duration: 15,
  passingScore: 75,
  difficulty: 'moyen',
  xpReward: 200,
  order: 99,
  questions: [
    {
      id: 'comfe-1',
      moduleId: 'commercial',
      question: 'La TVA est calculée automatiquement.',
      type: 'truefalse',
      options: [{ id: 0, text: 'Vrai' }, { id: 1, text: 'Faux' }],
      correctAnswers: [0],
      explanation: 'Le système calcule automatiquement la TVA par taux.',
      points: 10,
      difficulty: 'facile',
    },
    {
      id: 'comfe-2',
      moduleId: 'commercial',
      question: 'Une facture peut être générée depuis :',
      type: 'single',
      options: [
        { id: 0, text: 'Un contact uniquement' },
        { id: 1, text: 'Une commande validée' },
        { id: 2, text: 'Un email' },
      ],
      correctAnswers: [1],
      explanation: 'Les factures sont générées à partir des commandes validées.',
      points: 10,
      difficulty: 'facile',
    },
  ],
};

export const fr: ModuleTrainingContent = {
  moduleId: 'commercial',
  moduleName: 'Commercial - Devis et Factures',
  moduleIcon: 'FileText',
  moduleColor: '#10B981',
  version: '1.0.0',
  lastUpdated: '2025-01-15',
  estimatedDuration: 75,
  availableLanguages: ['fr', 'en', 'es', 'de', 'ar'],
  lessons,
  quizzes,
  exercises,
  finalExam,
  resources: [{ title: 'Guide Commercial', type: 'pdf', url: '/docs/commercial/guide.pdf' }],
};
