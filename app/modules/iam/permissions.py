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
