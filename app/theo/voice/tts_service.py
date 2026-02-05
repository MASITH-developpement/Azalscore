"""
THÉO — Service TTS (Text-to-Speech)
===================================

Abstraction pour la synthèse vocale.
Providers interchangeables: ElevenLabs, Google, Azure, etc.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncIterator, List
from dataclasses import dataclass, field
from enum import Enum
import logging
import os

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION VOIX
# ============================================================

@dataclass
class VoiceConfig:
    """Configuration d'une voix TTS."""

    voice_id: str
    name: str
    language: str = "fr"
    gender: str = "male"
    stability: float = 0.75
    similarity_boost: float = 0.8
    speed: float = 1.0
    pitch: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# RÉSULTAT TTS
# ============================================================

@dataclass
class TTSResult:
    """Résultat de synthèse vocale."""

    audio_data: bytes
    format: str
    duration_ms: int
    sample_rate: int = 22050
    text: str = ""
    voice_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "duration_ms": self.duration_ms,
            "sample_rate": self.sample_rate,
            "text": self.text,
            "voice_id": self.voice_id,
            "audio_size_bytes": len(self.audio_data),
            "metadata": self.metadata
        }


# ============================================================
# INTERFACE TTS
# ============================================================

class TTSService(ABC):
    """Interface abstraite pour les services TTS."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nom du provider."""
        pass

    @property
    @abstractmethod
    def voices(self) -> List[VoiceConfig]:
        """Voix disponibles."""
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        format: str = "mp3",
        **kwargs
    ) -> TTSResult:
        """
        Synthétise du texte en audio.

        Args:
            text: Texte à synthétiser
            voice_id: ID de la voix (ou défaut)
            format: Format de sortie (mp3, wav, etc.)

        Returns:
            Résultat avec données audio
        """
        pass

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        format: str = "mp3",
        **kwargs
    ) -> AsyncIterator[bytes]:
        """
        Synthétise en streaming.

        Yields:
            Chunks de données audio
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Vérifie la disponibilité du service."""
        pass


# ============================================================
# IMPLÉMENTATION ELEVENLABS
# ============================================================

class ElevenLabsTTSService(TTSService):
    """Implémentation TTS via ElevenLabs."""

    # Voix Théo par défaut (à configurer avec clone)
    DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel (placeholder)

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self._client = None
        self._voices: List[VoiceConfig] = [
            VoiceConfig(
                voice_id=self.DEFAULT_VOICE_ID,
                name="Théo",
                language="fr",
                gender="male",
                stability=0.75,
                similarity_boost=0.8
            )
        ]

    @property
    def name(self) -> str:
        return "elevenlabs"

    @property
    def voices(self) -> List[VoiceConfig]:
        return self._voices

    def _get_client(self):
        """Lazy initialization du client ElevenLabs."""
        if self._client is None:
            try:
                from elevenlabs.client import AsyncElevenLabs
                self._client = AsyncElevenLabs(api_key=self._api_key)
            except ImportError:
                raise ImportError("elevenlabs package required: pip install elevenlabs")
        return self._client

    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        format: str = "mp3",
        **kwargs
    ) -> TTSResult:
        """Synthétise via ElevenLabs API."""
        import time

        voice_id = voice_id or self.DEFAULT_VOICE_ID
        start_time = time.time()

        try:
            client = self._get_client()

            # Récupérer la config de voix
            voice_config = next(
                (v for v in self._voices if v.voice_id == voice_id),
                self._voices[0]
            )

            # Appel API
            audio = await client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings={
                    "stability": voice_config.stability,
                    "similarity_boost": voice_config.similarity_boost,
                    "speed": voice_config.speed
                },
                output_format=f"{format}_22050_32" if format == "mp3" else format
            )

            # Collecter les chunks
            audio_data = b""
            async for chunk in audio:
                audio_data += chunk

            duration_ms = int((time.time() - start_time) * 1000)

            # Estimer la durée audio (approximatif)
            # MP3 ~128kbps = 16KB/s
            estimated_audio_duration = int(len(audio_data) / 16 * 1000) if format == "mp3" else 0

            return TTSResult(
                audio_data=audio_data,
                format=format,
                duration_ms=estimated_audio_duration,
                sample_rate=22050,
                text=text,
                voice_id=voice_id,
                metadata={
                    "model": "eleven_multilingual_v2",
                    "processing_time_ms": duration_ms
                }
            )

        except Exception as e:
            logger.error("ElevenLabs synthesis error: %s", e)
            raise

    async def synthesize_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        format: str = "mp3",
        **kwargs
    ) -> AsyncIterator[bytes]:
        """Synthétise en streaming via ElevenLabs."""
        voice_id = voice_id or self.DEFAULT_VOICE_ID

        try:
            client = self._get_client()

            voice_config = next(
                (v for v in self._voices if v.voice_id == voice_id),
                self._voices[0]
            )

            audio = await client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_multilingual_v2",
                voice_settings={
                    "stability": voice_config.stability,
                    "similarity_boost": voice_config.similarity_boost,
                    "speed": voice_config.speed
                },
                output_format=f"{format}_22050_32" if format == "mp3" else format
            )

            async for chunk in audio:
                yield chunk

        except Exception as e:
            logger.error("ElevenLabs streaming error: %s", e)
            raise

    async def health_check(self) -> bool:
        """Vérifie la disponibilité de l'API."""
        try:
            client = self._get_client()
            # Vérifier les voix disponibles
            voices = await client.voices.get_all()
            return len(voices.voices) > 0
        except Exception as e:
            logger.error("ElevenLabs health check failed: %s", e)
            return False


