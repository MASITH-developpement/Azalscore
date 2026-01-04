"""
AZALS MODULE T0 - Permissions Prédéfinies
=========================================

Définitions des permissions standard AZALS.
Format: module.resource.action
"""

from typing import Dict, List

# ============================================================================
# PERMISSIONS PAR MODULE
# ============================================================================

IAM_PERMISSIONS = {
    # Gestion utilisateurs
    "iam.user.create": "Créer des utilisateurs",
    "iam.user.read": "Voir les utilisateurs",
    "iam.user.update": "Modifier les utilisateurs",
    "iam.user.delete": "Supprimer des utilisateurs",
    "iam.user.admin": "Administration complète utilisateurs",

    # Gestion rôles
    "iam.role.create": "Créer des rôles",
    "iam.role.read": "Voir les rôles",
    "iam.role.update": "Modifier les rôles",
    "iam.role.delete": "Supprimer des rôles",
    "iam.role.assign": "Attribuer/retirer des rôles",

    # Gestion permissions
    "iam.permission.create": "Créer des permissions",
    "iam.permission.read": "Voir les permissions",
    "iam.permission.update": "Modifier les permissions",
    "iam.permission.delete": "Supprimer des permissions",

    # Gestion groupes
    "iam.group.create": "Créer des groupes",
    "iam.group.read": "Voir les groupes",
    "iam.group.update": "Modifier les groupes",
    "iam.group.delete": "Supprimer des groupes",

    # Invitations
    "iam.invitation.create": "Créer des invitations",
    "iam.invitation.read": "Voir les invitations",
    "iam.invitation.cancel": "Annuler des invitations",

    # Politique
    "iam.policy.read": "Voir les politiques",
    "iam.policy.update": "Modifier les politiques",

    # Audit
    "iam.audit.read": "Voir les logs d'audit",
    "iam.audit.export": "Exporter les logs d'audit",
}

TREASURY_PERMISSIONS = {
    "treasury.forecast.create": "Créer des prévisions trésorerie",
    "treasury.forecast.read": "Voir les prévisions trésorerie",
    "treasury.forecast.update": "Modifier les prévisions",
    "treasury.forecast.validate": "Valider les prévisions",
    "treasury.report.read": "Voir les rapports trésorerie",
    "treasury.report.export": "Exporter les rapports",
}

LEGAL_PERMISSIONS = {
    "legal.contract.create": "Créer des contrats",
    "legal.contract.read": "Voir les contrats",
    "legal.contract.update": "Modifier les contrats",
    "legal.contract.validate": "Valider les contrats",
    "legal.compliance.read": "Voir la conformité",
    "legal.compliance.update": "Modifier la conformité",
}

TAX_PERMISSIONS = {
    "tax.declaration.create": "Créer des déclarations",
    "tax.declaration.read": "Voir les déclarations",
    "tax.declaration.validate": "Valider les déclarations",
    "tax.deadline.read": "Voir les échéances fiscales",
    "tax.deadline.update": "Modifier les échéances",
}

HR_PERMISSIONS = {
    "hr.employee.create": "Créer des employés",
    "hr.employee.read": "Voir les employés",
    "hr.employee.update": "Modifier les employés",
    "hr.employee.delete": "Supprimer des employés",
    "hr.payroll.create": "Créer la paie",
    "hr.payroll.read": "Voir la paie",
    "hr.payroll.validate": "Valider la paie",
    "hr.leave.create": "Créer des congés",
    "hr.leave.read": "Voir les congés",
    "hr.leave.validate": "Valider les congés",
}

ACCOUNTING_PERMISSIONS = {
    "accounting.entry.create": "Créer des écritures",
    "accounting.entry.read": "Voir les écritures",
    "accounting.entry.update": "Modifier les écritures",
    "accounting.entry.validate": "Valider les écritures",
    "accounting.report.read": "Voir les rapports comptables",
    "accounting.report.export": "Exporter les rapports",
    "accounting.closure.execute": "Exécuter les clôtures",
}

