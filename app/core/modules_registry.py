"""
AZALSCORE - Registre Central des Modules (Auto-généré)
======================================================
SOURCE UNIQUE DE VERITE pour tous les modules disponibles.

Les modules sont découverts automatiquement depuis:
- app/modules/ (modules backend)

Les métadonnées sont lues depuis __init__.py de chaque module:
- __module_code__ : Code du module
- __module_name__ : Nom affiché
- __module_description__ : Description (optionnel)
- __module_category__ : Catégorie (metier/technique/import)
- __module_icon__ : Icône lucide (optionnel)
- __enabled_by_default__ : Actif par défaut (optionnel)

Utilisation:
- Backend: from app.core.modules_registry import MODULES, get_module
- Frontend: GET /api/v1/admin/modules/available
"""

import os
import importlib
import importlib.util
import logging
from typing import List, Dict, Optional
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ModuleCategory(str, Enum):
    """Categories de modules"""
    METIER = "Metier"
    TECHNIQUE = "Technique"
    IMPORT = "Import de Donnees"


# =============================================================================
# CONFIGURATION MANUELLE DES METADONNEES (override si pas dans __init__.py)
# =============================================================================

MODULE_METADATA_OVERRIDES: Dict[str, Dict] = {
    # Format: "module_folder_name": { "name": "...", "description": "...", ... }

    # Modules métier
    "accounting": {"name": "Comptabilité", "description": "Comptabilité générale", "category": "Metier", "icon": "book"},
    "invoicing": {"name": "Facturation", "description": "Devis, commandes, factures", "category": "Metier", "icon": "file-text", "enabled_by_default": True},
    "treasury": {"name": "Trésorerie", "description": "Gestion de trésorerie", "category": "Metier", "icon": "dollar-sign", "enabled_by_default": True},
    "partners": {"name": "CRM/Clients", "description": "Gestion relation client", "category": "Metier", "icon": "users", "enabled_by_default": True},
    "payments": {"name": "Paiements", "description": "Gestion des paiements", "category": "Metier", "icon": "credit-card", "enabled_by_default": True},
    "projects": {"name": "Projets/Affaires", "description": "Suivi des projets et affaires", "category": "Metier", "icon": "briefcase"},
    "inventory": {"name": "Stock", "description": "Gestion des stocks", "category": "Metier", "icon": "package"},
    "purchases": {"name": "Achats", "description": "Commandes fournisseurs", "category": "Metier", "icon": "shopping-cart"},
    "hr": {"name": "RH", "description": "Ressources humaines", "category": "Metier", "icon": "user"},
    "production": {"name": "Production", "description": "Gestion de production", "category": "Metier", "icon": "settings"},
    "maintenance": {"name": "Maintenance", "description": "GMAO", "category": "Metier", "icon": "tool"},
    "quality": {"name": "Qualité", "description": "Contrôle qualité", "category": "Metier", "icon": "check-circle"},
    "pos": {"name": "Point de Vente", "description": "Caisse et POS", "category": "Metier", "icon": "monitor"},
    "ecommerce": {"name": "E-commerce", "description": "Boutique en ligne", "category": "Metier", "icon": "shopping-bag"},
    "helpdesk": {"name": "Support", "description": "Tickets support client", "category": "Metier", "icon": "headphones"},
    "bi": {"name": "BI/Reporting", "description": "Tableaux de bord et analyses", "category": "Metier", "icon": "bar-chart-2"},
    "compliance": {"name": "Conformité", "description": "Conformité réglementaire", "category": "Metier", "icon": "shield"},
    "interventions": {"name": "Interventions", "description": "Gestion des interventions", "category": "Metier", "icon": "truck"},
    "ai_assistant": {"name": "Assistant IA", "description": "Assistant intelligent Marceau", "category": "Metier", "icon": "bot"},
    "assets": {"name": "Immobilisations", "description": "Gestion des immobilisations", "category": "Metier", "icon": "building"},
    "contracts": {"name": "Contrats", "description": "Gestion des contrats", "category": "Metier", "icon": "file-signature"},
    "expenses": {"name": "Notes de Frais", "description": "Gestion des notes de frais", "category": "Metier", "icon": "receipt"},
    "timesheet": {"name": "Feuilles de Temps", "description": "Suivi du temps de travail", "category": "Metier", "icon": "clock"},
    "field_service": {"name": "Service Terrain", "description": "Gestion des équipes terrain", "category": "Metier", "icon": "map-pin"},
    "complaints": {"name": "Réclamations", "description": "Gestion des réclamations clients", "category": "Metier", "icon": "alert-circle"},
    "warranty": {"name": "Garanties", "description": "Gestion des garanties", "category": "Metier", "icon": "shield-check"},
    "rfq": {"name": "Appels d'Offres", "description": "Gestion des appels d'offres", "category": "Metier", "icon": "file-search"},
    "procurement": {"name": "Approvisionnement", "description": "Gestion des approvisionnements", "category": "Metier", "icon": "truck"},
    "subscriptions": {"name": "Abonnements", "description": "Gestion des abonnements", "category": "Metier", "icon": "repeat"},
    "marketplace": {"name": "Marketplace", "description": "Place de marché", "category": "Metier", "icon": "store"},
    "esignature": {"name": "Signature Électronique", "description": "Signature de documents", "category": "Metier", "icon": "pen-tool"},
    "email": {"name": "Email", "description": "Gestion des emails", "category": "Metier", "icon": "mail"},
    "broadcast": {"name": "Diffusion", "description": "Diffusion et communication", "category": "Metier", "icon": "send"},
    "web": {"name": "Site Web", "description": "Constructeur de site web", "category": "Metier", "icon": "globe"},
    "website": {"name": "Site Web Builder", "description": "Constructeur de site web avancé", "category": "Metier", "icon": "globe"},
    "crm": {"name": "CRM Avancé", "description": "CRM et pipeline commercial", "category": "Metier", "icon": "users"},
    "commercial": {"name": "Commercial", "description": "Gestion commerciale", "category": "Metier", "icon": "briefcase"},
    "finance": {"name": "Finance", "description": "Gestion financière avancée", "category": "Metier", "icon": "trending-up"},
    "consolidation": {"name": "Consolidation", "description": "Consolidation comptable", "category": "Metier", "icon": "layers"},
    "qc": {"name": "Contrôle Qualité", "description": "Contrôle qualité avancé", "category": "Metier", "icon": "check-square"},
    "automated_accounting": {"name": "Comptabilité Auto", "description": "Comptabilisation automatique", "category": "Metier", "icon": "cpu"},
    "social_networks": {"name": "Réseaux Sociaux", "description": "Gestion réseaux sociaux", "category": "Metier", "icon": "share-2"},
    "mobile": {"name": "Mobile", "description": "Application mobile", "category": "Metier", "icon": "smartphone"},
    "marceau": {"name": "Marceau", "description": "Assistant IA vocal", "category": "Metier", "icon": "mic"},
    "enrichment": {"name": "Enrichissement", "description": "Enrichissement de données", "category": "Metier", "icon": "database"},

    # Modules techniques
    "audit": {"name": "Audit", "description": "Audit et traçabilité", "category": "Technique", "icon": "eye"},
    "backup": {"name": "Sauvegardes", "description": "Gestion des sauvegardes", "category": "Technique", "icon": "database"},
    "guardian": {"name": "Guardian", "description": "Sécurité et surveillance", "category": "Technique", "icon": "shield"},
    "iam": {"name": "Gestion des Accès", "description": "Identités et autorisations", "category": "Technique", "icon": "key"},
    "tenants": {"name": "Multi-Tenants", "description": "Gestion multi-entreprises", "category": "Technique", "icon": "building-2"},
    "triggers": {"name": "Déclencheurs", "description": "Automatisations et workflows", "category": "Technique", "icon": "zap"},
    "autoconfig": {"name": "Configuration Auto", "description": "Configuration automatique", "category": "Technique", "icon": "settings"},
    "hr_vault": {"name": "Coffre-fort RH", "description": "Documents RH sécurisés", "category": "Technique", "icon": "lock"},
    "stripe_integration": {"name": "Intégration Stripe", "description": "Paiements Stripe", "category": "Technique", "icon": "credit-card"},
    "country_packs": {"name": "Packs Pays", "description": "Localisations par pays", "category": "Technique", "icon": "flag"},

    # Import de données
    "odoo_import": {"name": "Import Odoo", "description": "Import depuis Odoo (v8-18)", "category": "Import", "icon": "download"},
}

