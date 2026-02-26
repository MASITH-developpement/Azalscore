"""
AZALSCORE - IAM Invitations Router
Endpoints pour la gestion des invitations
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.core.models import User

from ..decorators import require_permission
from ..schemas import (
    InvitationAccept,
    InvitationCreate,
    InvitationResponse,
)
from .helpers import get_service, user_to_response

router = APIRouter(tags=["invitations"])


@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
@require_permission("iam.invitation.create")
async def create_invitation(
    data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Crée une invitation."""
    try:
        invitation = service.create_invitation(
            email=data.email,
            role_codes=data.role_codes,
            group_codes=data.group_codes,
            expires_in_hours=data.expires_in_hours,
            invited_by=current_user.id
        )

        return InvitationResponse(
            id=invitation.id,
            tenant_id=invitation.tenant_id,
            email=invitation.email,
            status=invitation.status.value,
            roles_to_assign=[],
            groups_to_assign=[],
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            invited_by=invitation.invited_by,
            accepted_at=invitation.accepted_at
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/invitations/accept")
async def accept_invitation(
    data: InvitationAccept,
    service=Depends(get_service)
):
    """Accepte une invitation et crée le compte."""
    user, error = service.accept_invitation(
        token=data.token,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name
    )

    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # Retourne UserResponse (le compte créé)
    return user_to_response(user)
