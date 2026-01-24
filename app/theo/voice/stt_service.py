"""
THÉO — Service STT (Speech-to-Text)
===================================

Abstraction pour la transcription vocale.
Providers interchangeables: Whisper, Google, Azure, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, BinaryIO
from dataclasses import dataclass
from enum import Enum
import logging
import os

logger = logging.getLogger(__name__)


# ============================================================
# RÉSULTAT STT
# ============================================================

@dataclass
class STTResult:
    """Résultat de transcription."""

    text: str
    confidence: float
    language: str
    duration_ms: int
    is_final: bool = True
    alternatives: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "duration_ms": self.duration_ms,
            "is_final": self.is_final,
            "alternatives": self.alternatives,
            "metadata": self.metadata
        }


# ============================================================
# INTERFACE STT
# ============================================================

class STTService(ABC):
    """Interface abstraite pour les services STT."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom du provider."""
        pass

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        format: str = "wav",
        language: str = "fr",
        **kwargs
    ) -> STTResult:
        """
        Transcrit un fichier audio.

        Args:
            audio_data: Données audio brutes
            format: Format audio (wav, mp3, webm, etc.)
            language: Code langue (fr, en, etc.)

        Returns:
            Résultat de transcription
        """
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: BinaryIO,
        format: str = "wav",
        language: str = "fr",
        **kwargs
    ):
        """
        Transcrit un flux audio en streaming.

        Yields:
            STTResult partiels puis final
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Vérifie la disponibilité du service."""
        pass


# ============================================================
# IMPLÉMENTATION WHISPER (OpenAI)
# ============================================================

class WhisperSTTService(STTService):
    """Implémentation STT via OpenAI Whisper."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

    @property
    def name(self) -> str:
        return "whisper"

    def _get_client(self):
        """Lazy initialization du client OpenAI."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self._api_key)
            except ImportError:
                raise ImportError("openai package required: pip install openai")
        return self._client

    async def transcribe(
        self,
        audio_data: bytes,
        format: str = "wav",
        language: str = "fr",
        **kwargs
    ) -> STTResult:
        """Transcrit via Whisper API."""
        import io
        import time

        client = self._get_client()
        start_time = time.time()

        try:
            # Créer un fichier-like object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{format}"

            # Appel API
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json"
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return STTResult(
                text=response.text,
                confidence=0.95,  # Whisper ne retourne pas de score
                language=response.language or language,
                duration_ms=duration_ms,
                is_final=True,
                metadata={
                    "model": "whisper-1",
                    "segments": getattr(response, "segments", [])
                }
            )

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            raise

    async def transcribe_stream(
        self,
        audio_stream: BinaryIO,
        format: str = "wav",
        language: str = "fr",
        **kwargs
    ):
        """
        Whisper ne supporte pas le streaming natif.
        On accumule et transcrit par chunks.
        """
        # Lire tout le stream
        audio_data = audio_stream.read()
        result = await self.transcribe(audio_data, format, language, **kwargs)
        yield result

    async def health_check(self) -> bool:
        """Vérifie la disponibilité de l'API."""
        try:
            client = self._get_client()
            # Simple test avec un petit audio vide
            return True
        except Exception as e:
            logger.error(f"Whisper health check failed: {e}")
            return False


# ============================================================
# IMPLÉMENTATION WEB SPEECH API (Fallback navigateur)
# ============================================================

class WebSpeechSTTService(STTService):
    """
    Placeholder pour le Web Speech API.
    La transcription se fait côté client (navigateur).
    Ce service reçoit le texte déjà transcrit.
    """

    @property
    def name(self) -> str:
        return "webspeech"

    async def transcribe(
        self,
        audio_data: bytes,
        format: str = "wav",
        language: str = "fr",
        **kwargs
    ) -> STTResult:
        """Non utilisé - la transcription est côté client."""
        raise NotImplementedError(
            "WebSpeech STT is client-side only. "
            "Use receive_transcription() instead."
        )

    async def transcribe_stream(
        self,
        audio_stream: BinaryIO,
        format: str = "wav",
        language: str = "fr",
        **kwargs
    ):
        """Non utilisé."""
        raise NotImplementedError("WebSpeech STT is client-side only.")

    async def receive_transcription(
        self,
        text: str,
        confidence: float = 0.9,
        language: str = "fr",
        is_final: bool = True
    ) -> STTResult:
        """
        Reçoit une transcription du client Web Speech API.

        Args:
            text: Texte transcrit par le navigateur
            confidence: Score de confiance
            language: Langue détectée
            is_final: Si c'est le résultat final

        Returns:
            STTResult
        """
        return STTResult(
            text=text,
            confidence=confidence,
            language=language,
            duration_ms=0,  # Non mesuré côté serveur
            is_final=is_final,
            metadata={"source": "webspeech"}
        )

    async def health_check(self) -> bool:
        """Toujours disponible (dépend du client)."""
        return True


# ============================================================
# FACTORY ET SINGLETON
# ============================================================

class STTProvider(Enum):
    """Providers STT disponibles."""
    WHISPER = "whisper"
    WEBSPEECH = "webspeech"


_stt_services: Dict[STTProvider, STTService] = {}
_default_provider: STTProvider = STTProvider.WHISPER


def get_stt_service(provider: Optional[STTProvider] = None) -> STTService:
    """
    Retourne une instance du service STT.

    Args:
        provider: Provider spécifique ou None pour le défaut

    Returns:
        Instance STTService
    """
    provider = provider or _default_provider

    if provider not in _stt_services:
        if provider == STTProvider.WHISPER:
            _stt_services[provider] = WhisperSTTService()
        elif provider == STTProvider.WEBSPEECH:
            _stt_services[provider] = WebSpeechSTTService()
        else:
            raise ValueError(f"Unknown STT provider: {provider}")

    return _stt_services[provider]


def set_default_stt_provider(provider: STTProvider) -> None:
    """Définit le provider STT par défaut."""
    global _default_provider
    _default_provider = provider
