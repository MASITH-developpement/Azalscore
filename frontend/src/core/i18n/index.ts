/**
 * AZALSCORE - Système d'internationalisation (i18n)
 * ================================================
 *
 * Système léger de traduction sans dépendance externe.
 * Langue par défaut : français (fr)
 *
 * Usage:
 *   const { t } = useTranslation();
 *   t('documents.types.quote') → "Devis"
 */

import { create } from 'zustand';

// ============================================================
// TYPES
// ============================================================

type TranslationKey = string;
type TranslationValue = string | Record<string, unknown>;
type Translations = Record<string, TranslationValue>;
type Language = 'fr' | 'en';

interface I18nState {
  language: Language;
  translations: Record<Language, Translations>;
  setLanguage: (lang: Language) => void;
}

// ============================================================
// TRADUCTIONS FRANÇAISES
// ============================================================

const frenchTranslations: Translations = {
  // === COMMUN ===
  'common.loading': 'Chargement...',
  'common.save': 'Enregistrer',
  'common.cancel': 'Annuler',
  'common.delete': 'Supprimer',
  'common.edit': 'Modifier',
  'common.create': 'Créer',
  'common.view': 'Voir',
  'common.back': 'Retour',
  'common.search': 'Rechercher',
  'common.filter': 'Filtrer',
  'common.filters': 'Filtres',
  'common.export': 'Exporter',
  'common.refresh': 'Actualiser',
  'common.confirm': 'Confirmer',
  'common.yes': 'Oui',
  'common.no': 'Non',
  'common.all': 'Tous',
  'common.none': 'Aucun',
  'common.actions': 'Actions',
  'common.status': 'Statut',
  'common.date': 'Date',
  'common.amount': 'Montant',
  'common.total': 'Total',
  'common.notes': 'Notes',
  'common.required': 'Requis',
  'common.optional': 'Optionnel',
  'common.reset': 'Réinitialiser',
  'common.clear': 'Effacer',
  'common.close': 'Fermer',
  'common.add': 'Ajouter',
  'common.remove': 'Retirer',
  'common.validate': 'Valider',
  'common.validated': 'Validé',
  'common.draft': 'Brouillon',
  'common.pending': 'En attente',
  'common.error': 'Erreur',
  'common.success': 'Succès',
  'common.warning': 'Attention',
  'common.info': 'Information',

  // === DOCUMENTS - Module principal ===
  'documents.title': 'Documents',
  'documents.subtitle': 'Gestion des documents commerciaux',
  'documents.newDocument': 'Nouveau document',
  'documents.selectType': 'Sélectionner un type',
  'documents.noDocuments': 'Aucun document',
  'documents.searchPlaceholder': 'Rechercher par numéro ou partenaire...',

  // === DOCUMENTS - Types ===
  'documents.types.quote': 'Devis',
  'documents.types.quotes': 'Devis',
  'documents.types.invoice': 'Facture',
  'documents.types.invoices': 'Factures',
  'documents.types.creditNote': 'Avoir',
  'documents.types.creditNotes': 'Avoirs',
  'documents.types.purchaseOrder': 'Commande fournisseur',
  'documents.types.purchaseOrders': 'Commandes fournisseurs',
  'documents.types.purchaseInvoice': 'Facture fournisseur',
  'documents.types.purchaseInvoices': 'Factures fournisseurs',

  // === DOCUMENTS - Catégories ===
  'documents.categories.sales': 'Ventes',
  'documents.categories.purchases': 'Achats',

  // === DOCUMENTS - Statuts ===
  'documents.status.draft': 'Brouillon',
  'documents.status.validated': 'Validé',
  'documents.status.sent': 'Envoyé',
  'documents.status.confirmed': 'Confirmé',
  'documents.status.partial': 'Partiel',
  'documents.status.received': 'Reçu',
  'documents.status.invoiced': 'Facturé',
  'documents.status.paid': 'Payé',
  'documents.status.cancelled': 'Annulé',

  // === DOCUMENTS - Formulaire ===
  'documents.form.generalInfo': 'Informations générales',
  'documents.form.partner': 'Partenaire',
  'documents.form.customer': 'Client',
  'documents.form.supplier': 'Fournisseur',
  'documents.form.selectCustomer': 'Sélectionner un client',
  'documents.form.selectSupplier': 'Sélectionner un fournisseur',
  'documents.form.date': 'Date',
  'documents.form.dueDate': 'Date d\'échéance',
  'documents.form.validityDate': 'Date de validité',
  'documents.form.expectedDate': 'Date de livraison prévue',
  'documents.form.reference': 'Référence',
  'documents.form.supplierReference': 'Référence fournisseur',
  'documents.form.notes': 'Notes',
  'documents.form.internalNotes': 'Notes internes',

  // === DOCUMENTS - Lignes ===
  'documents.lines.title': 'Lignes du document',
  'documents.lines.addLine': 'Ajouter une ligne',
  'documents.lines.noLines': 'Aucune ligne',
  'documents.lines.clickToAdd': 'Cliquez sur "Ajouter une ligne" pour commencer.',
  'documents.lines.description': 'Description',
  'documents.lines.quantity': 'Qté',
  'documents.lines.unitPrice': 'Prix unit. HT',
  'documents.lines.discount': 'Remise',
  'documents.lines.tax': 'TVA',
  'documents.lines.totalHT': 'Total HT',
  'documents.lines.totalTVA': 'Total TVA',
  'documents.lines.totalTTC': 'Total TTC',
  'documents.lines.clickToEdit': 'Cliquez pour éditer',

  // === DOCUMENTS - Actions ===
  'documents.actions.create': 'Créer le document',
  'documents.actions.save': 'Enregistrer',
  'documents.actions.validate': 'Valider',
  'documents.actions.send': 'Envoyer',
  'documents.actions.convert': 'Convertir',
  'documents.actions.convertToInvoice': 'Convertir en facture',
  'documents.actions.createInvoice': 'Créer une facture',
  'documents.actions.delete': 'Supprimer',
  'documents.actions.duplicate': 'Dupliquer',
  'documents.actions.print': 'Imprimer',
  'documents.actions.download': 'Télécharger',
  'documents.actions.exportCSV': 'Export CSV',

  // === DOCUMENTS - Messages ===
  'documents.messages.confirmDelete': 'Êtes-vous sûr de vouloir supprimer ce document ?',
  'documents.messages.confirmValidate': 'Voulez-vous valider ce document ?',
  'documents.messages.validateWarning': 'Un document validé ne peut plus être modifié.',
  'documents.messages.convertConfirm': 'Créer une facture à partir de ce document ?',
  'documents.messages.convertInfo': 'Une nouvelle facture sera créée avec les mêmes lignes.',
  'documents.messages.notFound': 'Document non trouvé',
  'documents.messages.notFoundDesc': 'Le document demandé n\'existe pas ou a été supprimé.',
  'documents.messages.cannotEdit': 'Ce document ne peut plus être modifié.',
  'documents.messages.alreadyValidated': 'Ce document a déjà été validé.',
  'documents.messages.created': 'Document créé avec succès',
  'documents.messages.updated': 'Document mis à jour avec succès',
  'documents.messages.deleted': 'Document supprimé avec succès',
  'documents.messages.validated': 'Document validé avec succès',

  // === DOCUMENTS - Erreurs de validation ===
  'documents.errors.selectPartner': 'Veuillez sélectionner un partenaire',
  'documents.errors.selectCustomer': 'Veuillez sélectionner un client',
  'documents.errors.selectSupplier': 'Veuillez sélectionner un fournisseur',
  'documents.errors.dateRequired': 'La date est requise',
  'documents.errors.addLine': 'Ajoutez au moins une ligne',
  'documents.errors.lineDescription': 'Toutes les lignes doivent avoir une description',

  // === PARTENAIRES ===
  'partners.title': 'Partenaires',
  'partners.customers': 'Clients',
  'partners.suppliers': 'Fournisseurs',
  'partners.contacts': 'Contacts',
  'partners.newCustomer': 'Nouveau client',
  'partners.newSupplier': 'Nouveau fournisseur',
  'partners.searchPlaceholder': 'Rechercher un partenaire...',
  'partners.noPartners': 'Aucun partenaire',

  // === PARTENAIRES - Champs ===
  'partners.fields.code': 'Code',
  'partners.fields.name': 'Nom',
  'partners.fields.contact': 'Contact',
  'partners.fields.email': 'Email',
  'partners.fields.phone': 'Téléphone',
  'partners.fields.address': 'Adresse',
  'partners.fields.postalCode': 'Code postal',
  'partners.fields.city': 'Ville',
  'partners.fields.country': 'Pays',
  'partners.fields.taxId': 'N° TVA / SIRET',
  'partners.fields.paymentTerms': 'Conditions de paiement',
  'partners.fields.notes': 'Notes',

  // === PARTENAIRES - Statuts ===
  'partners.status.prospect': 'Prospect',
  'partners.status.pending': 'En attente',
  'partners.status.approved': 'Approuvé',
  'partners.status.active': 'Actif',
  'partners.status.blocked': 'Bloqué',
  'partners.status.inactive': 'Inactif',

  // === PARTENAIRES - Conditions de paiement ===
  'partners.paymentTerms.immediate': 'Paiement immédiat',
  'partners.paymentTerms.net15': 'Net 15 jours',
  'partners.paymentTerms.net30': 'Net 30 jours',
  'partners.paymentTerms.net45': 'Net 45 jours',
  'partners.paymentTerms.net60': 'Net 60 jours',
  'partners.paymentTerms.eom': 'Fin de mois',
  'partners.paymentTerms.eom30': 'Fin de mois + 30',

  // === TABLEAU ===
  'table.noData': 'Aucune donnée',
  'table.loading': 'Chargement...',
  'table.page': 'Page',
  'table.of': 'sur',
  'table.rowsPerPage': 'Lignes par page',
  'table.showing': 'Affichage de',
  'table.to': 'à',
  'table.entries': 'entrées',

  // === FILTRES ===
  'filters.status': 'Statut',
  'filters.allStatuses': 'Tous les statuts',
  'filters.dateFrom': 'Date du',
  'filters.dateTo': 'Date au',
  'filters.partner': 'Partenaire',
  'filters.allPartners': 'Tous les partenaires',
  'filters.customer': 'Client',
  'filters.allCustomers': 'Tous les clients',
  'filters.supplier': 'Fournisseur',
  'filters.allSuppliers': 'Tous les fournisseurs',
  'filters.reset': 'Réinitialiser les filtres',

  // === TVA ===
  'tax.rate0': '0%',
  'tax.rate5_5': '5,5%',
  'tax.rate10': '10%',
  'tax.rate20': '20%',

  // === NAVIGATION ===
  'nav.dashboard': 'Tableau de bord',
  'nav.documents': 'Documents',
  'nav.partners': 'Partenaires',
  'nav.sales': 'Ventes',
  'nav.purchases': 'Achats',
  'nav.settings': 'Paramètres',
};

