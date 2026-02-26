"""
AZALSCORE - IAM Capabilities
Définition des capacités (permissions) par module
"""
from __future__ import annotations


def get_icon_for_module(icon_code: str) -> str:
    """Convertit le code icône en nom Lucide React."""
    icon_map = {
        "book": "BookOpen", "file-text": "FileText", "dollar-sign": "DollarSign",
        "users": "Users", "credit-card": "CreditCard", "briefcase": "Briefcase",
        "package": "Package", "shopping-cart": "ShoppingCart", "user": "User",
        "settings": "Settings", "tool": "Wrench", "check-circle": "CheckCircle",
        "monitor": "Monitor", "shopping-bag": "ShoppingBag", "headphones": "Headphones",
        "bar-chart-2": "BarChart2", "shield": "Shield", "truck": "Truck",
        "bot": "Bot", "building": "Building", "file-signature": "FileSignature",
        "receipt": "Receipt", "clock": "Clock", "map-pin": "MapPin",
        "alert-circle": "AlertCircle", "shield-check": "ShieldCheck",
        "file-search": "FileSearch", "repeat": "Repeat", "store": "Store",
        "pen-tool": "PenTool", "mail": "Mail", "send": "Send", "globe": "Globe",
        "trending-up": "TrendingUp", "layers": "Layers", "check-square": "CheckSquare",
        "cpu": "Cpu", "share-2": "Share2", "smartphone": "Smartphone", "mic": "Mic",
        "database": "Database", "eye": "Eye", "key": "Key", "building-2": "Building2",
        "zap": "Zap", "download": "Download", "flag": "Flag", "lock": "Lock",
        "folder": "Folder",
    }
    return icon_map.get(icon_code, "Folder")


