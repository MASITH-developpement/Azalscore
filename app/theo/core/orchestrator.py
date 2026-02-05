"""
THÉO — Orchestrateur Central
============================

Pipeline principal:
Voix → Wake Word → STT → Traduction Compagnon → Intention → Capacité →
Délégation → Réponse → TTS → Restitution

Théo ne sait rien. Théo sait à qui demander.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import asyncio

from app.theo.core.capability_registry import (
    CapabilityRegistry, CapabilityType, Capability,
    get_capability_registry
)
from app.theo.core.intent_detector import (
    IntentDetector, Intent, IntentCategory, ActionType,
    get_intent_detector
)
from app.theo.core.session_manager import (
    SessionManager, TheoSession, SessionState, AuthorityLevel,
    get_session_manager
)

# Import différé du délégateur pour éviter import circulaire
_delegator = None

def _get_delegator():
    """Lazy import du délégateur."""
    global _delegator
    if _delegator is None:
        from app.theo.delegator import get_delegator
        _delegator = get_delegator()
    return _delegator

logger = logging.getLogger(__name__)


# ============================================================
# RÉSULTAT D'ORCHESTRATION
# ============================================================

class OrchestratorResultType(str, Enum):
    """Types de résultats de l'orchestrateur."""

    RESPONSE = "response"                # Réponse directe
    CONFIRMATION_REQUIRED = "confirmation_required"  # Demande confirmation
    CLARIFICATION_REQUIRED = "clarification_required"  # Demande clarification
    ACTION_EXECUTED = "action_executed"  # Action exécutée
    ACTION_CANCELLED = "action_cancelled"  # Action annulée
    ACTION_POSTPONED = "action_postponed"  # Action reportée
    INTERRUPTED = "interrupted"          # Interruption
    ERROR = "error"                      # Erreur


@dataclass
class OrchestratorResult:
    """Résultat du pipeline d'orchestration."""

    type: OrchestratorResultType
    speech_text: str                     # Texte à synthétiser
    session_state: SessionState
    intent: Optional[Intent] = None
    action_result: Optional[Dict[str, Any]] = None
    visual_state: str = "idle"
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "speech_text": self.speech_text,
            "session_state": self.session_state.value,
            "intent": self.intent.to_dict() if self.intent else None,
            "action_result": self.action_result,
            "visual_state": self.visual_state,
            "metadata": self.metadata
        }


# ============================================================
# ORCHESTRATEUR THÉO
# ============================================================

