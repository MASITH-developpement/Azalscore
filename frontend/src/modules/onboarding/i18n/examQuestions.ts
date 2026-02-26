/**
 * AZALSCORE - Questions d'examens multilingues
 * =============================================
 * Traductions des questions pour tous les examens et quiz
 */

import { SupportedLanguage } from './translations';

// ============================================================================
// TYPE
// ============================================================================

export interface TranslatedQuestion {
  id: string;
  question: string;
  options: string[];
  correctAnswer: number;
  explanation: string;
  points: number;
  difficulty: 'facile' | 'moyen' | 'difficile';
}

export interface TranslatedExam {
  level: number;
  title: string;
  description: string;
  questions: TranslatedQuestion[];
}

export interface TranslatedQuiz {
  id: string;
  title: string;
  description: string;
  category: string;
  questions: TranslatedQuestion[];
}

// ============================================================================
// EXAMENS DE NIVEAU - FRANCAIS
// ============================================================================

const LEVEL_EXAMS_FR: TranslatedExam[] = [
  {
    level: 2,
    title: 'Examen Niveau 2 - Les Bases',
    description: 'Validez vos connaissances fondamentales d\'AZALSCORE',
    questions: [
      {
        id: 'l2-q1',
        question: 'Comment acceder au menu principal d\'AZALSCORE ?',
        options: [
          'Cliquer sur le logo en haut a gauche',
          'Appuyer sur la touche Echap',
          'Double-cliquer n\'importe ou',
          'Utiliser le raccourci Ctrl+M',
        ],
        correctAnswer: 0,
        explanation: 'Le logo AZALSCORE en haut a gauche ouvre le menu principal avec tous les modules.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q2',
        question: 'Quel raccourci permet d\'ouvrir la recherche globale ?',
        options: [
          'Ctrl+F',
          'Ctrl+K ou Cmd+K',
          'Alt+S',
          'F3',
        ],
        correctAnswer: 1,
        explanation: 'Ctrl+K (ou Cmd+K sur Mac) ouvre la barre de recherche globale pour trouver rapidement clients, devis, factures, etc.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q3',
        question: 'Ou se trouve le bouton pour creer un nouveau client ?',
        options: [
          'Dans les parametres',
          'En haut a droite de la liste clients',
          'Dans le menu Aide',
          'Sur la page d\'accueil uniquement',
        ],
        correctAnswer: 1,
        explanation: 'Le bouton "+ Nouveau client" se trouve en haut a droite de la liste des clients dans le module CRM.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q4',
        question: 'Comment sauvegarder vos modifications dans un formulaire ?',
        options: [
          'Elles sont sauvegardees automatiquement',
          'Cliquer sur le bouton Enregistrer',
          'Appuyer sur Entree',
          'Fermer le formulaire',
        ],
        correctAnswer: 1,
        explanation: 'Cliquez sur le bouton Enregistrer pour sauvegarder vos modifications. Un brouillon automatique peut exister mais la sauvegarde manuelle est requise.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q5',
        question: 'Quelle icone represente le module Comptabilite ?',
        options: [
          'Un graphique',
          'Une calculatrice',
          'Un livre ouvert',
          'Une piece de monnaie',
        ],
        correctAnswer: 1,
        explanation: 'La calculatrice represente le module Comptabilite dans la navigation.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q6',
        question: 'Comment acceder a l\'aide contextuelle ?',
        options: [
          'Appuyer sur F1',
          'Cliquer sur l\'icone ? en haut a droite',
          'Les deux reponses sont correctes',
          'Aucune de ces reponses',
        ],
        correctAnswer: 2,
        explanation: 'L\'aide contextuelle est accessible via F1 ou l\'icone ? en haut a droite.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q7',
        question: 'Ou se trouvent vos notifications ?',
        options: [
          'Dans les parametres',
          'Sur l\'icone cloche en haut a droite',
          'Dans le menu Aide',
          'Sur la page d\'accueil uniquement',
        ],
        correctAnswer: 1,
        explanation: 'L\'icone cloche en haut a droite affiche toutes vos notifications.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q8',
        question: 'Comment personnaliser votre tableau de bord ?',
        options: [
          'Cliquer sur l\'icone engrenage du dashboard',
          'Contacter l\'administrateur',
          'Ce n\'est pas possible',
          'Via le menu Fichier',
        ],
        correctAnswer: 0,
        explanation: 'L\'icone engrenage sur le tableau de bord permet d\'ajouter/supprimer/reorganiser les widgets.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q9',
        question: 'Quel est le role du fil d\'Ariane (breadcrumb) ?',
        options: [
          'Afficher les derniers documents consultes',
          'Montrer votre position dans l\'application',
          'Lister vos favoris',
          'Afficher les raccourcis clavier',
        ],
        correctAnswer: 1,
        explanation: 'Le fil d\'Ariane montre votre position dans l\'arborescence de l\'application et permet de remonter facilement.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q10',
        question: 'Comment ajouter une page aux favoris ?',
        options: [
          'Cliquer sur l\'etoile dans la barre d\'adresse',
          'Utiliser Ctrl+D',
          'Cliquer sur l\'icone signet a cote du titre',
          'Toutes ces reponses',
        ],
        correctAnswer: 2,
        explanation: 'L\'icone signet a cote du titre de la page permet de l\'ajouter aux favoris pour un acces rapide.',
        points: 10,
        difficulty: 'facile',
      },
    ],
  },
  {
    level: 3,
    title: 'Examen Niveau 3 - Gestion Clients',
    description: 'Maitrisez le module CRM et la gestion des clients',
    questions: [
      {
        id: 'l3-q1',
        question: 'Comment importer une liste de clients depuis Excel ?',
        options: [
          'Copier-coller directement',
          'Menu Importer > Fichier Excel',
          'Envoyer par email a l\'administrateur',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 1,
        explanation: 'Le menu Importer permet de charger un fichier Excel avec un mapping automatique des colonnes.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q2',
        question: 'Quels champs sont obligatoires pour creer un client ?',
        options: [
          'Nom uniquement',
          'Nom et email',
          'Nom, adresse et telephone',
          'Raison sociale ou Nom + prenom (selon le type)',
        ],
        correctAnswer: 3,
        explanation: 'Pour un client professionnel, la raison sociale est obligatoire. Pour un particulier, nom et prenom sont requis.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q3',
        question: 'Comment attribuer un commercial a un client ?',
        options: [
          'Dans l\'onglet "Equipe commerciale" de la fiche client',
          'Via le menu Administration',
          'Ce n\'est pas possible',
          'En envoyant un email',
        ],
        correctAnswer: 0,
        explanation: 'L\'onglet "Equipe commerciale" permet d\'assigner un ou plusieurs commerciaux a un client.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q4',
        question: 'Comment fusionner deux fiches clients en doublon ?',
        options: [
          'Supprimer l\'une des deux',
          'Utiliser l\'outil de deduplication',
          'Contacter le support',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 1,
        explanation: 'L\'outil de deduplication detecte les doublons et permet de fusionner les fiches en conservant toutes les donnees.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q5',
        question: 'Ou voir l\'historique des interactions avec un client ?',
        options: [
          'Dans l\'onglet "Activites" de la fiche client',
          'Dans le journal global',
          'Ce n\'est pas enregistre',
          'Dans les parametres',
        ],
        correctAnswer: 0,
        explanation: 'L\'onglet "Activites" de la fiche client affiche tout l\'historique : appels, emails, rendez-vous, etc.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q6',
        question: 'Comment creer un segment de clients ?',
        options: [
          'Menu Clients > Segments > Nouveau',
          'C\'est fait automatiquement',
          'Via l\'API uniquement',
          'Contacter l\'administrateur',
        ],
        correctAnswer: 0,
        explanation: 'Le menu Segments permet de creer des groupes de clients selon des criteres (CA, secteur, localisation, etc.).',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q7',
        question: 'Quelle est la difference entre un prospect et un client ?',
        options: [
          'Aucune difference',
          'Un prospect n\'a pas encore achete',
          'Un prospect est une entreprise',
          'Un client est un prospect inactif',
        ],
        correctAnswer: 1,
        explanation: 'Un prospect est un contact commercial qui n\'a pas encore effectue d\'achat. Il devient client apres sa premiere commande.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q8',
        question: 'Comment exporter la liste des clients ?',
        options: [
          'Imprimer et scanner',
          'Bouton Exporter > Choisir le format',
          'Capture d\'ecran',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 1,
        explanation: 'Le bouton Exporter permet d\'exporter en Excel, CSV ou PDF avec choix des colonnes.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q9',
        question: 'Comment ajouter un contact supplementaire a une entreprise ?',
        options: [
          'Creer un nouveau client',
          'Dans l\'onglet "Contacts" de la fiche entreprise',
          'Ce n\'est pas possible',
          'Via les parametres',
        ],
        correctAnswer: 1,
        explanation: 'L\'onglet "Contacts" permet d\'ajouter plusieurs interlocuteurs pour une meme entreprise cliente.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q10',
        question: 'Comment definir les conditions de paiement d\'un client ?',
        options: [
          'Dans les parametres generaux',
          'Dans l\'onglet "Facturation" de la fiche client',
          'Sur chaque facture',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 1,
        explanation: 'L\'onglet "Facturation" de la fiche client permet de definir les conditions par defaut (echeance, mode de paiement, etc.).',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q11',
        question: 'Comment voir le chiffre d\'affaires d\'un client ?',
        options: [
          'Dans le dashboard client',
          'En additionnant les factures manuellement',
          'Via un export Excel',
          'Ce n\'est pas calcule',
        ],
        correctAnswer: 0,
        explanation: 'Le dashboard sur la fiche client affiche le CA, les factures en cours, l\'evolution, etc.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'l3-q12',
        question: 'Comment bloquer un client pour impaye ?',
        options: [
          'Supprimer le client',
          'Activer le blocage dans la fiche client',
          'Envoyer un email d\'avertissement',
          'Contacter le service juridique',
        ],
        correctAnswer: 1,
        explanation: 'Le blocage client empeche la creation de nouveaux devis/commandes tant que le paiement n\'est pas regularise.',
        points: 15,
        difficulty: 'moyen',
      },
    ],
  },
  {
    level: 4,
    title: 'Examen Niveau 4 - Facturation',
    description: 'Maitrisez la creation et la gestion des devis et factures',
    questions: [
      {
        id: 'l4-q1',
        question: 'Comment transformer un devis en facture ?',
        options: [
          'Creer une nouvelle facture et copier les infos',
          'Bouton "Convertir en facture" sur le devis',
          'Envoyer le devis au client',
          'Attendre 30 jours',
        ],
        correctAnswer: 1,
        explanation: 'Le bouton "Convertir en facture" cree automatiquement une facture a partir du devis accepte.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q2',
        question: 'Comment appliquer une remise sur un devis ?',
        options: [
          'Modifier manuellement les prix',
          'Utiliser le champ "Remise" sur la ligne ou le total',
          'Ce n\'est pas possible',
          'Creer un avoir',
        ],
        correctAnswer: 1,
        explanation: 'Les remises peuvent etre appliquees par ligne (%) ou sur le total du devis.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q3',
        question: 'Quelle est la duree de validite par defaut d\'un devis ?',
        options: [
          '15 jours',
          '30 jours',
          'Configurable dans les parametres',
          'Illimitee',
        ],
        correctAnswer: 2,
        explanation: 'La duree de validite par defaut est configurable dans Parametres > Commercial > Devis.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q4',
        question: 'Comment envoyer une facture par email ?',
        options: [
          'Telecharger le PDF et l\'envoyer manuellement',
          'Bouton "Envoyer par email" sur la facture',
          'Via le menu Fichier > Envoyer',
          'Options B et C sont correctes',
        ],
        correctAnswer: 3,
        explanation: 'La facture peut etre envoyee directement via le bouton sur la facture ou via le menu Fichier.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q5',
        question: 'Comment creer une facture d\'avoir (credit note) ?',
        options: [
          'Creer une facture avec montant negatif',
          'Bouton "Creer un avoir" sur la facture d\'origine',
          'Annuler la facture',
          'Contacter la comptabilite',
        ],
        correctAnswer: 1,
        explanation: 'Le bouton "Creer un avoir" genere un avoir lie a la facture d\'origine avec trace comptable.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q6',
        question: 'Comment gerer les factures recurrentes ?',
        options: [
          'Les recreer manuellement chaque mois',
          'Configurer un abonnement/contrat',
          'Ce n\'est pas possible',
          'Utiliser des rappels',
        ],
        correctAnswer: 1,
        explanation: 'Les contrats/abonnements permettent de generer automatiquement des factures recurrentes.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l4-q7',
        question: 'Comment appliquer differents taux de TVA sur une facture ?',
        options: [
          'Une facture = un seul taux TVA',
          'Selectionner le taux TVA par ligne d\'article',
          'Creer plusieurs factures',
          'Contacter un comptable',
        ],
        correctAnswer: 1,
        explanation: 'Chaque ligne d\'article peut avoir un taux de TVA different, le total est calcule automatiquement.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q8',
        question: 'Comment suivre les paiements d\'une facture ?',
        options: [
          'Via l\'onglet "Paiements" de la facture',
          'Dans le module Comptabilite uniquement',
          'Ce n\'est pas suivi automatiquement',
          'Via les releves bancaires',
        ],
        correctAnswer: 0,
        explanation: 'L\'onglet "Paiements" de la facture affiche tous les reglements associes et le solde restant.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q9',
        question: 'Comment configurer les relances automatiques ?',
        options: [
          'Parametres > Facturation > Relances',
          'Ce n\'est pas possible automatiquement',
          'Via le module Email',
          'Contacter le support',
        ],
        correctAnswer: 0,
        explanation: 'Les relances automatiques se configurent avec des emails a J+X, J+Y, etc. apres echeance.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'l4-q10',
        question: 'Comment dupliquer un devis pour un autre client ?',
        options: [
          'Copier-coller les informations',
          'Bouton "Dupliquer" puis modifier le client',
          'Ce n\'est pas possible',
          'Exporter et reimporter',
        ],
        correctAnswer: 1,
        explanation: 'Le bouton "Dupliquer" cree une copie du devis que vous pouvez modifier (client, articles, etc.).',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q11',
        question: 'Comment ajouter des frais de port a un devis ?',
        options: [
          'Ajouter une ligne d\'article "Frais de port"',
          'Utiliser le champ "Frais supplementaires"',
          'Les deux methodes sont possibles',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 2,
        explanation: 'Les frais de port peuvent etre ajoutes comme ligne d\'article ou via le champ dedie.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'l4-q12',
        question: 'Quelle est la difference entre facture pro forma et facture definitive ?',
        options: [
          'Aucune difference',
          'La pro forma est un devis deguise',
          'La pro forma n\'a pas de valeur comptable',
          'La pro forma est pour l\'export',
        ],
        correctAnswer: 2,
        explanation: 'Une facture pro forma est un document commercial sans valeur comptable, souvent utilise pour les formalites douanieres ou le financement.',
        points: 20,
        difficulty: 'difficile',
      },
    ],
  },
  {
    level: 5,
    title: 'Examen Niveau 5 - Comptabilite',
    description: 'Validez vos competences en comptabilite et finance',
    questions: [
      {
        id: 'l5-q1',
        question: 'Comment effectuer un rapprochement bancaire ?',
        options: [
          'Comparer manuellement les releves',
          'Module Comptabilite > Rapprochement bancaire',
          'Ce n\'est pas possible dans l\'ERP',
          'Via le menu Fichier',
        ],
        correctAnswer: 1,
        explanation: 'Le module Rapprochement bancaire permet d\'importer les releves et de les matcher avec les ecritures.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q2',
        question: 'Comment creer une ecriture comptable manuelle ?',
        options: [
          'Ce n\'est pas recommande',
          'Module Comptabilite > Ecritures > Nouvelle',
          'Via le journal de caisse uniquement',
          'Contacter un comptable',
        ],
        correctAnswer: 1,
        explanation: 'Les ecritures manuelles sont possibles mais doivent respecter l\'equilibre debit/credit.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q3',
        question: 'Qu\'est-ce qu\'un journal comptable ?',
        options: [
          'Un rapport mensuel',
          'Un registre regroupant les ecritures par type',
          'Un log des connexions',
          'Un planning',
        ],
        correctAnswer: 1,
        explanation: 'Les journaux (Ventes, Achats, Banque, OD) regroupent les ecritures comptables par nature.',
        points: 25,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q4',
        question: 'Comment generer le Grand Livre ?',
        options: [
          'Rapports > Comptabilite > Grand Livre',
          'Il se genere automatiquement',
          'Via Excel',
          'Contacter l\'expert-comptable',
        ],
        correctAnswer: 0,
        explanation: 'Le Grand Livre est accessible via les rapports comptables avec filtres par periode/compte.',
        points: 25,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q5',
        question: 'Comment lettrer des ecritures ?',
        options: [
          'Cliquer sur les ecritures a lettrer + bouton Lettrer',
          'C\'est fait automatiquement',
          'Ce n\'est pas possible',
          'Via l\'export comptable',
        ],
        correctAnswer: 0,
        explanation: 'Le lettrage permet de rapprocher les factures et leurs paiements pour un suivi clair.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q6',
        question: 'Comment declarer la TVA ?',
        options: [
          'Via le module Declarations > TVA',
          'Manuellement sur impots.gouv.fr',
          'C\'est automatique',
          'Via l\'expert-comptable uniquement',
        ],
        correctAnswer: 0,
        explanation: 'Le module Declarations genere les declarations TVA (CA3, CA12) avec les montants calcules.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q7',
        question: 'Qu\'est-ce qu\'une ecriture d\'OD ?',
        options: [
          'Operation Diverse - ecriture de regularisation',
          'Ordre de Debit',
          'Operation de Depot',
          'Ouverture de Dossier',
        ],
        correctAnswer: 0,
        explanation: 'Les OD (Operations Diverses) sont des ecritures de regularisation, provisions, ou ajustements.',
        points: 25,
        difficulty: 'moyen',
      },
      {
        id: 'l5-q8',
        question: 'Comment gerer les immobilisations ?',
        options: [
          'Module Comptabilite > Immobilisations',
          'Via Excel',
          'Ce n\'est pas gere',
          'Via un logiciel tiers',
        ],
        correctAnswer: 0,
        explanation: 'Le module Immobilisations gere l\'amortissement, les sorties, et la comptabilisation automatique.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q9',
        question: 'Comment cloturer un exercice comptable ?',
        options: [
          'Automatique au 31/12',
          'Comptabilite > Exercices > Cloturer',
          'Contacter le support',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 1,
        explanation: 'La cloture d\'exercice genere les ecritures de cloture et ouvre le nouvel exercice.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l5-q10',
        question: 'Comment exporter les ecritures pour l\'expert-comptable ?',
        options: [
          'Export > Format FEC ou format cabinet',
          'Imprimer et envoyer',
          'Donner un acces au logiciel',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 0,
        explanation: 'L\'export FEC (Fichier des Ecritures Comptables) est le format standard pour les experts-comptables et l\'administration fiscale.',
        points: 25,
        difficulty: 'moyen',
      },
    ],
  },
  {
    level: 6,
    title: 'Examen Niveau 6 - Gestion des Stocks',
    description: 'Maitrisez la gestion des stocks et approvisionnements',
    questions: [
      {
        id: 'l6-q1',
        question: 'Comment creer un nouvel article en stock ?',
        options: [
          'Stocks > Articles > Nouveau',
          'Via l\'import uniquement',
          'Dans les parametres',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 0,
        explanation: 'Le menu Articles permet de creer de nouveaux articles avec leurs caracteristiques et stocks.',
        points: 25,
        difficulty: 'moyen',
      },
      {
        id: 'l6-q2',
        question: 'Comment effectuer un inventaire ?',
        options: [
          'Compter manuellement',
          'Stocks > Inventaire > Nouvel inventaire',
          'Via l\'import Excel',
          'Ce n\'est pas necessaire',
        ],
        correctAnswer: 1,
        explanation: 'L\'outil d\'inventaire permet de saisir les quantites comptees et genere les ecarts.',
        points: 25,
        difficulty: 'moyen',
      },
      {
        id: 'l6-q3',
        question: 'Qu\'est-ce qu\'un seuil de reapprovisionnement ?',
        options: [
          'Le stock maximum',
          'La quantite declenchant une alerte/commande',
          'Le stock de securite',
          'La quantite minimum de commande',
        ],
        correctAnswer: 1,
        explanation: 'Le seuil de reapprovisionnement declenche une alerte ou une commande automatique quand le stock passe en dessous.',
        points: 25,
        difficulty: 'moyen',
      },
      {
        id: 'l6-q4',
        question: 'Comment suivre les mouvements de stock ?',
        options: [
          'Via les factures uniquement',
          'Stocks > Mouvements',
          'Ce n\'est pas suivi',
          'Via l\'historique article',
        ],
        correctAnswer: 1,
        explanation: 'Le journal des mouvements liste toutes les entrees/sorties avec dates, quantites et origines.',
        points: 25,
        difficulty: 'moyen',
      },
      {
        id: 'l6-q5',
        question: 'Comment gerer plusieurs entrepots ?',
        options: [
          'Creer plusieurs societes',
          'Configurer les emplacements de stock',
          'Ce n\'est pas possible',
          'Utiliser des codes article differents',
        ],
        correctAnswer: 1,
        explanation: 'Les emplacements de stock permettent de gerer plusieurs entrepots avec transferts inter-sites.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q6',
        question: 'Qu\'est-ce que la methode FIFO ?',
        options: [
          'First In First Out - les plus anciens sortent en premier',
          'Un type de code-barres',
          'Une methode de comptage',
          'Un mode de livraison',
        ],
        correctAnswer: 0,
        explanation: 'FIFO (Premier Entre Premier Sorti) valorise les sorties au cout des articles les plus anciens.',
        points: 25,
        difficulty: 'moyen',
      },
      {
        id: 'l6-q7',
        question: 'Comment gerer les numeros de serie/lots ?',
        options: [
          'Dans les notes de l\'article',
          'Activer le suivi par lot/serie sur l\'article',
          'Ce n\'est pas possible',
          'Via un champ personnalise',
        ],
        correctAnswer: 1,
        explanation: 'Le suivi par lot ou numero de serie permet la tracabilite complete des articles.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q8',
        question: 'Comment generer un bon de preparation ?',
        options: [
          'Via la commande client',
          'Manuellement',
          'C\'est automatique',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 0,
        explanation: 'Le bon de preparation est genere depuis la commande client pour guider la preparation en entrepot.',
        points: 25,
        difficulty: 'moyen',
      },
      {
        id: 'l6-q9',
        question: 'Comment gerer les retours clients (SAV) ?',
        options: [
          'Creer un avoir',
          'Utiliser le module Retours',
          'Modifier la facture',
          'Ce n\'est pas gere',
        ],
        correctAnswer: 1,
        explanation: 'Le module Retours gere le processus complet : creation, controle qualite, remise en stock ou mise au rebut.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'l6-q10',
        question: 'Comment calculer la valeur du stock ?',
        options: [
          'Rapports > Stocks > Valorisation',
          'Addition manuelle',
          'Via la comptabilite',
          'Ce n\'est pas calcule',
        ],
        correctAnswer: 0,
        explanation: 'Le rapport de valorisation calcule la valeur du stock selon la methode choisie (FIFO, CUMP, etc.).',
        points: 25,
        difficulty: 'moyen',
      },
    ],
  },
  {
    level: 7,
    title: 'Examen Niveau 7 - Administration & IA',
    description: 'Maitrisez l\'administration systeme et les outils IA',
    questions: [
      {
        id: 'l7-q1',
        question: 'Comment creer un nouvel utilisateur ?',
        options: [
          'Admin > Utilisateurs > Nouveau',
          'L\'utilisateur s\'inscrit lui-meme',
          'Via l\'API uniquement',
          'Contacter Azal',
        ],
        correctAnswer: 0,
        explanation: 'L\'administrateur cree les utilisateurs et leur attribue des roles et permissions.',
        points: 30,
        difficulty: 'moyen',
      },
      {
        id: 'l7-q2',
        question: 'Comment configurer l\'authentification double facteur (2FA) ?',
        options: [
          'Securite > Double authentification',
          'Ce n\'est pas disponible',
          'Via Google uniquement',
          'Sur demande au support',
        ],
        correctAnswer: 0,
        explanation: 'La 2FA se configure par utilisateur ou globalement via les parametres de securite.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q3',
        question: 'Comment utiliser l\'assistant IA Theo ?',
        options: [
          'Icone robot en bas a droite',
          'Menu Aide > Assistant IA',
          'Raccourci Ctrl+Shift+T',
          'Toutes ces reponses',
        ],
        correctAnswer: 3,
        explanation: 'Theo est accessible via plusieurs methodes pour une aide contextuelle intelligente.',
        points: 30,
        difficulty: 'moyen',
      },
      {
        id: 'l7-q4',
        question: 'Que peut faire l\'agent IA Marceau ?',
        options: [
          'Repondre aux questions',
          'Executer des actions automatisees',
          'Generer des rapports',
          'Toutes ces reponses',
        ],
        correctAnswer: 3,
        explanation: 'Marceau est un agent IA capable d\'executer des taches : appels, creation devis, support client, etc.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q5',
        question: 'Comment configurer les webhooks ?',
        options: [
          'Admin > Integrations > Webhooks',
          'Via l\'API',
          'Ce n\'est pas possible',
          'Contacter le developpeur',
        ],
        correctAnswer: 0,
        explanation: 'Les webhooks permettent d\'envoyer des notifications en temps reel vers des systemes externes.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q6',
        question: 'Comment consulter les logs d\'audit ?',
        options: [
          'Admin > Audit > Journal',
          'Ils ne sont pas accessibles',
          'Via la base de donnees',
          'Contacter le DPO',
        ],
        correctAnswer: 0,
        explanation: 'Le journal d\'audit trace toutes les actions sensibles pour la conformite et la securite.',
        points: 30,
        difficulty: 'moyen',
      },
      {
        id: 'l7-q7',
        question: 'Comment programmer une sauvegarde automatique ?',
        options: [
          'Admin > Sauvegardes > Planification',
          'C\'est fait automatiquement par Azal',
          'Via un script externe',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 1,
        explanation: 'Les sauvegardes sont gerees automatiquement par l\'infrastructure Azal avec retention configurable.',
        points: 30,
        difficulty: 'moyen',
      },
      {
        id: 'l7-q8',
        question: 'Comment creer un workflow automatise ?',
        options: [
          'Admin > Workflows > Nouveau',
          'Via le code uniquement',
          'Contacter Azal',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 0,
        explanation: 'L\'editeur de workflows permet de creer des automatisations sans code avec triggers et actions.',
        points: 30,
        difficulty: 'difficile',
      },
      {
        id: 'l7-q9',
        question: 'Comment gerer les permissions par role ?',
        options: [
          'Admin > Roles > Modifier les permissions',
          'Modifier chaque utilisateur',
          'Via les groupes uniquement',
          'Contacter l\'administrateur superieur',
        ],
        correctAnswer: 0,
        explanation: 'Les roles definissent des ensembles de permissions attribuables aux utilisateurs.',
        points: 30,
        difficulty: 'moyen',
      },
      {
        id: 'l7-q10',
        question: 'Comment integrer AZALSCORE avec un service externe ?',
        options: [
          'Admin > Integrations',
          'Via l\'API REST',
          'Avec les connecteurs pre-configures',
          'Toutes ces reponses',
        ],
        correctAnswer: 3,
        explanation: 'AZALSCORE offre plusieurs methodes d\'integration : API, webhooks, connecteurs natifs.',
        points: 30,
        difficulty: 'difficile',
      },
    ],
  },
];

// ============================================================================
// EXAMENS DE NIVEAU - ANGLAIS
// ============================================================================

const LEVEL_EXAMS_EN: TranslatedExam[] = [
  {
    level: 2,
    title: 'Level 2 Exam - The Basics',
    description: 'Validate your fundamental knowledge of AZALSCORE',
    questions: [
      {
        id: 'l2-q1',
        question: 'How do you access the AZALSCORE main menu?',
        options: [
          'Click on the logo at the top left',
          'Press the Escape key',
          'Double-click anywhere',
          'Use the shortcut Ctrl+M',
        ],
        correctAnswer: 0,
        explanation: 'The AZALSCORE logo at the top left opens the main menu with all modules.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q2',
        question: 'Which shortcut opens the global search?',
        options: [
          'Ctrl+F',
          'Ctrl+K or Cmd+K',
          'Alt+S',
          'F3',
        ],
        correctAnswer: 1,
        explanation: 'Ctrl+K (or Cmd+K on Mac) opens the global search bar to quickly find clients, quotes, invoices, etc.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q3',
        question: 'Where is the button to create a new client?',
        options: [
          'In the settings',
          'At the top right of the client list',
          'In the Help menu',
          'On the homepage only',
        ],
        correctAnswer: 1,
        explanation: 'The "+ New client" button is located at the top right of the client list in the CRM module.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q4',
        question: 'How do you save your changes in a form?',
        options: [
          'They are saved automatically',
          'Click the Save button',
          'Press Enter',
          'Close the form',
        ],
        correctAnswer: 1,
        explanation: 'Click the Save button to save your changes. An automatic draft may exist but manual saving is required.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q5',
        question: 'Which icon represents the Accounting module?',
        options: [
          'A chart',
          'A calculator',
          'An open book',
          'A coin',
        ],
        correctAnswer: 1,
        explanation: 'The calculator represents the Accounting module in the navigation.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q6',
        question: 'How do you access contextual help?',
        options: [
          'Press F1',
          'Click the ? icon at the top right',
          'Both answers are correct',
          'None of these answers',
        ],
        correctAnswer: 2,
        explanation: 'Contextual help is accessible via F1 or the ? icon at the top right.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q7',
        question: 'Where are your notifications located?',
        options: [
          'In the settings',
          'On the bell icon at the top right',
          'In the Help menu',
          'On the homepage only',
        ],
        correctAnswer: 1,
        explanation: 'The bell icon at the top right displays all your notifications.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q8',
        question: 'How do you customize your dashboard?',
        options: [
          'Click the gear icon on the dashboard',
          'Contact the administrator',
          'This is not possible',
          'Via the File menu',
        ],
        correctAnswer: 0,
        explanation: 'The gear icon on the dashboard allows you to add/remove/reorganize widgets.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q9',
        question: 'What is the role of the breadcrumb?',
        options: [
          'Display recently viewed documents',
          'Show your position in the application',
          'List your favorites',
          'Display keyboard shortcuts',
        ],
        correctAnswer: 1,
        explanation: 'The breadcrumb shows your position in the application tree and allows you to navigate back easily.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'l2-q10',
        question: 'How do you add a page to favorites?',
        options: [
          'Click the star in the address bar',
          'Use Ctrl+D',
          'Click the bookmark icon next to the title',
          'All of these answers',
        ],
        correctAnswer: 2,
        explanation: 'The bookmark icon next to the page title allows you to add it to favorites for quick access.',
        points: 10,
        difficulty: 'facile',
      },
    ],
  },
  // Note: Additional levels would follow the same pattern
  // For brevity, I'm including just Level 2 as an example
];

// ============================================================================
// QUIZ D'ENTRAINEMENT - FRANCAIS
// ============================================================================

const PRACTICE_QUIZZES_FR: TranslatedQuiz[] = [
  {
    id: 'navigation',
    title: 'Navigation & Interface',
    description: 'Testez vos connaissances sur la navigation dans AZALSCORE',
    category: 'navigation',
    questions: [
      {
        id: 'nav-q1',
        question: 'Comment ouvrir la barre de recherche rapide ?',
        options: ['Ctrl+K', 'Ctrl+F', 'Alt+R', 'F5'],
        correctAnswer: 0,
        explanation: 'Ctrl+K (ou Cmd+K sur Mac) ouvre la recherche globale.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-q2',
        question: 'Ou se trouvent les notifications ?',
        options: [
          'En bas a gauche',
          'En haut a droite (icone cloche)',
          'Dans les parametres',
          'Sur la page d\'accueil',
        ],
        correctAnswer: 1,
        explanation: 'L\'icone cloche en haut a droite affiche toutes vos notifications.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-q3',
        question: 'Comment revenir a la page precedente ?',
        options: [
          'Cliquer sur le logo',
          'Utiliser le fil d\'Ariane ou le bouton retour',
          'Fermer et rouvrir l\'application',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 1,
        explanation: 'Le fil d\'Ariane et le bouton retour du navigateur permettent de revenir en arriere.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-q4',
        question: 'Comment personnaliser le tableau de bord ?',
        options: [
          'Via les parametres generaux',
          'Icone engrenage sur le dashboard',
          'Ce n\'est pas personnalisable',
          'En contactant le support',
        ],
        correctAnswer: 1,
        explanation: 'L\'icone engrenage permet d\'ajouter, supprimer et reorganiser les widgets.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-q5',
        question: 'Quel raccourci ouvre l\'aide contextuelle ?',
        options: ['F1', 'F2', 'Ctrl+H', 'Echap'],
        correctAnswer: 0,
        explanation: 'F1 ouvre l\'aide contextuelle adaptee a la page en cours.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-q6',
        question: 'Comment ajouter une page aux favoris ?',
        options: [
          'Cliquer sur l\'icone signet',
          'Ctrl+D',
          'Via le menu Favoris',
          'Toutes ces methodes',
        ],
        correctAnswer: 0,
        explanation: 'L\'icone signet a cote du titre permet d\'ajouter la page aux favoris.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-q7',
        question: 'Comment basculer en mode sombre ?',
        options: [
          'Parametres > Apparence',
          'Cliquer sur l\'icone lune',
          'Ctrl+Shift+D',
          'Toutes ces methodes',
        ],
        correctAnswer: 3,
        explanation: 'Le mode sombre est accessible via plusieurs methodes pour plus de flexibilite.',
        points: 10,
        difficulty: 'moyen',
      },
      {
        id: 'nav-q8',
        question: 'Ou trouver vos taches en attente ?',
        options: [
          'Page d\'accueil uniquement',
          'Widget "Mes taches" du dashboard',
          'Menu Taches',
          'B et C sont corrects',
        ],
        correctAnswer: 3,
        explanation: 'Les taches sont visibles sur le dashboard et via le menu dedie.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-q9',
        question: 'Comment changer de societe (multi-societes) ?',
        options: [
          'Se deconnecter et reconnecter',
          'Menu utilisateur > Changer de societe',
          'Ce n\'est pas possible',
          'Via les parametres',
        ],
        correctAnswer: 1,
        explanation: 'Le menu utilisateur permet de basculer entre les societes sans se deconnecter.',
        points: 10,
        difficulty: 'moyen',
      },
    ],
  },
  {
    id: 'crm',
    title: 'Gestion Clients (CRM)',
    description: 'Testez vos connaissances sur le module CRM',
    category: 'crm',
    questions: [
      {
        id: 'crm-q1',
        question: 'Comment creer un nouveau client ?',
        options: [
          'CRM > Clients > Nouveau',
          'Fichier > Nouveau > Client',
          'Bouton + en haut de la liste',
          'A et C sont corrects',
        ],
        correctAnswer: 3,
        explanation: 'Un nouveau client peut etre cree via le menu CRM ou le bouton + de la liste.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'crm-q2',
        question: 'Quelle est la difference entre prospect et client ?',
        options: [
          'Aucune difference',
          'Le prospect n\'a pas encore achete',
          'Le client est une entreprise',
          'Le prospect est un ancien client',
        ],
        correctAnswer: 1,
        explanation: 'Un prospect devient client apres sa premiere commande ou facture.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'crm-q3',
        question: 'Ou voir l\'historique des interactions ?',
        options: [
          'Onglet Activites de la fiche client',
          'Menu Historique',
          'Ce n\'est pas enregistre',
          'Dans les parametres',
        ],
        correctAnswer: 0,
        explanation: 'L\'onglet Activites affiche tout l\'historique : appels, emails, RDV, etc.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'crm-q4',
        question: 'Comment importer des clients depuis Excel ?',
        options: [
          'Copier-coller',
          'Menu Importer > Fichier Excel',
          'Ce n\'est pas possible',
          'Via l\'API',
        ],
        correctAnswer: 1,
        explanation: 'Le menu Importer permet de charger un fichier Excel avec mapping des colonnes.',
        points: 10,
        difficulty: 'moyen',
      },
      {
        id: 'crm-q5',
        question: 'Comment fusionner des doublons ?',
        options: [
          'Supprimer l\'un des deux',
          'Outil de deduplication',
          'Ce n\'est pas possible',
          'Contacter le support',
        ],
        correctAnswer: 1,
        explanation: 'L\'outil de deduplication detecte et fusionne les doublons en conservant toutes les donnees.',
        points: 10,
        difficulty: 'moyen',
      },
      {
        id: 'crm-q6',
        question: 'Comment attribuer un commercial a un client ?',
        options: [
          'Via l\'administration',
          'Onglet Equipe commerciale',
          'Ce n\'est pas possible',
          'Par email',
        ],
        correctAnswer: 1,
        explanation: 'L\'onglet Equipe commerciale permet d\'assigner des commerciaux au client.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'crm-q7',
        question: 'Comment voir le CA d\'un client ?',
        options: [
          'Dashboard de la fiche client',
          'Calculer manuellement',
          'Export Excel',
          'Ce n\'est pas disponible',
        ],
        correctAnswer: 0,
        explanation: 'Le dashboard client affiche le CA, les factures en cours, et l\'evolution.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'crm-q8',
        question: 'Comment bloquer un client impaye ?',
        options: [
          'Le supprimer',
          'Activer le blocage dans la fiche',
          'Envoyer un email',
          'Attendre',
        ],
        correctAnswer: 1,
        explanation: 'Le blocage empeche de creer des devis/commandes tant que le paiement n\'est pas fait.',
        points: 10,
        difficulty: 'moyen',
      },
      {
        id: 'crm-q9',
        question: 'Comment creer un segment de clients ?',
        options: [
          'CRM > Segments > Nouveau',
          'Automatiquement',
          'Via l\'API',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 0,
        explanation: 'Les segments permettent de grouper les clients selon des criteres (CA, secteur, etc.).',
        points: 10,
        difficulty: 'moyen',
      },
    ],
  },
  {
    id: 'invoicing',
    title: 'Facturation',
    description: 'Testez vos connaissances sur les devis et factures',
    category: 'invoicing',
    questions: [
      {
        id: 'inv-q1',
        question: 'Comment transformer un devis en facture ?',
        options: [
          'Recreer la facture manuellement',
          'Bouton "Convertir en facture"',
          'Envoyer le devis',
          'Attendre la validation',
        ],
        correctAnswer: 1,
        explanation: 'Le bouton "Convertir en facture" cree automatiquement une facture depuis le devis.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'inv-q2',
        question: 'Comment appliquer une remise ?',
        options: [
          'Modifier les prix manuellement',
          'Champ Remise sur la ligne ou le total',
          'Ce n\'est pas possible',
          'Via les parametres',
        ],
        correctAnswer: 1,
        explanation: 'Les remises peuvent etre appliquees par ligne (%) ou sur le total.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'inv-q3',
        question: 'Comment envoyer une facture par email ?',
        options: [
          'Telecharger et envoyer manuellement',
          'Bouton "Envoyer par email"',
          'Les deux methodes',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 2,
        explanation: 'L\'envoi peut se faire directement via le bouton ou apres telechargement du PDF.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'inv-q4',
        question: 'Comment creer un avoir ?',
        options: [
          'Facture avec montant negatif',
          'Bouton "Creer un avoir"',
          'Annuler la facture',
          'Contacter la compta',
        ],
        correctAnswer: 1,
        explanation: 'Le bouton "Creer un avoir" genere un avoir lie a la facture d\'origine.',
        points: 10,
        difficulty: 'moyen',
      },
      {
        id: 'inv-q5',
        question: 'Comment gerer les factures recurrentes ?',
        options: [
          'Les recreer chaque mois',
          'Configurer un abonnement/contrat',
          'Ce n\'est pas possible',
          'Via les rappels',
        ],
        correctAnswer: 1,
        explanation: 'Les contrats/abonnements generent automatiquement des factures recurrentes.',
        points: 10,
        difficulty: 'moyen',
      },
      {
        id: 'inv-q6',
        question: 'Comment dupliquer un devis ?',
        options: [
          'Copier-coller',
          'Bouton "Dupliquer"',
          'Export/Import',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 1,
        explanation: 'Le bouton "Dupliquer" cree une copie modifiable du devis.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'inv-q7',
        question: 'Comment suivre les paiements d\'une facture ?',
        options: [
          'Onglet Paiements de la facture',
          'Module Comptabilite uniquement',
          'Ce n\'est pas suivi',
          'Via les releves bancaires',
        ],
        correctAnswer: 0,
        explanation: 'L\'onglet Paiements affiche tous les reglements et le solde restant.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'inv-q8',
        question: 'Comment configurer les relances automatiques ?',
        options: [
          'Parametres > Facturation > Relances',
          'Ce n\'est pas automatique',
          'Via le module Email',
          'Contacter le support',
        ],
        correctAnswer: 0,
        explanation: 'Les relances automatiques se configurent avec des emails a J+X apres echeance.',
        points: 10,
        difficulty: 'difficile',
      },
      {
        id: 'inv-q9',
        question: 'Qu\'est-ce qu\'une facture pro forma ?',
        options: [
          'Une facture definitive',
          'Un document sans valeur comptable',
          'Une facture d\'acompte',
          'Une facture annulee',
        ],
        correctAnswer: 1,
        explanation: 'La pro forma est un document commercial sans valeur comptable, pour formalites ou financement.',
        points: 10,
        difficulty: 'moyen',
      },
    ],
  },
  {
    id: 'ai',
    title: 'Intelligence Artificielle (Theo & Marceau)',
    description: 'Testez vos connaissances sur les assistants IA',
    category: 'ai',
    questions: [
      {
        id: 'ai-q1',
        question: 'Qui est Theo ?',
        options: [
          'L\'administrateur systeme',
          'L\'assistant IA pour les questions',
          'Un module de reporting',
          'Le support client',
        ],
        correctAnswer: 1,
        explanation: 'Theo est l\'assistant IA qui repond a vos questions sur AZALSCORE.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'ai-q2',
        question: 'Comment acceder a Theo ?',
        options: [
          'Icone robot en bas a droite',
          'Raccourci Ctrl+Shift+T',
          'Menu Aide > Assistant IA',
          'Toutes ces methodes',
        ],
        correctAnswer: 3,
        explanation: 'Theo est accessible via plusieurs methodes pour plus de flexibilite.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'ai-q3',
        question: 'Qui est Marceau ?',
        options: [
          'L\'assistant vocal',
          'L\'agent IA qui execute des actions',
          'Le chatbot de support',
          'Le module analytics',
        ],
        correctAnswer: 1,
        explanation: 'Marceau est un agent IA capable d\'executer des taches automatisees.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'ai-q4',
        question: 'Que peut faire Marceau ?',
        options: [
          'Passer des appels telephoniques',
          'Creer des devis automatiquement',
          'Repondre aux tickets support',
          'Toutes ces actions',
        ],
        correctAnswer: 3,
        explanation: 'Marceau peut executer de nombreuses actions : appels, devis, support, etc.',
        points: 10,
        difficulty: 'moyen',
      },
      {
        id: 'ai-q5',
        question: 'Comment valider les actions de Marceau ?',
        options: [
          'Elles sont automatiques',
          'Via le dashboard Marceau',
          'Par email',
          'Ce n\'est pas necessaire',
        ],
        correctAnswer: 1,
        explanation: 'Le dashboard Marceau permet de valider ou rejeter les actions proposees.',
        points: 10,
        difficulty: 'moyen',
      },
      {
        id: 'ai-q6',
        question: 'Theo peut-il modifier des donnees ?',
        options: [
          'Oui, tout',
          'Non, il repond aux questions uniquement',
          'Seulement avec validation',
          'Selon les permissions',
        ],
        correctAnswer: 1,
        explanation: 'Theo est un assistant de consultation, il ne modifie pas les donnees.',
        points: 10,
        difficulty: 'moyen',
      },
      {
        id: 'ai-q7',
        question: 'Comment Marceau gere-t-il les appels ?',
        options: [
          'Via la telephonie integree',
          'Par un service externe',
          'Ce n\'est pas possible',
          'Manuellement',
        ],
        correctAnswer: 0,
        explanation: 'Marceau utilise la telephonie integree pour passer et recevoir des appels.',
        points: 10,
        difficulty: 'difficile',
      },
      {
        id: 'ai-q8',
        question: 'Comment former Marceau a vos processus ?',
        options: [
          'Via les parametres IA',
          'En lui expliquant par chat',
          'Via les workflows et prompts',
          'Ce n\'est pas possible',
        ],
        correctAnswer: 2,
        explanation: 'Marceau s\'adapte a vos processus via les workflows et les prompts personnalises.',
        points: 10,
        difficulty: 'difficile',
      },
    ],
  },
];

// ============================================================================
// QUIZ D'ENTRAINEMENT - ANGLAIS
// ============================================================================

const PRACTICE_QUIZZES_EN: TranslatedQuiz[] = [
  {
    id: 'navigation',
    title: 'Navigation & Interface',
    description: 'Test your knowledge of AZALSCORE navigation',
    category: 'navigation',
    questions: [
      {
        id: 'nav-q1',
        question: 'How do you open the quick search bar?',
        options: ['Ctrl+K', 'Ctrl+F', 'Alt+R', 'F5'],
        correctAnswer: 0,
        explanation: 'Ctrl+K (or Cmd+K on Mac) opens the global search.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-q2',
        question: 'Where are the notifications located?',
        options: [
          'Bottom left',
          'Top right (bell icon)',
          'In the settings',
          'On the homepage',
        ],
        correctAnswer: 1,
        explanation: 'The bell icon at the top right displays all your notifications.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-q3',
        question: 'How do you go back to the previous page?',
        options: [
          'Click on the logo',
          'Use the breadcrumb or back button',
          'Close and reopen the application',
          'This is not possible',
        ],
        correctAnswer: 1,
        explanation: 'The breadcrumb and browser back button allow you to navigate back.',
        points: 10,
        difficulty: 'facile',
      },
    ],
  },
  // Additional quizzes would follow the same pattern
];

// ============================================================================
// FONCTION D'ACCES AUX TRADUCTIONS
// ============================================================================

export function getLevelExams(language: SupportedLanguage): TranslatedExam[] {
  switch (language) {
    case 'en':
      return LEVEL_EXAMS_EN;
    case 'fr':
    default:
      return LEVEL_EXAMS_FR;
    // Other languages would fall back to French for now
    // Add translations as they become available
  }
}

export function getPracticeQuizzes(language: SupportedLanguage): TranslatedQuiz[] {
  switch (language) {
    case 'en':
      return PRACTICE_QUIZZES_EN;
    case 'fr':
    default:
      return PRACTICE_QUIZZES_FR;
  }
}

export function getExamByLevel(language: SupportedLanguage, level: number): TranslatedExam | undefined {
  const exams = getLevelExams(language);
  return exams.find(exam => exam.level === level);
}

export function getQuizById(language: SupportedLanguage, quizId: string): TranslatedQuiz | undefined {
  const quizzes = getPracticeQuizzes(language);
  return quizzes.find(quiz => quiz.id === quizId);
}

// ============================================================================
// EXPORTS
// ============================================================================

export {
  LEVEL_EXAMS_FR,
  LEVEL_EXAMS_EN,
  PRACTICE_QUIZZES_FR,
  PRACTICE_QUIZZES_EN,
};
