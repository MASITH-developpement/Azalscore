"""
THÉO — Couche Vocale d'Orchestration Universelle
================================================

Théo est une interface vocale intelligente de transcription,
de traduction et d'orchestration. Il ne sait rien, il sait à qui demander.

Architecture:
- core/        : Orchestrateur, registre de capacités, sessions
- voice/       : STT, TTS, wake word detection
- companions/  : Masques vocaux/visuels (Théo, Léa, Alex...)
- adapters/    : Implémentations concrètes (Whisper, ElevenLabs, AZALSCORE...)
- api/         : WebSocket et REST endpoints
- security/    : Niveaux d'autorité, confirmations

Principes:
- Voix > Écran
- Délégation > Duplication
- Orchestration > Monolithe
- Aucune IA figée
"""

from app.theo.core.orchestrator import TheoOrchestrator, get_theo_orchestrator
from app.theo.core.capability_registry import CapabilityRegistry, Capability
from app.theo.core.session_manager import SessionManager, TheoSession
from app.theo.core.intent_detector import IntentDetector, Intent
from app.theo.delegator import TheoDelegator, get_delegator
from app.theo.companions import CompanionRegistry, CompanionTranslator, get_companion_registry, get_translator

__all__ = [
    # Core
    "TheoOrchestrator",
    "get_theo_orchestrator",
    "CapabilityRegistry",
    "Capability",
    "SessionManager",
    "TheoSession",
    "IntentDetector",
    "Intent",
    # Delegator
    "TheoDelegator",
    "get_delegator",
    # Companions
    "CompanionRegistry",
    "CompanionTranslator",
    "get_companion_registry",
    "get_translator",
]

__version__ = "1.0.0"