def get_custom_capabilities() -> dict:
    """
    Capabilities personnalisées pour les modules complexes.

    Ces définitions remplacent les capabilities auto-générées
    pour les modules nécessitant un contrôle fin des permissions.
    """
    return {
        "cockpit": {
            "name": "Tableau de bord",
            "icon": "LayoutDashboard",
            "capabilities": [
                {"code": "cockpit.view", "name": "Voir le tableau de bord", "description": "Accès au cockpit principal"},
                {"code": "cockpit.decisions.view", "name": "Voir les décisions", "description": "Accès aux décisions stratégiques"},
            ]
        },
        "partners": {
            "name": "Partenaires",
            "icon": "Users",
            "capabilities": [
                {"code": "partners.view", "name": "Voir les partenaires", "description": "Accès en lecture aux partenaires"},
                {"code": "partners.create", "name": "Créer des partenaires", "description": "Créer de nouveaux partenaires"},
                {"code": "partners.edit", "name": "Modifier les partenaires", "description": "Modifier les partenaires existants"},
                {"code": "partners.delete", "name": "Supprimer les partenaires", "description": "Supprimer des partenaires"},
                {"code": "partners.clients.view", "name": "Voir les clients", "description": "Accès aux fiches clients"},
                {"code": "partners.clients.create", "name": "Créer des clients", "description": "Créer de nouveaux clients"},
                {"code": "partners.clients.edit", "name": "Modifier les clients", "description": "Modifier les clients"},
                {"code": "partners.clients.delete", "name": "Supprimer les clients", "description": "Supprimer des clients"},
                {"code": "partners.suppliers.view", "name": "Voir les fournisseurs", "description": "Accès aux fiches fournisseurs"},
                {"code": "partners.suppliers.create", "name": "Créer des fournisseurs", "description": "Créer de nouveaux fournisseurs"},
                {"code": "partners.suppliers.edit", "name": "Modifier les fournisseurs", "description": "Modifier les fournisseurs"},
                {"code": "partners.suppliers.delete", "name": "Supprimer les fournisseurs", "description": "Supprimer des fournisseurs"},
                {"code": "partners.contacts.view", "name": "Voir les contacts", "description": "Accès aux contacts"},
                {"code": "partners.contacts.create", "name": "Créer des contacts", "description": "Créer de nouveaux contacts"},
                {"code": "partners.contacts.edit", "name": "Modifier les contacts", "description": "Modifier les contacts"},
                {"code": "partners.contacts.delete", "name": "Supprimer les contacts", "description": "Supprimer des contacts"},
            ]
        },
        "contacts": {
            "name": "Contacts Unifiés",
            "icon": "Contact",
            "capabilities": [
                {"code": "contacts.view", "name": "Voir les contacts", "description": "Accès aux contacts unifiés"},
                {"code": "contacts.create", "name": "Créer des contacts", "description": "Créer de nouveaux contacts"},
                {"code": "contacts.edit", "name": "Modifier les contacts", "description": "Modifier les contacts"},
                {"code": "contacts.delete", "name": "Supprimer les contacts", "description": "Supprimer des contacts"},
            ]
        },
        "invoicing": {
            "name": "Facturation",
            "icon": "FileText",
            "capabilities": [
                {"code": "invoicing.view", "name": "Voir la facturation", "description": "Accès en lecture à la facturation"},
                {"code": "invoicing.create", "name": "Créer des documents", "description": "Créer devis/factures/avoirs"},
                {"code": "invoicing.edit", "name": "Modifier des documents", "description": "Modifier les documents"},
                {"code": "invoicing.delete", "name": "Supprimer des documents", "description": "Supprimer des documents"},
                {"code": "invoicing.send", "name": "Envoyer des documents", "description": "Envoyer par email"},
                {"code": "invoicing.quotes.view", "name": "Voir les devis", "description": "Accès aux devis"},
                {"code": "invoicing.quotes.create", "name": "Créer des devis", "description": "Créer de nouveaux devis"},
                {"code": "invoicing.quotes.edit", "name": "Modifier les devis", "description": "Modifier les devis"},
                {"code": "invoicing.quotes.delete", "name": "Supprimer les devis", "description": "Supprimer des devis"},
                {"code": "invoicing.quotes.send", "name": "Envoyer les devis", "description": "Envoyer les devis par email"},
                {"code": "invoicing.invoices.view", "name": "Voir les factures", "description": "Accès aux factures"},
                {"code": "invoicing.invoices.create", "name": "Créer des factures", "description": "Créer de nouvelles factures"},
                {"code": "invoicing.invoices.edit", "name": "Modifier les factures", "description": "Modifier les factures"},
                {"code": "invoicing.invoices.delete", "name": "Supprimer les factures", "description": "Supprimer des factures"},
                {"code": "invoicing.invoices.send", "name": "Envoyer les factures", "description": "Envoyer les factures par email"},
                {"code": "invoicing.credits.view", "name": "Voir les avoirs", "description": "Accès aux avoirs"},
                {"code": "invoicing.credits.create", "name": "Créer des avoirs", "description": "Créer de nouveaux avoirs"},
                {"code": "invoicing.credits.edit", "name": "Modifier les avoirs", "description": "Modifier les avoirs"},
                {"code": "invoicing.credits.delete", "name": "Supprimer les avoirs", "description": "Supprimer des avoirs"},
                {"code": "invoicing.credits.send", "name": "Envoyer les avoirs", "description": "Envoyer les avoirs par email"},
            ]
        },
        "treasury": {
            "name": "Trésorerie",
            "icon": "Wallet",
            "capabilities": [
                {"code": "treasury.view", "name": "Voir la trésorerie", "description": "Accès à la trésorerie"},
                {"code": "treasury.create", "name": "Créer des opérations", "description": "Créer des opérations"},
                {"code": "treasury.transfer.execute", "name": "Exécuter des virements", "description": "Exécuter des virements bancaires"},
                {"code": "treasury.accounts.view", "name": "Voir les comptes", "description": "Accès aux comptes bancaires"},
                {"code": "treasury.accounts.create", "name": "Créer des comptes", "description": "Créer de nouveaux comptes"},
                {"code": "treasury.accounts.edit", "name": "Modifier les comptes", "description": "Modifier les comptes"},
                {"code": "treasury.accounts.delete", "name": "Supprimer les comptes", "description": "Supprimer des comptes"},
            ]
        },
        "accounting": {
            "name": "Comptabilité",
            "icon": "Calculator",
            "capabilities": [
                {"code": "accounting.view", "name": "Voir la comptabilité", "description": "Accès à la comptabilité"},
                {"code": "accounting.journal.view", "name": "Voir les journaux", "description": "Accès aux journaux comptables"},
                {"code": "accounting.journal.delete", "name": "Supprimer des écritures", "description": "Supprimer des écritures comptables"},
            ]
        },
        "purchases": {
            "name": "Achats",
            "icon": "ShoppingCart",
            "capabilities": [
                {"code": "purchases.view", "name": "Voir les achats", "description": "Accès aux achats"},
                {"code": "purchases.create", "name": "Créer des achats", "description": "Créer des commandes d'achat"},
                {"code": "purchases.edit", "name": "Modifier les achats", "description": "Modifier les achats"},
                {"code": "purchases.orders.view", "name": "Voir les commandes", "description": "Accès aux commandes fournisseurs"},
                {"code": "purchases.orders.create", "name": "Créer des commandes", "description": "Créer des commandes"},
                {"code": "purchases.orders.edit", "name": "Modifier les commandes", "description": "Modifier les commandes"},
                {"code": "purchases.orders.delete", "name": "Supprimer les commandes", "description": "Supprimer des commandes"},
            ]
        },
        "projects": {
            "name": "Projets",
            "icon": "FolderKanban",
            "capabilities": [
                {"code": "projects.view", "name": "Voir les projets", "description": "Accès aux projets"},
                {"code": "projects.create", "name": "Créer des projets", "description": "Créer de nouveaux projets"},
                {"code": "projects.edit", "name": "Modifier les projets", "description": "Modifier les projets"},
                {"code": "projects.delete", "name": "Supprimer les projets", "description": "Supprimer des projets"},
            ]
        },
        "hr": {
            "name": "Ressources Humaines",
            "icon": "UserCog",
            "capabilities": [
                {"code": "hr.view", "name": "Voir les RH", "description": "Accès au module RH"},
                {"code": "hr.create", "name": "Créer des données RH", "description": "Créer des données RH"},
                {"code": "hr.edit", "name": "Modifier les données RH", "description": "Modifier les données RH"},
                {"code": "hr.delete", "name": "Supprimer les données RH", "description": "Supprimer des données RH"},
                {"code": "hr.employees.view", "name": "Voir les employés", "description": "Accès aux fiches employés"},
                {"code": "hr.employees.create", "name": "Créer des employés", "description": "Créer de nouveaux employés"},
                {"code": "hr.employees.edit", "name": "Modifier les employés", "description": "Modifier les employés"},
                {"code": "hr.employees.delete", "name": "Supprimer les employés", "description": "Supprimer des employés"},
                {"code": "hr.payroll.view", "name": "Voir la paie", "description": "Accès à la paie"},
                {"code": "hr.payroll.create", "name": "Créer des bulletins", "description": "Créer des bulletins de paie"},
                {"code": "hr.payroll.edit", "name": "Modifier la paie", "description": "Modifier les bulletins"},
                {"code": "hr.leave.view", "name": "Voir les congés", "description": "Accès aux congés"},
                {"code": "hr.leave.create", "name": "Créer des congés", "description": "Créer des demandes de congés"},
                {"code": "hr.leave.approve", "name": "Approuver les congés", "description": "Approuver/refuser les congés"},
            ]
        },
        "interventions": {
            "name": "Interventions",
            "icon": "Wrench",
            "capabilities": [
                {"code": "interventions.view", "name": "Voir les interventions", "description": "Accès aux interventions"},
                {"code": "interventions.create", "name": "Créer des interventions", "description": "Créer de nouvelles interventions"},
                {"code": "interventions.edit", "name": "Modifier les interventions", "description": "Modifier les interventions"},
                {"code": "interventions.tickets.view", "name": "Voir les tickets", "description": "Accès aux tickets"},
                {"code": "interventions.tickets.create", "name": "Créer des tickets", "description": "Créer de nouveaux tickets"},
                {"code": "interventions.tickets.edit", "name": "Modifier les tickets", "description": "Modifier les tickets"},
                {"code": "interventions.tickets.delete", "name": "Supprimer les tickets", "description": "Supprimer des tickets"},
            ]
        },
        "inventory": {
            "name": "Stock / Inventaire",
            "icon": "Package",
            "capabilities": [
                {"code": "inventory.view", "name": "Voir le stock", "description": "Accès au stock"},
                {"code": "inventory.create", "name": "Créer des articles", "description": "Créer des articles de stock"},
                {"code": "inventory.edit", "name": "Modifier le stock", "description": "Modifier le stock"},
                {"code": "inventory.delete", "name": "Supprimer du stock", "description": "Supprimer des articles"},
                {"code": "inventory.warehouses.view", "name": "Voir les entrepôts", "description": "Accès aux entrepôts"},
                {"code": "inventory.warehouses.create", "name": "Créer des entrepôts", "description": "Créer de nouveaux entrepôts"},
                {"code": "inventory.warehouses.edit", "name": "Modifier les entrepôts", "description": "Modifier les entrepôts"},
                {"code": "inventory.products.view", "name": "Voir les produits", "description": "Accès aux produits"},
                {"code": "inventory.products.create", "name": "Créer des produits", "description": "Créer de nouveaux produits"},
                {"code": "inventory.products.edit", "name": "Modifier les produits", "description": "Modifier les produits"},
                {"code": "inventory.movements.view", "name": "Voir les mouvements", "description": "Accès aux mouvements de stock"},
                {"code": "inventory.movements.create", "name": "Créer des mouvements", "description": "Créer des mouvements de stock"},
            ]
        },
        "admin": {
            "name": "Administration",
            "icon": "Lock",
            "capabilities": [
                {"code": "admin.view", "name": "Accès administration", "description": "Accès au module admin"},
                {"code": "admin.users.view", "name": "Voir les utilisateurs", "description": "Voir la liste des utilisateurs"},
                {"code": "admin.users.create", "name": "Créer des utilisateurs", "description": "Créer de nouveaux utilisateurs"},
                {"code": "admin.users.edit", "name": "Modifier les utilisateurs", "description": "Modifier les utilisateurs"},
                {"code": "admin.users.delete", "name": "Supprimer les utilisateurs", "description": "Supprimer des utilisateurs"},
                {"code": "admin.roles.view", "name": "Voir les rôles", "description": "Voir la liste des rôles"},
                {"code": "admin.roles.create", "name": "Créer des rôles", "description": "Créer de nouveaux rôles"},
                {"code": "admin.roles.edit", "name": "Modifier les rôles", "description": "Modifier les rôles"},
                {"code": "admin.roles.delete", "name": "Supprimer les rôles", "description": "Supprimer des rôles"},
                {"code": "admin.tenants.view", "name": "Voir les tenants", "description": "Voir la liste des tenants"},
                {"code": "admin.tenants.create", "name": "Créer des tenants", "description": "Créer de nouveaux tenants"},
                {"code": "admin.tenants.delete", "name": "Supprimer les tenants", "description": "Supprimer des tenants"},
                {"code": "admin.modules.view", "name": "Voir les modules", "description": "Voir les modules activés"},
                {"code": "admin.modules.edit", "name": "Modifier les modules", "description": "Activer/désactiver des modules"},
                {"code": "admin.logs.view", "name": "Voir les logs", "description": "Accès aux journaux système"},
                {"code": "admin.root.break_glass", "name": "Break Glass", "description": "Accès d'urgence super admin"},
            ]
        },
        "iam": {
            "name": "Gestion des Accès (IAM)",
            "icon": "Key",
            "capabilities": [
                {"code": "iam.user.create", "name": "Créer des utilisateurs IAM", "description": "Créer des utilisateurs"},
                {"code": "iam.user.read", "name": "Voir les utilisateurs IAM", "description": "Voir les utilisateurs"},
                {"code": "iam.user.update", "name": "Modifier les utilisateurs IAM", "description": "Modifier les utilisateurs"},
                {"code": "iam.user.delete", "name": "Supprimer les utilisateurs IAM", "description": "Supprimer des utilisateurs"},
                {"code": "iam.user.admin", "name": "Administrer les utilisateurs", "description": "Administration complète"},
                {"code": "iam.role.create", "name": "Créer des rôles", "description": "Créer de nouveaux rôles"},
                {"code": "iam.role.read", "name": "Voir les rôles", "description": "Voir les rôles"},
                {"code": "iam.role.update", "name": "Modifier les rôles", "description": "Modifier les rôles"},
                {"code": "iam.role.delete", "name": "Supprimer les rôles", "description": "Supprimer des rôles"},
                {"code": "iam.role.assign", "name": "Assigner des rôles", "description": "Assigner des rôles aux utilisateurs"},
                {"code": "iam.group.create", "name": "Créer des groupes", "description": "Créer de nouveaux groupes"},
                {"code": "iam.group.read", "name": "Voir les groupes", "description": "Voir les groupes"},
                {"code": "iam.group.update", "name": "Modifier les groupes", "description": "Modifier les groupes"},
                {"code": "iam.group.delete", "name": "Supprimer les groupes", "description": "Supprimer des groupes"},
                {"code": "iam.permission.read", "name": "Voir les permissions", "description": "Voir les permissions"},
                {"code": "iam.permission.admin", "name": "Administrer les permissions", "description": "Gérer toutes les permissions"},
                {"code": "iam.invitation.create", "name": "Créer des invitations", "description": "Inviter des utilisateurs"},
                {"code": "iam.policy.read", "name": "Voir les politiques", "description": "Voir les politiques de sécurité"},
                {"code": "iam.policy.update", "name": "Modifier les politiques", "description": "Modifier les politiques"},
            ]
        },
        "marceau": {
            "name": "Marceau AI Assistant",
            "icon": "Bot",
            "capabilities": [
                {"code": "marceau.view", "name": "Voir Marceau", "description": "Accès au module Marceau AI"},
                {"code": "marceau.config.view", "name": "Voir la configuration", "description": "Voir la configuration Marceau"},
                {"code": "marceau.config.edit", "name": "Modifier la configuration", "description": "Modifier les paramètres Marceau"},
                {"code": "marceau.actions.view", "name": "Voir les actions", "description": "Voir l'historique des actions IA"},
                {"code": "marceau.actions.validate", "name": "Valider les actions", "description": "Valider/rejeter les actions IA"},
                {"code": "marceau.conversations.view", "name": "Voir les conversations", "description": "Accès aux conversations téléphoniques"},
                {"code": "marceau.memory.view", "name": "Voir la mémoire", "description": "Accès à la mémoire Marceau"},
                {"code": "marceau.memory.edit", "name": "Modifier la mémoire", "description": "Ajouter/supprimer des souvenirs"},
                {"code": "marceau.knowledge.view", "name": "Voir la base de connaissances", "description": "Accès aux documents"},
                {"code": "marceau.knowledge.edit", "name": "Modifier la base de connaissances", "description": "Upload/supprimer des documents"},
                {"code": "marceau.chat", "name": "Discuter avec Marceau", "description": "Utiliser le chat Marceau"},
            ]
        },
        "enrichment": {
            "name": "Enrichissement",
            "icon": "Sparkles",
            "capabilities": [
                {"code": "enrichment.view", "name": "Utiliser l'enrichissement", "description": "Accès aux fonctions d'auto-enrichissement"},
                {"code": "enrichment.siret", "name": "Recherche SIRET/SIREN", "description": "Rechercher des entreprises par SIRET/SIREN"},
                {"code": "enrichment.address", "name": "Autocomplete adresse", "description": "Utiliser l'autocomplete d'adresses"},
                {"code": "enrichment.barcode", "name": "Recherche code-barres", "description": "Rechercher des produits par code-barres"},
                {"code": "enrichment.risk_analysis", "name": "Analyse de risque", "description": "Accès a l'analyse de risque entreprise"},
                {"code": "enrichment.history", "name": "Historique enrichissement", "description": "Voir l'historique des enrichissements"},
                {"code": "enrichment.stats", "name": "Statistiques enrichissement", "description": "Voir les statistiques d'utilisation"},
            ]
        },
    }


