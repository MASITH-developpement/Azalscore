"""
CORE SaaS - Dépendances FastAPI v2
===================================

Nouvelle génération d'injection de dépendances utilisant le CORE SaaS.

CHANGEMENT MAJEUR:
- Au lieu de retourner User séparément, retourne un SaaSContext unifié
- Toute la logique d'authentification/autorisation passe par CORE

MIGRATION:
Ancien:
    def my_endpoint(
        current_user: User = Depends(get_current_user),
        tenant_id: str = Depends(get_tenant_id)
    ):
        # Vérifier permissions manuellement
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(403)

Nouveau:
    def my_endpoint(
        context: SaaSContext = Depends(get_saas_context)
    ):
        # Permissions vérifiées via CORE
        if not CORE.authorize(context, "module.resource.action"):
            raise HTTPException(403)
"""

import uuid
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.saas_context import SaaSContext
from app.core.saas_core import get_saas_core, SaaSCore


# Security scheme
security = HTTPBearer()


# ============================================================================
# DEPENDENCY: get_saas_context
# ============================================================================

def get_saas_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    core: SaaSCore = Depends(get_saas_core),
) -> SaaSContext:
    """
    Dépendance FastAPI principale: crée et retourne un SaaSContext.

    Workflow:
    1. Extraire tenant_id depuis request.state (validé par middleware)
    2. Extraire JWT token depuis Authorization header
    3. Appeler CORE.authenticate() pour créer SaaSContext
    4. Retourner SaaSContext si succès, HTTPException sinon

    Le SaaSContext contient:
    - tenant_id: Tenant ID
    - user_id: User ID
    - role: Rôle utilisateur (SUPERADMIN, DIRIGEANT, etc.)
    - permissions: Set de permissions
    - scope: Scope (TENANT ou GLOBAL)
    - ip_address, user_agent, correlation_id: Pour audit trail

    Usage:
        @router.get("/customers")
        async def list_customers(
            context: SaaSContext = Depends(get_saas_context)
        ):
            # context contient tenant_id, user_id, role, permissions
            # Utiliser CORE.execute() pour exécuter l'action
            result = await CORE.execute(
                "commercial.customer.list",
                context
            )
            return result.data

    Args:
        request: Request FastAPI
        credentials: JWT token depuis Authorization header
        db: Session SQLAlchemy
        core: Instance SaaSCore

    Returns:
        SaaSContext si authentification réussie

    Raises:
        HTTPException 401: Si authentification échoue
        HTTPException 403: Si tenant non actif
    """
    # 1. Extraire tenant_id depuis request.state
    # (injecté par TenantMiddleware)
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Tenant-ID header"
        )

    tenant_id = request.state.tenant_id

    # 2. Extraire token JWT
    token = credentials.credentials

    # 3. Extraire informations de requête pour audit trail
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "")

    # Générer correlation_id si absent
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    # 4. Authentifier via CORE
    result = core.authenticate(
        token=token,
        tenant_id=tenant_id,
        ip_address=ip_address,
        user_agent=user_agent,
        correlation_id=correlation_id,
    )

    # 5. Gérer le résultat
    if not result.success:
        # Mapper les erreurs CORE vers HTTPException
        error_mapping = {
            "AUTH_INVALID_TOKEN": status.HTTP_401_UNAUTHORIZED,
            "AUTH_USER_NOT_FOUND": status.HTTP_401_UNAUTHORIZED,
            "AUTH_TENANT_NOT_FOUND": status.HTTP_401_UNAUTHORIZED,
            "AUTH_TENANT_NOT_ACTIVE": status.HTTP_403_FORBIDDEN,
        }

        status_code = error_mapping.get(
            result.error_code,
            status.HTTP_401_UNAUTHORIZED
        )

        raise HTTPException(
            status_code=status_code,
            detail=result.error
        )

    # 6. Retourner SaaSContext
    context: SaaSContext = result.data
    return context


# ============================================================================
# DEPENDENCY HELPERS (compatibilité/convenience)
# ============================================================================

def get_tenant_id(context: SaaSContext = Depends(get_saas_context)) -> str:
    """
    Helper: extrait tenant_id depuis SaaSContext.

    Utile pour compatibilité avec ancien code.

    Usage:
        def my_endpoint(tenant_id: str = Depends(get_tenant_id)):
            ...
    """
    return context.tenant_id


def get_user_id(context: SaaSContext = Depends(get_saas_context)) -> uuid.UUID:
    """
    Helper: extrait user_id depuis SaaSContext.

    Usage:
        def my_endpoint(user_id: UUID = Depends(get_user_id)):
            ...
    """
    return context.user_id


def require_role(*allowed_roles: str):
    """
    Dependency factory: vérifie que le rôle utilisateur est autorisé.

    Usage:
        @router.post("/admin-action")
        def admin_action(
            context: SaaSContext = Depends(get_saas_context),
            _: None = Depends(require_role("SUPERADMIN", "DIRIGEANT"))
        ):
            # Seuls SUPERADMIN et DIRIGEANT peuvent accéder
            ...

    Args:
        *allowed_roles: Liste de rôles autorisés (ex: "SUPERADMIN", "DIRIGEANT")

    Returns:
        Dependency function qui lève HTTPException si rôle non autorisé
    """
    def check_role(context: SaaSContext = Depends(get_saas_context)) -> None:
        if context.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {context.role.value} not authorized. "
                       f"Required: {', '.join(allowed_roles)}"
            )

    return check_role


def require_permission(permission: str):
    """
    Dependency factory: vérifie qu'une permission est accordée.

    Usage:
        @router.delete("/customers/{customer_id}")
        def delete_customer(
            customer_id: str,
            context: SaaSContext = Depends(get_saas_context),
            _: None = Depends(require_permission("commercial.customer.delete")),
            core: SaaSCore = Depends(get_saas_core),
        ):
            # Permission vérifiée automatiquement
            ...

    Args:
        permission: Permission requise (format "module.resource.action")

    Returns:
        Dependency function qui lève HTTPException si permission refusée
    """
    def check_permission(
        context: SaaSContext = Depends(get_saas_context),
        core: SaaSCore = Depends(get_saas_core),
    ) -> None:
        if not core.authorize(context, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}"
            )

    return check_permission


def require_module_active(module_code: str):
    """
    Dependency factory: vérifie qu'un module est actif pour le tenant.

    Usage:
        @router.get("/invoices")
        def list_invoices(
            context: SaaSContext = Depends(get_saas_context),
            _: None = Depends(require_module_active("invoicing")),
        ):
            # Module "invoicing" garanti actif
            ...

    Args:
        module_code: Code du module (ex: "commercial", "invoicing")

    Returns:
        Dependency function qui lève HTTPException si module inactif
    """
    def check_module(
        context: SaaSContext = Depends(get_saas_context),
        core: SaaSCore = Depends(get_saas_core),
    ) -> None:
        if not core.is_module_active(context, module_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Module {module_code} is not active for this tenant"
            )

    return check_module


# ============================================================================
# COMPATIBILITÉ LEGACY (à supprimer progressivement)
# ============================================================================

def get_tenant_id_legacy(request: Request) -> str:
    """
    LEGACY: Extraction tenant_id depuis request.state.

    À REMPLACER PAR: get_saas_context ou get_tenant_id

    Conservé temporairement pour compatibilité avec ancien code.
    """
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Tenant-ID header"
        )
    return request.state.tenant_id
