/**
 * Module Commercial - Formation en Francais
 * ==========================================
 * Devis, Factures, Commandes
 */

export const fr = {
  moduleId: 'commercial',
  moduleName: 'Commercial - Devis & Factures',
  moduleIcon: '📄',
  moduleColor: 'green',

  version: '1.0.0',
  lastUpdated: '2026-02-01',
  estimatedDuration: 120,
  availableLanguages: ['fr', 'en'],

  lessons: [
    {
      id: 'commercial-lesson-1',
      moduleId: 'commercial',
      title: 'Introduction au module Commercial',
      description: 'Decouvrez la gestion des devis et factures',
      duration: 12,
      difficulty: 'facile' as const,
      order: 1,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'com-1-1',
            title: 'Le cycle commercial',
            content: `
# Le Cycle Commercial AZALSCORE

## De l'opportunite a l'encaissement

\`\`\`
Prospect → Devis → Commande → Livraison → Facture → Paiement
\`\`\`

## Ce module vous permet de:
- Creer des **devis** professionnels
- Gerer les **commandes** clients
- Emettre des **factures** conformes
- Suivre les **paiements** et relances
- Analyser la **performance commerciale**
            `,
            animation: 'fade' as const,
          },
          {
            id: 'com-1-2',
            title: 'Navigation dans le module',
            content: `
# Acces au module Commercial

## Menu
\`Menu Principal\` > \`Commercial\`

## Sous-menus
- **Devis** : Liste et creation de devis
- **Commandes** : Commandes clients
- **Factures** : Facturation
- **Avoirs** : Notes de credit
- **Relances** : Suivi des impayes

## Raccourcis
- \`Ctrl+Shift+D\` : Nouveau devis
- \`Ctrl+Shift+F\` : Nouvelle facture
            `,
            animation: 'slide' as const,
          },
          {
            id: 'com-1-3',
            title: 'Statuts des documents',
            content: `
# Cycle de vie des documents

## Devis
- **Brouillon** : En cours de redaction
- **Envoye** : Transmis au client
- **Accepte** : Valide par le client
- **Refuse** : Decline
- **Expire** : Date de validite depassee

## Factures
- **Brouillon** : Non validee
- **Validee** : Numero definitif attribue
- **Envoyee** : Transmise au client
- **Payee partiellement** : Acompte recu
- **Payee** : Reglee integralement
            `,
            animation: 'fade' as const,
          },
        ],
      },
      tags: ['introduction', 'navigation'],
    },
    {
      id: 'commercial-lesson-2',
      moduleId: 'commercial',
      title: 'Creer un devis',
      description: 'Maitriser la creation de devis professionnels',
      duration: 15,
      difficulty: 'facile' as const,
      order: 2,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'com-2-1',
            title: 'Nouveau devis',
            content: `
# Creer un devis

## Etapes
1. \`Commercial\` > \`Devis\` > \`+ Nouveau\`
2. Selectionnez le **client**
3. Ajoutez les **lignes d'articles**
4. Verifiez les **conditions**
5. **Enregistrez** ou **Envoyez**

## Champs obligatoires
- Client
- Au moins une ligne d'article
- Date de validite

## Numerotation
Automatique selon le format configure
(ex: DEV-2026-00001)
            `,
            animation: 'fade' as const,
          },
          {
            id: 'com-2-2',
            title: 'Ajouter des articles',
            content: `
# Les lignes du devis

## Ajouter un article
- Cliquez sur **+ Ajouter une ligne**
- Recherchez l'article ou saisissez librement
- Indiquez la **quantite**
- Le prix se calcule automatiquement

## Modifier une ligne
- **Designation** : Description personnalisee
- **Quantite** : Nombre d'unites
- **Prix unitaire** : Modifiable
- **Remise** : % ou montant fixe
- **TVA** : Taux applicable

## Reorganiser
Glissez-deposez les lignes pour les reordonner
            `,
            animation: 'slide' as const,
          },
          {
            id: 'com-2-3',
            title: 'Remises et conditions',
            content: `
# Personnaliser le devis

## Types de remises
- **Par ligne** : Remise sur un article
- **Globale** : Remise sur le total HT

## Conditions de paiement
- Selectionnez dans la liste predefined
- Ou saisissez des conditions specifiques

## Validite
- Date de fin de validite
- Rappel automatique avant expiration

## Notes
- **Note interne** : Non visible client
- **Conditions** : Apparait sur le PDF
            `,
            animation: 'fade' as const,
          },
          {
            id: 'com-2-4',
            title: 'Envoyer le devis',
            content: `
# Transmettre au client

## Par email
1. Cliquez sur **Envoyer par email**
2. Verifiez le destinataire
3. Personnalisez le message
4. Le PDF est joint automatiquement

## Autres options
- **Telecharger PDF** : Pour envoi manuel
- **Imprimer** : Version papier
- **Lien de signature** : Acceptation en ligne

## Suivi
- Date d'envoi enregistree
- Notification d'ouverture (si active)
- Historique des relances
            `,
            animation: 'fade' as const,
          },
        ],
      },
      tags: ['devis', 'creation'],
    },
    {
      id: 'commercial-lesson-3',
      moduleId: 'commercial',
      title: 'De la commande a la facture',
      description: 'Transformer un devis en facture',
      duration: 15,
      difficulty: 'moyen' as const,
      order: 3,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'com-3-1',
            title: 'Convertir un devis',
            content: `
# Du devis a la commande

## Conversion
1. Ouvrez le devis **accepte**
2. Cliquez sur **Convertir en commande**
3. Verifiez les informations
4. Validez

## Ce qui est repris
- Client et contact
- Lignes d'articles
- Conditions de paiement
- Remises appliquees

## Modifications possibles
- Ajuster les quantites
- Ajouter/supprimer des lignes
- Modifier les dates
            `,
            animation: 'fade' as const,
          },
          {
            id: 'com-3-2',
            title: 'Gestion des commandes',
            content: `
# Suivi des commandes

## Statuts
- **Confirmee** : Validee par le client
- **En preparation** : Stock reserve
- **Expediee** : Livraison en cours
- **Livree** : Reception confirmee
- **Facturee** : Facture emise

## Actions
- **Bon de livraison** : Document d'expedition
- **Facturer** : Creer la facture
- **Annuler** : Si erreur ou annulation client

## Livraisons partielles
Possibilite de livrer et facturer en plusieurs fois
            `,
            animation: 'slide' as const,
          },
          {
            id: 'com-3-3',
            title: 'Creer une facture',
            content: `
# Facturation

## Depuis une commande
Cliquez sur **Facturer** dans la commande

## Facture directe
\`Commercial\` > \`Factures\` > \`+ Nouvelle\`

## Validation
- Verifiez toutes les informations
- Cliquez sur **Valider**
- Le numero definitif est attribue
- **Attention** : Facture validee = non modifiable

## Envoi
- Email automatique possible
- PDF genere selon modele
            `,
            animation: 'fade' as const,
          },
        ],
      },
      tags: ['commande', 'facture', 'conversion'],
    },
    {
      id: 'commercial-lesson-4',
      moduleId: 'commercial',
      title: 'Gestion des paiements',
      description: 'Suivre et enregistrer les reglements',
      duration: 12,
      difficulty: 'moyen' as const,
      order: 4,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'com-4-1',
            title: 'Enregistrer un paiement',
            content: `
# Saisie des reglements

## Acces
- Onglet **Paiements** de la facture
- Ou \`Tresorerie\` > \`Encaissements\`

## Informations requises
- **Montant** : Total ou partiel
- **Date** : Date de reception
- **Mode** : Virement, cheque, CB, especes
- **Reference** : N° de transaction

## Paiement partiel
Le solde restant est automatiquement calcule

## Paiement groupe
Regler plusieurs factures en une fois
            `,
            animation: 'fade' as const,
          },
          {
            id: 'com-4-2',
            title: 'Relances clients',
            content: `
# Gestion des impayes

## Relances automatiques
Configurez des emails automatiques :
- J+7 : Rappel amical
- J+15 : Premiere relance
- J+30 : Relance ferme
- J+45 : Mise en demeure

## Relance manuelle
1. \`Commercial\` > \`Relances\`
2. Selectionnez les factures
3. Choisissez le modele
4. Envoyez

## Suivi
- Historique des relances
- Date de derniere relance
- Commentaires
            `,
            animation: 'slide' as const,
          },
        ],
      },
      tags: ['paiement', 'relance', 'encaissement'],
    },
    {
      id: 'commercial-lesson-5',
      moduleId: 'commercial',
      title: 'Avoirs et rectifications',
      description: 'Gerer les retours et corrections',
      duration: 10,
      difficulty: 'moyen' as const,
      order: 5,
      content: {
        type: 'slides' as const,
        slides: [
          {
            id: 'com-5-1',
            title: 'Creer un avoir',
            content: `
# Notes de credit

## Quand creer un avoir ?
- Retour de marchandise
- Erreur de facturation
- Geste commercial
- Annulation partielle

## Creation
1. Ouvrez la facture concernee
2. Cliquez sur **Creer un avoir**
3. Selectionnez les lignes a crediter
4. Ajustez si necessaire
5. Validez

## Liaison
L'avoir est automatiquement lie a la facture d'origine
            `,
            animation: 'fade' as const,
          },
          {
            id: 'com-5-2',
            title: 'Utilisation de l\'avoir',
            content: `
# Affecter un avoir

## Options
- **Remboursement** : Restitution au client
- **Deduction** : Sur prochaine facture
- **Report** : Credit client

## Comptabilisation
L'avoir genere automatiquement les ecritures comptables inverses

## Suivi
- Solde client mis a jour
- Visible dans le compte client
- Historique des avoirs
            `,
            animation: 'slide' as const,
          },
        ],
      },
      tags: ['avoir', 'credit', 'rectification'],
    },
  ],

  quizzes: [
    {
      id: 'commercial-quiz-1',
      moduleId: 'commercial',
      title: 'Quiz: Les fondamentaux',
      description: 'Testez vos connaissances sur le module Commercial',
      duration: 10,
      passingScore: 70,
      difficulty: 'facile' as const,
      xpReward: 50,
      order: 1,
      questions: [
        {
          id: 'com-q1-1',
          moduleId: 'commercial',
          question: 'Quel est l\'ordre du cycle commercial ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Facture → Devis → Commande → Paiement' },
            { id: 1, text: 'Devis → Commande → Facture → Paiement' },
            { id: 2, text: 'Commande → Devis → Paiement → Facture' },
            { id: 3, text: 'Paiement → Facture → Devis → Commande' },
          ],
          correctAnswers: [1],
          explanation: 'Le cycle commercial standard est : Devis → Commande → Facture → Paiement.',
          points: 10,
          difficulty: 'facile' as const,
        },
        {
          id: 'com-q1-2',
          moduleId: 'commercial',
          question: 'Comment convertir un devis en commande ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Supprimer le devis et creer une commande' },
            { id: 1, text: 'Bouton "Convertir en commande" sur le devis accepte' },
            { id: 2, text: 'Envoyer un email au client' },
            { id: 3, text: 'Attendre 30 jours' },
          ],
          correctAnswers: [1],
          explanation: 'Le bouton "Convertir en commande" transforme automatiquement le devis accepte.',
          points: 10,
          difficulty: 'facile' as const,
        },
        {
          id: 'com-q1-3',
          moduleId: 'commercial',
          question: 'Peut-on modifier une facture validee ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Oui, a tout moment' },
            { id: 1, text: 'Oui, avec mot de passe admin' },
            { id: 2, text: 'Non, il faut creer un avoir' },
            { id: 3, text: 'Oui, dans les 24h' },
          ],
          correctAnswers: [2],
          explanation: 'Une facture validee est definitive. Pour corriger, on cree un avoir.',
          points: 10,
          difficulty: 'moyen' as const,
        },
        {
          id: 'com-q1-4',
          moduleId: 'commercial',
          question: 'Comment appliquer une remise globale sur un devis ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Modifier chaque ligne manuellement' },
            { id: 1, text: 'Utiliser le champ "Remise globale" en bas du devis' },
            { id: 2, text: 'Creer un article "Remise"' },
            { id: 3, text: 'Ce n\'est pas possible' },
          ],
          correctAnswers: [1],
          explanation: 'Le champ "Remise globale" applique une reduction sur le total HT.',
          points: 10,
          difficulty: 'facile' as const,
        },
        {
          id: 'com-q1-5',
          moduleId: 'commercial',
          question: 'Quand utiliser un avoir ?',
          type: 'multiple' as const,
          options: [
            { id: 0, text: 'Retour de marchandise' },
            { id: 1, text: 'Erreur de facturation' },
            { id: 2, text: 'Geste commercial' },
            { id: 3, text: 'Nouveau devis' },
          ],
          correctAnswers: [0, 1, 2],
          explanation: 'Un avoir sert a crediter le client pour retour, erreur ou geste commercial.',
          points: 15,
          difficulty: 'moyen' as const,
        },
      ],
    },
    {
      id: 'commercial-quiz-2',
      moduleId: 'commercial',
      title: 'Quiz: Paiements et relances',
      description: 'Testez vos connaissances sur la gestion des encaissements',
      duration: 8,
      passingScore: 70,
      difficulty: 'moyen' as const,
      xpReward: 60,
      order: 2,
      questions: [
        {
          id: 'com-q2-1',
          moduleId: 'commercial',
          question: 'Ou enregistrer un paiement client ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Dans les parametres' },
            { id: 1, text: 'Onglet Paiements de la facture ou Tresorerie > Encaissements' },
            { id: 2, text: 'Via le module CRM' },
            { id: 3, text: 'Par email' },
          ],
          correctAnswers: [1],
          explanation: 'Les paiements s\'enregistrent dans l\'onglet Paiements ou via Tresorerie.',
          points: 10,
          difficulty: 'facile' as const,
        },
        {
          id: 'com-q2-2',
          moduleId: 'commercial',
          question: 'Comment configurer les relances automatiques ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Parametres > Commercial > Relances' },
            { id: 1, text: 'Envoyer manuellement chaque email' },
            { id: 2, text: 'Ce n\'est pas possible' },
            { id: 3, text: 'Via Google Calendar' },
          ],
          correctAnswers: [0],
          explanation: 'Les relances automatiques se configurent dans les parametres du module Commercial.',
          points: 10,
          difficulty: 'moyen' as const,
        },
        {
          id: 'com-q2-3',
          moduleId: 'commercial',
          question: 'Peut-on enregistrer un paiement partiel ?',
          type: 'single' as const,
          options: [
            { id: 0, text: 'Non, paiement total uniquement' },
            { id: 1, text: 'Oui, le solde est calcule automatiquement' },
            { id: 2, text: 'Oui, mais il faut creer une nouvelle facture' },
            { id: 3, text: 'Uniquement avec approbation manager' },
          ],
          correctAnswers: [1],
          explanation: 'Les paiements partiels sont possibles, le solde restant est automatiquement mis a jour.',
          points: 10,
          difficulty: 'facile' as const,
        },
        {
          id: 'com-q2-4',
          moduleId: 'commercial',
          question: 'Quels modes de paiement sont disponibles ?',
          type: 'multiple' as const,
          options: [
            { id: 0, text: 'Virement bancaire' },
            { id: 1, text: 'Cheque' },
            { id: 2, text: 'Carte bancaire' },
            { id: 3, text: 'Especes' },
          ],
          correctAnswers: [0, 1, 2, 3],
          explanation: 'Tous ces modes de paiement sont disponibles dans AZALSCORE.',
          points: 15,
          difficulty: 'facile' as const,
        },
      ],
    },
  ],

  exercises: [
    {
      id: 'commercial-exercise-1',
      moduleId: 'commercial',
      title: 'Creer et envoyer un devis',
      description: 'Creez un devis complet et envoyez-le au client',
      objective: 'Maitriser la creation de devis de A a Z',
      duration: 15,
      difficulty: 'facile' as const,
      xpReward: 45,
      order: 1,
      steps: [
        { id: 'ex1-1', instruction: 'Allez dans Commercial > Devis > + Nouveau' },
        { id: 'ex1-2', instruction: 'Selectionnez un client existant' },
        { id: 'ex1-3', instruction: 'Ajoutez 3 lignes d\'articles' },
        { id: 'ex1-4', instruction: 'Appliquez une remise de 10% sur une ligne' },
        { id: 'ex1-5', instruction: 'Definissez la date de validite a 30 jours' },
        { id: 'ex1-6', instruction: 'Enregistrez le devis' },
        { id: 'ex1-7', instruction: 'Cliquez sur Envoyer par email' },
      ],
      validation: {
        type: 'checklist' as const,
        criteria: [
          'Le devis contient 3 lignes',
          'Une remise est appliquee',
          'La date de validite est definie',
          'Le devis est enregistre',
        ],
      },
    },
    {
      id: 'commercial-exercise-2',
      moduleId: 'commercial',
      title: 'Convertir et facturer',
      description: 'Transformez un devis en facture',
      objective: 'Maitriser le cycle devis → commande → facture',
      duration: 12,
      difficulty: 'moyen' as const,
      xpReward: 55,
      order: 2,
      steps: [
        { id: 'ex2-1', instruction: 'Ouvrez le devis cree precedemment' },
        { id: 'ex2-2', instruction: 'Changez son statut en "Accepte"' },
        { id: 'ex2-3', instruction: 'Cliquez sur "Convertir en commande"' },
        { id: 'ex2-4', instruction: 'Validez la commande' },
        { id: 'ex2-5', instruction: 'Cliquez sur "Facturer"' },
        { id: 'ex2-6', instruction: 'Validez la facture' },
        { id: 'ex2-7', instruction: 'Verifiez que le numero definitif est attribue' },
      ],
      validation: {
        type: 'checklist' as const,
        criteria: [
          'La commande a ete creee',
          'La facture a ete generee',
          'La facture est validee avec un numero',
        ],
      },
    },
  ],

  finalExam: {
    id: 'commercial-final-exam',
    moduleId: 'commercial',
    title: 'Examen Final: Module Commercial',
    description: 'Validez vos competences sur le cycle commercial complet',
    duration: 25,
    passingScore: 75,
    difficulty: 'moyen' as const,
    xpReward: 200,
    badgeReward: 'commercial-expert',
    order: 99,
    questions: [
      {
        id: 'com-final-1',
        moduleId: 'commercial',
        question: 'Quel raccourci cree un nouveau devis ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Ctrl+D' },
          { id: 1, text: 'Ctrl+Shift+D' },
          { id: 2, text: 'Alt+D' },
          { id: 3, text: 'F5' },
        ],
        correctAnswers: [1],
        explanation: 'Ctrl+Shift+D ouvre directement la creation de devis.',
        points: 10,
        difficulty: 'facile' as const,
      },
      {
        id: 'com-final-2',
        moduleId: 'commercial',
        question: 'Quels statuts peut avoir un devis ?',
        type: 'multiple' as const,
        options: [
          { id: 0, text: 'Brouillon' },
          { id: 1, text: 'Envoye' },
          { id: 2, text: 'Accepte' },
          { id: 3, text: 'Paye' },
        ],
        correctAnswers: [0, 1, 2],
        explanation: 'Un devis peut etre Brouillon, Envoye, Accepte, Refuse ou Expire. "Paye" est un statut de facture.',
        points: 15,
        difficulty: 'moyen' as const,
      },
      {
        id: 'com-final-3',
        moduleId: 'commercial',
        question: 'Que se passe-t-il quand on valide une facture ?',
        type: 'multiple' as const,
        options: [
          { id: 0, text: 'Un numero definitif est attribue' },
          { id: 1, text: 'Elle devient non modifiable' },
          { id: 2, text: 'Les ecritures comptables sont generees' },
          { id: 3, text: 'Un email est envoye automatiquement' },
        ],
        correctAnswers: [0, 1, 2],
        explanation: 'La validation attribue un numero, rend la facture non modifiable et genere les ecritures.',
        points: 15,
        difficulty: 'moyen' as const,
      },
      {
        id: 'com-final-4',
        moduleId: 'commercial',
        question: 'Comment gerer une livraison partielle ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Ce n\'est pas possible' },
          { id: 1, text: 'Creer plusieurs commandes' },
          { id: 2, text: 'Livrer partiellement depuis la commande' },
          { id: 3, text: 'Annuler et recommencer' },
        ],
        correctAnswers: [2],
        explanation: 'Les livraisons partielles sont gerees directement depuis la commande.',
        points: 10,
        difficulty: 'moyen' as const,
      },
      {
        id: 'com-final-5',
        moduleId: 'commercial',
        question: 'Quand creer un avoir ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Pour corriger une facture validee' },
          { id: 1, text: 'Pour un nouveau client' },
          { id: 2, text: 'Pour changer de mode de paiement' },
          { id: 3, text: 'Pour dupliquer une facture' },
        ],
        correctAnswers: [0],
        explanation: 'L\'avoir est le seul moyen de corriger ou annuler une facture validee.',
        points: 10,
        difficulty: 'facile' as const,
      },
      {
        id: 'com-final-6',
        moduleId: 'commercial',
        question: 'Comment regler plusieurs factures en une fois ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Impossible' },
          { id: 1, text: 'Paiement groupe dans Tresorerie' },
          { id: 2, text: 'Les fusionner d\'abord' },
          { id: 3, text: 'Creer un avoir global' },
        ],
        correctAnswers: [1],
        explanation: 'Le paiement groupe permet de regler plusieurs factures du meme client en une operation.',
        points: 10,
        difficulty: 'moyen' as const,
      },
      {
        id: 'com-final-7',
        moduleId: 'commercial',
        question: 'Que contient un bon de livraison ?',
        type: 'multiple' as const,
        options: [
          { id: 0, text: 'Liste des articles livres' },
          { id: 1, text: 'Quantites' },
          { id: 2, text: 'Prix de vente' },
          { id: 3, text: 'Adresse de livraison' },
        ],
        correctAnswers: [0, 1, 3],
        explanation: 'Le bon de livraison contient articles, quantites et adresse. Les prix sont sur la facture.',
        points: 15,
        difficulty: 'moyen' as const,
      },
      {
        id: 'com-final-8',
        moduleId: 'commercial',
        question: 'Comment suivre les factures impayees ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Commercial > Relances' },
          { id: 1, text: 'Uniquement en comptabilite' },
          { id: 2, text: 'Via le CRM' },
          { id: 3, text: 'Par email' },
        ],
        correctAnswers: [0],
        explanation: 'Le menu Relances centralise toutes les factures impayees avec historique.',
        points: 10,
        difficulty: 'facile' as const,
      },
      {
        id: 'com-final-9',
        moduleId: 'commercial',
        question: 'La TVA est calculee sur quel montant ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Le total TTC' },
          { id: 1, text: 'Le total HT apres remises' },
          { id: 2, text: 'Le total avant remises' },
          { id: 3, text: 'Uniquement sur les services' },
        ],
        correctAnswers: [1],
        explanation: 'La TVA est calculee sur le montant HT apres application des remises.',
        points: 10,
        difficulty: 'moyen' as const,
      },
      {
        id: 'com-final-10',
        moduleId: 'commercial',
        question: 'Comment dupliquer un devis ?',
        type: 'single' as const,
        options: [
          { id: 0, text: 'Copier-coller' },
          { id: 1, text: 'Bouton Dupliquer sur le devis' },
          { id: 2, text: 'Export/Import' },
          { id: 3, text: 'Impossible' },
        ],
        correctAnswers: [1],
        explanation: 'Le bouton Dupliquer cree une copie modifiable du devis.',
        points: 10,
        difficulty: 'facile' as const,
      },
    ],
  },

  resources: [
    { title: 'Guide PDF - Cycle commercial', type: 'pdf' as const, url: '/docs/commercial-guide.pdf' },
    { title: 'Video - Creer un devis', type: 'video' as const, url: 'https://videos.azalscore.com/devis' },
  ],
};
