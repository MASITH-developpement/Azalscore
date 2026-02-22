"""
AZALS MODULE - Marceau Dialogue Manager
========================================

Gestionnaire de dialogue conversationnel.
Gere le contexte, l'historique et le flux de conversation.

Fonctionnalites:
    - Gestion du contexte multi-tour
    - Detection d'intention en temps reel
    - Generation de reponses naturelles
    - Gestion des interruptions
    - Memoire de conversation
    - Slots et entites

Usage:
    from app.modules.marceau.dialogue_manager import DialogueManager

    dm = DialogueManager(tenant_id, db)
    await dm.start_conversation(caller_phone="+33612345678")

    response = await dm.process_utterance("Je voudrais un devis pour une intervention")
    # response.text = "Bien sur, je peux vous aider. Quelle est la nature de l'intervention?"

    response = await dm.process_utterance("C'est pour une fuite d'eau")
    # Continue la conversation avec contexte...
"""

import asyncio
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

from sqlalchemy.orm import Session

from .llm_client import get_llm_client_for_tenant
from .memory import MarceauMemoryService
from .models import ConversationOutcome, MarceauConversation, MemoryType

logger = logging.getLogger(__name__)


# ============================================================================
# TYPES ET CONFIGURATIONS
# ============================================================================

class DialogueState(str, Enum):
    """Etats du dialogue."""
    GREETING = "greeting"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    CONFIRMING = "confirming"
    COLLECTING_INFO = "collecting_info"
    TRANSFERRING = "transferring"
    ENDING = "ending"
    IDLE = "idle"


class IntentType(str, Enum):
    """Types d'intentions detectees."""
    GREETING = "greeting"
    QUOTE_REQUEST = "quote_request"
    APPOINTMENT_REQUEST = "appointment_request"
    SUPPORT_REQUEST = "support_request"
    INFORMATION_REQUEST = "information_request"
    COMPLAINT = "complaint"
    CALLBACK_REQUEST = "callback_request"
    TRANSFER_REQUEST = "transfer_request"
    CONFIRMATION = "confirmation"
    DENIAL = "denial"
    UNCLEAR = "unclear"
    GOODBYE = "goodbye"
    INTERRUPT = "interrupt"
    REPEAT = "repeat"


@dataclass
class Entity:
    """Entite extraite du dialogue."""
    name: str
    value: Any
    confidence: float
    source: str = "user"  # user, system, inferred


@dataclass
class Intent:
    """Intention detectee."""
    type: IntentType
    confidence: float
    entities: list[Entity] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class DialogueTurn:
    """Tour de parole dans le dialogue."""
    speaker: str  # "user" ou "assistant"
    text: str
    timestamp: datetime
    intent: Intent | None = None
    audio_duration: float = 0.0
    emotion: str | None = None


@dataclass
class DialogueContext:
    """Contexte de dialogue complet."""
    conversation_id: str
    tenant_id: str
    state: DialogueState
    turns: list[DialogueTurn]
    entities: dict[str, Entity]
    current_intent: Intent | None
    pending_slots: list[str]
    customer_id: str | None
    customer_name: str | None
    caller_phone: str | None
    started_at: datetime
    last_activity: datetime
    metadata: dict = field(default_factory=dict)


@dataclass
class DialogueResponse:
    """Reponse du gestionnaire de dialogue."""
    text: str
    state: DialogueState
    intent: Intent | None
    entities: dict[str, Any]
    actions: list[dict]
    suggestions: list[str]
    should_end: bool = False
    transfer_to: str | None = None
    confidence: float = 1.0


# ============================================================================
# SLOTS DE CONVERSATION
# ============================================================================

class SlotDefinition:
    """Definition d'un slot a remplir."""

    def __init__(
        self,
        name: str,
        prompt: str,
        required: bool = True,
        validator: Callable | None = None,
        extractor: str | None = None,
        examples: list[str] | None = None
    ):
        self.name = name
        self.prompt = prompt
        self.required = required
        self.validator = validator
        self.extractor = extractor
        self.examples = examples or []


# Slots predéfinis pour les cas d'usage courants
QUOTE_SLOTS = [
    SlotDefinition("service_type", "Quel type de service souhaitez-vous?", required=True),
    SlotDefinition("description", "Pouvez-vous decrire le probleme ou le besoin?", required=True),
    SlotDefinition("urgency", "Est-ce urgent?", required=False),
    SlotDefinition("address", "A quelle adresse se trouve le lieu d'intervention?", required=True),
    SlotDefinition("contact_name", "A quel nom dois-je etablir le devis?", required=True),
    SlotDefinition("contact_phone", "Quel est votre numero de telephone?", required=False),
    SlotDefinition("preferred_date", "Avez-vous une date preferee pour l'intervention?", required=False),
]