DECISION_PERMISSIONS = {
    "decision.classify": "Classifier des décisions",
    "decision.read": "Voir les décisions",
    "decision.validate.red": "Valider les décisions RED",
    "decision.journal.read": "Voir le journal décisions",
}

SALES_PERMISSIONS = {
    "sales.quote.create": "Créer des devis",
    "sales.quote.read": "Voir les devis",
    "sales.quote.update": "Modifier les devis",
    "sales.quote.validate": "Valider les devis",
    "sales.order.create": "Créer des commandes",
    "sales.order.read": "Voir les commandes",
    "sales.order.validate": "Valider les commandes",
    "sales.invoice.create": "Créer des factures",
    "sales.invoice.read": "Voir les factures",
    "sales.invoice.validate": "Valider les factures",
    "sales.customer.create": "Créer des clients",
    "sales.customer.read": "Voir les clients",
    "sales.customer.update": "Modifier les clients",
}

PURCHASE_PERMISSIONS = {
    "purchase.order.create": "Créer des commandes achat",
    "purchase.order.read": "Voir les commandes achat",
    "purchase.order.validate": "Valider les commandes achat",
    "purchase.invoice.create": "Créer des factures achat",
    "purchase.invoice.read": "Voir les factures achat",
    "purchase.invoice.validate": "Valider les factures achat",
    "purchase.supplier.create": "Créer des fournisseurs",
    "purchase.supplier.read": "Voir les fournisseurs",
    "purchase.supplier.update": "Modifier les fournisseurs",
}

STOCK_PERMISSIONS = {
    "stock.item.create": "Créer des articles",
    "stock.item.read": "Voir les articles",
    "stock.item.update": "Modifier les articles",
    "stock.movement.create": "Créer des mouvements stock",
    "stock.movement.read": "Voir les mouvements",
    "stock.inventory.create": "Créer des inventaires",
    "stock.inventory.validate": "Valider les inventaires",
}

ADMIN_PERMISSIONS = {
    "admin.tenant.read": "Voir les informations tenant",
    "admin.tenant.update": "Modifier le tenant",
    "admin.settings.read": "Voir les paramètres",
    "admin.settings.update": "Modifier les paramètres",
    "admin.backup.create": "Créer des sauvegardes",
    "admin.backup.restore": "Restaurer des sauvegardes",
    "admin.module.install": "Installer des modules",
    "admin.module.uninstall": "Désinstaller des modules",
}

TRIGGERS_PERMISSIONS = {
    # Gestion des triggers
    "triggers.create": "Créer des déclencheurs",
    "triggers.read": "Voir les déclencheurs",
    "triggers.update": "Modifier les déclencheurs",
    "triggers.delete": "Supprimer des déclencheurs",
    "triggers.admin": "Administration complète triggers",

    # Abonnements
    "triggers.subscribe": "S'abonner aux déclencheurs",
    "triggers.unsubscribe": "Se désabonner des déclencheurs",

    # Événements
    "triggers.events.read": "Voir les événements",
    "triggers.events.resolve": "Résoudre les événements",
    "triggers.events.escalate": "Escalader les événements",

    # Templates
    "triggers.templates.create": "Créer des templates",
    "triggers.templates.read": "Voir les templates",
    "triggers.templates.update": "Modifier les templates",
    "triggers.templates.delete": "Supprimer des templates",

    # Rapports planifiés
    "triggers.reports.create": "Créer des rapports planifiés",
    "triggers.reports.read": "Voir les rapports planifiés",
    "triggers.reports.update": "Modifier les rapports planifiés",
    "triggers.reports.delete": "Supprimer des rapports planifiés",
    "triggers.reports.generate": "Générer des rapports manuellement",

    # Webhooks
    "triggers.webhooks.create": "Créer des webhooks",
    "triggers.webhooks.read": "Voir les webhooks",
    "triggers.webhooks.update": "Modifier les webhooks",
    "triggers.webhooks.delete": "Supprimer des webhooks",
    "triggers.webhooks.test": "Tester les webhooks",

    # Logs
    "triggers.logs.read": "Voir les logs triggers",
}

