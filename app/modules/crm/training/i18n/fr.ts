/**
 * Module CRM - Contenu de formation (Français)
 */
import type { ModuleTrainingContent } from '@/modules/onboarding/training';

export const fr: ModuleTrainingContent = {
  moduleId: 'crm',
  moduleName: 'CRM - Gestion Relation Client',
  moduleIcon: 'Users',
  moduleColor: '#3B82F6',
  version: '1.0.0',
  lastUpdated: '2025-01-15',
  estimatedDuration: 130,
  availableLanguages: ['fr', 'en', 'es', 'de', 'ar'],

  lessons: [
    {
      id: 'crm-lesson-1',
      title: 'Introduction au CRM',
      description: 'Découvrir les fonctionnalités essentielles du module CRM',
      duration: 20,
      difficulty: 'beginner',
      xpReward: 70,
      order: 1,
      slides: [
        {
          id: 'crm-1-1',
          type: 'intro',
          title: 'Bienvenue dans le CRM AZALSCORE',
          content: 'Le module CRM vous permet de centraliser toutes vos interactions clients et prospects.',
        },
        {
          id: 'crm-1-2',
          type: 'content',
          title: 'Les entités principales',
          content: '• **Contacts** : Personnes physiques\n• **Entreprises** : Sociétés clientes\n• **Opportunités** : Affaires en cours\n• **Activités** : Appels, emails, RDV',
        },
        {
          id: 'crm-1-3',
          type: 'quiz',
          title: 'Vérification',
          content: 'Question test',
          quizData: {
            question: 'Quelle entité représente une affaire en cours ?',
            options: ['Contact', 'Entreprise', 'Opportunité', 'Activité'],
            correctIndex: 2,
            explanation: 'L opportunité représente un projet commercial.',
          },
        },
      ],
    },
    {
      id: 'crm-lesson-2',
      title: 'Gestion des Contacts',
      description: 'Créer et gérer les fiches contacts',
      duration: 25,
      difficulty: 'beginner',
      xpReward: 85,
      order: 2,
      prerequisites: ['crm-lesson-1'],
      slides: [
        {
          id: 'crm-2-1',
          type: 'content',
          title: 'Informations contact',
          content: '• **Identité** : Nom, prénom, fonction\n• **Coordonnées** : Email, téléphone\n• **Entreprise** : Lien vers société\n• **Tags** : Catégorisation',
        },
        {
          id: 'crm-2-2',
          type: 'interactive',
          title: 'Créer un contact',
          content: '1. Cliquez sur + Nouveau contact\n2. Remplissez les champs\n3. Associez à une entreprise\n4. Enregistrez',
          interactionType: 'simulation',
          interactionData: { scenario: 'contact_creation', steps: ['new', 'fill', 'link', 'save'] },
        },
      ],
    },
    {
      id: 'crm-lesson-3',
      title: 'Pipeline Commercial',
      description: 'Gérer vos opportunités',
      duration: 30,
      difficulty: 'intermediate',
      xpReward: 110,
      order: 3,
      prerequisites: ['crm-lesson-2'],
      slides: [
        {
          id: 'crm-3-1',
          type: 'content',
          title: 'Étapes du pipeline',
          content: '1. Qualification (10%)\n2. Découverte (25%)\n3. Proposition (50%)\n4. Négociation (75%)\n5. Closing (90%)',
        },
        {
          id: 'crm-3-2',
          type: 'quiz',
          title: 'Quiz pipeline',
          content: 'Calcul du montant pondéré',
          quizData: {
            question: 'Montant pondéré de 10 000€ à 50% ?',
            options: ['10 000€', '5 000€', '50 000€', '1 000€'],
            correctIndex: 1,
            explanation: '10 000€ × 50% = 5 000€',
          },
        },
      ],
    },
  ],

  quizzes: [
    {
      id: 'crm-quiz-1',
      title: 'Quiz - Fondamentaux CRM',
      description: 'Testez vos connaissances',
      lessonId: 'crm-lesson-1',
      passingScore: 70,
      timeLimit: 10,
      xpReward: 50,
      questions: [
        {
          id: 'crmq1-1',
          question: 'Un contact représente :',
          type: 'multiple-choice',
          options: ['Une entreprise', 'Une personne', 'Un devis', 'Une facture'],
          correctAnswer: 1,
          explanation: 'Un contact est une personne physique.',
          points: 10,
        },
      ],
    },
  ],

  exercises: [
    {
      id: 'crm-exercise-1',
      title: 'Créer un prospect',
      description: 'Créez une entreprise et un contact',
      type: 'scenario',
      difficulty: 'beginner',
      estimatedTime: 15,
      xpReward: 80,
      instructions: ['Créez une entreprise', 'Créez un contact associé', 'Ajoutez une activité'],
      validationCriteria: ['Entreprise créée', 'Contact associé', 'Activité planifiée'],
    },
  ],

  finalExam: {
    id: 'crm-final-exam',
    title: 'Examen Final - Module CRM',
    description: 'Évaluation complète',
    passingScore: 75,
    timeLimit: 20,
    xpReward: 250,
    questions: [
      {
        id: 'crmfe-1',
        question: 'Un contact peut être associé à plusieurs entreprises.',
        type: 'true-false',
        correctAnswer: true,
        explanation: 'Un contact peut avoir plusieurs rôles.',
        points: 10,
      },
      {
        id: 'crmfe-2',
        question: 'Le pipeline permet le glisser-déposer.',
        type: 'true-false',
        correctAnswer: true,
        explanation: 'Le Kanban supporte le drag & drop.',
        points: 10,
      },
      {
        id: 'crmfe-3',
        question: 'Probabilité de l étape Négociation :',
        type: 'multiple-choice',
        options: ['25%', '50%', '75%', '90%'],
        correctAnswer: 2,
        explanation: 'Négociation = 75%',
        points: 10,
      },
    ],
  },

  resources: [
    { title: 'Guide CRM', type: 'pdf', url: '/docs/crm/guide.pdf' },
  ],
};