def get_additional_capabilities() -> dict:
    """Capabilities additionnelles pour modules techniques et utilitaires."""
    return {
        "ecommerce": {"name": "E-commerce", "icon": "Store", "capabilities": [
            {"code": "ecommerce.view", "name": "Voir l'e-commerce", "description": "Accès au module e-commerce"},
            {"code": "ecommerce.create", "name": "Créer des données", "description": "Créer des données e-commerce"},
            {"code": "ecommerce.edit", "name": "Modifier l'e-commerce", "description": "Modifier les données"},
            {"code": "ecommerce.delete", "name": "Supprimer des données", "description": "Supprimer des données"},
        ]},
        "crm": {"name": "CRM", "icon": "Heart", "capabilities": [
            {"code": "crm.view", "name": "Voir le CRM", "description": "Accès au CRM"},
            {"code": "crm.create", "name": "Créer des données CRM", "description": "Créer des opportunités/leads"},
            {"code": "crm.edit", "name": "Modifier le CRM", "description": "Modifier les données CRM"},
            {"code": "crm.delete", "name": "Supprimer du CRM", "description": "Supprimer des données CRM"},
        ]},
        "production": {"name": "Production", "icon": "Factory", "capabilities": [
            {"code": "production.view", "name": "Voir la production", "description": "Accès à la production"},
            {"code": "production.create", "name": "Créer des ordres", "description": "Créer des ordres de fabrication"},
            {"code": "production.edit", "name": "Modifier la production", "description": "Modifier les ordres"},
            {"code": "production.delete", "name": "Supprimer des ordres", "description": "Supprimer des ordres"},
        ]},
        "quality": {"name": "Qualité", "icon": "CheckCircle", "capabilities": [
            {"code": "quality.view", "name": "Voir la qualité", "description": "Accès au module qualité"},
            {"code": "quality.create", "name": "Créer des contrôles", "description": "Créer des contrôles qualité"},
            {"code": "quality.edit", "name": "Modifier la qualité", "description": "Modifier les contrôles"},
        ]},
        "maintenance": {"name": "Maintenance (GMAO)", "icon": "Settings", "capabilities": [
            {"code": "maintenance.view", "name": "Voir la maintenance", "description": "Accès à la GMAO"},
            {"code": "maintenance.create", "name": "Créer des interventions", "description": "Créer des interventions"},
            {"code": "maintenance.edit", "name": "Modifier la maintenance", "description": "Modifier les interventions"},
            {"code": "maintenance.delete", "name": "Supprimer des interventions", "description": "Supprimer des interventions"},
        ]},
        "pos": {"name": "Point de Vente", "icon": "CreditCard", "capabilities": [
            {"code": "pos.view", "name": "Voir le POS", "description": "Accès au point de vente"},
            {"code": "pos.create", "name": "Créer des ventes", "description": "Créer des ventes"},
            {"code": "pos.edit", "name": "Modifier le POS", "description": "Modifier les ventes"},
        ]},
        "subscriptions": {"name": "Abonnements", "icon": "Repeat", "capabilities": [
            {"code": "subscriptions.view", "name": "Voir les abonnements", "description": "Accès aux abonnements"},
            {"code": "subscriptions.create", "name": "Créer des abonnements", "description": "Créer de nouveaux abonnements"},
            {"code": "subscriptions.edit", "name": "Modifier les abonnements", "description": "Modifier les abonnements"},
            {"code": "subscriptions.delete", "name": "Supprimer les abonnements", "description": "Supprimer des abonnements"},
        ]},
        "helpdesk": {"name": "Helpdesk", "icon": "Headphones", "capabilities": [
            {"code": "helpdesk.view", "name": "Voir le helpdesk", "description": "Accès au helpdesk"},
            {"code": "helpdesk.create", "name": "Créer des tickets", "description": "Créer des tickets support"},
            {"code": "helpdesk.edit", "name": "Modifier les tickets", "description": "Modifier les tickets"},
        ]},
        "bi": {"name": "Business Intelligence", "icon": "BarChart3", "capabilities": [
            {"code": "bi.view", "name": "Voir les rapports", "description": "Accès aux rapports BI"},
            {"code": "bi.create", "name": "Créer des rapports", "description": "Créer de nouveaux rapports"},
            {"code": "bi.edit", "name": "Modifier les rapports", "description": "Modifier les rapports"},
        ]},
        "compliance": {"name": "Conformité", "icon": "Shield", "capabilities": [
            {"code": "compliance.view", "name": "Voir la conformité", "description": "Accès à la conformité"},
            {"code": "compliance.edit", "name": "Modifier la conformité", "description": "Gérer la conformité"},
        ]},
        "mobile": {"name": "Application Mobile", "icon": "Smartphone", "capabilities": [
            {"code": "mobile.view", "name": "Accès mobile", "description": "Accès à l'application mobile"},
        ]},
        "audit": {"name": "Audit", "icon": "Eye", "capabilities": [
            {"code": "audit.view", "name": "Voir les audits", "description": "Accès aux logs d'audit"},
            {"code": "audit.create", "name": "Créer des audits", "description": "Déclencher des audits"},
            {"code": "audit.export", "name": "Exporter les audits", "description": "Exporter les données d'audit"},
        ]},
        "backup": {"name": "Sauvegardes", "icon": "Database", "capabilities": [
            {"code": "backup.view", "name": "Voir les sauvegardes", "description": "Accès aux sauvegardes"},
            {"code": "backup.create", "name": "Créer des sauvegardes", "description": "Créer de nouvelles sauvegardes"},
            {"code": "backup.restore", "name": "Restaurer", "description": "Restaurer depuis une sauvegarde"},
            {"code": "backup.delete", "name": "Supprimer des sauvegardes", "description": "Supprimer des sauvegardes"},
        ]},
        "expenses": {"name": "Notes de Frais", "icon": "Receipt", "capabilities": [
            {"code": "expenses.view", "name": "Voir les notes de frais", "description": "Accès aux notes de frais"},
            {"code": "expenses.create", "name": "Créer des notes de frais", "description": "Créer de nouvelles notes"},
            {"code": "expenses.approve", "name": "Approuver les notes", "description": "Approuver/rejeter les notes"},
            {"code": "expenses.reject", "name": "Rejeter les notes", "description": "Rejeter des notes de frais"},
        ]},
        "contracts": {"name": "Contrats", "icon": "FileSignature", "capabilities": [
            {"code": "contracts.view", "name": "Voir les contrats", "description": "Accès aux contrats"},
            {"code": "contracts.create", "name": "Créer des contrats", "description": "Créer de nouveaux contrats"},
            {"code": "contracts.edit", "name": "Modifier les contrats", "description": "Modifier les contrats"},
            {"code": "contracts.delete", "name": "Supprimer les contrats", "description": "Supprimer des contrats"},
        ]},
        "timesheet": {"name": "Feuilles de Temps", "icon": "Clock", "capabilities": [
            {"code": "timesheet.view", "name": "Voir les feuilles de temps", "description": "Accès aux feuilles de temps"},
            {"code": "timesheet.create", "name": "Créer des entrées", "description": "Saisir du temps"},
            {"code": "timesheet.approve", "name": "Approuver les feuilles", "description": "Approuver les feuilles de temps"},
        ]},
        "workflows": {"name": "Workflows", "icon": "GitBranch", "capabilities": [
            {"code": "workflows.view", "name": "Voir les workflows", "description": "Accès aux workflows"},
            {"code": "workflows.create", "name": "Créer des workflows", "description": "Créer de nouveaux workflows"},
            {"code": "workflows.edit", "name": "Modifier les workflows", "description": "Modifier les workflows"},
        ]},
        "notifications": {"name": "Notifications", "icon": "Bell", "capabilities": [
            {"code": "notifications.view", "name": "Voir les notifications", "description": "Accès aux notifications"},
            {"code": "notifications.config", "name": "Configurer", "description": "Configurer les notifications"},
            {"code": "notifications.send", "name": "Envoyer", "description": "Envoyer des notifications"},
        ]},
        "webhooks": {"name": "Webhooks", "icon": "Webhook", "capabilities": [
            {"code": "webhooks.view", "name": "Voir les webhooks", "description": "Accès aux webhooks"},
            {"code": "webhooks.create", "name": "Créer des webhooks", "description": "Créer de nouveaux webhooks"},
            {"code": "webhooks.edit", "name": "Modifier les webhooks", "description": "Modifier les webhooks"},
        ]},
        "import_data": {"name": "Import de Données", "icon": "Download", "capabilities": [
            {"code": "import_data.view", "name": "Voir les imports", "description": "Accès aux imports"},
            {"code": "import_data.odoo", "name": "Import Odoo", "description": "Importer depuis Odoo"},
            {"code": "import_data.axonaut", "name": "Import Axonaut", "description": "Importer depuis Axonaut"},
            {"code": "import_data.pennylane", "name": "Import Pennylane", "description": "Importer depuis Pennylane"},
            {"code": "import_data.sage", "name": "Import Sage", "description": "Importer depuis Sage"},
        ]},
    }


