"""
THÉO — Détecteur d'Intention
============================

Analyse la transcription vocale pour extraire:
- La catégorie d'intention
- L'action demandée
- Les entités (noms, montants, dates...)
- Le niveau de confiance
- Les champs manquants pour clarification
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import re
import logging

from app.theo.core.capability_registry import CapabilityType

logger = logging.getLogger(__name__)


# ============================================================
# CATÉGORIES D'INTENTION
# ============================================================

class IntentCategory(str, Enum):
    """Catégories d'intention de haut niveau."""

    BUSINESS_ACTION = "business_action"    # Actions métier AZALSCORE
    INFORMATION = "information"            # Questions / recherche
    NAVIGATION = "navigation"              # Déplacements
    CONVERSATION = "conversation"          # Discussion générale
    SYSTEM = "system"                      # Commandes système
    CONFIRMATION = "confirmation"          # Oui/Non/Annule
    INTERRUPTION = "interruption"          # Stop/Attends


# ============================================================
# ACTIONS DÉTECTABLES
# ============================================================

class ActionType(str, Enum):
    """Types d'actions spécifiques."""

    # Business Actions
    CREATE_INVOICE = "create_invoice"
    CREATE_QUOTE = "create_quote"
    CREATE_TICKET = "create_ticket"
    CREATE_NOTE = "create_note"
    SEARCH_CLIENT = "search_client"
    CHECK_PAYMENT = "check_payment"
    SCHEDULE_MEETING = "schedule_meeting"

    # Information
    ASK_QUESTION = "ask_question"
    SEARCH_WEB = "search_web"
    GET_WEATHER = "get_weather"
    GET_NEWS = "get_news"

    # Navigation
    GET_DIRECTIONS = "get_directions"
    CHECK_TRAFFIC = "check_traffic"

    # Conversation
    GREET = "greet"
    THANK = "thank"
    SMALL_TALK = "small_talk"

    # System
    HELP = "help"
    SETTINGS = "settings"
    STATUS = "status"

    # Confirmation
    CONFIRM_YES = "confirm_yes"
    CONFIRM_NO = "confirm_no"
    CANCEL = "cancel"
    POSTPONE = "postpone"

    # Interruption
    STOP = "stop"
    WAIT = "wait"


# ============================================================
# INTENT RESULT
# ============================================================

@dataclass
class Intent:
    """Intention détectée avec ses métadonnées."""

    category: IntentCategory
    action: ActionType
    capability_required: CapabilityType
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    requires_confirmation: bool = True
    missing_fields: List[str] = field(default_factory=list)
    original_text: str = ""
    clarification_question: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "action": self.action.value,
            "capability_required": self.capability_required.value,
            "entities": self.entities,
            "confidence": self.confidence,
            "requires_confirmation": self.requires_confirmation,
            "missing_fields": self.missing_fields,
            "original_text": self.original_text,
            "clarification_question": self.clarification_question
        }


# ============================================================
# PATTERNS DE DÉTECTION
# ============================================================

# Patterns pour les actions métier
BUSINESS_PATTERNS = {
    ActionType.CREATE_INVOICE: [
        r"(?:fais?|créer?|faire)\s+(?:une?\s+)?facture",
        r"factur(?:er?|ation)",
        r"nouvelle?\s+facture",
    ],
    ActionType.CREATE_QUOTE: [
        r"(?:fais?|créer?|faire)\s+(?:une?\s+)?devis",
        r"nouveau?\s+devis",
        r"établi[rs]?\s+(?:une?\s+)?devis",
    ],
    ActionType.CREATE_TICKET: [
        r"(?:créer?|ouvrir?|faire)\s+(?:une?\s+)?ticket",
        r"nouveau?\s+ticket",
        r"signaler?\s+(?:un\s+)?problème",
    ],
    ActionType.CREATE_NOTE: [
        r"(?:prends?|noter?|enregistrer?)\s+(?:une?\s+)?note",
        r"(?:note|rappel)(?:r|s)?\s+(?:que|pour)?",
        r"n'oublie\s+pas",
    ],
    ActionType.SEARCH_CLIENT: [
        r"(?:cherch|trouv|recherch)(?:er?|e)\s+(?:le\s+)?client",
        r"(?:info|information)s?\s+(?:sur\s+)?(?:le\s+)?client",
        r"fiche\s+(?:de\s+)?(?:le\s+)?client",
    ],
    ActionType.SCHEDULE_MEETING: [
        r"(?:planifi|programm|prévoi)(?:er?|s)\s+(?:une?\s+)?(?:réunion|rendez-vous|rdv)",
        r"(?:ajoute|mettre)\s+(?:une?\s+)?(?:réunion|rendez-vous|rdv)",
    ],
}

