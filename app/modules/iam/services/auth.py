"""
AZALS MODULE T0 - Auth Service
===============================

Gestion de l'authentification.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from app.core.config import get_settings
from app.core.security import create_access_token
from app.modules.iam.models import IAMUser, IAMSession, IAMRateLimit, IAMTokenBlacklist, SessionStatus
from .base import BaseIAMService

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService(BaseIAMService[IAMUser]):
    """Service d'authentification."""

    model = IAMUser

    def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> Tuple[Optional[IAMUser], str | None]:
        """Authentifie un utilisateur."""
        logger.info("Authentication attempt | tenant=%s email=%s", self.tenant_id, email)

        user = self._base_query().filter(IAMUser.email == email).first()

        if not user:
            logger.warning("Auth failed | tenant=%s email=%s reason=user_not_found", self.tenant_id, email)
            return None, "Email ou mot de passe incorrect"

        if not user.is_active:
            logger.warning("Auth failed | tenant=%s email=%s reason=inactive", self.tenant_id, email)
            return None, "Compte désactivé"

        if user.is_locked:
            if user.locked_until and user.locked_until > datetime.utcnow():
                logger.warning("Auth failed | tenant=%s email=%s reason=locked", self.tenant_id, email)
                return None, "Compte verrouillé"
            # Déverrouiller automatiquement si délai expiré
            user.is_locked = False
            user.lock_reason = None
            user.locked_until = None

        if not self._verify_password(password, user.password_hash):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            # Verrouiller après trop de tentatives
            max_attempts = 5
            if user.failed_login_attempts >= max_attempts:
                user.is_locked = True
                user.lock_reason = "Trop de tentatives de connexion"
                user.locked_at = datetime.utcnow()
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)

            self.db.commit()
            logger.warning("Auth failed | tenant=%s email=%s reason=bad_password attempts=%s",
                          self.tenant_id, email, user.failed_login_attempts)
            return None, "Email ou mot de passe incorrect"

        # Succès - reset tentatives
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        user.last_login_ip = ip_address
        self.db.commit()

        logger.info("Auth success | tenant=%s user_id=%s email=%s", self.tenant_id, user.id, email)
        return user, None

    def create_session(
        self,
        user: IAMUser,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_info: dict | None = None
    ) -> Tuple[str, str, IAMSession]:
        """Crée une session et génère les tokens."""
        # Générer les tokens
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "tenant_id": self.tenant_id,
                "email": user.email
            }
        )
        refresh_token = secrets.token_urlsafe(64)

        # Créer la session
        session = IAMSession(
            tenant_id=self.tenant_id,
            user_id=user.id,
            refresh_token_hash=self._hash_password(refresh_token),
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_info.get("fingerprint") if device_info else None,
            status=SessionStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        self.db.add(session)
        self.db.commit()

        return access_token, refresh_token, session

    def refresh_session(self, refresh_token: str) -> Tuple[Optional[str], Optional[str], str | None]:
        """Rafraîchit une session avec le refresh token."""
        sessions = self.db.query(IAMSession).filter(
            IAMSession.tenant_id == self.tenant_id,
            IAMSession.status == SessionStatus.ACTIVE,
            IAMSession.expires_at > datetime.utcnow()
        ).all()

        for session in sessions:
            if self._verify_password(refresh_token, session.refresh_token_hash):
                user = self.db.query(IAMUser).filter(
                    IAMUser.id == session.user_id,
                    IAMUser.tenant_id == self.tenant_id
                ).first()

                if not user or not user.is_active:
                    return None, None, "Utilisateur inactif"

                # Générer nouveau access token
                new_access_token = create_access_token(
                    data={
                        "sub": str(user.id),
                        "tenant_id": self.tenant_id,
                        "email": user.email
                    }
                )

                # Optionnel: rotation du refresh token
                new_refresh_token = secrets.token_urlsafe(64)
                session.refresh_token_hash = self._hash_password(new_refresh_token)
                session.last_activity = datetime.utcnow()
                self.db.commit()

                return new_access_token, new_refresh_token, None

        return None, None, "Session invalide ou expirée"

    def logout(self, user_id: UUID, session_id: UUID | None = None) -> bool:
        """Déconnecte un utilisateur."""
        query = self.db.query(IAMSession).filter(
            IAMSession.tenant_id == self.tenant_id,
            IAMSession.user_id == user_id,
            IAMSession.status == SessionStatus.ACTIVE
        )

        if session_id:
            query = query.filter(IAMSession.id == session_id)

        sessions = query.all()
        for session in sessions:
            session.status = SessionStatus.REVOKED
            session.revoked_at = datetime.utcnow()

        self.db.commit()
        return len(sessions) > 0

    def logout_all(self, user_id: UUID) -> int:
        """Déconnecte toutes les sessions d'un utilisateur."""
        result = self.db.query(IAMSession).filter(
            IAMSession.tenant_id == self.tenant_id,
            IAMSession.user_id == user_id,
            IAMSession.status == SessionStatus.ACTIVE
        ).update({
            "status": SessionStatus.REVOKED,
            "revoked_at": datetime.utcnow()
        })

        self.db.commit()
        return result

    def blacklist_token(self, token: str, user_id: UUID, reason: str = None) -> bool:
        """Ajoute un token à la blacklist."""
        blacklist = IAMTokenBlacklist(
            tenant_id=self.tenant_id,
            token_hash=self._hash_password(token),
            user_id=user_id,
            blacklisted_at=datetime.utcnow(),
            reason=reason
        )
        self.db.add(blacklist)
        self.db.commit()
        return True

    def get_active_sessions(self, user_id: UUID) -> list:
        """Récupère les sessions actives d'un utilisateur."""
        return self.db.query(IAMSession).filter(
            IAMSession.tenant_id == self.tenant_id,
            IAMSession.user_id == user_id,
            IAMSession.status == SessionStatus.ACTIVE,
            IAMSession.expires_at > datetime.utcnow()
        ).all()
