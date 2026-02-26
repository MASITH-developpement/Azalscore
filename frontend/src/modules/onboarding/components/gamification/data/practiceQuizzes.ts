/**
 * AZALSCORE - Quiz d'entraînement par thème
 * ==========================================
 * Quiz permettant de s'entraîner sans conséquence sur le niveau
 */

import type { PracticeQuiz } from '../types';

export const PRACTICE_QUIZZES: PracticeQuiz[] = [
  // ============================================================================
  // NAVIGATION & INTERFACE
  // ============================================================================
  {
    id: 'quiz-navigation',
    title: 'Navigation & Interface',
    description: "Maîtrisez l'interface d'AZALSCORE",
    category: 'Bases',
    icon: '🧭',
    color: 'blue',
    duration: 5,
    difficulty: 'facile',
    xpReward: 30,
    questions: [
      {
        id: 'nav-1',
        question: 'Quel raccourci ouvre la recherche globale ?',
        options: ['Ctrl+F', 'Touche /', 'Ctrl+K', 'F3'],
        correctAnswer: 1,
        explanation: 'La touche "/" ouvre la recherche globale depuis n\'importe quel écran.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-2',
        question: 'Comment accéder aux notifications ?',
        options: ['Menu principal', 'Icône cloche en haut à droite', 'Profil utilisateur', 'Paramètres'],
        correctAnswer: 1,
        explanation: 'L\'icône cloche dans la barre supérieure affiche les notifications.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-3',
        question: 'Où se trouve votre profil utilisateur ?',
        options: ['Menu principal', 'Clic sur votre avatar', 'Paramètres système', "Page d'accueil"],
        correctAnswer: 1,
        explanation: 'Cliquez sur votre avatar en haut à droite pour accéder à votre profil.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-4',
        question: 'Comment réduire la barre de menu latérale ?',
        options: ['Double-clic', 'Bouton flèche sur le menu', 'Paramètres', 'Impossible'],
        correctAnswer: 1,
        explanation: 'Le bouton flèche permet de réduire/étendre le menu latéral.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'nav-5',
        question: 'Quel préfixe pour chercher un client ?',
        options: ['#client', '@NomClient', '!client', '/client'],
        correctAnswer: 1,
        explanation: 'Le préfixe @ permet de rechercher parmi les clients.',
        points: 10,
        difficulty: 'facile',
      },
    ],
  },

  // ============================================================================
  // CRM & CLIENTS
  // ============================================================================
  {
    id: 'quiz-crm',
    title: 'CRM & Gestion Clients',
    description: 'Gérez efficacement vos clients et prospects',
    category: 'Commercial',
    icon: '👥',
    color: 'green',
    duration: 8,
    difficulty: 'moyen',
    xpReward: 50,
    questions: [
      {
        id: 'crm-1',
        question: 'Quelle est la différence entre prospect et client ?',
        options: ['Aucune', "Le prospect n'a pas encore acheté", 'Le client est inactif', 'Question de budget'],
        correctAnswer: 1,
        explanation: 'Un prospect devient client après sa première commande.',
        points: 15,
        difficulty: 'facile',
      },
      {
        id: 'crm-2',
        question: 'Quelle info est obligatoire pour un client B2B français ?',
        options: ['Email', 'Téléphone', 'SIRET', 'Site web'],
        correctAnswer: 2,
        explanation: 'Le SIRET (14 chiffres) est obligatoire pour les entreprises françaises.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'crm-3',
        question: 'Combien de contacts peut-on associer à un client ?',
        options: ['1 seul', 'Maximum 5', 'Maximum 10', 'Illimité'],
        correctAnswer: 3,
        explanation: "Il n'y a pas de limite au nombre de contacts par fiche client.",
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'crm-4',
        question: 'Comment archiver un client inactif ?',
        options: ['Le supprimer', 'Menu Actions > Archiver', 'Modifier son statut', 'Contacter le support'],
        correctAnswer: 1,
        explanation: "L'archivage conserve l'historique tout en masquant le client des listes.",
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'crm-5',
        question: "Où voir l'historique des échanges avec un client ?",
        options: ['Menu Rapports', 'Onglet Historique de la fiche', 'Export Excel', 'Module Audit'],
        correctAnswer: 1,
        explanation: "L'onglet Historique centralise tous les échanges: emails, appels, notes.",
        points: 15,
        difficulty: 'facile',
      },
      {
        id: 'crm-6',
        question: "Qu'est-ce que le scoring client ?",
        options: ['Note de satisfaction', 'Score calculé selon le comportement', 'Évaluation de risque', 'Classement par CA'],
        correctAnswer: 1,
        explanation: 'Le scoring attribue automatiquement un score basé sur les interactions et le potentiel.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'crm-7',
        question: 'Comment fusionner deux fiches client en doublon ?',
        options: ['Supprimer une', 'Menu Actions > Fusionner', 'Copier-coller', 'Impossible'],
        correctAnswer: 1,
        explanation: 'La fusion conserve toutes les données des deux fiches en une seule.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'crm-8',
        question: 'Comment importer une liste de clients depuis Excel ?',
        options: ['Copier-coller', 'CRM > Importer > CSV/Excel', 'Demander au support', 'API uniquement'],
        correctAnswer: 1,
        explanation: "L'import CSV/Excel permet de mapper les colonnes aux champs AZALSCORE.",
        points: 15,
        difficulty: 'moyen',
      },
    ],
  },

  // ============================================================================
  // DEVIS & FACTURATION
  // ============================================================================
  {
    id: 'quiz-facturation',
    title: 'Devis & Facturation',
    description: 'Maîtrisez le cycle commercial complet',
    category: 'Commercial',
    icon: '📄',
    color: 'indigo',
    duration: 10,
    difficulty: 'moyen',
    xpReward: 60,
    questions: [
      {
        id: 'fact-1',
        question: "Quel est l'ordre du cycle commercial ?",
        options: ['Facture > Devis > Commande', 'Devis > Commande > Facture', 'Commande > Facture > Devis', 'Devis > Facture'],
        correctAnswer: 1,
        explanation: 'Le cycle standard: Devis > Commande > Bon de livraison > Facture.',
        points: 15,
        difficulty: 'facile',
      },
      {
        id: 'fact-2',
        question: "Durée de validité par défaut d'un devis ?",
        options: ['15 jours', '30 jours', '60 jours', '90 jours'],
        correctAnswer: 1,
        explanation: 'Par défaut, un devis est valide 30 jours (modifiable dans les paramètres).',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'fact-3',
        question: 'Comment appliquer une remise de 10% sur une ligne ?',
        options: ['Modifier le prix', 'Colonne Remise de la ligne', 'Note en bas', 'Impossible par ligne'],
        correctAnswer: 1,
        explanation: 'Chaque ligne a sa colonne Remise pour les remises individuelles.',
        points: 15,
        difficulty: 'facile',
      },
      {
        id: 'fact-4',
        question: 'Quand le numéro de facture est-il généré ?',
        options: ['À la création', 'À la validation', "À l'envoi", 'Au paiement'],
        correctAnswer: 1,
        explanation: 'Le numéro est attribué à la validation, pas en mode brouillon.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'fact-5',
        question: 'Comment créer un avoir suite à un retour ?',
        options: ['Facture négative', 'Depuis la facture > Créer avoir', 'Supprimer la facture', 'Nouveau document'],
        correctAnswer: 1,
        explanation: "Créer l'avoir depuis la facture originale assure la traçabilité.",
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'fact-6',
        question: 'Comment dupliquer un devis existant ?',
        options: ['Copier-coller', 'Menu Actions > Dupliquer', 'Export/Import', 'Nouveau + copie manuelle'],
        correctAnswer: 1,
        explanation: 'La duplication crée une copie complète du devis.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'fact-7',
        question: 'Quel statut indique un devis en attente de réponse ?',
        options: ['Brouillon', 'Envoyé', 'Accepté', 'En cours'],
        correctAnswer: 1,
        explanation: 'Le statut "Envoyé" indique que le client a reçu le devis.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'fact-8',
        question: 'Comment envoyer une facture par email ?',
        options: ['Export PDF + email externe', 'Bouton Envoyer par email', 'Partager le lien', 'Impression uniquement'],
        correctAnswer: 1,
        explanation: 'Le bouton "Envoyer par email" génère le PDF et l\'envoie directement.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'fact-9',
        question: 'Peut-on modifier une facture validée ?',
        options: ['Oui librement', 'Non, il faut créer un avoir', 'Seulement les notes', 'Avec mot de passe admin'],
        correctAnswer: 1,
        explanation: 'Une facture validée est figée. Pour corriger, créez un avoir puis une nouvelle facture.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'fact-10',
        question: 'Où configurer les conditions de paiement par défaut ?',
        options: ['Chaque document', 'Paramètres > Commercial', 'Fiche client', 'Non configurable'],
        correctAnswer: 1,
        explanation: 'Les valeurs par défaut se définissent dans Paramètres > Commercial.',
        points: 15,
        difficulty: 'moyen',
      },
    ],
  },

  // ============================================================================
  // COMPTABILITÉ
  // ============================================================================
  {
    id: 'quiz-comptabilite',
    title: 'Comptabilité & Finance',
    description: 'Les fondamentaux de la gestion financière',
    category: 'Finance',
    icon: '💰',
    color: 'emerald',
    duration: 12,
    difficulty: 'difficile',
    xpReward: 80,
    questions: [
      {
        id: 'compta-1',
        question: 'Quel journal pour les factures de vente ?',
        options: ['AC (Achats)', 'VE (Ventes)', 'BQ (Banque)', 'OD (Opérations Diverses)'],
        correctAnswer: 1,
        explanation: 'Les ventes sont enregistrées dans le journal VE (Ventes).',
        points: 15,
        difficulty: 'facile',
      },
      {
        id: 'compta-2',
        question: 'Que signifie une écriture équilibrée ?',
        options: ['Débit > Crédit', 'Débit < Crédit', 'Débit = Crédit', 'Pas de relation'],
        correctAnswer: 2,
        explanation: 'En partie double, chaque écriture doit avoir Total Débit = Total Crédit.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'compta-3',
        question: 'Quel compte représente les clients ?',
        options: ['401', '411', '512', '707'],
        correctAnswer: 1,
        explanation: 'Le compte 411 enregistre les créances clients.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'compta-4',
        question: 'Quel compte représente la banque ?',
        options: ['401', '411', '512', '707'],
        correctAnswer: 2,
        explanation: 'Le compte 512 représente les comptes bancaires.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'compta-5',
        question: "Qu'est-ce que le lettrage ?",
        options: ['Classement alphabétique', 'Rapprochement facture/paiement', 'Numérotation', 'Archivage'],
        correctAnswer: 1,
        explanation: 'Le lettrage associe une facture à son paiement pour suivre les soldes.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'compta-6',
        question: 'Quel est le taux de TVA standard en France ?',
        options: ['5.5%', '10%', '20%', '25%'],
        correctAnswer: 2,
        explanation: 'Le taux normal de TVA en France est 20%.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'compta-7',
        question: "Qu'est-ce que la TVA déductible ?",
        options: ['TVA à payer', 'TVA récupérable sur achats', 'TVA exonérée', 'Remboursement TVA'],
        correctAnswer: 1,
        explanation: "La TVA déductible est payée sur les achats et récupérable auprès de l'État.",
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'compta-8',
        question: 'Comment effectuer un rapprochement bancaire ?',
        options: ['Manuellement dans Excel', 'Comptabilité > Banque > Rapprochement', 'Export uniquement', 'Support technique'],
        correctAnswer: 1,
        explanation: 'Le module de rapprochement compare les écritures au relevé bancaire.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'compta-9',
        question: 'Quel compte pour les ventes de services ?',
        options: ['706', '707', '708', '709'],
        correctAnswer: 0,
        explanation: 'Le compte 706 "Prestations de services" enregistre les ventes de services.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'compta-10',
        question: "Qu'est-ce qu'une immobilisation ?",
        options: ['Stock bloqué', 'Bien durable amorti sur plusieurs années', 'Trésorerie bloquée', 'Facture impayée'],
        correctAnswer: 1,
        explanation: "Une immobilisation est un actif durable (matériel, véhicule) amorti sur sa durée d'utilisation.",
        points: 20,
        difficulty: 'difficile',
      },
    ],
  },

  // ============================================================================
  // STOCKS
  // ============================================================================
  {
    id: 'quiz-stocks',
    title: 'Gestion des Stocks',
    description: 'Optimisez votre gestion des stocks',
    category: 'Operations',
    icon: '📦',
    color: 'orange',
    duration: 8,
    difficulty: 'moyen',
    xpReward: 50,
    questions: [
      {
        id: 'stock-1',
        question: "Quel document valide une entrée en stock ?",
        options: ['Bon de commande', 'Bon de réception', 'Facture', 'Devis'],
        correctAnswer: 1,
        explanation: "Le bon de réception confirme l'entrée physique des marchandises.",
        points: 15,
        difficulty: 'facile',
      },
      {
        id: 'stock-2',
        question: 'Comment calculer le stock disponible ?',
        options: ['Stock physique', 'Stock physique - Réservés', 'Stock physique + Commandes', 'Stock moyen'],
        correctAnswer: 1,
        explanation: 'Stock disponible = Stock physique moins les quantités réservées.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'stock-3',
        question: "Qu'est-ce qu'un inventaire tournant ?",
        options: ['Inventaire annuel', 'Comptage régulier partiel', 'Rotation des produits', 'Inventaire automatique'],
        correctAnswer: 1,
        explanation: "L'inventaire tournant compte régulièrement une partie du stock.",
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'stock-4',
        question: "Comment traiter un écart d'inventaire ?",
        options: ['Ignorer', 'Ajustement de stock documenté', "Modifier l'historique", 'Supprimer les mouvements'],
        correctAnswer: 1,
        explanation: 'Les écarts se régularisent par ajustement avec justificatif.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'stock-5',
        question: "Qu'est-ce que le seuil de réapprovisionnement ?",
        options: ['Stock maximum', 'Niveau déclenchant commande', 'Prix minimum', 'Délai livraison'],
        correctAnswer: 1,
        explanation: 'Sous ce seuil, une alerte ou commande auto est déclenchée.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'stock-6',
        question: 'Comment activer le suivi par lot ?',
        options: ['Paramètres globaux', 'Fiche produit > Traçabilité', 'Impossible', 'Module externe'],
        correctAnswer: 1,
        explanation: "La traçabilité lot/série s'active sur chaque fiche produit.",
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'stock-7',
        question: 'Peut-on gérer plusieurs entrepôts ?',
        options: ['Non', 'Oui, dans Paramètres > Entrepôts', 'Forfait Premium', 'Module séparé'],
        correctAnswer: 1,
        explanation: 'AZALSCORE supporte plusieurs entrepôts avec transferts inter-sites.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'stock-8',
        question: "Comment visualiser les mouvements d'un article ?",
        options: ['Export manuel', 'Fiche article > Mouvements', 'Module Rapports', 'Audit uniquement'],
        correctAnswer: 1,
        explanation: "L'onglet Mouvements de la fiche montre tout l'historique.",
        points: 10,
        difficulty: 'facile',
      },
    ],
  },

  // ============================================================================
  // ASSISTANT IA
  // ============================================================================
  {
    id: 'quiz-ia',
    title: 'Theo & Marceau - Assistants IA',
    description: "Exploitez la puissance de l'IA",
    category: 'Intelligence',
    icon: '🤖',
    color: 'purple',
    duration: 6,
    difficulty: 'moyen',
    xpReward: 40,
    questions: [
      {
        id: 'ia-1',
        question: 'Qui est Theo ?',
        options: ['Agent autonome', 'Assistant conversationnel', 'Module de reporting', 'Administrateur'],
        correctAnswer: 1,
        explanation: "Theo est l'assistant IA conversationnel qui répond à vos questions.",
        points: 15,
        difficulty: 'facile',
      },
      {
        id: 'ia-2',
        question: 'Qui est Marceau ?',
        options: ['Assistant vocal', 'Agent IA exécutant des tâches', 'Module comptable', 'Support technique'],
        correctAnswer: 1,
        explanation: "Marceau est l'agent IA autonome qui exécute des tâches complexes.",
        points: 15,
        difficulty: 'facile',
      },
      {
        id: 'ia-3',
        question: 'Que peut faire Theo ?',
        options: ['Modifier la base', "Répondre à des questions sur AZALSCORE", 'Valider des factures', 'Gérer les utilisateurs'],
        correctAnswer: 1,
        explanation: 'Theo aide et répond aux questions, mais ne modifie pas les données.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'ia-4',
        question: 'Comment demander à Marceau de créer un devis ?',
        options: ['Email', 'Chat avec description du besoin', 'Formulaire dédié', 'Impossible'],
        correctAnswer: 1,
        explanation: 'Décrivez votre besoin dans le chat Marceau, il créera le devis.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'ia-5',
        question: 'Les actions de Marceau sont-elles automatiques ?',
        options: ['Toujours', 'Jamais', 'Validation humaine requise', 'Selon configuration'],
        correctAnswer: 3,
        explanation: 'Selon la configuration, certaines actions requièrent une validation.',
        points: 20,
        difficulty: 'moyen',
      },
      {
        id: 'ia-6',
        question: "Où consulter l'historique des actions Marceau ?",
        options: ['Non disponible', 'Dashboard Marceau', 'Logs système', 'Email uniquement'],
        correctAnswer: 1,
        explanation: 'Le dashboard Marceau affiche toutes les actions avec leur statut.',
        points: 15,
        difficulty: 'moyen',
      },
    ],
  },

  // ============================================================================
  // ADMINISTRATION
  // ============================================================================
  {
    id: 'quiz-admin',
    title: 'Administration & Sécurité',
    description: 'Gérez les utilisateurs et la sécurité',
    category: 'Administration',
    icon: '⚙️',
    color: 'red',
    duration: 10,
    difficulty: 'difficile',
    xpReward: 70,
    questions: [
      {
        id: 'admin-1',
        question: 'Où gérer les utilisateurs ?',
        options: ['CRM', 'Paramètres > Utilisateurs', 'Module RH', 'Support technique'],
        correctAnswer: 1,
        explanation: 'La gestion des utilisateurs se fait dans Paramètres > Utilisateurs.',
        points: 10,
        difficulty: 'facile',
      },
      {
        id: 'admin-2',
        question: 'Comment créer un rôle personnalisé ?',
        options: ['Copier un existant', 'Paramètres > Rôles > Nouveau', 'Impossible', 'Support uniquement'],
        correctAnswer: 1,
        explanation: 'Les rôles personnalisés permettent des permissions sur mesure.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'admin-3',
        question: "Qu'est-ce que le 2FA ?",
        options: ['Format fichier', 'Double authentification', 'Sauvegarde', 'Type de rapport'],
        correctAnswer: 1,
        explanation: "Le 2FA (authentification à deux facteurs) renforce la sécurité.",
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'admin-4',
        question: 'Comment activer le 2FA ?',
        options: ['Automatique', 'Profil > Sécurité > 2FA', 'Admin uniquement', 'Forfait Premium'],
        correctAnswer: 1,
        explanation: 'Chaque utilisateur peut activer le 2FA dans son profil.',
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'admin-5',
        question: "Où consulter le journal d'audit ?",
        options: ['Rapports', 'Paramètres > Audit > Journal', 'Non disponible', 'Base de données'],
        correctAnswer: 1,
        explanation: "Le journal d'audit trace toutes les actions des utilisateurs.",
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'admin-6',
        question: "Combien de temps sont conservés les logs d'audit ?",
        options: ['30 jours', '1 an', '5 ans', '7 ans'],
        correctAnswer: 3,
        explanation: 'Les logs sont conservés 7 ans pour conformité légale.',
        points: 20,
        difficulty: 'difficile',
      },
      {
        id: 'admin-7',
        question: 'Comment configurer le SSO ?',
        options: ['Plugin externe', 'Paramètres > Sécurité > SSO', 'Non supporté', 'Développement custom'],
        correctAnswer: 1,
        explanation: 'Le SSO (SAML/OAuth) se configure dans les paramètres de sécurité.',
        points: 25,
        difficulty: 'difficile',
      },
      {
        id: 'admin-8',
        question: 'Comment sauvegarder les données ?',
        options: ['Manuel uniquement', 'Automatique quotidien + export', 'Non disponible', 'Cloud uniquement'],
        correctAnswer: 1,
        explanation: "Sauvegardes automatiques quotidiennes + possibilité d'export manuel.",
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'admin-9',
        question: 'Comment désactiver un utilisateur sans supprimer ?',
        options: ['Impossible', 'Utilisateur > Désactiver', 'Changer mot de passe', 'Retirer tous les rôles'],
        correctAnswer: 1,
        explanation: "La désactivation bloque l'accès tout en conservant l'historique.",
        points: 15,
        difficulty: 'moyen',
      },
      {
        id: 'admin-10',
        question: 'Quelle certification sécurité possède AZALSCORE ?',
        options: ['Aucune', 'ISO 27001', 'SOC 2 uniquement', 'PCI-DSS'],
        correctAnswer: 1,
        explanation: "AZALSCORE est certifié ISO 27001 pour la sécurité de l'information.",
        points: 20,
        difficulty: 'difficile',
      },
    ],
  },
];

// ============================================================================
// UTILITAIRES
// ============================================================================

/**
 * Obtient un quiz par son ID
 */
export function getQuizById(id: string): PracticeQuiz | undefined {
  return PRACTICE_QUIZZES.find(q => q.id === id);
}

/**
 * Obtient les quiz par catégorie
 */
export function getQuizzesByCategory(category: string): PracticeQuiz[] {
  if (category === 'all') return PRACTICE_QUIZZES;
  return PRACTICE_QUIZZES.filter(q => q.category === category);
}

/**
 * Obtient toutes les catégories de quiz
 */
export function getQuizCategories(): string[] {
  return ['all', ...new Set(PRACTICE_QUIZZES.map(q => q.category))];
}

/**
 * Calcule le nombre total de questions
 */
export function getTotalQuestionsCount(): number {
  return PRACTICE_QUIZZES.reduce((sum, q) => sum + q.questions.length, 0);
}
