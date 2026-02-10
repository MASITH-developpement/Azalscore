"""
AZALSCORE - Health Check Business
=================================
Endpoints de diagnostic systeme pour les modules metier.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.version import AZALS_VERSION

router = APIRouter(prefix="/health/business", tags=["Health Business"])

# Liste des modules critiques a verifier
CRITICAL_MODULES = [
    "accounting",
    "purchases",
    "treasury",
    "invoicing",
    "partners",
    "commercial",
    "iam",
    "tenants",
]


def check_module_health(module_name: str) -> dict[str, Any]:
    """Verifier la sante d'un module specifique."""
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
        except ImportError as e:
            return {
                "status": "unhealthy",
                "code": 503,
                "error": str(e),
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "code": 503,
            "error": str(e),
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
async def get_modules_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Verifier la sante de tous les modules critiques.

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
async def get_database_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Verifier la sante de la base de donnees.

    Returns:
        Dict avec status de la connexion DB
    """
    result = check_database(db)
    return {
        **result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/registry")
async def get_registry_health() -> dict[str, Any]:
    """
    Verifier l'etat du registry de modules.

    Returns:
        Dict avec status et nombre de manifests
    """
    result = check_registry()
    return {
        **result,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/complete")
async def get_complete_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Health check complet du systeme.

    Agregation de tous les checks: modules, database, registry.

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