AUTOCONFIG_PERMISSIONS = {
    # Profils
    "autoconfig.profiles.create": "Créer des profils",
    "autoconfig.profiles.read": "Voir les profils",
    "autoconfig.profiles.update": "Modifier les profils",
    "autoconfig.profiles.delete": "Supprimer des profils",

    # Assignations
    "autoconfig.assignments.create": "Assigner des profils",
    "autoconfig.assignments.read": "Voir les assignations",
    "autoconfig.assignments.update": "Modifier les assignations",
    "autoconfig.assignments.delete": "Supprimer des assignations",

    # Overrides
    "autoconfig.overrides.create": "Créer des dérogations",
    "autoconfig.overrides.read": "Voir les dérogations",
    "autoconfig.overrides.revoke": "Révoquer des dérogations",

    # Onboarding/Offboarding
    "autoconfig.onboarding.execute": "Exécuter onboarding",
    "autoconfig.offboarding.execute": "Exécuter offboarding",
}

AUDIT_PERMISSIONS = {
    # Logs d'audit
    "audit.logs.read": "Voir les logs d'audit",
    "audit.logs.export": "Exporter les logs d'audit",

    # Sessions
    "audit.sessions.read": "Voir les sessions",
    "audit.sessions.terminate": "Terminer des sessions",

    # Métriques
    "audit.metrics.create": "Créer des métriques",
    "audit.metrics.read": "Voir les métriques",
    "audit.metrics.record": "Enregistrer des métriques",

    # Benchmarks
    "audit.benchmarks.create": "Créer des benchmarks",
    "audit.benchmarks.read": "Voir les benchmarks",
    "audit.benchmarks.execute": "Exécuter des benchmarks",

    # Conformité
    "audit.compliance.create": "Créer des contrôles conformité",
    "audit.compliance.read": "Voir la conformité",
    "audit.compliance.update": "Mettre à jour la conformité",

    # Rétention
    "audit.retention.create": "Créer des règles rétention",
    "audit.retention.read": "Voir les règles rétention",
    "audit.retention.execute": "Exécuter les règles rétention",

    # Exports
    "audit.exports.create": "Créer des exports",
    "audit.exports.read": "Voir les exports",
    "audit.exports.process": "Traiter les exports",

    # Dashboards
    "audit.dashboards.create": "Créer des dashboards",
    "audit.dashboards.read": "Voir les dashboards",
    "audit.dashboards.update": "Modifier les dashboards",
    "audit.dashboards.delete": "Supprimer des dashboards",
}

QC_PERMISSIONS = {
    # Règles QC
    "qc.rules.create": "Créer des règles QC",
    "qc.rules.read": "Voir les règles QC",
    "qc.rules.update": "Modifier les règles QC",
    "qc.rules.delete": "Supprimer des règles QC",

    # Modules
    "qc.modules.create": "Enregistrer des modules",
    "qc.modules.read": "Voir les modules",
    "qc.modules.update": "Modifier les modules",

    # Validations
    "qc.validations.create": "Lancer des validations",
    "qc.validations.read": "Voir les validations",

    # Tests
    "qc.tests.create": "Enregistrer des tests",
    "qc.tests.read": "Voir les tests",

    # Métriques
    "qc.metrics.create": "Enregistrer des métriques QC",
    "qc.metrics.read": "Voir les métriques QC",

    # Alertes
    "qc.alerts.create": "Créer des alertes QC",
    "qc.alerts.read": "Voir les alertes QC",
    "qc.alerts.resolve": "Résoudre les alertes QC",

    # Dashboards
    "qc.dashboards.create": "Créer des dashboards QC",
    "qc.dashboards.read": "Voir les dashboards QC",
    "qc.dashboards.update": "Modifier les dashboards QC",
    "qc.dashboards.delete": "Supprimer des dashboards QC",

    # Templates
    "qc.templates.create": "Créer des templates QC",
    "qc.templates.read": "Voir les templates QC",
    "qc.templates.apply": "Appliquer des templates QC",

    # Stats
    "qc.stats.read": "Voir les statistiques QC",

    # Admin complet
    "qc.admin": "Administration complète QC",
}