# Patterns pour les confirmations
CONFIRMATION_PATTERNS = {
    ActionType.CONFIRM_YES: [
        r"^(?:oui|ouais|ok|okay|d'accord|vas-y|go|confirme|valide|c'est bon|parfait)$",
        r"^(?:oui\s+)?(?:vas-y|fais-le|lance|exécute)$",
    ],
    ActionType.CONFIRM_NO: [
        r"^(?:non|nan|pas|négatif|refuse|rejette)$",
        r"^(?:non\s+)?(?:merci|pas maintenant|plus tard)$",
    ],
    ActionType.CANCEL: [
        r"^(?:annule|annuler|stop|arrête|laisse tomber|oublie)$",
    ],
    ActionType.POSTPONE: [
        r"(?:plus tard|rappelle-moi|reporte|différer)",
        r"(?:pas maintenant|une autre fois)",
    ],
}

# Patterns pour les interruptions
INTERRUPTION_PATTERNS = {
    ActionType.STOP: [
        r"^(?:stop|arrête|tais-toi|silence|chut)$",
    ],
    ActionType.WAIT: [
        r"^(?:attends?|pause|une seconde|un instant|deux secondes)$",
    ],
}

# Patterns pour la navigation
NAVIGATION_PATTERNS = {
    ActionType.GET_DIRECTIONS: [
        r"(?:emmène|amène|conduis|guide)(?:-moi)?\s+(?:à|au|chez|vers)",
        r"(?:comment|itinéraire|route|chemin)\s+(?:pour\s+)?(?:aller\s+)?(?:à|au|chez|vers)",
        r"(?:je\s+veux|j'aimerais)\s+aller\s+(?:à|au|chez|vers)",
    ],
    ActionType.CHECK_TRAFFIC: [
        r"(?:trafic|circulation|bouchon|embouteillage)s?",
        r"(?:état|condition)s?\s+(?:de\s+)?(?:la\s+)?(?:route|circulation)",
    ],
}

# Patterns pour la météo
WEATHER_PATTERNS = {
    ActionType.GET_WEATHER: [
        r"(?:quel|quelle)\s+(?:temps|météo)",
        r"(?:météo|temps)\s+(?:à|pour|de)",
        r"(?:il\s+)?(?:va\s+)?(?:pleuvoir|faire\s+beau|faire\s+froid|faire\s+chaud)",
        r"(?:prévision|bulletin)\s+météo",
    ],
}

# Patterns pour les salutations
GREETING_PATTERNS = {
    ActionType.GREET: [
        r"^(?:bonjour|salut|coucou|hello|hey|bonsoir)(?:\s+théo)?$",
    ],
    ActionType.THANK: [
        r"^(?:merci|thanks|parfait|super|génial|excellent)(?:\s+théo)?$",
    ],
}


# ============================================================
# EXTRACTION D'ENTITÉS
# ============================================================

