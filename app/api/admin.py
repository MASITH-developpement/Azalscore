"""
AZALS - Admin Dashboard API
===========================
API pour le tableau de bord d'administration.
"""
from __future__ import annotations


import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.cache import cached, invalidate_cache
from app.core.database import get_db
from app.core.dependencies import get_tenant_id
from app.core.models import User
from app.core.modules_registry import (
    get_all_modules,
    get_modules_grouped_by_category,
    get_categories,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Administration"])


# ============================================================================
# SCHEMAS
# ============================================================================

class AdminDashboard(BaseModel):
    total_users: int = 0
    active_users: int = 0
    total_tenants: int = 0
    active_tenants: int = 0
    total_roles: int = 0
    storage_used_gb: float = 0
    api_calls_today: int = 0
    errors_today: int = 0


class AdminUserCreate(BaseModel):
    """
    Schéma de création d'utilisateur via l'interface admin.

    Conformité:
    - AZA-SEC-001: Validation stricte des entrées
    - AZA-BE-003: Contrat backend obligatoire

    Note: Ce schéma est moins strict que IAM.UserCreate (8 vs 12 caractères)
    car il est utilisé par des admins pour créer des comptes initiaux.
    """
    email: EmailStr = Field(..., description="Adresse email unique")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Mot de passe (8-128 caractères)"
    )
    roles: list[str] = Field(
        default=["EMPLOYE"],
        description="Liste des rôles (EMPLOYE, COMPTABLE, ADMIN, DIRIGEANT)"
    )
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validation basique du mot de passe.
        Pour une validation complète, utiliser le module IAM.
        """
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        if not any(c.isupper() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not any(c.islower() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins une minuscule")
        if not any(c.isdigit() for c in v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v

    @field_validator('roles')
    @classmethod
    def validate_roles(cls, v: list[str]) -> list[str]:
        """Validation des rôles."""
        valid_roles = {"EMPLOYE", "COMPTABLE", "ADMIN", "DIRIGEANT"}
        for role in v:
            if role not in valid_roles:
                raise ValueError(f"Rôle invalide: {role}. Valeurs autorisées: {valid_roles}")
        return v


class AdminUserResponse(BaseModel):
    """Réponse après création d'utilisateur admin."""
    id: str
    email: str
    name: str
    roles: list[str]
    is_active: bool


# ============================================================================
# FONCTIONS CACHABLES (separees des endpoints pour @cached)
# ============================================================================

def _build_dashboard_cache_key(db, tenant_id: str) -> str:
    """Construit la cle de cache pour le dashboard admin."""
    return f"admin:dashboard:{tenant_id}"


@cached(ttl=300, key_builder=lambda db, tenant_id: f"admin:dashboard:{tenant_id}")
def _get_admin_dashboard_data(db: Session, tenant_id: str) -> dict:
    """
    Calcule les donnees du dashboard admin (CACHABLE 5min).

    Separe de l'endpoint pour permettre le caching.
    """
    dashboard = AdminDashboard()

    # Compter les utilisateurs
    try:
        result = db.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_active = true) as active
            FROM iam_users
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id})
        row = result.fetchone()
        if row:
            dashboard.total_users = row[0] or 0
            dashboard.active_users = row[1] or 0
    except Exception as e:
        logger.warning(f"[ADMIN] Erreur comptage users: {e}")
        try:
            result = db.execute(text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE is_active = true) as active
                FROM users
                WHERE tenant_id = :tenant_id
            """), {"tenant_id": tenant_id})
            row = result.fetchone()
            if row:
                dashboard.total_users = row[0] or 0
                dashboard.active_users = row[1] or 0
        except Exception:
            pass

    # SÉCURITÉ: Chaque admin ne voit QUE son propre tenant
    # La requête précédente comptait TOUS les tenants (fuite cross-tenant)
    # Correction: On ne montre que les stats du tenant courant
    try:
        result = db.execute(text("""
            SELECT
                CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END as is_active
            FROM tenants
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id})
        row = result.fetchone()
        # Un admin ne voit que SON tenant
        dashboard.total_tenants = 1
        dashboard.active_tenants = 1 if (row and row[0] == 1) else 0
    except Exception as e:
        logger.warning(f"[ADMIN] Erreur vérification tenant: {e}")
        dashboard.total_tenants = 1
        dashboard.active_tenants = 1

    # Compter les roles
    try:
        result = db.execute(text("""
            SELECT COUNT(*) FROM iam_roles
            WHERE tenant_id = :tenant_id AND is_active = true
        """), {"tenant_id": tenant_id})
        dashboard.total_roles = result.scalar() or 0
    except Exception as e:
        logger.warning(f"[ADMIN] Erreur comptage roles: {e}")

    # Stockage utilise
    try:
        result = db.execute(text("""
            SELECT COALESCE(storage_used_gb, 0) FROM tenants
            WHERE tenant_id = :tenant_id
        """), {"tenant_id": tenant_id})
        dashboard.storage_used_gb = float(result.scalar() or 0)
    except Exception as e:
        logger.warning(f"[ADMIN] Erreur lecture stockage: {e}")

    # Appels API aujourd'hui
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = db.execute(text("""
            SELECT COUNT(*) FROM iam_audit_log
            WHERE tenant_id = :tenant_id
            AND created_at >= :today
        """), {"tenant_id": tenant_id, "today": today})
        dashboard.api_calls_today = result.scalar() or 0
    except Exception as e:
        logger.warning(f"[ADMIN] Erreur comptage API calls: {e}")

    # Erreurs aujourd'hui
    try:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = db.execute(text("""
            SELECT COUNT(*) FROM guardian_errors
            WHERE tenant_id = :tenant_id
            AND occurred_at >= :today
        """), {"tenant_id": tenant_id, "today": today})
        dashboard.errors_today = result.scalar() or 0
    except Exception as e:
        logger.warning(f"[ADMIN] Erreur comptage erreurs: {e}")

    return dashboard.model_dump()


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=AdminDashboard)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Dashboard d'administration avec statistiques systeme (cache 5min)."""
    data = _get_admin_dashboard_data(db, tenant_id)
    return AdminDashboard(**data)


# ============================================================================
# MODULES DISPONIBLES (source unique de verite)
# ============================================================================

@router.get("/modules/available")
def get_available_modules(
    current_user: User = Depends(get_current_user)
):
    """
    Liste tous les modules disponibles groupes par categorie.

    C'est la SOURCE UNIQUE DE VERITE pour les modules.
    Le frontend doit utiliser cet endpoint au lieu de listes codees en dur.

    SÉCURITÉ: Authentification requise.
    """
    return {
        "categories": get_categories(),
        "modules": get_all_modules(),
        "modules_by_category": get_modules_grouped_by_category(),
    }


@router.get("/modules/list")
def get_modules_list(
    current_user: User = Depends(get_current_user)
):
    """
    Liste simple des modules (pour compatibilite).

    SÉCURITÉ: Authentification requise.
    """
    return {"items": get_all_modules()}
