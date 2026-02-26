"""
AZALSCORE - IAM Permissions Router
Endpoints pour la gestion des permissions et capabilities
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.core.models import User

from ..capabilities import get_capabilities_by_module
from ..decorators import require_permission
from ..schemas import (
    PermissionCheck,
    PermissionCheckResult,
    PermissionListResponse,
    PermissionResponse,
)
from .helpers import get_service

router = APIRouter(tags=["permissions"])


@router.get("/capabilities/modules")
@require_permission("iam.permission.read")
async def get_capabilities_modules(
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Retourne toutes les capabilities groupées par module (auto-générées)."""
    return get_capabilities_by_module()


@router.get("/permissions", response_model=PermissionListResponse)
@require_permission("iam.permission.read")
async def list_permissions(
    module: str | None = None,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Liste les permissions."""
    permissions = service.list_permissions(module=module)

    return PermissionListResponse(
        items=[
            PermissionResponse(
                id=p.id,
                tenant_id=p.tenant_id,
                code=p.code,
                module=p.module,
                resource=p.resource,
                action=p.action.value,
                name=p.name,
                description=p.description,
                is_system=p.is_system,
                is_active=p.is_active,
                is_dangerous=p.is_dangerous,
                created_at=p.created_at
            )
            for p in permissions
        ],
        total=len(permissions)
    )


@router.post("/permissions/check", response_model=PermissionCheckResult)
async def check_permission(
    data: PermissionCheck,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Vérifie si l'utilisateur a une permission."""
    user_id = data.user_id or current_user.id
    granted, source = service.check_permission(user_id, data.permission_code)

    return PermissionCheckResult(
        permission_code=data.permission_code,
        granted=granted,
        source=source
    )


@router.get("/users/{user_id}/permissions", response_model=list[str])
@require_permission("iam.permission.read")
async def get_user_permissions(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Récupère toutes les permissions d'un utilisateur."""
    return service.get_user_permissions(user_id)


class PermissionsUpdateRequest(BaseModel):
    """Request body pour mise à jour des permissions."""
    capabilities: list[str] = []
    permissions: list[str] = []  # Alias pour compatibilité


@router.put("/users/{user_id}/permissions", response_model=list[str])
@require_permission("iam.permission.admin")
async def update_user_permissions(
    user_id: UUID,
    data: PermissionsUpdateRequest,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Met à jour les permissions d'un utilisateur."""
    # Accepte capabilities ou permissions
    perms = data.capabilities if data.capabilities else data.permissions
    return service.update_user_permissions(user_id, perms)