class TheoOrchestrator:
    """
    Orchestrateur central de Théo.

    Gère le pipeline complet de traitement des requêtes vocales.
    """

    def __init__(
        self,
        registry: Optional[CapabilityRegistry] = None,
        detector: Optional[IntentDetector] = None,
        session_manager: Optional[SessionManager] = None
    ):
        self._registry = registry or get_capability_registry()
        self._detector = detector or get_intent_detector()
        self._sessions = session_manager or get_session_manager()

        # Responses templates (mode conduite = phrases courtes)
        self._responses = {
            "greeting": [
                "Oui, je t'écoute.",
                "Je suis là.",
                "Qu'est-ce que je peux faire ?",
            ],
            "confirmation_ask": "Je fais ça ?",
            "confirmed": "C'est fait.",
            "cancelled": "Annulé.",
            "postponed": "OK, je note pour plus tard.",
            "not_understood": "J'ai pas compris, tu peux répéter ?",
            "error": "Il y a eu un problème. On réessaie ?",
            "no_capability": "Je ne peux pas faire ça pour l'instant.",
            "interrupted": "OK.",
            "waiting": "Je suis là quand tu veux.",
        }

    async def process(
        self,
        session_id: str,
        transcription: str,
        context: Optional[Dict[str, Any]] = None
    ) -> OrchestratorResult:
        """
        Traite une transcription vocale.

        Args:
            session_id: ID de la session
            transcription: Texte transcrit (après STT)
            context: Contexte additionnel

        Returns:
            Résultat de l'orchestration
        """
        context = context or {}

        # 1. Récupérer la session
        session = self._sessions.get(session_id)
        if not session:
            return OrchestratorResult(
                type=OrchestratorResultType.ERROR,
                speech_text="Session expirée. Dis 'Théo, s'il te plaît' pour recommencer.",
                session_state=SessionState.ERROR
            )

        # Mettre à jour le contexte de la session
        session.last_activity = datetime.utcnow()
        if "current_page" in context:
            session.current_page = context["current_page"]

        # 2. Ajouter le message utilisateur
        session.add_message("user", transcription)

        # 3. Détection d'intention
        detection_context = {
            "awaiting_confirmation": session.state == SessionState.AWAITING_CONFIRMATION,
            "awaiting_clarification": session.state == SessionState.AWAITING_CLARIFICATION,
        }
        intent = self._detector.detect(transcription, detection_context)

        logger.info(
            "Session %s: Detected intent "
            "%s/%s "
            "(confidence: %s)",
            session_id, intent.category.value, intent.action.value, intent.confidence
        )

        # 4. Router selon l'intention
        result = await self._route_intent(session, intent)

        # 5. Ajouter la réponse Théo
        session.add_message("theo", result.speech_text, intent=intent)

        return result

    async def _route_intent(
        self,
        session: TheoSession,
        intent: Intent
    ) -> OrchestratorResult:
        """Route l'intention vers le bon gestionnaire."""

        # Interruptions (priorité max)
        if intent.category == IntentCategory.INTERRUPTION:
            return self._handle_interruption(session, intent)

        # Confirmations
        if intent.category == IntentCategory.CONFIRMATION:
            return await self._handle_confirmation(session, intent)

        # Salutations
        if intent.action == ActionType.GREET:
            return self._handle_greeting(session)

        if intent.action == ActionType.THANK:
            return OrchestratorResult(
                type=OrchestratorResultType.RESPONSE,
                speech_text="De rien.",
                session_state=SessionState.IDLE,
                visual_state="soft_smile"
            )

        # Actions métier
        if intent.category == IntentCategory.BUSINESS_ACTION:
            return await self._handle_business_action(session, intent)

        # Navigation
        if intent.category == IntentCategory.NAVIGATION:
            return await self._handle_navigation(session, intent)

        # Information (fallback)
        return await self._handle_information(session, intent)

    def _handle_interruption(
        self,
        session: TheoSession,
        intent: Intent
    ) -> OrchestratorResult:
        """Gère les interruptions (stop, attends)."""
        session.clear_pending_action()

        if intent.action == ActionType.STOP:
            session.state = SessionState.IDLE
            return OrchestratorResult(
                type=OrchestratorResultType.INTERRUPTED,
                speech_text="",  # Silence
                session_state=SessionState.IDLE,
                visual_state="idle"
            )

        if intent.action == ActionType.WAIT:
            session.state = SessionState.PAUSED
            return OrchestratorResult(
                type=OrchestratorResultType.INTERRUPTED,
                speech_text=self._responses["waiting"],
                session_state=SessionState.PAUSED,
                visual_state="idle"
            )

        return OrchestratorResult(
            type=OrchestratorResultType.INTERRUPTED,
            speech_text=self._responses["interrupted"],
            session_state=SessionState.IDLE,
            visual_state="idle"
        )

    async def _handle_confirmation(
        self,
        session: TheoSession,
        intent: Intent
    ) -> OrchestratorResult:
        """Gère les confirmations (oui, non, annule, plus tard)."""

        if not session.pending_action:
            # Pas d'action en attente
            return OrchestratorResult(
                type=OrchestratorResultType.RESPONSE,
                speech_text="Il n'y a rien en attente.",
                session_state=SessionState.IDLE,
                visual_state="neutral"
            )

        pending = session.pending_action

        # Oui → Exécuter
        if intent.action == ActionType.CONFIRM_YES:
            return await self._execute_action(session, pending.intent)

        # Non / Annule → Annuler
        if intent.action in [ActionType.CONFIRM_NO, ActionType.CANCEL]:
            session.clear_pending_action()
            return OrchestratorResult(
                type=OrchestratorResultType.ACTION_CANCELLED,
                speech_text=self._responses["cancelled"],
                session_state=SessionState.IDLE,
                intent=pending.intent,
                visual_state="neutral"
            )

        # Plus tard → Reporter
        if intent.action == ActionType.POSTPONE:
            # TODO: Sauvegarder pour rappel
            session.clear_pending_action()
            return OrchestratorResult(
                type=OrchestratorResultType.ACTION_POSTPONED,
                speech_text=self._responses["postponed"],
                session_state=SessionState.IDLE,
                intent=pending.intent,
                visual_state="neutral"
            )

        return OrchestratorResult(
            type=OrchestratorResultType.RESPONSE,
            speech_text=self._responses["not_understood"],
            session_state=session.state,
            visual_state="confused"
        )

    def _handle_greeting(self, session: TheoSession) -> OrchestratorResult:
        """Gère les salutations."""
        import random
        response = random.choice(self._responses["greeting"])

        return OrchestratorResult(
            type=OrchestratorResultType.RESPONSE,
            speech_text=response,
            session_state=SessionState.IDLE,
            visual_state="soft_smile"
        )

    async def _handle_business_action(
        self,
        session: TheoSession,
        intent: Intent
    ) -> OrchestratorResult:
        """Gère les actions métier AZALSCORE."""

        # Vérifier les champs manquants
        if intent.missing_fields:
            session.set_pending_action(intent)
            return OrchestratorResult(
                type=OrchestratorResultType.CLARIFICATION_REQUIRED,
                speech_text=intent.clarification_question or "Je n'ai pas compris, tu peux préciser ?",
                session_state=SessionState.AWAITING_CLARIFICATION,
                intent=intent,
                visual_state="listening"
            )

        # Vérifier si confirmation requise
        if session.requires_confirmation(intent):
            session.set_pending_action(intent)

            # Générer la phrase de confirmation
            action_desc = self._describe_action(intent)
            speech = f"{action_desc}. {self._responses['confirmation_ask']}"

            return OrchestratorResult(
                type=OrchestratorResultType.CONFIRMATION_REQUIRED,
                speech_text=speech,
                session_state=SessionState.AWAITING_CONFIRMATION,
                intent=intent,
                visual_state="awaiting"
            )

        # Exécuter directement (CREATOR ou pas de confirmation)
        return await self._execute_action(session, intent)

    async def _handle_navigation(
        self,
        session: TheoSession,
        intent: Intent
    ) -> OrchestratorResult:
        """Gère les requêtes de navigation."""

        # Vérifier les champs manquants
        if intent.missing_fields:
            session.set_pending_action(intent)
            return OrchestratorResult(
                type=OrchestratorResultType.CLARIFICATION_REQUIRED,
                speech_text=intent.clarification_question or "Où veux-tu aller ?",
                session_state=SessionState.AWAITING_CLARIFICATION,
                intent=intent,
                visual_state="listening"
            )

        # Déléguer au provider de navigation
        return await self._delegate_to_capability(session, intent)

    async def _handle_information(
        self,
        session: TheoSession,
        intent: Intent
    ) -> OrchestratorResult:
        """Gère les demandes d'information."""
        return await self._delegate_to_capability(session, intent)

    async def _execute_action(
        self,
        session: TheoSession,
        intent: Intent
    ) -> OrchestratorResult:
        """Exécute une action confirmée via délégation."""
        # Récupérer les données adapter avant de clear
        adapter_data = {}
        if session.pending_action:
            adapter_data = session.pending_action.adapter_data

        session.clear_pending_action()

        # Déléguer avec flag confirmed
        return await self._delegate_to_capability(
            session, intent, confirmed=True, adapter_data=adapter_data
        )

    async def _delegate_to_capability(
        self,
        session: TheoSession,
        intent: Intent,
        confirmed: bool = False,
        adapter_data: Optional[Dict[str, Any]] = None
    ) -> OrchestratorResult:
        """Délègue au délégateur d'adapters AZALSCORE."""

        try:
            session.state = SessionState.PROCESSING

            # Préparer le contexte
            context = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "tenant_id": session.tenant_id,
                "authority_level": session.authority_level.value,
                "current_page": session.current_page,
                "conversation": session.get_conversation_context(),
                "confirmed": confirmed,
                "pending_action": adapter_data or {}
            }

            # Utiliser le nouveau délégateur
            delegator = _get_delegator()
            result = await delegator.delegate(intent, context)

            logger.info("Delegator result: %s", result.status)

            # Mapper les résultats de l'adapter vers OrchestratorResult
            from app.theo.adapters.base import ActionStatus

            if result.status == ActionStatus.SUCCESS:
                return OrchestratorResult(
                    type=OrchestratorResultType.ACTION_EXECUTED,
                    speech_text=result.message,
                    session_state=SessionState.IDLE,
                    intent=intent,
                    action_result=result.data,
                    visual_state="confirmation"
                )

            elif result.status == ActionStatus.PENDING_CONFIRMATION:
                # Sauvegarder l'action en attente
                session.set_pending_action(intent, data=result.data)
                return OrchestratorResult(
                    type=OrchestratorResultType.CONFIRMATION_REQUIRED,
                    speech_text=result.message,
                    session_state=SessionState.AWAITING_CONFIRMATION,
                    intent=intent,
                    action_result=result.data,
                    visual_state="awaiting"
                )

            elif result.status == ActionStatus.NEEDS_CLARIFICATION:
                return OrchestratorResult(
                    type=OrchestratorResultType.CLARIFICATION_REQUIRED,
                    speech_text=result.message,
                    session_state=SessionState.AWAITING_CLARIFICATION,
                    intent=intent,
                    visual_state="listening"
                )

            elif result.status == ActionStatus.UNAUTHORIZED:
                return OrchestratorResult(
                    type=OrchestratorResultType.ERROR,
                    speech_text="Tu n'as pas l'autorisation pour ça.",
                    session_state=SessionState.IDLE,
                    intent=intent,
                    visual_state="neutral"
                )

            else:  # ERROR
                return OrchestratorResult(
                    type=OrchestratorResultType.ERROR,
                    speech_text=result.message or self._responses["error"],
                    session_state=SessionState.IDLE,
                    intent=intent,
                    visual_state="error"
                )

        except Exception as e:
            logger.error("Delegation error: %s", e)

            # Fallback vers registre de capacités si le délégateur échoue
            capability = self._registry.resolve(intent.capability_required)

            if capability:
                try:
                    result = await capability.provider.execute(
                        capability=intent.capability_required,
                        params=intent.entities,
                        context=context
                    )
                    if result.get("success"):
                        return OrchestratorResult(
                            type=OrchestratorResultType.ACTION_EXECUTED,
                            speech_text=result.get("message", self._responses["confirmed"]),
                            session_state=SessionState.IDLE,
                            intent=intent,
                            action_result=result,
                            visual_state="confirmation"
                        )
                except Exception as e:
                    logger.error(
                        "[THEO_FALLBACK] Échec exécution capability fallback",
                        extra={
                            "capability": intent.capability_required,
                            "error": str(e)[:300],
                            "consequence": "fallback_to_error_response"
                        }
                    )

            return OrchestratorResult(
                type=OrchestratorResultType.ERROR,
                speech_text=self._responses["error"],
                session_state=SessionState.IDLE,
                intent=intent,
                visual_state="error"
            )

    def _describe_action(self, intent: Intent) -> str:
        """Génère une description courte de l'action."""
        descriptions = {
            ActionType.CREATE_INVOICE: "Je crée une facture",
            ActionType.CREATE_QUOTE: "Je crée un devis",
            ActionType.CREATE_TICKET: "Je crée un ticket",
            ActionType.CREATE_NOTE: "Je note",
            ActionType.SCHEDULE_MEETING: "Je planifie",
        }

        base = descriptions.get(intent.action, "Je fais ça")

        # Ajouter les entités
        if "client_name" in intent.entities:
            base += f" pour {intent.entities['client_name']}"
        if "amount" in intent.entities:
            base += f" de {intent.entities['amount']} euros"
        if "destination" in intent.entities:
            base += f" vers {intent.entities['destination']}"

        return base

    def status(self) -> Dict[str, Any]:
        """Retourne le statut de l'orchestrateur."""
        return {
            "registry": self._registry.status(),
            "sessions": self._sessions.status()
        }


# ============================================================
# SINGLETON
# ============================================================

_orchestrator: Optional[TheoOrchestrator] = None


def get_theo_orchestrator() -> TheoOrchestrator:
    """Retourne l'instance singleton de l'orchestrateur."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TheoOrchestrator()
    return _orchestrator
