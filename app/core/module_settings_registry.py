"""
AZALSCORE - Registre des Paramètres par Module
===============================================

Définit les paramètres configurables pour chaque module.
Chaque module peut avoir ses propres paramètres avec:
- Type de données (string, number, boolean, select, json)
- Valeur par défaut
- Validation
- Groupes de paramètres

Utilisation:
- Backend: from app.core.module_settings_registry import get_module_settings_schema
- Frontend: GET /api/v1/settings/modules/{module_code}/schema
"""

from typing import Any
from enum import Enum


class SettingType(str, Enum):
    """Types de paramètres supportés."""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTISELECT = "multiselect"
    JSON = "json"
    DATE = "date"
    EMAIL = "email"
    URL = "url"
    PASSWORD = "password"
    COLOR = "color"


class SettingCategory(str, Enum):
    """Catégories de paramètres."""
    GENERAL = "general"
    DISPLAY = "display"
    NOTIFICATIONS = "notifications"
    INTEGRATION = "integration"
    SECURITY = "security"
    ADVANCED = "advanced"


# =============================================================================
# DÉFINITIONS DES PARAMÈTRES PAR MODULE
# =============================================================================

MODULE_SETTINGS: dict[str, dict] = {
    # -------------------------------------------------------------------------
    # MODULE: FACTURATION (invoicing)
    # -------------------------------------------------------------------------
    "invoicing": {
        "name": "Facturation",
        "description": "Paramètres du module de facturation",
        "settings": [
            {
                "key": "invoice_prefix",
                "label": "Préfixe des factures",
                "type": SettingType.STRING,
                "default": "FACT-",
                "category": SettingCategory.GENERAL,
                "description": "Préfixe ajouté au numéro de facture",
                "placeholder": "FACT-",
                "max_length": 10,
            },
            {
                "key": "invoice_start_number",
                "label": "Numéro de départ",
                "type": SettingType.INTEGER,
                "default": 1,
                "category": SettingCategory.GENERAL,
                "description": "Numéro de la première facture",
                "min": 1,
                "max": 999999,
            },
            {
                "key": "default_payment_terms",
                "label": "Conditions de paiement par défaut",
                "type": SettingType.SELECT,
                "default": "NET_30",
                "category": SettingCategory.GENERAL,
                "options": [
                    {"value": "IMMEDIATE", "label": "Paiement immédiat"},
                    {"value": "NET_15", "label": "Net 15 jours"},
                    {"value": "NET_30", "label": "Net 30 jours"},
                    {"value": "NET_45", "label": "Net 45 jours"},
                    {"value": "NET_60", "label": "Net 60 jours"},
                    {"value": "END_OF_MONTH", "label": "Fin de mois"},
                ],
            },
            {
                "key": "default_vat_rate",
                "label": "Taux de TVA par défaut",
                "type": SettingType.SELECT,
                "default": "20",
                "category": SettingCategory.GENERAL,
                "options": [
                    {"value": "20", "label": "20% (taux normal)"},
                    {"value": "10", "label": "10% (taux intermédiaire)"},
                    {"value": "5.5", "label": "5,5% (taux réduit)"},
                    {"value": "2.1", "label": "2,1% (taux super-réduit)"},
                    {"value": "0", "label": "0% (exonéré)"},
                ],
            },
            {
                "key": "auto_send_invoice",
                "label": "Envoi automatique par email",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.NOTIFICATIONS,
                "description": "Envoyer automatiquement la facture au client",
            },
            {
                "key": "reminder_enabled",
                "label": "Relances automatiques",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.NOTIFICATIONS,
                "description": "Envoyer des rappels pour les factures impayées",
            },
            {
                "key": "reminder_days",
                "label": "Délai avant relance (jours)",
                "type": SettingType.INTEGER,
                "default": 7,
                "category": SettingCategory.NOTIFICATIONS,
                "min": 1,
                "max": 90,
                "depends_on": {"key": "reminder_enabled", "value": True},
            },
            {
                "key": "invoice_footer",
                "label": "Pied de page personnalisé",
                "type": SettingType.STRING,
                "default": "",
                "category": SettingCategory.DISPLAY,
                "description": "Texte affiché en bas de chaque facture",
                "multiline": True,
                "max_length": 500,
            },
            {
                "key": "show_discount_column",
                "label": "Afficher colonne remise",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.DISPLAY,
            },
            {
                "key": "decimal_places",
                "label": "Décimales pour les prix",
                "type": SettingType.SELECT,
                "default": "2",
                "category": SettingCategory.DISPLAY,
                "options": [
                    {"value": "2", "label": "2 décimales"},
                    {"value": "3", "label": "3 décimales"},
                    {"value": "4", "label": "4 décimales"},
                ],
            },
        ],
    },

    # -------------------------------------------------------------------------
    # MODULE: E-INVOICING FRANCE (einvoicing)
    # -------------------------------------------------------------------------
    "einvoicing": {
        "name": "Facturation Électronique France",
        "description": "Paramètres e-invoicing France 2026",
        "settings": [
            {
                "key": "default_format",
                "label": "Format par défaut",
                "type": SettingType.SELECT,
                "default": "FACTURX_EN16931",
                "category": SettingCategory.GENERAL,
                "options": [
                    {"value": "FACTURX_MINIMUM", "label": "Factur-X Minimum"},
                    {"value": "FACTURX_BASIC", "label": "Factur-X Basic"},
                    {"value": "FACTURX_EN16931", "label": "Factur-X EN16931 (recommandé)"},
                    {"value": "FACTURX_EXTENDED", "label": "Factur-X Extended"},
                    {"value": "UBL_21", "label": "UBL 2.1"},
                ],
            },
            {
                "key": "auto_submit",
                "label": "Soumission automatique au PDP",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.GENERAL,
                "description": "Soumettre automatiquement les factures validées",
            },
            {
                "key": "auto_validate",
                "label": "Validation automatique",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
                "description": "Valider automatiquement le XML à la création",
            },
            {
                "key": "generate_pdf",
                "label": "Générer PDF Factur-X",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
                "description": "Générer automatiquement le PDF avec XML embarqué",
            },
            {
                "key": "webhook_notifications",
                "label": "Notifications webhook activées",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.NOTIFICATIONS,
            },
            {
                "key": "notify_on_received",
                "label": "Notifier à la réception",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.NOTIFICATIONS,
                "description": "Notification quand une facture entrante est reçue",
            },
            {
                "key": "notify_on_status_change",
                "label": "Notifier au changement de statut",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.NOTIFICATIONS,
            },
            {
                "key": "auto_accept_inbound",
                "label": "Acceptation automatique",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.ADVANCED,
                "description": "Accepter automatiquement les factures entrantes valides",
            },
            {
                "key": "retention_days",
                "label": "Durée de conservation (jours)",
                "type": SettingType.INTEGER,
                "default": 3650,
                "category": SettingCategory.ADVANCED,
                "description": "Durée légale: 10 ans minimum",
                "min": 3650,
                "max": 7300,
            },
        ],
    },

    # -------------------------------------------------------------------------
    # MODULE: PAIEMENTS (payments)
    # -------------------------------------------------------------------------
    "payments": {
        "name": "Paiements",
        "description": "Paramètres de gestion des paiements",
        "settings": [
            {
                "key": "default_payment_method",
                "label": "Mode de paiement par défaut",
                "type": SettingType.SELECT,
                "default": "virement",
                "category": SettingCategory.GENERAL,
                "options": [
                    {"value": "virement", "label": "Virement bancaire"},
                    {"value": "carte", "label": "Carte bancaire"},
                    {"value": "prelevement", "label": "Prélèvement"},
                    {"value": "cheque", "label": "Chèque"},
                    {"value": "especes", "label": "Espèces"},
                ],
            },
            {
                "key": "auto_reconcile",
                "label": "Rapprochement automatique",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
                "description": "Rapprocher automatiquement les paiements reçus",
            },
            {
                "key": "partial_payment_allowed",
                "label": "Paiements partiels autorisés",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
            },
            {
                "key": "late_fee_enabled",
                "label": "Pénalités de retard",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
            },
            {
                "key": "late_fee_rate",
                "label": "Taux de pénalité (%)",
                "type": SettingType.NUMBER,
                "default": 10,
                "category": SettingCategory.GENERAL,
                "min": 0,
                "max": 20,
                "step": 0.5,
                "depends_on": {"key": "late_fee_enabled", "value": True},
            },
        ],
    },

    # -------------------------------------------------------------------------
    # MODULE: CRM/CLIENTS (partners)
    # -------------------------------------------------------------------------
    "partners": {
        "name": "CRM / Clients",
        "description": "Paramètres de gestion des clients",
        "settings": [
            {
                "key": "client_code_prefix",
                "label": "Préfixe code client",
                "type": SettingType.STRING,
                "default": "CLI-",
                "category": SettingCategory.GENERAL,
                "max_length": 10,
            },
            {
                "key": "auto_generate_code",
                "label": "Génération automatique du code",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
            },
            {
                "key": "require_siret",
                "label": "SIRET obligatoire",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.GENERAL,
                "description": "Exiger le SIRET pour les clients professionnels",
            },
            {
                "key": "duplicate_check",
                "label": "Vérification des doublons",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
            },
            {
                "key": "duplicate_fields",
                "label": "Champs de détection doublons",
                "type": SettingType.MULTISELECT,
                "default": ["email", "siret"],
                "category": SettingCategory.GENERAL,
                "options": [
                    {"value": "email", "label": "Email"},
                    {"value": "siret", "label": "SIRET"},
                    {"value": "phone", "label": "Téléphone"},
                    {"value": "name", "label": "Nom"},
                ],
                "depends_on": {"key": "duplicate_check", "value": True},
            },
        ],
    },

    # -------------------------------------------------------------------------
    # MODULE: STOCK (inventory)
    # -------------------------------------------------------------------------
    "inventory": {
        "name": "Stock",
        "description": "Paramètres de gestion des stocks",
        "settings": [
            {
                "key": "stock_valuation_method",
                "label": "Méthode de valorisation",
                "type": SettingType.SELECT,
                "default": "FIFO",
                "category": SettingCategory.GENERAL,
                "options": [
                    {"value": "FIFO", "label": "FIFO (Premier entré, premier sorti)"},
                    {"value": "LIFO", "label": "LIFO (Dernier entré, premier sorti)"},
                    {"value": "CUMP", "label": "CUMP (Coût unitaire moyen pondéré)"},
                ],
            },
            {
                "key": "low_stock_threshold",
                "label": "Seuil stock bas (%)",
                "type": SettingType.INTEGER,
                "default": 20,
                "category": SettingCategory.NOTIFICATIONS,
                "min": 5,
                "max": 50,
            },
            {
                "key": "alert_low_stock",
                "label": "Alertes stock bas",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.NOTIFICATIONS,
            },
            {
                "key": "auto_reorder",
                "label": "Réapprovisionnement automatique",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.ADVANCED,
            },
            {
                "key": "negative_stock_allowed",
                "label": "Stock négatif autorisé",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.ADVANCED,
            },
            {
                "key": "serial_tracking",
                "label": "Suivi par numéro de série",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.ADVANCED,
            },
            {
                "key": "lot_tracking",
                "label": "Suivi par lot",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.ADVANCED,
            },
        ],
    },

    # -------------------------------------------------------------------------
    # MODULE: ACHATS (purchases)
    # -------------------------------------------------------------------------
    "purchases": {
        "name": "Achats",
        "description": "Paramètres des achats fournisseurs",
        "settings": [
            {
                "key": "po_prefix",
                "label": "Préfixe commandes",
                "type": SettingType.STRING,
                "default": "PO-",
                "category": SettingCategory.GENERAL,
                "max_length": 10,
            },
            {
                "key": "approval_required",
                "label": "Validation requise",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
                "description": "Exiger une validation avant envoi au fournisseur",
            },
            {
                "key": "approval_threshold",
                "label": "Seuil de validation (€)",
                "type": SettingType.NUMBER,
                "default": 1000,
                "category": SettingCategory.GENERAL,
                "min": 0,
                "step": 100,
                "depends_on": {"key": "approval_required", "value": True},
            },
            {
                "key": "auto_receive",
                "label": "Réception automatique",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.ADVANCED,
            },
            {
                "key": "three_way_match",
                "label": "Rapprochement 3 voies",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.ADVANCED,
                "description": "BC / BL / Facture",
            },
        ],
    },

    # -------------------------------------------------------------------------
    # MODULE: RH (hr)
    # -------------------------------------------------------------------------
    "hr": {
        "name": "Ressources Humaines",
        "description": "Paramètres RH",
        "settings": [
            {
                "key": "employee_code_prefix",
                "label": "Préfixe matricule",
                "type": SettingType.STRING,
                "default": "EMP-",
                "category": SettingCategory.GENERAL,
                "max_length": 10,
            },
            {
                "key": "work_hours_per_week",
                "label": "Heures hebdomadaires",
                "type": SettingType.NUMBER,
                "default": 35,
                "category": SettingCategory.GENERAL,
                "min": 1,
                "max": 48,
            },
            {
                "key": "leave_approval_required",
                "label": "Validation congés requise",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
            },
            {
                "key": "timesheet_required",
                "label": "Feuilles de temps obligatoires",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.GENERAL,
            },
            {
                "key": "dsn_auto_generate",
                "label": "Génération DSN automatique",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.INTEGRATION,
            },
        ],
    },

    # -------------------------------------------------------------------------
    # MODULE: COMPTABILITÉ (accounting)
    # -------------------------------------------------------------------------
    "accounting": {
        "name": "Comptabilité",
        "description": "Paramètres comptables",
        "settings": [
            {
                "key": "fiscal_year_start",
                "label": "Début exercice fiscal",
                "type": SettingType.SELECT,
                "default": "01",
                "category": SettingCategory.GENERAL,
                "options": [
                    {"value": "01", "label": "Janvier"},
                    {"value": "04", "label": "Avril"},
                    {"value": "07", "label": "Juillet"},
                    {"value": "10", "label": "Octobre"},
                ],
            },
            {
                "key": "chart_of_accounts",
                "label": "Plan comptable",
                "type": SettingType.SELECT,
                "default": "PCG_2024",
                "category": SettingCategory.GENERAL,
                "options": [
                    {"value": "PCG_2024", "label": "PCG 2024 (France)"},
                    {"value": "PCG_ASSOC", "label": "PCG Associations"},
                    {"value": "SYSCOHADA", "label": "SYSCOHADA (Afrique)"},
                ],
            },
            {
                "key": "auto_journal_entries",
                "label": "Écritures automatiques",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
                "description": "Générer automatiquement les écritures depuis les factures",
            },
            {
                "key": "require_cost_center",
                "label": "Centre de coût obligatoire",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.ADVANCED,
            },
            {
                "key": "fec_auto_export",
                "label": "Export FEC automatique",
                "type": SettingType.BOOLEAN,
                "default": False,
                "category": SettingCategory.INTEGRATION,
            },
        ],
    },

    # -------------------------------------------------------------------------
    # MODULE: PROJETS (projects)
    # -------------------------------------------------------------------------
    "projects": {
        "name": "Projets / Affaires",
        "description": "Paramètres de gestion de projets",
        "settings": [
            {
                "key": "project_code_prefix",
                "label": "Préfixe projets",
                "type": SettingType.STRING,
                "default": "PRJ-",
                "category": SettingCategory.GENERAL,
                "max_length": 10,
            },
            {
                "key": "default_billing_type",
                "label": "Type de facturation par défaut",
                "type": SettingType.SELECT,
                "default": "fixed",
                "category": SettingCategory.GENERAL,
                "options": [
                    {"value": "fixed", "label": "Forfait"},
                    {"value": "time", "label": "Régie (temps passé)"},
                    {"value": "milestone", "label": "Jalons"},
                ],
            },
            {
                "key": "track_time",
                "label": "Suivi du temps",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
            },
            {
                "key": "track_expenses",
                "label": "Suivi des dépenses",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.GENERAL,
            },
            {
                "key": "budget_alerts",
                "label": "Alertes budget",
                "type": SettingType.BOOLEAN,
                "default": True,
                "category": SettingCategory.NOTIFICATIONS,
            },
            {
                "key": "budget_threshold",
                "label": "Seuil alerte budget (%)",
                "type": SettingType.INTEGER,
                "default": 80,
                "category": SettingCategory.NOTIFICATIONS,
                "min": 50,
                "max": 100,
                "depends_on": {"key": "budget_alerts", "value": True},
            },
        ],
    },
}


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def get_module_settings_schema(module_code: str) -> dict | None:
    """
    Retourne le schéma de paramètres pour un module.

    Args:
        module_code: Code du module (ex: "invoicing")

    Returns:
        Schéma des paramètres ou None si non trouvé
    """
    return MODULE_SETTINGS.get(module_code)