# Modules à ignorer (utilitaires, non-modules)
IGNORED_MODULES = {
    "__pycache__",
    "budget",
    "commissions",
    "loyalty",
    "documents",
    "theo",  # Module interne IA
}


# =============================================================================
# DÉCOUVERTE AUTOMATIQUE DES MODULES
# =============================================================================

def _get_modules_dir() -> Path:
    """Retourne le chemin du dossier des modules"""
    return Path(__file__).parent.parent / "modules"


def _discover_modules() -> List[Dict]:
    """
    Découvre automatiquement tous les modules depuis app/modules/
    Retourne une liste de modules avec leurs métadonnées.
    """
    modules = []
    modules_dir = _get_modules_dir()

    if not modules_dir.exists():
        logger.warning(f"Modules directory not found: {modules_dir}")
        return modules

    for item in sorted(modules_dir.iterdir()):
        if not item.is_dir():
            continue

        module_name = item.name

        # Ignorer les modules dans la liste d'exclusion
        if module_name in IGNORED_MODULES:
            continue

        # Ignorer les dossiers commençant par _
        if module_name.startswith("_"):
            continue

        # Récupérer les métadonnées
        metadata = _get_module_metadata(module_name, item)
        if metadata:
            modules.append(metadata)

    # Ajouter les modules d'import manuellement (pas de dossier dédié)
    modules.extend(_get_import_modules())

    return modules


