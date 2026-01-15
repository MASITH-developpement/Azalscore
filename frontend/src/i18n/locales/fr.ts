/**
 * AZALSCORE - Traductions françaises
 * Langue source du système
 * Structure hiérarchique par domaine
 */

const fr = {
  // ============================================================
  // COMMUN
  // ============================================================
  common: {
    loading: 'Chargement...',
    save: 'Enregistrer',
    cancel: 'Annuler',
    delete: 'Supprimer',
    edit: 'Modifier',
    view: 'Voir',
    add: 'Ajouter',
    create: 'Créer',
    close: 'Fermer',
    confirm: 'Confirmer',
    search: 'Rechercher',
    filter: 'Filtrer',
    export: 'Exporter',
    import: 'Importer',
    refresh: 'Actualiser',
    back: 'Retour',
    next: 'Suivant',
    previous: 'Précédent',
    yes: 'Oui',
    no: 'Non',
    all: 'Tous',
    none: 'Aucun',
    select: 'Sélectionner',
    required: 'Requis',
    optional: 'Optionnel',
    actions: 'Actions',
    details: 'Détails',
    status: 'Statut',
    date: 'Date',
    amount: 'Montant',
    total: 'Total',
    description: 'Description',
    notes: 'Notes',
    error: 'Erreur',
    success: 'Succès',
    warning: 'Attention',
    info: 'Information',
  },

  // ============================================================
  // STATUTS
  // ============================================================
  status: {
    active: 'Actif',
    inactive: 'Inactif',
    draft: 'Brouillon',
    validated: 'Validé',
    sent: 'Envoyé',
    confirmed: 'Confirmé',
    partial: 'Partiel',
    completed: 'Terminé',
    cancelled: 'Annulé',
    pending: 'En attente',
    paid: 'Payé',
    overdue: 'En retard',
    blocked: 'Bloqué',
    approved: 'Approuvé',
    prospect: 'Prospect',
  },

  // ============================================================
  // ENTITÉS
  // ============================================================
  entity: {
    client: 'Client',
    clients: 'Clients',
    supplier: 'Fournisseur',
    suppliers: 'Fournisseurs',
    contact: 'Contact',
    contacts: 'Contacts',
    partner: 'Partenaire',
    partners: 'Partenaires',
    product: 'Produit',
    products: 'Produits',
    service: 'Service',
    services: 'Services',
    document: 'Document',
    documents: 'Documents',
    quote: 'Devis',
    quotes: 'Devis',
    invoice: 'Facture',
    invoices: 'Factures',
    order: 'Commande',
    orders: 'Commandes',
    purchaseOrder: 'Commande fournisseur',
    purchaseInvoice: 'Facture fournisseur',
    user: 'Utilisateur',
    users: 'Utilisateurs',
    role: 'Rôle',
    roles: 'Rôles',
    intervention: 'Intervention',
    interventions: 'Interventions',
    project: 'Projet',
    projects: 'Projets',
    account: 'Compte',
    accounts: 'Comptes',
    transaction: 'Transaction',
    transactions: 'Transactions',
  },

  // ============================================================
  // CHAMPS FORMULAIRE
  // ============================================================
  field: {
    name: 'Nom',
    firstName: 'Prénom',
    lastName: 'Nom de famille',
    email: 'Email',
    phone: 'Téléphone',
    mobile: 'Mobile',
    address: 'Adresse',
    addressLine1: 'Adresse ligne 1',
    addressLine2: 'Adresse ligne 2',
    city: 'Ville',
    postalCode: 'Code postal',
    country: 'Pays',
    vatNumber: 'N° TVA',
    siret: 'SIRET',
    code: 'Code',
    reference: 'Référence',
    number: 'Numéro',
    quantity: 'Quantité',
    unitPrice: 'Prix unitaire',
    unitPriceHT: 'Prix unit. HT',
    discount: 'Remise',
    discountPercent: 'Remise %',
    taxRate: 'Taux TVA',
    subtotal: 'Sous-total',
    totalHT: 'Total HT',
    totalTVA: 'Total TVA',
    totalTTC: 'Total TTC',
    dueDate: 'Date d\'échéance',
    validityDate: 'Date de validité',
    deliveryDate: 'Date de livraison',
    expectedDate: 'Date prévue',
    paymentTerms: 'Conditions de paiement',
    jobTitle: 'Fonction',
    department: 'Service',
    company: 'Entreprise',
    type: 'Type',
    category: 'Catégorie',
    unit: 'Unité',
    bankName: 'Banque',
    iban: 'IBAN',
    bic: 'BIC',
    balance: 'Solde',
    currency: 'Devise',
  },

  // ============================================================
  // TYPES DE DOCUMENT
  // ============================================================
  documentType: {
    quote: 'Devis',
    invoice: 'Facture',
    creditNote: 'Avoir',
    purchaseOrder: 'Commande fournisseur',
    purchaseInvoice: 'Facture fournisseur',
    deliveryNote: 'Bon de livraison',
    proforma: 'Proforma',
  },

  // ============================================================
  // TYPES DE CLIENT
  // ============================================================
  clientType: {
    prospect: 'Prospect',
    lead: 'Lead',
    customer: 'Client',
    vip: 'VIP',
    partner: 'Partenaire',
    churned: 'Perdu',
  },

  // ============================================================
  // CONDITIONS DE PAIEMENT
  // ============================================================
  paymentTerms: {
    immediate: 'Paiement immédiat',
    net15: 'Net 15 jours',
    net30: 'Net 30 jours',
    net45: 'Net 45 jours',
    net60: 'Net 60 jours',
    eom: 'Fin de mois',
    eom30: 'Fin de mois + 30',
  },

  // ============================================================
  // TAUX TVA
  // ============================================================
  vatRates: {
    rate0: '0%',
    rate55: '5,5%',
    rate10: '10%',
    rate20: '20%',
  },

  // ============================================================
  // ACTIONS PAGE
  // ============================================================
  action: {
    title: 'Action',
    pageTitle: 'Nouvelle action',
    pageSubtitle: 'Créez un document en quelques clics',
    selectDocumentType: 'Type de document',
    selectClient: 'Sélectionner un client',
    selectSupplier: 'Sélectionner un fournisseur',
    searchPlaceholder: 'Rechercher par nom, code ou email...',
    newClient: 'Nouveau client',
    newSupplier: 'Nouveau fournisseur',
    newProduct: 'Nouveau produit',
    addLine: 'Ajouter une ligne',
    removeLine: 'Supprimer la ligne',
    noLines: 'Aucune ligne',
    noLinesHint: 'Cliquez sur "Ajouter une ligne" pour commencer.',
    clickToEdit: 'Cliquez pour éditer',
    documentLines: 'Lignes du document',
    generalInfo: 'Informations générales',
    createDocument: 'Créer le document',
    saveAsDraft: 'Enregistrer en brouillon',
    validateDocument: 'Valider le document',
    validateWarning: 'Un document validé ne peut plus être modifié.',
    confirmValidation: 'Confirmer la validation',
    convertToInvoice: 'Convertir en facture',
    convertHint: 'Une nouvelle facture sera créée avec les mêmes lignes.',
    documentCreated: 'Document créé avec succès',
    documentSaved: 'Document enregistré',
    documentValidated: 'Document validé',
  },

  // ============================================================
  // COCKPIT
  // ============================================================
  cockpit: {
    title: 'Cockpit Dirigeant',
    subtitle: 'Vue d\'ensemble de votre activité',
    treasury: 'Trésorerie',
    currentBalance: 'Solde actuel',
    forecast30d: 'Prévision 30j',
    pendingPayments: 'En attente',
    sales: 'Ventes',
    monthRevenue: 'CA du mois',
    pendingInvoices: 'Factures en attente',
    overdueInvoices: 'Factures en retard',
    activity: 'Activité',
    openQuotes: 'Devis ouverts',
    pendingOrders: 'Commandes en cours',
    scheduledInterventions: 'Interventions planifiées',
    criticalAlerts: 'Alertes Critiques',
    pendingDecisions: 'Décisions en attente',
    alertsAndNotifications: 'Alertes et Notifications',
    noDecisions: 'Aucune décision en attente',
  },

  // ============================================================
  // TRÉSORERIE
  // ============================================================
  treasury: {
    title: 'Trésorerie',
    subtitle: 'Vue d\'ensemble de votre trésorerie',
    totalBalance: 'Solde total',
    pendingIn: 'Encaissements attendus',
    pendingOut: 'Décaissements prévus',
    forecast: 'Prévision',
    bankAccounts: 'Comptes bancaires',
    transactions: 'Transactions',
    reconciliation: 'Rapprochement',
    forecasts: 'Prévisions',
    newAccount: 'Nouveau compte',
    viewTransactions: 'Voir les transactions',
    reconciled: 'Rapproché',
    notReconciled: 'Non rapproché',
    noTransaction: 'Aucune transaction',
    forecastTitle: 'Prévisions de trésorerie',
    forecastSubtitle: 'Projection sur les 30 prochains jours',
    forecastSummary: 'Résumé des prévisions',
    dailyEvolution: 'Évolution journalière',
    alertNegative: 'Attention : votre solde prévisionnel devient négatif dans les 30 prochains jours.',
    alertLow: 'Votre solde prévisionnel sera bas dans les 30 prochains jours.',
    alertHealthy: 'Votre trésorerie est saine pour les 30 prochains jours.',
  },

  // ============================================================
  // ACHATS
  // ============================================================
  purchases: {
    title: 'Achats',
    subtitle: 'Gestion des fournisseurs et des achats',
    activeSuppliers: 'Fournisseurs actifs',
    pendingOrders: 'Commandes en cours',
    pendingValue: 'Valeur en attente',
    pendingInvoices: 'Factures à traiter',
    supplierDirectory: 'Carnet fournisseurs',
    supplierOrders: 'Commandes fournisseurs',
    supplierInvoices: 'Factures fournisseurs',
    newSupplier: 'Nouveau fournisseur',
    newOrder: 'Nouvelle commande',
    newInvoice: 'Nouvelle facture',
    orderLines: 'Lignes de commande',
    invoiceLines: 'Lignes de facture',
    supplierReference: 'Réf. fournisseur',
    createInvoice: 'Créer facture',
    validateOrder: 'Valider la commande',
    validateInvoice: 'Valider la facture',
    orderNotFound: 'Commande introuvable',
    invoiceNotFound: 'Facture introuvable',
    supplierNotFound: 'Fournisseur introuvable',
    cannotModify: 'Modification impossible',
    alreadyValidated: 'Ce document a été validé et ne peut plus être modifié.',
  },

  // ============================================================
  // FACTURATION
  // ============================================================
  invoicing: {
    title: 'Facturation',
    quotes: 'Devis',
    invoices: 'Factures',
    newQuote: 'Nouveau devis',
    newInvoice: 'Nouvelle facture',
    draftQuotes: 'Devis en brouillon',
    draftInvoices: 'Factures en brouillon',
    viewAll: 'Voir tout',
    noQuote: 'Aucun devis',
    noInvoice: 'Aucune facture',
    documentNotFound: 'Document non trouvé',
    documentNotFoundDesc: 'Le document demandé n\'existe pas ou a été supprimé.',
    backToList: 'Retour à la liste',
    createdFrom: 'Créé à partir du devis',
    viewOriginalQuote: 'voir le devis original',
    validatedOn: 'Validé le',
    searchPlaceholder: 'Rechercher par numéro ou client...',
    filters: 'Filtres',
    resetFilters: 'Réinitialiser',
    exportCSV: 'Export CSV',
    dateFrom: 'Date début',
    dateTo: 'Date fin',
    allStatuses: 'Tous les statuts',
  },

  // ============================================================
  // ADMINISTRATION
  // ============================================================
  admin: {
    title: 'Administration',
    subtitle: 'Gestion du système',
    users: 'Utilisateurs',
    activeUsers: 'Utilisateurs actifs',
    rolesAndCapabilities: 'Rôles & Capacités',
    tenants: 'Tenants',
    modules: 'Modules',
    activeModules: 'Modules actifs',
    auditLogs: 'Journaux d\'audit',
    branding: 'Personnalisation',
    breakGlass: 'Break-Glass Souverain',
    breakGlassDesc: 'Procédure d\'urgence - Accès réservé au créateur.',
    manageUsers: 'Gérer les comptes utilisateurs, leurs rôles et permissions.',
    manageRoles: 'Définir les rôles et attribuer les capacités d\'accès.',
    manageTenants: 'Gérer les organisations clientes et leurs paramètres.',
    manageModules: 'Activer ou désactiver les modules du système.',
    viewLogs: 'Consulter l\'historique des actions système.',
    configureBranding: 'Modifier le favicon, logo et identité visuelle.',
    newUser: 'Nouvel utilisateur',
    newRole: 'Nouveau rôle',
    lastLogin: 'Dernière connexion',
    never: 'Jamais',
    capabilities: 'Capacités',
    systemRole: 'Système',
    customRole: 'Personnalisé',
    viewCapabilities: 'Voir les capacités',
    noEvent: 'Aucun événement',
    dateTime: 'Date/Heure',
    ipAddress: 'Adresse IP',
    resource: 'Ressource',
    resetPassword: 'Réinitialiser mot de passe',
    activateDeactivate: 'Activer/Désactiver',
  },

  // ============================================================
  // PARTENAIRES
  // ============================================================
  partners: {
    title: 'Partenaires',
    clientsDesc: 'Gérer vos clients et prospects',
    suppliersDesc: 'Gérer vos fournisseurs',
    contactsDesc: 'Carnet d\'adresses',
    newClient: 'Nouveau client',
    newSupplier: 'Nouveau fournisseur',
    newContact: 'Nouveau contact',
    noClientAvailable: 'Aucun client disponible. Veuillez d\'abord créer un client.',
    loadingClients: 'Chargement des clients...',
  },

  // ============================================================
  // ERREURS
  // ============================================================
  errors: {
    generic: 'Une erreur est survenue',
    loadingFailed: 'Impossible de charger les données',
    saveFailed: 'Erreur lors de l\'enregistrement',
    deleteFailed: 'Erreur lors de la suppression',
    validationFailed: 'Erreur de validation',
    networkError: 'Erreur réseau',
    unauthorized: 'Non autorisé',
    forbidden: 'Accès refusé',
    notFound: 'Non trouvé',
    serverError: 'Erreur serveur',
    retry: 'Réessayer',
    emailInvalid: 'Email invalide',
    nameRequired: 'Nom requis',
    fieldRequired: 'Ce champ est requis',
    minLength: 'Minimum {{count}} caractères',
    maxLength: 'Maximum {{count}} caractères',
    selectClient: 'Veuillez sélectionner un client',
    selectSupplier: 'Veuillez sélectionner un fournisseur',
    addLine: 'Ajoutez au moins une ligne',
    lineDescription: 'Toutes les lignes doivent avoir une description',
    dateRequired: 'La date est requise',
  },

  // ============================================================
  // MESSAGES DE CONFIRMATION
  // ============================================================
  confirm: {
    delete: 'Êtes-vous sûr de vouloir supprimer cet élément ?',
    deleteDocument: 'Êtes-vous sûr de vouloir supprimer ce document ?',
    validate: 'Êtes-vous sûr de vouloir valider ? Cette action est irréversible.',
    cancel: 'Êtes-vous sûr de vouloir annuler ?',
    unsavedChanges: 'Vous avez des modifications non enregistrées. Voulez-vous vraiment quitter ?',
  },

  // ============================================================
  // PLACEHOLDER / EMPTY STATES
  // ============================================================
  empty: {
    noData: 'Aucune donnée',
    noResults: 'Aucun résultat',
    noDocument: 'Aucun document',
    noClient: 'Aucun client',
    noSupplier: 'Aucun fournisseur',
    noContact: 'Aucun contact',
    noTransaction: 'Aucune transaction',
    noLine: 'Aucune ligne',
  },

  // ============================================================
  // BRANDING
  // ============================================================
  branding: {
    title: 'Personnalisation',
    subtitle: 'Favicon, logo et identité visuelle',
    favicon: 'Favicon (icône onglet)',
    logo: 'Logo entreprise',
    currentFavicon: 'Favicon actuel',
    currentLogo: 'Logo actuel',
    noLogo: 'Aucun logo',
    chooseFile: 'Choisir un fichier',
    saveFavicon: 'Enregistrer le favicon',
    saveLogo: 'Enregistrer le logo',
    reset: 'Réinitialiser',
    remove: 'Supprimer',
    uploadSuccess: 'Fichier mis à jour. Rechargez la page pour voir les changements.',
    uploadError: 'Erreur lors de l\'upload',
    faviconInfo: 'Le favicon apparaît dans l\'onglet du navigateur (recommandé: 32x32 ou 64x64 pixels)',
    logoInfo: 'Le logo peut être utilisé dans l\'interface et les documents (recommandé: format horizontal)',
    reloadInfo: 'Les changements de favicon nécessitent un rechargement complet de la page (Ctrl+Shift+R)',
    formats: 'Formats supportés: PNG, JPG, ICO, SVG',
  },

  // ============================================================
  // APPLICATION
  // ============================================================
  app: {
    name: 'Azalscore',
    loading: 'Chargement de l\'application...',
    error: 'Erreur',
    initError: 'Erreur lors de l\'initialisation de l\'application',
    reload: 'Recharger',
    auth: 'Auth',
    capabilities: 'Capabilities',
  },

  // ============================================================
  // AUTHENTIFICATION
  // ============================================================
  auth: {
    login: 'Connexion',
    logout: 'Déconnexion',
    email: 'Email',
    password: 'Mot de passe',
    forgotPassword: 'Mot de passe oublié ?',
    twoFactor: 'Authentification à deux facteurs',
    profile: 'Profil',
    settings: 'Paramètres',
    personalInfo: 'Informations personnelles',
  },

  // ============================================================
  // NAVIGATION
  // ============================================================
  nav: {
    home: 'Accueil',
    cockpit: 'Cockpit',
    action: 'Action',
    partners: 'Partenaires',
    invoicing: 'Facturation',
    purchases: 'Achats',
    treasury: 'Trésorerie',
    accounting: 'Comptabilité',
    projects: 'Projets',
    interventions: 'Interventions',
    admin: 'Administration',
    profile: 'Profil',
    settings: 'Paramètres',
  },

  // ============================================================
  // PAGINATION
  // ============================================================
  pagination: {
    page: 'Page',
    of: 'sur',
    items: 'éléments',
    perPage: 'par page',
    previous: 'Page précédente',
    next: 'Page suivante',
    first: 'Première page',
    last: 'Dernière page',
  },
};

export default fr;
