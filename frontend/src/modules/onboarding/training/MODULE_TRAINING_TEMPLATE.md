# Guide de Creation de Formation pour un Module AZALSCORE

## Exigence

**OBLIGATOIRE**: Tout nouveau module AZALSCORE doit inclure un dossier `training/` contenant son contenu de formation.

## Structure Requise

```
app/modules/[nom_module]/
├── training/
│   ├── index.ts           # Export principal + enregistrement
│   ├── content.ts         # Contenu de formation
│   └── i18n/              # Traductions
│       ├── fr.ts          # Francais (OBLIGATOIRE)
│       ├── en.ts          # Anglais (OBLIGATOIRE)
│       └── [langue].ts    # Autres langues (optionnel)
```

## Fichier index.ts

```typescript
/**
 * Module [NOM] - Formation
 * Enregistrement automatique du module de formation
 */

import { registerTrainingModule } from '@/modules/onboarding/training';
import { loadTrainingContent } from './content';

// Enregistrer le module au chargement
registerTrainingModule(
  '[MODULE_ID]',          // ID unique du module (ex: 'crm', 'commercial', 'accounting')
  loadTrainingContent,     // Fonction de chargement
  ['module.[MODULE_ID]']   // Permissions requises (optionnel)
);

export { loadTrainingContent };
```

## Fichier content.ts

```typescript
/**
 * Module [NOM] - Contenu de Formation
 */

import { ModuleTrainingContent, SupportedLanguage } from '@/modules/onboarding/training';
import { fr } from './i18n/fr';
import { en } from './i18n/en';

const translations: Record<SupportedLanguage, ModuleTrainingContent> = {
  fr,
  en,
  es: fr, // Fallback
  de: fr, // Fallback
  ar: fr, // Fallback
};

export async function loadTrainingContent(
  language: SupportedLanguage
): Promise<ModuleTrainingContent> {
  return translations[language] || translations.fr;
}
```

## Fichier i18n/fr.ts (Exemple)

```typescript
/**
 * Module [NOM] - Formation en Francais
 */

import { ModuleTrainingContent } from '@/modules/onboarding/training';

export const fr: ModuleTrainingContent = {
  moduleId: '[MODULE_ID]',
  moduleName: '[Nom du Module]',
  moduleIcon: '[emoji]',        // Ex: '📊', '💼', '📦'
  moduleColor: '[couleur]',     // Ex: 'blue', 'green', 'purple'

  version: '1.0.0',
  lastUpdated: '2026-02-01',
  estimatedDuration: 60,        // Duree totale en minutes

  availableLanguages: ['fr', 'en'],

  // =========================================================================
  // LECONS
  // =========================================================================
  lessons: [
    {
      id: '[module]-lesson-1',
      moduleId: '[MODULE_ID]',
      title: 'Introduction au module [NOM]',
      description: 'Decouvrez les fonctionnalites principales',
      duration: 10,
      difficulty: 'facile',
      order: 1,
      content: {
        type: 'slides',
        slides: [
          {
            id: 'slide-1',
            title: 'Bienvenue',
            content: `
# Bienvenue dans le module [NOM]

Ce module vous permet de:
- Fonctionnalite 1
- Fonctionnalite 2
- Fonctionnalite 3

> **Conseil**: Prenez le temps de bien lire chaque slide.
            `,
            animation: 'fade',
          },
          {
            id: 'slide-2',
            title: 'Navigation',
            content: `
# Naviguer dans le module

## Acces au module
Menu principal > [NOM]