COUNTRY_PACKS_PERMISSIONS = {
    # Packs pays
    "country.packs.create": "Créer des packs pays",
    "country.packs.read": "Voir les packs pays",
    "country.packs.update": "Modifier les packs pays",
    "country.packs.delete": "Supprimer des packs pays",
    "country.packs.set_default": "Définir le pack par défaut",

    # Taxes
    "country.taxes.create": "Créer des taux de taxe",
    "country.taxes.read": "Voir les taux de taxe",
    "country.taxes.update": "Modifier les taux de taxe",
    "country.taxes.delete": "Supprimer des taux de taxe",

    # Templates documents
    "country.templates.create": "Créer des templates documents",
    "country.templates.read": "Voir les templates documents",
    "country.templates.update": "Modifier les templates documents",

    # Config bancaire
    "country.bank.create": "Créer des configs bancaires",
    "country.bank.read": "Voir les configs bancaires",
    "country.bank.update": "Modifier les configs bancaires",

    # Jours fériés
    "country.holidays.create": "Créer des jours fériés",
    "country.holidays.read": "Voir les jours fériés",
    "country.holidays.update": "Modifier les jours fériés",
    "country.holidays.delete": "Supprimer des jours fériés",

    # Exigences légales
    "country.legal.create": "Créer des exigences légales",
    "country.legal.read": "Voir les exigences légales",
    "country.legal.update": "Modifier les exigences légales",

    # Paramètres tenant
    "country.tenant.activate": "Activer un pays pour le tenant",
    "country.tenant.read": "Voir les paramètres pays tenant",
    "country.tenant.update": "Modifier les paramètres pays tenant",

    # Utilitaires
    "country.utils.format": "Utiliser les utilitaires de formatage",
    "country.utils.validate": "Utiliser les validations pays",

    # Admin complet
    "country.admin": "Administration complète packs pays",
}

BROADCAST_PERMISSIONS = {
    # Templates
    "broadcast.templates.create": "Créer des templates diffusion",
    "broadcast.templates.read": "Voir les templates diffusion",
    "broadcast.templates.update": "Modifier les templates diffusion",
    "broadcast.templates.delete": "Supprimer des templates diffusion",

    # Listes de destinataires
    "broadcast.lists.create": "Créer des listes destinataires",
    "broadcast.lists.read": "Voir les listes destinataires",
    "broadcast.lists.update": "Modifier les listes destinataires",
    "broadcast.lists.delete": "Supprimer des listes destinataires",

    # Diffusions programmées
    "broadcast.scheduled.create": "Créer des diffusions programmées",
    "broadcast.scheduled.read": "Voir les diffusions programmées",
    "broadcast.scheduled.update": "Modifier les diffusions programmées",
    "broadcast.scheduled.delete": "Supprimer des diffusions programmées",
    "broadcast.scheduled.activate": "Activer/Pause diffusions",
    "broadcast.scheduled.execute": "Exécuter manuellement diffusions",

    # Exécutions
    "broadcast.executions.read": "Voir les exécutions",
    "broadcast.executions.details": "Voir les détails de livraison",

    # Préférences
    "broadcast.preferences.read": "Voir ses préférences",
    "broadcast.preferences.update": "Modifier ses préférences",
    "broadcast.preferences.admin": "Gérer préférences utilisateurs",

    # Métriques
    "broadcast.metrics.read": "Voir les métriques diffusion",
    "broadcast.metrics.record": "Enregistrer des métriques",

    # Dashboard
    "broadcast.dashboard.read": "Voir le dashboard diffusion",

    # Admin complet
    "broadcast.admin": "Administration complète diffusion",
}