def get_module_settings_defaults(module_code: str) -> dict[str, Any]:
    """
    Retourne les valeurs par défaut pour un module.

    Args:
        module_code: Code du module

    Returns:
        Dictionnaire des valeurs par défaut
    """
    schema = MODULE_SETTINGS.get(module_code)
    if not schema:
        return {}

    defaults = {}
    for setting in schema.get("settings", []):
        defaults[setting["key"]] = setting.get("default")

    return defaults


def get_all_module_settings() -> dict[str, dict]:
    """Retourne tous les schémas de paramètres."""
    return MODULE_SETTINGS


def get_modules_with_settings() -> list[str]:
    """Retourne la liste des modules ayant des paramètres configurables."""
    return list(MODULE_SETTINGS.keys())


def validate_module_setting(
    module_code: str,
    key: str,
    value: Any
) -> tuple[bool, str | None]:
    """
    Valide une valeur de paramètre.

    Returns:
        (is_valid, error_message)
    """
    schema = MODULE_SETTINGS.get(module_code)
    if not schema:
        return False, f"Module '{module_code}' non trouvé"

    setting = next(
        (s for s in schema.get("settings", []) if s["key"] == key),
        None
    )
    if not setting:
        return False, f"Paramètre '{key}' non trouvé pour le module '{module_code}'"

    setting_type = setting.get("type")

    # Validation par type
    if setting_type == SettingType.STRING:
        if not isinstance(value, str):
            return False, f"'{key}' doit être une chaîne de caractères"
        max_len = setting.get("max_length")
        if max_len and len(value) > max_len:
            return False, f"'{key}' ne doit pas dépasser {max_len} caractères"

    elif setting_type in (SettingType.NUMBER, SettingType.INTEGER):
        if not isinstance(value, (int, float)):
            return False, f"'{key}' doit être un nombre"
        min_val = setting.get("min")
        max_val = setting.get("max")
        if min_val is not None and value < min_val:
            return False, f"'{key}' doit être >= {min_val}"
        if max_val is not None and value > max_val:
            return False, f"'{key}' doit être <= {max_val}"

    elif setting_type == SettingType.BOOLEAN:
        if not isinstance(value, bool):
            return False, f"'{key}' doit être un booléen"

    elif setting_type == SettingType.SELECT:
        options = [opt["value"] for opt in setting.get("options", [])]
        if value not in options:
            return False, f"'{key}' doit être parmi: {', '.join(options)}"

    elif setting_type == SettingType.MULTISELECT:
        if not isinstance(value, list):
            return False, f"'{key}' doit être une liste"
        options = [opt["value"] for opt in setting.get("options", [])]
        for v in value:
            if v not in options:
                return False, f"Valeur '{v}' invalide pour '{key}'"

    return True, None


def validate_module_settings(
    module_code: str,
    settings: dict[str, Any]
) -> tuple[bool, list[str]]:
    """
    Valide un ensemble de paramètres pour un module.

    Returns:
        (is_valid, list of errors)
    """
    errors = []

    for key, value in settings.items():
        is_valid, error = validate_module_setting(module_code, key, value)
        if not is_valid:
            errors.append(error)

    return len(errors) == 0, errors


def merge_with_defaults(
    module_code: str,
    user_settings: dict[str, Any]
) -> dict[str, Any]:
    """
    Fusionne les paramètres utilisateur avec les valeurs par défaut.
    """
    defaults = get_module_settings_defaults(module_code)
    return {**defaults, **user_settings}
