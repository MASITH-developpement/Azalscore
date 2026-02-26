"""
AZALSCORE - IAM MFA Router
Endpoints pour l'authentification multi-facteurs
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.core.models import User

from ..schemas import MFADisable, MFASetupResponse, MFAVerify
from .helpers import get_service

router = APIRouter(tags=["mfa"])


@router.post("/users/me/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Configure MFA pour l'utilisateur connecté."""
    secret, qr_uri, backup_codes = service.setup_mfa(current_user.id)

    return MFASetupResponse(
        secret=secret,
        qr_code_uri=qr_uri,
        backup_codes=backup_codes
    )


@router.post("/users/me/mfa/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify_mfa(
    data: MFAVerify,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Vérifie et active MFA."""
    if not service.verify_mfa(current_user.id, data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code MFA invalide"
        )


@router.post("/users/me/mfa/disable", status_code=status.HTTP_204_NO_CONTENT)
async def disable_mfa(
    data: MFADisable,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Désactive MFA."""
    if not service.disable_mfa(current_user.id, data.password, data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe ou code MFA invalide"
        )
