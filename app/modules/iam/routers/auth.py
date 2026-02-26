"""
AZALSCORE - IAM Authentication Router
Endpoints pour l'authentification (login, refresh, logout)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.dependencies import get_current_user
from app.core.models import User
from app.core.security import decode_access_token
from app.core.token_blacklist import blacklist_token

from ..schemas import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from .helpers import get_service, user_to_response

router = APIRouter(tags=["auth"])
security = HTTPBearer()


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: Request,
    data: LoginRequest,
    service=Depends(get_service)
):
    """
    Authentification utilisateur.
    Retourne access_token et refresh_token si succès.
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    # Authentifier
    user, error = service.authenticate(
        email=data.email,
        password=data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )

    # Vérifier MFA si activé
    if user.mfa_enabled:
        if not data.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Code MFA requis",
                headers={"X-MFA-Required": "true"}
            )

        if not service.check_mfa_code(user.id, data.mfa_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Code MFA invalide"
            )

    # Créer session
    access_token, refresh_token, session = service.create_session(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent,
        remember_me=data.remember_me
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes
        user=user_to_response(user)
    )


@router.post("/auth/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    service=Depends(get_service)
):
    """Rafraîchit les tokens avec le refresh_token."""
    ip_address = request.client.host if request.client else None

    access_token, refresh_token, error = service.refresh_tokens(
        refresh_token=data.refresh_token,
        ip_address=ip_address
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )

    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """
    Déconnexion utilisateur.

    - Par défaut : révoque uniquement le token actuel (via JTI)
    - all_sessions=True : révoque toutes les sessions de l'utilisateur
    """
    if data.all_sessions:
        # Révoquer toutes les sessions
        service.revoke_all_sessions(current_user.id, "User logout all")
    else:
        # Extraire et révoquer le token actuel via JTI
        token = credentials.credentials
        payload = decode_access_token(token)

        if payload:
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                # Révoquer ce token spécifique
                blacklist_token(jti, float(exp))
            else:
                # Fallback: révoquer toutes les sessions si JTI manquant
                service.revoke_all_sessions(current_user.id, "User logout (no JTI)")