# ============================================================
# IMPLÉMENTATION GOOGLE TTS (Fallback)
# ============================================================

class GoogleTTSService(TTSService):
    """Implémentation TTS via Google Cloud Text-to-Speech."""

    def __init__(self):
        self._client = None
        self._voices: List[VoiceConfig] = [
            VoiceConfig(
                voice_id="fr-FR-Standard-B",
                name="Théo (Google)",
                language="fr-FR",
                gender="male"
            )
        ]

    @property
    def name(self) -> str:
        return "google"

    @property
    def voices(self) -> List[VoiceConfig]:
        return self._voices

    def _get_client(self):
        """Lazy initialization du client Google."""
        if self._client is None:
            try:
                from google.cloud import texttospeech_v1 as tts
                self._client = tts.TextToSpeechAsyncClient()
            except ImportError:
                raise ImportError(
                    "google-cloud-texttospeech required: "
                    "pip install google-cloud-texttospeech"
                )
        return self._client

    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        format: str = "mp3",
        **kwargs
    ) -> TTSResult:
        """Synthétise via Google Cloud TTS."""
        from google.cloud import texttospeech_v1 as tts
        import time

        voice_id = voice_id or "fr-FR-Standard-B"
        start_time = time.time()

        try:
            client = self._get_client()

            # Configuration
            synthesis_input = tts.SynthesisInput(text=text)

            voice = tts.VoiceSelectionParams(
                language_code="fr-FR",
                name=voice_id
            )

            audio_config = tts.AudioConfig(
                audio_encoding=tts.AudioEncoding.MP3 if format == "mp3" else tts.AudioEncoding.LINEAR16,
                speaking_rate=1.0
            )

            # Appel API
            response = await client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            duration_ms = int((time.time() - start_time) * 1000)

            return TTSResult(
                audio_data=response.audio_content,
                format=format,
                duration_ms=duration_ms,
                text=text,
                voice_id=voice_id,
                metadata={"provider": "google"}
            )

        except Exception as e:
            logger.error("Google TTS synthesis error: %s", e)
            raise

    async def synthesize_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        format: str = "mp3",
        **kwargs
    ) -> AsyncIterator[bytes]:
        """Google TTS ne supporte pas le streaming natif."""
        result = await self.synthesize(text, voice_id, format, **kwargs)
        yield result.audio_data

    async def health_check(self) -> bool:
        """Vérifie la disponibilité de l'API."""
        try:
            client = self._get_client()
            return True
        except Exception as e:
            logger.error("Google TTS health check failed: %s", e)
            return False


# ============================================================
# IMPLÉMENTATION WEB SPEECH (Fallback navigateur)
# ============================================================

class WebSpeechTTSService(TTSService):
    """
    Placeholder pour Web Speech API (SpeechSynthesis).
    La synthèse se fait côté client (navigateur).
    """

    @property
    def name(self) -> str:
        return "webspeech"

    @property
    def voices(self) -> List[VoiceConfig]:
        return []  # Les voix sont côté client

    async def synthesize(
        self,
        text: str,
        voice_id: Optional[str] = None,
        format: str = "mp3",
        **kwargs
    ) -> TTSResult:
        """
        Retourne le texte pour synthèse côté client.
        Pas de données audio - le client utilise SpeechSynthesis.
        """
        return TTSResult(
            audio_data=b"",  # Vide - synthèse côté client
            format="text",
            duration_ms=0,
            text=text,
            voice_id=voice_id or "",
            metadata={"client_synthesis": True}
        )

    async def synthesize_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        format: str = "mp3",
        **kwargs
    ) -> AsyncIterator[bytes]:
        """Non utilisé - synthèse côté client."""
        yield b""

    async def health_check(self) -> bool:
        """Toujours disponible (dépend du client)."""
        return True


# ============================================================
# FACTORY ET SINGLETON
# ============================================================

class TTSProvider(Enum):
    """Providers TTS disponibles."""
    ELEVENLABS = "elevenlabs"
    GOOGLE = "google"
    WEBSPEECH = "webspeech"


_tts_services: Dict[TTSProvider, TTSService] = {}
_default_provider: TTSProvider = TTSProvider.ELEVENLABS


def get_tts_service(provider: Optional[TTSProvider] = None) -> TTSService:
    """
    Retourne une instance du service TTS.

    Args:
        provider: Provider spécifique ou None pour le défaut

    Returns:
        Instance TTSService
    """
    provider = provider or _default_provider

    if provider not in _tts_services:
        if provider == TTSProvider.ELEVENLABS:
            _tts_services[provider] = ElevenLabsTTSService()
        elif provider == TTSProvider.GOOGLE:
            _tts_services[provider] = GoogleTTSService()
        elif provider == TTSProvider.WEBSPEECH:
            _tts_services[provider] = WebSpeechTTSService()
        else:
            raise ValueError(f"Unknown TTS provider: {provider}")

    return _tts_services[provider]


def set_default_tts_provider(provider: TTSProvider) -> None:
    """Définit le provider TTS par défaut."""
    global _default_provider
    _default_provider = provider