def _get_module_metadata(module_name: str, module_path: Path) -> Optional[Dict]:
    """
    Extrait les métadonnées d'un module depuis son __init__.py
    ou utilise les overrides si définis.
    """
    # Utiliser les overrides si disponibles
    if module_name in MODULE_METADATA_OVERRIDES:
        override = MODULE_METADATA_OVERRIDES[module_name]
        category_str = override.get("category", "Metier")
        category = ModuleCategory.METIER
        if category_str == "Technique":
            category = ModuleCategory.TECHNIQUE
        elif category_str == "Import":
            category = ModuleCategory.IMPORT

        # Convertir underscore en tiret pour la route
        route_name = module_name.replace("_", "-")

        return {
            "code": module_name.replace("_", "-"),
            "name": override.get("name", module_name.title()),
            "description": override.get("description", ""),
            "category": category,
            "icon": override.get("icon", "folder"),
            "route": f"/{route_name}",
            "enabled_by_default": override.get("enabled_by_default", False),
        }

    # Sinon, essayer de lire __init__.py
    init_file = module_path / "__init__.py"
    if not init_file.exists():
        return None

    try:
        # Lire le fichier pour extraire les variables
        content = init_file.read_text()

        # Extraire les métadonnées
        code = _extract_var(content, "__module_code__") or module_name
        name = _extract_var(content, "__module_name__") or module_name.replace("_", " ").title()
        description = _extract_var(content, "__module_description__") or ""
        category_str = _extract_var(content, "__module_category__") or "Metier"
        icon = _extract_var(content, "__module_icon__") or "folder"
        enabled = _extract_var(content, "__enabled_by_default__")
        enabled = enabled.lower() == "true" if enabled else False

        # Déterminer la catégorie
        category = ModuleCategory.METIER
        if "technique" in category_str.lower() or "admin" in category_str.lower():
            category = ModuleCategory.TECHNIQUE
        elif "import" in category_str.lower():
            category = ModuleCategory.IMPORT

        route_name = module_name.replace("_", "-")

        return {
            "code": module_name.replace("_", "-"),
            "name": name,
            "description": description,
            "category": category,
            "icon": icon,
            "route": f"/{route_name}",
            "enabled_by_default": enabled,
        }
    except Exception as e:
        logger.warning(f"Error reading module metadata for {module_name}: {e}")
        return None


