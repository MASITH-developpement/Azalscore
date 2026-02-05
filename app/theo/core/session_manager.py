"""
THÉO — Gestionnaire de Sessions
===============================

Gère les sessions vocales utilisateur:
- Contexte de conversation
- Mémoire courte (interaction en cours)
- Mémoire longue contrôlée (préférences fonctionnelles)
- État d'attente (confirmation, clarification)
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import logging

from app.theo.core.intent_detector import Intent, IntentCategory

logger = logging.getLogger(__name__)


# ============================================================
# ÉTATS DE SESSION
# ============================================================

class SessionState(str, Enum):
    """États possibles d'une session Théo."""

    IDLE = "idle"                        # Prêt à écouter
    LISTENING = "listening"              # En écoute active
    PROCESSING = "processing"            # Traitement en cours
    SPEAKING = "speaking"                # Théo parle
    AWAITING_CONFIRMATION = "awaiting_confirmation"  # Attend oui/non
    AWAITING_CLARIFICATION = "awaiting_clarification"  # Attend précision
    PAUSED = "paused"                    # En pause (interruption)
    ERROR = "error"                      # Erreur récupérable


# ============================================================
# NIVEAUX D'AUTORITÉ
# ============================================================

class AuthorityLevel(str, Enum):
    """Niveaux d'autorité utilisateur."""

    USER = "user"        # Utilisateur standard
    DESIGN = "design"    # Concepteur / Designer
    ADMIN = "admin"      # Administrateur
    CREATOR = "creator"  # Créateur (accès total)


# ============================================================
# MESSAGE DE CONVERSATION
# ============================================================

@dataclass
class ConversationMessage:
    """Message dans l'historique de conversation."""

    id: str
    role: str  # "user" | "theo" | "system"
    content: str
    timestamp: datetime
    intent: Optional[Intent] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# PENDING ACTION
# ============================================================

@dataclass
class PendingAction:
    """Action en attente de confirmation/clarification."""

    intent: Intent
    created_at: datetime
    expires_at: datetime
    clarification_attempts: int = 0
    max_clarification_attempts: int = 3
    adapter_data: Dict[str, Any] = field(default_factory=dict)  # Données adapter


# ============================================================
# SESSION THÉO
# ============================================================

@dataclass
class TheoSession:
    """Session vocale Théo."""

    session_id: str
    user_id: Optional[str]
    tenant_id: Optional[str]
    companion_id: str = "theo"
    authority_level: AuthorityLevel = AuthorityLevel.USER

    # État
    state: SessionState = SessionState.IDLE
    mode: str = "driving"  # "driving" | "desktop" | "mobile"

    # Contexte
    current_page: Optional[str] = None
    erp_context: Dict[str, Any] = field(default_factory=dict)

    # Conversation
    messages: List[ConversationMessage] = field(default_factory=list)
    pending_action: Optional[PendingAction] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=2))

    # Préférences (mémoire longue contrôlée)
    preferences: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Vérifie si la session est expirée."""
        return datetime.utcnow() > self.expires_at

    def is_awaiting_input(self) -> bool:
        """Vérifie si la session attend une entrée utilisateur."""
        return self.state in [
            SessionState.AWAITING_CONFIRMATION,
            SessionState.AWAITING_CLARIFICATION
        ]

    def add_message(
        self,
        role: str,
        content: str,
        intent: Optional[Intent] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Ajoute un message à la conversation."""
        msg = ConversationMessage(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            intent=intent,
            metadata=metadata or {}
        )
        self.messages.append(msg)
        self.last_activity = datetime.utcnow()

        # Limiter l'historique (mémoire courte)
        max_messages = 20
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]

        return msg

    def get_conversation_context(self, max_messages: int = 5) -> List[Dict[str, str]]:
        """Retourne le contexte de conversation récent."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages[-max_messages:]
        ]

    def set_pending_action(
        self,
        intent: Intent,
        timeout_seconds: int = 60,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Définit une action en attente."""
        self.pending_action = PendingAction(
            intent=intent,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=timeout_seconds),
            adapter_data=data or {}
        )

        if intent.missing_fields:
            self.state = SessionState.AWAITING_CLARIFICATION
        else:
            self.state = SessionState.AWAITING_CONFIRMATION

    def clear_pending_action(self) -> None:
        """Efface l'action en attente."""
        self.pending_action = None
        self.state = SessionState.IDLE

    def requires_confirmation(self, intent: Intent) -> bool:
        """Détermine si une intention requiert confirmation."""
        # CREATOR n'a jamais besoin de confirmation
        if self.authority_level == AuthorityLevel.CREATOR:
            return False

        # Les actions métier requièrent toujours confirmation
        if intent.category == IntentCategory.BUSINESS_ACTION:
            return True

        return intent.requires_confirmation

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise la session."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "companion_id": self.companion_id,
            "authority_level": self.authority_level.value,
            "state": self.state.value,
            "mode": self.mode,
            "current_page": self.current_page,
            "message_count": len(self.messages),
            "has_pending_action": self.pending_action is not None,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_expired": self.is_expired()
        }


