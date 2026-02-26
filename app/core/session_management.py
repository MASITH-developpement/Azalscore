"""
AZALSCORE - Service de Gestion des Sessions et Tokens
======================================================

Gestion avancée des sessions utilisateur:
- Sessions concurrentes avec limites
- Refresh Token Rotation (RTR)
- Token Binding (liaison appareil)
- Sliding Sessions
- Détection de hijacking
- Révocation granulaire

Conformité:
- OWASP Session Management Cheat Sheet
- NIST SP 800-63B (Session Management)
- RFC 6819 (OAuth 2.0 Security)
"""
from __future__ import annotations


import hashlib
import hmac
import json
import logging
import os
import secrets
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional, Callable
from collections import defaultdict
import threading

from jose import JWTError, jwt

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class SessionStatus(str, Enum):
    """Statut d'une session."""
    ACTIVE = "active"
    IDLE = "idle"  # Pas d'activité récente
    EXPIRED = "expired"
    REVOKED = "revoked"
    LOGGED_OUT = "logged_out"
    HIJACKED = "hijacked"  # Suspicion de vol


class TokenType(str, Enum):
    """Types de tokens."""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    SERVICE = "service"
    REMEMBER_ME = "remember_me"


class RevocationReason(str, Enum):
    """Raison de révocation."""
    USER_LOGOUT = "user_logout"
    ADMIN_REVOKE = "admin_revoke"
    PASSWORD_CHANGE = "password_change"
    SECURITY_ALERT = "security_alert"
    CONCURRENT_LIMIT = "concurrent_limit"
    DEVICE_REVOKED = "device_revoked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    TOKEN_REFRESH = "token_refresh"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TokenClaims:
    """Claims standard d'un token."""
    sub: str  # User ID
    tenant_id: str
    jti: str  # Token ID unique
    iat: datetime
    exp: datetime
    token_type: TokenType
    session_id: Optional[str] = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    device_id: Optional[str] = None
    ip_address: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "sub": self.sub,
            "tenant_id": self.tenant_id,
            "jti": self.jti,
            "iat": int(self.iat.timestamp()),
            "exp": int(self.exp.timestamp()),
            "type": self.token_type.value,
            "sid": self.session_id,
            "roles": self.roles,
            "permissions": self.permissions,
            "device_id": self.device_id,
        }


@dataclass
class Session:
    """Session utilisateur."""
    session_id: str
    user_id: str
    tenant_id: str
    status: SessionStatus

    # Timestamps
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime

    # Tokens
    access_token_jti: Optional[str] = None
    refresh_token_jti: Optional[str] = None
    refresh_token_hash: Optional[str] = None

    # Contexte
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    device_fingerprint: Optional[str] = None
    geo_location: Optional[dict] = None

    # Métadonnées
    login_method: str = "password"  # password, sso, mfa, api_key
    mfa_verified: bool = False
    remember_me: bool = False

    # Révocation
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[RevocationReason] = None
    revoked_by: Optional[str] = None

    def is_active(self) -> bool:
        return (
            self.status == SessionStatus.ACTIVE
            and datetime.utcnow() < self.expires_at
        )

    def is_idle(self, idle_timeout_minutes: int = 30) -> bool:
        idle_threshold = datetime.utcnow() - timedelta(minutes=idle_timeout_minutes)
        return self.last_activity_at < idle_threshold


@dataclass
class RefreshToken:
    """Refresh token avec métadonnées."""
    token_hash: str
    jti: str
    user_id: str
    tenant_id: str
    session_id: str
    created_at: datetime
    expires_at: datetime
    used: bool = False
    used_at: Optional[datetime] = None
    rotation_count: int = 0
    previous_jti: Optional[str] = None
    device_id: Optional[str] = None


@dataclass
class APIKey:
    """Clé API pour intégrations."""
    key_id: str
    key_hash: str
    tenant_id: str
    name: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime] = None
    scopes: list[str] = field(default_factory=list)
    rate_limit: int = 1000  # Requêtes par heure
    ip_whitelist: list[str] = field(default_factory=list)
    is_active: bool = True
    created_by: Optional[str] = None


# =============================================================================
# SESSION STORE ABSTRACTION
# =============================================================================

