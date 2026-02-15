"""
AZALS API v3 - CRUDRouter Edition
==================================

API v3 utilisant les routers CRUDRouter pour un code minimal.
Reduction de ~60% du boilerplate CRUD.

Architecture:
- v1/v2: router_unified.py (compatibilite)
- v3: router_crud.py (CRUDRouter minimal)

NOTE: Chargement resilient - les modules avec erreurs sont ignores.
"""

import logging
from typing import List, Tuple
from fastapi import APIRouter

logger = logging.getLogger(__name__)

# =============================================================================
# LISTE DES MODULES A CHARGER
# =============================================================================

MODULES_TO_LOAD = [
    # MODULES CRITIQUES
    ("iam", "IAM"),
    ("backup", "Backup"),
    ("tenants", "Tenants"),
    ("guardian", "Guardian"),
    ("audit", "Audit"),

    # MODULES FINANCIERS
    ("accounting", "Accounting"),
    ("finance", "Finance"),
    ("procurement", "Procurement"),
    ("purchases", "Purchases"),
    ("pos", "POS"),
    ("ecommerce", "E-Commerce"),
    ("stripe_integration", "Stripe"),
    ("subscriptions", "Subscriptions"),

    # MODULES OPERATIONNELS
    ("inventory", "Inventory"),
    ("production", "Production"),
    ("projects", "Projects"),
    ("maintenance", "Maintenance"),
    ("field_service", "Field Service"),
    ("helpdesk", "Helpdesk"),
    ("interventions", "Interventions"),
    ("qc", "QC"),
    ("quality", "Quality"),

    # MODULES COMMERCIAUX
    ("commercial", "Commercial"),
    ("contacts", "Contacts"),

    # MODULES SUPPORT
    ("bi", "BI"),
    ("broadcast", "Broadcast"),
    ("compliance", "Compliance"),
    ("hr", "HR"),
    ("email", "Email"),
    ("mobile", "Mobile"),
    ("marketplace", "Marketplace"),

    # MODULES CONFIGURATION
    ("autoconfig", "Autoconfig"),
    ("triggers", "Triggers"),
    ("country_packs", "Country Packs"),

    # MODULES WEB
    ("web", "Web"),
    ("website", "Website"),

    # MODULES IA
    ("ai_assistant", "AI Assistant"),
    ("marceau", "Marceau"),

    # MODULES COMPTABILITE AUTOMATISEE
    ("automated_accounting", "Automated Accounting"),

    # MODULES ENRICHMENT & IMPORT
    ("enrichment", "Enrichment"),
    ("odoo_import", "Odoo Import"),
]

# =============================================================================
# CHARGEMENT RESILIENT DES ROUTERS
# =============================================================================

def load_module_router(module_name: str, display_name: str) -> Tuple[bool, object]:
    """
    Charge un router_crud de maniere resiliente.

    Returns:
        Tuple[success: bool, router or error_message]
    """
    try:
        module = __import__(
            f"app.modules.{module_name}.router_crud",
            fromlist=["router"]
        )
        return True, module.router
    except Exception as e:
        return False, str(e)


# =============================================================================
# ROUTER PRINCIPAL V3
# =============================================================================

router = APIRouter(prefix="/v3", tags=["API v3 - CRUDRouter"])

# Compteurs pour le logging
loaded_modules: List[str] = []
failed_modules: List[Tuple[str, str]] = []

for module_name, display_name in MODULES_TO_LOAD:
    success, result = load_module_router(module_name, display_name)
    if success:
        router.include_router(result)
        loaded_modules.append(module_name)
    else:
        failed_modules.append((module_name, result))

# Log du resultat
if loaded_modules:
    logger.info(
        f"[API V3] {len(loaded_modules)} modules charges avec succes",
        extra={"modules": loaded_modules}
    )

if failed_modules:
    logger.warning(
        f"[API V3] {len(failed_modules)} modules en erreur (ignores)",
        extra={"failed": [m[0] for m in failed_modules]}
    )


# =============================================================================
# ENDPOINT DE STATUT V3
# =============================================================================

@router.get("/status")
def get_v3_status():
    """
    Retourne le statut de l'API v3.
    Liste les modules charges et ceux en erreur.
    """
    return {
        "version": "v3",
        "engine": "CRUDRouter",
        "loaded_modules": loaded_modules,
        "loaded_count": len(loaded_modules),
        "failed_modules": [
            {"module": m, "error": e[:100]} for m, e in failed_modules
        ],
        "failed_count": len(failed_modules),
        "reduction": "~60% boilerplate CRUD",
    }
