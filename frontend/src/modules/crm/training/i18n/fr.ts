/**
 * Module CRM - Contenu de formation (Français)
 */
import type { ModuleTrainingContent, ModuleLesson, ModuleQuiz, ModuleExercise } from '@/modules/onboarding/training/types';

const lessons: ModuleLesson[] = [
  {
    id: 'crm-lesson-1',
    moduleId: 'crm',
    title: 'Introduction au CRM',
    description: 'Découvrir les fonctionnalités essentielles du module CRM',
    duration: 20,
    difficulty: 'facile',
    order: 1,
    content: {
      type: 'slides',
      slides: [
        {
          id: 'crm-1-1',
          title: 'Bienvenue dans le CRM AZALSCORE',
          content: 'Le module CRM (Customer Relationship Management) vous permet de centraliser toutes vos interactions clients, de gérer vos prospects et d\'optimiser votre relation commerciale.',
        },
        {
          id: 'crm-1-2',
          title: 'Les entités principales',
          content: '- **Contacts** : Personnes physiques (décideurs, interlocuteurs)\n- **Entreprises** : Sociétés clientes ou prospects\n- **Opportunités** : Affaires en cours de négociation\n- **Activités** : Appels, emails, rendez-vous',
        },
        {
          id: 'crm-1-3',
          title: 'Organisation du module',
          content: '📊 **Tableau de bord** : Vue d\'ensemble\n👥 **Contacts** : Fiches contacts\n🏢 **Entreprises** : Fiches entreprises\n💼 **Opportunités** : Pipeline commercial\n📅 **Activités** : Planning et historique',
        },
      ],
    },
  },
  {
    id: 'crm-lesson-2',
    moduleId: 'crm',
    title: 'Gestion des Contacts',
    description: 'Créer et gérer les fiches contacts efficacement',
    duration: 25,
    difficulty: 'facile',
    order: 2,
    prerequisites: ['crm-lesson-1'],
    content: {
      type: 'slides',
      slides: [
        {
          id: 'crm-2-1',
          title: 'La fiche contact',
          content: '- **Identité** : Nom, prénom, fonction\n- **Coordonnées** : Email, téléphone, adresse\n- **Entreprise** : Lien vers la société\n- **Réseaux** : LinkedIn, Twitter\n- **Tags** : Catégorisation personnalisée',
        },
        {
          id: 'crm-2-2',
          title: 'Créer un contact',
          content: '1. Cliquez sur **+ Nouveau contact**\n2. Remplissez les champs obligatoires\n3. Associez à une entreprise\n4. Ajoutez des tags\n5. Enregistrez',
        },
        {
          id: 'crm-2-3',
          title: 'Import de contacts',
          content: 'Importez en masse via CSV :\n1. Préparez le fichier\n2. Utilisez l\'assistant d\'import\n3. Mappez les colonnes\n4. Vérifiez les doublons\n5. Validez',
        },
      ],
    },
  },
  {
    id: 'crm-lesson-3',
    moduleId: 'crm',
    title: 'Pipeline Commercial',
    description: 'Gérer vos opportunités et suivre votre pipeline',
    duration: 30,
    difficulty: 'moyen',
    order: 3,
    prerequisites: ['crm-lesson-2'],
    content: {
      type: 'slides',
      slides: [
        {
          id: 'crm-3-1',
          title: 'Étapes du pipeline',
          content: '1️⃣ **Qualification** (10%)\n2️⃣ **Découverte** (25%)\n3️⃣ **Proposition** (50%)\n4️⃣ **Négociation** (75%)\n5️⃣ **Closing** (90%)\n\n🎯 Gagné ou ❌ Perdu',
        },
        {
          id: 'crm-3-2',
          title: 'Vue Kanban',
          content: 'Le Kanban permet de :\n- Visualiser toutes les opportunités par étape\n- Glisser-déposer pour changer d\'étape\n- Voir le montant total par colonne\n- Identifier les opportunités bloquées',
        },
        {
          id: 'crm-3-3',
          title: 'Montant pondéré',
          content: 'Calcul automatique :\n\n**Montant pondéré** = Montant × Probabilité\n\nExemple : 10 000€ × 50% = 5 000€\n\nReprésente la valeur "espérée" de l\'opportunité.',
        },
      ],
    },
  },
];