WEB_PERMISSIONS = {
    # Thèmes
    "web.themes.create": "Créer des thèmes",
    "web.themes.read": "Voir les thèmes",
    "web.themes.update": "Modifier les thèmes",
    "web.themes.delete": "Supprimer des thèmes",
    "web.themes.set_default": "Définir le thème par défaut",

    # Widgets
    "web.widgets.create": "Créer des widgets",
    "web.widgets.read": "Voir les widgets",
    "web.widgets.update": "Modifier les widgets",
    "web.widgets.delete": "Supprimer des widgets",

    # Dashboards
    "web.dashboards.create": "Créer des dashboards",
    "web.dashboards.read": "Voir les dashboards",
    "web.dashboards.update": "Modifier les dashboards",
    "web.dashboards.delete": "Supprimer des dashboards",
    "web.dashboards.set_default": "Définir le dashboard par défaut",

    # Menus
    "web.menus.create": "Créer des éléments de menu",
    "web.menus.read": "Voir les menus",
    "web.menus.update": "Modifier les menus",
    "web.menus.delete": "Supprimer des menus",

    # Préférences UI
    "web.preferences.read": "Voir ses préférences UI",
    "web.preferences.update": "Modifier ses préférences UI",
    "web.preferences.admin": "Gérer préférences UI utilisateurs",

    # Raccourcis
    "web.shortcuts.create": "Créer des raccourcis clavier",
    "web.shortcuts.read": "Voir les raccourcis clavier",

    # Pages personnalisées
    "web.pages.create": "Créer des pages personnalisées",
    "web.pages.read": "Voir les pages personnalisées",
    "web.pages.update": "Modifier les pages personnalisées",
    "web.pages.publish": "Publier des pages",

    # Composants UI
    "web.components.create": "Créer des composants UI",
    "web.components.read": "Voir les composants UI",

    # Configuration UI complète
    "web.config.read": "Voir la configuration UI complète",

    # Admin complet
    "web.admin": "Administration complète web UI",
}

WEBSITE_PERMISSIONS = {
    # Pages du site
    "website.pages.create": "Créer des pages du site",
    "website.pages.read": "Voir les pages du site",
    "website.pages.update": "Modifier les pages du site",
    "website.pages.delete": "Supprimer des pages du site",
    "website.pages.publish": "Publier des pages du site",

    # Blog
    "website.blog.create": "Créer des articles de blog",
    "website.blog.read": "Voir les articles de blog",
    "website.blog.update": "Modifier les articles de blog",
    "website.blog.delete": "Supprimer des articles de blog",
    "website.blog.publish": "Publier des articles de blog",

    # Témoignages
    "website.testimonials.create": "Créer des témoignages",
    "website.testimonials.read": "Voir les témoignages",
    "website.testimonials.update": "Modifier les témoignages",
    "website.testimonials.delete": "Supprimer des témoignages",
    "website.testimonials.publish": "Publier des témoignages",

    # Contact
    "website.contact.read": "Voir les soumissions de contact",
    "website.contact.update": "Modifier les soumissions de contact",
    "website.contact.respond": "Répondre aux soumissions",
    "website.contact.stats": "Voir les statistiques contact",

    # Newsletter
    "website.newsletter.read": "Voir les abonnés newsletter",
    "website.newsletter.manage": "Gérer les abonnements newsletter",
    "website.newsletter.stats": "Voir les statistiques newsletter",

    # Média
    "website.media.create": "Uploader des médias",
    "website.media.read": "Voir les médias",
    "website.media.update": "Modifier les médias",
    "website.media.delete": "Supprimer des médias",

    # SEO
    "website.seo.read": "Voir la configuration SEO",
    "website.seo.update": "Modifier la configuration SEO",

    # Analytics
    "website.analytics.read": "Voir les analytics du site",
    "website.analytics.record": "Enregistrer des données analytics",

    # Config publique
    "website.config.read": "Voir la configuration du site",

    # Admin complet
    "website.admin": "Administration complète site web",
}

