/**
 * AZALSCORE - Système i18n
 * =========================
 *
 * Toutes les clés de traduction.
 * Français = langue source.
 * Aucune chaîne en dur dans les composants.
 */

import { useCallback } from 'react';

// ============================================================
// TRADUCTIONS FRANÇAISES (SOURCE)
// ============================================================

const translations: Record<string, Record<string, string>> = {
  fr: {
    // Worksheet - Types de document
    'worksheet.type.quote': 'Devis',
    'worksheet.type.invoice': 'Facture',
    'worksheet.type.order': 'Commande',
    'worksheet.type.intervention': 'Intervention',

    // Worksheet - Client
    'worksheet.selectClient': 'Sélectionner un client',
    'worksheet.searchClient': 'Rechercher un client...',
    'worksheet.noClientFound': 'Aucun client trouvé',
    'worksheet.taxId': 'N° TVA',

    // Worksheet - Lignes
    'worksheet.description': 'Description',
    'worksheet.qty': 'Qté',
    'worksheet.unitPrice': 'Prix unit. HT',
    'worksheet.tax': 'TVA',
    'worksheet.total': 'Total TTC',
    'worksheet.addLine': 'Ajouter une ligne',
    'worksheet.removeLine': 'Supprimer la ligne',
    'worksheet.descriptionPlaceholder': 'Description du produit ou service',

    // Worksheet - Totaux
    'worksheet.subtotal': 'Total HT',
    'worksheet.taxTotal': 'TVA',

    // Worksheet - Notes
    'worksheet.notesPlaceholder': 'Notes (optionnel)',

    // Worksheet - Actions
    'worksheet.save.quote': 'Enregistrer le devis',
    'worksheet.save.invoice': 'Enregistrer la facture',
    'worksheet.save.order': 'Enregistrer la commande',
    'worksheet.save.intervention': 'Créer l\'intervention',
    'worksheet.saved': 'Enregistré',
    'worksheet.loading': 'Chargement...',

    // Worksheet - Erreurs
    'worksheet.error.noClient': 'Veuillez sélectionner un client',
    'worksheet.error.noLines': 'Ajoutez au moins une ligne',
    'worksheet.error.save': 'Erreur lors de l\'enregistrement',

    // Navigation
    'nav.worksheet': 'Saisie',
    'nav.history': 'Historique',
    'nav.logout': 'Déconnexion',

    // Commun
    'common.cancel': 'Annuler',
    'common.confirm': 'Confirmer',
    'common.delete': 'Supprimer',
    'common.edit': 'Modifier',
    'common.save': 'Enregistrer',
    'common.search': 'Rechercher',
    'common.loading': 'Chargement...',
    'common.error': 'Erreur',
    'common.success': 'Succès',
    'common.yes': 'Oui',
    'common.no': 'Non',

    // Formats
    'format.currency': '€',
    'format.date': 'dd/MM/yyyy',

    // États documents
    'status.draft': 'Brouillon',
    'status.validated': 'Validé',
    'status.sent': 'Envoyé',
    'status.paid': 'Payé',
    'status.cancelled': 'Annulé',

    // Interventions - Statuts
    'intervention.status.pending': 'À planifier',
    'intervention.status.planned': 'Planifiée',
    'intervention.status.inProgress': 'En cours',
    'intervention.status.completed': 'Terminée',
    'intervention.status.cancelled': 'Annulée',

    // Interventions - Types
    'intervention.type.installation': 'Installation',
    'intervention.type.maintenance': 'Maintenance',
    'intervention.type.reparation': 'Réparation',
    'intervention.type.inspection': 'Inspection',
    'intervention.type.formation': 'Formation',
    'intervention.type.consultation': 'Consultation',
    'intervention.type.autre': 'Autre',

    // Interventions - Priorités
    'intervention.priority.low': 'Basse',
    'intervention.priority.normal': 'Normale',
    'intervention.priority.high': 'Haute',
    'intervention.priority.urgent': 'Urgente',

    // Interventions - Corps d'état
    'intervention.trade.electricite': 'Électricité',
    'intervention.trade.plomberie': 'Plomberie',
    'intervention.trade.electricite_plomberie': 'Électricité + Plomberie',

    // Interventions - Module UI
    'intervention.title': 'Interventions',
    'intervention.subtitle': 'Gestion des interventions terrain',
    'intervention.tab.dashboard': 'Vue d\'ensemble',
    'intervention.tab.list': 'Interventions',
    'intervention.tab.planning': 'Planning',
    'intervention.tab.donneurs': 'Donneurs d\'ordre',
    'intervention.new': 'Nouvelle intervention',
    'intervention.detail': 'Détail',
    'intervention.planifier': 'Planifier',
    'intervention.demarrer': 'Démarrer',
    'intervention.terminer': 'Terminer',
    'intervention.annuler': 'Annuler',
    'intervention.filter.allStatuts': 'Tous statuts',
    'intervention.filter.allTypes': 'Tous types',
    'intervention.filter.allPriorities': 'Toutes priorités',
    'intervention.planifier.title': 'Planifier l\'intervention',
    'intervention.planifier.date': 'Date',
    'intervention.planifier.heureDebut': 'Heure début',
    'intervention.planifier.heureFin': 'Heure fin',
    'intervention.planifier.intervenant': 'Intervenant',
    'intervention.planifier.selectIntervenant': 'Choisir un intervenant...',
    'intervention.planifier.submit': 'Planifier',
    'intervention.planifier.submitting': 'Planification...',
    'intervention.planifier.errorIntervenant': 'Veuillez sélectionner un intervenant',
    'intervention.annuler.title': 'Confirmer l\'annulation',
    'intervention.annuler.confirm': 'Êtes-vous sûr de vouloir annuler l\'intervention {reference} ?',
    'intervention.annuler.irreversible': 'Cette action est irréversible.',
    'intervention.annuler.keep': 'Non, garder',
    'intervention.annuler.confirmBtn': 'Oui, annuler',
    'intervention.annuler.submitting': 'Annulation...',
    'intervention.stats.aPlanifier': 'À planifier',
    'intervention.stats.planifiees': 'Planifiées',
    'intervention.stats.enCours': 'En cours',
    'intervention.stats.termineesSemaine': 'Terminées (semaine)',
    'intervention.stats.termineesMois': 'Terminées (mois)',
    'intervention.stats.dureeMoyenne': 'Durée moyenne',
    'intervention.stats.aujourdhui': 'Aujourd\'hui',
    'intervention.stats.loading': 'Chargement des statistiques...',
    'intervention.stats.error': 'Impossible de charger les statistiques',

    // Interventions - Donneurs d'ordre
    'intervention.donneurs.title': 'Donneurs d\'ordre',
    'intervention.donneurs.new': 'Nouveau donneur d\'ordre',
    'intervention.donneurs.create': 'Créer',
    'intervention.donneurs.creating': 'Création...',
    'intervention.donneurs.errorNom': 'Le nom est obligatoire',
    'intervention.donneurs.errorCode': 'Le code est obligatoire',

    // Profil utilisateur
    'user.profile': 'Mon profil',
    'user.settings': 'Paramètres',
    'user.logout': 'Déconnexion',
  },
};

// ============================================================
// HOOK DE TRADUCTION
// ============================================================

let currentLocale = 'fr';

export const setLocale = (locale: string) => {
  if (translations[locale]) {
    currentLocale = locale;
  }
};

export const getLocale = () => currentLocale;

export const useTranslation = () => {
  const t = useCallback((key: string, params?: Record<string, string | number>): string => {
    const translation = translations[currentLocale]?.[key] || translations['fr']?.[key] || key;

    if (!params) return translation;

    // Remplacement des paramètres {param}
    return Object.entries(params).reduce(
      (str, [k, v]) => str.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v)),
      translation
    );
  }, []);

  return { t, locale: currentLocale, setLocale };
};

// ============================================================
// EXPORT DIRECT POUR USAGE HORS COMPOSANTS
// ============================================================

export const t = (key: string, params?: Record<string, string | number>): string => {
  const translation = translations[currentLocale]?.[key] || translations['fr']?.[key] || key;

  if (!params) return translation;

  return Object.entries(params).reduce(
    (str, [k, v]) => str.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v)),
    translation
  );
};

export default { useTranslation, t, setLocale, getLocale };