# ============================================================
# GESTIONNAIRE DE SESSIONS
# ============================================================

class SessionManager:
    """
    Gestionnaire de sessions Théo.

    Gère le cycle de vie des sessions vocales.
    """

    def __init__(self):
        self._sessions: Dict[str, TheoSession] = {}
        self._user_sessions: Dict[str, str] = {}  # user_id -> session_id

    def create(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        companion_id: str = "theo",
        authority_level: AuthorityLevel = AuthorityLevel.USER,
        mode: str = "driving"
    ) -> TheoSession:
        """
        Crée une nouvelle session.

        Args:
            user_id: ID utilisateur (optionnel)
            tenant_id: ID tenant (optionnel)
            companion_id: ID du compagnon actif
            authority_level: Niveau d'autorité
            mode: Mode d'interaction (driving, desktop, mobile)

        Returns:
            Nouvelle session
        """
        session_id = str(uuid.uuid4())

        # Fermer l'ancienne session de l'utilisateur si elle existe
        if user_id and user_id in self._user_sessions:
            old_session_id = self._user_sessions[user_id]
            self.close(old_session_id)

        session = TheoSession(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            companion_id=companion_id,
            authority_level=authority_level,
            mode=mode
        )

        self._sessions[session_id] = session
        if user_id:
            self._user_sessions[user_id] = session_id

        logger.info("Created session %s for user %s", session_id, user_id)
        return session

    def get(self, session_id: str) -> Optional[TheoSession]:
        """Récupère une session par ID."""
        session = self._sessions.get(session_id)
        if session and session.is_expired():
            self.close(session_id)
            return None
        return session

    def get_by_user(self, user_id: str) -> Optional[TheoSession]:
        """Récupère la session d'un utilisateur."""
        session_id = self._user_sessions.get(user_id)
        if session_id:
            return self.get(session_id)
        return None

    def close(self, session_id: str) -> bool:
        """Ferme une session."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        # Retirer du mapping utilisateur
        if session.user_id and session.user_id in self._user_sessions:
            del self._user_sessions[session.user_id]

        del self._sessions[session_id]
        logger.info("Closed session %s", session_id)
        return True

    def end(self, session_id: str) -> bool:
        """Alias pour close()."""
        return self.close(session_id)

    def cleanup_expired(self) -> int:
        """Nettoie les sessions expirées."""
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired()
        ]
        for sid in expired:
            self.close(sid)
        return len(expired)

    def get_active_count(self) -> int:
        """Retourne le nombre de sessions actives."""
        return len(self._sessions)

    def status(self) -> Dict[str, Any]:
        """Retourne le statut du gestionnaire."""
        return {
            "active_sessions": len(self._sessions),
            "sessions": [
                session.to_dict()
                for session in self._sessions.values()
            ]
        }


# ============================================================
# SINGLETON
# ============================================================

_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Retourne l'instance singleton du gestionnaire."""
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager
