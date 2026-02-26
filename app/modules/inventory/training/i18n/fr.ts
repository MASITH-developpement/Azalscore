/**
 * Module Stocks - Formation en Francais
 */

export const fr = {
  moduleId: 'inventory',
  moduleName: 'Gestion des Stocks',
  moduleIcon: '📦',
  moduleColor: 'orange',

  version: '1.0.0',
  lastUpdated: '2026-02-01',
  estimatedDuration: 90,
  availableLanguages: ['fr', 'en'],

  lessons: [
    {
      id: 'inventory-lesson-1',
      moduleId: 'inventory',
      title: 'Introduction aux stocks',
      description: 'Decouvrez la gestion des stocks AZALSCORE',
      duration: 12,
      difficulty: 'facile' as const,
      order: 1,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'inv-1-1',
            title: 'Module Stocks',
            content: `
# Gestion des Stocks AZALSCORE

## Fonctionnalites
- **Articles** : Catalogue produits
- **Mouvements** : Entrees/sorties
- **Inventaires** : Comptage physique
- **Emplacements** : Multi-entrepots
- **Alertes** : Seuils de reappro

## Integration
- Commandes clients → Sorties stock
- Commandes fournisseurs → Entrees stock
- Valorisation comptable automatique
            `,
            animation: 'fade' as const,
          },
          {
            id: 'inv-1-2',
            title: 'Types d\'articles',
            content: `
# Categories d\'articles

## Stockables
- Suivis en quantite
- Valorisation (FIFO, CUMP)
- Inventaire physique

## Non stockables
- Services
- Pas de suivi quantite

## Consommables
- Suivi simplifie
- Pas de valorisation

## Kits
- Assemblage d\'articles
- Nomenclature
            `,
            animation: 'slide' as const,
          },
        ],
      },
      tags: ['introduction', 'articles'],
    },
    {
      id: 'inventory-lesson-2',
      moduleId: 'inventory',
      title: 'Gerer les articles',
      description: 'Creer et configurer vos articles',
      duration: 15,
      difficulty: 'facile' as const,
      order: 2,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'inv-2-1',
            title: 'Creer un article',
            content: `
# Nouvel article

## Informations obligatoires
- **Reference** : Code unique
- **Designation** : Nom complet
- **Type** : Stockable, Service, etc.
- **Unite** : Piece, Kg, L, etc.

## Informations recommandees
- Prix d\'achat / vente
- Fournisseur principal
- Code-barres (EAN13)
- Photo

## Categorisation
- Famille / Sous-famille
- Tags personnalises
            `,
            animation: 'fade' as const,
          },
          {
            id: 'inv-2-2',
            title: 'Parametres de stock',
            content: `
# Configuration stock

## Seuils
- **Stock minimum** : Alerte basse
- **Stock securite** : Reserve
- **Seuil reappro** : Declenchement commande
- **Quantite reappro** : Commande optimale

## Suivi
- **Par lot** : Tracabilite lot
- **Par serie** : N° unique
- **DLUO/DLC** : Perissables

## Emplacements
- Entrepot par defaut
- Emplacement picking
            `,
            animation: 'slide' as const,
          },
        ],
      },
      tags: ['articles', 'creation', 'parametres'],
    },
    {
      id: 'inventory-lesson-3',
      moduleId: 'inventory',
      title: 'Mouvements de stock',
      description: 'Gerer les entrees et sorties',
      duration: 12,
      difficulty: 'moyen' as const,
      order: 3,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'inv-3-1',
            title: 'Types de mouvements',
            content: `
# Mouvements de stock

## Automatiques
- **Vente** : Sortie client
- **Achat** : Entree fournisseur
- **Production** : Transformation

## Manuels
- **Ajustement** : Correction
- **Transfert** : Entre emplacements
- **Rebut** : Mise au dechet

## Historique
Chaque mouvement est trace avec :
- Date, heure, utilisateur
- Quantite, valeur
- Document source
            `,
            animation: 'fade' as const,
          },
          {
            id: 'inv-3-2',
            title: 'Saisie manuelle',
            content: `
# Mouvement manuel

## Etapes
1. \`Stocks\` > \`Mouvements\` > \`+ Nouveau\`
2. Selectionnez le type
3. Choisissez l\'article
4. Indiquez la quantite
5. Selectionnez l\'emplacement
6. Ajoutez un motif
7. Validez

## Controles
- Stock suffisant (sorties)
- Emplacement valide
- Coherence lot/serie
            `,
            animation: 'slide' as const,
          },
        ],
      },
      tags: ['mouvements', 'entrees', 'sorties'],
    },
    {
      id: 'inventory-lesson-4',
      moduleId: 'inventory',
      title: 'Inventaire physique',
      description: 'Realiser un inventaire',
      duration: 15,
      difficulty: 'moyen' as const,
      order: 4,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'inv-4-1',
            title: 'Processus d\'inventaire',
            content: `
# Realiser un inventaire

## Preparation
1. Choisir la date
2. Definir le perimetre
3. Geler les mouvements (optionnel)
4. Imprimer les feuilles de comptage

## Comptage
- Equipes de comptage
- Double comptage recommande
- Saisie temps reel ou differee

## Validation
- Analyse des ecarts
- Justification
- Validation manageriale
- Ecritures d\'ajustement
            `,
            animation: 'fade' as const,
          },
          {
            id: 'inv-4-2',
            title: 'Types d\'inventaire',
            content: `
# Methodes d\'inventaire

## Complet
- Tout le stock
- Annuel obligatoire
- Cloture recommandee

## Tournant
- Par zone/famille
- Toute l\'annee
- Plus frequent

## Permanent
- A chaque mouvement
- Controle continu
- Code-barres

## Aleatoire
- Echantillon
- Verification qualite
            `,
            animation: 'slide' as const,
          },
        ],
      },
      tags: ['inventaire', 'comptage'],
    },
    {
      id: 'inventory-lesson-5',
      moduleId: 'inventory',
      title: 'Multi-entrepots',
      description: 'Gerer plusieurs sites de stockage',
      duration: 10,
      difficulty: 'moyen' as const,
      order: 5,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'inv-5-1',
            title: 'Emplacements',
            content: `
# Gestion multi-sites

## Hierarchie
- **Entrepot** : Site physique
- **Zone** : Secteur dans l\'entrepot
- **Emplacement** : Etagere/Rack

## Configuration
\`Stocks\` > \`Emplacements\` > \`+ Nouveau\`

## Par article
- Emplacement par defaut
- Emplacements autorises
- Capacite maximale

## Transferts
Mouvements inter-sites traces
            `,
            animation: 'fade' as const,
          },
        ],
      },
      tags: ['entrepots', 'emplacements', 'transferts'],
    },
  ],

  quizzes: [
    {
      id: 'inventory-quiz-1',
      moduleId: 'inventory',
      title: 'Quiz: Gestion des stocks',
      description: 'Testez vos connaissances sur les stocks',
      duration: 10,
      passingScore: 70,
      difficulty: 'moyen' as const,
      xpReward: 55,
      order: 1,
      questions: [
        {
          id: 'inv-q1-1', moduleId: 'inventory',
          question: 'Qu\'est-ce que le seuil de reapprovisionnement ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Le stock maximum' },
            { id: 1, text: 'La quantite declenchant une commande' },
            { id: 2, text: 'Le stock de securite' },
            { id: 3, text: 'La quantite vendue' },
          ],
          correctAnswers: [1],
          explanation: 'Le seuil de reappro declenche une alerte ou commande quand le stock passe en dessous.',
          points: 10, difficulty: 'moyen' as const,
        },
        {
          id: 'inv-q1-2', moduleId: 'inventory',
          question: 'FIFO signifie ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'First In First Out' },
            { id: 1, text: 'Fast Inventory For Orders' },
            { id: 2, text: 'Final Input Final Output' },
            { id: 3, text: 'Flexible Inventory Flow Option' },
          ],
          correctAnswers: [0],
          explanation: 'FIFO = Premier Entre Premier Sorti, methode de valorisation des stocks.',
          points: 10, difficulty: 'facile' as const,
        },
        {
          id: 'inv-q1-3', moduleId: 'inventory',
          question: 'Quand faire un inventaire complet obligatoire ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Chaque mois' },
            { id: 1, text: 'Au moins une fois par an' },
            { id: 2, text: 'Jamais' },
            { id: 3, text: 'A chaque vente' },
          ],
          correctAnswers: [1],
          explanation: 'L\'inventaire annuel est obligatoire pour la cloture comptable.',
          points: 10, difficulty: 'facile' as const,
        },
        {
          id: 'inv-q1-4', moduleId: 'inventory',
          question: 'A quoi sert le suivi par lot ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Grouper les commandes' },
            { id: 1, text: 'Assurer la tracabilite des produits' },
            { id: 2, text: 'Calculer les remises' },
            { id: 3, text: 'Trier les articles' },
          ],
          correctAnswers: [1],
          explanation: 'Le suivi par lot permet de tracer l\'origine et la destination de chaque lot.',
          points: 10, difficulty: 'moyen' as const,
        },
        {
          id: 'inv-q1-5', moduleId: 'inventory',
          question: 'Un mouvement de rebut correspond a ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Une vente' },
            { id: 1, text: 'Une mise au dechet' },
            { id: 2, text: 'Un transfert' },
            { id: 3, text: 'Un achat' },
          ],
          correctAnswers: [1],
          explanation: 'Le rebut correspond a des articles mis au dechet (casses, perimes...).',
          points: 10, difficulty: 'facile' as const,
        },
      ],
    },
  ],

  exercises: [
    {
      id: 'inventory-exercise-1', moduleId: 'inventory',
      title: 'Creer un article',
      description: 'Creer et configurer un article stockable',
      objective: 'Maitriser la creation d\'articles',
      duration: 12, difficulty: 'facile' as const, xpReward: 40, order: 1,
      steps: [
        { id: 'ex1-1', instruction: 'Allez dans Stocks > Articles > + Nouveau' },
        { id: 'ex1-2', instruction: 'Saisissez Reference: ART-TEST-001' },
        { id: 'ex1-3', instruction: 'Designation: Article de test formation' },
        { id: 'ex1-4', instruction: 'Type: Stockable, Unite: Piece' },
        { id: 'ex1-5', instruction: 'Definissez le seuil de reappro a 10' },
        { id: 'ex1-6', instruction: 'Enregistrez l\'article' },
      ],
      validation: { type: 'checklist' as const, criteria: ['Article cree', 'Seuil defini'] },
    },
    {
      id: 'inventory-exercise-2', moduleId: 'inventory',
      title: 'Mouvement d\'entree',
      description: 'Enregistrer une entree de stock',
      objective: 'Savoir saisir des mouvements',
      duration: 10, difficulty: 'moyen' as const, xpReward: 45, order: 2,
      steps: [
        { id: 'ex2-1', instruction: 'Allez dans Stocks > Mouvements > + Nouveau' },
        { id: 'ex2-2', instruction: 'Type: Entree' },
        { id: 'ex2-3', instruction: 'Selectionnez l\'article cree precedemment' },
        { id: 'ex2-4', instruction: 'Quantite: 50' },
        { id: 'ex2-5', instruction: 'Motif: Approvisionnement initial' },
        { id: 'ex2-6', instruction: 'Validez le mouvement' },
      ],
      validation: { type: 'checklist' as const, criteria: ['Mouvement cree', 'Stock mis a jour'] },
    },
  ],

  finalExam: {
    id: 'inventory-final-exam', moduleId: 'inventory',
    title: 'Examen Final: Gestion des Stocks',
    description: 'Validez vos competences en gestion des stocks',
    duration: 20, passingScore: 75, difficulty: 'moyen' as const,
    xpReward: 180, badgeReward: 'inventory-expert', order: 99,
    questions: [
      {
        id: 'inv-final-1', moduleId: 'inventory',
        question: 'Quels types d\'articles existent ?',
        type: 'multiple' as const,
        options: [
          { id: 0, text: 'Stockable' },
          { id: 1, text: 'Service' },
          { id: 2, text: 'Consommable' },
          { id: 3, text: 'Financier' },
        ],
        correctAnswers: [0, 1, 2],
        explanation: 'Les types sont: Stockable, Service (non stockable), Consommable.',
        points: 15, difficulty: 'facile' as const,
      },
      {
        id: 'inv-final-2', moduleId: 'inventory',
        question: 'CUMP signifie ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Cout Unitaire Moyen Pondere' },
          { id: 1, text: 'Cout Uniforme par Module' },
          { id: 2, text: 'Calcul Unitaire Mensuel' },
          { id: 3, text: 'Controle Uniforme de Marchandise' },
        ],
        correctAnswers: [0],
        explanation: 'CUMP = Cout Unitaire Moyen Pondere, methode de valorisation.',
        points: 10, difficulty: 'moyen' as const,
      },
      {
        id: 'inv-final-3', moduleId: 'inventory',
        question: 'Qu\'est-ce qu\'un inventaire tournant ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Inventaire rotatif par zone tout au long de l\'annee' },
          { id: 1, text: 'Inventaire en tournant la tete' },
          { id: 2, text: 'Inventaire uniquement des produits tournant vite' },
          { id: 3, text: 'Inventaire annuel' },
        ],
        correctAnswers: [0],
        explanation: 'L\'inventaire tournant couvre progressivement tout le stock sur l\'annee.',
        points: 10, difficulty: 'moyen' as const,
      },
      {
        id: 'inv-final-4', moduleId: 'inventory',
        question: 'Ou configurer les seuils d\'alerte stock ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Parametres generaux' },
          { id: 1, text: 'Fiche article, onglet Stock' },
          { id: 2, text: 'Module comptabilite' },
          { id: 3, text: 'Impossible a configurer' },
        ],
        correctAnswers: [1],
        explanation: 'Les seuils se definissent sur chaque fiche article.',
        points: 10, difficulty: 'facile' as const,
      },
      {
        id: 'inv-final-5', moduleId: 'inventory',
        question: 'Un transfert de stock correspond a ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Vente a un client' },
          { id: 1, text: 'Mouvement entre deux emplacements' },
          { id: 2, text: 'Mise au rebut' },
          { id: 3, text: 'Inventaire' },
        ],
        correctAnswers: [1],
        explanation: 'Le transfert deplace du stock d\'un emplacement a un autre.',
        points: 10, difficulty: 'facile' as const,
      },
    ],
  },

  resources: [
    { title: 'Guide Stocks PDF', type: 'pdf' as const, url: '/docs/stocks-guide.pdf' },
  ],
};