def _extract_var(content: str, var_name: str) -> Optional[str]:
    """Extrait la valeur d'une variable depuis le contenu d'un fichier"""
    import re
    pattern = rf'^{var_name}\s*=\s*["\'](.+?)["\']'
    match = re.search(pattern, content, re.MULTILINE)
    return match.group(1) if match else None


def _get_import_modules() -> List[Dict]:
    """Retourne les modules d'import (définis manuellement)"""
    return [
        {
            "code": "IMP1",
            "name": "Import Odoo",
            "description": "Import depuis Odoo (v8-18)",
            "category": ModuleCategory.IMPORT,
            "icon": "download",
            "route": "/import/odoo",
            "enabled_by_default": False,
        },
        {
            "code": "IMP2",
            "name": "Import Axonaut",
            "description": "Import depuis Axonaut",
            "category": ModuleCategory.IMPORT,
            "icon": "download",
            "route": "/import/axonaut",
            "enabled_by_default": False,
        },
        {
            "code": "IMP3",
            "name": "Import Pennylane",
            "description": "Import depuis Pennylane",
            "category": ModuleCategory.IMPORT,
            "icon": "download",
            "route": "/import/pennylane",
            "enabled_by_default": False,
        },
        {
            "code": "IMP4",
            "name": "Import Sage",
            "description": "Import depuis Sage",
            "category": ModuleCategory.IMPORT,
            "icon": "download",
            "route": "/import/sage",
            "enabled_by_default": False,
        },
        {
            "code": "IMP5",
            "name": "Import Chorus",
            "description": "Import depuis Chorus Pro",
            "category": ModuleCategory.IMPORT,
            "icon": "download",
            "route": "/import/chorus",
            "enabled_by_default": False,
        },
    ]


# =============================================================================
# REGISTRE DES MODULES - GÉNÉRÉ AUTOMATIQUEMENT
# =============================================================================

# Découverte au chargement du module
MODULES: List[Dict] = _discover_modules()


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def get_all_modules() -> List[Dict]:
    """Retourne tous les modules disponibles"""
    return MODULES


def get_module(code: str) -> Optional[Dict]:
    """Retourne un module par son code"""
    for mod in MODULES:
        if mod["code"] == code:
            return mod
    return None


def get_modules_by_category(category: ModuleCategory) -> List[Dict]:
    """Retourne les modules d'une catégorie"""
    return [m for m in MODULES if m["category"] == category]


def get_module_codes() -> List[str]:
    """Retourne la liste des codes de modules"""
    return [m["code"] for m in MODULES]


def get_default_modules() -> List[str]:
    """Retourne les codes des modules activés par défaut"""
    return [m["code"] for m in MODULES if m.get("enabled_by_default", False)]


def get_categories() -> List[str]:
    """Retourne la liste des catégories"""
    return [c.value for c in ModuleCategory]


def get_modules_grouped_by_category() -> Dict[str, List[Dict]]:
    """Retourne les modules groupés par catégorie"""
    result = {}
    for category in ModuleCategory:
        modules = get_modules_by_category(category)
        if modules:
            result[category.value] = modules
    return result


def refresh_modules() -> int:
    """Rafraîchit la liste des modules (redécouverte)"""
    global MODULES
    MODULES = _discover_modules()
    return len(MODULES)


# Log au chargement
logger.info(f"[ModulesRegistry] Discovered {len(MODULES)} modules")
