"""
AZALSCORE - IAM Sessions Router
Endpoints pour la gestion des sessions
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user
from app.core.models import User

from ..schemas import (
    SessionListResponse,
    SessionResponse,
    SessionRevoke,
)
from .helpers import get_service

router = APIRouter(tags=["sessions"])


@router.get("/users/me/sessions", response_model=SessionListResponse)
async def list_my_sessions(
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Liste les sessions de l'utilisateur connecté."""
    from ..models import IAMSession, SessionStatus

    sessions = service.db.query(IAMSession).filter(
        IAMSession.user_id == current_user.id,
        IAMSession.tenant_id == service.tenant_id,
        IAMSession.status == SessionStatus.ACTIVE
    ).order_by(IAMSession.created_at.desc()).all()

    return SessionListResponse(
        items=[
            SessionResponse(
                id=s.id,
                token_jti=s.token_jti,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                status=s.status.value,
                created_at=s.created_at,
                expires_at=s.expires_at,
                last_activity_at=s.last_activity_at,
                is_current=False  # NOTE: Phase 2 - comparer avec JTI du token
            )
            for s in sessions
        ],
        total=len(sessions)
    )


@router.post("/users/me/sessions/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_sessions(
    data: SessionRevoke,
    current_user: User = Depends(get_current_user),
    service=Depends(get_service)
):
    """Révoque des sessions."""
    if data.session_ids:
        # Révoquer sessions spécifiques
        from ..models import IAMSession, SessionStatus

        for session_id in data.session_ids:
            session = service.db.query(IAMSession).filter(
                IAMSession.id == session_id,
                IAMSession.user_id == current_user.id,
                IAMSession.tenant_id == service.tenant_id
            ).first()

            if session:
                session.status = SessionStatus.REVOKED
                session.revoked_at = datetime.utcnow()
                session.revoked_reason = data.reason or "User revoked"

        service.db.commit()
    else:
        # Révoquer toutes sauf courante
        service.revoke_all_sessions(current_user.id, data.reason or "User revoked all")