def extract_entities(text: str, action: ActionType) -> Tuple[Dict[str, Any], List[str]]:
    """
    Extrait les entités d'un texte selon l'action.

    Returns:
        Tuple (entités trouvées, champs manquants)
    """
    entities = {}
    missing = []
    text_lower = text.lower()

    # Extraction de noms de personnes/entreprises
    # Pattern: "pour/de/à [Monsieur/Madame/Société/Entreprise] [Nom]"
    name_match = re.search(
        r"(?:pour|de|à|chez)\s+"
        r"(?:monsieur|madame|mme?|mr?|société|entreprise|ets|sarl|sas)?\s*"
        r"([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)*)",
        text, re.IGNORECASE
    )
    if name_match:
        entities["client_name"] = name_match.group(1).strip()

    # Extraction de montants
    amount_match = re.search(
        r"(\d+(?:[.,]\d{1,2})?)\s*(?:€|euros?|eur)",
        text_lower
    )
    if amount_match:
        entities["amount"] = float(amount_match.group(1).replace(",", "."))

    # Extraction de lieux (pour navigation)
    if action in [ActionType.GET_DIRECTIONS, ActionType.CHECK_TRAFFIC]:
        place_match = re.search(
            r"(?:à|au|chez|vers|pour)\s+(.+?)(?:\s*$|\s+(?:s'il|stp|svp))",
            text_lower
        )
        if place_match:
            entities["destination"] = place_match.group(1).strip()

    # Déterminer les champs manquants selon l'action
    if action == ActionType.CREATE_INVOICE:
        if "client_name" not in entities:
            missing.append("client_name")
        if "amount" not in entities:
            missing.append("amount")
    elif action == ActionType.CREATE_QUOTE:
        if "client_name" not in entities:
            missing.append("client_name")
    elif action == ActionType.GET_DIRECTIONS:
        if "destination" not in entities:
            missing.append("destination")

    return entities, missing


def get_clarification_question(missing_fields: List[str], action: ActionType) -> Optional[str]:
    """Génère une question de clarification courte."""
    if not missing_fields:
        return None

    field = missing_fields[0]
    questions = {
        "client_name": "Pour qui ?",
        "amount": "Quel montant ?",
        "destination": "Où ça ?",
        "description": "C'est pour quoi ?",
        "date": "Quand ?",
    }

    return questions.get(field, f"Je n'ai pas compris, tu peux préciser ?")


# ============================================================
# DÉTECTEUR D'INTENTION
# ============================================================

