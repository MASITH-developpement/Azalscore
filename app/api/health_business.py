"""
AZALSCORE - Health Check Business
=================================
Endpoints de diagnostic systeme pour les modules metier.

SECURITE: Ces endpoints exposent des informations systeme et requierent
une authentification. Les probes Kubernetes (/health, /health/live,
/health/ready) restent publiques.
"""
from __future__ import annotations


from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.models import User
from app.core.version import AZALS_VERSION

router = APIRouter(prefix="/health/business", tags=["Health Business"])

# Liste des modules critiques a verifier
# SÉCURITÉ: Cette liste sert aussi de whitelist pour les imports dynamiques
CRITICAL_MODULES = frozenset([
    "accounting",
    "purchases",
    "treasury",
    "invoicing",
    "partners",
    "commercial",
    "iam",
    "tenants",
])

# Pattern de validation pour les noms de modules (alphanumériques et underscores uniquement)
import re
_MODULE_NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')


def _validate_module_name(module_name: str) -> bool:
    """
    Valide qu'un nom de module est sécurisé.

    SÉCURITÉ:
    - Vérifie que le module est dans la whitelist
    - Vérifie que le nom ne contient que des caractères alphanumériques et underscores
    - Empêche les attaques par path traversal ou injection
    """
    if not module_name:
        return False

    # Vérifier le pattern (alphanumériques et underscores uniquement)
    if not _MODULE_NAME_PATTERN.match(module_name):
        return False

    # Vérifier la whitelist
    if module_name not in CRITICAL_MODULES:
        return False

    return True


def check_module_health(module_name: str) -> dict[str, Any]:
    """
    Verifier la sante d'un module specifique.

    SÉCURITÉ: Le module doit être dans la whitelist CRITICAL_MODULES.
    """
    # SÉCURITÉ: Validation stricte du nom de module avant import
    if not _validate_module_name(module_name):
        return {
            "status": "error",
            "code": 400,
            "error": "Module name not allowed",
        }

    try:
        # Essayer d'importer le router_v2 du module
        __import__(f"app.modules.{module_name}.router_v2")
        return {
            "status": "healthy",
            "code": 200,
        }
    except ImportError:
        # Essayer router v1 si v2 n'existe pas
        try:
            __import__(f"app.modules.{module_name}.router")
            return {
                "status": "healthy",
                "code": 200,
                "note": "v1 only",
            }
        except ImportError:
            # SÉCURITÉ: Ne pas exposer les détails de l'erreur d'import
            return {
                "status": "unhealthy",
                "code": 503,
                "error": "Module not found or failed to load",
            }
    except Exception:
        # SÉCURITÉ: Ne pas exposer les détails des exceptions internes
        return {
            "status": "unhealthy",
            "code": 503,
            "error": "Module health check failed",
        }


def check_database(db: Session) -> dict[str, Any]:
    """Verifier la connexion base de donnees."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "code": 200,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "code": 503,
            "error": str(e),
        }


def check_registry() -> dict[str, Any]:
    """Verifier l'etat du registry de modules."""
    try:
        registry_path = Path("registry")
        if not registry_path.exists():
            return {
                "status": "warning",
                "code": 200,
                "message": "Registry directory not found",
                "count": 0,
            }

        manifests = list(registry_path.glob("**/manifest.json"))
        count = len(manifests)

        if count >= 30:
            return {
                "status": "healthy",
                "code": 200,
                "count": count,
            }
        elif count >= 10:
            return {
                "status": "warning",
                "code": 200,
                "count": count,
                "message": f"Only {count} manifests found",
            }
        else:
            return {
                "status": "degraded",
                "code": 200,
                "count": count,
                "message": f"Low manifest count: {count}",
            }
    except Exception as e:
        return {
            "status": "error",
            "code": 500,
            "error": str(e),
        }


@router.get("/modules")
async def get_modules_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Verifier la sante de tous les modules critiques.

    Requiert authentification (expose informations systeme).

    Returns:
        Dict avec status global et status par module
    """
    modules_status = {}

    for module in CRITICAL_MODULES:
        modules_status[module] = check_module_health(module)

    all_healthy = all(
        m.get("code") == 200 for m in modules_status.values()
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "modules": modules_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": AZALS_VERSION,
    }


@router.get("/database")
async def get_database_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Verifier la sante de la base de donnees.

    Requiert authentification (expose informations systeme).

    Returns:
        Dict avec status de la connexion DB
    """
    result = check_database(db)
    return {
        **result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/registry")
async def get_registry_health(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Verifier l'etat du registry de modules.

    Requiert authentification (expose informations systeme).

    Returns:
        Dict avec status et nombre de manifests
    """
    result = check_registry()
    return {
        **result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/complete")
async def get_complete_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Health check complet du systeme.

    Agregation de tous les checks: modules, database, registry.
    Requiert authentification (expose informations systeme sensibles).

    Returns:
        Dict avec status global et details de chaque composant
    """
    # Collecter tous les checks
    modules_check = {}
    for module in CRITICAL_MODULES:
        modules_check[module] = check_module_health(module)

    database_check = check_database(db)
    registry_check = check_registry()

    # Calculer le status global
    all_modules_healthy = all(
        m.get("code") == 200 for m in modules_check.values()
    )
    db_healthy = database_check.get("code") == 200
    registry_ok = registry_check.get("code") == 200

    if all_modules_healthy and db_healthy and registry_ok:
        global_status = "healthy"
    elif db_healthy and all_modules_healthy:
        global_status = "operational"
    elif db_healthy:
        global_status = "degraded"
    else:
        global_status = "critical"

    return {
        "status": global_status,
        "components": {
            "modules": {
                "status": "healthy" if all_modules_healthy else "degraded",
                "details": modules_check,
            },
            "database": database_check,
            "registry": registry_check,
        },
        "version": AZALS_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }
