"""
AZALSCORE - IAM Roles Router
Endpoints pour la gestion des rôles
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.models import User

from ..decorators import require_permission
from ..schemas import (
    RoleAssignment,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from .helpers import get_service, role_to_response

router = APIRouter(tags=["roles"])


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.role.create")
async def create_role(
    data: RoleCreate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Crée un nouveau rôle."""
    try:
        role = service.create_role(data, created_by=current_user.id)
        return role_to_response(role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/roles", response_model=list[RoleResponse])
@require_permission("iam.role.read")
async def list_roles(
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service),
    db: Session = Depends(get_db)
):
    """Liste tous les rôles."""
    from ..models import IAMUser

    roles = service.list_roles(include_inactive=include_inactive)

    # SÉCURITÉ: Récupérer les noms des créateurs (filtrer par tenant_id)
    creator_ids = [r.created_by for r in roles if r.created_by]
    creators = {}
    if creator_ids:
        creator_users = db.query(IAMUser).filter(
            IAMUser.tenant_id == service.tenant_id,
            IAMUser.id.in_(creator_ids)
        ).all()
        creators = {
            u.id: f"{u.first_name or ''} {u.last_name or ''}".strip() or u.email
            for u in creator_users
        }

    return [
        role_to_response(r, creators.get(r.created_by) if r.created_by else None)
        for r in roles
    ]


@router.get("/roles/{role_id}", response_model=RoleResponse)
@require_permission("iam.role.read")
async def get_role(
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service),
    db: Session = Depends(get_db)
):
    """Récupère un rôle par ID."""
    from ..models import IAMUser

    role = service.get_role(role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rôle non trouvé")

    # SÉCURITÉ: Récupérer le nom du créateur (filtrer par tenant_id)
    created_by_name = None
    if role.created_by:
        creator = db.query(IAMUser).filter(
            IAMUser.tenant_id == service.tenant_id,
            IAMUser.id == role.created_by
        ).first()
        if creator:
            created_by_name = f"{creator.first_name or ''} {creator.last_name or ''}".strip() or creator.email

    return role_to_response(role, created_by_name)


@router.patch("/roles/{role_id}", response_model=RoleResponse)
@require_permission("iam.role.update")
async def update_role(
    role_id: UUID,
    data: RoleUpdate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Met à jour un rôle."""
    try:
        role = service.update_role(role_id, data, updated_by=current_user.id)
        return role_to_response(role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.role.delete")
async def delete_role(
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Supprime un rôle."""
    try:
        if not service.delete_role(role_id, deleted_by=current_user.id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/roles/assign", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.role.assign")
async def assign_role(
    data: RoleAssignment,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Attribue un rôle à un utilisateur."""
    try:
        service.assign_role_to_user(
            user_id=data.user_id,
            role_code=data.role_code,
            granted_by=current_user.id,
            expires_at=data.expires_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/roles/revoke", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.role.assign")
async def revoke_role(
    data: RoleAssignment,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Retire un rôle à un utilisateur."""
    service.revoke_role_from_user(
        user_id=data.user_id,
        role_code=data.role_code,
        revoked_by=current_user.id
    )