const quizzes: ModuleQuiz[] = [
  {
    id: 'crm-quiz-1',
    moduleId: 'crm',
    title: 'Quiz - Fondamentaux CRM',
    description: 'Testez vos connaissances de base',
    duration: 10,
    passingScore: 70,
    difficulty: 'facile',
    xpReward: 50,
    order: 1,
    questions: [
      {
        id: 'crmq1-1',
        moduleId: 'crm',
        question: 'Quelle entité représente une affaire en cours de négociation ?',
        type: 'single',
        options: [
          { id: 0, text: 'Contact' },
          { id: 1, text: 'Entreprise' },
          { id: 2, text: 'Opportunité' },
          { id: 3, text: 'Activité' },
        ],
        correctAnswers: [2],
        explanation: 'L\'opportunité représente un projet commercial avec un client potentiel.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'crmq1-2',
        moduleId: 'crm',
        question: 'Un contact peut être associé à plusieurs entreprises.',
        type: 'truefalse',
        options: [
          { id: 0, text: 'Vrai' },
          { id: 1, text: 'Faux' },
        ],
        correctAnswers: [0],
        explanation: 'Un contact peut avoir plusieurs rôles dans différentes entreprises.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'crmq1-3',
        moduleId: 'crm',
        question: 'Le montant pondéré d\'une opportunité de 10 000€ à l\'étape Proposition (50%) est :',
        type: 'single',
        options: [
          { id: 0, text: '10 000€' },
          { id: 1, text: '5 000€' },
          { id: 2, text: '50 000€' },
          { id: 3, text: '1 000€' },
        ],
        correctAnswers: [1],
        explanation: 'Montant pondéré = 10 000€ × 50% = 5 000€',
        points: 10,
        difficulty: 'moyen',
      },
    ],
  },
];

const exercises: ModuleExercise[] = [
  {
    id: 'crm-exercise-1',
    moduleId: 'crm',
    title: 'Créer votre premier prospect',
    description: 'Créez une entreprise prospect avec son contact principal',
    objective: 'Maîtriser la création de fiches dans le CRM',
    duration: 15,
    difficulty: 'facile',
    xpReward: 80,
    order: 1,
    steps: [
      { id: 'step-1', instruction: 'Créez une nouvelle entreprise "Test Formation SARL"' },
      { id: 'step-2', instruction: 'Renseignez : secteur IT, CA 500k€, Type Prospect' },
      { id: 'step-3', instruction: 'Créez un contact associé : Jean Dupont, Directeur Commercial' },
      { id: 'step-4', instruction: 'Ajoutez une note : "Rencontré au salon XYZ"' },
      { id: 'step-5', instruction: 'Créez une activité : Appel prévu dans 3 jours' },
    ],
    validation: {
      type: 'checklist',
      criteria: [
        'Entreprise créée avec les bonnes informations',
        'Contact associé à l\'entreprise',
        'Note présente sur la fiche',
        'Activité planifiée',
      ],
    },
  },
];

const finalExam: ModuleQuiz = {
  id: 'crm-final-exam',
  moduleId: 'crm',
  title: 'Examen Final - Module CRM',
  description: 'Évaluation complète de vos connaissances CRM',
  duration: 20,
  passingScore: 75,
  difficulty: 'moyen',
  xpReward: 250,
  order: 99,
  questions: [
    {
      id: 'crmfe-1',
      moduleId: 'crm',
      question: 'Le pipeline en mode Kanban permet le glisser-déposer.',
      type: 'truefalse',
      options: [
        { id: 0, text: 'Vrai' },
        { id: 1, text: 'Faux' },
      ],
      correctAnswers: [0],
      explanation: 'Vous pouvez déplacer les opportunités par simple drag & drop.',
      points: 10,
      difficulty: 'facile',
    },
    {
      id: 'crmfe-2',
      moduleId: 'crm',
      question: 'L\'étape Négociation a une probabilité de :',
      type: 'single',
      options: [
        { id: 0, text: '25%' },
        { id: 1, text: '50%' },
        { id: 2, text: '75%' },
        { id: 3, text: '90%' },
      ],
      correctAnswers: [2],
      explanation: 'L\'étape Négociation correspond à 75% de probabilité.',
      points: 10,
      difficulty: 'moyen',
    },
    {
      id: 'crmfe-3',
      moduleId: 'crm',
      question: 'L\'import CSV détecte automatiquement les doublons.',
      type: 'truefalse',
      options: [
        { id: 0, text: 'Vrai' },
        { id: 1, text: 'Faux' },
      ],
      correctAnswers: [0],
      explanation: 'L\'assistant d\'import inclut un détecteur de doublons.',
      points: 10,
      difficulty: 'facile',
    },
  ],
};

export const fr: ModuleTrainingContent = {
  moduleId: 'crm',
  moduleName: 'CRM - Gestion Relation Client',
  moduleIcon: 'Users',
  moduleColor: '#3B82F6',
  version: '1.0.0',
  lastUpdated: '2025-01-15',
  estimatedDuration: 75,
  availableLanguages: ['fr', 'en', 'es', 'de', 'ar'],
  lessons,
  quizzes,
  exercises,
  finalExam,
  resources: [
    { title: 'Guide CRM complet', type: 'pdf', url: '/docs/crm/guide.pdf' },
    { title: 'Tutoriel vidéo Pipeline', type: 'video', url: '/videos/crm/pipeline.mp4' },
  ],
};