## Raccourcis utiles
- \`Ctrl+N\` : Nouveau
- \`Ctrl+S\` : Sauvegarder
- \`Ctrl+F\` : Rechercher
            `,
            image: '/images/training/[module]/navigation.png',
          },
          // ... autres slides
        ],
      },
      tags: ['introduction', 'navigation'],
    },
    // ... autres lecons
  ],

  // =========================================================================
  // QUIZ
  // =========================================================================
  quizzes: [
    {
      id: '[module]-quiz-1',
      moduleId: '[MODULE_ID]',
      title: 'Quiz: Les bases du module [NOM]',
      description: 'Testez vos connaissances sur les fonctionnalites de base',
      duration: 10,
      passingScore: 70,
      difficulty: 'facile',
      xpReward: 50,
      order: 1,
      questions: [
        {
          id: '[module]-q1',
          moduleId: '[MODULE_ID]',
          question: 'Comment acceder au module [NOM] ?',
          type: 'single',
          options: [
            { id: 0, text: 'Option A' },
            { id: 1, text: 'Option B (correcte)' },
            { id: 2, text: 'Option C' },
            { id: 3, text: 'Option D' },
          ],
          correctAnswers: [1],
          explanation: 'Explication de la bonne reponse...',
          points: 10,
          difficulty: 'facile',
          relatedLessonId: '[module]-lesson-1',
        },
        // ... autres questions (minimum 5 par quiz)
      ],
    },
    // ... autres quiz
  ],

  // =========================================================================
  // EXERCICES PRATIQUES
  // =========================================================================
  exercises: [
    {
      id: '[module]-exercise-1',
      moduleId: '[MODULE_ID]',
      title: 'Exercice: Creer votre premier [element]',
      description: 'Mettez en pratique vos connaissances',
      objective: 'A la fin de cet exercice, vous saurez creer un [element]',
      duration: 15,
      difficulty: 'facile',
      xpReward: 40,
      order: 1,
      steps: [
        {
          id: 'step-1',
          instruction: 'Ouvrez le module [NOM] depuis le menu principal',
          hint: 'Cliquez sur le logo AZALSCORE puis selectionnez [NOM]',
        },
        {
          id: 'step-2',
          instruction: 'Cliquez sur le bouton "Nouveau"',
          screenshot: '/images/training/[module]/new-button.png',
        },
        // ... autres etapes
      ],
      validation: {
        type: 'checklist',
        criteria: [
          'Le formulaire de creation est ouvert',
          'Les champs obligatoires sont remplis',
          'L\'element a ete sauvegarde',
        ],
      },
    },
    // ... autres exercices
  ],

  // =========================================================================
  // EXAMEN FINAL (optionnel mais recommande)
  // =========================================================================
  finalExam: {
    id: '[module]-final-exam',
    moduleId: '[MODULE_ID]',
    title: 'Examen Final: Module [NOM]',
    description: 'Validez vos competences sur le module [NOM]',
    duration: 30,
    passingScore: 75,
    difficulty: 'moyen',
    xpReward: 200,
    badgeReward: '[module]-expert',
    order: 99,
    questions: [
      // Minimum 15 questions couvrant tous les sujets
    ],
  },

  // =========================================================================
  // RESSOURCES ADDITIONNELLES (optionnel)
  // =========================================================================
  resources: [
    {
      title: 'Guide PDF complet',
      type: 'pdf',
      url: '/docs/[module]-guide.pdf',
    },
    {
      title: 'Video tutoriel',
      type: 'video',
      url: 'https://videos.azalscore.com/[module]-intro',
    },
  ],
};
```

## Checklist de Validation

Avant de soumettre un nouveau module, verifiez:

- [ ] Dossier `training/` present dans le module
- [ ] Fichier `index.ts` avec enregistrement via `registerTrainingModule()`
- [ ] Traductions FR et EN completes
- [ ] Minimum 3 lecons
- [ ] Minimum 2 quiz avec 5+ questions chacun
- [ ] Minimum 2 exercices pratiques
- [ ] Examen final avec 15+ questions
- [ ] Toutes les explications presentes pour chaque question
- [ ] Images/screenshots references existants
- [ ] `moduleId` unique et coherent
- [ ] Permissions requises definies si necessaire

## Integration

Le module de formation sera automatiquement detecte et integre dans le hub de formation
des que le fichier `index.ts` est importe (via import dynamique ou bundle).

Pour forcer l'enregistrement au demarrage de l'application, ajoutez dans `App.tsx`:

```typescript
// Charger les formations des modules
import '@/modules/crm/training';
import '@/modules/commercial/training';
import '@/modules/accounting/training';
// ... etc
```

## Support

Pour toute question sur la creation de contenu de formation:
- Email: formation@azalscore.com
- Documentation: docs.azalscore.com/dev/training