class IntentDetector:
    """
    Détecte l'intention d'un utilisateur à partir d'une transcription.

    Utilise des patterns regex pour la détection rapide,
    avec possibilité d'extension vers un modèle ML.
    """

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile tous les patterns regex."""
        self._compiled_patterns: Dict[ActionType, List[re.Pattern]] = {}

        all_patterns = {
            **BUSINESS_PATTERNS,
            **CONFIRMATION_PATTERNS,
            **INTERRUPTION_PATTERNS,
            **NAVIGATION_PATTERNS,
            **WEATHER_PATTERNS,
            **GREETING_PATTERNS,
        }

        for action, patterns in all_patterns.items():
            self._compiled_patterns[action] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def detect(self, text: str, context: Optional[Dict[str, Any]] = None) -> Intent:
        """
        Détecte l'intention principale d'un texte.

        Args:
            text: Transcription vocale
            context: Contexte optionnel (état précédent, etc.)

        Returns:
            Intent détectée
        """
        text = text.strip()
        text_lower = text.lower()
        context = context or {}

        # 1. Vérifier les interruptions (priorité max)
        for action, patterns in self._compiled_patterns.items():
            if action in [ActionType.STOP, ActionType.WAIT]:
                for pattern in patterns:
                    if pattern.search(text_lower):
                        return Intent(
                            category=IntentCategory.INTERRUPTION,
                            action=action,
                            capability_required=CapabilityType.CONVERSATION,
                            confidence=1.0,
                            requires_confirmation=False,
                            original_text=text
                        )

        # 2. Vérifier les confirmations (si contexte d'attente)
        if context.get("awaiting_confirmation"):
            for action in [ActionType.CONFIRM_YES, ActionType.CONFIRM_NO,
                          ActionType.CANCEL, ActionType.POSTPONE]:
                for pattern in self._compiled_patterns.get(action, []):
                    if pattern.search(text_lower):
                        return Intent(
                            category=IntentCategory.CONFIRMATION,
                            action=action,
                            capability_required=CapabilityType.CONVERSATION,
                            confidence=0.95,
                            requires_confirmation=False,
                            original_text=text
                        )

        # 3. Vérifier les salutations
        for action in [ActionType.GREET, ActionType.THANK]:
            for pattern in self._compiled_patterns.get(action, []):
                if pattern.search(text_lower):
                    return Intent(
                        category=IntentCategory.CONVERSATION,
                        action=action,
                        capability_required=CapabilityType.CONVERSATION,
                        confidence=0.9,
                        requires_confirmation=False,
                        original_text=text
                    )

        # 4. Vérifier les actions métier
        best_match: Optional[Tuple[ActionType, float]] = None

        for action, patterns in self._compiled_patterns.items():
            if action in BUSINESS_PATTERNS:
                for pattern in patterns:
                    if pattern.search(text_lower):
                        # Score basé sur la spécificité du match
                        match = pattern.search(text_lower)
                        if match:
                            score = len(match.group()) / len(text_lower)
                            if best_match is None or score > best_match[1]:
                                best_match = (action, min(0.7 + score * 0.3, 0.95))

        if best_match:
            action, confidence = best_match
            entities, missing = extract_entities(text, action)
            clarification = get_clarification_question(missing, action)

            # Mapper action vers capacité
            capability_map = {
                ActionType.CREATE_INVOICE: CapabilityType.FACTURE,
                ActionType.CREATE_QUOTE: CapabilityType.DEVIS,
                ActionType.CREATE_TICKET: CapabilityType.TICKET,
                ActionType.CREATE_NOTE: CapabilityType.NOTE,
                ActionType.SEARCH_CLIENT: CapabilityType.CRM,
                ActionType.SCHEDULE_MEETING: CapabilityType.PLANNING,
            }

            return Intent(
                category=IntentCategory.BUSINESS_ACTION,
                action=action,
                capability_required=capability_map.get(action, CapabilityType.CONVERSATION),
                entities=entities,
                confidence=confidence,
                requires_confirmation=True,
                missing_fields=missing,
                original_text=text,
                clarification_question=clarification
            )

        # 5. Vérifier la navigation
        for action in [ActionType.GET_DIRECTIONS, ActionType.CHECK_TRAFFIC]:
            for pattern in self._compiled_patterns.get(action, []):
                if pattern.search(text_lower):
                    entities, missing = extract_entities(text, action)
                    return Intent(
                        category=IntentCategory.NAVIGATION,
                        action=action,
                        capability_required=CapabilityType.NAVIGATION if action == ActionType.GET_DIRECTIONS else CapabilityType.TRAFIC,
                        entities=entities,
                        confidence=0.85,
                        requires_confirmation=False,
                        missing_fields=missing,
                        original_text=text,
                        clarification_question=get_clarification_question(missing, action)
                    )

        # 6. Vérifier la météo
        for pattern in self._compiled_patterns.get(ActionType.GET_WEATHER, []):
            if pattern.search(text_lower):
                return Intent(
                    category=IntentCategory.INFORMATION,
                    action=ActionType.GET_WEATHER,
                    capability_required=CapabilityType.METEO,
                    confidence=0.9,
                    requires_confirmation=False,
                    original_text=text
                )

        # 7. Fallback: question générale
        return Intent(
            category=IntentCategory.INFORMATION,
            action=ActionType.ASK_QUESTION,
            capability_required=CapabilityType.INFORMATION,
            entities={"query": text},
            confidence=0.5,
            requires_confirmation=False,
            original_text=text
        )


# ============================================================
# SINGLETON
# ============================================================

_detector: Optional[IntentDetector] = None


def get_intent_detector() -> IntentDetector:
    """Retourne l'instance singleton du détecteur."""
    global _detector
    if _detector is None:
        _detector = IntentDetector()
    return _detector
