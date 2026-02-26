"""
AZALSCORE - IAM Groups Router
Endpoints pour la gestion des groupes
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.core.models import User

from ..decorators import require_permission
from ..schemas import (
    GroupCreate,
    GroupListResponse,
    GroupMembership,
    GroupResponse,
)
from .helpers import get_service, group_to_response

router = APIRouter(tags=["groups"])


@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.group.create")
async def create_group(
    data: GroupCreate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Crée un nouveau groupe."""
    try:
        group = service.create_group(data, created_by=current_user.id)
        return group_to_response(group)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/groups", response_model=GroupListResponse)
@require_permission("iam.group.read")
async def list_groups(
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Liste tous les groupes."""
    groups = service.list_groups()

    return GroupListResponse(
        items=[group_to_response(g) for g in groups],
        total=len(groups)
    )


@router.post("/groups/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.group.update")
async def add_group_members(
    group_id: UUID,
    data: GroupMembership,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Ajoute des utilisateurs à un groupe."""
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for user_id in data.user_ids:
        service.add_user_to_group(user_id, group.code, added_by=current_user.id)


@router.delete("/groups/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT)
@require_permission("iam.group.update")
async def remove_group_members(
    group_id: UUID,
    data: GroupMembership,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Retire des utilisateurs d'un groupe."""
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    for user_id in data.user_ids:
        service.remove_user_from_group(user_id, group.code, removed_by=current_user.id)
