/**
 * AZALSCORE Module - Onboarding - Constants
 * Tours predefinies et configurations
 */

import type { OnboardingTour } from './types';

// ============================================================================
// TOURS PREDEFINIES
// ============================================================================

export const ONBOARDING_TOURS: OnboardingTour[] = [
  {
    id: 'welcome',
    name: 'Bienvenue sur AZALSCORE',
    description: 'Decouvrez les bases de votre nouvel ERP',
    duration: '5 min',
    level: 'debutant',
    steps: [
      {
        id: 'welcome-1',
        title: 'Bienvenue sur AZALSCORE !',
        description: 'Felicitations pour votre premiere connexion. Ce guide rapide va vous presenter les fonctionnalites essentielles de votre nouvel ERP.',
        position: 'center',
      },
      {
        id: 'welcome-2',
        title: 'La barre de recherche',
        description: 'Appuyez sur "/" pour rechercher instantanement clients, documents ou produits. Utilisez @ pour les clients, # pour les documents.',
        target: '[data-tour="search-bar"]',
        position: 'bottom',
      },
      {
        id: 'welcome-3',
        title: 'Le menu principal',
        description: 'Accedez a tous les modules depuis ce menu. Les sections sont organisees par domaine : Gestion, Finance, Operations...',
        target: '[data-tour="main-menu"]',
        position: 'right',
      },
      {
        id: 'welcome-4',
        title: 'Vos notifications',
        description: 'La cloche vous alerte des evenements importants : nouveaux messages, validations en attente, alertes systeme.',
        target: '[data-tour="notifications"]',
        position: 'bottom',
      },
      {
        id: 'welcome-5',
        title: 'Votre assistant Theo',
        description: 'Cliquez ici pour parler a Theo, votre assistant IA. Il peut repondre a vos questions et effectuer des actions pour vous.',
        target: '[data-tour="theo-button"]',
        position: 'top',
      },
      {
        id: 'welcome-6',
        title: 'Vous etes pret !',
        description: 'Explorez AZALSCORE a votre rythme. D\'autres formations sont disponibles dans le Centre d\'aide. Bonne decouverte !',
        position: 'center',
      },
    ],
  },
  {
    id: 'crm-basics',
    name: 'Gestion des Clients',
    description: 'Apprenez a gerer vos clients dans le CRM',
    module: 'crm',
    duration: '8 min',
    level: 'debutant',
    steps: [
      {
        id: 'crm-1',
        title: 'Le module CRM',
        description: 'Bienvenue dans le CRM AZALSCORE. C\'est ici que vous gerez toutes les informations de vos clients et prospects.',
        position: 'center',
      },
      {
        id: 'crm-2',
        title: 'Liste des clients',
        description: 'Tous vos clients apparaissent ici. Utilisez les filtres pour trouver rapidement ce que vous cherchez.',
        target: '[data-tour="client-list"]',
        position: 'top',
      },
      {
        id: 'crm-3',
        title: 'Creer un client',
        description: 'Cliquez sur ce bouton pour ajouter un nouveau client. Les champs obligatoires sont marques d\'un asterisque.',
        target: '[data-tour="new-client-btn"]',
        position: 'left',
      },
      {
        id: 'crm-4',
        title: 'Fiche client',
        description: 'Chaque client a sa fiche detaillee avec onglets : informations, documents, historique, notes.',
        target: '[data-tour="client-card"]',
        position: 'right',
      },
      {
        id: 'crm-5',
        title: 'Recherche rapide',
        description: 'Tapez @NomClient dans la recherche globale pour trouver instantanement un client.',
        target: '[data-tour="search-bar"]',
        position: 'bottom',
      },
    ],
  },
  {
    id: 'invoicing-basics',
    name: 'Devis et Factures',
    description: 'Creez et gerez vos documents commerciaux',
    module: 'invoicing',
    duration: '10 min',
    level: 'debutant',
    steps: [
      {
        id: 'inv-1',
        title: 'La facturation dans AZALSCORE',
        description: 'Ce module gere tout le cycle commercial : devis, commandes, factures, avoirs.',
        position: 'center',
      },
      {
        id: 'inv-2',
        title: 'Creer un devis',
        description: 'Cliquez ici pour creer un nouveau devis. Selectionnez le client, ajoutez les lignes, et c\'est pret !',
        target: '[data-tour="new-quote-btn"]',
        position: 'left',
      },
      {
        id: 'inv-3',
        title: 'Ajouter des lignes',
        description: 'Chaque ligne correspond a un produit ou service. Le prix et la TVA se calculent automatiquement.',
        target: '[data-tour="quote-lines"]',
        position: 'top',
      },
      {
        id: 'inv-4',
        title: 'Envoyer le devis',
        description: 'Une fois pret, envoyez le devis par email directement depuis AZALSCORE.',
        target: '[data-tour="send-btn"]',
        position: 'bottom',
      },
      {
        id: 'inv-5',
        title: 'Convertir en facture',
        description: 'Quand le client accepte, convertissez le devis en commande puis en facture en quelques clics.',
        target: '[data-tour="convert-btn"]',
        position: 'left',
      },
    ],
  },
  {
    id: 'cockpit-tour',
    name: 'Tableau de Bord',
    description: 'Maitrisez le Cockpit dirigeant',
    module: 'cockpit',
    duration: '5 min',
    level: 'intermediaire',
    steps: [
      {
        id: 'cockpit-1',
        title: 'Le Cockpit Dirigeant',
        description: 'Vue d\'ensemble de votre activite en temps reel. Tous les indicateurs cles sont ici.',
        position: 'center',
      },
      {
        id: 'cockpit-2',
        title: 'Indicateurs cles',
        description: 'CA, pipeline, tresorerie, tendances... Cliquez sur un chiffre pour voir le detail.',
        target: '[data-tour="kpi-cards"]',
        position: 'bottom',
      },
      {
        id: 'cockpit-3',
        title: 'Graphiques',
        description: 'Visualisez l\'evolution de vos performances. Survolez pour les details.',
        target: '[data-tour="charts"]',
        position: 'top',
      },
      {
        id: 'cockpit-4',
        title: 'Personnalisation',
        description: 'Configurez votre tableau de bord selon vos besoins. Ajoutez, supprimez ou reorganisez les widgets.',
        target: '[data-tour="customize-btn"]',
        position: 'left',
      },
    ],
  },
];
