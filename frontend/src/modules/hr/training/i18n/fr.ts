/**
 * Module RH - Contenu de formation (Français)
 */
import type { ModuleTrainingContent, ModuleLesson, ModuleQuiz, ModuleExercise } from '@/modules/onboarding/training/types';

const lessons: ModuleLesson[] = [
  {
    id: 'hr-lesson-1',
    moduleId: 'hr',
    title: 'Gestion des Employés',
    description: 'Créer et gérer les fiches employés',
    duration: 25,
    difficulty: 'facile',
    order: 1,
    content: {
      type: 'slides',
      slides: [
        { id: 'hr-1-1', title: 'Bienvenue', content: 'Le module RH gère vos collaborateurs : fiches, congés, temps, entretiens.' },
        { id: 'hr-1-2', title: 'Fiche employé', content: '- **Identité** : Nom, prénom, date de naissance\n- **Poste** : Fonction, département, manager\n- **Contrat** : Type, salaire, date d\'embauche\n- **Documents** : Pièces justificatives' },
        { id: 'hr-1-3', title: 'Organigramme', content: 'Généré automatiquement à partir des relations hiérarchiques.\n\nVous pouvez filtrer par département et exporter en PDF.' },
      ],
    },
  },
  {
    id: 'hr-lesson-2',
    moduleId: 'hr',
    title: 'Gestion des Congés',
    description: 'Paramétrer et traiter les demandes de congés',
    duration: 25,
    difficulty: 'facile',
    order: 2,
    prerequisites: ['hr-lesson-1'],
    content: {
      type: 'slides',
      slides: [
        { id: 'hr-2-1', title: 'Types de congés', content: '- **Congés payés** : Acquisition mensuelle\n- **RTT** : Selon accord\n- **Maladie** : Avec justificatif\n- **Exceptionnels** : Mariage, naissance...' },
        { id: 'hr-2-2', title: 'Workflow de validation', content: '1. Demande employé\n2. Validation N+1\n3. Validation RH (optionnel)\n4. Confirmation automatique' },
        { id: 'hr-2-3', title: 'Soldes', content: 'Compteurs mis à jour en temps réel.\n\nChaque employé voit ses droits acquis, pris et restants.' },
      ],
    },
  },
];

const quizzes: ModuleQuiz[] = [
  {
    id: 'hr-quiz-1',
    moduleId: 'hr',
    title: 'Quiz - Gestion RH',
    description: 'Testez vos connaissances',
    duration: 10,
    passingScore: 70,
    difficulty: 'facile',
    xpReward: 50,
    order: 1,
    questions: [
      {
        id: 'hrq1-1',
        moduleId: 'hr',
        question: 'L\'organigramme est saisi manuellement.',
        type: 'truefalse',
        options: [{ id: 0, text: 'Vrai' }, { id: 1, text: 'Faux' }],
        correctAnswers: [1],
        explanation: 'L\'organigramme est généré automatiquement depuis les fiches employés.',
        points: 10,
        difficulty: 'facile',
      },
    ],
  },
];

const exercises: ModuleExercise[] = [
  {
    id: 'hr-exercise-1',
    moduleId: 'hr',
    title: 'Traiter une demande de congés',
    description: 'Validez ou refusez une demande',
    objective: 'Maîtriser le workflow de congés',
    duration: 10,
    difficulty: 'facile',
    xpReward: 60,
    order: 1,
    steps: [
      { id: 'step-1', instruction: 'Accédez aux demandes en attente' },
      { id: 'step-2', instruction: 'Consultez le planning d\'équipe' },
      { id: 'step-3', instruction: 'Validez la demande avec un commentaire' },
    ],
    validation: { type: 'checklist', criteria: ['Demande traitée', 'Commentaire ajouté'] },
  },
];

const finalExam: ModuleQuiz = {
  id: 'hr-final-exam',
  moduleId: 'hr',
  title: 'Examen Final - Module RH',
  description: 'Évaluation complète',
  duration: 15,
  passingScore: 75,
  difficulty: 'moyen',
  xpReward: 200,
  order: 99,
  questions: [
    {
      id: 'hrfe-1',
      moduleId: 'hr',
      question: 'L\'entretien professionnel est obligatoire tous les :',
      type: 'single',
      options: [{ id: 0, text: '6 mois' }, { id: 1, text: '1 an' }, { id: 2, text: '2 ans' }],
      correctAnswers: [2],
      explanation: 'L\'entretien professionnel est une obligation légale tous les 2 ans.',
      points: 10,
      difficulty: 'moyen',
    },
  ],
};

export const fr: ModuleTrainingContent = {
  moduleId: 'hr',
  moduleName: 'Ressources Humaines',
  moduleIcon: 'Users',
  moduleColor: '#8B5CF6',
  version: '1.0.0',
  lastUpdated: '2025-01-15',
  estimatedDuration: 50,
  availableLanguages: ['fr', 'en', 'es', 'de', 'ar'],
  lessons,
  quizzes,
  exercises,
  finalExam,
  resources: [{ title: 'Guide RH', type: 'pdf', url: '/docs/hr/guide.pdf' }],
};
