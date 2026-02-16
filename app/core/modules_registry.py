"""
AZALSCORE - Registre Central des Modules
=========================================
SOURCE UNIQUE DE VERITE pour tous les modules disponibles.

Utilisation:
- Backend: from app.core.modules_registry import MODULES, get_module, get_modules_by_category
- Frontend: GET /api/v1/admin/modules/available

POUR AJOUTER UN MODULE:
1. Ajouter une entree dans MODULES ci-dessous
2. C'est tout. Le menu et l'admin se mettent a jour automatiquement.
"""

from typing import List, Dict, Optional
from enum import Enum


class ModuleCategory(str, Enum):
    """Categories de modules"""
    METIER = "Metier"
    TECHNIQUE = "Technique"
    IMPORT = "Import de Donnees"


# =============================================================================
# REGISTRE DES MODULES - AJOUTER VOS MODULES ICI
# =============================================================================

MODULES: List[Dict] = [
    # -------------------------------------------------------------------------
    # MODULES METIER
    # -------------------------------------------------------------------------
    {
        "code": "invoicing",
        "name": "Facturation",
        "description": "Devis, commandes, factures",
        "category": ModuleCategory.METIER,
        "icon": "file-text",
        "route": "/invoicing",
        "enabled_by_default": True,
    },
    {
        "code": "payments",
        "name": "Paiements",
        "description": "Gestion des paiements",
        "category": ModuleCategory.METIER,
        "icon": "credit-card",
        "route": "/payments",
        "enabled_by_default": True,
    },
    {
        "code": "partners",
        "name": "CRM/Clients",
        "description": "Gestion relation client",
        "category": ModuleCategory.METIER,
        "icon": "users",
        "route": "/partners",
        "enabled_by_default": True,
    },
    {
        "code": "projects",
        "name": "Projets/Affaires",
        "description": "Suivi des projets et affaires",
        "category": ModuleCategory.METIER,
        "icon": "briefcase",
        "route": "/projects",
        "enabled_by_default": False,
    },
    {
        "code": "inventory",
        "name": "Stock",
        "description": "Gestion des stocks",
        "category": ModuleCategory.METIER,
        "icon": "package",
        "route": "/inventory",
        "enabled_by_default": False,
    },
    {
        "code": "purchases",
        "name": "Achats",
        "description": "Commandes fournisseurs",
        "category": ModuleCategory.METIER,
        "icon": "shopping-cart",
        "route": "/purchases",
        "enabled_by_default": False,
    },
    {
        "code": "hr",
        "name": "RH",
        "description": "Ressources humaines",
        "category": ModuleCategory.METIER,
        "icon": "user",
        "route": "/hr",
        "enabled_by_default": False,
    },
    {
        "code": "production",
        "name": "Production",
        "description": "Gestion de production",
        "category": ModuleCategory.METIER,
        "icon": "settings",
        "route": "/production",
        "enabled_by_default": False,
    },
    {
        "code": "maintenance",
        "name": "Maintenance",
        "description": "GMAO",
        "category": ModuleCategory.METIER,
        "icon": "tool",
        "route": "/maintenance",
        "enabled_by_default": False,
    },
    {
        "code": "quality",
        "name": "Qualite",
        "description": "Controle qualite",
        "category": ModuleCategory.METIER,
        "icon": "check-circle",
        "route": "/quality",
        "enabled_by_default": False,
    },
    {
        "code": "pos",
        "name": "Point de Vente",
        "description": "Caisse et POS",
        "category": ModuleCategory.METIER,
        "icon": "monitor",
        "route": "/pos",
        "enabled_by_default": False,
    },
    {
        "code": "ecommerce",
        "name": "E-commerce",
        "description": "Boutique en ligne",
        "category": ModuleCategory.METIER,
        "icon": "shopping-bag",
        "route": "/ecommerce",
        "enabled_by_default": False,
    },
    {
        "code": "helpdesk",
        "name": "Support",
        "description": "Tickets support client",
        "category": ModuleCategory.METIER,
        "icon": "headphones",
        "route": "/helpdesk",
        "enabled_by_default": False,
    },
    {
        "code": "accounting",
        "name": "Comptabilite",
        "description": "Comptabilite generale",
        "category": ModuleCategory.METIER,
        "icon": "book",
        "route": "/accounting",
        "enabled_by_default": False,
    },
    {
        "code": "treasury",
        "name": "Tresorerie",
        "description": "Gestion de tresorerie",
        "category": ModuleCategory.METIER,
        "icon": "dollar-sign",
        "route": "/treasury",
        "enabled_by_default": True,
    },
    {
        "code": "bi",
        "name": "BI/Reporting",
        "description": "Tableaux de bord et analyses",
        "category": ModuleCategory.METIER,
        "icon": "bar-chart-2",
        "route": "/bi",
        "enabled_by_default": False,
    },
    {
        "code": "compliance",
        "name": "Conformite",
        "description": "Conformite reglementaire",
        "category": ModuleCategory.METIER,
        "icon": "shield",
        "route": "/compliance",
        "enabled_by_default": False,
    },
    {
        "code": "interventions",
        "name": "Interventions",
        "description": "Gestion des interventions",
        "category": ModuleCategory.METIER,
        "icon": "truck",
        "route": "/interventions",
        "enabled_by_default": False,
    },

    # -------------------------------------------------------------------------
    # IMPORT DE DONNEES
    # -------------------------------------------------------------------------
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
    """Retourne les modules d'une categorie"""
    return [m for m in MODULES if m["category"] == category]


def get_module_codes() -> List[str]:
    """Retourne la liste des codes de modules"""
    return [m["code"] for m in MODULES]


def get_default_modules() -> List[str]:
    """Retourne les codes des modules actives par defaut"""
    return [m["code"] for m in MODULES if m.get("enabled_by_default", False)]


def get_categories() -> List[str]:
    """Retourne la liste des categories"""
    return [c.value for c in ModuleCategory]


def get_modules_grouped_by_category() -> Dict[str, List[Dict]]:
    """Retourne les modules groupes par categorie"""
    result = {}
    for category in ModuleCategory:
        modules = get_modules_by_category(category)
        if modules:
            result[category.value] = modules
    return result