class SessionStore(ABC):
    """Interface pour le stockage des sessions."""

    @abstractmethod
    def create_session(self, session: Session) -> None:
        """Crée une session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Session]:
        """Récupère une session."""
        pass

    @abstractmethod
    def update_session(self, session: Session) -> None:
        """Met à jour une session."""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> None:
        """Supprime une session."""
        pass

    @abstractmethod
    def get_user_sessions(self, user_id: str, tenant_id: str) -> list[Session]:
        """Récupère toutes les sessions d'un utilisateur."""
        pass

    @abstractmethod
    def count_active_sessions(self, user_id: str, tenant_id: str) -> int:
        """Compte les sessions actives."""
        pass


class InMemorySessionStore(SessionStore):
    """Session store en mémoire."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}
        self._user_sessions: dict[str, set[str]] = defaultdict(set)
        self._lock = threading.Lock()

    def create_session(self, session: Session) -> None:
        with self._lock:
            self._sessions[session.session_id] = session
            key = f"{session.tenant_id}:{session.user_id}"
            self._user_sessions[key].add(session.session_id)

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def update_session(self, session: Session) -> None:
        with self._lock:
            self._sessions[session.session_id] = session

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.pop(session_id, None)
            if session:
                key = f"{session.tenant_id}:{session.user_id}"
                self._user_sessions[key].discard(session_id)

    def get_user_sessions(self, user_id: str, tenant_id: str) -> list[Session]:
        key = f"{tenant_id}:{user_id}"
        session_ids = self._user_sessions.get(key, set())
        return [
            self._sessions[sid]
            for sid in session_ids
            if sid in self._sessions
        ]

    def count_active_sessions(self, user_id: str, tenant_id: str) -> int:
        sessions = self.get_user_sessions(user_id, tenant_id)
        return sum(1 for s in sessions if s.is_active())


class RedisSessionStore(SessionStore):
    """Session store utilisant Redis."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "azls:session:",
        ttl_hours: int = 24,
    ):
        self.prefix = prefix
        self.ttl_hours = ttl_hours
        self._client = None
        self._redis_url = redis_url

    def _get_client(self):
        if self._client is None:
            import redis
            self._client = redis.from_url(self._redis_url)
        return self._client

    def _serialize(self, session: Session) -> str:
        return json.dumps({
            "session_id": session.session_id,
            "user_id": session.user_id,
            "tenant_id": session.tenant_id,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "access_token_jti": session.access_token_jti,
            "refresh_token_jti": session.refresh_token_jti,
            "refresh_token_hash": session.refresh_token_hash,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "device_id": session.device_id,
            "device_fingerprint": session.device_fingerprint,
            "geo_location": session.geo_location,
            "login_method": session.login_method,
            "mfa_verified": session.mfa_verified,
            "remember_me": session.remember_me,
            "revoked_at": session.revoked_at.isoformat() if session.revoked_at else None,
            "revoked_reason": session.revoked_reason.value if session.revoked_reason else None,
            "revoked_by": session.revoked_by,
        })

    def _deserialize(self, data: str) -> Session:
        d = json.loads(data)
        return Session(
            session_id=d["session_id"],
            user_id=d["user_id"],
            tenant_id=d["tenant_id"],
            status=SessionStatus(d["status"]),
            created_at=datetime.fromisoformat(d["created_at"]),
            last_activity_at=datetime.fromisoformat(d["last_activity_at"]),
            expires_at=datetime.fromisoformat(d["expires_at"]),
            access_token_jti=d.get("access_token_jti"),
            refresh_token_jti=d.get("refresh_token_jti"),
            refresh_token_hash=d.get("refresh_token_hash"),
            ip_address=d.get("ip_address"),
            user_agent=d.get("user_agent"),
            device_id=d.get("device_id"),
            device_fingerprint=d.get("device_fingerprint"),
            geo_location=d.get("geo_location"),
            login_method=d.get("login_method", "password"),
            mfa_verified=d.get("mfa_verified", False),
            remember_me=d.get("remember_me", False),
            revoked_at=datetime.fromisoformat(d["revoked_at"]) if d.get("revoked_at") else None,
            revoked_reason=RevocationReason(d["revoked_reason"]) if d.get("revoked_reason") else None,
            revoked_by=d.get("revoked_by"),
        )

    def create_session(self, session: Session) -> None:
        client = self._get_client()
        key = f"{self.prefix}{session.session_id}"
        client.setex(
            key,
            timedelta(hours=self.ttl_hours),
            self._serialize(session)
        )

        # Index par utilisateur
        user_key = f"{self.prefix}user:{session.tenant_id}:{session.user_id}"
        client.sadd(user_key, session.session_id)

    def get_session(self, session_id: str) -> Optional[Session]:
        client = self._get_client()
        key = f"{self.prefix}{session_id}"
        data = client.get(key)
        if data:
            return self._deserialize(data.decode())
        return None

    def update_session(self, session: Session) -> None:
        self.create_session(session)  # Redis SETEX écrase

    def delete_session(self, session_id: str) -> None:
        client = self._get_client()
        session = self.get_session(session_id)
        if session:
            key = f"{self.prefix}{session_id}"
            client.delete(key)
            user_key = f"{self.prefix}user:{session.tenant_id}:{session.user_id}"
            client.srem(user_key, session_id)

    def get_user_sessions(self, user_id: str, tenant_id: str) -> list[Session]:
        client = self._get_client()
        user_key = f"{self.prefix}user:{tenant_id}:{user_id}"
        session_ids = client.smembers(user_key)
        sessions = []
        for sid in session_ids:
            session = self.get_session(sid.decode())
            if session:
                sessions.append(session)
        return sessions

    def count_active_sessions(self, user_id: str, tenant_id: str) -> int:
        sessions = self.get_user_sessions(user_id, tenant_id)
        return sum(1 for s in sessions if s.is_active())


