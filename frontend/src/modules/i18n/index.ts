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

    // Interventions
    'intervention.status.pending': 'À planifier',
    'intervention.status.planned': 'Planifiée',
    'intervention.status.inProgress': 'En cours',
    'intervention.status.completed': 'Terminée',

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
