"""
AZALSCORE THEO Module

LLM Souverain - Interface humaine unique.
Theo est la SEULE interface exposée aux utilisateurs.

Conformité: AZA-NF-006, AZA-IA
"""
from __future__ import annotations


import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from app.ai.audit import get_audit_logger, AuditEventType
from app.ai.guardian import get_guardian, GuardianDecision
from app.ai.roles import AIRole

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """États de conversation"""
    INITIAL = "initial"
    CLARIFYING = "clarifying"
    PROCESSING = "processing"
    AWAITING_VALIDATION = "awaiting_validation"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class IntentionAnalysis:
    """Analyse d'intention utilisateur"""
    raw_input: str
    understood_intent: str
    confidence: float
    requires_clarification: bool
    clarification_questions: List[str] = field(default_factory=list)
    suggested_actions: List[str] = field(default_factory=list)
    target_modules: List[str] = field(default_factory=list)


@dataclass
class TheoResponse:
    """Réponse de Theo à l'utilisateur"""
    session_id: str
    message: str
    state: ConversationState
    intention: Optional[IntentionAnalysis] = None
    requires_validation: bool = False
    actions_taken: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TheoInterface:
    """
    THEO - LLM Souverain AZALSCORE

    Responsabilités:
    1. Dialoguer avec l'humain
    2. Écouter la demande brute
    3. Poser des questions de clarification
    4. Reformuler l'intention humaine
    5. Faire valider la compréhension
    6. Décider quels rôles IA internes activer
    7. Orchestrer les appels
    8. Consolider les réponses
    9. Restituer une synthèse claire et traçable

    Interdictions:
    - Décider à la place de l'humain
    - Interpréter une norme
    - Représenter légalement l'humain
    - Contourner Guardian
    """

    def __init__(self, orchestrator=None):
        """
        Initialise Theo

        Args:
            orchestrator: AIOrchestrator (injecté pour éviter import circulaire)
        """
        self.audit = get_audit_logger()
        self.guardian = get_guardian()
        self._orchestrator = orchestrator
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def set_orchestrator(self, orchestrator):
        """Définit l'orchestrateur (injection de dépendance)"""
        self._orchestrator = orchestrator

    def start_session(self, user_id: Optional[str] = None) -> str:
        """
        Démarre une nouvelle session de dialogue

        Args:
            user_id: ID de l'utilisateur (optionnel)

        Returns:
            session_id: ID unique de la session
        """
        session_id = str(uuid.uuid4())

        self._sessions[session_id] = {
            "id": session_id,
            "user_id": user_id,
            "started_at": datetime.utcnow().isoformat(),
            "state": ConversationState.INITIAL,
            "history": [],
            "context": {},
            "pending_intention": None
        }

        logger.info("[THEO] New session started: %s", session_id)

        return session_id

    def process_input(
        self,
        session_id: str,
        user_input: str,
        user_id: Optional[str] = None
    ) -> TheoResponse:
        """
        Traite une entrée utilisateur

        Args:
            session_id: ID de la session
            user_input: Texte de l'utilisateur
            user_id: ID de l'utilisateur

        Returns:
            TheoResponse avec la réponse de Theo
        """
        # Vérifier la session
        if session_id not in self._sessions:
            return TheoResponse(
                session_id=session_id,
                message="Session non trouvée. Veuillez démarrer une nouvelle session.",
                state=ConversationState.ERROR
            )

        session = self._sessions[session_id]

        # Journaliser la demande
        self.audit.log_human_request(
            session_id=session_id,
            user_id=user_id or session.get("user_id", "anonymous"),
            request=user_input
        )

        # Validation Guardian
        guardian_check = self.guardian.validate_request(
            session_id=session_id,
            user_id=user_id,
            action="process_input",
            target_module="theo",
            role=AIRole.THEO_DIALOGUE,
            input_data={"input": user_input}
        )

        if guardian_check.decision == GuardianDecision.BLOCKED:
            return TheoResponse(
                session_id=session_id,
                message=f"Requête bloquée par les contrôles de sécurité: {guardian_check.reason}",
                state=ConversationState.ERROR,
                metadata={"guardian_decision": "blocked"}
            )

        # Analyser l'intention
        intention = self._analyze_intention(user_input, session)

        # Ajouter à l'historique
        session["history"].append({
            "type": "user",
            "content": user_input,
            "timestamp": datetime.utcnow().isoformat(),
            "intention": intention
        })

        # Si clarification nécessaire
        if intention.requires_clarification:
            session["state"] = ConversationState.CLARIFYING
            session["pending_intention"] = intention

            response_message = self._format_clarification_request(intention)

            return TheoResponse(
                session_id=session_id,
                message=response_message,
                state=ConversationState.CLARIFYING,
                intention=intention,
                requires_validation=True
            )

        # Sinon, processer la demande
        return self._process_intention(session_id, intention)

    def confirm_intention(
        self,
        session_id: str,
        confirmed: bool,
        additional_info: Optional[str] = None
    ) -> TheoResponse:
        """
        Confirme ou infirme la compréhension de l'intention

        Args:
            session_id: ID de la session
            confirmed: True si l'intention est confirmée
            additional_info: Information additionnelle si non confirmé

        Returns:
            TheoResponse
        """
        if session_id not in self._sessions:
            return TheoResponse(
                session_id=session_id,
                message="Session non trouvée.",
                state=ConversationState.ERROR
            )

        session = self._sessions[session_id]

        if not session.get("pending_intention"):
            return TheoResponse(
                session_id=session_id,
                message="Aucune intention en attente de confirmation.",
                state=session["state"]
            )

        intention = session["pending_intention"]

        if confirmed:
            # Processer l'intention confirmée
            return self._process_intention(session_id, intention)
        else:
            # Demander plus d'informations
            if additional_info:
                # Ré-analyser avec les nouvelles informations
                combined_input = f"{intention.raw_input}. {additional_info}"
                new_intention = self._analyze_intention(combined_input, session)
                session["pending_intention"] = new_intention

                if new_intention.requires_clarification:
                    return TheoResponse(
                        session_id=session_id,
                        message=self._format_clarification_request(new_intention),
                        state=ConversationState.CLARIFYING,
                        intention=new_intention,
                        requires_validation=True
                    )
                else:
                    return self._process_intention(session_id, new_intention)
            else:
                return TheoResponse(
                    session_id=session_id,
                    message="Pourriez-vous préciser votre demande ?",
                    state=ConversationState.CLARIFYING,
                    requires_validation=True
                )

    def _analyze_intention(
        self,
        user_input: str,
        session: Dict[str, Any]
    ) -> IntentionAnalysis:
        """
        Analyse l'intention utilisateur

        Args:
            user_input: Entrée brute
            session: Contexte de session

        Returns:
            IntentionAnalysis
        """
        # Analyse basique - sera enrichie par l'orchestrateur
        input_lower = user_input.lower()

        # Détection des actions communes
        action_keywords = {
            "créer": ["create", "add", "new"],
            "modifier": ["edit", "update", "change"],
            "supprimer": ["delete", "remove"],
            "afficher": ["show", "display", "list"],
            "analyser": ["analyze", "check", "audit"],
            "rechercher": ["search", "find", "query"],
        }

        detected_actions = []
        for action, keywords in action_keywords.items():
            if action in input_lower or any(kw in input_lower for kw in keywords):
                detected_actions.append(action)

        # Détection des modules cibles
        module_keywords = {
            "finance": ["facture", "comptabilité", "paiement", "invoice"],
            "crm": ["client", "contact", "prospect"],
            "rh": ["employé", "congé", "paie", "salaire"],
            "projet": ["projet", "tâche", "planning"],
        }

        detected_modules = []
        for module, keywords in module_keywords.items():
            if any(kw in input_lower for kw in keywords):
                detected_modules.append(module)

        # Évaluer si clarification nécessaire
        requires_clarification = (
            len(detected_actions) == 0 or
            len(detected_modules) == 0 or
            len(user_input) < 10
        )

        clarification_questions = []
        if len(detected_actions) == 0:
            clarification_questions.append(
                "Quelle action souhaitez-vous effectuer ? (créer, modifier, afficher, analyser...)"
            )
        if len(detected_modules) == 0:
            clarification_questions.append(
                "Quel domaine est concerné ? (finance, CRM, RH, projets...)"
            )

        # Calculer la confiance
        confidence = 0.5
        if detected_actions:
            confidence += 0.2
        if detected_modules:
            confidence += 0.2
        if len(user_input) > 50:
            confidence += 0.1

        return IntentionAnalysis(
            raw_input=user_input,
            understood_intent=f"Action: {detected_actions}, Module: {detected_modules}",
            confidence=min(confidence, 1.0),
            requires_clarification=requires_clarification,
            clarification_questions=clarification_questions,
            suggested_actions=detected_actions,
            target_modules=detected_modules
        )

    def _format_human_intent(self, intention: IntentionAnalysis) -> str:
        """Formate l'intention de manière lisible pour un humain"""
        parts = []

        # Modules ciblés
        if intention.target_modules:
            modules_friendly = {
                'crm': 'gestion des clients',
                'invoicing': 'facturation',
                'treasury': 'trésorerie',
                'hr': 'ressources humaines',
                'inventory': 'gestion des stocks',
                'projects': 'gestion de projets',
            }
            module_names = [modules_friendly.get(m, m) for m in intention.target_modules]
            parts.append(f"dans le module **{', '.join(module_names)}**")

        # Actions suggérées
        if intention.suggested_actions:
            actions_friendly = {
                'create': 'créer',
                'update': 'modifier',
                'delete': 'supprimer',
                'view': 'consulter',
                'analyze': 'analyser',
            }
            action_names = [actions_friendly.get(a, a) for a in intention.suggested_actions]
            parts.append(f"action **{', '.join(action_names)}**")

        if parts:
            return "Vous souhaitez " + " ".join(parts) + "."
        return "Je n'ai pas bien compris votre demande."

    def _format_clarification_request(self, intention: IntentionAnalysis) -> str:
        """Formate une demande de clarification"""
        message = "J'ai besoin de quelques précisions pour bien comprendre votre demande.\n\n"

        # Afficher ce qui a été compris de manière lisible
        human_intent = self._format_human_intent(intention)
        if human_intent and human_intent != "Je n'ai pas bien compris votre demande.":
            message += f"✓ **Ce que j'ai compris :** {human_intent}\n\n"

        if intention.clarification_questions:
            message += "**Questions :**\n"
            for i, q in enumerate(intention.clarification_questions, 1):
                message += f"{i}. {q}\n"

        message += "\nMerci de confirmer ou de préciser."

        return message

    def _process_intention(
        self,
        session_id: str,
        intention: IntentionAnalysis
    ) -> TheoResponse:
        """
        Traite une intention confirmée

        Args:
            session_id: ID de la session
            intention: Intention à traiter

        Returns:
            TheoResponse
        """
        session = self._sessions[session_id]
        session["state"] = ConversationState.PROCESSING
        session["pending_intention"] = None

        actions_taken = []

        # Utiliser l'orchestrateur si disponible
        if self._orchestrator and intention.target_modules:
            try:
                # Dispatcher vers les modules appropriés
                for module in intention.target_modules:
                    self.audit.log_theo_dispatch(
                        session_id=session_id,
                        target_module=module,
                        role=AIRole.THEO_ORCHESTRATION.value,
                        input_data={"intention": intention.understood_intent}
                    )
                    actions_taken.append(f"Dispatched to {module}")

                # Construire la réponse
                response_message = self._build_response(intention, actions_taken)

            except Exception as e:
                logger.error("[THEO] Error processing intention: %s", e)
                return TheoResponse(
                    session_id=session_id,
                    message=f"Une erreur s'est produite lors du traitement: {str(e)}",
                    state=ConversationState.ERROR,
                    intention=intention
                )
        else:
            response_message = self._build_response(intention, actions_taken)

        # Mettre à jour l'état
        session["state"] = ConversationState.COMPLETED
        session["history"].append({
            "type": "theo",
            "content": response_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        return TheoResponse(
            session_id=session_id,
            message=response_message,
            state=ConversationState.COMPLETED,
            intention=intention,
            actions_taken=actions_taken,
            metadata={"confidence": intention.confidence}
        )

    def _build_response(
        self,
        intention: IntentionAnalysis,
        actions_taken: List[str]
    ) -> str:
        """Construit la réponse finale"""
        # Format lisible de l'intention
        human_intent = self._format_human_intent(intention)

        if actions_taken:
            message = f"✓ **Compris !** {human_intent}\n\n"
            message += "**Actions effectuées :**\n"
            for action in actions_taken:
                message += f"• {action}\n"
        else:
            message = f"✓ **Compris !** {human_intent}\n\n"
            message += "Je suis prêt à procéder. Souhaitez-vous que je continue ?"

        # Afficher niveau de confiance seulement si bas
        if intention.confidence < 0.7:
            message += f"\n\n_(Niveau de confiance: {intention.confidence * 100:.0f}%)_"

        return message

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Récupère l'historique d'une session"""
        if session_id not in self._sessions:
            return []
        return self._sessions[session_id].get("history", [])

    def end_session(self, session_id: str) -> bool:
        """Termine une session"""
        if session_id in self._sessions:
            self._sessions[session_id]["ended_at"] = datetime.utcnow().isoformat()
            self._sessions[session_id]["state"] = ConversationState.COMPLETED
            logger.info("[THEO] Session ended: %s", session_id)
            return True
        return False


# Instance singleton
_theo_instance: Optional[TheoInterface] = None


def get_theo() -> TheoInterface:
    """Récupère l'instance singleton de Theo"""
    global _theo_instance
    if _theo_instance is None:
        _theo_instance = TheoInterface()
    return _theo_instance
