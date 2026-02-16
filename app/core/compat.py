"""
AZALS - Couche de Compatibilité v1/v2
======================================
Adaptateurs pour permettre la coexistence des API v1 et v2.

Le pattern v1 utilise get_current_user() qui retourne un User.
Le pattern v2 utilise get_saas_context() qui retourne un SaaSContext.

Ce module fournit des adaptateurs pour unifier ces deux patterns.

Conformité : AZA-NF-004
"""

import logging
from typing import Set
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_tenant_id
from app.core.models import User
from app.core.saas_context import SaaSContext, UserRole, TenantScope

logger = logging.getLogger(__name__)


# =============================================================================
# Mapping des rôles User → UserRole enum
# =============================================================================

ROLE_MAPPING = {
    "SUPERADMIN": UserRole.SUPERADMIN,
    "DIRIGEANT": UserRole.DIRIGEANT,
    "ADMIN": UserRole.ADMIN,
    "DAF": UserRole.DAF,
    "COMPTABLE": UserRole.COMPTABLE,
    "COMMERCIAL": UserRole.COMMERCIAL,
    "EMPLOYE": UserRole.EMPLOYE,
    # Fallback pour rôles non mappés
    None: UserRole.EMPLOYE,
    "": UserRole.EMPLOYE,
}


def _map_role(user_role: str | None) -> UserRole:
    """Convertit le rôle utilisateur en UserRole enum."""
    if user_role is None:
        return UserRole.EMPLOYE

    role_str = str(user_role).upper()
    return ROLE_MAPPING.get(role_str, UserRole.EMPLOYE)


def _extract_permissions(user: User) -> Set[str]:
    """
    Extrait les permissions de l'utilisateur.

    Note: Cette fonction peut être étendue pour charger les permissions
    depuis les rôles/groupes de l'utilisateur.
    """
    permissions = set()

    # Si l'utilisateur a des rôles avec permissions
    if hasattr(user, 'roles') and user.roles:
        for role in user.roles:
            if hasattr(role, 'permissions') and role.permissions:
                for perm in role.permissions:
                    if hasattr(perm, 'code'):
                        permissions.add(perm.code)

    # Permissions basées sur le rôle (fallback)
    role = _map_role(getattr(user, 'role', None))

    # Permissions implicites par rôle
    if role == UserRole.SUPERADMIN:
        permissions.add("*")  # Toutes permissions
    elif role == UserRole.DIRIGEANT:
        permissions.add("tenant.*")
    elif role == UserRole.ADMIN:
        permissions.add("admin.*")

    return permissions


# =============================================================================
# Adaptateur v1 → v2
# =============================================================================

def v1_to_saas_context(
    current_user: User = Depends(get_current_user),
    request: Request = None
) -> SaaSContext:
    """
    Adapte le pattern v1 (User) vers SaaSContext v2.

    Usage:
        @router.get("/endpoint")
        async def endpoint(
            context: SaaSContext = Depends(v1_to_saas_context),
            db: Session = Depends(get_db)
        ):
            service = MyService(db, context)
            ...
    """
    # Extraction des infos
    tenant_id = current_user.tenant_id
    user_id = current_user.id

    # Convertir user_id en UUID si nécessaire
    if not isinstance(user_id, UUID):
        user_id = UUID(str(user_id)) if '-' in str(user_id) else UUID(int=int(user_id))

    # Mapper le rôle
    role = _map_role(getattr(current_user, 'role', None))

    # Extraire les permissions
    permissions = _extract_permissions(current_user)

    # Déterminer le scope
    scope = TenantScope.GLOBAL if role == UserRole.SUPERADMIN else TenantScope.TENANT

    # Info de la requête pour audit
    ip_address = ""
    user_agent = ""
    correlation_id = ""

    if request:
        ip_address = request.client.host if request.client else ""
        user_agent = request.headers.get("User-Agent", "")
        correlation_id = request.headers.get("X-Correlation-ID", "")

    return SaaSContext(
        tenant_id=tenant_id,
        user_id=user_id,
        role=role,
        permissions=permissions,
        scope=scope,
        ip_address=ip_address,
        user_agent=user_agent,
        correlation_id=correlation_id
    )


# =============================================================================
# Dépendance unifiée
# =============================================================================

def get_context(
    context: SaaSContext = Depends(v1_to_saas_context)
) -> SaaSContext:
    """
    Dépendance unifiée qui fonctionne pour v1 et v2.

    Usage dans les routers unifiés:
        from app.core.compat import get_context

        @router.get("/items")
        async def list_items(
            context: SaaSContext = Depends(get_context),
            db: Session = Depends(get_db)
        ):
            service = ItemService(db, context)
            return service.list()
    """
    return context


# =============================================================================
# Dépendances combinées pour faciliter la migration
# =============================================================================

async def get_context_and_db(
    context: SaaSContext = Depends(get_context),
    db: Session = Depends(get_db)
) -> tuple[SaaSContext, Session]:
    """
    Combine context et db en une seule dépendance.

    Usage:
        @router.get("/items")
        async def list_items(deps = Depends(get_context_and_db)):
            context, db = deps
            service = ItemService(db, context)
    """
    return context, db


# =============================================================================
# Helpers pour migration progressive
# =============================================================================

def create_context_from_user(
    user: User,
    request: Request = None
) -> SaaSContext:
    """
    Crée un SaaSContext à partir d'un User (pour usage programmatique).

    Usage dans les services qui reçoivent un User:
        context = create_context_from_user(current_user, request)
        service = MyService(db, context)
    """
    user_id = user.id
    if not isinstance(user_id, UUID):
        user_id = UUID(str(user_id)) if '-' in str(user_id) else UUID(int=int(user_id))

    role = _map_role(getattr(user, 'role', None))
    permissions = _extract_permissions(user)
    scope = TenantScope.GLOBAL if role == UserRole.SUPERADMIN else TenantScope.TENANT

    ip_address = ""
    user_agent = ""
    correlation_id = ""

    if request:
        ip_address = request.client.host if request.client else ""
        user_agent = request.headers.get("User-Agent", "")
        correlation_id = request.headers.get("X-Correlation-ID", "")

    return SaaSContext(
        tenant_id=user.tenant_id,
        user_id=user_id,
        role=role,
        permissions=permissions,
        scope=scope,
        ip_address=ip_address,
        user_agent=user_agent,
        correlation_id=correlation_id
    )


# =============================================================================
# Decorateur pour endpoints unifiés
# =============================================================================

def unified_endpoint(func):
    """
    Décorateur pour marquer un endpoint comme unifié (v1+v2 compatible).

    Usage:
        @router.get("/items")
        @unified_endpoint
        async def list_items(context: SaaSContext = Depends(get_context)):
            ...
    """
    func._unified = True
    return func
