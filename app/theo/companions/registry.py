"""
THÉO — Registre des Compagnons
==============================

Gère les compagnons (masques vocaux/visuels) disponibles.
Chaque compagnon a une identité mais aucune logique propre.
"""
from __future__ import annotations


from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import os
import logging

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION COMPAGNON
# ============================================================

class CompanionGender(str, Enum):
    """Genre du compagnon (pour la voix)."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VisualStyle(str, Enum):
    """Style visuel du compagnon."""
    SEMI_REALISTIC = "semi_realistic"
    CARTOON = "cartoon"
    ABSTRACT = "abstract"
    MINIMAL = "minimal"


@dataclass
class VoiceSettings:
    """Configuration vocale d'un compagnon."""
    provider: str = "elevenlabs"
    voice_id: str = ""
    stability: float = 0.75
    similarity_boost: float = 0.8
    speed: float = 1.0
    pitch: float = 1.0


@dataclass
class VisualSettings:
    """Configuration visuelle d'un compagnon."""
    enabled: bool = True
    avatar_url: str = ""
    style: VisualStyle = VisualStyle.SEMI_REALISTIC
    animations: List[str] = field(default_factory=lambda: ["blink", "breathe", "lip_sync"])
    background_color: str = "#6366f1"


@dataclass
class Companion:
    """Définition d'un compagnon Théo."""

    id: str
    display_name: str
    wake_aliases: List[str]
    gender: CompanionGender
    description: str
    voice: VoiceSettings
    visual: VisualSettings
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches_wake_word(self, text: str) -> bool:
        """Vérifie si le texte contient un alias de ce compagnon."""
        text_lower = text.lower()
        for alias in self.wake_aliases:
            if alias.lower() in text_lower:
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "wake_aliases": self.wake_aliases,
            "gender": self.gender.value,
            "description": self.description,
            "voice": {
                "provider": self.voice.provider,
                "voice_id": self.voice.voice_id,
                "stability": self.voice.stability,
                "similarity_boost": self.voice.similarity_boost,
                "speed": self.voice.speed,
                "pitch": self.voice.pitch
            },
            "visual": {
                "enabled": self.visual.enabled,
                "avatar_url": self.visual.avatar_url,
                "style": self.visual.style.value,
                "animations": self.visual.animations,
                "background_color": self.visual.background_color
            },
            "metadata": self.metadata
        }


# ============================================================
# COMPAGNONS PAR DÉFAUT
# ============================================================

DEFAULT_COMPANIONS = [
    Companion(
        id="theo",
        display_name="Théo",
        wake_aliases=["Théo", "Theo"],
        gender=CompanionGender.MALE,
        description="Assistant principal AZALSCORE. Homme ~45 ans, cheveux gris, lunettes rondes.",
        voice=VoiceSettings(
            provider="elevenlabs",
            voice_id="theo-fr-v1",
            stability=0.75,
            similarity_boost=0.8,
            speed=0.95
        ),
        visual=VisualSettings(
            enabled=True,
            avatar_url="/assets/theo/avatar.png",
            style=VisualStyle.SEMI_REALISTIC,
            animations=["blink", "breathe", "lip_sync", "nod"],
            background_color="#6366f1"
        ),
        metadata={
            "is_default": True,
            "age": 45,
            "hair": "grey",
            "glasses": "round"
        }
    ),
    Companion(
        id="lea",
        display_name="Léa",
        wake_aliases=["Léa", "Lea"],
        gender=CompanionGender.FEMALE,
        description="Assistante dynamique. Femme ~35 ans, brune, moderne.",
        voice=VoiceSettings(
            provider="elevenlabs",
            voice_id="lea-fr-v1",
            stability=0.7,
            similarity_boost=0.85,
            speed=1.0
        ),
        visual=VisualSettings(
            enabled=True,
            avatar_url="/assets/companions/lea.png",
            style=VisualStyle.SEMI_REALISTIC,
            animations=["blink", "breathe", "lip_sync", "smile"],
            background_color="#ec4899"
        ),
        metadata={
            "is_default": False,
            "age": 35,
            "hair": "brown"
        }
    ),
    Companion(
        id="alex",
        display_name="Alex",
        wake_aliases=["Alex"],
        gender=CompanionGender.NEUTRAL,
        description="Assistant neutre et professionnel. Représentation abstraite.",
        voice=VoiceSettings(
            provider="elevenlabs",
            voice_id="alex-neutral-v1",
            stability=0.8,
            similarity_boost=0.7,
            speed=1.0
        ),
        visual=VisualSettings(
            enabled=True,
            avatar_url="/assets/companions/alex.png",
            style=VisualStyle.ABSTRACT,
            animations=["pulse", "morph"],
            background_color="#10b981"
        ),
        metadata={
            "is_default": False,
            "style": "abstract"
        }
    ),
]