TENANTS_PERMISSIONS = {
    # Tenants
    "tenants.create": "Créer des tenants",
    "tenants.read": "Voir les tenants",
    "tenants.update": "Modifier les tenants",
    "tenants.delete": "Supprimer des tenants",
    "tenants.activate": "Activer des tenants",
    "tenants.suspend": "Suspendre des tenants",
    "tenants.cancel": "Annuler des tenants",

    # Abonnements
    "tenants.subscriptions.create": "Créer des abonnements",
    "tenants.subscriptions.read": "Voir les abonnements",
    "tenants.subscriptions.update": "Modifier les abonnements",

    # Modules tenant
    "tenants.modules.read": "Voir les modules du tenant",
    "tenants.modules.activate": "Activer des modules",
    "tenants.modules.deactivate": "Désactiver des modules",
    "tenants.modules.configure": "Configurer des modules",

    # Invitations
    "tenants.invitations.create": "Créer des invitations tenant",
    "tenants.invitations.read": "Voir les invitations tenant",
    "tenants.invitations.accept": "Accepter des invitations",
    "tenants.invitations.revoke": "Révoquer des invitations",

    # Usage
    "tenants.usage.read": "Voir l'usage du tenant",
    "tenants.usage.record": "Enregistrer l'usage",

    # Événements
    "tenants.events.read": "Voir les événements tenant",
    "tenants.events.log": "Logger des événements",

    # Settings
    "tenants.settings.read": "Voir les paramètres tenant",
    "tenants.settings.update": "Modifier les paramètres tenant",

    # Onboarding
    "tenants.onboarding.read": "Voir l'onboarding",
    "tenants.onboarding.update": "Modifier l'onboarding",
    "tenants.onboarding.complete": "Compléter l'onboarding",

    # Provisioning
    "tenants.provision": "Provisionner des tenants",

    # Admin complet
    "tenants.admin": "Administration complète tenants",
}

COMMERCIAL_PERMISSIONS = {
    # Clients
    "commercial.customers.create": "Créer des clients",
    "commercial.customers.read": "Voir les clients",
    "commercial.customers.update": "Modifier les clients",
    "commercial.customers.delete": "Supprimer des clients",
    "commercial.customers.convert": "Convertir des prospects",

    # Contacts
    "commercial.contacts.create": "Créer des contacts",
    "commercial.contacts.read": "Voir les contacts",
    "commercial.contacts.update": "Modifier les contacts",
    "commercial.contacts.delete": "Supprimer des contacts",

    # Opportunités
    "commercial.opportunities.create": "Créer des opportunités",
    "commercial.opportunities.read": "Voir les opportunités",
    "commercial.opportunities.update": "Modifier les opportunités",
    "commercial.opportunities.win": "Marquer comme gagnée",
    "commercial.opportunities.lose": "Marquer comme perdue",

    # Documents
    "commercial.documents.create": "Créer des documents commerciaux",
    "commercial.documents.read": "Voir les documents commerciaux",
    "commercial.documents.update": "Modifier les documents",
    "commercial.documents.validate": "Valider les documents",
    "commercial.documents.send": "Envoyer les documents",
    "commercial.documents.convert": "Convertir devis en commande",

    # Paiements
    "commercial.payments.create": "Enregistrer des paiements",
    "commercial.payments.read": "Voir les paiements",

    # Activités
    "commercial.activities.create": "Créer des activités",
    "commercial.activities.read": "Voir les activités",
    "commercial.activities.complete": "Compléter des activités",

    # Pipeline
    "commercial.pipeline.create": "Créer des étapes pipeline",
    "commercial.pipeline.read": "Voir le pipeline",
    "commercial.pipeline.update": "Modifier le pipeline",

    # Produits
    "commercial.products.create": "Créer des produits",
    "commercial.products.read": "Voir les produits",
    "commercial.products.update": "Modifier les produits",

    # Dashboard
    "commercial.dashboard.read": "Voir le dashboard commercial",

    # Admin complet
    "commercial.admin": "Administration complète commercial",
}

