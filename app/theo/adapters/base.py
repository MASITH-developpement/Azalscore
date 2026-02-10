"""
THÉO — Base Adapter
====================

Interface de base pour les adapters AZALSCORE.
Chaque adapter expose des actions vocales pour un domaine métier.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================
# TYPES
# ============================================================

class ActionStatus(str, Enum):
    """Statut d'exécution d'une action."""
    SUCCESS = "success"
    PENDING_CONFIRMATION = "pending_confirmation"
    NEEDS_CLARIFICATION = "needs_clarification"
    ERROR = "error"
    UNAUTHORIZED = "unauthorized"


@dataclass
class AdapterAction:
    """
    Définition d'une action exposée par un adapter.

    Exemple:
        AdapterAction(
            name="creer_devis",
            description="Créer un nouveau devis",
            required_params=["client_name"],
            optional_params=["montant", "description"],
            confirmation_required=True
        )
    """
    name: str
    description: str
    required_params: List[str] = field(default_factory=list)
    optional_params: List[str] = field(default_factory=list)
    confirmation_required: bool = False
    voice_examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required_params": self.required_params,
            "optional_params": self.optional_params,
            "confirmation_required": self.confirmation_required,
            "voice_examples": self.voice_examples
        }


@dataclass
class AdapterResult:
    """Résultat d'une action adapter."""

    status: ActionStatus
    message: str  # Message vocal pour l'utilisateur
    data: Dict[str, Any] = field(default_factory=dict)
    confirmation_prompt: Optional[str] = None
    clarification_questions: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return self.status == ActionStatus.SUCCESS

    @property
    def needs_confirmation(self) -> bool:
        return self.status == ActionStatus.PENDING_CONFIRMATION

    @property
    def needs_clarification(self) -> bool:
        return self.status == ActionStatus.NEEDS_CLARIFICATION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "message": self.message,
            "data": self.data,
            "confirmation_prompt": self.confirmation_prompt,
            "clarification_questions": self.clarification_questions,
            "next_actions": self.next_actions
        }


# ============================================================
# INTERFACE ADAPTER
# ============================================================

class BaseAdapter(ABC):
    """
    Interface de base pour tous les adapters Théo.

    Un adapter:
    - Encapsule un module métier AZALSCORE
    - Expose des actions vocales standardisées
    - Gère les confirmations et clarifications
    - Retourne des messages optimisés pour la voix
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom de l'adapter (ex: 'commercial', 'treasury')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description pour Théo."""
        pass

    @property
    @abstractmethod
    def actions(self) -> List[AdapterAction]:
        """Actions disponibles."""
        pass

    @abstractmethod
    async def execute(
        self,
        action_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """
        Exécute une action.

        Args:
            action_name: Nom de l'action
            params: Paramètres extraits de l'intent
            context: Contexte (session_id, user_id, tenant_id, etc.)

        Returns:
            AdapterResult avec message vocal
        """
        pass

    @abstractmethod
    async def confirm(
        self,
        action_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> AdapterResult:
        """
        Confirme et exécute une action en attente.

        Args:
            action_name: Nom de l'action
            params: Paramètres
            context: Contexte incluant pending_action

        Returns:
            AdapterResult
        """
        pass

    def get_action(self, action_name: str) -> Optional[AdapterAction]:
        """Récupère une action par son nom."""
        for action in self.actions:
            if action.name == action_name:
                return action
        return None

    def list_actions(self) -> List[Dict[str, Any]]:
        """Liste les actions disponibles."""
        return [action.to_dict() for action in self.actions]

    def _voice_error(self, message: str) -> AdapterResult:
        """Helper pour créer une erreur vocale."""
        return AdapterResult(
            status=ActionStatus.ERROR,
            message=message
        )

    def _voice_success(
        self,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Helper pour créer un succès vocal."""
        return AdapterResult(
            status=ActionStatus.SUCCESS,
            message=message,
            data=data or {}
        )

    def _voice_confirm(
        self,
        prompt: str,
        data: Optional[Dict[str, Any]] = None
    ) -> AdapterResult:
        """Helper pour demander confirmation."""
        return AdapterResult(
            status=ActionStatus.PENDING_CONFIRMATION,
            message=prompt,
            confirmation_prompt=prompt,
            data=data or {}
        )

    def _voice_clarify(
        self,
        message: str,
        questions: List[str]
    ) -> AdapterResult:
        """Helper pour demander clarification."""
        return AdapterResult(
            status=ActionStatus.NEEDS_CLARIFICATION,
            message=message,
            clarification_questions=questions
        )


# ============================================================
# REGISTRE DES ADAPTERS
# ============================================================

class AdapterRegistry:
    """Registre des adapters disponibles."""

    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}

    def register(self, adapter: BaseAdapter) -> None:
        """Enregistre un adapter."""
        self._adapters[adapter.name] = adapter
        logger.info("Registered adapter: %s", adapter.name)

    def get(self, name: str) -> Optional[BaseAdapter]:
        """Récupère un adapter par nom."""
        return self._adapters.get(name)

    def list_all(self) -> List[BaseAdapter]:
        """Liste tous les adapters."""
        return list(self._adapters.values())

    def find_by_action(self, action_name: str) -> Optional[BaseAdapter]:
        """Trouve l'adapter qui gère une action."""
        for adapter in self._adapters.values():
            if adapter.get_action(action_name):
                return adapter
        return None

    def get_all_actions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retourne toutes les actions par adapter."""
        return {
            adapter.name: adapter.list_actions()
            for adapter in self._adapters.values()
        }


# Singleton
_adapter_registry: Optional[AdapterRegistry] = None


def get_adapter_registry() -> AdapterRegistry:
    """Retourne l'instance singleton du registre."""
    global _adapter_registry
    if _adapter_registry is None:
        _adapter_registry = AdapterRegistry()
    return _adapter_registry