// ============================================================
// TRADUCTIONS ANGLAISES (optionnel, pour le futur)
// ============================================================

const englishTranslations: Translations = {
  'common.loading': 'Loading...',
  'common.save': 'Save',
  'common.cancel': 'Cancel',
  // ... (à compléter si nécessaire)
};

// ============================================================
// STORE I18N
// ============================================================

export const useI18nStore = create<I18nState>((set) => ({
  language: 'fr',
  translations: {
    fr: frenchTranslations,
    en: englishTranslations,
  },
  setLanguage: (lang) => set({ language: lang }),
}));

// ============================================================
// HOOK useTranslation
// ============================================================

interface UseTranslationReturn {
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
  language: Language;
  setLanguage: (lang: Language) => void;
}

export const useTranslation = (): UseTranslationReturn => {
  const { language, translations, setLanguage } = useI18nStore();

  const t = (key: TranslationKey, params?: Record<string, string | number>): string => {
    const currentTranslations = translations[language] || translations.fr;
    let value = currentTranslations[key];

    if (typeof value !== 'string') {
      // Clé non trouvée, retourner la clé elle-même (pour debug)
      console.warn(`[i18n] Missing translation for key: ${key}`);
      return key;
    }

    // Remplacer les paramètres {{param}}
    if (params) {
      Object.entries(params).forEach(([paramKey, paramValue]) => {
        value = (value as string).replace(new RegExp(`{{${paramKey}}}`, 'g'), String(paramValue));
      });
    }

    return value as string;
  };

  return { t, language, setLanguage };
};

// ============================================================
// EXPORT PAR DÉFAUT
// ============================================================

export default useTranslation;