# ============================================================================
# AGRÉGATION DE TOUTES LES PERMISSIONS
# ============================================================================

ALL_PERMISSIONS: Dict[str, str] = {
    **IAM_PERMISSIONS,
    **TREASURY_PERMISSIONS,
    **LEGAL_PERMISSIONS,
    **TAX_PERMISSIONS,
    **HR_PERMISSIONS,
    **ACCOUNTING_PERMISSIONS,
    **DECISION_PERMISSIONS,
    **SALES_PERMISSIONS,
    **PURCHASE_PERMISSIONS,
    **STOCK_PERMISSIONS,
    **ADMIN_PERMISSIONS,
    **TRIGGERS_PERMISSIONS,
    **AUTOCONFIG_PERMISSIONS,
    **AUDIT_PERMISSIONS,
    **QC_PERMISSIONS,
    **COUNTRY_PACKS_PERMISSIONS,
    **BROADCAST_PERMISSIONS,
    **WEB_PERMISSIONS,
    **WEBSITE_PERMISSIONS,
    **TENANTS_PERMISSIONS,
    **COMMERCIAL_PERMISSIONS,
}


# ============================================================================
# RÔLES PRÉDÉFINIS ET LEURS PERMISSIONS
# ============================================================================

ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "SUPER_ADMIN": ["*"],  # Toutes les permissions

    "TENANT_ADMIN": [
        "iam.*",
        "admin.*",
        "triggers.*",
        "autoconfig.*",
        "qc.*",
        "country.*",
        "broadcast.*",
        "web.*",
        "website.*",
        "tenants.*",
        "commercial.*",
    ],

    "DIRIGEANT": [
        "iam.user.read",
        "iam.role.read",
        "iam.group.read",
        "iam.audit.read",
        "treasury.*",
        "legal.*",
        "tax.*",
        "hr.employee.read",
        "hr.payroll.read",
        "accounting.*",
        "decision.*",
        "sales.*",
        "purchase.*",
        "stock.*",
        "admin.tenant.read",
        "admin.settings.read",
        "triggers.*",
        "autoconfig.*",
        "qc.validations.read",
        "qc.modules.read",
        "qc.stats.read",
        "qc.dashboards.read",
        "country.packs.read",
        "country.taxes.read",
        "country.holidays.read",
        "country.tenant.read",
        "broadcast.scheduled.read",
        "broadcast.executions.read",
        "broadcast.metrics.read",
        "broadcast.dashboard.read",
        "web.themes.read",
        "web.widgets.read",
        "web.dashboards.read",
        "web.menus.read",
        "web.preferences.read",
        "web.preferences.update",
        "web.shortcuts.read",
        "web.pages.read",
        "web.config.read",
        "website.pages.read",
        "website.blog.read",
        "website.testimonials.read",
        "website.contact.stats",
        "website.newsletter.stats",
        "website.analytics.read",
        "website.config.read",
        "tenants.read",
        "tenants.subscriptions.read",
        "tenants.modules.read",
        "tenants.usage.read",
        "tenants.events.read",
        "tenants.settings.read",
        "tenants.onboarding.read",
        "commercial.customers.read",
        "commercial.contacts.read",
        "commercial.opportunities.read",
        "commercial.documents.read",
        "commercial.payments.read",
        "commercial.activities.read",
        "commercial.pipeline.read",
        "commercial.products.read",
        "commercial.dashboard.read",
    ],

    "DAF": [
        "treasury.*",
        "accounting.*",
        "tax.*",
        "sales.invoice.read",
        "sales.invoice.validate",
        "purchase.invoice.read",
        "purchase.invoice.validate",
        "decision.read",
        "decision.classify",
        "triggers.read",
        "triggers.events.read",
        "triggers.events.resolve",
        "triggers.reports.read",
        "triggers.reports.generate",
        "country.packs.read",
        "country.taxes.read",
        "country.bank.read",
        "country.legal.read",
        "country.utils.format",
    ],

    "DRH": [
        "hr.*",
        "iam.user.read",
        "iam.invitation.create",
        "decision.read",
    ],

    "RESPONSABLE_COMMERCIAL": [
        "sales.*",
        "stock.item.read",
        "stock.movement.read",
        "decision.read",
    ],

    "RESPONSABLE_ACHATS": [
        "purchase.*",
        "stock.item.read",
        "stock.movement.read",
        "decision.read",
    ],

    "RESPONSABLE_PRODUCTION": [
        "stock.*",
        "purchase.order.read",
        "decision.read",
    ],

    "COMPTABLE": [
        "accounting.entry.create",
        "accounting.entry.read",
        "accounting.entry.update",
        "accounting.report.read",
        "sales.invoice.read",
        "purchase.invoice.read",
        "treasury.forecast.read",
        "treasury.report.read",
    ],

    "COMMERCIAL": [
        "sales.quote.create",
        "sales.quote.read",
        "sales.quote.update",
        "sales.order.create",
        "sales.order.read",
        "sales.customer.create",
        "sales.customer.read",
        "sales.customer.update",
        "stock.item.read",
    ],

    "ACHETEUR": [
        "purchase.order.create",
        "purchase.order.read",
        "purchase.supplier.create",
        "purchase.supplier.read",
        "purchase.supplier.update",
        "stock.item.read",
    ],

    "MAGASINIER": [
        "stock.item.read",
        "stock.movement.create",
        "stock.movement.read",
        "stock.inventory.create",
    ],

    "RH": [
        "hr.employee.read",
        "hr.employee.update",
        "hr.leave.create",
        "hr.leave.read",
    ],

    "CONSULTANT": [
        "treasury.forecast.read",
        "treasury.report.read",
        "accounting.report.read",
        "sales.quote.read",
        "sales.order.read",
        "sales.invoice.read",
        "purchase.order.read",
        "purchase.invoice.read",
        "stock.item.read",
    ],

    "AUDITEUR": [
        "iam.audit.read",
        "iam.audit.export",
        "accounting.entry.read",
        "accounting.report.read",
        "accounting.report.export",
        "treasury.report.read",
        "treasury.report.export",
        "decision.journal.read",
    ],
}


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_permissions_for_role(role_code: str) -> List[str]:
    """Retourne les permissions pour un rôle."""
    if role_code not in ROLE_PERMISSIONS:
        return []

    permissions = []
    for perm in ROLE_PERMISSIONS[role_code]:
        if perm == "*":
            # Toutes les permissions
            permissions.extend(ALL_PERMISSIONS.keys())
        elif perm.endswith(".*"):
            # Wildcard module
            module = perm[:-2]
            permissions.extend([p for p in ALL_PERMISSIONS.keys() if p.startswith(f"{module}.")])
        else:
            permissions.append(perm)

    return list(set(permissions))


def get_modules() -> List[str]:
    """Retourne la liste des modules."""
    modules = set()
    for perm in ALL_PERMISSIONS.keys():
        module = perm.split(".")[0]
        modules.add(module)
    return sorted(list(modules))


def get_permissions_by_module(module: str) -> Dict[str, str]:
    """Retourne les permissions d'un module."""
    return {
        code: desc for code, desc in ALL_PERMISSIONS.items()
        if code.startswith(f"{module}.")
    }
