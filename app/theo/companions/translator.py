"""
THÉO — Traducteur Compagnon → Théo
==================================

Règle absolue: Toute commande adressée à un compagnon
est traduite vers Théo.

"Léa, fais une facture" → "Théo, fais une facture"

Un seul acteur réel: Théo.
Les compagnons ne font que traduire et incarner.
"""

from typing import Optional, Tuple
import re
import logging

from app.theo.companions.registry import (
    CompanionRegistry, Companion, get_companion_registry
)

logger = logging.getLogger(__name__)


# ============================================================
# RÉSULTAT DE TRADUCTION
# ============================================================

class TranslationResult:
    """Résultat de la traduction compagnon → Théo."""

    def __init__(
        self,
        original_text: str,
        translated_text: str,
        companion_detected: Optional[Companion],
        wake_word_found: bool,
        is_for_theo: bool
    ):
        self.original_text = original_text
        self.translated_text = translated_text
        self.companion = companion_detected
        self.wake_word_found = wake_word_found
        self.is_for_theo = is_for_theo

    @property
    def companion_id(self) -> str:
        """ID du compagnon détecté ou 'theo' par défaut."""
        return self.companion.id if self.companion else "theo"

    def to_dict(self) -> dict:
        return {
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "companion_id": self.companion_id,
            "wake_word_found": self.wake_word_found,
            "is_for_theo": self.is_for_theo
        }


# ============================================================
# TRADUCTEUR
# ============================================================

class CompanionTranslator:
    """
    Traduit les commandes adressées aux compagnons vers Théo.

    Principe: Le compagnon est un masque. Théo est l'unique acteur.
    """

    # Wake word canonique
    THEO_WAKE_WORD = "Théo, s'il te plaît"
    THEO_WAKE_PATTERN = re.compile(
        r"th[eé]o[,\s]+s['\s]?il\s+te\s+pla[iî]t",
        re.IGNORECASE
    )

    # Patterns de wake word génériques
    GENERIC_WAKE_PATTERNS = [
        re.compile(r"^([A-Za-zÀ-ÿ]+)[,\s]+", re.IGNORECASE),  # "Nom, ..."
        re.compile(r"^(?:dis|hey|ok|salut)\s+([A-Za-zÀ-ÿ]+)", re.IGNORECASE),  # "Dis Nom..."
    ]

    def __init__(self, registry: Optional[CompanionRegistry] = None):
        self._registry = registry or get_companion_registry()

    def translate(self, text: str) -> TranslationResult:
        """
        Traduit une commande vers Théo.

        Args:
            text: Texte de la commande utilisateur

        Returns:
            TranslationResult avec le texte traduit
        """
        text = text.strip()
        original = text

        # 1. Vérifier le wake word canonique "Théo, s'il te plaît"
        if self.THEO_WAKE_PATTERN.search(text):
            # Retirer le wake word
            translated = self.THEO_WAKE_PATTERN.sub("", text).strip()
            translated = self._clean_text(translated)

            return TranslationResult(
                original_text=original,
                translated_text=translated,
                companion_detected=self._registry.get("theo"),
                wake_word_found=True,
                is_for_theo=True
            )

        # 2. Chercher un compagnon par son alias
        companion = self._registry.get_by_wake_word(text)

        if companion:
            # Retirer le nom du compagnon du texte
            translated = self._remove_companion_name(text, companion)
            translated = self._clean_text(translated)

            return TranslationResult(
                original_text=original,
                translated_text=translated,
                companion_detected=companion,
                wake_word_found=True,
                is_for_theo=True  # Toujours pour Théo après traduction
            )

        # 3. Aucun wake word trouvé
        # On considère quand même que c'est pour Théo (session active)
        return TranslationResult(
            original_text=original,
            translated_text=self._clean_text(text),
            companion_detected=None,
            wake_word_found=False,
            is_for_theo=True  # Dans une session, tout va à Théo
        )

    def _remove_companion_name(self, text: str, companion: Companion) -> str:
        """Retire le nom du compagnon du début du texte."""
        for alias in companion.wake_aliases:
            # Pattern: "Alias, ..." ou "Alias ..."
            pattern = re.compile(
                rf"^{re.escape(alias)}[,\s]+",
                re.IGNORECASE
            )
            text = pattern.sub("", text)

            # Pattern: "Dis Alias, ..." ou "Hey Alias, ..."
            pattern2 = re.compile(
                rf"^(?:dis|hey|ok|salut)\s+{re.escape(alias)}[,\s]+",
                re.IGNORECASE
            )
            text = pattern2.sub("", text)

        return text

    def _clean_text(self, text: str) -> str:
        """Nettoie le texte (espaces multiples, ponctuation initiale)."""
        # Retirer ponctuation initiale
        text = re.sub(r"^[,\s.!?]+", "", text)
        # Normaliser les espaces
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def detect_wake_word(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Détecte si le texte contient un wake word.

        Returns:
            Tuple (wake_word_found, companion_id)
        """
        # Wake word canonique
        if self.THEO_WAKE_PATTERN.search(text):
            return True, "theo"

        # Autres compagnons
        companion = self._registry.get_by_wake_word(text)
        if companion:
            return True, companion.id

        return False, None

    def is_valid_wake_phrase(self, text: str) -> bool:
        """
        Vérifie si le texte est une phrase de wake valide.

        La phrase doit commencer par un wake word et contenir une commande.
        """
        result = self.translate(text)
        return result.wake_word_found and len(result.translated_text) > 0


# ============================================================
# SINGLETON
# ============================================================

_translator: Optional[CompanionTranslator] = None


def get_translator() -> CompanionTranslator:
    """Retourne l'instance singleton du traducteur."""
    global _translator
    if _translator is None:
        _translator = CompanionTranslator()
    return _translator