APPOINTMENT_SLOTS = [
    SlotDefinition("service_type", "Quel type de rendez-vous souhaitez-vous?", required=True),
    SlotDefinition("preferred_date", "Quelle date vous conviendrait?", required=True),
    SlotDefinition("preferred_time", "A quelle heure preferez-vous?", required=True),
    SlotDefinition("address", "A quelle adresse?", required=True),
    SlotDefinition("contact_name", "Votre nom?", required=True),
]

SUPPORT_SLOTS = [
    SlotDefinition("issue_type", "Quel est le type de probleme?", required=True),
    SlotDefinition("description", "Pouvez-vous decrire le probleme en detail?", required=True),
    SlotDefinition("reference", "Avez-vous un numero de reference ou de commande?", required=False),
]


# ============================================================================
# GESTIONNAIRE DE DIALOGUE
# ============================================================================

class DialogueManager:
    """
    Gestionnaire de dialogue conversationnel.
    Orchestre les conversations avec gestion du contexte et des intentions.
    """

    # Prompts systeme pour differents etats
    SYSTEM_PROMPTS = {
        DialogueState.GREETING: """Tu es Marceau, l'assistant vocal d'une entreprise de services.
Tu accueilles l'appelant chaleureusement et lui demandes comment tu peux l'aider.
Sois professionnel mais amical.""",

        DialogueState.COLLECTING_INFO: """Tu collectes des informations pour {intent}.
Continue a poser des questions naturellement pour obtenir: {pending_slots}.
Reformule si necessaire et confirme les informations recues.""",

        DialogueState.CONFIRMING: """Tu recapitules les informations collectees et demandes confirmation.
Entites collectees: {entities}
Demande si tout est correct avant de proceder.""",

        "default": """Tu es Marceau, assistant vocal intelligent.
Tu aides les clients avec leurs demandes de maniere naturelle et efficace.
Tu peux gerer: devis, rendez-vous, support technique, informations generales.
Sois concis mais complet dans tes reponses.""",
    }

    # Expressions pour detection d'intention
    INTENT_PATTERNS = {
        IntentType.GREETING: r"\b(bonjour|salut|hello|bonsoir|hey)\b",
        IntentType.GOODBYE: r"\b(au revoir|bye|bonne journ[ée]e|a bient[oô]t|merci.*c'est tout)\b",
        IntentType.QUOTE_REQUEST: r"\b(devis|estimation|prix|co[uû]t|tarif|combien)\b",
        IntentType.APPOINTMENT_REQUEST: r"\b(rendez-vous|rdv|disponibilit[ée]|cr[ée]neau|planifier|prendre)\b",
        IntentType.SUPPORT_REQUEST: r"\b(probl[eè]me|panne|bug|aide|support|assistance|d[ée]faut)\b",
        IntentType.COMPLAINT: r"\b(plainte|m[ée]content|insatisfait|r[ée]clamation|inacceptable)\b",
        IntentType.CONFIRMATION: r"\b(oui|d'accord|ok|parfait|correct|exact|c'est [çc]a)\b",
        IntentType.DENIAL: r"\b(non|pas vraiment|incorrect|faux|erreur)\b",
        IntentType.REPEAT: r"\b(r[ée]p[eè]te|pardon|comment|quoi|j'ai pas compris)\b",
        IntentType.TRANSFER_REQUEST: r"\b(humain|personne|agent|conseiller|transf[ée]r)\b",
    }

    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db
        self.memory = MarceauMemoryService(tenant_id, db)
        self._contexts: dict[str, DialogueContext] = {}

    # ========================================================================
    # GESTION DE CONVERSATION
    # ========================================================================

    async def start_conversation(
        self,
        caller_phone: str,
        customer_id: str | None = None,
        customer_name: str | None = None,
        metadata: dict | None = None
    ) -> DialogueResponse:
        """
        Demarre une nouvelle conversation.

        Args:
            caller_phone: Numero de telephone de l'appelant
            customer_id: ID client si connu
            customer_name: Nom du client si connu

        Returns:
            Reponse de bienvenue
        """
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow()

        # Creer le contexte
        context = DialogueContext(
            conversation_id=conversation_id,
            tenant_id=self.tenant_id,
            state=DialogueState.GREETING,
            turns=[],
            entities={},
            current_intent=None,
            pending_slots=[],
            customer_id=customer_id,
            customer_name=customer_name,
            caller_phone=caller_phone,
            started_at=now,
            last_activity=now,
            metadata=metadata or {},
        )

        self._contexts[conversation_id] = context

        # Creer l'enregistrement en DB
        db_conversation = MarceauConversation(
            id=uuid.UUID(conversation_id),
            tenant_id=self.tenant_id,
            caller_phone=caller_phone,
            customer_id=uuid.UUID(customer_id) if customer_id else None,
            caller_name=customer_name,
            started_at=now,
        )
        self.db.add(db_conversation)
        self.db.commit()

        # Generer le message de bienvenue
        greeting = await self._generate_greeting(context)

        # Ajouter au transcript
        self._add_turn(context, "assistant", greeting)

        return DialogueResponse(
            text=greeting,
            state=DialogueState.LISTENING,
            intent=None,
            entities={},
            actions=[],
            suggestions=["Demander un devis", "Prendre rendez-vous", "Support technique"],
        )

    async def process_utterance(
        self,
        conversation_id: str,
        text: str,
        audio_duration: float = 0.0
    ) -> DialogueResponse:
        """
        Traite une utterance utilisateur.

        Args:
            conversation_id: ID de la conversation
            text: Texte transcrit
            audio_duration: Duree audio originale

        Returns:
            Reponse du dialogue
        """
        context = self._contexts.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} non trouvee")

        context.last_activity = datetime.utcnow()

        # Detecter l'intention
        intent = await self._detect_intent(text, context)

        # Ajouter le tour utilisateur
        self._add_turn(context, "user", text, intent, audio_duration)

        # Extraire les entites
        entities = await self._extract_entities(text, intent, context)
        for name, entity in entities.items():
            context.entities[name] = entity

        context.current_intent = intent

        # Traiter selon l'etat et l'intention
        response = await self._process_state(context, intent, text)

        # Ajouter la reponse au transcript
        self._add_turn(context, "assistant", response.text)

        return response

    async def end_conversation(
        self,
        conversation_id: str,
        outcome: ConversationOutcome = ConversationOutcome.INFORMATION_PROVIDED,
        summary: str | None = None
    ) -> dict:
        """
        Termine une conversation.

        Args:
            conversation_id: ID de la conversation
            outcome: Resultat de la conversation
            summary: Resume optionnel

        Returns:
            Recap de la conversation
        """
        context = self._contexts.get(conversation_id)
        if not context:
            raise ValueError(f"Conversation {conversation_id} non trouvee")

        # Generer le resume si pas fourni
        if not summary:
            summary = await self._generate_summary(context)

        # Mettre a jour en DB
        db_conversation = self.db.query(MarceauConversation).filter(
            MarceauConversation.id == uuid.UUID(conversation_id),
            MarceauConversation.tenant_id == self.tenant_id
        ).first()

        if db_conversation:
            db_conversation.ended_at = datetime.utcnow()
            db_conversation.duration_seconds = int(
                (datetime.utcnow() - context.started_at).total_seconds()
            )
            db_conversation.transcript = self._format_transcript(context)
            db_conversation.summary = summary
            db_conversation.outcome = outcome
            db_conversation.intent = context.current_intent.type.value if context.current_intent else None
            self.db.commit()

        # Stocker en memoire pour apprentissage
        await self.memory.store_memory(
            content=f"Conversation {outcome.value}: {summary}",
            memory_type=MemoryType.DECISION,
            tags=["conversation", outcome.value],
            importance_score=0.7,
        )

        # Nettoyer le contexte
        del self._contexts[conversation_id]

        return {
            "conversation_id": conversation_id,
            "duration_seconds": int((datetime.utcnow() - context.started_at).total_seconds()),
            "turns_count": len(context.turns),
            "outcome": outcome.value,
            "summary": summary,
            "entities": {k: v.value for k, v in context.entities.items()},
        }

    def get_context(self, conversation_id: str) -> DialogueContext | None:
        """Recupere le contexte d'une conversation."""
        return self._contexts.get(conversation_id)

    # ========================================================================
    # DETECTION D'INTENTION
    # ========================================================================

    async def _detect_intent(self, text: str, context: DialogueContext) -> Intent:
        """Detecte l'intention d'une utterance."""
        text_lower = text.lower()

        # Detection par patterns regex (rapide)
        for intent_type, pattern in self.INTENT_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                return Intent(
                    type=intent_type,
                    confidence=0.8,
                    raw_text=text
                )

        # Detection LLM pour cas complexes
        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            # Construire l'historique recent
            recent_turns = context.turns[-6:] if context.turns else []
            history = "\n".join([
                f"{t.speaker.upper()}: {t.text}" for t in recent_turns
            ])

            prompt = f"""Analyse cette utterance dans le contexte d'une conversation telephonique d'entreprise.

HISTORIQUE:
{history}

NOUVELLE UTTERANCE: {text}

Determine l'intention parmi:
- greeting: Salutation
- quote_request: Demande de devis ou estimation
- appointment_request: Demande de rendez-vous
- support_request: Demande d'aide technique
- information_request: Demande d'information generale
- complaint: Reclamation ou plainte
- callback_request: Demande de rappel
- transfer_request: Veut parler a un humain
- confirmation: Confirme quelque chose (oui, d'accord)
- denial: Refuse ou corrige (non, pas vraiment)
- unclear: Intention pas claire

Reponds en JSON:
{{"intent": "type_intention", "confidence": 0.85, "reasoning": "explication"}}"""

            response = await llm.generate(
                prompt,
                temperature=0.1,
                max_tokens=150,
                system_prompt="Tu analyses les intentions dans un dialogue telephonique.",
            )

            # Parser la reponse
            from .llm_client import extract_json_from_response
            result = await extract_json_from_response(response)

            if result:
                try:
                    intent_type = IntentType(result.get("intent", "unclear"))
                except ValueError:
                    intent_type = IntentType.UNCLEAR

                return Intent(
                    type=intent_type,
                    confidence=float(result.get("confidence", 0.5)),
                    raw_text=text
                )

        except Exception as e:
            logger.warning(f"[Dialogue] Erreur detection intention LLM: {e}")

        return Intent(
            type=IntentType.UNCLEAR,
            confidence=0.3,
            raw_text=text
        )

    # ========================================================================
    # EXTRACTION D'ENTITES
    # ========================================================================

    async def _extract_entities(
        self,
        text: str,
        intent: Intent,
        context: DialogueContext
    ) -> dict[str, Entity]:
        """Extrait les entites d'une utterance."""
        entities = {}

        # Extraction par regex pour entites communes
        # Telephone
        phone_match = re.search(r"(?:\+33|0)[1-9](?:[0-9]{8}|[0-9\s.-]{8,})", text)
        if phone_match:
            entities["phone"] = Entity(
                name="phone",
                value=phone_match.group().replace(" ", "").replace(".", "").replace("-", ""),
                confidence=0.95,
            )

        # Email
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if email_match:
            entities["email"] = Entity(
                name="email",
                value=email_match.group(),
                confidence=0.95,
            )

        # Date (formats courants)
        date_patterns = [
            r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})",  # 15/01/2024
            r"(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)",
            r"(demain|apr[eè]s-demain|la semaine prochaine)",
            r"(ce soir|cet apr[eè]s-midi|ce matin)",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities["date_mention"] = Entity(
                    name="date_mention",
                    value=match.group(),
                    confidence=0.8,
                )
                break

        # Heure
        time_match = re.search(r"(\d{1,2})[hH:](\d{2})?", text)
        if time_match:
            entities["time"] = Entity(
                name="time",
                value=time_match.group(),
                confidence=0.9,
            )

        # Adresse (detection basique)
        address_match = re.search(
            r"(\d+)[\s,]+(rue|avenue|boulevard|place|chemin|impasse|all[ée]e)[^,]+",
            text,
            re.IGNORECASE
        )
        if address_match:
            entities["address"] = Entity(
                name="address",
                value=address_match.group(),
                confidence=0.7,
            )

        # Extraction LLM pour entites complexes
        if intent.type in [IntentType.QUOTE_REQUEST, IntentType.APPOINTMENT_REQUEST]:
            llm_entities = await self._extract_entities_llm(text, intent, context)
            entities.update(llm_entities)

        return entities

    async def _extract_entities_llm(
        self,
        text: str,
        intent: Intent,
        context: DialogueContext
    ) -> dict[str, Entity]:
        """Extraction d'entites via LLM."""
        entities = {}

        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            slots = []
            if intent.type == IntentType.QUOTE_REQUEST:
                slots = ["service_type", "description", "urgency", "address"]
            elif intent.type == IntentType.APPOINTMENT_REQUEST:
                slots = ["service_type", "preferred_date", "preferred_time", "address"]
            elif intent.type == IntentType.SUPPORT_REQUEST:
                slots = ["issue_type", "description", "reference"]

            prompt = f"""Extrait les informations suivantes de ce texte si presentes:
{json.dumps(slots)}

Texte: "{text}"

Reponds en JSON avec uniquement les champs trouves:
{{"slot_name": "valeur", ...}}
Si un slot n'est pas mentionne, ne l'inclus pas."""

            response = await llm.generate(
                prompt,
                temperature=0.1,
                max_tokens=200,
                system_prompt="Tu extrais des informations structurees d'un texte.",
            )

            from .llm_client import extract_json_from_response
            result = await extract_json_from_response(response)

            if result:
                for slot, value in result.items():
                    if value and slot in slots:
                        entities[slot] = Entity(
                            name=slot,
                            value=value,
                            confidence=0.75,
                            source="llm",
                        )

        except Exception as e:
            logger.warning(f"[Dialogue] Erreur extraction LLM: {e}")

        return entities

    # ========================================================================
    # TRAITEMENT DES ETATS
    # ========================================================================

    async def _process_state(
        self,
        context: DialogueContext,
        intent: Intent,
        text: str
    ) -> DialogueResponse:
        """Traite l'utterance selon l'etat actuel."""

        # Gestion des intentions transversales
        if intent.type == IntentType.GOODBYE:
            return await self._handle_goodbye(context)

        if intent.type == IntentType.TRANSFER_REQUEST:
            return await self._handle_transfer_request(context)

        if intent.type == IntentType.REPEAT:
            return await self._handle_repeat_request(context)

        # Traitement selon l'etat
        state_handlers = {
            DialogueState.GREETING: self._handle_greeting_state,
            DialogueState.LISTENING: self._handle_listening_state,
            DialogueState.COLLECTING_INFO: self._handle_collecting_state,
            DialogueState.CONFIRMING: self._handle_confirming_state,
        }

        handler = state_handlers.get(context.state, self._handle_default_state)
        return await handler(context, intent, text)

    async def _handle_greeting_state(
        self,
        context: DialogueContext,
        intent: Intent,
        text: str
    ) -> DialogueResponse:
        """Traite les reponses apres le greeting."""
        context.state = DialogueState.LISTENING
        return await self._handle_listening_state(context, intent, text)

    async def _handle_listening_state(
        self,
        context: DialogueContext,
        intent: Intent,
        text: str
    ) -> DialogueResponse:
        """Traite une nouvelle demande."""

        if intent.type == IntentType.QUOTE_REQUEST:
            return await self._start_quote_flow(context, intent)

        elif intent.type == IntentType.APPOINTMENT_REQUEST:
            return await self._start_appointment_flow(context, intent)

        elif intent.type == IntentType.SUPPORT_REQUEST:
            return await self._start_support_flow(context, intent)

        elif intent.type == IntentType.INFORMATION_REQUEST:
            return await self._handle_info_request(context, text)

        elif intent.type == IntentType.COMPLAINT:
            return await self._handle_complaint(context, text)

        elif intent.type == IntentType.GREETING:
            response_text = "Bonjour! Comment puis-je vous aider aujourd'hui?"
            return DialogueResponse(
                text=response_text,
                state=DialogueState.LISTENING,
                intent=intent,
                entities={},
                actions=[],
                suggestions=["Devis", "Rendez-vous", "Support"],
            )

        else:
            # Reponse LLM pour cas non geres
            return await self._generate_llm_response(context, text)

    async def _handle_collecting_state(
        self,
        context: DialogueContext,
        intent: Intent,
        text: str
    ) -> DialogueResponse:
        """Collecte les informations manquantes."""

        # Verifier les slots remplis
        filled = [s for s in context.pending_slots if s in context.entities]
        remaining = [s for s in context.pending_slots if s not in context.entities]

        if not remaining:
            # Tous les slots sont remplis, passer a la confirmation
            context.state = DialogueState.CONFIRMING
            return await self._generate_confirmation(context)

        # Demander le prochain slot
        next_slot = remaining[0]
        slot_prompts = {
            "service_type": "Quel type de service souhaitez-vous?",
            "description": "Pouvez-vous me decrire votre besoin?",
            "address": "A quelle adresse se situe l'intervention?",
            "contact_name": "A quel nom dois-je enregistrer la demande?",
            "preferred_date": "Quelle date vous conviendrait?",
            "preferred_time": "A quelle heure preferez-vous?",
            "urgency": "Est-ce urgent?",
        }

        prompt = slot_prompts.get(next_slot, f"Pouvez-vous preciser {next_slot}?")

        return DialogueResponse(
            text=prompt,
            state=DialogueState.COLLECTING_INFO,
            intent=intent,
            entities={k: v.value for k, v in context.entities.items()},
            actions=[],
            suggestions=[],
        )

    async def _handle_confirming_state(
        self,
        context: DialogueContext,
        intent: Intent,
        text: str
    ) -> DialogueResponse:
        """Gere la confirmation."""

        if intent.type == IntentType.CONFIRMATION:
            # Executer l'action
            return await self._execute_action(context)

        elif intent.type == IntentType.DENIAL:
            # Demander ce qui est incorrect
            context.state = DialogueState.COLLECTING_INFO
            return DialogueResponse(
                text="D'accord, qu'est-ce qui n'est pas correct? Je peux modifier les informations.",
                state=DialogueState.COLLECTING_INFO,
                intent=intent,
                entities={k: v.value for k, v in context.entities.items()},
                actions=[],
                suggestions=["Modifier l'adresse", "Modifier la date", "Tout reprendre"],
            )

        else:
            # Redemander confirmation
            return await self._generate_confirmation(context)

    async def _handle_default_state(
        self,
        context: DialogueContext,
        intent: Intent,
        text: str
    ) -> DialogueResponse:
        """Gestion par defaut."""
        return await self._generate_llm_response(context, text)

    # ========================================================================
    # FLOWS SPECIFIQUES
    # ========================================================================

    async def _start_quote_flow(
        self,
        context: DialogueContext,
        intent: Intent
    ) -> DialogueResponse:
        """Demarre le flow de demande de devis."""
        context.state = DialogueState.COLLECTING_INFO
        context.pending_slots = ["service_type", "description", "address", "contact_name"]

        # Verifier ce qui est deja collecte
        remaining = [s for s in context.pending_slots if s not in context.entities]

        if not remaining:
            context.state = DialogueState.CONFIRMING
            return await self._generate_confirmation(context)

        return DialogueResponse(
            text="Bien sur, je peux vous etablir un devis. Quel type de service vous interesse?",
            state=DialogueState.COLLECTING_INFO,
            intent=intent,
            entities={},
            actions=[],
            suggestions=["Plomberie", "Electricite", "Chauffage", "Autre"],
        )

    async def _start_appointment_flow(
        self,
        context: DialogueContext,
        intent: Intent
    ) -> DialogueResponse:
        """Demarre le flow de prise de rendez-vous."""
        context.state = DialogueState.COLLECTING_INFO
        context.pending_slots = ["service_type", "preferred_date", "preferred_time", "address"]

        return DialogueResponse(
            text="Je vais vous aider a prendre rendez-vous. Pour quel type d'intervention?",
            state=DialogueState.COLLECTING_INFO,
            intent=intent,
            entities={},
            actions=[],
            suggestions=["Diagnostic", "Reparation", "Installation", "Entretien"],
        )

    async def _start_support_flow(
        self,
        context: DialogueContext,
        intent: Intent
    ) -> DialogueResponse:
        """Demarre le flow support."""
        context.state = DialogueState.COLLECTING_INFO
        context.pending_slots = ["issue_type", "description"]

        return DialogueResponse(
            text="Je suis desole que vous rencontriez un probleme. Pouvez-vous me decrire la situation?",
            state=DialogueState.COLLECTING_INFO,
            intent=intent,
            entities={},
            actions=[],
            suggestions=[],
        )

    async def _handle_info_request(
        self,
        context: DialogueContext,
        text: str
    ) -> DialogueResponse:
        """Traite une demande d'information."""
        # Utiliser RAG pour trouver l'information
        relevant_context = await self.memory.retrieve_relevant_context(
            query=text,
            limit=3,
            memory_types=[MemoryType.KNOWLEDGE]
        )

        # Generer reponse avec contexte
        return await self._generate_llm_response(context, text, extra_context=relevant_context)

    async def _handle_complaint(
        self,
        context: DialogueContext,
        text: str
    ) -> DialogueResponse:
        """Traite une reclamation."""
        context.metadata["has_complaint"] = True

        return DialogueResponse(
            text="Je suis vraiment desole de cette situation. Je prends note de votre reclamation. "
                 "Pouvez-vous me donner plus de details pour que je puisse vous aider au mieux?",
            state=DialogueState.COLLECTING_INFO,
            intent=Intent(type=IntentType.COMPLAINT, confidence=0.9, raw_text=text),
            entities={},
            actions=[{"type": "flag_complaint"}],
            suggestions=["Parler a un responsable"],
        )

    # ========================================================================
    # GESTION DES CAS SPECIAUX
    # ========================================================================

    async def _handle_goodbye(self, context: DialogueContext) -> DialogueResponse:
        """Gere la fin de conversation."""
        context.state = DialogueState.ENDING

        goodbye_text = "Au revoir et merci de votre appel! N'hesitez pas a nous recontacter. Bonne journee!"

        return DialogueResponse(
            text=goodbye_text,
            state=DialogueState.ENDING,
            intent=Intent(type=IntentType.GOODBYE, confidence=1.0),
            entities={},
            actions=[],
            suggestions=[],
            should_end=True,
        )

    async def _handle_transfer_request(self, context: DialogueContext) -> DialogueResponse:
        """Gere une demande de transfert."""
        context.state = DialogueState.TRANSFERRING

        return DialogueResponse(
            text="Je comprends, vous souhaitez parler a un conseiller. "
                 "Je vous transfere immediatement. Veuillez patienter quelques instants.",
            state=DialogueState.TRANSFERRING,
            intent=Intent(type=IntentType.TRANSFER_REQUEST, confidence=1.0),
            entities={},
            actions=[{"type": "transfer", "department": "default"}],
            suggestions=[],
            transfer_to="agent",
        )

    async def _handle_repeat_request(self, context: DialogueContext) -> DialogueResponse:
        """Repete la derniere reponse."""
        # Trouver la derniere reponse assistant
        for turn in reversed(context.turns):
            if turn.speaker == "assistant":
                return DialogueResponse(
                    text=f"Bien sur, je repete: {turn.text}",
                    state=context.state,
                    intent=Intent(type=IntentType.REPEAT, confidence=1.0),
                    entities={},
                    actions=[],
                    suggestions=[],
                )

        return DialogueResponse(
            text="Je suis la pour vous aider. Que puis-je faire pour vous?",
            state=DialogueState.LISTENING,
            intent=None,
            entities={},
            actions=[],
            suggestions=[],
        )

    # ========================================================================
    # GENERATION DE REPONSES
    # ========================================================================

    async def _generate_greeting(self, context: DialogueContext) -> str:
        """Genere un message de bienvenue personnalise."""
        if context.customer_name:
            return f"Bonjour {context.customer_name}! Je suis Marceau, votre assistant. Comment puis-je vous aider aujourd'hui?"
        else:
            return "Bonjour et bienvenue! Je suis Marceau, votre assistant virtuel. Comment puis-je vous aider?"

    async def _generate_confirmation(self, context: DialogueContext) -> DialogueResponse:
        """Genere un message de confirmation."""
        entities_text = []
        for name, entity in context.entities.items():
            label = {
                "service_type": "Service",
                "description": "Description",
                "address": "Adresse",
                "contact_name": "Nom",
                "preferred_date": "Date",
                "preferred_time": "Heure",
            }.get(name, name)
            entities_text.append(f"- {label}: {entity.value}")

        recap = "\n".join(entities_text)

        intent_label = {
            IntentType.QUOTE_REQUEST: "votre demande de devis",
            IntentType.APPOINTMENT_REQUEST: "votre rendez-vous",
            IntentType.SUPPORT_REQUEST: "votre demande de support",
        }.get(context.current_intent.type if context.current_intent else None, "votre demande")

        return DialogueResponse(
            text=f"Parfait, je recapitule {intent_label}:\n{recap}\n\nEst-ce correct?",
            state=DialogueState.CONFIRMING,
            intent=context.current_intent,
            entities={k: v.value for k, v in context.entities.items()},
            actions=[],
            suggestions=["Oui, c'est correct", "Non, je veux modifier"],
        )

    async def _generate_llm_response(
        self,
        context: DialogueContext,
        text: str,
        extra_context: list[str] | None = None
    ) -> DialogueResponse:
        """Genere une reponse via LLM."""
        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            # Construire l'historique
            history = "\n".join([
                f"{t.speaker.upper()}: {t.text}" for t in context.turns[-6:]
            ])

            # Contexte supplementaire
            ctx_text = ""
            if extra_context:
                ctx_text = "\n\nINFORMATIONS UTILES:\n" + "\n".join(extra_context)

            prompt = f"""Continue cette conversation telephonique professionnelle.

HISTORIQUE:
{history}

UTILISATEUR: {text}
{ctx_text}

Reponds de maniere naturelle, concise et utile. Maximum 2-3 phrases.
Si tu ne peux pas aider, propose de transferer a un conseiller.

ASSISTANT:"""

            response = await llm.generate(
                prompt,
                temperature=0.7,
                max_tokens=200,
                system_prompt=self.SYSTEM_PROMPTS["default"],
            )

            return DialogueResponse(
                text=response.strip(),
                state=context.state,
                intent=context.current_intent,
                entities={k: v.value for k, v in context.entities.items()},
                actions=[],
                suggestions=[],
            )

        except Exception as e:
            logger.error(f"[Dialogue] Erreur generation LLM: {e}")
            return DialogueResponse(
                text="Je suis desole, je n'ai pas bien compris. Pouvez-vous reformuler?",
                state=context.state,
                intent=None,
                entities={},
                actions=[],
                suggestions=["Parler a un conseiller"],
            )

    async def _execute_action(self, context: DialogueContext) -> DialogueResponse:
        """Execute l'action apres confirmation."""
        intent = context.current_intent

        if not intent:
            return DialogueResponse(
                text="Je vais transmettre votre demande a notre equipe. Vous serez contacte rapidement.",
                state=DialogueState.ENDING,
                intent=None,
                entities={k: v.value for k, v in context.entities.items()},
                actions=[{"type": "create_task"}],
                suggestions=[],
                should_end=True,
            )

        actions = []

        if intent.type == IntentType.QUOTE_REQUEST:
            actions.append({
                "type": "create_quote",
                "module": "commercial",
                "data": {k: v.value for k, v in context.entities.items()}
            })
            response_text = "C'est note! Je cree votre demande de devis. Vous recevrez une proposition par email dans les plus brefs delais. Puis-je vous aider pour autre chose?"

        elif intent.type == IntentType.APPOINTMENT_REQUEST:
            actions.append({
                "type": "schedule_appointment",
                "module": "telephonie",
                "data": {k: v.value for k, v in context.entities.items()}
            })
            response_text = "Parfait! Votre rendez-vous est enregistre. Vous recevrez une confirmation par SMS. Y a-t-il autre chose?"

        elif intent.type == IntentType.SUPPORT_REQUEST:
            actions.append({
                "type": "create_ticket",
                "module": "support",
                "data": {k: v.value for k, v in context.entities.items()}
            })
            response_text = "J'ai enregistre votre demande de support. Un technicien vous recontactera rapidement. Autre chose?"

        else:
            response_text = "C'est enregistre! Notre equipe va traiter votre demande. Puis-je vous aider autrement?"

        context.state = DialogueState.LISTENING

        return DialogueResponse(
            text=response_text,
            state=DialogueState.LISTENING,
            intent=intent,
            entities={k: v.value for k, v in context.entities.items()},
            actions=actions,
            suggestions=["Non merci, c'est tout", "Autre question"],
        )

    async def _generate_summary(self, context: DialogueContext) -> str:
        """Genere un resume de la conversation."""
        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            transcript = self._format_transcript(context)

            prompt = f"""Resume cette conversation telephonique en 2-3 phrases.
Inclus: le motif de l'appel, les informations cles, et le resultat.

CONVERSATION:
{transcript[:2000]}

RESUME:"""

            response = await llm.generate(
                prompt,
                temperature=0.2,
                max_tokens=150,
            )

            return response.strip()

        except Exception as e:
            logger.warning(f"[Dialogue] Erreur generation resume: {e}")
            return f"Conversation de {len(context.turns)} echanges."

    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    def _add_turn(
        self,
        context: DialogueContext,
        speaker: str,
        text: str,
        intent: Intent | None = None,
        audio_duration: float = 0.0
    ):
        """Ajoute un tour de parole."""
        turn = DialogueTurn(
            speaker=speaker,
            text=text,
            timestamp=datetime.utcnow(),
            intent=intent,
            audio_duration=audio_duration,
        )
        context.turns.append(turn)

    def _format_transcript(self, context: DialogueContext) -> str:
        """Formate le transcript pour stockage."""
        lines = []
        for turn in context.turns:
            timestamp = turn.timestamp.strftime("%H:%M:%S")
            speaker = "MARCEAU" if turn.speaker == "assistant" else "CLIENT"
            lines.append(f"[{timestamp}] {speaker}: {turn.text}")
        return "\n".join(lines)