# =============================================================================
# TOKEN BLACKLIST
# =============================================================================

class TokenBlacklist:
    """
    Blacklist de tokens révoqués.

    Stocke les JTI des tokens révoqués jusqu'à leur expiration naturelle.
    """

    def __init__(self, store_type: str = "memory"):
        self._memory_store: dict[str, float] = {}  # jti -> exp_timestamp
        self._lock = threading.Lock()
        self._redis_client = None
        self.store_type = store_type

    def add(self, jti: str, exp_timestamp: float) -> None:
        """Ajoute un token à la blacklist."""
        if self.store_type == "redis" and self._redis_client:
            ttl = int(exp_timestamp - time.time())
            if ttl > 0:
                self._redis_client.setex(f"blacklist:{jti}", ttl, "1")
        else:
            with self._lock:
                self._memory_store[jti] = exp_timestamp

    def is_blacklisted(self, jti: str) -> bool:
        """Vérifie si un token est blacklisté."""
        if self.store_type == "redis" and self._redis_client:
            return self._redis_client.exists(f"blacklist:{jti}") > 0
        else:
            with self._lock:
                exp = self._memory_store.get(jti)
                if exp:
                    if time.time() > exp:
                        del self._memory_store[jti]
                        return False
                    return True
                return False

    def cleanup(self) -> int:
        """Nettoie les entrées expirées."""
        count = 0
        current_time = time.time()
        with self._lock:
            expired = [jti for jti, exp in self._memory_store.items() if current_time > exp]
            for jti in expired:
                del self._memory_store[jti]
                count += 1
        return count


# =============================================================================
# TOKEN SERVICE
# =============================================================================