def generate_capabilities_by_module() -> dict:
    """
    Génère automatiquement CAPABILITIES_BY_MODULE depuis modules_registry.
    Les modules avec overrides personnalisés sont préservés.
    """
    from app.core.modules_registry import MODULES

    # Combiner les capabilities personnalisées
    result = dict(get_custom_capabilities())
    result.update(get_additional_capabilities())

    # Générer les capabilities pour les modules non personnalisés
    for module in MODULES:
        code = module["code"].replace("-", "_")

        # Ignorer les imports (IMP1, IMP2, etc.)
        if code.startswith("IMP"):
            continue

        # Ignorer si déjà personnalisé
        if code in result:
            continue

        # Générer capabilities par défaut
        result[code] = {
            "name": module["name"],
            "icon": get_icon_for_module(module.get("icon", "folder")),
            "capabilities": [
                {"code": f"{code}.view", "name": f"Voir {module['name']}", "description": f"Accès au module {module['name']}"},
                {"code": f"{code}.create", "name": "Créer", "description": f"Créer dans {module['name']}"},
                {"code": f"{code}.edit", "name": "Modifier", "description": f"Modifier dans {module['name']}"},
                {"code": f"{code}.delete", "name": "Supprimer", "description": f"Supprimer dans {module['name']}"},
            ]
        }

    return result


# Cache des capabilities générées
_capabilities_cache: dict | None = None


def get_capabilities_by_module() -> dict:
    """Retourne les capabilities par module (avec cache)."""
    global _capabilities_cache
    if _capabilities_cache is None:
        _capabilities_cache = generate_capabilities_by_module()
    return _capabilities_cache
