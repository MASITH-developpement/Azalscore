/**
 * Module Comptabilite - Formation en Francais
 * ============================================
 */

export const fr = {
  moduleId: 'accounting',
  moduleName: 'Comptabilite',
  moduleIcon: '🧮',
  moduleColor: 'emerald',

  version: '1.0.0',
  lastUpdated: '2026-02-01',
  estimatedDuration: 150,
  availableLanguages: ['fr', 'en'],

  lessons: [
    {
      id: 'accounting-lesson-1',
      moduleId: 'accounting',
      title: 'Introduction a la comptabilite',
      description: 'Les bases de la comptabilite dans AZALSCORE',
      duration: 15,
      difficulty: 'facile' as const,
      order: 1,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'acc-1-1',
            title: 'Bienvenue dans la Comptabilite',
            content: `
# Module Comptabilite AZALSCORE

## Fonctionnalites principales
- **Saisie d'ecritures** manuelle et automatique
- **Journaux** comptables (Achats, Ventes, Banque, OD)
- **Rapprochement bancaire** automatise
- **Declarations fiscales** (TVA, IS, etc.)
- **Etats financiers** (Bilan, Compte de resultat)

## Integration complete
Les factures, paiements et operations generent automatiquement les ecritures comptables.
            `,
            animation: 'fade' as const,
          },
          {
            id: 'acc-1-2',
            title: 'Plan comptable',
            content: `
# Le Plan Comptable

## Structure
- **Classe 1** : Capitaux
- **Classe 2** : Immobilisations
- **Classe 3** : Stocks
- **Classe 4** : Tiers (clients, fournisseurs)
- **Classe 5** : Financiers (banque, caisse)
- **Classe 6** : Charges
- **Classe 7** : Produits

## Plan par defaut
AZALSCORE utilise le PCG (Plan Comptable General) francais.
Personnalisable selon vos besoins.
            `,
            animation: 'slide' as const,
          },
          {
            id: 'acc-1-3',
            title: 'Navigation',
            content: `
# Acces au module

## Menu
\`Menu Principal\` > \`Comptabilite\`

## Sous-menus
- **Ecritures** : Saisie et consultation
- **Journaux** : Par type d'operation
- **Comptes** : Plan comptable
- **Rapprochement** : Banque
- **Declarations** : TVA, liasses
- **Rapports** : Etats financiers

## Raccourcis
- \`Ctrl+Shift+E\` : Nouvelle ecriture
- \`Ctrl+Shift+B\` : Balance
            `,
            animation: 'fade' as const,
          },
        ],
      },
      tags: ['introduction', 'plan comptable'],
    },
    {
      id: 'accounting-lesson-2',
      moduleId: 'accounting',
      title: 'Saisie des ecritures',
      description: 'Maitriser la saisie comptable',
      duration: 20,
      difficulty: 'moyen' as const,
      order: 2,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'acc-2-1',
            title: 'Principe de base',
            content: `
# La partie double

## Regle fondamentale
**Debit = Credit**

Chaque ecriture doit etre equilibree.

## Exemple : Vente de 1000 EUR
| Compte | Libelle | Debit | Credit |
|--------|---------|-------|--------|
| 411000 | Client X | 1200 | |
| 707000 | Ventes | | 1000 |
| 445710 | TVA collectee | | 200 |

**Total** : 1200 = 1200 ✓
            `,
            animation: 'fade' as const,
          },
          {
            id: 'acc-2-2',
            title: 'Saisie manuelle',
            content: `
# Creer une ecriture

## Etapes
1. \`Comptabilite\` > \`Ecritures\` > \`+ Nouvelle\`
2. Selectionnez le **journal**
3. Indiquez la **date**
4. Ajoutez les **lignes**
5. Verifiez l'**equilibre**
6. **Validez**

## Champs par ligne
- Compte comptable
- Libelle
- Montant debit OU credit
- Lettrage (optionnel)

## Controles automatiques
- Equilibre debit/credit
- Compte existant
- Periode ouverte
            `,
            animation: 'slide' as const,
          },
          {
            id: 'acc-2-3',
            title: 'Ecritures automatiques',
            content: `
# Generation automatique

## Sources automatiques
- **Factures de vente** : Journal VE
- **Factures d'achat** : Journal AC
- **Paiements** : Journal BQ
- **Salaires** : Journal OD

## Avantages
- Pas de ressaisie
- Moins d'erreurs
- Tracabilite complete
- Gain de temps

## Parametrage
Configurez les comptes par defaut dans les parametres.
            `,
            animation: 'fade' as const,
          },
        ],
      },
      tags: ['ecritures', 'saisie', 'partie double'],
    },
    {
      id: 'accounting-lesson-3',
      moduleId: 'accounting',
      title: 'Rapprochement bancaire',
      description: 'Rapprocher vos comptes avec les releves',
      duration: 15,
      difficulty: 'moyen' as const,
      order: 3,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'acc-3-1',
            title: 'Principe',
            content: `
# Rapprochement bancaire

## Objectif
Verifier que vos ecritures correspondent au releve de banque.

## Processus
1. Importer le releve bancaire
2. Associer les lignes aux ecritures
3. Identifier les ecarts
4. Valider le rapprochement

## Frequence recommandee
- Mensuel minimum
- Hebdomadaire ideal
- Quotidien pour gros volumes
            `,
            animation: 'fade' as const,
          },
          {
            id: 'acc-3-2',
            title: 'Rapprochement automatique',
            content: `
# Matching automatique

## Comment ca marche
AZALSCORE analyse :
- Montants identiques
- Dates proches
- References correspondantes

## Taux de matching
Typiquement 70-90% automatique

## Actions manuelles
- Associer les ecarts
- Creer les ecritures manquantes
- Signaler les anomalies

## Validation
Une fois tout rapproche, validez pour verrouiller.
            `,
            animation: 'slide' as const,
          },
        ],
      },
      tags: ['rapprochement', 'banque'],
    },
    {
      id: 'accounting-lesson-4',
      moduleId: 'accounting',
      title: 'Declarations fiscales',
      description: 'Generer vos declarations TVA et autres',
      duration: 15,
      difficulty: 'difficile' as const,
      order: 4,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'acc-4-1',
            title: 'Declaration de TVA',
            content: `
# TVA dans AZALSCORE

## Types supportes
- **CA3** : Mensuelle ou trimestrielle
- **CA12** : Annuelle (regime simplifie)

## Generation
1. \`Comptabilite\` > \`Declarations\` > \`TVA\`
2. Selectionnez la periode
3. Verifiez les montants
4. Generez le fichier EDI
5. Teledeclarez sur impots.gouv.fr

## Controles
- Coherence TVA collectee vs factures
- Coherence TVA deductible vs achats
            `,
            animation: 'fade' as const,
          },
          {
            id: 'acc-4-2',
            title: 'Cloture d\'exercice',
            content: `
# Cloturer l'exercice

## Etapes
1. Verifier toutes les ecritures
2. Passer les ecritures d'inventaire
3. Generer les etats financiers
4. Valider avec l'expert-comptable
5. Cloturer l'exercice
6. A-nouveaux automatiques

## Attention
La cloture est **irreversible**.
Verifiez tout avant de cloturer.

## Export FEC
Fichier des Ecritures Comptables obligatoire.
            `,
            animation: 'slide' as const,
          },
        ],
      },
      tags: ['TVA', 'declarations', 'cloture'],
    },
    {
      id: 'accounting-lesson-5',
      moduleId: 'accounting',
      title: 'Etats financiers',
      description: 'Generer balance, grand livre, bilan',
      duration: 12,
      difficulty: 'moyen' as const,
      order: 5,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'acc-5-1',
            title: 'Les etats disponibles',
            content: `
# Rapports comptables

## Etats courants
- **Balance** : Soldes de tous les comptes
- **Grand Livre** : Detail par compte
- **Balance agee** : Anciennete des creances/dettes

## Etats de synthese
- **Bilan** : Patrimoine a une date
- **Compte de resultat** : Performance de l'exercice
- **Annexes** : Informations complementaires

## Export
Tous les etats sont exportables en PDF, Excel, CSV.
            `,
            animation: 'fade' as const,
          },
          {
            id: 'acc-5-2',
            title: 'Generer un etat',
            content: `
# Creation d'un rapport

## Etapes
1. \`Comptabilite\` > \`Rapports\`
2. Choisissez l'etat souhaite
3. Definissez la periode
4. Appliquez les filtres
5. Generez
6. Exportez si besoin

## Filtres utiles
- Periode (date debut/fin)
- Comptes (de X a Y)
- Journaux
- Analytique

## Comparatif
Comparez avec N-1 automatiquement.
            `,
            animation: 'slide' as const,
          },
        ],
      },
      tags: ['rapports', 'balance', 'bilan'],
    },
  ],

  quizzes: [
    {
      id: 'accounting-quiz-1',
      moduleId: 'accounting',
      title: 'Quiz: Bases comptables',
      description: 'Testez vos connaissances sur les fondamentaux',
      duration: 12,
      passingScore: 70,
      difficulty: 'moyen' as const,
      xpReward: 60,
      order: 1,
      questions: [
        {
          id: 'acc-q1-1',
          moduleId: 'accounting',
          question: 'Quelle est la regle fondamentale de la comptabilite ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Debit > Credit' },
            { id: 1, text: 'Debit = Credit' },
            { id: 2, text: 'Credit > Debit' },
            { id: 3, text: 'Pas de regle' },
          ],
          correctAnswers: [1],
          explanation: 'La partie double impose que le total des debits egale le total des credits.',
          points: 10,
          difficulty: 'facile' as const,
        },
        {
          id: 'acc-q1-2',
          moduleId: 'accounting',
          question: 'Quelle classe de comptes correspond aux clients ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Classe 1' },
            { id: 1, text: 'Classe 4' },
            { id: 2, text: 'Classe 6' },
            { id: 3, text: 'Classe 7' },
          ],
          correctAnswers: [1],
          explanation: 'La classe 4 regroupe les comptes de tiers (clients 411, fournisseurs 401...).',
          points: 10,
          difficulty: 'facile' as const,
        },
        {
          id: 'acc-q1-3',
          moduleId: 'accounting',
          question: 'Ou sont enregistrees les factures de vente ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Journal des Achats (AC)' },
            { id: 1, text: 'Journal des Ventes (VE)' },
            { id: 2, text: 'Journal de Banque (BQ)' },
            { id: 3, text: 'Journal des OD' },
          ],
          correctAnswers: [1],
          explanation: 'Les factures de vente sont enregistrees dans le journal VE (Ventes).',
          points: 10,
          difficulty: 'facile' as const,
        },
        {
          id: 'acc-q1-4',
          moduleId: 'accounting',
          question: 'Qu\'est-ce que le rapprochement bancaire ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Creer un compte bancaire' },
            { id: 1, text: 'Comparer ecritures et releves bancaires' },
            { id: 2, text: 'Payer les fournisseurs' },
            { id: 3, text: 'Calculer les interets' },
          ],
          correctAnswers: [1],
          explanation: 'Le rapprochement verifie la coherence entre comptabilite et banque.',
          points: 10,
          difficulty: 'moyen' as const,
        },
        {
          id: 'acc-q1-5',
          moduleId: 'accounting',
          question: 'Qu\'est-ce que le FEC ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Format d\'Envoi Commercial' },
            { id: 1, text: 'Fichier des Ecritures Comptables' },
            { id: 2, text: 'Facture Electronique Certifiee' },
            { id: 3, text: 'Fond d\'Exploitation Commercial' },
          ],
          correctAnswers: [1],
          explanation: 'Le FEC est le Fichier des Ecritures Comptables, obligatoire pour le fisc.',
          points: 10,
          difficulty: 'moyen' as const,
        },
      ],
    },
  ],

  exercises: [
    {
      id: 'accounting-exercise-1',
      moduleId: 'accounting',
      title: 'Saisir une ecriture',
      description: 'Creer une ecriture comptable equilibree',
      objective: 'Maitriser la saisie d\'ecritures',
      duration: 15,
      difficulty: 'moyen' as const,
      xpReward: 50,
      order: 1,
      steps: [
        { id: 'ex1-1', instruction: 'Allez dans Comptabilite > Ecritures > + Nouvelle' },
        { id: 'ex1-2', instruction: 'Selectionnez le journal OD (Operations Diverses)' },
        { id: 'ex1-3', instruction: 'Saisissez la date du jour' },
        { id: 'ex1-4', instruction: 'Ajoutez une ligne debit : compte 6064 (Fournitures), 100 EUR' },
        { id: 'ex1-5', instruction: 'Ajoutez une ligne credit : compte 401 (Fournisseurs), 100 EUR' },
        { id: 'ex1-6', instruction: 'Verifiez l\'equilibre (Debit = Credit)' },
        { id: 'ex1-7', instruction: 'Validez l\'ecriture' },
      ],
      validation: {
        type: 'checklist' as const,
        criteria: ['L\'ecriture est equilibree', 'Le journal est correct', 'L\'ecriture est validee'],
      },
    },
    {
      id: 'accounting-exercise-2',
      moduleId: 'accounting',
      title: 'Generer la balance',
      description: 'Produire la balance des comptes',
      objective: 'Savoir generer les etats comptables',
      duration: 10,
      difficulty: 'facile' as const,
      xpReward: 35,
      order: 2,
      steps: [
        { id: 'ex2-1', instruction: 'Allez dans Comptabilite > Rapports > Balance' },
        { id: 'ex2-2', instruction: 'Selectionnez la periode (mois en cours)' },
        { id: 'ex2-3', instruction: 'Cliquez sur Generer' },
        { id: 'ex2-4', instruction: 'Verifiez que le total Debit = total Credit' },
        { id: 'ex2-5', instruction: 'Exportez en PDF' },
      ],
      validation: {
        type: 'checklist' as const,
        criteria: ['La balance est generee', 'Elle est equilibree', 'Export PDF reussi'],
      },
    },
  ],

  finalExam: {
    id: 'accounting-final-exam',
    moduleId: 'accounting',
    title: 'Examen Final: Comptabilite',
    description: 'Validez vos competences comptables',
    duration: 30,
    passingScore: 75,
    difficulty: 'difficile' as const,
    xpReward: 250,
    badgeReward: 'accounting-expert',
    order: 99,
    questions: [
      {
        id: 'acc-final-1',
        moduleId: 'accounting',
        question: 'Comment s\'assurer qu\'une ecriture est correcte ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Verifier que Debit = Credit' },
          { id: 1, text: 'Demander au manager' },
          { id: 2, text: 'Attendre la fin du mois' },
          { id: 3, text: 'Imprimer le document' },
        ],
        correctAnswers: [0],
        explanation: 'Une ecriture equilibree a toujours Debit = Credit.',
        points: 10,
        difficulty: 'facile' as const,
      },
      {
        id: 'acc-final-2',
        moduleId: 'accounting',
        question: 'Quels comptes utilisent la classe 7 ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Les charges' },
          { id: 1, text: 'Les produits (revenus)' },
          { id: 2, text: 'Les immobilisations' },
          { id: 3, text: 'Les stocks' },
        ],
        correctAnswers: [1],
        explanation: 'La classe 7 regroupe tous les produits (ventes, produits financiers...).',
        points: 10,
        difficulty: 'facile' as const,
      },
      {
        id: 'acc-final-3',
        moduleId: 'accounting',
        question: 'Quel document est obligatoire pour l\'administration fiscale ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Balance' },
          { id: 1, text: 'FEC (Fichier des Ecritures Comptables)' },
          { id: 2, text: 'Grand Livre' },
          { id: 3, text: 'Brouillard de caisse' },
        ],
        correctAnswers: [1],
        explanation: 'Le FEC est obligatoire et doit pouvoir etre fourni en cas de controle fiscal.',
        points: 15,
        difficulty: 'moyen' as const,
      },
      {
        id: 'acc-final-4',
        moduleId: 'accounting',
        question: 'Que permet le lettrage ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Envoyer des lettres aux clients' },
          { id: 1, text: 'Associer les factures et leurs paiements' },
          { id: 2, text: 'Classer les documents' },
          { id: 3, text: 'Imprimer en couleur' },
        ],
        correctAnswers: [1],
        explanation: 'Le lettrage associe les ecritures de facture et de reglement pour faciliter le suivi.',
        points: 10,
        difficulty: 'moyen' as const,
      },
      {
        id: 'acc-final-5',
        moduleId: 'accounting',
        question: 'La cloture d\'exercice est-elle reversible ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Oui, a tout moment' },
          { id: 1, text: 'Oui, dans les 30 jours' },
          { id: 2, text: 'Non, elle est definitive' },
          { id: 3, text: 'Oui, avec mot de passe admin' },
        ],
        correctAnswers: [2],
        explanation: 'La cloture est irreversible, c\'est pourquoi il faut tout verifier avant.',
        points: 15,
        difficulty: 'difficile' as const,
      },
      {
        id: 'acc-final-6',
        moduleId: 'accounting',
        question: 'Quels sont les deux etats de synthese principaux ?',
        type: 'multiple' as const,
        options: [
          { id: 0, text: 'Bilan' },
          { id: 1, text: 'Compte de resultat' },
          { id: 2, text: 'Grand Livre' },
          { id: 3, text: 'Balance' },
        ],
        correctAnswers: [0, 1],
        explanation: 'Le Bilan et le Compte de resultat sont les deux etats de synthese obligatoires.',
        points: 15,
        difficulty: 'moyen' as const,
      },
      {
        id: 'acc-final-7',
        moduleId: 'accounting',
        question: 'Quelle declaration TVA est mensuelle ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'CA12' },
          { id: 1, text: 'CA3' },
          { id: 2, text: 'DAS2' },
          { id: 3, text: 'CFE' },
        ],
        correctAnswers: [1],
        explanation: 'La CA3 est la declaration de TVA mensuelle (ou trimestrielle).',
        points: 10,
        difficulty: 'moyen' as const,
      },
      {
        id: 'acc-final-8',
        moduleId: 'accounting',
        question: 'Quelle est la frequence recommandee pour le rapprochement bancaire ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Annuelle' },
          { id: 1, text: 'Trimestrielle' },
          { id: 2, text: 'Mensuelle ou plus' },
          { id: 3, text: 'Pas necessaire' },
        ],
        correctAnswers: [2],
        explanation: 'Le rapprochement doit etre fait au moins mensuellement, idealement plus souvent.',
        points: 10,
        difficulty: 'facile' as const,
      },
      {
        id: 'acc-final-9',
        moduleId: 'accounting',
        question: 'Les ecritures de vente sont generees automatiquement depuis ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Les devis' },
          { id: 1, text: 'Les factures validees' },
          { id: 2, text: 'Les bons de commande' },
          { id: 3, text: 'Les emails clients' },
        ],
        correctAnswers: [1],
        explanation: 'Seules les factures validees generent des ecritures comptables automatiques.',
        points: 10,
        difficulty: 'facile' as const,
      },
      {
        id: 'acc-final-10',
        moduleId: 'accounting',
        question: 'Qu\'est-ce qu\'une ecriture OD ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Operation de Depot' },
          { id: 1, text: 'Operation Diverse (regularisation)' },
          { id: 2, text: 'Ordre de Debit' },
          { id: 3, text: 'Ouverture de Dossier' },
        ],
        correctAnswers: [1],
        explanation: 'OD = Operation Diverse, utilisee pour les regularisations, provisions, etc.',
        points: 10,
        difficulty: 'facile' as const,
      },
    ],
  },

  resources: [
    { title: 'Guide Comptabilite PDF', type: 'pdf' as const, url: '/docs/comptabilite-guide.pdf' },
    { title: 'Video - Saisie ecritures', type: 'video' as const, url: 'https://videos.azalscore.com/compta' },
  ],
};