class TokenService:
    """
    Service de gestion des tokens JWT.

    Features:
    - Access tokens (courte durée)
    - Refresh tokens avec rotation
    - Token binding (liaison appareil)
    - Révocation instantanée
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
        remember_me_expire_days: int = 30,
        issuer: str = "azalscore",
        audience: str = "azalscore-api",
    ):
        self.secret_key = secret_key.encode()
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.remember_me_expire_days = remember_me_expire_days
        self.issuer = issuer
        self.audience = audience

        self._blacklist = TokenBlacklist()
        self._refresh_tokens: dict[str, RefreshToken] = {}
        self._lock = threading.RLock()  # RLock pour permettre appels imbriqués

    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        roles: list[str] = None,
        permissions: list[str] = None,
        device_id: Optional[str] = None,
        custom_claims: Optional[dict] = None,
    ) -> tuple[str, TokenClaims]:
        """
        Crée un access token.

        Returns:
            Tuple (token_string, claims)
        """
        now = datetime.utcnow()
        exp = now + timedelta(minutes=self.access_token_expire_minutes)
        jti = str(uuid.uuid4())

        claims = TokenClaims(
            sub=user_id,
            tenant_id=tenant_id,
            jti=jti,
            iat=now,
            exp=exp,
            token_type=TokenType.ACCESS,
            session_id=session_id,
            roles=roles or [],
            permissions=permissions or [],
            device_id=device_id,
        )

        payload = claims.to_dict()
        payload["iss"] = self.issuer
        payload["aud"] = self.audience

        if custom_claims:
            payload.update(custom_claims)

        token = jwt.encode(payload, self.secret_key.decode(), algorithm=self.algorithm)

        return token, claims

    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
        session_id: str,
        device_id: Optional[str] = None,
        remember_me: bool = False,
    ) -> tuple[str, RefreshToken]:
        """
        Crée un refresh token.

        Returns:
            Tuple (token_string, refresh_token_data)
        """
        now = datetime.utcnow()

        if remember_me:
            exp = now + timedelta(days=self.remember_me_expire_days)
        else:
            exp = now + timedelta(days=self.refresh_token_expire_days)

        jti = str(uuid.uuid4())

        # Générer un token opaque
        token_value = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(token_value.encode()).hexdigest()

        refresh_token = RefreshToken(
            token_hash=token_hash,
            jti=jti,
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            created_at=now,
            expires_at=exp,
            device_id=device_id,
        )

        # Stocker le refresh token
        with self._lock:
            self._refresh_tokens[token_hash] = refresh_token

        return token_value, refresh_token

    def rotate_refresh_token(
        self,
        old_token: str,
        device_id: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[RefreshToken], Optional[str]]:
        """
        Effectue une rotation du refresh token (RTR).

        Returns:
            Tuple (new_token, new_refresh_data, error_message)
        """
        old_token_hash = hashlib.sha256(old_token.encode()).hexdigest()

        with self._lock:
            old_refresh = self._refresh_tokens.get(old_token_hash)

            if not old_refresh:
                return None, None, "Invalid refresh token"

            # Vérifier l'expiration
            if datetime.utcnow() > old_refresh.expires_at:
                del self._refresh_tokens[old_token_hash]
                return None, None, "Refresh token expired"

            # Vérifier si déjà utilisé (possible replay attack)
            if old_refresh.used:
                # Révoquer toute la chaîne de tokens de cette session
                logger.warning(
                    f"Refresh token reuse detected for session {old_refresh.session_id}"
                )
                self._revoke_session_tokens(old_refresh.session_id)
                return None, None, "Token reuse detected - session revoked"

            # Marquer comme utilisé
            old_refresh.used = True
            old_refresh.used_at = datetime.utcnow()

            # Créer un nouveau token
            new_token, new_refresh = self.create_refresh_token(
                user_id=old_refresh.user_id,
                tenant_id=old_refresh.tenant_id,
                session_id=old_refresh.session_id,
                device_id=device_id or old_refresh.device_id,
            )

            new_refresh.rotation_count = old_refresh.rotation_count + 1
            new_refresh.previous_jti = old_refresh.jti

            # Blacklister l'ancien JTI
            self._blacklist.add(old_refresh.jti, old_refresh.expires_at.timestamp())

            return new_token, new_refresh, None

    def verify_access_token(
        self,
        token: str,
        verify_session: bool = True,
        session_store: Optional[SessionStore] = None,
    ) -> tuple[Optional[TokenClaims], Optional[str]]:
        """
        Vérifie un access token.

        Returns:
            Tuple (claims, error_message)
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key.decode(),
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience,
            )

            jti = payload.get("jti")

            # Vérifier la blacklist
            if self._blacklist.is_blacklisted(jti):
                return None, "Token has been revoked"

            # Reconstruire les claims
            claims = TokenClaims(
                sub=payload["sub"],
                tenant_id=payload["tenant_id"],
                jti=jti,
                iat=datetime.fromtimestamp(payload["iat"]),
                exp=datetime.fromtimestamp(payload["exp"]),
                token_type=TokenType(payload.get("type", "access")),
                session_id=payload.get("sid"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                device_id=payload.get("device_id"),
            )

            # Vérifier la session si demandé
            if verify_session and session_store and claims.session_id:
                session = session_store.get_session(claims.session_id)
                if not session or not session.is_active():
                    return None, "Session expired or revoked"

            return claims, None

        except jwt.ExpiredSignatureError:
            return None, "Token expired"
        except JWTError as e:
            return None, f"Invalid token: {e}"

    def revoke_token(self, jti: str, exp_timestamp: float) -> None:
        """Révoque un token spécifique."""
        self._blacklist.add(jti, exp_timestamp)
        logger.info(f"Token revoked: {jti}")

    def revoke_all_user_tokens(self, user_id: str, tenant_id: str) -> int:
        """Révoque tous les refresh tokens d'un utilisateur."""
        count = 0
        with self._lock:
            to_remove = []
            for token_hash, refresh in self._refresh_tokens.items():
                if refresh.user_id == user_id and refresh.tenant_id == tenant_id:
                    self._blacklist.add(refresh.jti, refresh.expires_at.timestamp())
                    to_remove.append(token_hash)
                    count += 1
            for token_hash in to_remove:
                del self._refresh_tokens[token_hash]

        logger.info(f"Revoked {count} tokens for user {user_id}")
        return count

    def _revoke_session_tokens(self, session_id: str) -> int:
        """Révoque tous les tokens d'une session."""
        count = 0
        with self._lock:
            to_remove = []
            for token_hash, refresh in self._refresh_tokens.items():
                if refresh.session_id == session_id:
                    self._blacklist.add(refresh.jti, refresh.expires_at.timestamp())
                    to_remove.append(token_hash)
                    count += 1
            for token_hash in to_remove:
                del self._refresh_tokens[token_hash]
        return count


# =============================================================================
# SESSION SERVICE
# =============================================================================

class SessionService:
    """
    Service principal de gestion des sessions.

    Features:
    - Création/destruction de sessions
    - Limite de sessions concurrentes
    - Sliding sessions (extension automatique)
    - Détection de hijacking
    - Gestion des tokens liés
    """

    def __init__(
        self,
        session_store: SessionStore,
        token_service: TokenService,
        max_concurrent_sessions: int = 5,
        session_duration_hours: int = 24,
        idle_timeout_minutes: int = 30,
        enable_sliding_sessions: bool = True,
        enable_hijack_detection: bool = True,
    ):
        self.session_store = session_store
        self.token_service = token_service
        self.max_concurrent_sessions = max_concurrent_sessions
        self.session_duration_hours = session_duration_hours
        self.idle_timeout_minutes = idle_timeout_minutes
        self.enable_sliding_sessions = enable_sliding_sessions
        self.enable_hijack_detection = enable_hijack_detection

        self._session_hooks: list[Callable] = []

    def register_hook(self, hook: Callable[[str, Session, dict], None]) -> None:
        """Enregistre un hook de session (création, destruction, etc.)."""
        self._session_hooks.append(hook)

    def create_session(
        self,
        user_id: str,
        tenant_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        login_method: str = "password",
        mfa_verified: bool = False,
        remember_me: bool = False,
        roles: list[str] = None,
        permissions: list[str] = None,
    ) -> tuple[Session, str, str]:
        """
        Crée une nouvelle session avec tokens.

        Returns:
            Tuple (session, access_token, refresh_token)
        """
        # Vérifier la limite de sessions concurrentes
        active_count = self.session_store.count_active_sessions(user_id, tenant_id)
        if active_count >= self.max_concurrent_sessions:
            # Révoquer la session la plus ancienne
            sessions = self.session_store.get_user_sessions(user_id, tenant_id)
            active_sessions = [s for s in sessions if s.is_active()]
            if active_sessions:
                oldest = min(active_sessions, key=lambda s: s.created_at)
                self.revoke_session(
                    oldest.session_id,
                    RevocationReason.CONCURRENT_LIMIT
                )

        # Créer la session
        now = datetime.utcnow()
        session_id = str(uuid.uuid4())

        session = Session(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status=SessionStatus.ACTIVE,
            created_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(hours=self.session_duration_hours),
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            device_fingerprint=device_fingerprint,
            login_method=login_method,
            mfa_verified=mfa_verified,
            remember_me=remember_me,
        )

        # Créer les tokens
        access_token, access_claims = self.token_service.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            roles=roles,
            permissions=permissions,
            device_id=device_id,
        )

        refresh_token, refresh_data = self.token_service.create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            device_id=device_id,
            remember_me=remember_me,
        )

        # Lier les tokens à la session
        session.access_token_jti = access_claims.jti
        session.refresh_token_jti = refresh_data.jti
        session.refresh_token_hash = refresh_data.token_hash

        # Sauvegarder
        self.session_store.create_session(session)

        # Appeler les hooks
        self._call_hooks("session_created", session, {
            "ip_address": ip_address,
            "login_method": login_method,
        })

        logger.info(
            f"Session created: {session_id} for user {user_id}",
            extra={
                "session_id": session_id,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "ip_address": ip_address,
            }
        )

        return session, access_token, refresh_token

    def refresh_session(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[str], Optional[Session], Optional[str]]:
        """
        Rafraîchit une session avec un refresh token.

        Returns:
            Tuple (new_access_token, new_refresh_token, session, error)
        """
        # Effectuer la rotation du refresh token
        new_refresh, refresh_data, error = self.token_service.rotate_refresh_token(
            refresh_token,
            device_id=device_id,
        )

        if error:
            return None, None, None, error

        # Récupérer et mettre à jour la session
        session = self.session_store.get_session(refresh_data.session_id)
        if not session:
            return None, None, None, "Session not found"

        if not session.is_active():
            return None, None, None, "Session expired or revoked"

        # Détection de hijacking
        if self.enable_hijack_detection:
            if self._detect_hijacking(session, ip_address, user_agent):
                self.revoke_session(
                    session.session_id,
                    RevocationReason.SUSPICIOUS_ACTIVITY
                )
                return None, None, None, "Session hijacking detected"

        # Créer un nouveau access token
        new_access, access_claims = self.token_service.create_access_token(
            user_id=session.user_id,
            tenant_id=session.tenant_id,
            session_id=session.session_id,
            device_id=device_id or session.device_id,
        )

        # Mettre à jour la session
        now = datetime.utcnow()
        session.last_activity_at = now
        session.access_token_jti = access_claims.jti
        session.refresh_token_jti = refresh_data.jti
        session.refresh_token_hash = refresh_data.token_hash

        # Sliding session: prolonger si activé
        if self.enable_sliding_sessions:
            remaining = (session.expires_at - now).total_seconds() / 3600
            if remaining < self.session_duration_hours / 2:
                session.expires_at = now + timedelta(hours=self.session_duration_hours)

        self.session_store.update_session(session)

        return new_access, new_refresh, session, None

    def touch_session(
        self,
        session_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[Session]:
        """
        Met à jour l'activité d'une session (heartbeat).
        """
        session = self.session_store.get_session(session_id)
        if not session or not session.is_active():
            return None

        # Détection de hijacking
        if self.enable_hijack_detection:
            if self._detect_hijacking(session, ip_address, user_agent):
                self.revoke_session(
                    session_id,
                    RevocationReason.SUSPICIOUS_ACTIVITY
                )
                return None

        session.last_activity_at = datetime.utcnow()

        # Sliding session
        if self.enable_sliding_sessions:
            now = datetime.utcnow()
            remaining = (session.expires_at - now).total_seconds() / 3600
            if remaining < self.session_duration_hours / 2:
                session.expires_at = now + timedelta(hours=self.session_duration_hours)

        self.session_store.update_session(session)
        return session

    def revoke_session(
        self,
        session_id: str,
        reason: RevocationReason,
        revoked_by: Optional[str] = None,
    ) -> bool:
        """Révoque une session."""
        session = self.session_store.get_session(session_id)
        if not session:
            return False

        now = datetime.utcnow()
        session.status = SessionStatus.REVOKED
        session.revoked_at = now
        session.revoked_reason = reason
        session.revoked_by = revoked_by

        # Révoquer les tokens
        if session.access_token_jti:
            self.token_service.revoke_token(
                session.access_token_jti,
                session.expires_at.timestamp()
            )
        if session.refresh_token_jti:
            self.token_service.revoke_token(
                session.refresh_token_jti,
                session.expires_at.timestamp()
            )

        self.session_store.update_session(session)

        # Appeler les hooks
        self._call_hooks("session_revoked", session, {
            "reason": reason.value,
            "revoked_by": revoked_by,
        })

        logger.info(
            f"Session revoked: {session_id}",
            extra={
                "session_id": session_id,
                "reason": reason.value,
                "revoked_by": revoked_by,
            }
        )

        return True

    def logout(
        self,
        session_id: str,
        revoke_all: bool = False,
    ) -> bool:
        """
        Déconnecte un utilisateur.

        Args:
            session_id: Session à déconnecter
            revoke_all: Révoquer toutes les sessions de l'utilisateur
        """
        session = self.session_store.get_session(session_id)
        if not session:
            return False

        if revoke_all:
            # Révoquer toutes les sessions
            return self.revoke_all_user_sessions(
                session.user_id,
                session.tenant_id,
                RevocationReason.USER_LOGOUT
            )
        else:
            # Révoquer uniquement cette session
            session.status = SessionStatus.LOGGED_OUT
            session.revoked_at = datetime.utcnow()
            session.revoked_reason = RevocationReason.USER_LOGOUT

            if session.access_token_jti:
                self.token_service.revoke_token(
                    session.access_token_jti,
                    session.expires_at.timestamp()
                )

            self.session_store.update_session(session)

            self._call_hooks("session_logout", session, {})
            return True

    def revoke_all_user_sessions(
        self,
        user_id: str,
        tenant_id: str,
        reason: RevocationReason,
        except_session_id: Optional[str] = None,
        revoked_by: Optional[str] = None,
    ) -> bool:
        """Révoque toutes les sessions d'un utilisateur."""
        sessions = self.session_store.get_user_sessions(user_id, tenant_id)

        for session in sessions:
            if except_session_id and session.session_id == except_session_id:
                continue
            if session.is_active():
                self.revoke_session(session.session_id, reason, revoked_by)

        # Révoquer tous les tokens
        self.token_service.revoke_all_user_tokens(user_id, tenant_id)

        logger.info(
            f"All sessions revoked for user {user_id}",
            extra={
                "user_id": user_id,
                "tenant_id": tenant_id,
                "reason": reason.value,
            }
        )

        return True

    def get_user_sessions(self, user_id: str, tenant_id: str) -> list[Session]:
        """Liste toutes les sessions d'un utilisateur."""
        return self.session_store.get_user_sessions(user_id, tenant_id)

    def cleanup_expired_sessions(self) -> int:
        """Nettoie les sessions expirées."""
        # Note: En production, utiliser un job schedulé
        count = 0
        # L'implémentation dépend du store
        self.token_service._blacklist.cleanup()
        return count

    def _detect_hijacking(
        self,
        session: Session,
        current_ip: Optional[str],
        current_user_agent: Optional[str],
    ) -> bool:
        """
        Détecte une potentielle usurpation de session.

        Heuristiques:
        - Changement de pays (via IP)
        - Changement majeur de user-agent
        """
        if not current_ip or not session.ip_address:
            return False

        # Changement d'IP (simpliste - en production utiliser GeoIP)
        # On pourrait tolérer des changements d'IP dans le même /24
        if current_ip != session.ip_address:
            # Extraire le préfixe /24
            old_prefix = ".".join(session.ip_address.split(".")[:3])
            new_prefix = ".".join(current_ip.split(".")[:3])

            if old_prefix != new_prefix:
                logger.warning(
                    f"IP change detected for session {session.session_id}: "
                    f"{session.ip_address} -> {current_ip}"
                )
                # En production: vérifier si c'est un VPN/proxy connu
                # Pour l'instant, on ne bloque pas sur changement d'IP seul

        # Changement de user-agent majeur
        if current_user_agent and session.user_agent:
            if not self._similar_user_agent(session.user_agent, current_user_agent):
                logger.warning(
                    f"User-agent change detected for session {session.session_id}"
                )
                return True

        return False

    def _similar_user_agent(self, ua1: str, ua2: str) -> bool:
        """Vérifie si deux user-agents sont similaires."""
        # Extraire les parties principales (navigateur, OS)
        def normalize(ua: str) -> str:
            # Garder seulement les mots-clés importants
            keywords = ["Chrome", "Firefox", "Safari", "Edge", "Windows", "Mac", "Linux", "Android", "iOS"]
            return " ".join(k for k in keywords if k.lower() in ua.lower())

        return normalize(ua1) == normalize(ua2)

    def _call_hooks(self, event: str, session: Session, context: dict) -> None:
        """Appelle les hooks enregistrés."""
        for hook in self._session_hooks:
            try:
                hook(event, session, context)
            except Exception as e:
                logger.error(f"Session hook error: {e}")


# =============================================================================
# API KEY SERVICE
# =============================================================================

class APIKeyService:
    """
    Service de gestion des clés API.
    """

    def __init__(self, secret_key: bytes):
        self._secret_key = secret_key
        self._api_keys: dict[str, APIKey] = {}
        self._lock = threading.Lock()

    def create_api_key(
        self,
        tenant_id: str,
        name: str,
        scopes: list[str],
        created_by: str,
        expires_days: Optional[int] = None,
        rate_limit: int = 1000,
        ip_whitelist: Optional[list[str]] = None,
    ) -> tuple[str, APIKey]:
        """
        Crée une nouvelle clé API.

        Returns:
            Tuple (key_value, api_key_data)
        """
        # Générer la clé
        key_id = f"azls_{secrets.token_hex(8)}"
        key_secret = secrets.token_urlsafe(32)
        full_key = f"{key_id}.{key_secret}"

        # Hash de la clé pour stockage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        now = datetime.utcnow()
        expires_at = None
        if expires_days:
            expires_at = now + timedelta(days=expires_days)

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            tenant_id=tenant_id,
            name=name,
            created_at=now,
            expires_at=expires_at,
            scopes=scopes,
            rate_limit=rate_limit,
            ip_whitelist=ip_whitelist or [],
            created_by=created_by,
        )

        with self._lock:
            self._api_keys[key_id] = api_key

        logger.info(
            f"API key created: {key_id}",
            extra={
                "key_id": key_id,
                "tenant_id": tenant_id,
                "name": name,
            }
        )

        return full_key, api_key

    def validate_api_key(
        self,
        key: str,
        required_scope: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> tuple[Optional[APIKey], Optional[str]]:
        """
        Valide une clé API.

        Returns:
            Tuple (api_key_data, error_message)
        """
        try:
            parts = key.split(".")
            if len(parts) != 2:
                return None, "Invalid key format"

            key_id = parts[0]
            key_hash = hashlib.sha256(key.encode()).hexdigest()

            with self._lock:
                api_key = self._api_keys.get(key_id)

            if not api_key:
                return None, "API key not found"

            # Vérifier le hash
            if not hmac.compare_digest(api_key.key_hash, key_hash):
                return None, "Invalid API key"

            # Vérifier si active
            if not api_key.is_active:
                return None, "API key is disabled"

            # Vérifier l'expiration
            if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
                return None, "API key expired"

            # Vérifier l'IP
            if api_key.ip_whitelist and client_ip:
                if client_ip not in api_key.ip_whitelist:
                    return None, "IP not whitelisted"

            # Vérifier le scope
            if required_scope and required_scope not in api_key.scopes:
                if "*" not in api_key.scopes:
                    return None, f"Missing scope: {required_scope}"

            # Mettre à jour last_used
            api_key.last_used_at = datetime.utcnow()

            return api_key, None

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None, "Validation error"

    def revoke_api_key(self, key_id: str) -> bool:
        """Révoque une clé API."""
        with self._lock:
            if key_id in self._api_keys:
                self._api_keys[key_id].is_active = False
                logger.info(f"API key revoked: {key_id}")
                return True
        return False

    def list_api_keys(self, tenant_id: str) -> list[APIKey]:
        """Liste les clés API d'un tenant."""
        with self._lock:
            return [
                k for k in self._api_keys.values()
                if k.tenant_id == tenant_id
            ]


# =============================================================================
# FACTORY
# =============================================================================

_session_service: Optional[SessionService] = None
_token_service: Optional[TokenService] = None
_api_key_service: Optional[APIKeyService] = None


def initialize_session_services(
    secret_key: str,
    session_store_type: str = "memory",
    redis_url: Optional[str] = None,
    max_concurrent_sessions: int = 5,
    access_token_expire_minutes: int = 15,
    refresh_token_expire_days: int = 7,
) -> dict:
    """
    Initialise les services de gestion de sessions.

    Returns:
        Dict avec les instances de services
    """
    global _session_service, _token_service, _api_key_service

    # Token service
    _token_service = TokenService(
        secret_key=secret_key,
        access_token_expire_minutes=access_token_expire_minutes,
        refresh_token_expire_days=refresh_token_expire_days,
    )

    # Session store
    if session_store_type == "redis" and redis_url:
        session_store = RedisSessionStore(redis_url=redis_url)
    else:
        session_store = InMemorySessionStore()

    # Session service
    _session_service = SessionService(
        session_store=session_store,
        token_service=_token_service,
        max_concurrent_sessions=max_concurrent_sessions,
    )

    # API Key service
    _api_key_service = APIKeyService(secret_key.encode())

    logger.info(
        "Session services initialized",
        extra={
            "session_store": session_store_type,
            "max_concurrent_sessions": max_concurrent_sessions,
        }
    )

    return {
        "session": _session_service,
        "token": _token_service,
        "api_key": _api_key_service,
    }


def get_session_service() -> SessionService:
    """Retourne le service de sessions."""
    global _session_service
    if _session_service is None:
        raise RuntimeError("Session service not initialized. Call initialize_session_services first.")
    return _session_service


def get_token_service() -> TokenService:
    """Retourne le service de tokens."""
    global _token_service
    if _token_service is None:
        raise RuntimeError("Token service not initialized. Call initialize_session_services first.")
    return _token_service


def get_api_key_service() -> APIKeyService:
    """Retourne le service de clés API."""
    global _api_key_service
    if _api_key_service is None:
        raise RuntimeError("API Key service not initialized. Call initialize_session_services first.")
    return _api_key_service
