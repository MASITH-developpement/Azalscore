"""
AZALS MODULE T0 - Invitation Service
=====================================

Gestion des invitations utilisateurs.
"""

import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from app.modules.iam.models import IAMInvitation, InvitationStatus
from .base import BaseIAMService

logger = logging.getLogger(__name__)


class InvitationService(BaseIAMService[IAMInvitation]):
    """Service de gestion des invitations."""

    model = IAMInvitation

    def create(
        self,
        email: str,
        role_codes: list[str],
        invited_by: int,
        expires_in_days: int = 7,
        message: str | None = None
    ) -> IAMInvitation:
        """Crée une invitation."""
        # Vérifier si invitation active existe déjà
        existing = self._base_query().filter(
            IAMInvitation.email == email,
            IAMInvitation.status == InvitationStatus.PENDING,
            IAMInvitation.expires_at > datetime.utcnow()
        ).first()

        if existing:
            raise ValueError(f"Une invitation active existe déjà pour {email}")

        # Générer token unique
        token = secrets.token_urlsafe(64)

        invitation = IAMInvitation(
            tenant_id=self.tenant_id,
            email=email,
            token=token,
            role_codes=",".join(role_codes),
            status=InvitationStatus.PENDING,
            invited_by=invited_by,
            message=message,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )

        self.db.add(invitation)
        self._audit_log("INVITATION_CREATED", "INVITATION", None, invited_by,
                       new_values={"email": email, "roles": role_codes})
        self.db.commit()
        self.db.refresh(invitation)

        logger.info("Invitation created | tenant=%s email=%s invited_by=%s",
                   self.tenant_id, email, invited_by)
        return invitation

    def get_by_token(self, token: str) -> Optional[IAMInvitation]:
        """Récupère une invitation par token."""
        return self._base_query().filter(
            IAMInvitation.token == token,
            IAMInvitation.status == InvitationStatus.PENDING,
            IAMInvitation.expires_at > datetime.utcnow()
        ).first()

    def get_by_email(self, email: str) -> Optional[IAMInvitation]:
        """Récupère une invitation par email."""
        return self._base_query().filter(
            IAMInvitation.email == email,
            IAMInvitation.status == InvitationStatus.PENDING
        ).first()

    def list(
        self,
        status: InvitationStatus | None = None,
        include_expired: bool = False
    ) -> List[IAMInvitation]:
        """Liste les invitations."""
        query = self._base_query()

        if status:
            query = query.filter(IAMInvitation.status == status)

        if not include_expired:
            query = query.filter(IAMInvitation.expires_at > datetime.utcnow())

        return query.order_by(IAMInvitation.created_at.desc()).all()

    def accept(self, token: str, user_id: UUID) -> Optional[IAMInvitation]:
        """Accepte une invitation."""
        invitation = self.get_by_token(token)
        if not invitation:
            return None

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_by = user_id

        self._audit_log("INVITATION_ACCEPTED", "INVITATION", invitation.id, None,
                       new_values={"user_id": str(user_id)})
        self.db.commit()

        logger.info("Invitation accepted | tenant=%s email=%s user_id=%s",
                   self.tenant_id, invitation.email, user_id)
        return invitation

    def cancel(self, invitation_id: UUID, cancelled_by: int) -> bool:
        """Annule une invitation."""
        invitation = self._base_query().filter(
            IAMInvitation.id == invitation_id,
            IAMInvitation.status == InvitationStatus.PENDING
        ).first()

        if not invitation:
            return False

        invitation.status = InvitationStatus.CANCELLED
        invitation.cancelled_at = datetime.utcnow()
        invitation.cancelled_by = cancelled_by

        self._audit_log("INVITATION_CANCELLED", "INVITATION", invitation_id, cancelled_by)
        self.db.commit()

        logger.info("Invitation cancelled | tenant=%s invitation_id=%s",
                   self.tenant_id, invitation_id)
        return True

    def resend(self, invitation_id: UUID, resent_by: int) -> Optional[IAMInvitation]:
        """Renvoie une invitation (génère nouveau token, réinitialise expiration)."""
        invitation = self._base_query().filter(
            IAMInvitation.id == invitation_id,
            IAMInvitation.status == InvitationStatus.PENDING
        ).first()

        if not invitation:
            return None

        invitation.token = secrets.token_urlsafe(64)
        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        invitation.resent_count = (invitation.resent_count or 0) + 1
        invitation.last_resent_at = datetime.utcnow()

        self._audit_log("INVITATION_RESENT", "INVITATION", invitation_id, resent_by)
        self.db.commit()

        logger.info("Invitation resent | tenant=%s invitation_id=%s",
                   self.tenant_id, invitation_id)
        return invitation

    def cleanup_expired(self) -> int:
        """Nettoie les invitations expirées."""
        result = self._base_query().filter(
            IAMInvitation.status == InvitationStatus.PENDING,
            IAMInvitation.expires_at <= datetime.utcnow()
        ).update({"status": InvitationStatus.EXPIRED})

        self.db.commit()
        return result
