"""
AZALSCORE AI Authentication Module

Authentification MFA pour les utilisateurs privilégiés.
L'authentification sert à vérifier l'identité, pas à limiter l'autorité légitime.

Conformité: AZA-SEC-002, AZA-SEC-003
"""

import os
import uuid
import hmac
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from app.ai.audit import get_audit_logger, AuditEventType, AuditEvent

logger = logging.getLogger(__name__)


class PrivilegeLevel(Enum):
    """Niveaux de privilège"""
    ANONYMOUS = "anonymous"
    USER = "user"
    OPERATOR = "operator"
    ADMIN = "admin"
    OWNER = "owner"  # Propriétaire du système


class AuthMethod(Enum):
    """Méthodes d'authentification"""
    PASSWORD = "password"
    EMAIL_CODE = "email_code"
    SMS_CODE = "sms_code"
    TOTP = "totp"
    BIOMETRIC = "biometric"


@dataclass
class AuthSession:
    """Session authentifiée"""
    session_id: str
    user_id: str
    privilege_level: PrivilegeLevel
    created_at: datetime
    expires_at: datetime
    auth_methods_used: List[AuthMethod] = field(default_factory=list)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Vérifie si la session est encore valide"""
        return datetime.utcnow() < self.expires_at

    def is_mfa_complete(self) -> bool:
        """Vérifie si MFA est complet (au moins 2 facteurs)"""
        return len(self.auth_methods_used) >= 2


@dataclass
class PendingMFA:
    """Code MFA en attente"""
    user_id: str
    code: str
    method: AuthMethod
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    max_attempts: int = 3


class AIAuthManager:
    """
    Gestionnaire d'authentification AZALSCORE

    Responsabilités:
    - Gérer l'authentification des utilisateurs
    - Implémenter le MFA (Multi-Factor Authentication)
    - Gérer les sessions et privilèges
    - Journaliser toutes les tentatives d'accès
    """

    # Configuration des utilisateurs privilégiés
    # En production, ceci viendrait d'une base de données sécurisée
    PRIVILEGED_USERS = {
        "owner": {
            "user_id": "owner-001",
            "email": "contact@masith.fr",
            "name": "Stéphane Moreau",
            "entity": "MASITH",
            "privilege_level": PrivilegeLevel.OWNER,
            "mfa_required": True,
        }
    }

    # Durée de validité des sessions
    SESSION_DURATION = {
        PrivilegeLevel.ANONYMOUS: timedelta(hours=1),
        PrivilegeLevel.USER: timedelta(hours=8),
        PrivilegeLevel.OPERATOR: timedelta(hours=4),
        PrivilegeLevel.ADMIN: timedelta(hours=2),
        PrivilegeLevel.OWNER: timedelta(hours=1),  # Sessions courtes pour le propriétaire
    }

    # Durée de validité des codes MFA
    MFA_CODE_VALIDITY = timedelta(minutes=10)

    def __init__(self):
        self.audit = get_audit_logger()
        self._sessions: Dict[str, AuthSession] = {}
        self._pending_mfa: Dict[str, PendingMFA] = {}
        self._failed_attempts: Dict[str, List[datetime]] = {}

    def authenticate_password(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> Optional[AuthSession]:
        """
        Authentification par mot de passe (premier facteur)

        Args:
            username: Nom d'utilisateur
            password: Mot de passe
            ip_address: Adresse IP du client

        Returns:
            AuthSession partielle (MFA requis) ou None si échec
        """
        # Vérifier le rate limiting
        if self._is_rate_limited(username):
            logger.warning(f"[AUTH] Rate limited: {username}")
            return None

        # Vérifier les identifiants
        # En production: vérification contre une base de données sécurisée
        user_config = self.PRIVILEGED_USERS.get(username)

        if not user_config:
            self._record_failed_attempt(username)
            self.audit.log_event(AuditEvent(
                event_type=AuditEventType.SYSTEM_ERROR,
                source_module="auth",
                action="login_failed",
                input_data={"username": username},
                success=False,
                error_message="User not found"
            ))
            return None

        # Vérifier le mot de passe (en production: hash bcrypt)
        # Pour la démo, on utilise une variable d'environnement
        expected_password_hash = os.getenv("AZALSCORE_OWNER_PASSWORD_HASH", "")
        provided_hash = hashlib.sha256(password.encode()).hexdigest()

        if not hmac.compare_digest(provided_hash, expected_password_hash):
            self._record_failed_attempt(username)
            logger.warning(f"[AUTH] Invalid password for: {username}")
            return None

        # Créer une session partielle (MFA requis)
        session = AuthSession(
            session_id=str(uuid.uuid4()),
            user_id=user_config["user_id"],
            privilege_level=user_config["privilege_level"],
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=15),  # Court pour MFA
            auth_methods_used=[AuthMethod.PASSWORD],
            ip_address=ip_address,
            metadata={
                "name": user_config["name"],
                "entity": user_config["entity"],
                "mfa_pending": True
            }
        )

        self._sessions[session.session_id] = session

        # Générer et envoyer le code MFA
        if user_config.get("mfa_required", True):
            self._initiate_mfa(user_config["user_id"], user_config["email"])

        logger.info(f"[AUTH] Password auth success for: {username}, MFA pending")

        return session

    def verify_mfa_code(
        self,
        session_id: str,
        code: str,
        method: AuthMethod = AuthMethod.EMAIL_CODE
    ) -> Optional[AuthSession]:
        """
        Vérifie un code MFA

        Args:
            session_id: ID de la session en cours
            code: Code MFA fourni
            method: Méthode MFA utilisée

        Returns:
            AuthSession complète ou None si échec
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"[AUTH] MFA verification: session not found")
            return None

        # Vérifier le code en attente
        pending = self._pending_mfa.get(session.user_id)
        if not pending:
            logger.warning(f"[AUTH] No pending MFA for user: {session.user_id}")
            return None

        # Vérifier l'expiration
        if datetime.utcnow() > pending.expires_at:
            del self._pending_mfa[session.user_id]
            logger.warning(f"[AUTH] MFA code expired for: {session.user_id}")
            return None

        # Vérifier les tentatives
        pending.attempts += 1
        if pending.attempts > pending.max_attempts:
            del self._pending_mfa[session.user_id]
            self._invalidate_session(session_id)
            logger.warning(f"[AUTH] MFA max attempts exceeded for: {session.user_id}")
            return None

        # Vérifier le code
        if not hmac.compare_digest(code, pending.code):
            logger.warning(f"[AUTH] Invalid MFA code for: {session.user_id}")
            return None

        # MFA réussi - mettre à jour la session
        session.auth_methods_used.append(method)
        session.metadata["mfa_pending"] = False
        session.metadata["mfa_verified_at"] = datetime.utcnow().isoformat()

        # Étendre la durée de la session
        session.expires_at = datetime.utcnow() + self.SESSION_DURATION.get(
            session.privilege_level,
            timedelta(hours=1)
        )

        # Nettoyer
        del self._pending_mfa[session.user_id]

        # Journaliser
        self.audit.log_admin_action(
            user_id=session.user_id,
            action="mfa_verified",
            details={
                "method": method.value,
                "privilege_level": session.privilege_level.value
            },
            session_id=session_id
        )

        logger.info(f"[AUTH] MFA verified for: {session.user_id}")

        return session

    def get_session(self, session_id: str) -> Optional[AuthSession]:
        """Récupère une session par son ID"""
        session = self._sessions.get(session_id)
        if session and session.is_valid():
            return session
        elif session:
            # Session expirée, la supprimer
            del self._sessions[session_id]
        return None

    def validate_privilege(
        self,
        session_id: str,
        required_level: PrivilegeLevel
    ) -> bool:
        """
        Vérifie si une session a le niveau de privilège requis

        Args:
            session_id: ID de la session
            required_level: Niveau requis

        Returns:
            True si autorisé
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # Vérifier MFA pour les niveaux élevés
        if required_level in [PrivilegeLevel.ADMIN, PrivilegeLevel.OWNER]:
            if not session.is_mfa_complete():
                return False

        # Hiérarchie des privilèges
        hierarchy = [
            PrivilegeLevel.ANONYMOUS,
            PrivilegeLevel.USER,
            PrivilegeLevel.OPERATOR,
            PrivilegeLevel.ADMIN,
            PrivilegeLevel.OWNER
        ]

        session_index = hierarchy.index(session.privilege_level)
        required_index = hierarchy.index(required_level)

        return session_index >= required_index

    def logout(self, session_id: str) -> bool:
        """Déconnecte une session"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            self.audit.log_admin_action(
                user_id=session.user_id,
                action="logout",
                details={},
                session_id=session_id
            )
            del self._sessions[session_id]
            return True
        return False

    def _initiate_mfa(self, user_id: str, email: str):
        """
        Initie le processus MFA

        Args:
            user_id: ID utilisateur
            email: Email pour envoyer le code
        """
        # Générer un code à 6 chiffres
        code = "".join([str(secrets.randbelow(10)) for _ in range(6)])

        self._pending_mfa[user_id] = PendingMFA(
            user_id=user_id,
            code=code,
            method=AuthMethod.EMAIL_CODE,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.MFA_CODE_VALIDITY
        )

        # En production: envoyer le code par email
        # Pour la démo, on le logue (À NE PAS FAIRE EN PRODUCTION!)
        logger.info(f"[AUTH] MFA code for {email}: {code}")

        # TODO: Implémenter l'envoi réel par email
        # self._send_email(email, "Code de vérification AZALSCORE", f"Votre code: {code}")

    def _invalidate_session(self, session_id: str):
        """Invalide une session"""
        if session_id in self._sessions:
            del self._sessions[session_id]

    def _record_failed_attempt(self, username: str):
        """Enregistre une tentative échouée pour le rate limiting"""
        if username not in self._failed_attempts:
            self._failed_attempts[username] = []

        self._failed_attempts[username].append(datetime.utcnow())

        # Garder seulement les tentatives des 15 dernières minutes
        cutoff = datetime.utcnow() - timedelta(minutes=15)
        self._failed_attempts[username] = [
            t for t in self._failed_attempts[username] if t > cutoff
        ]

    def _is_rate_limited(self, username: str) -> bool:
        """Vérifie si un utilisateur est rate limité"""
        attempts = self._failed_attempts.get(username, [])

        # Plus de 5 tentatives en 15 minutes = blocage
        cutoff = datetime.utcnow() - timedelta(minutes=15)
        recent_attempts = [t for t in attempts if t > cutoff]

        return len(recent_attempts) >= 5

    def get_active_sessions_for_user(self, user_id: str) -> List[AuthSession]:
        """Liste les sessions actives pour un utilisateur"""
        return [
            s for s in self._sessions.values()
            if s.user_id == user_id and s.is_valid()
        ]


# Instance singleton
_auth_manager: Optional[AIAuthManager] = None


def get_auth_manager() -> AIAuthManager:
    """Récupère l'instance singleton du gestionnaire d'auth"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AIAuthManager()
    return _auth_manager