# ============================================================
# REGISTRE DES COMPAGNONS
# ============================================================

class CompanionRegistry:
    """
    Registre des compagnons disponibles.

    Gère l'enregistrement, la recherche et la sélection des compagnons.
    """

    def __init__(self):
        self._companions: Dict[str, Companion] = {}
        self._default_id: str = "theo"

        # Charger les compagnons par défaut
        for companion in DEFAULT_COMPANIONS:
            self.register(companion)

    def register(self, companion: Companion) -> None:
        """Enregistre un compagnon."""
        self._companions[companion.id] = companion
        logger.info("Registered companion: %s (%s)", companion.id, companion.display_name)

    def unregister(self, companion_id: str) -> bool:
        """Désenregistre un compagnon."""
        if companion_id not in self._companions:
            return False
        if companion_id == self._default_id:
            logger.warning("Cannot unregister default companion")
            return False
        del self._companions[companion_id]
        return True

    def get(self, companion_id: str) -> Optional[Companion]:
        """Récupère un compagnon par ID."""
        return self._companions.get(companion_id)

    def get_default(self) -> Companion:
        """Récupère le compagnon par défaut."""
        return self._companions[self._default_id]

    def get_by_wake_word(self, text: str) -> Optional[Companion]:
        """
        Trouve le compagnon correspondant à un wake word dans le texte.

        Args:
            text: Texte contenant potentiellement un wake word

        Returns:
            Compagnon trouvé ou None
        """
        for companion in self._companions.values():
            if companion.matches_wake_word(text):
                return companion
        return None

    def list_all(self) -> List[Companion]:
        """Liste tous les compagnons."""
        return list(self._companions.values())

    def set_default(self, companion_id: str) -> bool:
        """Définit le compagnon par défaut."""
        if companion_id not in self._companions:
            return False
        self._default_id = companion_id
        return True

    def load_from_file(self, path: str) -> int:
        """
        Charge des compagnons depuis un fichier JSON.

        Args:
            path: Chemin vers le fichier JSON

        Returns:
            Nombre de compagnons chargés
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            count = 0
            for item in data.get("companions", []):
                companion = self._parse_companion(item)
                if companion:
                    self.register(companion)
                    count += 1

            return count
        except Exception as e:
            logger.error("Failed to load companions from %s: %s", path, e)
            return 0

    def _parse_companion(self, data: Dict[str, Any]) -> Optional[Companion]:
        """Parse un compagnon depuis un dict."""
        try:
            voice_data = data.get("voice", {})
            visual_data = data.get("visual", {})

            return Companion(
                id=data["id"],
                display_name=data["display_name"],
                wake_aliases=data.get("wake_aliases", [data["display_name"]]),
                gender=CompanionGender(data.get("gender", "neutral")),
                description=data.get("description", ""),
                voice=VoiceSettings(
                    provider=voice_data.get("provider", "elevenlabs"),
                    voice_id=voice_data.get("voice_id", ""),
                    stability=voice_data.get("stability", 0.75),
                    similarity_boost=voice_data.get("similarity_boost", 0.8),
                    speed=voice_data.get("speed", 1.0),
                    pitch=voice_data.get("pitch", 1.0)
                ),
                visual=VisualSettings(
                    enabled=visual_data.get("enabled", True),
                    avatar_url=visual_data.get("avatar_url", ""),
                    style=VisualStyle(visual_data.get("style", "semi_realistic")),
                    animations=visual_data.get("animations", ["blink", "breathe"]),
                    background_color=visual_data.get("background_color", "#6366f1")
                ),
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            logger.error("Failed to parse companion: %s", e)
            return None

    def status(self) -> Dict[str, Any]:
        """Retourne le statut du registre."""
        return {
            "companions": [c.to_dict() for c in self._companions.values()],
            "default": self._default_id,
            "count": len(self._companions)
        }


# ============================================================
# SINGLETON
# ============================================================

_registry: Optional[CompanionRegistry] = None


def get_companion_registry() -> CompanionRegistry:
    """Retourne l'instance singleton du registre."""
    global _registry
    if _registry is None:
        _registry = CompanionRegistry()
    return _registry
